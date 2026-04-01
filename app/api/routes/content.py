import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api.dependencies import get_admin_user, get_content_editor, get_current_user, get_db, get_teacher_user
from app.db.models import (
    ContentCategory,
    ContentComment,
    ContentCommentLike,
    StudentLearningRecord,
    TeachingContent,
    User,
)
from app.schemas.content import (
    ContentCategoryCreate,
    ContentCategoryResponse,
    ContentCategoryWithChildren,
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
from app.services.notification_service import create_notification


router = APIRouter(tags=["content"])


def _display_name(user: User | None) -> str | None:
    if not user:
        return None
    return user.real_name or user.username


def _ensure_content_interaction_allowed(content: TeachingContent | None, current_user: User) -> None:
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if not content.is_published and current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="无权互动未发布内容")


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

    serialized: dict[int, ContentCommentResponse] = {}
    for row in comments:
        serialized[row.id] = ContentCommentResponse(
            id=row.id,
            content_id=row.content_id,
            student_id=row.student_id,
            student_name=_display_name(row.student),
            student_avatar_url=row.student.avatar_url if row.student else None,
            parent_id=row.parent_id,
            comment=row.comment,
            like_count=like_counts.get(row.id, 0),
            liked=row.id in liked_ids,
            teacher_reply=row.teacher_reply,
            reply_at=row.reply_at,
            created_at=row.created_at,
            replies=[],
        )

    roots: list[ContentCommentResponse] = []
    for row in comments:
        current = serialized[row.id]
        if row.parent_id and row.parent_id in serialized:
            serialized[row.parent_id].replies.append(current)
        else:
            roots.append(current)

    return roots


