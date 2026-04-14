import datetime

from pydantic import BaseModel, ConfigDict


class StudyGroupBase(BaseModel):
    group_name: str
    class_id: int
    device_id: int | None = None
    description: str | None = None


class StudyGroupCreate(StudyGroupBase):
    pass


class StudyGroupUpdate(BaseModel):
    group_name: str | None = None
    class_id: int | None = None
    device_id: int | None = None
    description: str | None = None


class StudyGroupResponse(StudyGroupBase):
    id: int
    class_name: str | None = None
    device_name: str | None = None
    created_by: int | None = None
    can_manage: bool = False
    member_count: int = 0
    members: list[dict] = []
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class GroupMemberBase(BaseModel):
    student_id: int
    role: str


class GroupMemberCreate(GroupMemberBase):
    pass


class GroupMemberUpdate(BaseModel):
    role: str


class GroupMemberResponse(BaseModel):
    id: int
    group_id: int
    student_id: int
    student_name: str | None = None
    role: str
    joined_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class GroupMigrateRequest(BaseModel):
    target_class_id: int
    target_device_id: int | None = None


class GroupMemberRolePatch(BaseModel):
    member_id: int
    role: str


class GroupMemberBatchRoleUpdateRequest(BaseModel):
    updates: list[GroupMemberRolePatch]
