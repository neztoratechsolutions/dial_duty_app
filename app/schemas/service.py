
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    service_name: str = Field(..., min_length=1, max_length=150)
    service_type: str | None = Field(default=None, max_length=100)
    description: str
    price: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)
    original_price: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    duration_minutes: int = Field(..., gt=0)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class ServiceUpdate(BaseModel):
    service_name: str | None = Field(default=None, min_length=1, max_length=150)
    service_type: str | None = Field(default=None, max_length=100)
    description: str | None = None
    price: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    original_price: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    duration_minutes: int | None = Field(default=None, gt=0)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ServiceResponse(BaseModel):
    id: int
    service_name: str
    service_type: str | None
    description: str
    price: Decimal
    original_price: Decimal | None
    rating: Decimal | None
    total_reviews: int
    duration_minutes: int
    image_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
