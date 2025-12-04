from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

# --- Entity ---
class EntityBase(BaseModel):
    name: str
    domain: Optional[str] = None

class EntityCreate(EntityBase):
    pass

class EntityUpdate(EntityBase):
    name: Optional[str] = None

class EntityResponse(EntityBase):
    entity_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Instance ---
class InstanceBase(BaseModel):
    name: str
    description: Optional[str] = None

class InstanceCreate(InstanceBase):
    entity_id: UUID

class InstanceUpdate(InstanceBase):
    name: Optional[str] = None

class InstanceResponse(InstanceBase):
    instance_id: UUID
    entity_id: UUID
    api_key: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- User ---
class UserBase(BaseModel):
    name: str
    role: str # admin_entity, admin_instance, user

class UserCreate(UserBase):
    entity_id: Optional[UUID] = None
    instance_id: Optional[UUID] = None

class UserUpdate(UserBase):
    name: Optional[str] = None
    role: Optional[str] = None

class UserResponse(UserBase):
    user_id: UUID
    entity_id: Optional[UUID]
    instance_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True
