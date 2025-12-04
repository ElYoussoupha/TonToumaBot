import uuid
from typing import List, Optional
from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin

class KBDocument(Base, TimestampMixin):
    __tablename__ = "kb_documents"

    doc_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.entity_id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relations
    entity: Mapped["Entity"] = relationship(back_populates="kb_documents")
    chunks: Mapped[List["KBChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class KBChunk(Base, TimestampMixin):
    __tablename__ = "kb_chunks"

    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kb_documents.doc_id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relations
    document: Mapped["KBDocument"] = relationship(back_populates="chunks")
    embedding: Mapped[Optional["KBEmbedding"]] = relationship(back_populates="chunk", uselist=False, cascade="all, delete-orphan")

class KBEmbedding(Base):
    __tablename__ = "kb_embeddings"

    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kb_chunks.chunk_id"), primary_key=True)
    embedding: Mapped[List[float]] = mapped_column(Vector(768), nullable=False)

    # Relations
    chunk: Mapped["KBChunk"] = relationship(back_populates="embedding")
