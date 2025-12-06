import uuid
from typing import Optional
from datetime import time, date
from sqlalchemy import ForeignKey, Integer, Boolean, Time, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class TimeSlot(Base, TimestampMixin):
    """Available time slots for a doctor (recurring or specific date)"""
    __tablename__ = "time_slots"

    slot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.doctor_id"), nullable=False)
    
    # For recurring slots (weekly): day_of_week 0=Monday, 6=Sunday
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # For specific date slots
    specific_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    # True = recurring weekly, False = specific date only
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Is this slot currently active?
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relations
    doctor: Mapped["Doctor"] = relationship(back_populates="time_slots")
