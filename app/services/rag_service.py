import logging
import os
import re
import hashlib
from typing import Any

from app.core.config import settings
from app.db.models import TeachingContent
from app.db.session import SessionLocal


try:
    from langchain_community.vectorstores import Chroma
    from langchain_core.embeddings import Embeddings

    RAG_LIB_AVAILABLE = True
except Exception:
    Chroma = None  # type: ignore[assignment]
    Embeddings = object  # type: ignore[assignment]
    RAG_LIB_AVAILABLE = False


logger = logging.getLogger(__name__)


class _SimpleHashEmbeddings(Embeddings):
    """A tiny local embedding fallback that avoids heavy model downloads."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]+", (text or "").lower())

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = self._tokenize(text)
        if not tokens:
            return vec

        for token in tokens:
            digest = hashlib.sha1(token.encode("utf-8")).hexdigest()
            idx = int(digest[:8], 16) % self.dim
            vec[idx] += 1.0

        norm = sum(v * v for v in vec) ** 0.5
        if norm <= 0:
            return vec

        return [v / norm for v in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def is_rag_enabled() -> bool:
    return settings.rag_enabled and RAG_LIB_AVAILABLE


def _get_store() -> Any:
    os.makedirs(settings.rag_index_dir, exist_ok=True)
    return Chroma(
        collection_name="teaching_contents",
        persist_directory=settings.rag_index_dir,
        embedding_function=_SimpleHashEmbeddings(),
    )


def _chunk_text(text: str, chunk_size: int = 360, overlap: int = 80) -> list[str]:
    compact = re.sub(r"\s+", " ", (text or "")).strip()
    if not compact:
        return []

    chunks: list[str] = []
    start = 0
    size = len(compact)
    while start < size:
        end = min(size, start + chunk_size)
        chunks.append(compact[start:end])
        if end >= size:
            break
        start = max(0, end - overlap)
    return chunks


def _build_chunks_for_content(content: TeachingContent) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    text = "\n".join(
        [
            f"标题：{content.title}",
            f"分类：{content.category_id}",
            f"正文：{content.content or ''}",
        ]
    )
    chunks = _chunk_text(text)
    if not chunks:
        chunks = [f"标题：{content.title}"]

    metadatas: list[dict[str, Any]] = []
    ids: list[str] = []
    for idx, chunk in enumerate(chunks):
        ids.append(f"content-{content.id}-chunk-{idx}")
        metadatas.append(
            {
                "content_id": int(content.id),
                "title": content.title,
                "category_id": int(content.category_id) if content.category_id is not None else -1,
                "chunk_index": idx,
            }
        )
    return chunks, metadatas, ids


def sync_teaching_content_index(content_id: int) -> None:
    """Incrementally sync one content item into vector index. Safe to call in BackgroundTasks."""
    if not is_rag_enabled():
        return

    db = SessionLocal()
    try:
        store = _get_store()

        # Cleanup old chunks first.
        try:
            store.delete(where={"content_id": int(content_id)})
        except Exception:
            logger.debug("RAG delete by where failed for content_id=%s", content_id)
            try:
                if hasattr(store, "_collection"):
                    old_rows = store._collection.get(where={"content_id": int(content_id)})  # type: ignore[attr-defined]
                    old_ids = old_rows.get("ids") or []
                    if old_ids:
                        store.delete(ids=old_ids)
            except Exception:
                logger.debug("RAG delete by ids fallback failed for content_id=%s", content_id)

        content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
        if not content or not content.is_published:
            if hasattr(store, "persist"):
                store.persist()
            return

        texts, metadatas, ids = _build_chunks_for_content(content)
        store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        if hasattr(store, "persist"):
            store.persist()
    except Exception:
        logger.exception("RAG sync failed for content_id=%s", content_id)
    finally:
        db.close()


def rebuild_published_content_index() -> int:
    """Rebuild index for all published teaching contents."""
    if not is_rag_enabled():
        return 0

    db = SessionLocal()
    count = 0
    try:
        store = _get_store()
        try:
            store.delete(where={})
        except Exception:
            try:
                if hasattr(store, "_collection"):
                    all_rows = store._collection.get()  # type: ignore[attr-defined]
                    all_ids = all_rows.get("ids") or []
                    if all_ids:
                        store.delete(ids=all_ids)
            except Exception:
                logger.debug("RAG full clear fallback failed")

        contents = (
            db.query(TeachingContent)
            .filter(TeachingContent.is_published == True)
            .order_by(TeachingContent.id)
            .all()
        )
        for content in contents:
            sync_teaching_content_index(content.id)
            count += 1
    finally:
        db.close()

    return count


def search_teaching_content_context(question: str, k: int | None = None) -> list[dict[str, Any]]:
    if not is_rag_enabled() or not question.strip():
        return []

    try:
        store = _get_store()
        rows = store.similarity_search_with_score(question, k=k or settings.rag_top_k)
    except Exception:
        logger.exception("RAG search failed")
        return []

    result: list[dict[str, Any]] = []
    for doc, score in rows:
        text = (doc.page_content or "").strip()
        if not text:
            continue
        result.append(
            {
                "title": str(doc.metadata.get("title") or "教学内容"),
                "snippet": text[:180],
                "score": float(score),
            }
        )
    return result
