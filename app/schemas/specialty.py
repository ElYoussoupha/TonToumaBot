from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class SpecialtyBase(BaseModel):
    name: str
    description: Optional[str] = None


class SpecialtyCreate(SpecialtyBase):
    pass


class SpecialtyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SpecialtyResponse(SpecialtyBase):
    specialty_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
