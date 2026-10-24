from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database import get_db
from app.models.admin import StoreAdmin
from app.models.store import Store
from app.schemas.admin import (
    StoreAdminCreate,
    StoreAdminUpdate,
)

router = APIRouter(prefix="/api/admins",tags=["Admin Management"])


def format_admin(admin: StoreAdmin):
    store = admin.store

    return {
        "id": admin.id,
        "name": admin.name,
        "email": admin.email,
        "phone": admin.phone,
        "role": admin.role,
        "store_id": admin.store_id,
        "store_name": store.store_name if store else None,
        "category_name": (
            store.category.name
            if store and store.category
            else None
        ),
        "status": admin.status,
        "created_at": admin.created_at,
        "updated_at": admin.updated_at,
    }


def validate_store(db: Session, store_id: int | None):
    if store_id is None:
        return

    store = db.query(Store).filter(Store.id == store_id).first()

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )


def admin_query(db: Session):
    return db.query(StoreAdmin).options(
        joinedload(StoreAdmin.store).joinedload(Store.category)
    )


# 1. CREATE ADMIN
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: StoreAdminCreate,
    db: Session = Depends(get_db)
):
    validate_store(db, payload.store_id)

    if db.query(StoreAdmin).filter(
        StoreAdmin.email == str(payload.email)
    ).first():
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    if db.query(StoreAdmin).filter(
        StoreAdmin.phone == payload.phone
    ).first():
        raise HTTPException(
            status_code=409,
            detail="Phone number already exists"
        )

    try:
        admin = StoreAdmin(
            name=payload.name,
            email=str(payload.email),
            phone=payload.phone,
            role=payload.role,
            store_id=payload.store_id,
            status=payload.status
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        admin = admin_query(db).filter(
            StoreAdmin.id == admin.id
        ).first()

        return {
            "message": "Admin created successfully",
            "data": format_admin(admin)
        }

    except IntegrityError as e:
        db.rollback()
        print("ADMIN CREATE ERROR:", repr(e))
        raise HTTPException(
            status_code=409,
            detail="Email, phone, or store constraint failed"
        )

    except SQLAlchemyError as e:
        db.rollback()
        print("ADMIN DATABASE ERROR:", repr(e))
        raise HTTPException(
            status_code=400,
            detail="Unable to create admin"
        )


# 2. GET ALL ADMINS
@router.get("/")
def get_all_admins(
    db: Session = Depends(get_db)
):
    admins = admin_query(db).order_by(
        StoreAdmin.id.desc()
    ).all()

    return {
        "message": "Admins retrieved successfully",
        "total": len(admins),
        "data": [format_admin(admin) for admin in admins]
    }


# 3. GET ADMIN BY ID
@router.get("/{admin_id}")
def get_admin_by_id(
    admin_id: int,
    db: Session = Depends(get_db)
):
    admin = admin_query(db).filter(
        StoreAdmin.id == admin_id
    ).first()

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin not found"
        )

    return {
        "message": "Admin retrieved successfully",
        "data": format_admin(admin)
    }


# 4. UPDATE ADMIN
@router.put("/{admin_id}")
def update_admin(
    admin_id: int,
    payload: StoreAdminUpdate,
    db: Session = Depends(get_db)
):
    admin = db.query(StoreAdmin).filter(
        StoreAdmin.id == admin_id
    ).first()

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin not found"
        )

    update_data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    if "store_id" in update_data:
        validate_store(db, update_data["store_id"])

    if "email" in update_data:
        update_data["email"] = str(update_data["email"])

        existing_email = db.query(StoreAdmin).filter(
            StoreAdmin.email == update_data["email"],
            StoreAdmin.id != admin_id
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )

    if "phone" in update_data:
        existing_phone = db.query(StoreAdmin).filter(
            StoreAdmin.phone == update_data["phone"],
            StoreAdmin.id != admin_id
        ).first()

        if existing_phone:
            raise HTTPException(
                status_code=409,
                detail="Phone number already exists"
            )

    try:
        for field, value in update_data.items():
            setattr(admin, field, value)

        db.commit()

        admin = admin_query(db).filter(
            StoreAdmin.id == admin_id
        ).first()

        return {
            "message": "Admin updated successfully",
            "data": format_admin(admin)
        }

    except IntegrityError as e:
        db.rollback()
        print("ADMIN UPDATE ERROR:", repr(e))
        raise HTTPException(
            status_code=409,
            detail="Email, phone, or store constraint failed"
        )

    except SQLAlchemyError as e:
        db.rollback()
        print("ADMIN UPDATE DATABASE ERROR:", repr(e))
        raise HTTPException(
            status_code=400,
            detail="Unable to update admin"
        )


# 5. DELETE ADMIN
@router.delete("/{admin_id}")
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db)
):
    admin = db.query(StoreAdmin).filter(
        StoreAdmin.id == admin_id
    ).first()

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin not found"
        )

    try:
        db.delete(admin)
        db.commit()

        return {
            "message": "Admin deleted successfully",
            "admin_id": admin_id
        }

    except SQLAlchemyError as e:
        db.rollback()
        print("ADMIN DELETE DATABASE ERROR:", repr(e))
        raise HTTPException(
            status_code=400,
            detail="Unable to delete admin"
        )
