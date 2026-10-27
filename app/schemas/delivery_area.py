from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DeliveryAreaCreate(BaseModel):
    pincode: str = Field(..., min_length=1, max_length=10)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    status: bool = True


class DeliveryAreaUpdate(BaseModel):
    pincode: Optional[str] = Field(None, min_length=1, max_length=10)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[bool] = None


class DeliveryAreaResponse(BaseModel):
    id: int
    pincode: str
    city: str
    state: str
    status: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)