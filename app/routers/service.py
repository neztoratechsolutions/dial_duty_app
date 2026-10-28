
import logging
import uuid
from pathlib import Path
from decimal import Decimal
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.service import Service
from app.models.user import User
from app.schemas.service import ServiceResponse
from app.dependencies import get_current_user


router = APIRouter(prefix="/services", tags=["Services"])

UPLOAD_DIR = Path("uploads/services")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def check_super_admin(current_user: User):
    role = current_user.role

    if (
        role is None
        or not role.status
        or (role.name or "").strip().lower()
        not in {"super admin", "super_admin", "superadmin"}
    ):
        raise HTTPException(
            status_code=403,
            detail="Only Super Admin can perform this action",
        )


def get_service_or_404(db: Session, service_id: int):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    return service


async def save_image(image: UploadFile) -> str:
    if not image.filename:
        raise HTTPException(400, "Please select an image")

    extension = Path(image.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG, PNG and WEBP images are allowed",
        )

    content = await image.read()

    if not content:
        raise HTTPException(400, "Image file is empty")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "Image size must not exceed 5 MB")

    signatures = {
        ".jpg": b"\xff\xd8\xff",
        ".jpeg": b"\xff\xd8\xff",
        ".png": b"\x89PNG\r\n\x1a\n",
    }

    if extension in signatures and not content.startswith(signatures[extension]):
        raise HTTPException(400, "Invalid image file")

    if extension == ".webp":
        if not content.startswith(b"RIFF") or content[8:12] != b"WEBP":
            raise HTTPException(400, "Invalid WEBP image")

    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename

    try:
        file_path.write_bytes(content)
    except OSError:
        raise HTTPException(500, "Unable to save image")

    return f"/uploads/services/{filename}"


def delete_image_file(image_path: Optional[str]):
    if not image_path:
        return

    filename = Path(image_path).name
    file_path = (UPLOAD_DIR / filename).resolve()

    # Prevent deleting a file outside the service image directory.
    if file_path.parent != UPLOAD_DIR.resolve():
        return

    try:
        if file_path.is_file():
            file_path.unlink()
    except OSError:
        logging.exception("Unable to delete service image: %s", filename)


def validate_service_values(
    price: Optional[Decimal],
    original_price: Optional[Decimal],
    rating: Optional[Decimal],
    duration_minutes: Optional[int],
    total_reviews: Optional[int],
):
    if price is not None and price < 0:
        raise HTTPException(400, "Price cannot be negative")

    if original_price is not None and original_price < 0:
        raise HTTPException(400, "Original price cannot be negative")

    if rating is not None and not Decimal("0") <= rating <= Decimal("5"):
        raise HTTPException(400, "Rating must be between 0 and 5")

    if duration_minutes is not None and duration_minutes <= 0:
        raise HTTPException(400, "Duration must be greater than zero")

    if total_reviews is not None and total_reviews < 0:
        raise HTTPException(400, "Total reviews cannot be negative")


# CREATE SERVICE
# Only Super Admin can create a service.
@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_service(
    service_name: str = Form(...),
    service_type: str = Form(...),
    duration_minutes: int = Form(...),

    description: Optional[str] = Form(None),
    price: Optional[Decimal] = Form(None),
    original_price: Optional[Decimal] = Form(None),
    rating: Optional[Decimal] = Form(None),
    total_reviews: int = Form(0),
    is_active: bool = Form(True),
    image: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_super_admin(current_user)

    if not service_name.strip():
        raise HTTPException(400, "Service name is required")

    if not service_type.strip():
        raise HTTPException(400, "Service type is required")

    validate_service_values(
        price, original_price, rating, duration_minutes, total_reviews
    )

    image_path = None

    try:
        if image is not None and image.filename:
            image_path = await save_image(image)

        service = Service(
            service_name=service_name.strip(),
            service_type=service_type.strip(),
            duration_minutes=duration_minutes,
            description=description,
            price=price,
            original_price=original_price,
            rating=rating,
            total_reviews=total_reviews,
            is_active=is_active,
            image_url=image_path,
        )

        db.add(service)
        db.commit()
        db.refresh(service)

        return service

    except HTTPException:
        db.rollback()
        delete_image_file(image_path)
        raise

    except Exception:
        db.rollback()
        delete_image_file(image_path)
        logging.exception("Service creation failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to create service",
        )

    finally:
        if image is not None:
            await image.close()


# GET ALL SERVICES
@router.get("/", response_model=list[ServiceResponse])
def get_all_services(db: Session = Depends(get_db)):
    return db.query(Service).order_by(Service.id.desc()).all()


# GET SERVICE BY ID
@router.get("/{service_id}", response_model=ServiceResponse)
def get_service_by_id(
    service_id: int,
    db: Session = Depends(get_db),
):
    return get_service_or_404(db, service_id)


# UPDATE SERVICE
# All update fields are optional.
@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,

    service_name: Optional[str] = Form(None),
    service_type: Optional[str] = Form(None),
    duration_minutes: Optional[int] = Form(None),

    description: Optional[str] = Form(None),
    price: Optional[Decimal] = Form(None),
    original_price: Optional[Decimal] = Form(None),
    rating: Optional[Decimal] = Form(None),
    total_reviews: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_super_admin(current_user)
    service = get_service_or_404(db, service_id)

    if service_name is not None and not service_name.strip():
        raise HTTPException(400, "Service name cannot be empty")

    if service_type is not None and not service_type.strip():
        raise HTTPException(400, "Service type cannot be empty")

    validate_service_values(
        price, original_price, rating, duration_minutes, total_reviews
    )

    old_image_path = service.image_url
    new_image_path = None

    try:
        if image is not None and image.filename:
            new_image_path = await save_image(image)

        update_data = {
            "service_name": service_name.strip() if service_name is not None else None,
            "service_type": service_type.strip() if service_type is not None else None,
            "duration_minutes": duration_minutes,
            "description": description,
            "price": price,
            "original_price": original_price,
            "rating": rating,
            "total_reviews": total_reviews,
            "is_active": is_active,
        }

        for field, value in update_data.items():
            if value is not None:
                setattr(service, field, value)

        if new_image_path:
            service.image_url = new_image_path

        db.commit()
        db.refresh(service)

        if new_image_path:
            delete_image_file(old_image_path)

        return service

    except HTTPException:
        db.rollback()
        delete_image_file(new_image_path)
        raise

    except Exception:
        db.rollback()
        delete_image_file(new_image_path)
        logging.exception("Service update failed for id=%s", service_id)

        raise HTTPException(
            status_code=500,
            detail="Unable to update service",
        )

    finally:
        if image is not None:
            await image.close()


# DELETE SERVICE
@router.delete("/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_super_admin(current_user)
    service = get_service_or_404(db, service_id)
    image_path = service.image_url

    try:
        db.delete(service)
        db.commit()

    except Exception:
        db.rollback()
        logging.exception("Service deletion failed for id=%s", service_id)

        raise HTTPException(
            status_code=500,
            detail="Unable to delete service. Check server logs for details.",
        )

    delete_image_file(image_path)

    return {
        "message": "Service deleted successfully",
        "service_id": service_id,
    }
