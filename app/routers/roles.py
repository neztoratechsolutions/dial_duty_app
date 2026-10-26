
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database import get_db
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse

router = APIRouter(prefix="/roles", tags=["Roles"])


# CREATE ROLE
@router.post("/", response_model=RoleResponse, status_code=201)
def create_role(
    request: RoleCreate,
    db: Session = Depends(get_db)
):
    name = request.name.strip()

    if len(name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Role name must contain at least 2 characters"
        )

    existing_role = db.query(Role).filter(
        func.lower(Role.name) == name.lower()
    ).first()

    if existing_role:
        raise HTTPException(
            status_code=409,
            detail="Role already exists"
        )

    role = Role(
        name=name,
        description=request.description,
        status=request.status
    )

    try:
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Role already exists"
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to create role"
        )


# GET ALL ROLES
@router.get("/", response_model=list[RoleResponse], status_code=200)
def get_all_roles(
    db: Session = Depends(get_db)
):
    return db.query(Role).order_by(Role.id.desc()).all()


# GET ROLE BY ID
@router.get("/{role_id}", response_model=RoleResponse, status_code=200)
def get_role_by_id(
    role_id: int,
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    return role


# UPDATE ROLE
@router.put("/{role_id}", response_model=RoleResponse, status_code=200)
def update_role(
    role_id: int,
    request: RoleUpdate,
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    update_data = request.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one field to update"
        )

    if "name" in update_data:
        if update_data["name"] is None:
            raise HTTPException(
                status_code=400,
                detail="Role name cannot be null"
            )

        name = update_data["name"].strip()

        if len(name) < 2:
            raise HTTPException(
                status_code=400,
                detail="Role name must contain at least 2 characters"
            )

        existing_role = db.query(Role).filter(
            func.lower(Role.name) == name.lower(),
            Role.id != role_id
        ).first()

        if existing_role:
            raise HTTPException(
                status_code=409,
                detail="Role name already exists"
            )

        update_data["name"] = name

    for field, value in update_data.items():
        setattr(role, field, value)

    try:
        db.commit()
        db.refresh(role)
        return role

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Role update conflicts with existing data"
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update role"
        )


# DELETE ROLE
@router.delete("/{role_id}", status_code=200)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    # Prevent deletion when users are assigned to this role.
    if role.users:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete role because users are assigned to it"
        )

    try:
        db.delete(role)
        db.commit()

        return {
            "message": "Role deleted successfully",
            "role_id": role_id
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete role because related records exist"
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to delete role"
        )
