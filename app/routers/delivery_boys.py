from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.delivery_boy import DeliveryBoy
from app.models.delivery_area import DeliveryArea

from app.schemas.delivery_boy import (
    DeliveryBoyCreate,
    DeliveryBoyUpdate,
    DeliveryBoyResponse,
)

router = APIRouter(
    prefix="/api/delivery-boys",
    tags=["Delivery Boys"]
)


# 1. CREATE DELIVERY BOY
@router.post(
    "/",
    response_model=DeliveryBoyResponse,
    status_code=status.HTTP_201_CREATED
)
def create_delivery_boy(
    boy_data: DeliveryBoyCreate,
    db: Session = Depends(get_db)
):
    # Check duplicate phone
    existing_boy = (
        db.query(DeliveryBoy)
        .filter(DeliveryBoy.phone == boy_data.phone)
        .first()
    )

    if existing_boy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery boy with this phone number already exists"
        )

    # Check whether delivery area exists
    area = (
        db.query(DeliveryArea)
        .filter(DeliveryArea.id == boy_data.area_id)
        .first()
    )

    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery area not found"
        )

    if not area.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign delivery boy to an inactive area"
        )

    new_boy = DeliveryBoy(
        name=boy_data.name,
        phone=boy_data.phone,
        area_id=boy_data.area_id,
        status=boy_data.status
    )

    db.add(new_boy)
    db.commit()
    db.refresh(new_boy)

    return {
        "id": new_boy.id,
        "name": new_boy.name,
        "phone": new_boy.phone,
        "area_id": new_boy.area_id,
        "area": area.city,
        "status": new_boy.status,
        "created_at": new_boy.created_at,
        "updated_at": new_boy.updated_at
    }


# 2. GET ALL DELIVERY BOYS
@router.get(
    "/",
    response_model=list[DeliveryBoyResponse],
    status_code=status.HTTP_200_OK
)
def get_all_delivery_boys(
    db: Session = Depends(get_db)
):
    boys = (
        db.query(DeliveryBoy)
        .options(joinedload(DeliveryBoy.area))
        .order_by(DeliveryBoy.id.desc())
        .all()
    )

    result = []

    for boy in boys:
        result.append({
            "id": boy.id,
            "name": boy.name,
            "phone": boy.phone,
            "area_id": boy.area_id,
            "area": boy.area.city if boy.area else None,
            "status": boy.status,
            "created_at": boy.created_at,
            "updated_at": boy.updated_at
        })

    return result


# 3. GET DELIVERY BOY BY ID
@router.get(
    "/{boy_id}",
    response_model=DeliveryBoyResponse,
    status_code=status.HTTP_200_OK
)
def get_delivery_boy_by_id(
    boy_id: int,
    db: Session = Depends(get_db)
):
    boy = (
        db.query(DeliveryBoy)
        .options(joinedload(DeliveryBoy.area))
        .filter(DeliveryBoy.id == boy_id)
        .first()
    )

    if not boy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery boy not found"
        )

    return {
        "id": boy.id,
        "name": boy.name,
        "phone": boy.phone,
        "area_id": boy.area_id,
        "area": boy.area.city if boy.area else None,
        "status": boy.status,
        "created_at": boy.created_at,
        "updated_at": boy.updated_at
    }


# 4. UPDATE DELIVERY BOY
@router.put(
    "/{boy_id}",
    response_model=DeliveryBoyResponse,
    status_code=status.HTTP_200_OK
)
def update_delivery_boy(
    boy_id: int,
    boy_data: DeliveryBoyUpdate,
    db: Session = Depends(get_db)
):
    boy = (
        db.query(DeliveryBoy)
        .filter(DeliveryBoy.id == boy_id)
        .first()
    )

    if not boy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery boy not found"
        )

    update_data = boy_data.model_dump(exclude_unset=True)

    # Check duplicate phone if phone is updated
    if "phone" in update_data:
        existing_boy = (
            db.query(DeliveryBoy)
            .filter(
                DeliveryBoy.phone == update_data["phone"],
                DeliveryBoy.id != boy_id
            )
            .first()
        )

        if existing_boy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery boy with this phone number already exists"
            )

    # Validate area if area_id is updated
    if "area_id" in update_data:
        area = (
            db.query(DeliveryArea)
            .filter(DeliveryArea.id == update_data["area_id"])
            .first()
        )

        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery area not found"
            )

        if not area.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign delivery boy to an inactive area"
            )

    for field, value in update_data.items():
        setattr(boy, field, value)

    db.commit()
    db.refresh(boy)

    db.refresh(boy)

    return {
        "id": boy.id,
        "name": boy.name,
        "phone": boy.phone,
        "area_id": boy.area_id,
        "area": boy.area.city if boy.area else None,
        "status": boy.status,
        "created_at": boy.created_at,
        "updated_at": boy.updated_at
    }


# 5. DELETE DELIVERY BOY
@router.delete(
    "/{boy_id}",
    status_code=status.HTTP_200_OK
)
def delete_delivery_boy(
    boy_id: int,
    db: Session = Depends(get_db)
):
    boy = (
        db.query(DeliveryBoy)
        .filter(DeliveryBoy.id == boy_id)
        .first()
    )

    if not boy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery boy not found"
        )

    db.delete(boy)
    db.commit()

    return {
        "message": "Delivery boy deleted successfully",
        "id": boy_id
    }