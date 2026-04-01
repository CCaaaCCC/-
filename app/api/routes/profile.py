import datetime
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.models import User, UserNotification
from app.schemas.profile import (
    UserNotificationListResponse,
    UserNotificationResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from app.services.profile_service import get_my_profile

router = APIRouter()

UPLOAD_ROOT = "uploads"
AVATAR_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "avatars")
MAX_AVATAR_SIZE = 2 * 1024 * 1024


@router.get("/api/profile/me", response_model=UserProfileResponse)
@router.get("/api/legacy/profile/me", response_model=UserProfileResponse)
async def get_my_profile_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_my_profile(db, current_user)


@router.patch("/api/profile/me", response_model=UserProfileResponse)
async def update_my_profile_endpoint(
    payload: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    real_name = payload.real_name.strip()
    if len(real_name) < 2 or len(real_name) > 20:
        raise HTTPException(status_code=400, detail="名称长度需在 2-20 字之间")

    current_user.real_name = real_name
    db.commit()
    db.refresh(current_user)
    return get_my_profile(db, current_user)


@router.post("/api/profile/avatar")
async def upload_my_avatar_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持上传图片文件")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="头像格式仅支持 jpg/jpeg/png/webp")

    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="头像大小不能超过 2MB")

    os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)
    filename = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(AVATAR_UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(content)

    current_user.avatar_url = f"/uploads/avatars/{filename}"
    db.commit()

    return {"avatar_url": current_user.avatar_url}


@router.get("/api/notifications", response_model=UserNotificationListResponse)
async def get_my_notifications(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    query = db.query(UserNotification).filter(UserNotification.user_id == current_user.id)
    total = query.count()
    rows = (
        query.order_by(desc(UserNotification.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        UserNotificationResponse(
            id=row.id,
            user_id=row.user_id,
            actor_id=row.actor_id,
            actor_name=row.actor.real_name if row.actor and row.actor.real_name else (row.actor.username if row.actor else None),
            notification_type=row.notification_type,
            title=row.title,
            content=row.content,
            content_id=row.content_id,
            comment_id=row.comment_id,
            is_read=row.is_read,
            created_at=row.created_at,
        )
        for row in rows
    ]

    return UserNotificationListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/api/notifications/unread-count")
async def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        db.query(UserNotification)
        .filter(UserNotification.user_id == current_user.id, UserNotification.is_read == False)
        .count()
    )
    return {"unread_count": count}


@router.post("/api/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(UserNotification)
        .filter(UserNotification.id == notification_id, UserNotification.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="通知不存在")

    if not row.is_read:
        row.is_read = True
        db.commit()

    return {"message": "已标记为已读"}


@router.post("/api/notifications/read-all")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = (
        db.query(UserNotification)
        .filter(UserNotification.user_id == current_user.id, UserNotification.is_read == False)
        .update({UserNotification.is_read: True}, synchronize_session=False)
    )
    db.commit()
    return {"message": "已全部标记为已读", "updated": updated}

