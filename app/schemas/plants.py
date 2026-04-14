import datetime
from pydantic import BaseModel, ConfigDict


class PlantProfileBase(BaseModel):
    plant_name: str
    species: str | None = None
    class_id: int | None = None
    group_id: int | None = None
    device_id: int | None = None
    plant_date: datetime.date | None = None
    cover_image: str | None = None
    status: str | None = "growing"
    expected_harvest_date: datetime.date | None = None
    description: str | None = None


class PlantProfileCreate(PlantProfileBase):
    pass


class PlantProfileUpdate(BaseModel):
    plant_name: str | None = None
    species: str | None = None
    class_id: int | None = None
    group_id: int | None = None
    device_id: int | None = None
    plant_date: datetime.date | None = None
    cover_image: str | None = None
    status: str | None = None
    expected_harvest_date: datetime.date | None = None
    description: str | None = None


class PlantProfileResponse(PlantProfileBase):
    id: int
    class_name: str | None = None
    device_name: str | None = None
    group_name: str | None = None
    created_by: int | None = None
    can_manage: bool = False
    growth_record_count: int = 0
    created_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class GrowthRecordBase(BaseModel):
    plant_id: int
    record_date: datetime.date
    stage: str | None = None
    height_cm: float | None = None
    leaf_count: int | None = None
    flower_count: int | None = None
    fruit_count: int | None = None
    description: str | None = None
    photos: str | None = None


class GrowthRecordCreateRequest(BaseModel):
    record_date: datetime.date
    stage: str | None = None
    height_cm: float | None = None
    leaf_count: int | None = None
    flower_count: int | None = None
    fruit_count: int | None = None
    description: str | None = None
    photos: str | None = None


class GrowthRecordResponse(GrowthRecordBase):
    id: int
    recorder_name: str | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PlantMigrateRequest(BaseModel):
    target_class_id: int
    target_group_id: int | None = None
    target_device_id: int | None = None
