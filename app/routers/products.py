import csv
from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database import get_db
from app.dependencies import get_current_user

from app.models.product import Product
from app.models.store import Store
from app.models.category import Category
from app.models.user import User

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["Products"])


# --------------------------------------------------
# COMMON HELPERS
# --------------------------------------------------

def normalize_role(role_name: Optional[str]) -> str:
    return (role_name or "").strip().lower()


def get_role_name(user: Optional[User]) -> Optional[str]:
    if user and user.role:
        return user.role.name
    return None


def role_details(user: Optional[User]) -> dict:
    return {
        "role_id": user.role_id if user else None,
        "role_name": get_role_name(user),
    }


def require_vendor_or_admin(current_user: User):
    role_name = normalize_role(get_role_name(current_user))

    if role_name not in ("vendor", "admin"):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Only Vendor or Admin can access products",
                **role_details(current_user),
            },
        )

    return role_name


def product_query(db: Session):
    return db.query(Product).options(
        joinedload(Product.creator).joinedload(User.role),
        joinedload(Product.updater).joinedload(User.role),
    )


def serialize_product(product: Product) -> dict:
    creator = product.creator
    updater = product.updater

    return {
        "id": product.id,
        "product_name": product.product_name,
        "store_id": product.store_id,
        "category_id": product.category_id,
        "brand": product.brand,
        "price": product.price,
        "stock_quantity": product.stock_quantity,
        "created_by": product.created_by,
        "created_by_role_id": (
            creator.role_id if creator else None
        ),
        "created_by_role_name": (
            get_role_name(creator) if creator else None
        ),
        "updated_by": product.updated_by,
        "updated_by_role_id": (
            updater.role_id if updater else None
        ),
        "updated_by_role_name": (
            get_role_name(updater) if updater else None
        ),
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }


def get_accessible_product(
    db: Session,
    product_id: int,
    current_user: User,
) -> Product:
    current_role = require_vendor_or_admin(current_user)

    product = (
        product_query(db)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    creator_role = normalize_role(
        get_role_name(product.creator)
    )

    # Vendor can access their own products by ID.
    if (
        current_role == "vendor"
        and product.created_by != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Vendor can access only their own product by ID",
                **role_details(current_user),
            },
        )

    # Admin can access products created by Vendor/Admin users.
    if (
        current_role == "admin"
        and creator_role not in ("vendor", "admin")
    ):
        raise HTTPException(
            status_code=403,
            detail="Admin can access only Vendor/Admin products",
        )

    return product


# --------------------------------------------------
# CREATE PRODUCT
# POST /products/
# --------------------------------------------------

