from typing import Optional, List
from uuid import UUID
from datetime import datetime, date, time
from pydantic import BaseModel
from enum import Enum


class AppointmentStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class AppointmentBase(BaseModel):
    patient_name: str
    patient_email: str
    patient_phone: Optional[str] = None
    reason: str


class AppointmentCreate(AppointmentBase):
    doctor_id: UUID
    date: date
    start_time: time
    end_time: time
    session_id: Optional[UUID] = None


class AppointmentUpdate(BaseModel):
    patient_name: Optional[str] = None
    patient_email: Optional[str] = None
    patient_phone: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[AppointmentStatusEnum] = None


class AppointmentResponse(AppointmentBase):
    appointment_id: UUID
    doctor_id: UUID
    session_id: Optional[UUID] = None
    date: date
    start_time: time
    end_time: time
    status: AppointmentStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentWithDoctor(AppointmentResponse):
    """Extended response with doctor details"""
    doctor_first_name: str
    doctor_last_name: str
    specialty_name: Optional[str] = None


class BookAppointmentRequest(BaseModel):
    """Simplified request for chatbot booking"""
    entity_id: UUID
    doctor_id: Optional[UUID] = None  # If None, use specialty to find doctor
    specialty_id: Optional[UUID] = None
    date: date
    start_time: time
    patient_name: str
    patient_email: str
    patient_phone: Optional[str] = None
    reason: str
    session_id: Optional[UUID] = None


class BookAppointmentResponse(BaseModel):
    """Response after successful booking"""
    success: bool
    appointment_id: Optional[UUID] = None
    message: str
    doctor_name: Optional[str] = None
    date: Optional[date] = None
    time: Optional[time] = None
