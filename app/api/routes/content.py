import datetime
import os
import time
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_admin_user, get_content_editor, get_current_user, get_db, get_teacher_user
from app.db.models import (
    ContentComment,
    ContentCommentLike,
    StudentLearningRecord,
    TeachingContent,
    User,
)
from app.schemas.content import (
    ContentAIPolishRequest,
    ContentAIPolishResponse,
    ContentCommentCreate,
    ContentCommentLikeResponse,
    ContentCommentReplyCreate,
    ContentCommentResponse,
    LearningStats,
    StudentLearningRecordResponse,
    StudentProgress,
    TeachingContentCreate,
    TeachingContentDetail,
    TeachingContentResponse,
    TeachingContentUpdate,
)
from app.services.ai_science_service import polish_teaching_content
from app.services.ai_audit_service import infer_fallback_reason, record_ai_audit
from app.services.notification_service import create_notification
from app.services.rag_service import rebuild_published_content_index, sync_teaching_content_index


router = APIRouter(tags=["content"])

UPLOAD_ROOT = "uploads"
CONTENT_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "content")
ALLOWED_CONTENT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    ".mp4", ".mov", ".avi", ".webm",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
}
MAX_CONTENT_FILE_SIZE = 50 * 1024 * 1024
MAX_PAGE_SIZE = 100


def _safe_remove_local_upload(path_or_url: str | None) -> bool:
    if not path_or_url:
        return False

    raw = path_or_url.strip()
    if not raw:
        return False

    normalized = raw.replace("\\", "/")
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return False

    relative = normalized.lstrip("/")
    if relative.startswith("uploads/"):
        relative = relative[len("uploads/") :]
    if not relative.startswith("content/"):
        return False

    candidate = os.path.abspath(os.path.join(UPLOAD_ROOT, relative))
    allowed_root = os.path.abspath(CONTENT_UPLOAD_DIR)
    if not (candidate == allowed_root or candidate.startswith(allowed_root + os.sep)):
        return False
    if not os.path.isfile(candidate):
        return False

    try:
        os.remove(candidate)
        return True
    except OSError:
        return False


def _normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []

    result: list[str] = []
    seen: set[str] = set()
    for item in tags:
        value = (item or "").strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(value)
    return result


def _parse_tags(tags_raw: str | None) -> list[str]:
    if not tags_raw:
        return []
    return _normalize_tags(tags_raw.split(","))


def _join_tags(tags: list[str] | None) -> str | None:
    normalized = _normalize_tags(tags)
    if not normalized:
        return None
    return ",".join(normalized)


def _display_name(user: User | None) -> str | None:
    if not user:
        return None
    return user.real_name or user.username


def _content_permissions(content: TeachingContent, current_user: User) -> dict[str, bool]:
    can_manage = current_user.role == "admin" or content.author_id == current_user.id
    return {
        "can_edit": can_manage,
        "can_delete": can_manage,
        "can_publish": can_manage,
    }


def _serialize_teaching_content(
    content: TeachingContent,
    current_user: User,
) -> dict[str, object]:
    author = getattr(content, "author", None)
    author_name = _display_name(author)

    payload: dict[str, object] = {
        "id": content.id,
        "title": content.title,
        "tags": _parse_tags(content.tags),
        "content_type": content.content_type,
        "content": content.content,
        "video_url": content.video_url,
        "file_path": content.file_path,
        "cover_image": content.cover_image,
        "author_id": content.author_id,
        "author_name": author_name,
        "author_username": getattr(author, "username", None),
        "publisher_name": author_name,
        "view_count": content.view_count,
        "is_published": content.is_published,
        "published_at": content.published_at,
        "created_at": content.created_at,
        "updated_at": content.updated_at,
        **_content_permissions(content, current_user),
    }
    return payload


def _ensure_content_interaction_allowed(content: TeachingContent | None, current_user: User) -> None:
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if not content.is_published and current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="无权互动未发布内容")


