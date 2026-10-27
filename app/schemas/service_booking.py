from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ServiceBookingUpdate(BaseModel):
    warranty_number: Optional[str] = None
    issue_description: Optional[str] = Field(
        default=None,
        min_length=1,
    )
    booking_status: Optional[str] = None


class ServiceBookingResponse(BaseModel):
    id: int
    customer_id: int
    service_id: int
    warranty_number: Optional[str] = None
    issue_photo: Optional[str] = None
    issue_description: str
    booking_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)