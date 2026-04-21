import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AssignmentBase(BaseModel):
    title: str
    description: str | None = None
    device_id: int | None = None
    class_id: int | None = None
    start_date: datetime.datetime | None = None
    due_date: datetime.datetime | None = None
    requirement: str | None = None
    template: str | None = None
    is_published: bool | None = True


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    device_id: int | None = None
    class_id: int | None = None
    start_date: datetime.datetime | None = None
    due_date: datetime.datetime | None = None
    requirement: str | None = None
    template: str | None = None
    is_published: bool | None = None


class AssignmentResponse(AssignmentBase):
    id: int
    teacher_id: int | None = None
    teacher_name: str | None = None
    device_name: str | None = None
    class_name: str | None = None
    can_manage: bool = False
    can_grade: bool = False
    created_at: datetime.datetime | None = None
    submission_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AssignmentListResponse(BaseModel):
    items: list[AssignmentResponse]
    total: int
    page: int
    page_size: int


class AssignmentSubmissionBase(BaseModel):
    experiment_date: datetime.date | None = None
    observations: str | None = None
    conclusion: str | None = None


class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    temp_records: str | None = None
    humidity_records: str | None = None
    soil_moisture_records: str | None = None
    light_records: str | None = None
    photos: str | None = None


class AssignmentSubmissionSubmit(BaseModel):
    experiment_date: datetime.date | None = None
    observations: str | None = None
    conclusion: str | None = None
    temp_records: str | None = None
    humidity_records: str | None = None
    soil_moisture_records: str | None = None
    light_records: str | None = None
    photos: str | None = None


class AssignmentSubmissionUpdate(BaseModel):
    observations: str | None = None
    conclusion: str | None = None
    temp_records: str | None = None
    humidity_records: str | None = None
    soil_moisture_records: str | None = None
    light_records: str | None = None
    photos: str | None = None


class AssignmentSubmissionGrade(BaseModel):
    score: float
    teacher_comment: str | None = None


class AssignmentPublishRequest(BaseModel):
    is_published: bool


class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    id: int
    assignment_id: int
    student_id: int
    student_name: str | None = None
    status: str
    temp_records: str | None = None
    humidity_records: str | None = None
    soil_moisture_records: str | None = None
    light_records: str | None = None
    photos: str | None = None
    score: float | None = None
    teacher_comment: str | None = None
    report_file_name: str | None = None
    report_file_path: str | None = None
    report_file_size: int | None = None
    graded_at: datetime.datetime | None = None
    submitted_at: datetime.datetime | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentAIFeedbackRequest(BaseModel):
    submission_id: int


class AssignmentAIFeedbackResponse(BaseModel):
    score_band: str
    strengths: list[str]
    improvements: list[str]
    teacher_comment_draft: str
    source: str
    debug_context: dict[str, Any] | None = None
