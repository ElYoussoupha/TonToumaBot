import json
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.crud import crud_chat, crud_entity
from app.models.chat import Session, Message, Speaker
from app.schemas import chat as schemas

router = APIRouter()

# Lazy-loaded services to avoid import errors at startup
_audio_service = None
_rag_service = None
_llm_service = None

def get_audio_service() -> "AudioService":
    """Lazy load AudioService only when needed"""
    global _audio_service
    if _audio_service is None:
        from app.services.audio import AudioService
        _audio_service = AudioService(settings.UPLOAD_DIR)
    return _audio_service

def get_rag_service() -> "RAGService":
    """Lazy load RAGService only when needed"""
    global _rag_service
    if _rag_service is None:
        from app.services.rag import RAGService
        _rag_service = RAGService()
    return _rag_service

def get_llm_service() -> "LLMService":
    """Lazy load LLMService only when needed"""
    global _llm_service
    if _llm_service is None:
        from app.services.llm import LLMService
        _llm_service = LLMService()
    return _llm_service

@router.post("/messages", response_model=dict)
async def handle_voice_message(
    instance_id: UUID = Form(...),
    speaker_id: Optional[UUID] = Form(None),
    metadata: Optional[str] = Form(None),
    audio_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Get lazy-loaded services
    audio_service = get_audio_service()
    rag_service = get_rag_service()
    llm_service = get_llm_service()
    
    # 1. Save Audio
    audio_path = await audio_service.save_upload_file(audio_file)
    
    # 2. Transcribe
    transcription = await audio_service.transcribe(audio_path)
    
    # 3. Speaker Identification
    if not speaker_id:
        fingerprint, embedding = await audio_service.get_speaker_embedding(audio_path)
        # Check if speaker exists (mock logic here, would query DB by fingerprint)
        # For now, create new speaker
        new_speaker = Speaker(fingerprint_hash=fingerprint, embedding=embedding)
        db.add(new_speaker)
        await db.commit()
        await db.refresh(new_speaker)
        speaker_id = new_speaker.speaker_id
    
    # 4. Get Entity & Session
    instance = await crud_entity.instance.get(db=db, id=instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Find active session
    # Simplified: just create new one for now or find last active
    # In real app: query Session where speaker_id=... and is_active=True
    session = Session(entity_id=instance.entity_id, speaker_id=speaker_id, is_active=True)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # 5. Save User Message
    user_msg = Message(
        session_id=session.session_id,
        instance_id=instance_id,
        role="user",
        content=transcription,
        audio_path=audio_path
    )
    db.add(user_msg)
    await db.commit()
    
    # 6. RAG
    # query_embedding = await rag_service.embed_text(transcription)
    # chunks = await rag_service.search_kb(db, instance.entity_id, query_embedding)
    context = "Contexte simulé de la base de connaissances."
    
    # 7. LLM
    # Get history
    history = "Historique simulé."
    system_instruction = "Tu es un assistant utile."
    
    response_text = await llm_service.generate_response(
        system_instruction, context, history, transcription
    )
    
    # 8. Save Assistant Message
    assistant_msg = Message(
        session_id=session.session_id,
        instance_id=instance_id,
        role="assistant",
        content=response_text
    )
    db.add(assistant_msg)
    await db.commit()
    
    # 9. TTS
    response_audio_path = await audio_service.text_to_speech(response_text)
    
    return {
        "speaker_id": str(speaker_id),
        "session_id": str(session.session_id),
        "response_text": response_text,
        "response_audio": response_audio_path # In real app, return URL or base64
    }
