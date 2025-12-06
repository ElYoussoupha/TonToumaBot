import uuid
from typing import List, Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class Specialty(Base, TimestampMixin):
    """Medical specialty (e.g., Cardiology, Pediatrics)"""
    __tablename__ = "specialties"

    specialty_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relations
    doctors: Mapped[List["Doctor"]] = relationship(back_populates="specialty")