def _build_comment_response(
    comment: ContentComment,
    *,
    student: User | None = None,
    like_count: int | None = None,
    liked: bool = False,
    replies: list[ContentCommentResponse] | None = None,
) -> ContentCommentResponse:
    owner = student or comment.student
    return ContentCommentResponse(
        id=comment.id,
        content_id=comment.content_id,
        student_id=comment.student_id,
        student_name=_display_name(owner),
        student_avatar_url=owner.avatar_url if owner else None,
        parent_id=comment.parent_id,
        comment=comment.comment,
        like_count=int(comment.like_count or 0) if like_count is None else like_count,
        liked=liked,
        teacher_reply=comment.teacher_reply,
        reply_at=comment.reply_at,
        created_at=comment.created_at,
        replies=replies or [],
    )


def _serialize_comment_rows(
    db: Session,
    comments: list[ContentComment],
    current_user_id: int,
) -> list[ContentCommentResponse]:
    if not comments:
        return []

    comment_ids = [c.id for c in comments]
    like_counts = {
        cid: cnt
        for cid, cnt in (
            db.query(ContentCommentLike.comment_id, func.count(ContentCommentLike.id))
            .filter(ContentCommentLike.comment_id.in_(comment_ids))
            .group_by(ContentCommentLike.comment_id)
            .all()
        )
    }
    liked_ids = {
        cid
        for (cid,) in (
            db.query(ContentCommentLike.comment_id)
            .filter(
                ContentCommentLike.comment_id.in_(comment_ids),
                ContentCommentLike.user_id == current_user_id,
            )
            .all()
        )
    }

    serialized: dict[int, ContentCommentResponse] = {
        row.id: _build_comment_response(
            row,
            like_count=like_counts.get(row.id, 0),
            liked=row.id in liked_ids,
            replies=[],
        )
        for row in comments
    }

    roots: list[ContentCommentResponse] = []
    for row in comments:
        current = serialized[row.id]
        if row.parent_id and row.parent_id in serialized:
            serialized[row.parent_id].replies.append(current)
        else:
            roots.append(current)

    return roots


# ---------------- 内容管理 ----------------
@router.get("/api/content/contents")
async def get_contents(
    tag: Optional[str] = None,
    content_type: Optional[str] = None,
    is_published: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取内容列表（支持筛选和搜索/分页）"""
    if page < 1:
        raise HTTPException(status_code=400, detail="页码必须大于等于 1")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"page_size 必须在 1 到 {MAX_PAGE_SIZE} 之间")

    query = db.query(TeachingContent).options(
        joinedload(TeachingContent.author),
    )

    if current_user.role not in ["teacher", "admin"]:
        is_published = True

    if tag:
        tag_pattern = f"%{tag.strip()}%"
        query = query.filter(TeachingContent.tags.like(tag_pattern))
    if content_type:
        query = query.filter(TeachingContent.content_type == content_type)
    if is_published is not None:
        query = query.filter(TeachingContent.is_published == is_published)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (TeachingContent.title.like(search_pattern))
            | (TeachingContent.content.like(search_pattern))
            | (TeachingContent.tags.like(search_pattern))
        )

    total = query.count()
    contents = (
        query.order_by(desc(TeachingContent.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = [_serialize_teaching_content(content, current_user) for content in contents]

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.get("/api/content/contents/{content_id}", response_model=TeachingContentDetail)
async def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取内容详情"""
    content = (
        db.query(TeachingContent)
        .options(joinedload(TeachingContent.author))
        .filter(TeachingContent.id == content_id)
        .first()
    )
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if current_user.role not in ["teacher", "admin"] and not content.is_published:
        raise HTTPException(status_code=403, detail="无权查看未发布的内容")

    content.view_count += 1
    db.commit()
    db.refresh(content)

    return _serialize_teaching_content(content, current_user)


@router.post("/api/content/contents", response_model=TeachingContentResponse)
async def create_content(
    content: TeachingContentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_content_editor),
    db: Session = Depends(get_db),
):
    """创建内容（教师/管理员）"""
    content_data = content.model_dump()
    content_data["tags"] = _join_tags(content_data.get("tags"))
    db_content = TeachingContent(**content_data, author_id=current_user.id)
    if content.is_published:
        db_content.published_at = datetime.datetime.utcnow()

    db.add(db_content)
    db.commit()
    db.refresh(db_content)

    background_tasks.add_task(sync_teaching_content_index, db_content.id)
    return _serialize_teaching_content(db_content, current_user)


