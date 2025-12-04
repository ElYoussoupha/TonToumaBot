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
        # This would perform the vector search using pgvector
        # For now, we return empty list or mock
        # Real query:
        # stmt = select(KBChunk).filter(KBChunk.doc_id.in_(...)).order_by(KBEmbedding.embedding.l2_distance(query_embedding)).limit(top_k)
        return []
