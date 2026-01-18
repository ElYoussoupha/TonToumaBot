# Custom Chatbot API Endpoints
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.custom_chat import CustomChatConfig, CustomChatMessage
from app.services.audio import AudioService

router = APIRouter(prefix="/custom_chat_bot", tags=["Custom ChatBot"])

# Get audio service singleton
_audio_service = None
def get_audio_service():
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService("uploads")
    return _audio_service

# Pydantic models
class ConfigCreate(BaseModel):
    question: str
    response: str
    response_lang: str = "fr"

class ConfigResponse(BaseModel):
    id: str
    question: str
    response: str
    response_lang: str
    created_at: datetime

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    audio_url: Optional[str] = None
    created_at: datetime

class MessageHistoryResponse(BaseModel):
    messages: List[ChatResponse]


# ========== CONFIG ENDPOINTS ==========

@router.post("/config", response_model=ConfigResponse)
async def create_config(
    config: ConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a new Q&A configuration."""
    new_config = CustomChatConfig(
        question=config.question,
        response=config.response,
        response_lang=config.response_lang
    )
    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)
    
    return ConfigResponse(
        id=str(new_config.id),
        question=new_config.question,
        response=new_config.response,
        response_lang=new_config.response_lang,
        created_at=new_config.created_at
    )

@router.get("/config", response_model=List[ConfigResponse])
async def list_configs(db: AsyncSession = Depends(get_db)):
    """List all Q&A configurations."""
    result = await db.execute(select(CustomChatConfig).order_by(CustomChatConfig.created_at.desc()))
    configs = result.scalars().all()
    
    return [
        ConfigResponse(
            id=str(c.id),
            question=c.question,
            response=c.response,
            response_lang=c.response_lang,
            created_at=c.created_at
        )
        for c in configs
    ]

@router.delete("/config/{config_id}")
async def delete_config(config_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a Q&A configuration."""
    try:
        config_uuid = uuid.UUID(config_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid config ID")
    
    result = await db.execute(
        delete(CustomChatConfig).where(CustomChatConfig.id == config_uuid)
    )
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Config not found")
    
    return {"message": "Config deleted successfully"}


# ========== CHAT ENDPOINTS ==========

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Process a chat message.
    Finds matching Q&A config and returns exact response with TTS.
    """
    from openai import AsyncOpenAI
    from app.core.config import settings
    
    user_message = request.message.strip().lower()
    session_id = request.session_id
    
    # Save user message
    user_msg = CustomChatMessage(
        session_id=session_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)
    
    # Find matching config (simple substring matching)
    result = await db.execute(select(CustomChatConfig))
    configs = result.scalars().all()
    
    matched_config = None
    for config in configs:
        # Check if user message contains the configured question keywords
        config_question = config.question.strip().lower()
        if config_question in user_message or user_message in config_question:
            matched_config = config
            break
    
    # If no exact match, use LLM to find best match or generate fallback
    if matched_config is None:
        # Use GPT to match or generate response
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build context from configs
        config_context = "\n".join([
            f"Q: {c.question}\nA: {c.response} (lang: {c.response_lang})"
            for c in configs
        ])
        
        system_prompt = f"""Tu es un assistant qui répond uniquement avec les réponses préconfigurées.

RÉPONSES DISPONIBLES:
{config_context}

RÈGLES:
1. Si la question de l'utilisateur correspond à une question configurée, retourne EXACTEMENT la réponse associée.
2. Si aucune correspondance, dis "Je n'ai pas de réponse configurée pour cette question."
3. Retourne UNIQUEMENT la réponse, sans explication.
"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            max_tokens=500
        )
        
        bot_response = response.choices[0].message.content
        response_lang = "fr"  # Default for fallback
        
        # Try to detect which config was matched
        for config in configs:
            if config.response in bot_response:
                response_lang = config.response_lang
                break
    else:
        bot_response = matched_config.response
        response_lang = matched_config.response_lang
    
    # Generate TTS based on language
    audio_service = get_audio_service()
    try:
        audio_path = await audio_service.text_to_speech(bot_response, language=response_lang)
        audio_url = f"/uploads/{audio_path.split('/')[-1].split(chr(92))[-1]}"
    except Exception as e:
        print(f"[CustomChat] TTS failed: {e}")
        audio_url = None
    
    # Save assistant message
    assistant_msg = CustomChatMessage(
        session_id=session_id,
        role="assistant",
        content=bot_response,
        audio_url=audio_url
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    
    return ChatResponse(
        id=str(assistant_msg.id),
        session_id=session_id,
        role="assistant",
        content=bot_response,
        audio_url=audio_url,
        created_at=assistant_msg.created_at
    )


@router.get("/messages/{session_id}", response_model=MessageHistoryResponse)
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get chat history for a session."""
    result = await db.execute(
        select(CustomChatMessage)
        .where(CustomChatMessage.session_id == session_id)
        .order_by(CustomChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    
    return MessageHistoryResponse(
        messages=[
            ChatResponse(
                id=str(m.id),
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                audio_url=m.audio_url,
                created_at=m.created_at
            )
            for m in messages
        ]
    )


@router.delete("/messages/{session_id}")
async def clear_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """Clear chat history for a session."""
    await db.execute(
        delete(CustomChatMessage).where(CustomChatMessage.session_id == session_id)
    )
    await db.commit()
    return {"message": "Session cleared"}


# ========== TTS TESTER ENDPOINT ==========

class TTSRequest(BaseModel):
    text: str
    language: str = "fr"

class TTSResponse(BaseModel):
    audio_url: str
    text: str
    language: str

@router.post("/tts", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """
    Generate TTS audio from text.
    Uses ADIA_TTS for Wolof ('wo'), OpenAI TTS for others.
    """
    audio_service = get_audio_service()
    
    try:
        audio_path = await audio_service.text_to_speech(request.text, language=request.language)
        # Extract filename from path
        filename = audio_path.replace("\\", "/").split("/")[-1]
        audio_url = f"/uploads/{filename}"
        
        return TTSResponse(
            audio_url=audio_url,
            text=request.text,
            language=request.language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
