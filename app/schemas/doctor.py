from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class DoctorBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    consultation_duration: int = 30


class DoctorCreate(DoctorBase):
    entity_id: UUID
    specialty_id: Optional[UUID] = None
    password: Optional[str] = None  # If None, will be auto-generated


class DoctorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    specialty_id: Optional[UUID] = None
    consultation_duration: Optional[int] = None
    is_active: Optional[bool] = None


class DoctorResponse(DoctorBase):
    doctor_id: UUID
    entity_id: UUID
    specialty_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DoctorWithSpecialty(DoctorResponse):
    """Extended response with specialty details"""
    specialty_name: Optional[str] = None


class DoctorCredentials(BaseModel):
    """Returned after doctor creation with temporary password"""
    doctor_id: UUID
    email: str
    temporary_password: str
    message: str = "Veuillez communiquer ces identifiants au médecin. Le mot de passe devra être changé à la première connexion."


class DoctorLogin(BaseModel):
    email: str
    password: str


class DoctorLoginResponse(BaseModel):
    doctor_id: UUID
    first_name: str
    last_name: str
    entity_id: UUID
    specialty_id: Optional[UUID] = None
    token: str  # Simple session token
