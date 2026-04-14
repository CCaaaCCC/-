from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, get_teacher_user
from app.core.permission import can_manage_owned_resource
from app.db.models import Class, Device, GroupMember, StudyGroup, User
from app.schemas.groups import (
    GroupMemberBatchRoleUpdateRequest,
    GroupMemberCreate,
    GroupMemberResponse,
    GroupMigrateRequest,
    GroupMemberUpdate,
    StudyGroupCreate,
    StudyGroupResponse,
    StudyGroupUpdate,
)
from app.services.groups_service import get_groups, get_group_detail

router = APIRouter()


def _ensure_group_manage_permission(group: StudyGroup, current_user: User) -> None:
    if not can_manage_owned_resource(current_user, group.created_by):
        raise HTTPException(status_code=403, detail="仅可修改自己创建的小组")


@router.get("/api/groups")
@router.get("/api/legacy/groups")
async def get_groups_endpoint(
    class_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_groups(db, current_user, class_id)


@router.get("/api/groups/{group_id}")
@router.get("/api/legacy/groups/{group_id}")
async def get_group_detail_endpoint(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_group_detail(db, current_user, group_id)


@router.post("/api/groups", response_model=StudyGroupResponse)
async def create_group(
    group: StudyGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_group = StudyGroup(**group.model_dump(), created_by=current_user.id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return StudyGroupResponse(
        id=db_group.id,
        group_name=db_group.group_name,
        class_id=db_group.class_id,
        class_name=None,
        device_id=db_group.device_id,
        device_name=None,
        description=db_group.description,
        created_by=db_group.created_by,
        can_manage=True,
        member_count=0,
        members=[],
        created_at=db_group.created_at,
    )


@router.post("/api/groups/{group_id}/members", response_model=GroupMemberResponse)
async def add_group_member(
    group_id: int,
    member: GroupMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="小组不存在")
    _ensure_group_manage_permission(group, current_user)

    student = db.query(User).filter(User.id == member.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.student_id == member.student_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该学生已在本小组中")

    db_member = GroupMember(group_id=group_id, student_id=member.student_id, role=member.role)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)

    return GroupMemberResponse(
        id=db_member.id,
        group_id=db_member.group_id,
        student_id=db_member.student_id,
        student_name=student.username,
        role=db_member.role,
        joined_at=db_member.joined_at,
    )


@router.delete("/api/groups/members/{member_id}")
async def remove_group_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="成员不存在")

    group = db.query(StudyGroup).filter(StudyGroup.id == db_member.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="小组不存在")
    _ensure_group_manage_permission(group, current_user)

    db.delete(db_member)
    db.commit()
    return {"message": "成员已移除"}


@router.put("/api/groups/{group_id}", response_model=StudyGroupResponse)
async def update_group(
    group_id: int,
    group_update: StudyGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="小组不存在")
    _ensure_group_manage_permission(db_group, current_user)

    update_data = group_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_group, field, value)

    db.commit()
    db.refresh(db_group)

    members = db.query(GroupMember).filter(GroupMember.group_id == db_group.id).all()
    class_name = None
    if db_group.class_id:
        cls = db.query(Class).filter(Class.id == db_group.class_id).first()
        class_name = cls.class_name if cls else None

    device_name = None
    if db_group.device_id:
        device = db.query(Device).filter(Device.id == db_group.device_id).first()
        device_name = device.device_name if device else None

    member_list = []
    for m in members:
        stu = db.query(User).filter(User.id == m.student_id).first()
        member_list.append(
            {
                "id": m.id,
                "student_id": m.student_id,
                "student_name": stu.username if stu else None,
                "role": m.role,
            }
        )

    return StudyGroupResponse(
        id=db_group.id,
        group_name=db_group.group_name,
        class_id=db_group.class_id,
        class_name=class_name,
        device_id=db_group.device_id,
        device_name=device_name,
        description=db_group.description,
        created_by=db_group.created_by,
        can_manage=can_manage_owned_resource(current_user, db_group.created_by),
        member_count=len(member_list),
        members=member_list,
        created_at=db_group.created_at,
    )


@router.delete("/api/groups/{group_id}")
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="小组不存在")
    _ensure_group_manage_permission(db_group, current_user)

    db.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
    db.delete(db_group)
    db.commit()
    return {"message": "小组已删除"}


@router.put("/api/groups/members/{member_id}", response_model=GroupMemberResponse)
async def update_group_member(
    member_id: int,
    update: GroupMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="成员不存在")

    group = db.query(StudyGroup).filter(StudyGroup.id == db_member.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="小组不存在")
    _ensure_group_manage_permission(group, current_user)

    db_member.role = update.role
    db.commit()
    db.refresh(db_member)

    student = db.query(User).filter(User.id == db_member.student_id).first()
    return GroupMemberResponse(
        id=db_member.id,
        group_id=db_member.group_id,
        student_id=db_member.student_id,
        student_name=student.username if student else None,
        role=db_member.role,
        joined_at=db_member.joined_at,
    )


@router.post("/api/admin/groups/{group_id}/migrate", response_model=StudyGroupResponse)
async def migrate_group(
    group_id: int,
    payload: GroupMigrateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可执行小组迁移")

    db_group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="小组不存在")

    target_class = db.query(Class).filter(Class.id == payload.target_class_id).first()
    if not target_class:
        raise HTTPException(status_code=404, detail="目标班级不存在")

    if payload.target_device_id is not None:
        target_device = db.query(Device).filter(Device.id == payload.target_device_id).first()
        if not target_device:
            raise HTTPException(status_code=404, detail="目标设备不存在")
        db_group.device_id = payload.target_device_id

    db_group.class_id = payload.target_class_id

    db.commit()
    db.refresh(db_group)

    members = db.query(GroupMember).filter(GroupMember.group_id == db_group.id).all()
    member_list = []
    for m in members:
        stu = db.query(User).filter(User.id == m.student_id).first()
        member_list.append(
            {
                "id": m.id,
                "student_id": m.student_id,
                "student_name": (stu.real_name or stu.username) if stu else None,
                "username": stu.username if stu else None,
                "role": m.role,
            }
        )

    return StudyGroupResponse(
        id=db_group.id,
        group_name=db_group.group_name,
        class_id=db_group.class_id,
        class_name=target_class.class_name,
        device_id=db_group.device_id,
        device_name=(db.query(Device).filter(Device.id == db_group.device_id).first().device_name if db_group.device_id else None),
        description=db_group.description,
        created_by=db_group.created_by,
        can_manage=True,
        member_count=len(member_list),
        members=member_list,
        created_at=db_group.created_at,
    )


@router.post("/api/admin/groups/{group_id}/members/batch-role")
async def batch_update_group_member_roles(
    group_id: int,
    payload: GroupMemberBatchRoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可批量修正成员角色")

    db_group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="小组不存在")

    member_ids = [item.member_id for item in payload.updates]
    if not member_ids:
        return {"updated": 0, "group_id": group_id}

    members = db.query(GroupMember).filter(GroupMember.id.in_(member_ids)).all()
    member_map = {m.id: m for m in members}

    for item in payload.updates:
        member = member_map.get(item.member_id)
        if not member or member.group_id != group_id:
            raise HTTPException(status_code=400, detail=f"成员 {item.member_id} 不属于该小组")

    for item in payload.updates:
        member_map[item.member_id].role = item.role

    db.commit()
    return {"updated": len(payload.updates), "group_id": group_id}

