from sqlalchemy.orm import Session

from app.db.models import UserNotification


def create_notification(
    db: Session,
    *,
    user_id: int,
    notification_type: str,
    title: str,
    content: str | None = None,
    actor_id: int | None = None,
    content_id: int | None = None,
    comment_id: int | None = None,
) -> UserNotification:
    notification = UserNotification(
        user_id=user_id,
        actor_id=actor_id,
        notification_type=notification_type,
        title=title,
        content=content,
        content_id=content_id,
        comment_id=comment_id,
        is_read=False,
    )
    db.add(notification)
    return notification
