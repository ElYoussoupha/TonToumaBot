from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

# --- Document ---
class KBDocumentBase(BaseModel):
    title: str
    source: Optional[str] = None

class KBDocumentCreate(KBDocumentBase):
    entity_id: UUID

class KBDocumentResponse(KBDocumentBase):
    doc_id: UUID
    entity_id: UUID
    created_at: datetime
    chunks: List["KBChunkResponse"] = []

    class Config:
        from_attributes = True

# --- Chunk ---
class KBChunkBase(BaseModel):
    chunk_index: int
    content: str

class KBChunkCreate(KBChunkBase):
    doc_id: UUID

class KBChunkResponse(KBChunkBase):
    chunk_id: UUID
    doc_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Embedding ---
class KBEmbeddingCreate(BaseModel):
    chunk_id: UUID
    embedding: List[float]

class KBEmbeddingResponse(BaseModel):
    chunk_id: UUID
    embedding: List[float]

    class Config:
        from_attributes = True
