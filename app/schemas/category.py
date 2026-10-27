
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None
    status: bool = True


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)