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
    title: str = Form(...),
    file: UploadFile = File(...),
    entity_id: UUID = Form(...)
) -> Any:
    """
    Create new KB document with content.
    """
    # Upload to MinIO
    from app.services.storage import storage_service
    
    file_content = await file.read()
    file_name = f"{entity_id}/{file.filename}"
    storage_service.upload_file(file_content, file_name, file.content_type or "application/octet-stream")
    
    # Extract text content (simple decoding for now, later use unstructured or similar)
    # Extract text content
    if file.content_type == "application/pdf":
        try:
            import pypdf
            import io
            pdf_file = io.BytesIO(file_content)
            reader = pypdf.PdfReader(pdf_file)
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            text_content = f"[PDF Error] Could not extract text: {str(e)}"
    else:
        try:
            text_content = file_content.decode("utf-8")
        except:
            text_content = f"[Binary Content] File: {file.filename}"

    # Create document
    doc_in = schemas.KBDocumentCreate(
        title=title,
        source=file_name, # Store MinIO path as source
        entity_id=entity_id
    )
    document = await crud_knowledge.kb_document.create(db=db, obj_in=doc_in)
    
    # Simple chunking: split by double newlines or every 500 characters
    # TODO: Implement better chunking strategy
    from app.services.rag import RAGService
    rag_service = RAGService()

    if text_content and not text_content.startswith("[Binary Content]"):
        chunk_size = 500
        for i in range(0, len(text_content), chunk_size):
            chunk_text = text_content[i:i+chunk_size]
            
            # Create Chunk
            chunk_in = schemas.KBChunkCreate(
                doc_id=document.doc_id,
                chunk_index=i // chunk_size,
                content=chunk_text
            )
            chunk = await crud_knowledge.kb_chunk.create(db=db, obj_in=chunk_in)
            
            # Generate Embedding
            embedding_vector = await rag_service.embed_text(chunk_text)
            
            # Store Embedding
            embedding_in = schemas.KBEmbeddingCreate(
                chunk_id=chunk.chunk_id,
                embedding=embedding_vector
            )
            await crud_knowledge.kb_embedding.create(db=db, obj_in=embedding_in)
    
    # Refresh document to load chunks for response
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.knowledge import KBDocument
    
    query = select(KBDocument).options(selectinload(KBDocument.chunks)).filter(KBDocument.doc_id == document.doc_id)
    result = await db.execute(query)
    document = result.scalar_one()

    return document

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

# --- Create document from raw text ---
@router.post("/text", response_model=schemas.KBDocumentResponse)
async def create_document_from_text(
    *,
    db: AsyncSession = Depends(get_db),
    title: str = Form(...),
    content: str = Form(...),
    entity_id: UUID = Form(...),
) -> Any:
    """
    Create a KB document directly from raw text (no file upload).
    Reuses the same chunking and embedding pipeline as file-based creation.
    """
    # Create document (no external storage path)
    doc_in = schemas.KBDocumentCreate(
        title=title,
        source=None,
        entity_id=entity_id,
    )
    document = await crud_knowledge.kb_document.create(db=db, obj_in=doc_in)

    # Chunk and embed like in the file path
    from app.services.rag import RAGService
    rag_service = RAGService()

    text_content = content or ""
    if text_content:
        chunk_size = 500
        for i in range(0, len(text_content), chunk_size):
            chunk_text = text_content[i:i+chunk_size]

            # Create Chunk
            chunk_in = schemas.KBChunkCreate(
                doc_id=document.doc_id,
                chunk_index=i // chunk_size,
                content=chunk_text,
            )
            chunk = await crud_knowledge.kb_chunk.create(db=db, obj_in=chunk_in)

            # Generate Embedding
            embedding_vector = await rag_service.embed_text(chunk_text)

            # Store Embedding
            embedding_in = schemas.KBEmbeddingCreate(
                chunk_id=chunk.chunk_id,
                embedding=embedding_vector,
            )
            await crud_knowledge.kb_embedding.create(db=db, obj_in=embedding_in)

    # Refresh document with chunks
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.knowledge import KBDocument

    query = (
        select(KBDocument)
        .options(selectinload(KBDocument.chunks))
        .filter(KBDocument.doc_id == document.doc_id)
    )
    result = await db.execute(query)
    document = result.scalar_one()
    return document

@router.delete("/documents/{doc_id}", response_model=schemas.KBDocumentResponse)
async def delete_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a document.
    """
    document = await crud_knowledge.kb_document.get(db=db, id=doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from MinIO
    from app.services.storage import storage_service
    if document.source:
        try:
            storage_service.delete_file(document.source)
        except Exception as e:
            print(f"Error deleting file from MinIO: {e}")
            # Continue to delete from DB even if MinIO deletion fails
            
    # Delete from DB
    document = await crud_knowledge.kb_document.remove(db=db, id=doc_id)
    return document