@router.put("/api/content/contents/{content_id}", response_model=TeachingContentResponse)
async def update_content(
    content_id: int,
    content_update: TeachingContentUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_content_editor),
    db: Session = Depends(get_db),
):
    """更新内容（教师/管理员）"""
    db_content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
    if not db_content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if current_user.role != "admin" and db_content.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能编辑自己创建的内容")

    was_published = bool(db_content.is_published)
    update_data = content_update.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = _join_tags(update_data.get("tags"))
    for key, value in update_data.items():
        setattr(db_content, key, value)

    if update_data.get("is_published") and not was_published:
        db_content.published_at = datetime.datetime.utcnow()
    if update_data.get("is_published") is False:
        db_content.published_at = None

    db.commit()
    db.refresh(db_content)

    background_tasks.add_task(sync_teaching_content_index, db_content.id)
    return _serialize_teaching_content(db_content, current_user)


@router.delete("/api/content/contents/{content_id}")
async def delete_content(
    content_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_content_editor),
    db: Session = Depends(get_db),
):
    """删除内容（教师/管理员）"""
    db_content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
    if not db_content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if current_user.role != "admin" and db_content.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己创建的内容")

    deleted_content_id = db_content.id
    removed_files = 0
    if _safe_remove_local_upload(db_content.file_path):
        removed_files += 1
    if _safe_remove_local_upload(db_content.cover_image):
        removed_files += 1
    db.delete(db_content)
    db.commit()

    background_tasks.add_task(sync_teaching_content_index, deleted_content_id)
    return {"message": "内容已删除", "removed_files": removed_files}


@router.post("/api/content/upload")
async def upload_content_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_content_editor),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_CONTENT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="上传文件为空")
    if len(payload) > MAX_CONTENT_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超出限制（最大 50MB）")

    os.makedirs(CONTENT_UPLOAD_DIR, exist_ok=True)
    filename = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(CONTENT_UPLOAD_DIR, filename)
    with open(save_path, "wb") as fw:
        fw.write(payload)

    return {
        "url": f"/uploads/content/{filename}",
        "filename": file.filename,
        "size": len(payload),
    }


@router.post("/api/content/ai/polish", response_model=ContentAIPolishResponse)
async def ai_polish_content(
    request: ContentAIPolishRequest,
    current_user: User = Depends(get_content_editor),
):
    start_ts = time.perf_counter()
    result, source = await polish_teaching_content(
        bullet_points=request.bullet_points,
        mode=request.mode,
        tone=request.tone,
        target_length=request.target_length,
    )

    latency_ms = int((time.perf_counter() - start_ts) * 1000)
    record_ai_audit(
        operator_id=current_user.id,
        operation_type="ai_polish",
        source=source,
        latency_ms=latency_ms,
        prompt_text=request.bullet_points,
        output_text=result.get("organized_content", ""),
        fallback_reason=infer_fallback_reason(source),
        extra={"mode": request.mode, "tone": request.tone, "target_length": request.target_length},
    )

    return ContentAIPolishResponse(
        title_suggestion=result.get("title_suggestion", "科学探究小课堂"),
        organized_content=result.get("organized_content", ""),
        source=source,
    )


@router.post("/api/content/ai/reindex")
async def rebuild_ai_content_index(
    current_user: User = Depends(get_admin_user),
):
    count = rebuild_published_content_index()
    return {"message": "重建完成", "indexed_contents": count}


