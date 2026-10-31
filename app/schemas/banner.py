from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BannerCreate(BaseModel):
    category_id: int
    title: str = Field(..., min_length=1, max_length=150)
    redirect_url: Optional[str] = None


class BannerUpdate(BaseModel):
    title: Optional[str] = None
    redirect_url: Optional[str] = None


class BannerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    title: str
    image: str
    redirect_url: Optional[str]
    created_at: datetime
    updated_at: datetime 
    