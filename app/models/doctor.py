import uuid
from typing import List, Optional
from sqlalchemy import String, Text, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class Doctor(Base, TimestampMixin):
    """Doctor belonging to an entity with optional specialty"""
    __tablename__ = "doctors"

    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.entity_id"), nullable=False)
    specialty_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("specialties.specialty_id"), nullable=True)
    
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Default consultation duration in minutes
    consultation_duration: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relations
    entity: Mapped["Entity"] = relationship(back_populates="doctors")
    specialty: Mapped[Optional["Specialty"]] = relationship(back_populates="doctors")
    time_slots: Mapped[List["TimeSlot"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
