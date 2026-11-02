from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database.dependencies import get_db
from models.service import Service
from models.admin import Admin
from schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
)
from core.dependencies import get_current_admin


router = APIRouter(
    prefix="/api/services",
    tags=["Services"],
)


# GET: Retrieve all active services (public)
@router.get("/", response_model=list[ServiceResponse])
def get_services(db: Session = Depends(get_db)):

    statement = (
        select(Service)
        .where(Service.is_active.is_(True))
        .order_by(Service.id)
    )

    return db.scalars(statement).all()


@router.get("/admin/all", response_model=list[ServiceResponse])
def get_all_services(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """Return all services, including inactive services, for admin management."""
    return db.scalars(
        select(Service).order_by(Service.id.desc())
    ).all()


# GET: Retrieve a particular service (public)
@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
):

    service = db.get(Service, service_id)

    if service is None or not service.is_active:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    return service


# POST: Create a service (admin only)
@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):

    statement = select(Service).where(
        func.lower(Service.name) == service_data.name.strip().lower()
    )

    existing_service = db.scalars(statement).one_or_none()

    if existing_service:
        raise HTTPException(
            status_code=409,
            detail="A service with this name already exists",
        )

    new_service = Service(
        name=service_data.name.strip(),
        description=service_data.description.strip(),
        price=service_data.price,
        duration=service_data.duration,
        category=service_data.category.strip(),
    )

    try:
        db.add(new_service)
        db.commit()
        db.refresh(new_service)

    except Exception:
        db.rollback()
        raise

    return new_service


# PATCH: Update a service (admin only)
@router.patch("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):

    service = db.get(Service, service_id)

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    update_data = service_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one field to update",
        )

    if "name" in update_data:
        update_data["name"] = update_data["name"].strip()

        duplicate_statement = select(Service).where(
            func.lower(Service.name) == update_data["name"].lower(),
            Service.id != service_id,
        )

        duplicate = db.scalars(duplicate_statement).one_or_none()

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="A service with this name already exists",
            )

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()

        setattr(service, field, value)

    try:
        db.commit()
        db.refresh(service)

    except Exception:
        db.rollback()
        raise

    return service


# DELETE: Deactivate a service (admin only)
@router.delete("/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):

    service = db.get(Service, service_id)

    if service is None or not service.is_active:
        raise HTTPException(
            status_code=404,
            detail="Service not found",
        )

    service.is_active = False

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Service deactivated successfully",
        "service_id": service.id,
    }