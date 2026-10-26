
from pydantic import BaseModel, Field
from typing import Optional


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    status: bool = True


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None, min_length=2, max_length=50
    )
    description: Optional[str] = None
    status: Optional[bool] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: bool

    class Config:
        from_attributes = True
