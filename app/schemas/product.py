from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ProductCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=150)
    store_id: int = Field(..., gt=0)
    category_id: int = Field(..., gt=0)

    brand: Optional[str] = Field(default=None, max_length=100)
    price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)

    created_by: int = Field(..., gt=0)


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    store_id: Optional[int] = Field(default=None, gt=0)
    category_id: Optional[int] = Field(default=None, gt=0)

    brand: Optional[str] = Field(default=None, max_length=100)
    price: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    stock_quantity: Optional[int] = Field(default=None, ge=0)

    updated_by: Optional[int] = Field(default=None, gt=0)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    store_id: int
    category_id: int
    brand: Optional[str] = None
    price: Decimal
    stock_quantity: int
    created_by: int
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None