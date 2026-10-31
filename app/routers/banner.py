import os
import shutil
from uuid import uuid4
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user

from app.models.banner import Banner
from app.models.category import Category
from app.models.user import User

from app.schemas.banner import BannerResponse


router = APIRouter(
    prefix="/banners",
    tags=["Banners"]
)


# Image Upload Folder
UPLOAD_DIR = "uploads/banners"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Admin Role -> Category Name
CATEGORY_ADMIN_ROLES = {
    "solar admin": "solar",
    "water admin": "water",
    "battery admin": "battery"
}


# Get Admin Allowed Category
def get_allowed_category(
    current_user: User,
    db: Session
):
    if not current_user.role or not current_user.role.status:
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
            detail="Only Solar Admin, Water Admin and Battery Admin can manage banners"
        )

    category = db.query(Category).filter(
        Category.name.ilike(allowed_category)
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"{allowed_category.title()} category not found"
        )

    return category


# Validate Image
def validate_image(image: UploadFile):

    if not image.filename:
        raise HTTPException(
            status_code=400,
            detail="Image file is required"
        )

    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed"
        )


# Save Image
def save_image(image: UploadFile):

    validate_image(image)

    extension = os.path.splitext(image.filename)[1].lower()

    if extension not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        raise HTTPException(
            status_code=400,
            detail="Allowed image formats: JPG, JPEG, PNG, WEBP, GIF"
        )

    filename = f"{uuid4().hex}{extension}"

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        return file_path.replace("\\", "/")

    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail="Image upload failed"
        )

    finally:
        image.file.close()


# Delete Old Image
def delete_image(image_path: Optional[str]):

    if not image_path:
        return

    normalized_path = os.path.normpath(image_path)

    if (
        os.path.commonpath([
            os.path.abspath(UPLOAD_DIR),
            os.path.abspath(normalized_path)
        ]) == os.path.abspath(UPLOAD_DIR)
        and os.path.isfile(normalized_path)
    ):
        os.remove(normalized_path)


# CREATE BANNER
@router.post(
    "/",
    response_model=BannerResponse,
    status_code=status.HTTP_201_CREATED
)
def create_banner(
    category_id: int = Form(...),
    title: str = Form(...),
    redirect_url: Optional[str] = Form(None),
    image: UploadFile = File(...),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = get_allowed_category(current_user, db)

    if category_id != category.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot create banners for this category"
        )

    image_path = save_image(image)

    try:
        banner = Banner(
            category_id=category.id,
            title=title,
            image=image_path,
            redirect_url=redirect_url
        )

        db.add(banner)
        db.commit()
        db.refresh(banner)

        return banner

    except Exception:
        db.rollback()
        delete_image(image_path)

        raise HTTPException(
            status_code=500,
            detail="Failed to create banner"
        )


# GET ALL BANNERS
@router.get(
    "/",
    response_model=list[BannerResponse],
    status_code=status.HTTP_200_OK
)
def get_all_banners(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = get_allowed_category(current_user, db)

    banners = db.query(Banner).filter(
        Banner.category_id == category.id
    ).order_by(Banner.id.desc()).all()

    return banners


# GET BANNER BY ID
@router.get(
    "/{banner_id}",
    response_model=BannerResponse,
    status_code=status.HTTP_200_OK
)
def get_banner_by_id(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = get_allowed_category(current_user, db)

    banner = db.query(Banner).filter(
        Banner.id == banner_id,
        Banner.category_id == category.id
    ).first()

    if not banner:
        raise HTTPException(
            status_code=404,
            detail="Banner not found"
        )

    return banner


# UPDATE BANNER
@router.put(
    "/{banner_id}",
    response_model=BannerResponse,
    status_code=status.HTTP_200_OK
)
def update_banner(
    banner_id: int,
    title: Optional[str] = Form(None),
    redirect_url: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = get_allowed_category(current_user, db)

    banner = db.query(Banner).filter(
        Banner.id == banner_id,
        Banner.category_id == category.id
    ).first()

    if not banner:
        raise HTTPException(
            status_code=404,
            detail="Banner not found"
        )

    new_image_path = None

    if image is not None:
        new_image_path = save_image(image)

    try:
        old_image_path = banner.image

        if title is not None:
            banner.title = title

        if redirect_url is not None:
            banner.redirect_url = redirect_url

        if new_image_path is not None:
            banner.image = new_image_path

        banner.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(banner)

        if new_image_path is not None:
            delete_image(old_image_path)

        return banner

    except Exception:
        db.rollback()

        if new_image_path:
            delete_image(new_image_path)

        raise HTTPException(
            status_code=500,
            detail="Failed to update banner"
        )


# DELETE BANNER
@router.delete(
    "/{banner_id}",
    status_code=status.HTTP_200_OK
)
def delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = get_allowed_category(current_user, db)

    banner = db.query(Banner).filter(
        Banner.id == banner_id,
        Banner.category_id == category.id
    ).first()

    if not banner:
        raise HTTPException(
            status_code=404,
            detail="Banner not found"
        )

    old_image_path = banner.image

    try:
        db.delete(banner)
        db.commit()

        delete_image(old_image_path)

        return {
            "message": "Banner deleted successfully",
            "banner_id": banner_id
        }

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to delete banner"
        )
