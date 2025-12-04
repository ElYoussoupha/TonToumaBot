from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.chat import Session, Message
from app.schemas.chat import SessionCreate, MessageCreate, MessageBase

class CRUDSession(CRUDBase[Session, SessionCreate, SessionCreate]): # Update schema same as create for now
    pass

class CRUDMessage(CRUDBase[Message, MessageCreate, MessageBase]):
    async def get_by_session_id(self, db: AsyncSession, *, session_id: UUID) -> List[Message]:
        query = select(self.model).filter(self.model.session_id == session_id)
        result = await db.execute(query)
        return result.scalars().all()

session = CRUDSession(Session)
message = CRUDMessage(Message)