@router.post("/", status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_vendor_or_admin(current_user)

    if payload.role_id != current_user.role_id:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "role_id does not match logged-in user's role",
                "request_role_id": payload.role_id,
                **role_details(current_user),
            },
        )

    store = db.query(Store).filter(
        Store.id == payload.store_id
    ).first()

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found",
        )

    category = db.query(Category).filter(
        Category.id == payload.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    product = Product(
        product_name=payload.product_name,
        store_id=payload.store_id,
        category_id=payload.category_id,
        brand=payload.brand,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        # Automatically use the logged-in user's ID.
        created_by=current_user.id,
    )

    try:
        db.add(product)
        db.commit()
        db.refresh(product)

        product = (
            product_query(db)
            .filter(Product.id == product.id)
            .first()
        )

        return {
            "message": "Product created successfully",
            **role_details(current_user),
            "data": serialize_product(product),
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid product data or related ID",
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create product",
        )


# --------------------------------------------------
# GET ALL PRODUCTS
# GET /products/?vendor_id=3
# GET /products/?admin_id=4
# --------------------------------------------------

@router.get("/")
def get_all_products(
    vendor_id: Optional[int] = Query(None, gt=0),
    admin_id: Optional[int] = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_vendor_or_admin(current_user)

    if vendor_id is not None and admin_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either vendor_id or admin_id, not both",
        )

    query = product_query(db)

    # vendor_id is a ROLE ID, not a users.id.
    if vendor_id is not None:
        query = (
            query.join(
                User,
                Product.created_by == User.id,
            )
            .filter(User.role_id == vendor_id)
        )

    # admin_id is a ROLE ID, not a users.id.
    elif admin_id is not None:
        query = (
            query.join(
                User,
                Product.created_by == User.id,
            )
            .filter(User.role_id == admin_id)
        )

    else:
        current_role = normalize_role(
            get_role_name(current_user)
        )

        if current_role == "vendor":
            # No filter: show only the logged-in vendor's products.
            query = query.filter(
                Product.created_by == current_user.id
            )
        else:
            # No filter for admin: show Vendor/Admin-created products.
            query = query.join(
                User,
                Product.created_by == User.id,
            ).filter(
                User.role_id.in_([3, 4])
            )

    total = query.count()

    products = (
        query.order_by(Product.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "message": "Products retrieved successfully",
        **role_details(current_user),
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [serialize_product(p) for p in products],
    }


# --------------------------------------------------
# EXPORT CSV
# GET /products/export/csv?vendor_id=3
# GET /products/export/csv?admin_id=4
# --------------------------------------------------

@router.get("/export/csv")
def export_products_csv(
    vendor_id: Optional[int] = Query(None, gt=0),
    admin_id: Optional[int] = Query(None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_vendor_or_admin(current_user)

    if vendor_id is not None and admin_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either vendor_id or admin_id, not both",
        )

    query = product_query(db)

    if vendor_id is not None:
        query = (
            query.join(
                User,
                Product.created_by == User.id,
            )
            .filter(User.role_id == vendor_id)
        )

    elif admin_id is not None:
        query = (
            query.join(
                User,
                Product.created_by == User.id,
            )
            .filter(User.role_id == admin_id)
        )

    else:
        current_role = normalize_role(
            get_role_name(current_user)
        )

        if current_role == "vendor":
            query = query.filter(
                Product.created_by == current_user.id
            )
        else:
            query = query.join(
                User,
                Product.created_by == User.id,
            ).filter(
                User.role_id.in_([3, 4])
            )

    products = query.order_by(Product.id.desc()).all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Product Name",
        "Store ID",
        "Category ID",
        "Brand",
        "Price",
        "Stock Quantity",
        "Created By",
        "Creator Role ID",
        "Creator Role Name",
        "Updated By",
    ])

    for product in products:
        writer.writerow([
            product.id,
            product.product_name,
            product.store_id,
            product.category_id,
            product.brand or "",
            product.price,
            product.stock_quantity,
            product.created_by,
            product.creator.role_id if product.creator else "",
            get_role_name(product.creator) if product.creator else "",
            product.updated_by or "",
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=products.csv"
        },
    )


# --------------------------------------------------
# GET PRODUCT BY ID
# GET /products/{product_id}
# --------------------------------------------------

@router.get("/{product_id}")
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = get_accessible_product(
        db,
        product_id,
        current_user,
    )

    return {
        "message": "Product retrieved successfully",
        **role_details(current_user),
        "data": serialize_product(product),
    }


# --------------------------------------------------
# UPDATE PRODUCT
# PUT /products/{product_id}
# --------------------------------------------------

@router.put("/{product_id}")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = get_accessible_product(
        db,
        product_id,
        current_user,
    )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one field to update",
        )

    if (
        update_data.get("store_id") is not None
        and "store_id" in update_data
    ):
        store = db.query(Store).filter(
            Store.id == update_data["store_id"]
        ).first()

        if not store:
            raise HTTPException(
                status_code=404,
                detail="Store not found",
            )

    if (
        update_data.get("category_id") is not None
        and "category_id" in update_data
    ):
        category = db.query(Category).filter(
            Category.id == update_data["category_id"]
        ).first()

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found",
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    product.updated_by = current_user.id

    try:
        db.commit()
        db.refresh(product)

        product = (
            product_query(db)
            .filter(Product.id == product_id)
            .first()
        )

        return {
            "message": "Product updated successfully",
            **role_details(current_user),
            "data": serialize_product(product),
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid product data or related ID",
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update product",
        )


# --------------------------------------------------
# DELETE PRODUCT
# DELETE /products/{product_id}
# --------------------------------------------------

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = get_accessible_product(
        db,
        product_id,
        current_user,
    )

    try:
        db.delete(product)
        db.commit()

        return {
            "message": "Product deleted successfully",
            "product_id": product_id,
            **role_details(current_user),
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product because related records exist",
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete product",
        )
