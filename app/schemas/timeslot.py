from typing import Optional, List
from uuid import UUID
from datetime import datetime, date, time
from pydantic import BaseModel


class TimeSlotBase(BaseModel):
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    specific_date: Optional[date] = None
    start_time: time
    end_time: time
    is_recurring: bool = True


class TimeSlotCreate(TimeSlotBase):
    doctor_id: UUID


class TimeSlotUpdate(BaseModel):
    day_of_week: Optional[int] = None
    specific_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_recurring: Optional[bool] = None
    is_active: Optional[bool] = None


class TimeSlotResponse(TimeSlotBase):
    slot_id: UUID
    doctor_id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AvailableSlot(BaseModel):
    """Represents an available appointment slot for chatbot display"""
    doctor_id: UUID
    doctor_name: str
    specialty_name: Optional[str] = None
    date: date
    start_time: time
    end_time: time


class AvailableSlotsRequest(BaseModel):
    """Request to get available slots"""
    entity_id: UUID
    specialty_id: Optional[UUID] = None
    doctor_id: Optional[UUID] = None
    date: date
