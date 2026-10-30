from datetime import datetime, timezone
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from app.database import get_db
from app.dependencies import get_current_user

from app.models.product import Product
from app.models.category import Category
from app.models.user import User


router = APIRouter(
    prefix="/product-approval",
    tags=["Product Approval"],
)


# Request schema
class ProductApprovalRequest(BaseModel):
    product_id: int = Field(gt=0)

    status: Literal["approved", "rejected"]

    rejection_reason: Optional[str] = Field(
        default=None,
        max_length=500,
    )


# Each category admin can manage only their category
CATEGORY_ADMIN_ROLES = {
    "solar admin": "solar",
    "water admin": "water",
    "battery admin": "battery",
}


# Validate logged-in admin role
def get_allowed_category(current_user: User) -> str:

    if not current_user.role:
        raise HTTPException(
            status_code=403,
            detail="User role not found",
        )

    if not current_user.role.status:
        raise HTTPException(
            status_code=403,
            detail="User role is inactive",
        )

    role_name = (
        current_user.role.name.strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )

    allowed_category = CATEGORY_ADMIN_ROLES.get(role_name)

    if not allowed_category:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only Solar Admin, Water Admin, and Battery Admin "
                "can approve or reject products"
            ),
        )

    return allowed_category


# Convert product object to response
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
        "updated_by": product.updated_by,
        "approval_status": product.approval_status,
        "approved_by": product.approved_by,
        "approved_at": product.approved_at,
        "rejection_reason": product.rejection_reason,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }


# --------------------------------------------------
# 1. GET ALL PENDING PRODUCTS FOR LOGGED-IN CATEGORY
# --------------------------------------------------
@router.get("/pending")
def get_pending_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Allow only Solar Admin, Water Admin, Battery Admin
    allowed_category = get_allowed_category(current_user)

    products = (
        db.query(Product)
        .join(
            Category,
            Product.category_id == Category.id,
        )
        .filter(
            Product.approval_status == "pending",
            func.lower(Category.name) == allowed_category,
        )
        .order_by(Product.id.desc())
        .all()
    )

    return {
        "message": "Pending products fetched successfully",
        "category": allowed_category,
        "total": len(products),
        "data": [
            serialize_product(product)
            for product in products
        ],
    }


# --------------------------------------------------
# 2. APPROVE OR REJECT PRODUCT
# --------------------------------------------------
@router.post("/update-status")
def update_product_approval_status(
    payload: ProductApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Validate role and get authorized category
    allowed_category = get_allowed_category(current_user)

    # Find product only inside authorized category
    product = (
        db.query(Product)
        .join(
            Category,
            Product.category_id == Category.id,
        )
        .filter(
            Product.id == payload.product_id,
            func.lower(Category.name) == allowed_category,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found in your authorized category",
        )

    # Prevent repeated approval/rejection
    if product.approval_status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Product is already {product.approval_status}",
        )

    # Rejection reason validation
    if payload.status == "rejected":
        if not payload.rejection_reason or not payload.rejection_reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required",
            )

    try:

        product.approval_status = payload.status
        product.approved_by = current_user.id

        if payload.status == "approved":

            product.approved_at = datetime.now(timezone.utc)
            product.rejection_reason = None

        else:

            product.approved_at = None
            product.rejection_reason = (
                payload.rejection_reason.strip()
            )

        db.commit()
        db.refresh(product)

        return {
            "message": f"Product {payload.status} successfully",
            "category": allowed_category,
            "data": serialize_product(product),
        }

    except SQLAlchemyError:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to update product approval status",
        )