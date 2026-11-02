from datetime import date, time, datetime, timedelta
from sqlalchemy.orm import Session, selectinload

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from database.dependencies import get_db
from core.dependencies import get_current_admin
from core.availability import (
    TIMEZONE,
    is_working_day,
    is_within_working_hours,
    generate_time_slots,
)

from models.appointment import Appointment
from models.customer import Customer
from models.service import Service
from models.admin import Admin

from schemas.appointment import AppointmentCreate, AppointmentResponse


router = APIRouter(
    prefix="/api/appointments",
    tags=["Appointments"],
)


# --------------------------------------------------
# CREATE APPOINTMENT
# Public endpoint - customers do not need to log in
# --------------------------------------------------

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
):
    today = datetime.now(TIMEZONE).date()

    # Check appointment date
    if appointment_data.appointment_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment date cannot be in the past",
        )

    # Check working day
    if not is_working_day(appointment_data.appointment_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The parlour is closed on this day",
        )

    # Get active service
    service = db.get(Service, appointment_data.service_id)

    if service is None or not service.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or inactive",
        )

    # Check working hours and break time
    if not is_within_working_hours(
        appointment_data.appointment_time,
        service.duration,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected time is outside working hours or overlaps the break",
        )

    # Prevent two simultaneous booking requests from
    # creating overlapping appointments for the same date.
    db.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"),
        {"lock_key": appointment_data.appointment_date.toordinal()},
    )

    # Check whether the requested time overlaps
    # an existing pending or confirmed appointment.
    statement = (
        select(Appointment, Service.duration)
        .join(Service, Appointment.service_id == Service.id)
        .where(
            Appointment.appointment_date == appointment_data.appointment_date,
            Appointment.status.in_(["pending", "confirmed"]),
        )
    )

    existing_appointments = db.execute(statement).all()

    requested_start = datetime.combine(
        appointment_data.appointment_date,
        appointment_data.appointment_time,
    )

    requested_end = requested_start + timedelta(minutes=service.duration)

    for existing, existing_duration in existing_appointments:
        existing_start = datetime.combine(
            existing.appointment_date,
            existing.appointment_time,
        )

        existing_end = existing_start + timedelta(minutes=existing_duration)

        if requested_start < existing_end and requested_end > existing_start:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This time slot is already booked. Please select another time.",
            )

    try:
        # Find an existing customer using email.
        customer_statement = select(Customer).where(
            Customer.email == appointment_data.customer_email
        )

        customer = db.scalars(customer_statement).one_or_none()

        # Create customer if they do not already exist.
        if customer is None:
            customer = Customer(
                name=appointment_data.customer_name,
                email=appointment_data.customer_email,
                phone=appointment_data.customer_phone,
            )

            db.add(customer)
            db.flush()

        # Create appointment.
        new_appointment = Appointment(
            customer=customer,
            service=service,
            appointment_date=appointment_data.appointment_date,
            appointment_time=appointment_data.appointment_time,
            status="pending",
            notes=appointment_data.notes,
        )

        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)

        return new_appointment

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# CHECK AVAILABLE TIME SLOTS
# Public endpoint
# --------------------------------------------------

@router.get("/availability")
def get_available_slots(
    service_id: int,
    appointment_date: date,
    db: Session = Depends(get_db),
):
    today = datetime.now(TIMEZONE).date()

    # Check past date
    if appointment_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment date cannot be in the past",
        )

    # Check working day
    if not is_working_day(appointment_date):
        return {
            "date": appointment_date,
            "service_id": service_id,
            "available_slots": [],
            "message": "The parlour is closed on this day",
        }

    # Get active service
    service = db.get(Service, service_id)

    if service is None or not service.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or inactive",
        )

    # Get existing appointments for the selected date.
    statement = (
        select(Appointment, Service.duration)
        .join(Service, Appointment.service_id == Service.id)
        .where(
            Appointment.appointment_date == appointment_date,
            Appointment.status.in_(["pending", "confirmed"]),
        )
    )

    existing_appointments = db.execute(statement).all()

    available_slots = []

    for slot in generate_time_slots(appointment_date):

        # Hide past time slots when the selected date is today.
        if appointment_date == today:
            current_time = datetime.now(TIMEZONE).time().replace(tzinfo=None)

            if slot <= current_time:
                continue

        # Check business hours and break time.
        if not is_within_working_hours(slot, service.duration):
            continue

        requested_start = datetime.combine(appointment_date, slot)

        requested_end = requested_start + timedelta(
            minutes=service.duration
        )

        overlapping = False

        # Check overlap with existing appointments.
        for existing, existing_duration in existing_appointments:

            existing_start = datetime.combine(
                existing.appointment_date,
                existing.appointment_time,
            )

            existing_end = existing_start + timedelta(
                minutes=existing_duration
            )

            if requested_start < existing_end and requested_end > existing_start:
                overlapping = True
                break

        if not overlapping:
            available_slots.append(slot.strftime("%H:%M"))

    return {
        "date": appointment_date,
        "service_id": service.id,
        "service_name": service.name,
        "duration": service.duration,
        "available_slots": available_slots,
    }


# --------------------------------------------------
# GET ALL APPOINTMENTS
# Admin only
# --------------------------------------------------

@router.get("/", response_model=list[AppointmentResponse])
def get_all_appointments(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    statement = (
        select(Appointment)
        .options(
            selectinload(Appointment.customer),
            selectinload(Appointment.service),
        )
        .order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc(),
        )
    )

    return db.scalars(statement).all()


# --------------------------------------------------
# GET SINGLE APPOINTMENT
# Admin only
# --------------------------------------------------

@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    appointment = db.get(Appointment, appointment_id)

    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    return appointment


# --------------------------------------------------
# UPDATE APPOINTMENT STATUS
# Admin only
# pending -> confirmed -> completed
# --------------------------------------------------

@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    appointment = db.get(Appointment, appointment_id)

    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    allowed_transitions = {
        "pending": ["confirmed"],
        "confirmed": ["completed"],
    }

    allowed_statuses = allowed_transitions.get(appointment.status, [])

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change appointment status from {appointment.status} to {new_status}",
        )

    appointment.status = new_status

    db.commit()
    db.refresh(appointment)

    return appointment


# --------------------------------------------------
# CANCEL APPOINTMENT
# Admin only
# --------------------------------------------------

@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    appointment = db.get(Appointment, appointment_id)

    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    if appointment.status not in ["pending", "confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This appointment cannot be cancelled",
        )

    appointment.status = "cancelled"

    db.commit()
    db.refresh(appointment)

    return appointment