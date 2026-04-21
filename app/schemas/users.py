import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str
    role: Literal['student', 'teacher', 'admin']
    email: str | None = None
    real_name: str | None = None


class UserCreate(UserBase):
    password: str
    student_id: str | None = None
    teacher_id: str | None = None
    class_id: int | None = None
    is_active: bool = True


class UserUpdate(BaseModel):
    email: str | None = None
    real_name: str | None = None
    student_id: str | None = None
    teacher_id: str | None = None
    class_id: int | None = None
    is_active: bool | None = None
    role: str | None = None


class UserResponse(UserBase):
    id: int
    student_id: str | None = None
    teacher_id: str | None = None
    class_id: int | None = None
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    class_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserImportResult(BaseModel):
    success_count: int
    error_rows: list
    message: str


class ClassBase(BaseModel):
    class_name: str
    grade: str | None = None
    description: str | None = None
    teacher_id: int | None = None


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    class_name: str | None = None
    grade: str | None = None
    description: str | None = None
    teacher_id: int | None = None
    is_active: bool | None = None


class ClassResponse(ClassBase):
    id: int
    invite_code: str | None = None
    is_active: bool
    created_at: datetime.datetime
    teacher_name: str | None = None
    student_count: int = 0
    device_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ClassDeviceBindCreate(BaseModel):
    class_id: int
    device_id: int


class ClassDeviceBindResponse(BaseModel):
    id: int
    class_id: int
    class_name: str
    device_id: int
    device_name: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class UserStats(BaseModel):
    total_users: int
    admin_count: int
    teacher_count: int
    student_count: int
    active_count: int
    inactive_count: int


class BatchDeleteRequest(BaseModel):
    user_ids: list[int]


class BatchUpdateClassRequest(BaseModel):
    user_ids: list[int]
    class_id: int | None = None


class BatchResetPasswordRequest(BaseModel):
    user_ids: list[int]
    new_password: str
