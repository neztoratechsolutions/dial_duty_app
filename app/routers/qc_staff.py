from fastapi import APIRouter,HTTPException,status,Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.qc_staff import QCStaff
from app.models.category import Category
from app.schemas.qc_staff import QCStaffCreate,QCStaffResponse,QCStaffUpdate

router = APIRouter(
    prefix="/qc_staff",
    tags=["QC Management"]
)

# POST: Create QC staff for a category

@router.post(
    "",response_model=QCStaffResponse,
    status_code=status.HTTP_201_CREATED
)
def create_qc_staff(
    payload:QCStaffCreate,
    db:Session = Depends(get_db)
):
    category = db.query(Category).filter(
        Category.id == payload.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code= 404,
            detail="Category not found"
        )

    staff = QCStaff(
        name = payload.name.strip(),
        phone=payload.phone.strip(),
        category_id=payload.category_id,
    )

    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


# GET: List QC staff, optionally filtered by category
@router.get(
    "/",
    response_model=list[QCStaffResponse]
)
def get_qc_staff(
    category_id : int,
    db:Session = Depends(get_db)
):
    category = db.query(Category).filter(
        Category.id == category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    return db.query(QCStaff).filter(
        QCStaff.category_id == category_id
    ).order_by(QCStaff.id.desc()).all()

# GET: Get one QC staff member
@router.get(
    "/{staff_id}",
    response_model=QCStaffResponse
)
def get_qc_staff_by_id(
    staff_id : int,
    db:Session = Depends(get_db)
):
    staff = db.query(QCStaff).filter(
        QCStaff.id == staff_id
    ).first()

    if not staff:
        raise HTTPException(
            status_code=404,
            detail="QC staff not found",
        )

    return staff

# PUT: Update QC staff name or phone
@router.put(
    "/{staff_id}",
    response_model=QCStaffResponse,
)
def update_qc_staff(
    staff_id: int,
    payload: QCStaffUpdate,
    db: Session = Depends(get_db),
):
    staff = db.query(QCStaff).filter(
        QCStaff.id == staff_id
    ).first()

    if not staff:
        raise HTTPException(
            status_code=404,
            detail="QC staff not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(staff, field, value)

    db.commit()
    db.refresh(staff)

    return staff


# DELETE: Delete QC staff
@router.delete("/{staff_id}")
def delete_qc_staff(
    staff_id: int,
    db: Session = Depends(get_db),
):
    staff = db.query(QCStaff).filter(
        QCStaff.id == staff_id
    ).first()

    if not staff:
        raise HTTPException(
            status_code=404,
            detail="QC staff not found",
        )

    db.delete(staff)
    db.commit()

    return {"message": "QC staff deleted successfully"}
