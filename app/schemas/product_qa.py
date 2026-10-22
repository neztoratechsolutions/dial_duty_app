from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductQACreate(BaseModel):
    product_id: int
    question_en: str = Field(..., min_length=1)
    answer_en: str = Field(..., min_length=1)
    question_ta: Optional[str] = None
    answer_ta: Optional[str] = None


class ProductQAUpdate(BaseModel):
    question_en: Optional[str] = Field(None, min_length=1)
    answer_en: Optional[str] = Field(None, min_length=1)
    question_ta: Optional[str] = None
    answer_ta: Optional[str] = None


class ProductQAResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    question_en: str
    answer_en: str
    question_ta: Optional[str] = None
    answer_ta: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None