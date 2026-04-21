from typing import Literal

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: Literal["student", "teacher"]
    invite_code: str
    real_name: str | None = None
    email: str | None = None
    student_id: str | None = None
    teacher_id: str | None = None


class RegisterResponse(BaseModel):
    id: int
    username: str
    role: str
    class_id: int | None = None
    created_by: int | None = None
    message: str
