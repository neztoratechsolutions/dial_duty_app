from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# CREATE DELIVERY AREA
class DeliveryAreaCreate(BaseModel):
    pincode: str = Field(..., min_length=1, max_length=10)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    category_id: int
    status: bool = True


# UPDATE DELIVERY AREA
class DeliveryAreaUpdate(BaseModel):
    pincode: Optional[str] = Field(None, min_length=1, max_length=10)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    category_id: Optional[int] = None
    status: Optional[bool] = None


# DELIVERY AREA RESPONSE
class DeliveryAreaResponse(BaseModel):
    id: int
    pincode: str
    city: str
    state: str
    category_id: int
    status: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
