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


class AIConversationMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(..., min_length=1, max_length=500)


class AIScienceAskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=300)
    device_id: Optional[int] = None
    conversation_history: list[AIConversationMessage] = Field(default_factory=list, max_length=12)
    enable_deep_thinking: bool = False
    enable_web_search: bool = False


class AISourceLink(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None


class AIScienceAskResponse(BaseModel):
    answer: str
    source: str
    model: str
    deep_thinking: bool = False
    web_search_enabled: bool = False
    web_search_used: bool = False
    web_search_notice: Optional[str] = None
    citations: list[AISourceLink] = Field(default_factory=list)


class AIConversationCreateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)


class AIConversationRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)


class AIConversationSummaryResponse(BaseModel):
    id: int
    title: str
    is_pinned: bool = False
    pinned_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_message_at: Optional[datetime.datetime] = None
    message_count: int = 0
    preview: Optional[str] = None


class AIConversationMessageResponse(BaseModel):
    id: int
    role: Literal['user', 'assistant']
    content: str
    reasoning: Optional[str] = None
    source: Optional[str] = None
    model: Optional[str] = None
    citations: list[AISourceLink] = Field(default_factory=list)
    web_search_notice: Optional[str] = None
    status: Literal['done', 'error'] = 'done'
    created_at: datetime.datetime


class AIConversationDetailResponse(BaseModel):
    id: int
    title: str
    is_pinned: bool = False
    pinned_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_message_at: Optional[datetime.datetime] = None
    messages: list[AIConversationMessageResponse] = Field(default_factory=list)


class AIConversationAskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=300)
    device_id: Optional[int] = None
    enable_deep_thinking: bool = False
    enable_web_search: bool = False


class AIConversationPinRequest(BaseModel):
    is_pinned: bool


class DemoScenarioRequest(BaseModel):
    scenario: Literal['drought', 'heatwave', 'low_light', 'healthy']


class ExportRequest(BaseModel):
    device_id: int
    start_date: str
    end_date: str
