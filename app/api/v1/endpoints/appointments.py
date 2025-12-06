from typing import Any, List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.core.database import get_db
from app.crud import crud_appointment
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.schemas import appointment as schemas
from app.schemas.timeslot import AvailableSlot
from app.services.appointment_service import appointment_service

router = APIRouter()


@router.post("/", response_model=schemas.AppointmentResponse)
async def create_appointment(
    *,
    db: AsyncSession = Depends(get_db),
    appointment_in: schemas.AppointmentCreate
) -> Any:
    """Create new appointment directly."""
    # Check doctor exists
    doctor = await crud_appointment.doctor.get(db=db, id=appointment_in.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    return await crud_appointment.appointment.create(db=db, obj_in=appointment_in)


@router.get("/", response_model=List[schemas.AppointmentResponse])
async def read_appointments(
    db: AsyncSession = Depends(get_db),
    doctor_id: Optional[UUID] = None,
    target_date: Optional[date] = Query(None, alias="date"),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """Retrieve appointments with optional filters."""
    if doctor_id and target_date:
        return await crud_appointment.appointment.get_by_doctor_and_date(
            db=db, doctor_id=doctor_id, date=target_date
        )
    elif doctor_id:
        return await crud_appointment.appointment.get_by_doctor_id(db=db, doctor_id=doctor_id)
    else:
        return await crud_appointment.appointment.get_multi(db=db, skip=skip, limit=limit)


@router.get("/available", response_model=List[AvailableSlot])
async def get_available_slots(
    entity_id: UUID,
    target_date: date = Query(..., alias="date"),
    specialty_id: Optional[UUID] = None,
    doctor_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get available appointment slots for booking."""
    return await appointment_service.get_available_slots(
        db=db,
        entity_id=entity_id,
        target_date=target_date,
        specialty_id=specialty_id,
        doctor_id=doctor_id
    )


@router.post("/book", response_model=schemas.BookAppointmentResponse)
async def book_appointment(
    request: schemas.BookAppointmentRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Book an appointment (used by chatbot)."""
    return await appointment_service.book_appointment(db=db, request=request)


@router.get("/{appointment_id}", response_model=schemas.AppointmentWithDoctor)
async def read_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get appointment by ID with doctor details."""
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.doctor).selectinload(Doctor.specialty))
        .filter(Appointment.appointment_id == appointment_id)
    )
    appointment = result.scalars().first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    response_data = {
        **schemas.AppointmentResponse.model_validate(appointment).model_dump(),
        "doctor_first_name": appointment.doctor.first_name,
        "doctor_last_name": appointment.doctor.last_name,
        "specialty_name": appointment.doctor.specialty.name if appointment.doctor.specialty else None
    }
    return schemas.AppointmentWithDoctor(**response_data)


@router.put("/{appointment_id}", response_model=schemas.AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    appointment_in: schemas.AppointmentUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update an appointment (e.g., cancel)."""
    appointment = await crud_appointment.appointment.get(db=db, id=appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return await crud_appointment.appointment.update(db=db, db_obj=appointment, obj_in=appointment_in)


@router.delete("/{appointment_id}", response_model=schemas.AppointmentResponse)
async def delete_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete an appointment."""
    appointment = await crud_appointment.appointment.get(db=db, id=appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return await crud_appointment.appointment.remove(db=db, id=appointment_id)
