
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StoreCreate(BaseModel):
    store_name: str
    category_id: int
    manager_name: str
    address: str
    status: bool = True


class StoreUpdate(BaseModel):
    store_name: Optional[str] = None
    category_id: Optional[int] = None
    manager_name: Optional[str] = None
    address: Optional[str] = None
    status: Optional[bool] = None


class StoreResponse(BaseModel):
    id: int
    store_name: str
    category_id: int
    category_name: Optional[str] = None
    manager_name: str
    address: str
    status: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
