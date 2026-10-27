import csv
from io import StringIO
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database import get_db
from app.models.product import Product
from app.models.store import Store
from app.models.category import Category
from app.models.user import User

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)

router = APIRouter(prefix="/products", tags=["Products"])


# -------------------- HELPERS --------------------

def validate_references(
    db: Session,
    store_id=None,
    category_id=None,
    user_id=None,
):
    if store_id is not None:
        if not db.query(Store.id).filter(Store.id == store_id).first():
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID {store_id} not found",
            )

    if category_id is not None:
        if not db.query(Category.id).filter(
            Category.id == category_id
        ).first():
            raise HTTPException(
                status_code=404,
                detail=f"Category with ID {category_id} not found",
            )

    if user_id is not None:
        if not db.query(User.id).filter(User.id == user_id).first():
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found",
            )


def get_product_or_404(db: Session, product_id: int):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


# -------------------- CREATE PRODUCT --------------------

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    request: ProductCreate,
    db: Session = Depends(get_db),
):
    validate_references(
        db,
        store_id=request.store_id,
        category_id=request.category_id,
        user_id=request.created_by,
    )

    product = Product(
        product_name=request.product_name.strip(),
        store_id=request.store_id,
        category_id=request.category_id,
        brand=request.brand,
        price=request.price,
        stock_quantity=request.stock_quantity,
        created_by=request.created_by,
    )

    try:
        db.add(product)
        db.commit()
        db.refresh(product)

        return product

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid product data or database constraint violation",
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to create product",
        )


# -------------------- GET ALL PRODUCTS --------------------

@router.get("/", response_model=list[ProductResponse], status_code=200)
def get_all_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    store_id: int | None = Query(default=None, gt=0),
    category_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    if store_id is not None:
        query = query.filter(Product.store_id == store_id)

    if category_id is not None:
        query = query.filter(Product.category_id == category_id)

    return (
        query.order_by(Product.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# -------------------- GET PRODUCT BY ID --------------------

@router.get("/{product_id}", response_model=ProductResponse, status_code=200)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    return get_product_or_404(db, product_id)


# -------------------- UPDATE PRODUCT --------------------

@router.put("/{product_id}", response_model=ProductResponse, status_code=200)
def update_product(
    product_id: int,
    request: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = get_product_or_404(db, product_id)

    # Only fields sent in the request will be updated.
    update_data = request.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one field to update",
        )

    # Validate only references being changed.
    validate_references(
        db,
        store_id=update_data.get("store_id"),
        category_id=update_data.get("category_id"),
        user_id=update_data.get("updated_by"),
    )

    if "product_name" in update_data:
        if update_data["product_name"] is None:
            raise HTTPException(
                status_code=400,
                detail="Product name cannot be null",
            )

        update_data["product_name"] = update_data["product_name"].strip()

    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)

        return product

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid update data or database constraint violation",
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update product",
        )


# -------------------- DELETE PRODUCT --------------------

@router.delete("/{product_id}", status_code=200)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = get_product_or_404(db, product_id)

    try:
        db.delete(product)
        db.commit()

        return {
            "message": "Product deleted successfully",
            "product_id": product_id,
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
            detail="Unable to delete product",
        )


# -------------------- EXPORT PRODUCTS CSV --------------------

@router.get("/export/csv", status_code=200)
def export_products_csv(
    db: Session = Depends(get_db),
):
    products = (
        db.query(Product)
        .order_by(Product.id.asc())
        .all()
    )

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
        "Updated By",
        "Created At",
        "Updated At",
    ])

    for product in products:
        writer.writerow([
            product.id,
            product.product_name,
            product.store_id,
            product.category_id,
            product.brand or "",
            str(product.price),
            product.stock_quantity,
            product.created_by,
            product.updated_by or "",
            product.created_at.isoformat() if product.created_at else "",
            product.updated_at.isoformat() if product.updated_at else "",
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="products.csv"'
        },
    )