
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form, Query
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reel import Reel


router = APIRouter(prefix="/reels", tags=["Reels"])

UPLOAD_DIR = Path("uploads/reels")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


def save_media(file: UploadFile):
    content_type = file.content_type or ""

    if content_type in ALLOWED_IMAGE_TYPES:
        media_type = "image"
    elif content_type in ALLOWED_VIDEO_TYPES:
        media_type = "video"
    else:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPG, PNG, WEBP, MP4, WEBM, or MOV file"
        )

    extension = Path(file.filename or "").suffix.lower()
    if not extension:
        raise HTTPException(status_code=400, detail="File extension is required")

    filename = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename

    size = 0
    try:
        with destination.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File must be 100 MB or smaller"
                    )
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    return media_type, f"/uploads/reels/{filename}", destination


def reel_response(reel: Reel):
    return {
        "id": reel.id,
        "title": reel.title,
        "description": reel.description,
        "media_type": reel.media_type,
        "media_url": reel.media_url,
        "status": reel.status,
        "created_at": reel.created_at,
        "updated_at": reel.updated_at,
    }


@router.post("/", status_code=201)
def create_reel(
    title: str = Form(...),
    description: str | None = Form(None),
    media: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    media_type, media_url, path = save_media(media)

    try:
        reel = Reel(
            title=title,
            description=description,
            media_type=media_type,
            media_url=media_url,
            status="active"
        )
        db.add(reel)
        db.commit()
        db.refresh(reel)
        return reel_response(reel)
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Could not create reel")
    finally:
        media.file.close()


@router.get("/")
def get_reels(
    status: str | None = Query(
        None,
        description="Filter by active or inactive"
    ),
    db: Session = Depends(get_db)
):
    query = db.query(Reel)

    if status is not None:
        status = status.strip().lower()
        if status not in {"active", "inactive"}:
            raise HTTPException(
                status_code=400,
                detail="Status must be active or inactive"
            )
        query = query.filter(Reel.status == status)

    reels = query.order_by(Reel.created_at.desc()).all()
    return [reel_response(reel) for reel in reels]


@router.get("/{reel_id}")
def get_reel(reel_id: int, db: Session = Depends(get_db)):
    reel = db.query(Reel).filter(Reel.id == reel_id).first()

    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")

    return reel_response(reel)


@router.put("/{reel_id}")
def update_reel(
    reel_id: int,
    title: str | None = Form(None),
    description: str | None = Form(None),
    status: str | None = Form(None),
    media: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    reel = db.query(Reel).filter(Reel.id == reel_id).first()

    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")

    if title is not None:
        reel.title = title

    if description is not None:
        reel.description = description

    if status is not None:
        status = status.strip().lower()
        if status not in {"active", "inactive"}:
            raise HTTPException(
                status_code=400,
                detail="Status must be active or inactive"
            )
        reel.status = status

    old_media_path = None
    new_media_path = None

    if media is not None:
        media_type, media_url, new_media_path = save_media(media)
        old_media_url = reel.media_url
        reel.media_type = media_type
        reel.media_url = media_url
        old_media_path = Path(old_media_url.lstrip("/"))

    try:
        db.commit()
        db.refresh(reel)
    except Exception:
        db.rollback()
        if new_media_path:
            new_media_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Could not update reel")
    finally:
        if media is not None:
            media.file.close()

    # Remove the old uploaded file only after the database update succeeds.
    if old_media_path:
        old_media_path.unlink(missing_ok=True)

    return reel_response(reel)


@router.delete("/{reel_id}")
def delete_reel(reel_id: int, db: Session = Depends(get_db)):
    reel = db.query(Reel).filter(Reel.id == reel_id).first()

    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")

    db.delete(reel)
    db.commit()

    file_path = Path(reel.media_url.lstrip("/"))
    file_path.unlink(missing_ok=True)

    return {"message": "Reel deleted successfully"}