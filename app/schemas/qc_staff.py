
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QCStaffCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    phone: str = Field(..., min_length=1, max_length=20)
    category_id: int = Field(..., gt=0)


class QCStaffUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, min_length=1, max_length=20)


class QCStaffResponse(BaseModel):
    id: int
    name: str
    phone: str
    category_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
