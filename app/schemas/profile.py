import datetime

from pydantic import BaseModel, Field

from app.schemas.assignments import AssignmentResponse


class UserTodoStats(BaseModel):
    pending_assignments: int = 0
    overdue_assignments: int = 0
    assignments_to_grade: int = 0
    plants_in_class: int = 0


class UserProfileResponse(BaseModel):
    id: int
    username: str
    role: str
    real_name: str | None = None
    avatar_url: str | None = None
    email: str | None = None
    class_id: int | None = None
    class_name: str | None = None
    todos: UserTodoStats
    upcoming_assignments: list[AssignmentResponse] = []


class UserProfileUpdateRequest(BaseModel):
    real_name: str = Field(min_length=2, max_length=20)


class UserNotificationResponse(BaseModel):
    id: int
    user_id: int
    actor_id: int | None = None
    actor_name: str | None = None
    notification_type: str
    title: str
    content: str | None = None
    content_id: int | None = None
    comment_id: int | None = None
    is_read: bool
    created_at: datetime.datetime


class UserNotificationListResponse(BaseModel):
    items: list[UserNotificationResponse]
    total: int
    page: int
    page_size: int
