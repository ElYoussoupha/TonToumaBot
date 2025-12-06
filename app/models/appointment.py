import uuid
from typing import Optional
from datetime import datetime, date, time
from enum import Enum as PyEnum
from sqlalchemy import String, Text, ForeignKey, Date, Time, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class AppointmentStatus(PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Appointment(Base, TimestampMixin):
    """Booked appointment with a doctor"""
    __tablename__ = "appointments"

    appointment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.doctor_id"), nullable=False)
    
    # Optional link to chatbot session that created this appointment
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sessions.session_id"), nullable=True)
    
    # Patient info (collected by chatbot)
    patient_name: Mapped[str] = mapped_column(String(200), nullable=False)
    patient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    patient_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Appointment datetime
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), 
        default=AppointmentStatus.PENDING, 
        nullable=False
    )

    # Relations
    doctor: Mapped["Doctor"] = relationship(back_populates="appointments")
    session: Mapped[Optional["Session"]] = relationship()
