from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.dependencies import require_vendor_or_admin

from app.models.product import Product
from app.models.product_qa import ProductQA
from app.schemas.product_qa import (
    ProductQACreate,
    ProductQAUpdate,
    ProductQAResponse,
)


router = APIRouter(
    prefix="/product-qa",
    tags=["Product Q&A"]
)


# --------------------------------------------------
# COMMON HELPER
# --------------------------------------------------

def get_qa_or_404(db: Session, qa_id: int):
    qa = (
        db.query(ProductQA)
        .filter(ProductQA.id == qa_id)
        .first()
    )

    if not qa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product Q&A not found"
        )

    return qa


# --------------------------------------------------
# 1. CREATE PRODUCT Q&A
# POST /product-qa/
# Vendor/Admin only
# --------------------------------------------------

@router.post(
    "/",
    response_model=ProductQAResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product_qa(
    data: ProductQACreate,
    current_user=Depends(require_vendor_or_admin),
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.id == data.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    qa = ProductQA(**data.model_dump())

    try:
        db.add(qa)
        db.commit()
        db.refresh(qa)

        return qa

    except SQLAlchemyError as exc:
        db.rollback()
        print("PRODUCT Q&A CREATE ERROR:", repr(exc))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create Product Q&A"
        )


# --------------------------------------------------
# 2. GET ALL PRODUCT Q&A
# GET /product-qa/
# Public
# --------------------------------------------------

@router.get(
    "/",
    response_model=list[ProductQAResponse],
    status_code=status.HTTP_200_OK
)
def get_all_product_qa(
    db: Session = Depends(get_db)
):
    return (
        db.query(ProductQA)
        .order_by(ProductQA.id.desc())
        .all()
    )


# --------------------------------------------------
# 3. GET Q&A BY PRODUCT ID
# GET /product-qa/product/{product_id}
# Public
# --------------------------------------------------

@router.get(
    "/product/{product_id}",
    response_model=list[ProductQAResponse],
    status_code=status.HTTP_200_OK
)
def get_product_qa_by_product_id(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return (
        db.query(ProductQA)
        .filter(ProductQA.product_id == product_id)
        .order_by(ProductQA.id.desc())
        .all()
    )


# --------------------------------------------------
# 4. GET Q&A BY Q&A ID
# GET /product-qa/{qa_id}
# Public
# --------------------------------------------------

@router.get(
    "/{qa_id}",
    response_model=ProductQAResponse,
    status_code=status.HTTP_200_OK
)
def get_product_qa_by_id(
    qa_id: int,
    db: Session = Depends(get_db)
):
    return get_qa_or_404(db, qa_id)


# --------------------------------------------------
# 5. UPDATE PRODUCT Q&A
# PUT /product-qa/{qa_id}
# Vendor/Admin only
# --------------------------------------------------

@router.put(
    "/{qa_id}",
    response_model=ProductQAResponse,
    status_code=status.HTTP_200_OK
)
def update_product_qa(
    qa_id: int,
    data: ProductQAUpdate,
    current_user=Depends(require_vendor_or_admin),
    db: Session = Depends(get_db)
):
    qa = get_qa_or_404(db, qa_id)

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least one field to update"
        )

    # If product_id is being changed, verify that the product exists.
    if (
        "product_id" in update_data
        and update_data["product_id"] is not None
    ):
        product = (
            db.query(Product)
            .filter(Product.id == update_data["product_id"])
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

    try:
        for field, value in update_data.items():
            setattr(qa, field, value)

        db.commit()
        db.refresh(qa)

        return qa

    except SQLAlchemyError as exc:
        db.rollback()
        print("PRODUCT Q&A UPDATE ERROR:", repr(exc))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update Product Q&A"
        )


# --------------------------------------------------
# 6. DELETE PRODUCT Q&A
# DELETE /product-qa/{qa_id}
# Vendor/Admin only
# --------------------------------------------------

@router.delete(
    "/{qa_id}",
    status_code=status.HTTP_200_OK
)
def delete_product_qa(
    qa_id: int,
    current_user=Depends(require_vendor_or_admin),
    db: Session = Depends(get_db)
):
    qa = get_qa_or_404(db, qa_id)

    try:
        db.delete(qa)
        db.commit()

        return {
            "message": "Product Q&A deleted successfully",
            "id": qa_id
        }

    except SQLAlchemyError as exc:
        db.rollback()
        print("PRODUCT Q&A DELETE ERROR:", repr(exc))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete Product Q&A"
        )