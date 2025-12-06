from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import crud_appointment
from app.schemas import specialty as schemas

router = APIRouter()


@router.post("/", response_model=schemas.SpecialtyResponse)
async def create_specialty(
    *,
    db: AsyncSession = Depends(get_db),
    specialty_in: schemas.SpecialtyCreate
) -> Any:
    """Create new specialty."""
    # Check if specialty with same name exists
    existing = await crud_appointment.specialty.get_by_name(db=db, name=specialty_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="Specialty with this name already exists")
    return await crud_appointment.specialty.create(db=db, obj_in=specialty_in)


@router.get("/", response_model=List[schemas.SpecialtyResponse])
async def read_specialties(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """Retrieve all specialties."""
    return await crud_appointment.specialty.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{specialty_id}", response_model=schemas.SpecialtyResponse)
async def read_specialty(
    specialty_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get specialty by ID."""
    specialty = await crud_appointment.specialty.get(db=db, id=specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Specialty not found")
    return specialty


@router.put("/{specialty_id}", response_model=schemas.SpecialtyResponse)
async def update_specialty(
    specialty_id: UUID,
    specialty_in: schemas.SpecialtyUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update a specialty."""
    specialty = await crud_appointment.specialty.get(db=db, id=specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Specialty not found")
    return await crud_appointment.specialty.update(db=db, db_obj=specialty, obj_in=specialty_in)


@router.delete("/{specialty_id}", response_model=schemas.SpecialtyResponse)
async def delete_specialty(
    specialty_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete a specialty."""
    specialty = await crud_appointment.specialty.get(db=db, id=specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Specialty not found")
    return await crud_appointment.specialty.remove(db=db, id=specialty_id)
