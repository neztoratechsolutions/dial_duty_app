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
from app.models.product import Product
from app.models.product_image import ProductImage


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


def get_image_or_404(db: Session, image_id: int):
    image = db.query(ProductImage).filter(
        ProductImage.id == image_id
    ).first()

    if not image:
        raise HTTPException(
            status_code=404,
            detail="Product image not found"
        )

    return image


# 1. UPLOAD MULTIPLE IMAGES FOR A PRODUCT
@router.post("/upload/{product_id}", status_code=201)
def upload_product_images(
    product_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Please select at least one image"
        )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        for file in files:
            file.file.close()

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Validate all files before saving
    for file in files:
        extension = Path(file.filename or "").suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            for uploaded_file in files:
                uploaded_file.file.close()

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid image format: {file.filename}. "
                    "Only JPG, JPEG, PNG and WEBP are allowed"
                )
            )

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            for uploaded_file in files:
                uploaded_file.file.close()

            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {file.filename}"
            )

    saved_paths = []
    uploaded_images = []

    try:
        for file in files:
            extension = Path(file.filename or "").suffix.lower()
            filename = f"{uuid.uuid4().hex}{extension}"
            file_path = UPLOAD_DIR / filename

            with file_path.open("wb") as buffer:
                while True:
                    chunk = file.file.read(1024 * 1024)

                    if not chunk:
                        break

                    buffer.write(chunk)

            saved_paths.append(file_path)

            image = ProductImage(
                product_id=product_id,
                image=file_path.as_posix()
            )

            db.add(image)
            db.flush()

            uploaded_images.append({
                "id": image.id,
                "product_id": image.product_id,
                "image": image.image,
                "image_url": (
                    f"/product-images/{image.id}/file"
                )
            })

        db.commit()

        return {
            "message": "Product images uploaded successfully",
            "product_id": product_id,
            "total_images": len(uploaded_images),
            "images": uploaded_images
        }

    except (SQLAlchemyError, OSError):
        db.rollback()

        for path in saved_paths:
            path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Unable to upload product images"
        )

    finally:
        for file in files:
            file.file.close()


# 2. GET ALL PRODUCT IMAGES
@router.get("/", status_code=200)
def get_all_product_images(
    db: Session = Depends(get_db)
):
    images = db.query(ProductImage).order_by(
        ProductImage.id.desc()
    ).all()

    return {
        "total_images": len(images),
        "images": [
            {
                "id": image.id,
                "product_id": image.product_id,
                "image": image.image,
                "image_url": (
                    f"/product-images/{image.id}/file"
                )
            }
            for image in images
        ]
    }


# 3. GET IMAGES BY PRODUCT ID
@router.get("/product/{product_id}", status_code=200)
def get_product_images(
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

    images = db.query(ProductImage).filter(
        ProductImage.product_id == product_id
    ).order_by(ProductImage.id.desc()).all()

    return {
        "product_id": product_id,
        "total_images": len(images),
        "images": [
            {
                "id": image.id,
                "product_id": image.product_id,
                "image": image.image,
                "image_url": (
                    f"/product-images/{image.id}/file"
                )
            }
            for image in images
        ]
    }


# # 4. GET / VIEW ONE IMAGE FILE
# @router.get("/{image_id}/file", status_code=200)
# def get_product_image_file(
#     image_id: int,
#     db: Session = Depends(get_db)
# ):
#     image = get_image_or_404(db, image_id)
#     file_path = Path(image.image)

#     if not file_path.is_file():
#         raise HTTPException(
#             status_code=404,
#             detail="Image file not found"
#         )

#     return FileResponse(file_path)


# 5. DELETE ONE PRODUCT IMAGE
@router.delete("/{image_id}", status_code=200)
def delete_product_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    image = get_image_or_404(db, image_id)
    file_path = Path(image.image)

    try:
        db.delete(image)
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to delete product image"
        )

    file_path.unlink(missing_ok=True)

    return {
        "message": "Product image deleted successfully",
        "id": image_id
    }
