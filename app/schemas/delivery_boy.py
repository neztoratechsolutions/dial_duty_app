from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DeliveryBoyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    phone: str = Field(..., min_length=10, max_length=20)
    area_id: int
    category_id: int
    status: bool = True


class DeliveryBoyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    area_id: Optional[int] = None
    category_id: Optional[int] = None
    status: Optional[bool] = None


class DeliveryBoyResponse(BaseModel):
    id: int
    name: str
    phone: str
    area_id: int
    area: Optional[str] = None
    category_id: int
    status: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)