
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.store import Store
from app.models.category import Category
from app.schemas.store import StoreCreate, StoreUpdate

router = APIRouter(
    prefix="/api/stores",
    tags=["Stores / Warehouses"]
)


def format_store(store: Store):
    return {
        "id": store.id,
        "store_name": store.store_name,
        "category_id": store.category_id,
        "category_name": (
            store.category.name if store.category else None
        ),
        "manager_name": store.manager_name,
        "address": store.address,
        "status": store.status,
        "created_at": store.created_at,
        "updated_at": store.updated_at,
    }


# CREATE STORE
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_store(
    payload: StoreCreate,
    db: Session = Depends(get_db)
):
    try:
        category = (
            db.query(Category)
            .filter(Category.id == payload.category_id)
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found"
            )

        store = Store(
            store_name=payload.store_name,
            category_id=payload.category_id,
            manager_name=payload.manager_name,
            address=payload.address,
            status=payload.status
        )

        db.add(store)
        db.commit()
        db.refresh(store)

        store = (
            db.query(Store)
            .options(joinedload(Store.category))
            .filter(Store.id == store.id)
            .first()
        )

        return {
            "message": "Store created successfully",
            "data": format_store(store)
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as e:
        db.rollback()
        print("STORE CREATE DATABASE ERROR:", repr(e))
        raise HTTPException(
            status_code=400,
            detail=(
                str(e.orig)
                if getattr(e, "orig", None)
                else str(e)
            )
        )

    except Exception as e:
        db.rollback()
        print("STORE CREATE ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while creating store."
        )


# GET ALL STORES
@router.get("/")
def get_all_stores(db: Session = Depends(get_db)):
    stores = (
        db.query(Store)
        .options(joinedload(Store.category))
        .order_by(Store.id.desc())
        .all()
    )

    return {
        "message": "Stores retrieved successfully",
        "total": len(stores),
        "data": [format_store(store) for store in stores]
    }


# GET STORE BY ID
@router.get("/{store_id}")
def get_store_by_id(
    store_id: int,
    db: Session = Depends(get_db)
):
    store = (
        db.query(Store)
        .options(joinedload(Store.category))
        .filter(Store.id == store_id)
        .first()
    )

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )

    return {
        "message": "Store retrieved successfully",
        "data": format_store(store)
    }


# UPDATE STORE
@router.put("/{store_id}")
def update_store(
    store_id: int,
    payload: StoreUpdate,
    db: Session = Depends(get_db)
):
    store = db.query(Store).filter(Store.id == store_id).first()

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "category_id" in update_data:
        category = (
            db.query(Category)
            .filter(Category.id == update_data["category_id"])
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found"
            )

    try:
        for field, value in update_data.items():
            setattr(store, field, value)

        db.commit()
        db.refresh(store)

        store = (
            db.query(Store)
            .options(joinedload(Store.category))
            .filter(Store.id == store_id)
            .first()
        )

        return {
            "message": "Store updated successfully",
            "data": format_store(store)
        }

    except SQLAlchemyError as e:
        db.rollback()
        print("STORE UPDATE DATABASE ERROR:", repr(e))
        raise HTTPException(
            status_code=400,
            detail=(
                str(e.orig)
                if getattr(e, "orig", None)
                else str(e)
            )
        )

    except Exception as e:
        db.rollback()
        print("STORE UPDATE ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while updating store."
        )


# DELETE STORE
@router.delete("/{store_id}")
def delete_store(
    store_id: int,
    db: Session = Depends(get_db)
):
    store = db.query(Store).filter(Store.id == store_id).first()

    if not store:
        raise HTTPException(
            status_code=404,
            detail="Store not found"
        )

    try:
        if store.products or store.coupons:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot delete store because products "
                    "or coupons are linked to it."
                )
            )

        db.delete(store)
        db.commit()

        return {
            "message": "Store deleted successfully",
            "store_id": store_id
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as e:
        db.rollback()
        print("STORE DELETE DATABASE ERROR:", repr(e))
        raise HTTPException(
            status_code=400,
            detail=(
                str(e.orig)
                if getattr(e, "orig", None)
                else str(e)
            )
        )

    except Exception as e:
        db.rollback()
        print("STORE DELETE ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while deleting store."
        )
