from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
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


def get_qa_or_404(db: Session, qa_id: int):
    qa = db.query(ProductQA).filter(
        ProductQA.id == qa_id
    ).first()

    if not qa:
        raise HTTPException(
            status_code=404,
            detail="Product Q&A not found"
        )

    return qa


# 1. CREATE PRODUCT Q&A
@router.post(
    "/",
    response_model=ProductQAResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product_qa(
    data: ProductQACreate,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == data.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    qa = ProductQA(**data.model_dump())

    try:
        db.add(qa)
        db.commit()
        db.refresh(qa)

        return qa

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to create Product Q&A"
        )


# 2. GET ALL PRODUCT Q&A
@router.get(
    "/",
    response_model=list[ProductQAResponse],
    status_code=status.HTTP_200_OK
)
def get_all_product_qa(
    db: Session = Depends(get_db)
):
    return db.query(ProductQA).order_by(
        ProductQA.id.desc()
    ).all()


# 3. GET Q&A BY PRODUCT ID
@router.get(
    "/product/{product_id}",
    response_model=list[ProductQAResponse],
    status_code=status.HTTP_200_OK
)
def get_product_qa_by_product_id(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return db.query(ProductQA).filter(
        ProductQA.product_id == product_id
    ).order_by(
        ProductQA.id.desc()
    ).all()


# 4. GET Q&A BY Q&A ID
# @router.get(
#     "/{qa_id}",
#     response_model=ProductQAResponse,
#     status_code=status.HTTP_200_OK
# )
# def get_product_qa_by_id(
#     qa_id: int,
#     db: Session = Depends(get_db)
# ):
#     return get_qa_or_404(db, qa_id)


# 5. UPDATE PRODUCT Q&A
@router.put(
    "/{qa_id}",
    response_model=ProductQAResponse,
    status_code=status.HTTP_200_OK
)
def update_product_qa(
    qa_id: int,
    data: ProductQAUpdate,
    db: Session = Depends(get_db)
):
    qa = get_qa_or_404(db, qa_id)

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one field to update"
        )

    for field, value in update_data.items():
        setattr(qa, field, value)

    try:
        db.commit()
        db.refresh(qa)

        return qa

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update Product Q&A"
        )


# 6. DELETE PRODUCT Q&A
@router.delete(
    "/{qa_id}",
    status_code=status.HTTP_200_OK
)
def delete_product_qa(
    qa_id: int,
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

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to delete Product Q&A"
        )