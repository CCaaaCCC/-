from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, get_teacher_user
from app.db.models import Class, Device, GroupMember, StudyGroup, User
from app.schemas.groups import (
    GroupMemberCreate,
    GroupMemberResponse,
    GroupMemberUpdate,
    StudyGroupCreate,
    StudyGroupResponse,
    StudyGroupUpdate,
)
from app.services.groups_service import get_groups, get_group_detail

router = APIRouter()


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
    db_group = StudyGroup(**group.model_dump())
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

