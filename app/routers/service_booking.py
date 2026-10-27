
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    File,
    Form,
    status,
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.user import User
from app.models.service import Service
from app.models.service_booking import ServiceBooking
from app.schemas.service_booking import (
    ServiceBookingUpdate,
    ServiceBookingResponse,
)


router = APIRouter(
    prefix="/service-bookings",
    tags=["Service Bookings"],
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

UPLOAD_DIR = Path("uploads/service_bookings")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_BOOKING_STATUSES = {
    "Pending",
    "Confirmed",
    "Completed",
    "Cancelled",
}


# --------------------------------------------------
# CUSTOMER ROLE VALIDATION
# --------------------------------------------------

def verify_customer(db: Session, customer_id: int):
    customer = (
        db.query(User)
        .filter(User.id == customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    if not customer.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can book services",
        )

    role_name = (customer.role.name or "").strip().lower()

    if role_name != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can book services",
        )

    return customer


# --------------------------------------------------
# SAVE UPLOADED PHOTO
# --------------------------------------------------

def save_uploaded_photo(photo: UploadFile) -> Optional[str]:
    if not photo or not photo.filename:
        return None

    extension = Path(photo.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        photo.file.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, JPEG, PNG, and WEBP images are allowed",
        )

    if photo.content_type not in ALLOWED_CONTENT_TYPES:
        photo.file.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image content type",
        )

    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename
    total_size = 0

    try:
        with file_path.open("wb") as buffer:
            while True:
                chunk = photo.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Image size must not exceed 5 MB",
                    )

                buffer.write(chunk)

    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise

    except OSError:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded image",
        )

    finally:
        photo.file.close()

    return file_path.as_posix()


# --------------------------------------------------
# 1. CREATE SERVICE BOOKING
# --------------------------------------------------

@router.post(
    "/",
    response_model=ServiceBookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service_booking(
    customer_id: int = Form(..., gt=0),
    service_id: int = Form(..., gt=0),
    issue_description: str = Form(..., min_length=1),
    warranty_number: Optional[str] = Form(None),
    issue_photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # Only users with Customer role can book
    verify_customer(db, customer_id)

    # Check that service exists and is active
    service = (
        db.query(Service)
        .filter(
            Service.id == service_id,
            Service.is_active.is_(True),
        )
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or inactive",
        )

    issue_description = issue_description.strip()

    if not issue_description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Issue description is required",
        )

    if warranty_number is not None:
        warranty_number = warranty_number.strip() or None

    saved_photo_path = None

    try:
        if issue_photo and issue_photo.filename:
            saved_photo_path = save_uploaded_photo(issue_photo)

        booking = ServiceBooking(
            customer_id=customer_id,
            service_id=service_id,
            warranty_number=warranty_number,
            issue_photo=saved_photo_path,
            issue_description=issue_description,
            booking_status="Pending",
        )

        db.add(booking)
        db.commit()
        db.refresh(booking)

        return booking

    except HTTPException:
        db.rollback()

        if saved_photo_path:
            Path(saved_photo_path).unlink(missing_ok=True)

        raise

    except SQLAlchemyError:
        db.rollback()

        if saved_photo_path:
            Path(saved_photo_path).unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create service booking",
        )


# --------------------------------------------------
# 2. GET ALL SERVICE BOOKINGS
# --------------------------------------------------

@router.get(
    "/",
    response_model=List[ServiceBookingResponse],
)
def get_all_service_bookings(
    customer_id: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    query = db.query(ServiceBooking)

    if customer_id is not None:
        verify_customer(db, customer_id)

        query = query.filter(
            ServiceBooking.customer_id == customer_id
        )

    return query.order_by(
        ServiceBooking.id.desc()
    ).all()


# --------------------------------------------------
# 3. GET SERVICE BOOKING BY ID
# --------------------------------------------------

@router.get(
    "/{booking_id}",
    response_model=ServiceBookingResponse,
)
def get_service_booking_by_id(
    booking_id: int,
    db: Session = Depends(get_db),
):
    booking = (
        db.query(ServiceBooking)
        .filter(ServiceBooking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    return booking


# --------------------------------------------------
# 4. UPDATE SERVICE BOOKING
# --------------------------------------------------

@router.put(
    "/{booking_id}",
    response_model=ServiceBookingResponse,
)
def update_service_booking(
    booking_id: int,
    booking_data: ServiceBookingUpdate,
    db: Session = Depends(get_db),
):
    booking = (
        db.query(ServiceBooking)
        .filter(ServiceBooking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    update_data = booking_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required to update",
        )

    if "issue_description" in update_data:
        description = update_data["issue_description"]

        if description is not None:
            description = description.strip()

            if not description:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Issue description cannot be empty",
                )

            update_data["issue_description"] = description

    if "warranty_number" in update_data:
        warranty_number = update_data["warranty_number"]

        if warranty_number is not None:
            update_data["warranty_number"] = (
                warranty_number.strip() or None
            )

    if "booking_status" in update_data:
        booking_status = update_data["booking_status"]

        if booking_status not in ALLOWED_BOOKING_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid booking status. Allowed values: "
                    "Pending, Confirmed, Completed, Cancelled"
                ),
            )

    for field, value in update_data.items():
        setattr(booking, field, value)

    try:
        db.commit()
        db.refresh(booking)

        return booking

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update service booking",
        )


# --------------------------------------------------
# 5. DELETE SERVICE BOOKING
# --------------------------------------------------

@router.delete("/{booking_id}")
def delete_service_booking(
    booking_id: int,
    db: Session = Depends(get_db),
):
    booking = (
        db.query(ServiceBooking)
        .filter(ServiceBooking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    photo_path = booking.issue_photo

    try:
        db.delete(booking)
        db.commit()

        if photo_path:
            Path(photo_path).unlink(missing_ok=True)

        return {
            "message": "Service booking deleted successfully",
            "booking_id": booking_id,
        }

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete service booking",
        )
