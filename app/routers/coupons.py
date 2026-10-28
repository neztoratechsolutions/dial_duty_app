from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database import get_db
from app.models.coupon import Coupon
from app.models.category import Category
from app.schemas.coupon import (
    CouponCreate,
    CouponUpdate,
    CouponResponse,
)

router = APIRouter(
    prefix="/api/coupons",
    tags=["Coupons"]
)


# CREATE COUPON
@router.post(
    "/",
    response_model=CouponResponse,
    status_code=status.HTTP_201_CREATED
)
def create_coupon(
    coupon_data: CouponCreate,
    db: Session = Depends(get_db)
):
    try:
        # Check duplicate coupon code
        existing_coupon = (
            db.query(Coupon)
            .filter(Coupon.code == coupon_data.code)
            .first()
        )

        if existing_coupon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coupon code already exists"
            )

        # Check category exists
        category = (
            db.query(Category)
            .filter(Category.id == coupon_data.category_id)
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        # Percentage discount cannot exceed 100
        if (
            coupon_data.discount_type == "percentage"
            and coupon_data.discount > 100
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Percentage discount cannot exceed 100"
            )

        # Validate date range
        if (
            coupon_data.start_date
            and coupon_data.end_date
            and coupon_data.end_date < coupon_data.start_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date cannot be earlier than start date"
            )

        # Create coupon without store_id
        new_coupon = Coupon(
            code=coupon_data.code,
            discount=coupon_data.discount,
            discount_type=coupon_data.discount_type,
            start_date=coupon_data.start_date,
            end_date=coupon_data.end_date,
            category_id=coupon_data.category_id,
            status=coupon_data.status
        )

        db.add(new_coupon)
        db.commit()
        db.refresh(new_coupon)

        return new_coupon

    except HTTPException:
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create coupon. Check the provided data."
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating coupon"
        )


# GET ALL COUPONS
@router.get(
    "/",
    response_model=list[CouponResponse],
    status_code=status.HTTP_200_OK
)
def get_all_coupons(
    db: Session = Depends(get_db)
):
    try:
        return (
            db.query(Coupon)
            .order_by(Coupon.id.desc())
            .all()
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching coupons"
        )


# GET COUPON BY ID
@router.get(
    "/{coupon_id}",
    response_model=CouponResponse,
    status_code=status.HTTP_200_OK
)
def get_coupon_by_id(
    coupon_id: int,
    db: Session = Depends(get_db)
):
    coupon = (
        db.query(Coupon)
        .filter(Coupon.id == coupon_id)
        .first()
    )

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )

    return coupon


# UPDATE COUPON
@router.put(
    "/{coupon_id}",
    response_model=CouponResponse,
    status_code=status.HTTP_200_OK
)
def update_coupon(
    coupon_id: int,
    coupon_data: CouponUpdate,
    db: Session = Depends(get_db)
):
    coupon = (
        db.query(Coupon)
        .filter(Coupon.id == coupon_id)
        .first()
    )

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )

    update_data = coupon_data.model_dump(exclude_unset=True)

    # Check duplicate code
    if "code" in update_data:
        existing_coupon = (
            db.query(Coupon)
            .filter(
                Coupon.code == update_data["code"],
                Coupon.id != coupon_id
            )
            .first()
        )

        if existing_coupon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coupon code already exists"
            )

    # Check category exists
    if "category_id" in update_data:
        category = (
            db.query(Category)
            .filter(Category.id == update_data["category_id"])
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # Validate discount
    new_discount_type = update_data.get(
        "discount_type",
        coupon.discount_type
    )
    new_discount = update_data.get(
        "discount",
        coupon.discount
    )

    if (
        new_discount_type == "percentage"
        and new_discount > 100
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Percentage discount cannot exceed 100"
        )

    # Validate date range
    new_start_date = update_data.get(
        "start_date",
        coupon.start_date
    )
    new_end_date = update_data.get(
        "end_date",
        coupon.end_date
    )

    if (
        new_start_date
        and new_end_date
        and new_end_date < new_start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be earlier than start date"
        )

    try:
        for field, value in update_data.items():
            setattr(coupon, field, value)

        db.commit()
        db.refresh(coupon)

        return coupon

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to update coupon. Check the provided data."
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating coupon"
        )


# DELETE COUPON
@router.delete(
    "/{coupon_id}",
    status_code=status.HTTP_200_OK
)
def delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db)
):
    coupon = (
        db.query(Coupon)
        .filter(Coupon.id == coupon_id)
        .first()
    )

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )

    try:
        db.delete(coupon)
        db.commit()

        return {
            "message": "Coupon deleted successfully",
            "id": coupon_id
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while deleting coupon"
        )