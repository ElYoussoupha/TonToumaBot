import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, ForeignKey, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin

class Speaker(Base, TimestampMixin):
    __tablename__ = "speakers"

    speaker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fingerprint_hash: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(256), nullable=True)

    # Relations
    sessions: Mapped[List["Session"]] = relationship(back_populates="speaker")

class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.entity_id"), nullable=False)
    speaker_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("speakers.speaker_id"), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relations
    entity: Mapped["Entity"] = relationship(back_populates="sessions")
    speaker: Mapped[Optional["Speaker"]] = relationship(back_populates="sessions")
    messages: Mapped[List["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    analytics: Mapped[List["Analytics"]] = relationship(back_populates="session")

class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.session_id"), nullable=False)
    instance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instances.instance_id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False) # user/assistant/system
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relations
    session: Mapped["Session"] = relationship(back_populates="messages")
    instance: Mapped["Instance"] = relationship(back_populates="messages")