@router.post("/api/content/contents/{content_id}/publish")
async def publish_content(
    content_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_content_editor),
    db: Session = Depends(get_db),
):
    """发布/取消发布内容"""
    db_content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
    if not db_content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if current_user.role != "admin" and db_content.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能操作自己创建的内容")

    db_content.is_published = not db_content.is_published
    if db_content.is_published:
        db_content.published_at = datetime.datetime.utcnow()
    else:
        db_content.published_at = None

    db.commit()
    background_tasks.add_task(sync_teaching_content_index, db_content.id)
    return {"message": f"内容已{'发布' if db_content.is_published else '取消发布'}"}


# ---------------- 学习记录 ----------------
@router.get("/api/content/my-learning", response_model=list[StudentLearningRecordResponse])
async def get_my_learning(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取我的学习记录（学生）"""
    records = (
        db.query(StudentLearningRecord)
        .filter(StudentLearningRecord.student_id == current_user.id)
        .all()
    )
    return records


@router.post("/api/content/contents/{content_id}/start", response_model=StudentLearningRecordResponse)
async def start_learning(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """开始学习（创建或更新学习记录）"""
    content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    record = (
        db.query(StudentLearningRecord)
        .filter(
            StudentLearningRecord.student_id == current_user.id,
            StudentLearningRecord.content_id == content_id,
        )
        .first()
    )

    if record:
        record.status = "in_progress"
        record.last_accessed = datetime.datetime.utcnow()
    else:
        record = StudentLearningRecord(
            student_id=current_user.id,
            content_id=content_id,
            status="in_progress",
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


@router.post("/api/content/contents/{content_id}/complete", response_model=StudentLearningRecordResponse)
async def complete_learning(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """完成学习"""
    record = (
        db.query(StudentLearningRecord)
        .filter(
            StudentLearningRecord.student_id == current_user.id,
            StudentLearningRecord.content_id == content_id,
        )
        .first()
    )

    if not record:
        record = StudentLearningRecord(
            student_id=current_user.id,
            content_id=content_id,
            status="completed",
            completed_at=datetime.datetime.utcnow(),
        )
        db.add(record)
    else:
        record.status = "completed"
        record.completed_at = datetime.datetime.utcnow()
        record.progress_percent = 100

    db.commit()
    db.refresh(record)
    return record


@router.put("/api/content/contents/{content_id}/progress")
async def update_progress(
    content_id: int,
    progress: int,
    time_spent: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新学习进度"""
    record = (
        db.query(StudentLearningRecord)
        .filter(
            StudentLearningRecord.student_id == current_user.id,
            StudentLearningRecord.content_id == content_id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="学习记录不存在")

    record.progress_percent = min(100, max(0, progress))
    record.time_spent_seconds = time_spent
    record.last_accessed = datetime.datetime.utcnow()

    if record.progress_percent >= 100:
        record.status = "completed"
        record.completed_at = datetime.datetime.utcnow()

    db.commit()
    return {"message": "进度已更新", "progress": record.progress_percent}


# ---------------- 评论/问答 ----------------
@router.get("/api/content/contents/{content_id}/comments", response_model=list[ContentCommentResponse])
async def get_comments(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取内容的评论列表"""
    content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if current_user.role not in ["teacher", "admin"] and not content.is_published:
        raise HTTPException(status_code=403, detail="无权查看未发布内容的评论")

    comments = (
        db.query(ContentComment)
        .filter(ContentComment.content_id == content_id)
        .order_by(ContentComment.created_at)
        .all()
    )
    return _serialize_comment_rows(db, comments, current_user.id)


@router.post("/api/content/contents/{content_id}/comments", response_model=ContentCommentResponse)
async def add_comment(
    content_id: int,
    payload: ContentCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """添加评论（支持主评论/回复）"""
    content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
    _ensure_content_interaction_allowed(content, current_user)

    comment_text = payload.comment.strip()
    if not comment_text:
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    if len(comment_text) > 500:
        raise HTTPException(status_code=400, detail="评论内容不能超过 500 字")

    parent_comment = None
    if payload.parent_id is not None:
        parent_comment = (
            db.query(ContentComment)
            .filter(
                ContentComment.id == payload.parent_id,
                ContentComment.content_id == content_id,
            )
            .first()
        )
        if not parent_comment:
            raise HTTPException(status_code=404, detail="回复目标评论不存在")

    db_comment = ContentComment(
        content_id=content_id,
        student_id=current_user.id,
        parent_id=payload.parent_id,
        comment=comment_text,
    )
    db.add(db_comment)

    if parent_comment and parent_comment.student_id != current_user.id:
        create_notification(
            db,
            user_id=parent_comment.student_id,
            actor_id=current_user.id,
            notification_type="comment_reply",
            title="你的评论收到了新回复",
            content=f"{_display_name(current_user)} 回复了你的评论",
            content_id=content_id,
            comment_id=parent_comment.id,
        )

    db.commit()
    db.refresh(db_comment)

    return _build_comment_response(
        db_comment,
        student=current_user,
        like_count=0,
        liked=False,
        replies=[],
    )


@router.post("/api/content/comments/{comment_id}/reply", response_model=ContentCommentResponse)
async def reply_to_comment(
    comment_id: int,
    payload: ContentCommentReplyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parent_comment = db.query(ContentComment).filter(ContentComment.id == comment_id).first()
    if not parent_comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    content = db.query(TeachingContent).filter(TeachingContent.id == parent_comment.content_id).first()
    _ensure_content_interaction_allowed(content, current_user)

    comment_text = payload.comment.strip()
    if not comment_text:
        raise HTTPException(status_code=400, detail="回复内容不能为空")
    if len(comment_text) > 500:
        raise HTTPException(status_code=400, detail="回复内容不能超过 500 字")

    db_comment = ContentComment(
        content_id=parent_comment.content_id,
        student_id=current_user.id,
        parent_id=parent_comment.id,
        comment=comment_text,
    )
    db.add(db_comment)

    if parent_comment.student_id != current_user.id:
        create_notification(
            db,
            user_id=parent_comment.student_id,
            actor_id=current_user.id,
            notification_type="comment_reply",
            title="你的评论收到了新回复",
            content=f"{_display_name(current_user)} 回复了你的评论",
            content_id=parent_comment.content_id,
            comment_id=parent_comment.id,
        )

    db.commit()
    db.refresh(db_comment)

    return _build_comment_response(
        db_comment,
        student=current_user,
        like_count=0,
        liked=False,
        replies=[],
    )


@router.post("/api/content/comments/{comment_id}/like", response_model=ContentCommentLikeResponse)
async def toggle_comment_like(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_comment = db.query(ContentComment).filter(ContentComment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    content = db.query(TeachingContent).filter(TeachingContent.id == db_comment.content_id).first()
    _ensure_content_interaction_allowed(content, current_user)

    if db_comment.student_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能给自己的评论点赞")

    db_like = (
        db.query(ContentCommentLike)
        .filter(
            ContentCommentLike.comment_id == comment_id,
            ContentCommentLike.user_id == current_user.id,
        )
        .first()
    )

    liked = False
    if db_like:
        db.delete(db_like)
    else:
        liked = True
        db.add(ContentCommentLike(comment_id=comment_id, user_id=current_user.id))
        create_notification(
            db,
            user_id=db_comment.student_id,
            actor_id=current_user.id,
            notification_type="comment_like",
            title="你的评论收到了新点赞",
            content=f"{_display_name(current_user)} 赞了你的评论",
            content_id=db_comment.content_id,
            comment_id=db_comment.id,
        )

    db.flush()
    like_count = (
        db.query(ContentCommentLike)
        .filter(ContentCommentLike.comment_id == comment_id)
        .count()
    )
    db_comment.like_count = like_count
    db.commit()

    return ContentCommentLikeResponse(comment_id=comment_id, liked=liked, like_count=like_count)


@router.put("/api/content/comments/{comment_id}", response_model=ContentCommentResponse)
async def reply_comment(
    comment_id: int,
    reply: str,
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
):
    """回复评论（教师/管理员）"""
    db_comment = db.query(ContentComment).filter(ContentComment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    db_comment.teacher_reply = reply
    db_comment.reply_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(db_comment)

    return _build_comment_response(db_comment, replies=[])


# ---------------- 学习统计（教师端） ----------------
@router.get("/api/content/stats/overview", response_model=LearningStats)
async def get_learning_stats(
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
):
    """获取学习统计概览（教师/管理员）"""
    total_students = db.query(User).filter(User.role == "student").count()
    total_contents = db.query(TeachingContent).filter(TeachingContent.is_published == True).count()

    total_records = db.query(StudentLearningRecord).count()
    completed = (
        db.query(StudentLearningRecord)
        .filter(StudentLearningRecord.status == "completed")
        .count()
    )
    in_progress = (
        db.query(StudentLearningRecord)
        .filter(StudentLearningRecord.status == "in_progress")
        .count()
    )
    not_started = total_records - completed - in_progress

    completion_rate = (completed / total_contents * 100) if total_contents > 0 else 0
    avg_progress_result = (
        db.query(
            (
                func.sum(StudentLearningRecord.progress_percent)
                / func.count(StudentLearningRecord.id)
            ).label("avg")
        )
        .filter(StudentLearningRecord.progress_percent > 0)
        .first()
    )
    average_progress = float(avg_progress_result.avg) if avg_progress_result and avg_progress_result.avg is not None else 0

    return LearningStats(
        total_students=total_students,
        total_contents=total_contents,
        total_learning_records=total_records,
        completed_count=completed,
        in_progress_count=in_progress,
        not_started_count=not_started,
        completion_rate=round(completion_rate, 2),
        average_progress=round(average_progress, 2),
    )


@router.get("/api/content/stats/students", response_model=list[StudentProgress])
async def get_students_progress(
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
):
    """获取所有学生学习进度（教师/管理员）"""
    students = db.query(User).filter(User.role == "student").all()
    published_contents = db.query(TeachingContent).filter(TeachingContent.is_published == True).count()

    result = []
    for student in students:
        records = db.query(StudentLearningRecord).filter(StudentLearningRecord.student_id == student.id).all()

        completed = sum(1 for r in records if r.status == "completed")
        in_progress = sum(1 for r in records if r.status == "in_progress")
        total_time = sum(r.time_spent_seconds for r in records)

        completion_rate = (completed / published_contents * 100) if published_contents > 0 else 0

        result.append(
            StudentProgress(
                student_id=student.id,
                student_name=student.username,
                total_contents=published_contents,
                completed_count=completed,
                in_progress_count=in_progress,
                completion_rate=round(completion_rate, 2),
                total_time_spent=total_time,
            )
        )

    return result


@router.get("/api/content/stats/content/{content_id}", response_model=list[StudentProgress])
async def get_content_learning_stats(
    content_id: int,
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
):
    """获取特定内容的学习统计（教师/管理员）"""
    content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    records = db.query(StudentLearningRecord).filter(StudentLearningRecord.content_id == content_id).all()

    result = []
    for record in records:
        student = db.query(User).filter(User.id == record.student_id).first()
        if student:
            result.append(
                StudentProgress(
                    student_id=student.id,
                    student_name=student.username,
                    total_contents=1,
                    completed_count=1 if record.status == "completed" else 0,
                    in_progress_count=1 if record.status == "in_progress" else 0,
                    completion_rate=100 if record.status == "completed" else 0,
                    total_time_spent=record.time_spent_seconds,
                )
            )

    return result
