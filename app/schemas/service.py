
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ServiceResponse(BaseModel):
    id: int
    service_name: str
    service_type: str
    duration_minutes: int

    description: Optional[str] = None
    price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    rating: Optional[Decimal] = None
    total_reviews: int
    image_url: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
