from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from app.core.permission import get_allowed_class_ids
from app.db.models import GroupMember, StudyGroup, User


def _build_group_response(group: StudyGroup, class_name: Optional[str], device_name: Optional[str]) -> Dict[str, Any]:
    member_list: List[Dict[str, Any]] = []
    for member in group.members or []:
        student = getattr(member, "student", None)
        member_list.append(
            {
                "id": member.id,
                "student_id": member.student_id,
                "student_name": getattr(student, "username", None),
                "role": member.role,
            }
        )

    return {
        "id": group.id,
        "group_name": group.group_name,
        "class_id": group.class_id,
        "class_name": class_name,
        "device_id": group.device_id,
        "device_name": device_name,
        "description": group.description,
        "member_count": len(group.members or []),
        "members": member_list,
        "created_at": group.created_at,
    }


def get_groups(
    db: Session,
    current_user: User,
    class_id: Optional[int],
) -> List[Dict[str, Any]]:
    query = db.query(StudyGroup).options(
        selectinload(StudyGroup.members).selectinload(GroupMember.student),
        selectinload(StudyGroup.clas),
        selectinload(StudyGroup.device),
    )

    allowed_class_ids = get_allowed_class_ids(db, current_user)
    if allowed_class_ids is None:
        # admin: optionally filter by class_id
        if class_id is not None:
            query = query.filter(StudyGroup.class_id == class_id)
    else:
        if class_id is not None:
            if class_id not in allowed_class_ids:
                raise HTTPException(status_code=403, detail="无权访问该班级的小组")
            query = query.filter(StudyGroup.class_id == class_id)
        else:
            if not allowed_class_ids:
                return []
            query = query.filter(StudyGroup.class_id.in_(allowed_class_ids))

    groups = query.order_by(StudyGroup.created_at.desc()).all()
    result: List[Dict[str, Any]] = []
    for g in groups:
        class_name = getattr(getattr(g, "clas", None), "class_name", None)
        device_name = getattr(getattr(g, "device", None), "device_name", None)
        result.append(_build_group_response(g, class_name=class_name, device_name=device_name))
    return result


def get_group_detail(db: Session, current_user: User, group_id: int) -> Dict[str, Any]:
    group = (
        db.query(StudyGroup)
        .options(
            selectinload(StudyGroup.members).selectinload(GroupMember.student),
            selectinload(StudyGroup.clas),
            selectinload(StudyGroup.device),
        )
        .filter(StudyGroup.id == group_id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="小组不存在")

    allowed_class_ids = get_allowed_class_ids(db, current_user)
    if allowed_class_ids is not None and group.class_id not in allowed_class_ids:
        raise HTTPException(status_code=403, detail="无权访问该小组")

    class_name = getattr(getattr(group, "clas", None), "class_name", None)
    device_name = getattr(getattr(group, "device", None), "device_name", None)
    return _build_group_response(group, class_name=class_name, device_name=device_name)

