import secrets
import hashlib
from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.core.database import get_db
from app.crud import crud_appointment, crud_entity
from app.models.doctor import Doctor
from app.schemas import doctor as schemas

router = APIRouter()


def hash_password(password: str) -> str:
    """Simple password hashing using SHA256 + salt (for demo purposes)"""
    # In production, use bcrypt or argon2
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        salt, hashed = password_hash.split("$")
        return hashlib.sha256((password + salt).encode()).hexdigest() == hashed
    except:
        return False


def generate_temp_password() -> str:
    """Generate a temporary password"""
    return secrets.token_urlsafe(12)


@router.post("/", response_model=schemas.DoctorCredentials)
async def create_doctor(
    *,
    db: AsyncSession = Depends(get_db),
    doctor_in: schemas.DoctorCreate
) -> Any:
    """Create new doctor and return credentials."""
    # Check entity exists
    entity = await crud_entity.entity.get(db=db, id=doctor_in.entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Check email uniqueness
    existing = await crud_appointment.doctor.get_by_email(db=db, email=doctor_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate or use provided password
    temp_password = doctor_in.password if doctor_in.password else generate_temp_password()
    password_hash = hash_password(temp_password)
    
    # Create doctor
    doctor_data = doctor_in.model_dump(exclude={"password"})
    doctor_data["password_hash"] = password_hash
    
    db_doctor = Doctor(**doctor_data)
    db.add(db_doctor)
    await db.commit()
    await db.refresh(db_doctor)
    
    return schemas.DoctorCredentials(
        doctor_id=db_doctor.doctor_id,
        email=db_doctor.email,
        temporary_password=temp_password
    )


@router.get("/", response_model=List[schemas.DoctorResponse])
async def read_doctors(
    db: AsyncSession = Depends(get_db),
    entity_id: Optional[UUID] = None,
    specialty_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """Retrieve doctors with optional filters."""
    if entity_id and specialty_id:
        return await crud_appointment.doctor.get_by_specialty(db=db, entity_id=entity_id, specialty_id=specialty_id)
    elif entity_id:
        return await crud_appointment.doctor.get_by_entity_id(db=db, entity_id=entity_id)
    else:
        return await crud_appointment.doctor.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{doctor_id}", response_model=schemas.DoctorWithSpecialty)
async def read_doctor(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get doctor by ID with specialty info."""
    result = await db.execute(
        select(Doctor)
        .options(selectinload(Doctor.specialty))
        .filter(Doctor.doctor_id == doctor_id)
    )
    doctor = result.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    response = schemas.DoctorWithSpecialty.model_validate(doctor)
    if doctor.specialty:
        response.specialty_name = doctor.specialty.name
    return response


@router.put("/{doctor_id}", response_model=schemas.DoctorResponse)
async def update_doctor(
    doctor_id: UUID,
    doctor_in: schemas.DoctorUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update a doctor."""
    doctor = await crud_appointment.doctor.get(db=db, id=doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return await crud_appointment.doctor.update(db=db, db_obj=doctor, obj_in=doctor_in)


@router.delete("/{doctor_id}", response_model=schemas.DoctorResponse)
async def delete_doctor(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete a doctor."""
    doctor = await crud_appointment.doctor.get(db=db, id=doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return await crud_appointment.doctor.remove(db=db, id=doctor_id)


@router.post("/login", response_model=schemas.DoctorLoginResponse)
async def doctor_login(
    login_data: schemas.DoctorLogin,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Doctor login endpoint."""
    doctor = await crud_appointment.doctor.get_by_email(db=db, email=login_data.email)
    if not doctor:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(login_data.password, doctor.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not doctor.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    # Generate simple session token
    token = secrets.token_urlsafe(32)
    
    return schemas.DoctorLoginResponse(
        doctor_id=doctor.doctor_id,
        first_name=doctor.first_name,
        last_name=doctor.last_name,
        entity_id=doctor.entity_id,
        specialty_id=doctor.specialty_id,
        token=token
    )
