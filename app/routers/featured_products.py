from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.dependencies import get_current_user

from app.models.product import Product
from app.models.category import Category
from app.models.feature_product import FeaturedProduct
from app.models.user import User


router = APIRouter(
    prefix="/featured-products",
    tags=["Featured Products"]
)


# Request schema
class FeaturedProductRequest(BaseModel):
    is_featured: bool


# Category admin permissions
CATEGORY_ADMIN_ROLES = {
    "solar admin": "solar",
    "water admin": "water",
    "battery admin": "battery",
}


# Validate logged-in admin
def get_allowed_category(current_user: User):

    if not current_user.role:
        raise HTTPException(
            status_code=403,
            detail="User role not found"
        )

    if not current_user.role.status:
        raise HTTPException(
            status_code=403,
            detail="User role is inactive"
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
                "Only Solar Admin, Water Admin, and "
                "Battery Admin can manage featured products"
            )
        )

    return allowed_category


# Product response
def serialize_product(product: Product, featured: bool):

    return {
        "id": product.id,
        "product_name": product.product_name,
        "store_id": product.store_id,
        "category_id": product.category_id,
        "brand": product.brand,
        "price": product.price,
        "stock_quantity": product.stock_quantity,
        "approval_status": product.approval_status,
        "is_featured": featured,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }


# Common category product query
def get_category_products(db: Session, category: str):

    return (
        db.query(Product, FeaturedProduct)
        .join(
            Category,
            Product.category_id == Category.id
        )
        .outerjoin(
            FeaturedProduct,
            FeaturedProduct.product_id == Product.id
        )
        .filter(
            func.lower(Category.name) == category,
            Product.approval_status == "approved"
        )
    )


# ------------------------------------------------
# 1. GET ALL APPROVED PRODUCTS WITH FEATURE STATUS
# ------------------------------------------------
@router.get("/")
def get_all_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = get_allowed_category(current_user)

    products = (
        get_category_products(db, category)
        .order_by(Product.id.desc())
        .all()
    )

    data = []

    for product, featured_product in products:

        is_featured = (
            featured_product.is_featured
            if featured_product
            else False
        )

        data.append(
            serialize_product(product, is_featured)
        )

    return {
        "message": "Products fetched successfully",
        "category": category,
        "total": len(data),
        "data": data
    }


# ------------------------------------------------
# 2. GET FEATURED PRODUCTS ONLY
# ------------------------------------------------
@router.get("/featured")
def get_featured_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = get_allowed_category(current_user)

    products = (
        get_category_products(db, category)
        .filter(
            FeaturedProduct.is_featured == True
        )
        .order_by(Product.id.desc())
        .all()
    )

    data = [
        serialize_product(product, True)
        for product, featured_product in products
    ]

    return {
        "message": "Featured products fetched successfully",
        "category": category,
        "total": len(data),
        "data": data
    }


# ------------------------------------------------
# 3. FEATURE / UNFEATURE PRODUCT
# ------------------------------------------------
@router.put("/{product_id}/toggle")
def toggle_featured_product(
    product_id: int,
    payload: FeaturedProductRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Validate admin role and category
    category = get_allowed_category(current_user)

    # Check product belongs to logged-in admin category
    product = (
        db.query(Product)
        .join(
            Category,
            Product.category_id == Category.id
        )
        .filter(
            Product.id == product_id,
            func.lower(Category.name) == category
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found in your authorized category"
        )

    # Only approved products can be featured
    if product.approval_status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Only approved products can be featured"
        )

    try:

        featured_product = (
            db.query(FeaturedProduct)
            .filter(
                FeaturedProduct.product_id == product_id
            )
            .first()
        )

        if featured_product:

            # Update existing record
            featured_product.is_featured = payload.is_featured
            featured_product.featured_by = current_user.id
            featured_product.updated_at = datetime.now(timezone.utc)

        else:

            # Create record only when featuring
            if not payload.is_featured:
                raise HTTPException(
                    status_code=400,
                    detail="Product is already unfeatured"
                )

            featured_product = FeaturedProduct(
                product_id=product_id,
                featured_by=current_user.id,
                is_featured=True
            )

            db.add(featured_product)

        db.commit()
        db.refresh(featured_product)

        return {
            "message": (
                "Product featured successfully"
                if featured_product.is_featured
                else "Product unfeatured successfully"
            ),
            "category": category,
            "data": {
                "id": featured_product.id,
                "product_id": featured_product.product_id,
                "featured_by": featured_product.featured_by,
                "is_featured": featured_product.is_featured,
                "created_at": featured_product.created_at,
                "updated_at": featured_product.updated_at
            }
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to update featured product"
        )