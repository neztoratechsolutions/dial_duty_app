from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.service import Service
from app.schemas.service import ServiceCreate,ServiceResponse,ServiceUpdate

router = APIRouter(
    prefix="/service",
    tags=["Service"],
)

# GET: Get all services
@router.get("/",response_model=list[ServiceResponse])
def get_services(
    include_inactive : bool = False,
    db:Session = Depends(get_db)
):
    query = db.query(Service)

    if not include_inactive:
        query = query.filter(Service.is_active.is_(True))

    return query.order_by(Service.id.desc()).all()

# GET: Get one service by ID
@router.get(
    "/{service_id}",
    response_model=ServiceResponse
)
def get_service(
    service_id : int,
    db:Session = Depends(get_db)
):
    service = db.query(Service).filter(
        Service.id == service_id
    ).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    return service

@router.post("/create",response_model=ServiceResponse,status_code=status.HTTP_201_CREATED)
def create_service(
    payload : ServiceCreate,
    db:Session = Depends(get_db)
):
    # Check if service already exists
    existing_service  = db.query(Service).filter(
        Service.service_name.ilike(payload.service_name.strip())
    ).first()

    if existing_service:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Service already exists",
        )

    service_data = payload.model_dump()
    service_data["service_name"]= payload.service_name.strip()

    service = Service(**service_data)

    db.add(service)
    db.commit()
    db.refresh(service)

    return service

# PUT: Update a service
@router.put("/{service_id}",response_model=ServiceResponse)
def update_service(
    service_id:int,
    payload : ServiceUpdate,
    db:Session = Depends(get_db)
):
    service = db.query(Service).filter(
        Service.id == service_id
    ).first()

    if not service:
        raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail="Service not found",
         )
    update_service = payload.model_dump(exclude_unset=True)

    for field,value in update_service.items():
        setattr(service,field,value)

    db.commit()
    db.refresh(service)
    
    return service

# DELETE: Delete a service
@router.delete("/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
):
    service = db.query(Service).filter(
        Service.id == service_id
    ).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    db.delete(service)
    db.commit()

    return {"message": "Service deleted successfully"}