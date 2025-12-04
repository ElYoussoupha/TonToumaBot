from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import crud_entity
from app.schemas import entity as schemas

router = APIRouter()

@router.post("/", response_model=schemas.UserResponse)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserCreate
) -> Any:
    """
    Create new user.
    """
    return await crud_entity.user.create(db=db, obj_in=user_in)

@router.get("/", response_model=List[schemas.UserResponse])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve users.
    """
    return await crud_entity.user.get_multi(db=db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def read_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get user by ID.
    """
    user = await crud_entity.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: UUID,
    user_in: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update a user.
    """
    user = await crud_entity.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await crud_entity.user.update(db=db, db_obj=user, obj_in=user_in)

@router.delete("/{user_id}", response_model=schemas.UserResponse)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a user.
    """
    user = await crud_entity.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await crud_entity.user.remove(db=db, id=user_id)
