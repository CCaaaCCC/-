import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ContentCategoryBase(BaseModel):
    name: str
    description: str | None = None
    parent_id: int | None = None
    sort_order: int = 0


class ContentCategoryCreate(ContentCategoryBase):
    pass


class ContentCategoryResponse(ContentCategoryBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class ContentCategoryWithChildren(ContentCategoryResponse):
    children: list[ContentCategoryResponse] = Field(default_factory=list)


class TeachingContentBase(BaseModel):
    title: str
    category_id: int
    content_type: str = "article"
    content: str | None = None
    video_url: str | None = None
    file_path: str | None = None
    cover_image: str | None = None


class TeachingContentCreate(TeachingContentBase):
    is_published: bool = False


class TeachingContentUpdate(BaseModel):
    title: str | None = None
    category_id: int | None = None
    content_type: str | None = None
    content: str | None = None
    video_url: str | None = None
    file_path: str | None = None
    cover_image: str | None = None
    is_published: bool | None = None


class TeachingContentResponse(TeachingContentBase):
    id: int
    author_id: int
    author_name: str | None = None
    author_username: str | None = None
    publisher_name: str | None = None
    view_count: int
    is_published: bool
    published_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    can_edit: bool = False
    can_delete: bool = False
    can_publish: bool = False
    category: ContentCategoryResponse | None = None
    model_config = ConfigDict(from_attributes=True)


class TeachingContentDetail(TeachingContentResponse):
    pass


class StudentLearningRecordCreate(BaseModel):
    status: str = "in_progress"
    progress_percent: int = 0
    time_spent_seconds: int = 0


class StudentLearningRecordResponse(BaseModel):
    id: int
    student_id: int
    content_id: int
    status: str
    progress_percent: int
    time_spent_seconds: int
    last_accessed: datetime.datetime
    completed_at: datetime.datetime | None
    model_config = ConfigDict(from_attributes=True)


class ContentCommentCreate(BaseModel):
    comment: str
    parent_id: int | None = None


class ContentCommentReplyCreate(BaseModel):
    comment: str


class ContentCommentResponse(BaseModel):
    id: int
    content_id: int
    student_id: int
    student_name: str | None = None
    student_avatar_url: str | None = None
    parent_id: int | None = None
    comment: str
    like_count: int = 0
    liked: bool = False
    teacher_reply: str | None = None
    reply_at: datetime.datetime | None = None
    created_at: datetime.datetime
    replies: list["ContentCommentResponse"] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class LearningStats(BaseModel):
    total_students: int
    total_contents: int
    total_learning_records: int
    completed_count: int
    in_progress_count: int
    not_started_count: int
    completion_rate: float
    average_progress: float


class StudentProgress(BaseModel):
    student_id: int
    student_name: str
    total_contents: int
    completed_count: int
    in_progress_count: int
    completion_rate: float
    total_time_spent: int


class ContentCommentLikeResponse(BaseModel):
    comment_id: int
    liked: bool
    like_count: int


class ContentAIPolishRequest(BaseModel):
    bullet_points: str = Field(..., min_length=3)
    mode: Literal["conservative", "expanded", "article"] = "conservative"
    tone: str | None = None
    target_length: str | None = None


class ContentAIPolishResponse(BaseModel):
    title_suggestion: str
    organized_content: str
    source: str


ContentCommentResponse.model_rebuild()
