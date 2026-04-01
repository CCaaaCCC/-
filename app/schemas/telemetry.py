import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class TelemetryData(BaseModel):
    device_id: int
    temp: float
    humidity: float
    soil_moisture: float
    light: float


class TelemetryResponse(TelemetryData):
    id: int
    timestamp: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class DeviceResponse(BaseModel):
    id: int
    device_name: str
    status: int
    last_seen: Optional[datetime.datetime]
    pump_state: int
    fan_state: int
    light_state: int
    model_config = ConfigDict(from_attributes=True)


class DeviceCreateRequest(BaseModel):
    device_name: str
    status: Optional[int] = 1
    pump_state: Optional[int] = 0
    fan_state: Optional[int] = 0
    light_state: Optional[int] = 0


class ControlRequest(BaseModel):
    pump_state: Optional[int] = None
    fan_state: Optional[int] = None
    light_state: Optional[int] = None


class AIScienceAskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=300)
    device_id: Optional[int] = None


class AIScienceAskResponse(BaseModel):
    answer: str
    source: str


class DemoScenarioRequest(BaseModel):
    scenario: Literal['drought', 'heatwave', 'low_light', 'healthy']


class ExportRequest(BaseModel):
    device_id: int
    start_date: str
    end_date: str
