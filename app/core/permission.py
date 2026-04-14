from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import (
    Class,
    ClassDeviceBind,
    Device,
    PlantProfile,
    StudyGroup,
    User,
)


def get_allowed_class_ids(db: Session, current_user: User) -> Optional[List[int]]:
    """
    Returns:
    - None: admin => allowed for all classes
    - []: allowed for none (e.g., student without class / teacher without classes)
    - [..ids]: allowed class ids
    """
    if current_user.role == "admin":
        return None

    if current_user.role == "student":
        return [current_user.class_id] if current_user.class_id else []

    if current_user.role == "teacher":
        rows = db.query(Class.id).filter(Class.teacher_id == current_user.id).all()
        return [r[0] for r in rows]

    return []


def get_allowed_device_ids(db: Session, current_user: User) -> Optional[List[int]]:
    allowed_class_ids = get_allowed_class_ids(db, current_user)
    if allowed_class_ids is None:
        return None

    # Compatibility mode: if no class-device binds are configured yet,
    # expose all devices to authenticated non-admin users.
    has_any_bind = db.query(ClassDeviceBind.id).first() is not None
    if not has_any_bind:
        rows = db.query(Device.id).all()
        return [r[0] for r in rows]

    if not allowed_class_ids:
        return []

    rows = (
        db.query(ClassDeviceBind.device_id)
        .filter(ClassDeviceBind.class_id.in_(allowed_class_ids))
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def get_allowed_group_ids(db: Session, current_user: User) -> Optional[List[int]]:
    allowed_class_ids = get_allowed_class_ids(db, current_user)
    if allowed_class_ids is None:
        return None

    if not allowed_class_ids:
        return []

    rows = db.query(StudyGroup.id).filter(StudyGroup.class_id.in_(allowed_class_ids)).all()
    return [r[0] for r in rows]


def resolve_plant_class_id(db: Session, plant: PlantProfile) -> Optional[int]:
    """
    Plants may store either `class_id` or only `group_id`.
    For permission checks we resolve to the owning class.
    """
    if plant.class_id:
        return plant.class_id
    if plant.group_id:
        group = db.query(StudyGroup).filter(StudyGroup.id == plant.group_id).first()
        return group.class_id if group else None
    return None


def require_allowed_class_for_class_id(
    allowed_class_ids: Optional[List[int]],
    class_id: Optional[int],
    detail: str,
) -> None:
    if allowed_class_ids is None:
        return  # admin

    if class_id is None or class_id not in allowed_class_ids:
        raise HTTPException(status_code=403, detail=detail)


def can_manage_owned_resource(current_user: User, owner_id: int | None) -> bool:
    if current_user.role == "admin":
        return True
    if owner_id is None:
        return False
    return owner_id == current_user.id


def require_can_access_plant(db: Session, current_user: User, plant: PlantProfile) -> None:
    if current_user.role in ["admin", "teacher"]:
        return

    allowed_class_ids = get_allowed_class_ids(db, current_user)
    plant_class_id = resolve_plant_class_id(db, plant)
    require_allowed_class_for_class_id(
        allowed_class_ids,
        plant_class_id,
        detail="无权访问该植物所属班级",
    )


def require_can_access_device_history(
    db: Session,
    current_user: User,
    device_id: int,
) -> None:
    allowed_class_ids = get_allowed_class_ids(db, current_user)
    if allowed_class_ids is None:
        return  # admin

    # If no class-device bindings exist, keep telemetry readable in
    # non-configured environments (e.g., fresh demo deployments).
    has_any_bind = db.query(ClassDeviceBind.id).first() is not None
    if not has_any_bind:
        return

    if not allowed_class_ids:
        raise HTTPException(status_code=403, detail="尚未分配班级，无权访问设备历史记录")

    allowed = (
        db.query(ClassDeviceBind.id)
        .filter(
            ClassDeviceBind.device_id == device_id,
            ClassDeviceBind.class_id.in_(allowed_class_ids),
        )
        .first()
        is not None
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="无权访问该设备历史记录（非本班/任教班级设备）")


def require_can_access_group(db: Session, current_user: User, group_id: int) -> StudyGroup:
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="小组不存在")

    allowed_class_ids = get_allowed_class_ids(db, current_user)
    require_allowed_class_for_class_id(
        allowed_class_ids,
        group.class_id,
        detail="无权访问该小组",
    )
    return group

