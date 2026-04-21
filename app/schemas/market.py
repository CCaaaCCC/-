import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MarketProductBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    price: Decimal | None = None
    location: str = Field(..., min_length=2, max_length=255)
    contact_info: str = Field(..., min_length=2, max_length=255)
    image_url: str | None = None


class MarketProductCreate(MarketProductBase):
    status: str = "on_sale"


class MarketProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    price: Decimal | None = None
    location: str | None = None
    contact_info: str | None = None
    image_url: str | None = None
    status: str | None = None


class MarketProductResponse(MarketProductBase):
    id: int
    seller_id: int
    seller_name: str | None = None
    status: str
    view_count: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    can_edit: bool = False
    can_delete: bool = False

    model_config = ConfigDict(from_attributes=True)


class MarketProductListResponse(BaseModel):
    items: list[MarketProductResponse]
    total: int
    page: int
    page_size: int