# ---------------- 分类管理 ----------------
@router.get("/api/content/categories", response_model=list[ContentCategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """获取所有分类（按排序排序）"""
    categories = (
        db.query(ContentCategory)
        .filter(ContentCategory.parent_id == None)
        .order_by(ContentCategory.sort_order)
        .all()
    )
    return categories


@router.get("/api/content/categories/tree", response_model=list[ContentCategoryWithChildren])
async def get_categories_tree(db: Session = Depends(get_db)):
    """获取分类树形结构"""
    parent_categories = (
        db.query(ContentCategory)
        .filter(ContentCategory.parent_id == None)
        .order_by(ContentCategory.sort_order)
        .all()
    )

    result = []
    for parent in parent_categories:
        parent_dict = ContentCategoryWithChildren(
            id=parent.id,
            name=parent.name,
            description=parent.description,
            parent_id=parent.parent_id,
            sort_order=parent.sort_order,
            created_at=parent.created_at,
            children=[],
        )
        children = (
            db.query(ContentCategory)
            .filter(ContentCategory.parent_id == parent.id)
            .order_by(ContentCategory.sort_order)
            .all()
        )
        parent_dict.children = [
            ContentCategoryResponse(
                id=child.id,
                name=child.name,
                description=child.description,
                parent_id=child.parent_id,
                sort_order=child.sort_order,
                created_at=child.created_at,
            )
            for child in children
        ]
        result.append(parent_dict)

    return result


@router.post("/api/content/categories", response_model=ContentCategoryResponse)
async def create_category(
    category: ContentCategoryCreate,
    current_user: User = Depends(get_content_editor),
    db: Session = Depends(get_db),
):
    """创建分类（教师/管理员）"""
    db_category = ContentCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/api/content/categories/{category_id}", response_model=ContentCategoryResponse)
async def update_category(
    category_id: int,
    category: ContentCategoryCreate,
    current_user: User = Depends(get_content_editor),
    db: Session = Depends(get_db),
):
    """更新分类（教师/管理员）"""
    db_category = db.query(ContentCategory).filter(ContentCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")

    for key, value in category.model_dump().items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/api/content/categories/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """删除分类（仅管理员）"""
    db_category = db.query(ContentCategory).filter(ContentCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")

    has_children = db.query(ContentCategory).filter(ContentCategory.parent_id == category_id).first()
    if has_children:
        raise HTTPException(status_code=400, detail="请先删除子分类")

    has_contents = db.query(TeachingContent).filter(TeachingContent.category_id == category_id).first()
    if has_contents:
        raise HTTPException(status_code=400, detail="请先删除该分类下的内容")

    db.delete(db_category)
    db.commit()
    return {"message": "分类已删除"}


# ---------------- 内容管理 ----------------
@router.get("/api/content/contents")
async def get_contents(
    category_id: Optional[int] = None,
    content_type: Optional[str] = None,
    is_published: Optional[bool] = True,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取内容列表（支持筛选和搜索/分页）"""
    query = db.query(TeachingContent)

    if current_user.role not in ["teacher", "admin"]:
        is_published = True

    if category_id:
        query = query.filter(TeachingContent.category_id == category_id)
    if content_type:
        query = query.filter(TeachingContent.content_type == content_type)
    if is_published is not None:
        query = query.filter(TeachingContent.is_published == is_published)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (TeachingContent.title.like(search_pattern))
            | (TeachingContent.content.like(search_pattern))
        )

    total = query.count()
    contents = (
        query.order_by(desc(TeachingContent.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for content in contents:
        category_name = getattr(getattr(content, "category", None), "name", None)
        result.append(
            {
                "id": content.id,
                "title": content.title,
                "category_id": content.category_id,
                "category_name": category_name,
                "content_type": content.content_type,
                "content": content.content,
                "video_url": content.video_url,
                "file_path": content.file_path,
                "cover_image": content.cover_image,
                "author_id": content.author_id,
                "view_count": content.view_count,
                "is_published": content.is_published,
                "published_at": content.published_at,
                "created_at": content.created_at,
                "updated_at": content.updated_at,
            }
        )

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.get("/api/content/contents/{content_id}", response_model=TeachingContentDetail)
async def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取内容详情"""
    content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if current_user.role not in ["teacher", "admin"] and not content.is_published:
        raise HTTPException(status_code=403, detail="无权查看未发布的内容")

    content.view_count += 1
    db.commit()
    db.refresh(content)

    return content


@router.post("/api/content/contents", response_model=TeachingContentResponse)
async def create_content(
    content: TeachingContentCreate,
    current_user: User = Depends(get_content_editor),
    db: Session = Depends(get_db),
):
    """创建内容（教师/管理员）"""
    db_content = TeachingContent(**content.model_dump(), author_id=current_user.id)
    if content.is_published:
        db_content.published_at = datetime.datetime.utcnow()

    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content


@router.put("/api/content/contents/{content_id}", response_model=TeachingContentResponse)
async def update_content(
    content_id: int,
    content_update: TeachingContentUpdate,
    current_user: User = Depends(get_content_editor),
    db: Session = Depends(get_db),
):
    """更新内容（教师/管理员）"""
    db_content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
    if not db_content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if current_user.role != "admin" and db_content.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能编辑自己创建的内容")

    update_data = content_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_content, key, value)

    if update_data.get("is_published") and not db_content.is_published:
        db_content.published_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(db_content)
    return db_content


@router.delete("/api/content/contents/{content_id}")
async def delete_content(
    content_id: int,
    current_user: User = Depends(get_content_editor),
    db: Session = Depends(get_db),
):
    """删除内容（教师/管理员）"""
    db_content = db.query(TeachingContent).filter(TeachingContent.id == content_id).first()
    if not db_content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if current_user.role != "admin" and db_content.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己创建的内容")

    db.delete(db_content)
    db.commit()
    return {"message": "内容已删除"}


@router.post("/api/content/contents/{content_id}/publish")
async def publish_content(
    content_id: int,
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

    return ContentCommentResponse(
        id=db_comment.id,
        content_id=db_comment.content_id,
        student_id=db_comment.student_id,
        student_name=_display_name(current_user),
        student_avatar_url=current_user.avatar_url,
        parent_id=db_comment.parent_id,
        comment=db_comment.comment,
        like_count=0,
        liked=False,
        teacher_reply=db_comment.teacher_reply,
        reply_at=db_comment.reply_at,
        created_at=db_comment.created_at,
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

    return ContentCommentResponse(
        id=db_comment.id,
        content_id=db_comment.content_id,
        student_id=db_comment.student_id,
        student_name=_display_name(current_user),
        student_avatar_url=current_user.avatar_url,
        parent_id=db_comment.parent_id,
        comment=db_comment.comment,
        like_count=0,
        liked=False,
        teacher_reply=db_comment.teacher_reply,
        reply_at=db_comment.reply_at,
        created_at=db_comment.created_at,
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

    return ContentCommentResponse(
        id=db_comment.id,
        content_id=db_comment.content_id,
        student_id=db_comment.student_id,
        student_name=db_comment.student.username if db_comment.student else None,
        comment=db_comment.comment,
        teacher_reply=db_comment.teacher_reply,
        reply_at=db_comment.reply_at,
        created_at=db_comment.created_at,
    )


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
        db.query((db.func.sum(StudentLearningRecord.progress_percent) / db.func.count(StudentLearningRecord)).label("avg"))
        .filter(StudentLearningRecord.progress_percent > 0)
        .first()
    )
    average_progress = avg_progress_result.avg if avg_progress_result and avg_progress_result.avg else 0

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
