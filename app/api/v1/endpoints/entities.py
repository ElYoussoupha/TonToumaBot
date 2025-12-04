from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import crud_entity
from app.schemas import entity as schemas

router = APIRouter()

# --- Entities ---
@router.post("/entities", response_model=schemas.EntityResponse)
async def create_entity(
    *,
    db: AsyncSession = Depends(get_db),
    entity_in: schemas.EntityCreate
) -> Any:
    """
    Create new entity.
    """
    return await crud_entity.entity.create(db=db, obj_in=entity_in)

@router.get("/entities", response_model=List[schemas.EntityResponse])
async def read_entities(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve entities.
    """
    return await crud_entity.entity.get_multi(db=db, skip=skip, limit=limit)

@router.get("/entities/{entity_id}", response_model=schemas.EntityResponse)
async def read_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get entity by ID.
    """
    entity = await crud_entity.entity.get(db=db, id=entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity

@router.put("/entities/{entity_id}", response_model=schemas.EntityResponse)
async def update_entity(
    entity_id: UUID,
    entity_in: schemas.EntityUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update an entity.
    """
    entity = await crud_entity.entity.get(db=db, id=entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return await crud_entity.entity.update(db=db, db_obj=entity, obj_in=entity_in)

@router.delete("/entities/{entity_id}", response_model=schemas.EntityResponse)
async def delete_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete an entity.
    """
    entity = await crud_entity.entity.get(db=db, id=entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return await crud_entity.entity.remove(db=db, id=entity_id)

# --- Instances ---
@router.post("/instances", response_model=schemas.InstanceResponse)
async def create_instance(
    *,
    db: AsyncSession = Depends(get_db),
    instance_in: schemas.InstanceCreate
) -> Any:
    """
    Create new instance.
    """
    # Check if entity exists
    entity = await crud_entity.entity.get(db=db, id=instance_in.entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Generate API Key (simple mock for now)
    import secrets
    api_key = secrets.token_urlsafe(32)
    
    # We need to inject api_key into the model creation since it's required but not in schema
    # Pydantic model dump doesn't have it.
    # We can handle this by creating a dict and adding it, or updating the schema.
    # Let's update the crud create method to handle extra fields or just do it manually here.
    # Ideally, InstanceCreate shouldn't have api_key, but the DB model needs it.
    # We can modify the obj_in before passing to CRUD, but CRUD expects Schema.
    # Let's do a manual create here for simplicity or modify schema.
    # Better: modify CRUD to accept dict.
    
    instance_data = instance_in.model_dump()
    instance_data["api_key"] = api_key
    
    # We can't use crud.create directly if it strictly expects Schema and Schema doesn't have api_key field.
    # But our generic CRUD takes Schema, dumps it.
    # So we can pass a dict if we change type hint or just instantiate model directly.
    # Let's instantiate model directly here to be safe.
    from app.models.entity import Instance
    db_obj = Instance(**instance_data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/instances", response_model=List[schemas.InstanceResponse])
async def read_instances(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve instances.
    """
    return await crud_entity.instance.get_multi(db=db, skip=skip, limit=limit)

@router.get("/instances/{instance_id}", response_model=schemas.InstanceResponse)
async def read_instance(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get instance by ID.
    """
    instance = await crud_entity.instance.get(db=db, id=instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return instance

@router.put("/instances/{instance_id}", response_model=schemas.InstanceResponse)
async def update_instance(
    instance_id: UUID,
    instance_in: schemas.InstanceUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update an instance.
    """
    instance = await crud_entity.instance.get(db=db, id=instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return await crud_entity.instance.update(db=db, db_obj=instance, obj_in=instance_in)

@router.delete("/instances/{instance_id}", response_model=schemas.InstanceResponse)
async def delete_instance(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete an instance.
    """
    instance = await crud_entity.instance.get(db=db, id=instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return await crud_entity.instance.remove(db=db, id=instance_id)
