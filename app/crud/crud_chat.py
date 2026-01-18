from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.chat import Session, Message
from app.schemas.chat import SessionCreate, MessageCreate, MessageBase

class CRUDSession(CRUDBase[Session, SessionCreate, SessionCreate]):
    async def get_multi_by_entity(
        self, db: AsyncSession, *, entity_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Session]:
        query = (
            select(self.model)
            .filter(self.model.entity_id == entity_id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

class CRUDMessage(CRUDBase[Message, MessageCreate, MessageBase]):
    async def get_by_session_id(self, db: AsyncSession, *, session_id: UUID) -> List[Message]:
        query = select(self.model).filter(self.model.session_id == session_id)
        result = await db.execute(query)
        return result.scalars().all()

session = CRUDSession(Session)
message = CRUDMessage(Message)
