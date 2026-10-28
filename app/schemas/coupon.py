from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict


DiscountType = Literal["percentage", "fixed"]


class CouponCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    discount: Decimal = Field(..., gt=0)
    discount_type: DiscountType = "percentage"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category_id: int
    status: bool = True


class CouponUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    discount: Optional[Decimal] = Field(None, gt=0)
    discount_type: Optional[DiscountType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category_id: Optional[int] = None
    status: Optional[bool] = None


class CouponResponse(BaseModel):
    id: int
    code: str
    discount: Decimal
    discount_type: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category_id: int
    status: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)