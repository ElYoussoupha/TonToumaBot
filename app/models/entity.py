import uuid
from typing import List, Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class Entity(Base, TimestampMixin):
    __tablename__ = "entities"

    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relations
    instances: Mapped[List["Instance"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    users: Mapped[List["User"]] = relationship(back_populates="entity")
    kb_documents: Mapped[List["KBDocument"]] = relationship(back_populates="entity")
    sessions: Mapped[List["Session"]] = relationship(back_populates="entity")

class Instance(Base, TimestampMixin):
    __tablename__ = "instances"

    instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.entity_id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    api_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    # Relations
    entity: Mapped["Entity"] = relationship(back_populates="instances")
    users: Mapped[List["User"]] = relationship(back_populates="instance")
    messages: Mapped[List["Message"]] = relationship(back_populates="instance")

class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False) # admin_entity, admin_instance, user
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("entities.entity_id"), nullable=True)
    instance_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("instances.instance_id"), nullable=True)

    # Relations
    entity: Mapped[Optional["Entity"]] = relationship(back_populates="users")
    instance: Mapped[Optional["Instance"]] = relationship(back_populates="users")
