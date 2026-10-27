
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


AdminRole = Literal["store admin", "team leader", "sub admin"]


class StoreAdminCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    role: AdminRole = "store admin"
    store_id: Optional[int] = None
    status: bool = True


class StoreAdminUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, min_length=10, max_length=20)
    role: Optional[AdminRole] = None
    store_id: Optional[int] = None
    status: Optional[bool] = None


class StoreAdminResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    role: str
    store_id: Optional[int] = None
    store_name: Optional[str] = None
    category_name: Optional[str] = None
    status: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
