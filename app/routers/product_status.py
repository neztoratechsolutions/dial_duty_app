from datetime import datetime, timezone
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.dependencies import require_super_admin
from app.models.product import Product
from app.models.user import User


router = APIRouter(
    prefix="/product-approval",
    tags=["Product Approval"]
)


class ProductApprovalRequest(BaseModel):
    product_id: int = Field(gt=0)
    status: Literal["approved", "rejected"]
    rejection_reason: Optional[str] = Field(default=None, max_length=500)


def serialize_product(product: Product):
    return {
        "id": product.id,
        "product_name": product.product_name,
        "store_id": product.store_id,
        "category_id": product.category_id,
        "brand": product.brand,
        "price": product.price,
        "stock_quantity": product.stock_quantity,
        "created_by": product.created_by,
        "approval_status": product.approval_status,
        "approved_by": product.approved_by,
        "approved_at": product.approved_at,
        "rejection_reason": product.rejection_reason,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }


# Get all pending products
@router.get("/pending")
def get_pending_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    products = (
        db.query(Product)
        .filter(Product.approval_status == "pending")
        .order_by(Product.id.desc())
        .all()
    )

    return {
        "message": "Pending products fetched successfully",
        "total": len(products),
        "data": [serialize_product(product) for product in products],
    }


# Single endpoint for approve and reject
@router.post("/update-status")
def update_product_approval_status(
    payload: ProductApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    product = (
        db.query(Product)
        .filter(Product.id == payload.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if product.approval_status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Product is already {product.approval_status}"
        )

    try:
        product.approval_status = payload.status
        product.approved_by = current_user.id

        if payload.status == "approved":
            product.approved_at = datetime.now(timezone.utc)
            product.rejection_reason = None
        else:
            product.approved_at = None
            reason = (
                payload.rejection_reason.strip()
                if payload.rejection_reason
                else None
            )
            product.rejection_reason = reason or None

        db.commit()
        db.refresh(product)

        return {
            "message": f"Product {payload.status} successfully",
            "data": serialize_product(product),
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update product approval status"
        )