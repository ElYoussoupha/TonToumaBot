from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        result = await db.execute(select(self.model).filter(self.model.entity_id == id if hasattr(self.model, 'entity_id') and self.model.__tablename__ == 'entities' else self.model.instance_id == id if hasattr(self.model, 'instance_id') and self.model.__tablename__ == 'instances' else self.model.user_id == id if hasattr(self.model, 'user_id') and self.model.__tablename__ == 'users' else self.model.session_id == id if hasattr(self.model, 'session_id') and self.model.__tablename__ == 'sessions' else self.model.message_id == id if hasattr(self.model, 'message_id') and self.model.__tablename__ == 'messages' else self.model.doc_id == id if hasattr(self.model, 'doc_id') and self.model.__tablename__ == 'kb_documents' else self.model.chunk_id == id if hasattr(self.model, 'chunk_id') and self.model.__tablename__ == 'kb_chunks' else None))
        # The above logic is a bit hacky for a generic base, usually we pass the PK column name or assume 'id'. 
        # Given our models have different PK names (entity_id, instance_id, etc.), we should probably override `get` in subclasses or make it smarter.
        # Let's try a simpler approach: assume the caller knows how to filter or we use a standard 'id' field if possible, 
        # but our models don't use 'id'.
        # Better approach: Use `db.get(self.model, id)` which works with PKs automatically.
        return await db.get(self.model, id)

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: UUID) -> ModelType:
        obj = await db.get(self.model, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
