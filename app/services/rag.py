from typing import List
from openai import AsyncOpenAI
from app.core.config import settings

class RAGService:
    def __init__(self):
        print(f"Initializing OpenAI Client for Embeddings (timeout={settings.OPENAI_TIMEOUT}s, retries={settings.OPENAI_MAX_RETRIES})...")
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT,
            max_retries=settings.OPENAI_MAX_RETRIES
        )
        self.model = "text-embedding-3-small"

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        text = text.replace("\n", " ")
        response = await self.client.embeddings.create(input=[text], model=self.model)
        return response.data[0].embedding

    async def search_kb(self, db, entity_id, query_embedding, top_k=3):
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.knowledge import KBChunk, KBEmbedding, KBDocument
        
        # Perform vector search
        # Join KBEmbedding -> KBChunk -> KBDocument to filter by entity_id
        # Use selectinload to eagerly load the document relationship
        stmt = (
            select(KBChunk)
            .join(KBEmbedding)
            .join(KBDocument)
            .options(selectinload(KBChunk.document))
            .filter(KBDocument.entity_id == entity_id)
            .order_by(KBEmbedding.embedding.l2_distance(query_embedding))
            .limit(top_k)
        )
        
        result = await db.execute(stmt)
        return result.scalars().all()
