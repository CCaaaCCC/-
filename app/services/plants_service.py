from typing import Any, Dict, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.permission import require_can_access_plant
from app.db.models import (
    GrowthRecord,
    GroupMember,
    PlantProfile,
    User,
)


def get_plant_records(db: Session, current_user: User, plant_id: int) -> List[Dict[str, Any]]:
    plant = db.query(PlantProfile).filter(PlantProfile.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="植物档案不存在")

    require_can_access_plant(db, current_user, plant)

    records = (
        db.query(GrowthRecord)
        .filter(GrowthRecord.plant_id == plant_id)
        .order_by(GrowthRecord.record_date.desc())
        .all()
    )

    result: List[Dict[str, Any]] = []
    for record in records:
        recorder_name = None
        if record.recorded_by:
            recorder = db.query(User).filter(User.id == record.recorded_by).first()
            recorder_name = recorder.username if recorder else None

        result.append(
            {
                "id": record.id,
                "plant_id": record.plant_id,
                "record_date": record.record_date.isoformat() if record.record_date else None,
                "stage": record.stage,
                "height_cm": float(record.height_cm) if record.height_cm is not None else None,
                "leaf_count": record.leaf_count,
                "flower_count": record.flower_count,
                "fruit_count": record.fruit_count,
                "description": record.description,
                "photos": record.photos,
                "recorder_name": recorder_name,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
        )
    return result


def create_plant_record(
    db: Session,
    current_user: User,
    plant_id: int,
    record_data: Dict[str, Any],
) -> Dict[str, Any]:
    plant = db.query(PlantProfile).filter(PlantProfile.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="植物档案不存在")

    require_can_access_plant(db, current_user, plant)

    # student: only group members (when group_id exists) can write
    if current_user.role not in ["teacher", "admin"]:
        if plant.group_id:
            member = (
                db.query(GroupMember)
                .filter(
                    GroupMember.group_id == plant.group_id,
                    GroupMember.student_id == current_user.id,
                )
                .first()
            )
            if not member:
                raise HTTPException(status_code=403, detail="无权为该植物添加记录")

    db_record = GrowthRecord(
        **record_data,
        plant_id=plant_id,
        recorded_by=current_user.id,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return {
        "id": db_record.id,
        "plant_id": db_record.plant_id,
        "record_date": db_record.record_date.isoformat() if db_record.record_date else None,
        "stage": db_record.stage,
        "height_cm": float(db_record.height_cm) if db_record.height_cm is not None else None,
        "leaf_count": db_record.leaf_count,
        "flower_count": db_record.flower_count,
        "fruit_count": db_record.fruit_count,
        "description": db_record.description,
        "photos": db_record.photos,
        "recorder_name": current_user.username,
        "created_at": db_record.created_at.isoformat() if db_record.created_at else None,
    }

