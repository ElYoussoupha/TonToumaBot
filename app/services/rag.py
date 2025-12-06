from typing import List
from sentence_transformers import SentenceTransformer

class RAGService:
    def __init__(self):
        print("Loading Sentence Transformer model...")
        # 'all-MiniLM-L6-v2' is small (80MB) and fast
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    async def embed_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

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

