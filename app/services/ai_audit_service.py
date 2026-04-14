import json
import logging
from typing import Any

from app.core.config import settings
from app.db.models import UserOperationLog
from app.db.session import SessionLocal


logger = logging.getLogger(__name__)


def _estimate_tokens(text: str) -> int:
    # Simple heuristic for mixed zh/en text to keep auditing lightweight.
    if not text:
        return 0
    return max(1, len(text) // 2)


def infer_fallback_reason(source: str) -> str | None:
    if source == "stream-error":
        return "stream_connection_or_provider_error"
    if source.startswith("rule-based"):
        if not settings.qwen_api_key:
            return "missing_qwen_api_key"
        return "model_call_failed_or_empty"
    if source in {"qwen", "deepseek", "llm"}:
        if settings.ai_langchain_enabled:
            return "langchain_path_failed_or_disabled_at_runtime"
    return None


def record_ai_audit(
    *,
    operator_id: int,
    operation_type: str,
    source: str,
    latency_ms: int,
    prompt_text: str,
    output_text: str,
    fallback_reason: str | None = None,
    token_usage: dict[str, int] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    session = SessionLocal()
    try:
        prompt_tokens = token_usage.get("prompt_tokens") if token_usage else None
        completion_tokens = token_usage.get("completion_tokens") if token_usage else None

        if prompt_tokens is None:
            prompt_tokens = _estimate_tokens(prompt_text)
        if completion_tokens is None:
            completion_tokens = _estimate_tokens(output_text)

        total_tokens = int(prompt_tokens) + int(completion_tokens)

        detail_payload = {
            "source": source,
            "latency_ms": latency_ms,
            "fallback_reason": fallback_reason,
            "token_usage": {
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(total_tokens),
                "estimated": token_usage is None,
            },
            "prompt_preview": (prompt_text or "")[:200],
            "output_preview": (output_text or "")[:200],
            "extra": extra or {},
        }

        log_row = UserOperationLog(
            operator_id=operator_id,
            operation_type=operation_type[:20],
            details=json.dumps(detail_payload, ensure_ascii=False),
        )
        session.add(log_row)
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to persist AI audit log")
    finally:
        session.close()
