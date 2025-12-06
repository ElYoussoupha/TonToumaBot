from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.knowledge import KBDocument, KBChunk, KBEmbedding
from app.schemas.knowledge import KBDocumentCreate, KBChunkCreate, KBEmbeddingCreate

class CRUDKBDocument(CRUDBase[KBDocument, KBDocumentCreate, KBDocumentCreate]):
    async def get_by_entity_id(self, db: AsyncSession, *, entity_id: UUID) -> List[KBDocument]:
        query = select(self.model).options(selectinload(self.model.chunks)).filter(self.model.entity_id == entity_id)
        result = await db.execute(query)
        return result.scalars().all()

class CRUDKBChunk(CRUDBase[KBChunk, KBChunkCreate, KBChunkCreate]):
    async def get_by_doc_id(self, db: AsyncSession, *, doc_id: UUID) -> List[KBChunk]:
        query = select(self.model).filter(self.model.doc_id == doc_id)
        result = await db.execute(query)
        return result.scalars().all()

class CRUDKBEmbedding(CRUDBase[KBEmbedding, KBEmbeddingCreate, KBEmbeddingCreate]):
    pass

kb_document = CRUDKBDocument(KBDocument)
kb_chunk = CRUDKBChunk(KBChunk)
kb_embedding = CRUDKBEmbedding(KBEmbedding)
