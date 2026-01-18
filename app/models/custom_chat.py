# Custom Chatbot Configuration Model
from datetime import datetime
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin
import uuid

class CustomChatConfig(Base, TimestampMixin):
    """Configuration for predefined Q&A pairs in custom chatbot."""
    __tablename__ = "custom_chat_configs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    response_lang: Mapped[str] = mapped_column(String(10), nullable=False, default="fr")  # 'fr', 'wo', 'en', etc.


class CustomChatMessage(Base, TimestampMixin):
    """Message history for custom chatbot sessions."""
    __tablename__ = "custom_chat_messages"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    audio_url: Mapped[str] = mapped_column(String(500), nullable=True)
