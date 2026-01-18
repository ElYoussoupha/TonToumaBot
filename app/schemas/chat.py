from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

# --- Session ---
class SessionBase(BaseModel):
    is_active: bool = True

class SessionCreate(SessionBase):
    entity_id: UUID
    speaker_id: Optional[UUID] = None

class SessionResponse(SessionBase):
    session_id: UUID
    entity_id: UUID
    speaker_id: Optional[UUID]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

# --- Message ---
class MessageBase(BaseModel):
    role: str
    content: Optional[str] = None
    translated_content: Optional[str] = None
    audio_path: Optional[str] = None
    tokens: Optional[int] = None

class MessageCreate(MessageBase):
    session_id: UUID
    instance_id: UUID

class MessageResponse(MessageBase):
    message_id: UUID
    session_id: UUID
    instance_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
