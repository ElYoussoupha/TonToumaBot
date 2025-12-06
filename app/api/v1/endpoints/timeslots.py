from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import crud_appointment
from app.schemas import timeslot as schemas

router = APIRouter()


@router.post("/", response_model=schemas.TimeSlotResponse)
async def create_time_slot(
    *,
    db: AsyncSession = Depends(get_db),
    slot_in: schemas.TimeSlotCreate
) -> Any:
    """Create new time slot for a doctor."""
    # Check doctor exists
    doctor = await crud_appointment.doctor.get(db=db, id=slot_in.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Validate slot data
    if slot_in.is_recurring and slot_in.day_of_week is None:
        raise HTTPException(status_code=400, detail="Recurring slots require day_of_week")
    if not slot_in.is_recurring and slot_in.specific_date is None:
        raise HTTPException(status_code=400, detail="Non-recurring slots require specific_date")
    
    return await crud_appointment.time_slot.create(db=db, obj_in=slot_in)


@router.get("/", response_model=List[schemas.TimeSlotResponse])
async def read_time_slots(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve time slots for a doctor."""
    return await crud_appointment.time_slot.get_by_doctor_id(db=db, doctor_id=doctor_id)


@router.get("/{slot_id}", response_model=schemas.TimeSlotResponse)
async def read_time_slot(
    slot_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get time slot by ID."""
    slot = await crud_appointment.time_slot.get(db=db, id=slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return slot


@router.put("/{slot_id}", response_model=schemas.TimeSlotResponse)
async def update_time_slot(
    slot_id: UUID,
    slot_in: schemas.TimeSlotUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update a time slot."""
    slot = await crud_appointment.time_slot.get(db=db, id=slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return await crud_appointment.time_slot.update(db=db, db_obj=slot, obj_in=slot_in)


@router.delete("/{slot_id}", response_model=schemas.TimeSlotResponse)
async def delete_time_slot(
    slot_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete a time slot."""
    slot = await crud_appointment.time_slot.get(db=db, id=slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return await crud_appointment.time_slot.remove(db=db, id=slot_id)
