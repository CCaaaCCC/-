import datetime
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, get_teacher_user
from app.core.permission import get_allowed_class_ids, get_allowed_group_ids, require_can_access_plant
from app.db.models import Class, Device, GroupMember, GrowthRecord, PlantProfile, StudyGroup, User
from app.schemas.plants import (
    GrowthRecordCreateRequest,
    GrowthRecordResponse,
    PlantProfileCreate,
    PlantProfileResponse,
    PlantProfileUpdate,
)
from app.services.plants_service import create_plant_record, get_plant_records


router = APIRouter(tags=["plants"])

UPLOAD_ROOT = "uploads"
PLANT_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "plants")


@router.get("/api/plants", response_model=list[PlantProfileResponse])
async def get_plants(
    class_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(PlantProfile)

    allowed_class_ids = get_allowed_class_ids(db, current_user)

    if allowed_class_ids is None:
        if class_id is not None:
            group_ids_for_class = [
                r[0] for r in db.query(StudyGroup.id).filter(StudyGroup.class_id == class_id).all()
            ]
            if group_ids_for_class:
                query = query.filter(
                    (PlantProfile.class_id == class_id) | (PlantProfile.group_id.in_(group_ids_for_class))
                )
            else:
                query = query.filter(PlantProfile.class_id == class_id)
    else:
        if not allowed_class_ids:
            return []

        if class_id is not None:
            if class_id not in allowed_class_ids:
                raise HTTPException(status_code=403, detail="无权访问该班级的植物")
            group_ids_for_class = [
                r[0] for r in db.query(StudyGroup.id).filter(StudyGroup.class_id == class_id).all()
            ]
            if group_ids_for_class:
                query = query.filter(
                    (PlantProfile.class_id == class_id) | (PlantProfile.group_id.in_(group_ids_for_class))
                )
            else:
                query = query.filter(PlantProfile.class_id == class_id)
        else:
            allowed_group_ids = get_allowed_group_ids(db, current_user)
            condition = PlantProfile.class_id.in_(allowed_class_ids)
            if allowed_group_ids:
                condition = condition | PlantProfile.group_id.in_(allowed_group_ids)
            query = query.filter(condition)

    if status:
        query = query.filter(PlantProfile.status == status)

    plants = query.order_by(desc(PlantProfile.created_at)).all()
    if not plants:
        return []

    plant_ids = [p.id for p in plants]
    class_ids = {p.class_id for p in plants if p.class_id}
    device_ids = {p.device_id for p in plants if p.device_id}
    group_ids = {p.group_id for p in plants if p.group_id}

    class_map = {}
    device_map = {}
    group_map = {}

    if class_ids:
        class_map = {c.id: c.class_name for c in db.query(Class).filter(Class.id.in_(class_ids)).all()}
    if device_ids:
        device_map = {d.id: d.device_name for d in db.query(Device).filter(Device.id.in_(device_ids)).all()}
    if group_ids:
        group_map = {g.id: g.group_name for g in db.query(StudyGroup).filter(StudyGroup.id.in_(group_ids)).all()}

    record_counts = {
        plant_id: count
        for plant_id, count in db.query(GrowthRecord.plant_id, func.count(GrowthRecord.id))
        .filter(GrowthRecord.plant_id.in_(plant_ids))
        .group_by(GrowthRecord.plant_id)
        .all()
    }

    result = []
    for plant in plants:
        result.append(
            PlantProfileResponse(
                id=plant.id,
                plant_name=plant.plant_name,
                species=plant.species,
                class_id=plant.class_id,
                group_id=plant.group_id,
                device_id=plant.device_id,
                class_name=class_map.get(plant.class_id),
                device_name=device_map.get(plant.device_id),
                group_name=group_map.get(plant.group_id),
                plant_date=plant.plant_date,
                cover_image=plant.cover_image,
                status=plant.status,
                expected_harvest_date=plant.expected_harvest_date,
                description=plant.description,
                growth_record_count=record_counts.get(plant.id, 0),
                created_at=plant.created_at,
            )
        )

    return result


@router.get("/api/plants/{plant_id}", response_model=PlantProfileResponse)
async def get_plant(
    plant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plant = db.query(PlantProfile).filter(PlantProfile.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="植物档案不存在")

    require_can_access_plant(db, current_user, plant)
    return plant


@router.post("/api/plants/upload-image")
async def upload_plant_cover_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_teacher_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持上传图片文件")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise HTTPException(status_code=400, detail="图片格式仅支持 jpg/jpeg/png/webp/gif")

    os.makedirs(PLANT_UPLOAD_DIR, exist_ok=True)
    filename = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(PLANT_UPLOAD_DIR, filename)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    return {"url": f"/uploads/plants/{filename}"}


@router.post("/api/plants", response_model=PlantProfileResponse)
async def create_plant(
    plant: PlantProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_plant = PlantProfile(**plant.model_dump())
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)

    class_name = None
    device_name = None
    group_name = None

    if db_plant.class_id:
        cls = db.query(Class).filter(Class.id == db_plant.class_id).first()
        if cls:
            class_name = cls.class_name

    if db_plant.device_id:
        device = db.query(Device).filter(Device.id == db_plant.device_id).first()
        if device:
            device_name = device.device_name

    if db_plant.group_id:
        group = db.query(StudyGroup).filter(StudyGroup.id == db_plant.group_id).first()
        if group:
            group_name = group.group_name

    record_count = db.query(GrowthRecord).filter(GrowthRecord.plant_id == db_plant.id).count()

    return PlantProfileResponse(
        id=db_plant.id,
        plant_name=db_plant.plant_name,
        species=db_plant.species,
        class_id=db_plant.class_id,
        group_id=db_plant.group_id,
        device_id=db_plant.device_id,
        plant_date=db_plant.plant_date,
        cover_image=db_plant.cover_image,
        status=db_plant.status,
        expected_harvest_date=db_plant.expected_harvest_date,
        description=db_plant.description,
        class_name=class_name,
        device_name=device_name,
        group_name=group_name,
        growth_record_count=record_count,
        created_at=db_plant.created_at,
    )


@router.put("/api/plants/{plant_id}", response_model=PlantProfileResponse)
async def update_plant(
    plant_id: int,
    plant_update: PlantProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_plant = db.query(PlantProfile).filter(PlantProfile.id == plant_id).first()
    if not db_plant:
        raise HTTPException(status_code=404, detail="植物档案不存在")

    update_data = plant_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_plant, key, value)

    db.commit()
    db.refresh(db_plant)

    class_name = None
    device_name = None
    group_name = None

    if db_plant.class_id:
        cls = db.query(Class).filter(Class.id == db_plant.class_id).first()
        if cls:
            class_name = cls.class_name

    if db_plant.device_id:
        device = db.query(Device).filter(Device.id == db_plant.device_id).first()
        if device:
            device_name = device.device_name

    if db_plant.group_id:
        group = db.query(StudyGroup).filter(StudyGroup.id == db_plant.group_id).first()
        if group:
            group_name = group.group_name

    record_count = db.query(GrowthRecord).filter(GrowthRecord.plant_id == db_plant.id).count()

    return PlantProfileResponse(
        id=db_plant.id,
        plant_name=db_plant.plant_name,
        species=db_plant.species,
        class_id=db_plant.class_id,
        group_id=db_plant.group_id,
        device_id=db_plant.device_id,
        plant_date=db_plant.plant_date,
        cover_image=db_plant.cover_image,
        status=db_plant.status,
        expected_harvest_date=db_plant.expected_harvest_date,
        description=db_plant.description,
        class_name=class_name,
        device_name=device_name,
        group_name=group_name,
        growth_record_count=record_count,
        created_at=db_plant.created_at,
    )


@router.delete("/api/plants/{plant_id}")
async def delete_plant(
    plant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_plant = db.query(PlantProfile).filter(PlantProfile.id == plant_id).first()
    if not db_plant:
        raise HTTPException(status_code=404, detail="植物档案不存在")

    db.delete(db_plant)
    db.commit()
    return {"message": "植物档案已删除"}


@router.get("/api/plants/{plant_id}/records", response_model=list[GrowthRecordResponse])
async def get_plant_records_endpoint(
    plant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = get_plant_records(db, current_user, plant_id)
    return [GrowthRecordResponse(**item) for item in records]


@router.post("/api/plants/{plant_id}/records", response_model=GrowthRecordResponse)
async def create_plant_record_endpoint(
    plant_id: int,
    record: GrowthRecordCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    created = create_plant_record(db, current_user, plant_id, record.model_dump())
    return GrowthRecordResponse(**created)


@router.get("/api/legacy/plants/{plant_id}/records", response_model=list[GrowthRecordResponse])
async def get_plant_records_legacy_endpoint(
    plant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = get_plant_records(db, current_user, plant_id)
    return [GrowthRecordResponse(**item) for item in records]


@router.post("/api/legacy/plants/{plant_id}/records", response_model=GrowthRecordResponse)
async def create_plant_record_legacy_endpoint(
    plant_id: int,
    record: GrowthRecordCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    created = create_plant_record(db, current_user, plant_id, record.model_dump())
    return GrowthRecordResponse(**created)


@router.delete("/api/plants/records/{record_id}")
async def delete_plant_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_record = db.query(GrowthRecord).filter(GrowthRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="记录不存在")

    db.delete(db_record)
    db.commit()
    return {"message": "记录已删除"}

