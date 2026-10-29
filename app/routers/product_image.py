import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.dependencies import require_vendor_or_admin

from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.user import User


router = APIRouter(
    prefix="/product-images",
    tags=["Product Images"]
)

UPLOAD_DIR = Path("uploads/product_images").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


# --------------------------------------------------
# COMMON HELPERS
# --------------------------------------------------

def get_image_or_404(db: Session, image_id: int):
    image = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id)
        .first()
    )

    if not image:
        raise HTTPException(
            status_code=404,
            detail="Product image not found"
        )

    return image


def serialize_image(image: ProductImage):
    return {
        "id": image.id,
        "product_id": image.product_id,
        "image": image.image,
        "image_url": f"/product-images/{image.id}/file",
    }


def validate_image(file: UploadFile):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid image format: {file.filename}. "
                "Only JPG, JPEG, PNG and WEBP are allowed"
            )
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image file: {file.filename}"
        )

    return extension


def save_uploaded_image(file: UploadFile):
    extension = validate_image(file)
    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename

    try:
        with file_path.open("wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                buffer.write(chunk)

        return file_path

    except OSError:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Unable to save image file"
        )


# --------------------------------------------------
# 1. UPLOAD MULTIPLE PRODUCT IMAGES
# POST /product-images/upload/{product_id}
# Vendor/Admin only
# --------------------------------------------------

@router.post("/upload/{product_id}", status_code=201)
def upload_product_images(
    product_id: int,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(require_vendor_or_admin),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Please select at least one image"
        )

    saved_paths = []

    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        # Validate every file before saving.
        for file in files:
            validate_image(file)

        uploaded_images = []

        for file in files:
            file_path = save_uploaded_image(file)
            saved_paths.append(file_path)

            image = ProductImage(
                product_id=product_id,
                image=file_path.as_posix()
            )

            db.add(image)
            db.flush()

            uploaded_images.append(serialize_image(image))

        db.commit()

        return {
            "message": "Product images uploaded successfully",
            "uploaded_by": {
                "user_id": current_user.id,
                "role_name": current_user.role.name,
            },
            "product_id": product_id,
            "total_images": len(uploaded_images),
            "images": uploaded_images,
        }

    except HTTPException:
        db.rollback()

        for path in saved_paths:
            path.unlink(missing_ok=True)

        raise

    except (SQLAlchemyError, OSError) as exc:
        db.rollback()

        for path in saved_paths:
            path.unlink(missing_ok=True)

        print("PRODUCT IMAGE UPLOAD ERROR:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail="Unable to upload product images"
        )

    finally:
        for file in files:
            file.file.close()


# --------------------------------------------------
# 2. GET ALL PRODUCT IMAGES
# GET /product-images/
# --------------------------------------------------

@router.get("/", status_code=200)
def get_all_product_images(
    db: Session = Depends(get_db)
):
    images = (
        db.query(ProductImage)
        .order_by(ProductImage.id.desc())
        .all()
    )

    return {
        "total_images": len(images),
        "images": [
            serialize_image(image)
            for image in images
        ]
    }


# --------------------------------------------------
# 3. GET IMAGES BY PRODUCT ID
# GET /product-images/product/{product_id}
# --------------------------------------------------

@router.get("/product/{product_id}", status_code=200)
def get_product_images(
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
            status_code=404,
            detail="Product not found"
        )

    images = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id)
        .order_by(ProductImage.id.desc())
        .all()
    )

    return {
        "product_id": product_id,
        "total_images": len(images),
        "images": [
            serialize_image(image)
            for image in images
        ]
    }


# --------------------------------------------------
# 4. VIEW ONE IMAGE FILE
# GET /product-images/{image_id}/file
# --------------------------------------------------

@router.get("/{image_id}/file", status_code=200)
def get_product_image_file(
    image_id: int,
    db: Session = Depends(get_db)
):
    image = get_image_or_404(db, image_id)
    file_path = Path(image.image)

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Image file not found"
        )

    return FileResponse(file_path)


# --------------------------------------------------
# 5. UPDATE / REPLACE PRODUCT IMAGE
# PUT /product-images/{image_id}
# Vendor/Admin only
# --------------------------------------------------

@router.put("/{image_id}", status_code=200)
def update_product_image(
    image_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_vendor_or_admin),
    db: Session = Depends(get_db),
):
    image = get_image_or_404(db, image_id)

    new_path = None
    old_path = Path(image.image)

    try:
        # Validate and save the replacement image.
        validate_image(file)
        new_path = save_uploaded_image(file)

        # Update database with new image path.
        image.image = new_path.as_posix()

        db.commit()
        db.refresh(image)

        # Delete the old image only after successful commit.
        if old_path != new_path:
            old_path.unlink(missing_ok=True)

        return {
            "message": "Product image updated successfully",
            "updated_by": {
                "user_id": current_user.id,
                "role_name": current_user.role.name,
            },
            "data": serialize_image(image),
        }

    except HTTPException:
        if new_path:
            new_path.unlink(missing_ok=True)
        raise

    except (SQLAlchemyError, OSError) as exc:
        db.rollback()

        if new_path:
            new_path.unlink(missing_ok=True)

        print("PRODUCT IMAGE UPDATE ERROR:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail="Unable to update product image"
        )

    finally:
        file.file.close()


# --------------------------------------------------
# 6. DELETE ONE PRODUCT IMAGE
# DELETE /product-images/{image_id}
# Vendor/Admin only
# --------------------------------------------------

@router.delete("/{image_id}", status_code=200)
def delete_product_image(
    image_id: int,
    current_user: User = Depends(require_vendor_or_admin),
    db: Session = Depends(get_db),
):
    image = get_image_or_404(db, image_id)
    file_path = Path(image.image)

    try:
        db.delete(image)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()

        print("PRODUCT IMAGE DELETE ERROR:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail="Unable to delete product image"
        )

    # Delete the physical file after successful DB deletion.
    file_path.unlink(missing_ok=True)

    return {
        "message": "Product image deleted successfully",
        "id": image_id,
        "deleted_by": {
            "user_id": current_user.id,
            "role_name": current_user.role.name,
        },
    }
