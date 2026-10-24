from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.delivery_area import DeliveryArea
from app.schemas.delivery_area import (
    DeliveryAreaCreate,
    DeliveryAreaUpdate,
    DeliveryAreaResponse,
)

router = APIRouter(
    prefix="/api/delivery-areas",
    tags=["Delivery Areas"]
)


# 1. CREATE DELIVERY AREA
@router.post(
    "/",
    response_model=DeliveryAreaResponse,
    status_code=status.HTTP_201_CREATED
)
def create_delivery_area(
    area_data: DeliveryAreaCreate,
    db: Session = Depends(get_db)
):
    existing_area = (
        db.query(DeliveryArea)
        .filter(DeliveryArea.pincode == area_data.pincode)
        .first()
    )

    if existing_area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery area with this pincode already exists"
        )

    new_area = DeliveryArea(
        pincode=area_data.pincode,
        city=area_data.city,
        state=area_data.state,
        status=area_data.status
    )

    db.add(new_area)
    db.commit()
    db.refresh(new_area)

    return new_area


# 2. GET ALL DELIVERY AREAS
@router.get(
    "/",
    response_model=list[DeliveryAreaResponse],
    status_code=status.HTTP_200_OK
)
def get_all_delivery_areas(
    db: Session = Depends(get_db)
):
    areas = (
        db.query(DeliveryArea)
        .order_by(DeliveryArea.id.desc())
        .all()
    )

    return areas


# 3. GET DELIVERY AREA BY ID
@router.get(
    "/{area_id}",
    response_model=DeliveryAreaResponse,
    status_code=status.HTTP_200_OK
)
def get_delivery_area_by_id(
    area_id: int,
    db: Session = Depends(get_db)
):
    area = (
        db.query(DeliveryArea)
        .filter(DeliveryArea.id == area_id)
        .first()
    )

    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery area not found"
        )

    return area


# 4. UPDATE DELIVERY AREA
@router.put(
    "/{area_id}",
    response_model=DeliveryAreaResponse,
    status_code=status.HTTP_200_OK
)
def update_delivery_area(
    area_id: int,
    area_data: DeliveryAreaUpdate,
    db: Session = Depends(get_db)
):
    area = (
        db.query(DeliveryArea)
        .filter(DeliveryArea.id == area_id)
        .first()
    )

    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery area not found"
        )

    update_data = area_data.model_dump(exclude_unset=True)

    # Check duplicate pincode if pincode is being updated
    if "pincode" in update_data:
        existing_area = (
            db.query(DeliveryArea)
            .filter(
                DeliveryArea.pincode == update_data["pincode"],
                DeliveryArea.id != area_id
            )
            .first()
        )

        if existing_area:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery area with this pincode already exists"
            )

    for field, value in update_data.items():
        setattr(area, field, value)

    db.commit()
    db.refresh(area)

    return area


# 5. DELETE DELIVERY AREA
@router.delete(
    "/{area_id}",
    status_code=status.HTTP_200_OK
)
def delete_delivery_area(
    area_id: int,
    db: Session = Depends(get_db)
):
    area = (
        db.query(DeliveryArea)
        .filter(DeliveryArea.id == area_id)
        .first()
    )

    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery area not found"
        )

    db.delete(area)
    db.commit()

    return {
        "message": "Delivery area deleted successfully",
        "id": area_id
    }