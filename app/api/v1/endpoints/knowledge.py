from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import crud_knowledge
from app.schemas import knowledge as schemas

router = APIRouter()

@router.post("/upload", response_model=schemas.KBDocumentResponse)
async def upload_document(
    entity_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Upload a file as a KB document.
    """
    content = await file.read()
    # Simple text decoding for now.
    try:
        text_content = content.decode("utf-8")
    except:
        text_content = f"[Binary Content] File: {file.filename}"
    
    doc_in = schemas.KBDocumentCreate(
        title=file.filename,
        source=file.filename,
        entity_id=entity_id,
        content=text_content
    )
    return await crud_knowledge.kb_document.create(db=db, obj_in=doc_in)

# --- Documents ---
@router.post("/documents", response_model=schemas.KBDocumentResponse)
async def create_document(
    *,
    db: AsyncSession = Depends(get_db),
    document_in: schemas.KBDocumentCreate
) -> Any:
    """
    Create new KB document.
    """
    # Note: Logic to chunk content would go here or in a service layer.
    # For now, we just save the document.
    return await crud_knowledge.kb_document.create(db=db, obj_in=document_in)

@router.get("/documents/{entity_id}", response_model=List[schemas.KBDocumentResponse])
async def read_documents(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retrieve documents for an entity.
    """
    return await crud_knowledge.kb_document.get_by_entity_id(db=db, entity_id=entity_id)

# --- Chunks ---
@router.post("/chunks", response_model=schemas.KBChunkResponse)
async def create_chunk(
    *,
    db: AsyncSession = Depends(get_db),
    chunk_in: schemas.KBChunkCreate
) -> Any:
    """
    Create new KB chunk.
    """
    return await crud_knowledge.kb_chunk.create(db=db, obj_in=chunk_in)

@router.get("/chunks/{doc_id}", response_model=List[schemas.KBChunkResponse])
async def read_chunks(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retrieve chunks for a document.
    """
    return await crud_knowledge.kb_chunk.get_by_doc_id(db=db, doc_id=doc_id)

# --- Embeddings ---
@router.post("/embeddings", response_model=schemas.KBEmbeddingResponse)
async def create_embedding(
    *,
    db: AsyncSession = Depends(get_db),
    embedding_in: schemas.KBEmbeddingCreate
) -> Any:
    """
    Create new KB embedding.
    """
    return await crud_knowledge.kb_embedding.create(db=db, obj_in=embedding_in)

@router.get("/embeddings/{chunk_id}", response_model=schemas.KBEmbeddingResponse)
async def read_embedding(
    chunk_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get embedding by chunk ID.
    """
    embedding = await crud_knowledge.kb_embedding.get(db=db, id=chunk_id)
    if not embedding:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return embedding
