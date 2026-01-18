import json
from uuid import UUID
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.crud import crud_chat, crud_entity
from app.models.chat import Session, Message, Speaker
from app.schemas import chat as schemas

router = APIRouter()

# Fixed speaker ID for demo/testing purposes
DEFAULT_SPEAKER_ID = None
FIXED_SPEAKER_UUID = UUID("11111111-1111-1111-1111-111111111111")

# Lazy-loaded services
_audio_service = None
_rag_service = None
_llm_service = None

def get_audio_service() -> "AudioService":
    global _audio_service
    if _audio_service is None:
        from app.services.audio import AudioService
        _audio_service = AudioService(settings.UPLOAD_DIR)
    return _audio_service

def get_rag_service() -> "RAGService":
    global _rag_service
    if _rag_service is None:
        from app.services.rag import RAGService
        _rag_service = RAGService()
    return _rag_service

def get_llm_service() -> "LLMService":
    global _llm_service
    if _llm_service is None:
        from app.services.llm import LLMService
        _llm_service = LLMService()
    return _llm_service

async def get_or_create_default_speaker(db: AsyncSession) -> UUID:
    """Get or create a fixed default speaker for all users"""
    global DEFAULT_SPEAKER_ID
    if DEFAULT_SPEAKER_ID:
        return DEFAULT_SPEAKER_ID

    stmt = select(Speaker).filter(Speaker.speaker_id == FIXED_SPEAKER_UUID)
    result = await db.execute(stmt)
    speaker = result.scalars().first()

    if not speaker:
        speaker = Speaker(
            speaker_id=FIXED_SPEAKER_UUID,
            fingerprint_hash="fixed-speaker",
            embedding=[0.0] * 256
        )
        db.add(speaker)
        await db.commit()
        await db.refresh(speaker)

    DEFAULT_SPEAKER_ID = speaker.speaker_id
    return DEFAULT_SPEAKER_ID

async def execute_appointment_function(
    db: AsyncSession, 
    entity_id, 
    session_id,
    func_name: str, 
    func_args: dict
) -> dict:
    """Execute an appointment-related function call"""
    from datetime import datetime
    from app.services.appointment_service import appointment_service
    from app.schemas.appointment import BookAppointmentRequest
    from uuid import UUID
    
    try:
        if func_name == "search_doctors":
            specialty = func_args.get("specialty")
            doctors = await appointment_service.search_doctors(
                db=db,
                entity_id=entity_id,
                specialty_name=specialty
            )
            if doctors:
                return {"success": True, "doctors": doctors}
            else:
                return {"success": False, "message": "Aucun médecin trouvé pour cette spécialité."}
        
        elif func_name == "get_available_slots":
            date_str = func_args.get("date")
            doctor_id = func_args.get("doctor_id")
            specialty = func_args.get("specialty")
            
            if date_str:
                parsed_date_str = parse_natural_date(date_str)
                try:
                    target_date = datetime.strptime(parsed_date_str, "%Y-%m-%d").date()
                except:
                    # If date parsing fails, ignore date and search generic
                    target_date = None
            else:
                target_date = None
            
            specialty_id = None
            if specialty and not doctor_id:
                from app.crud.crud_appointment import specialty as specialty_crud
                spec = await specialty_crud.get_by_name(db=db, name=specialty)
                if spec:
                    specialty_id = spec.specialty_id
            
            slots = await appointment_service.get_available_slots(
                db=db,
                entity_id=entity_id,
                target_date=target_date,
                specialty_id=specialty_id,
                doctor_id=UUID(doctor_id) if doctor_id else None
            )
            
            if slots:
                return {
                    "success": True, 
                    "slots": [
                        {
                            "doctor_id": str(s.doctor_id),
                            "doctor_name": s.doctor_name,
                            "specialty": s.specialty_name,
                            "date": s.date.isoformat(),
                            "start_time": s.start_time.strftime("%H:%M"),
                            "end_time": s.end_time.strftime("%H:%M")
                        }
                        for s in slots
                    ]
                }
            else:
                return {"success": False, "message": "Aucun créneau trouvé dans les prochains jours."}
        
        elif func_name == "book_appointment":
            required = ["doctor_id", "date", "time", "patient_name", "patient_email", "reason"]
            missing = [f for f in required if not func_args.get(f)]
            if missing:
                return {"success": False, "message": f"Informations manquantes: {', '.join(missing)}"}
            
            parsed_date_str = parse_natural_date(func_args["date"])
            try:
                target_date = datetime.strptime(parsed_date_str, "%Y-%m-%d").date()
                target_time = datetime.strptime(func_args["time"], "%H:%M").time()
            except Exception as e:
                return {"success": False, "message": f"Format invalide: {str(e)}"}
            
            request = BookAppointmentRequest(
                entity_id=entity_id,
                doctor_id=UUID(func_args["doctor_id"]),
                date=target_date,
                start_time=target_time,
                patient_name=func_args["patient_name"],
                patient_email=func_args["patient_email"],
                patient_phone=func_args.get("patient_phone"),
                reason=func_args["reason"],
                session_id=session_id
            )
            
            result = await appointment_service.book_appointment(db=db, request=request)
            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "appointment_id": result.get("appointment_id"),
                "doctor_name": result.get("doctor_name"),
                "date": result.get("date"),
                "start_time": result.get("start_time"),
                "end_time": result.get("end_time")
            }
        
        else:
            return {"success": False, "message": f"Fonction inconnue: {func_name}"}
            
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}

async def process_chat_request(
    db: AsyncSession,
    instance_id: str,
    user_input: str,
    audio_path: Optional[str] = None,
    detected_language: str = "fr",
    forced_language: Optional[str] = None,
    session_id: Optional[str] = None
) -> dict:
    """
    Common logic for processing both text and voice chat requests.
    Handles RAG, History, LLM, Tools, and Persistence.
    For Wolof (wo): translates input to French, processes, then translates back.
    """
    rag_service = get_rag_service()
    llm_service = get_llm_service()
    audio_service = get_audio_service()
    
    # Import global settings function
    from app.api.v1.endpoints.global_settings import get_global_forced_language
    
    # Cascading priority: per-request forced_language > global setting > detected_language
    if forced_language and forced_language != "auto":
        lang_to_use = forced_language
    else:
        global_lang = get_global_forced_language()
        if global_lang:
            lang_to_use = global_lang
        else:
            lang_to_use = detected_language
    
    # Normalize language code
    if lang_to_use == "wolof":
        lang_to_use = "wo"

    # Wolof handling: translate input to French for processing
    is_wolof = lang_to_use == "wo"
    original_user_input = user_input
    
    if is_wolof:
        print(f"[Wolof] Detected Wolof input, translating to French...")
        user_input = await llm_service.translate_wolof_to_french(user_input)
        print(f"[Wolof] Translated: {user_input}")

    # 1. Setup Session
    speaker_uuid = await get_or_create_default_speaker(db)
    instance = await crud_entity.instance.get(db=db, id=instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    session = None
    if session_id:
        # Try to fetch specific session
        stmt = select(Session).filter(Session.session_id == UUID(session_id))
        result = await db.execute(stmt)
        session = result.scalars().first()
        
        if not session:
            print(f"[Warn] Session {session_id} not found, falling back to new session")
    
    # If no session_id provided or not found, try to find last active session for this speaker/instance
    if not session:
        stmt = select(Session).filter(
            Session.entity_id == instance.entity_id,
            Session.speaker_id == speaker_uuid,
            Session.is_active == True
        ).order_by(Session.created_at.desc())
        result = await db.execute(stmt)
        session = result.scalars().first()

    # Create new session if still none
    if not session:
        session = Session(entity_id=instance.entity_id, speaker_id=speaker_uuid, is_active=True)
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # 2. Save User Message
    user_msg = Message(
        session_id=session.session_id,
        instance_id=instance_id,
        role="user",
        content=original_user_input, # Always save original input in 'content' for UI
        translated_content=user_input if is_wolof else None, # Save French translation if Wolof
        audio_path=audio_path
    )
    db.add(user_msg)
    await db.commit()

    # 3. RAG Context
    query_embedding = await rag_service.embed_text(user_input)
    chunks = await rag_service.search_kb(db, instance.entity_id, query_embedding)
    
    context = ""
    if chunks:
        context = "\n\n".join([f"Source: {chunk.document.title}\nContent: {chunk.content}" for chunk in chunks])
    else:
        context = "Aucune information pertinente trouvée dans la base de connaissances."

    # 4. Build History (including previous tools outputs)
    # Exclude the current user message we just saved, because we pass the translated version as explicit input
    previous_messages = await crud_chat.message.get_by_session_id(db=db, session_id=session.session_id)
    history = ""
    # Take last 15 messages excluding the very last one (current user msg)
    msgs_to_process = previous_messages[:-1] if previous_messages else []
    for msg in msgs_to_process[-15:]:
        # Use translated content for history if available, otherwise regular content
        msg_content = msg.translated_content if msg.translated_content else msg.content
        
        if msg.role == "user":
            history += f"User: {msg_content}\n"
        elif msg.role == "assistant":
            # Assistant messages are already in French (translated for invalid output only)
            # Actually, we should check if assistant message has a translation? 
            # Logic: Assistant writes in French (content), then we translate to Wolof for UI display.
            # But in DB we just saved 'display_response_text' which might be Wolof.
            # Wait, let's fix assistant saving too later. For now assume content is fine or check below.
            history += f"Assistant: {msg_content}\n"
        elif msg.role == "tool":
            # Include tool outputs in history so LLM remembers IDs
            history += f"System (Tool Output): {msg.content}\n"

    # 5. System Instruction - Use entity-specific prompt if available
    # Fetch entity first to avoid lazy loading issues in async context
    from app.models.entity import Entity
    entity_stmt = select(Entity).filter(Entity.entity_id == instance.entity_id)
    entity_result = await db.execute(entity_stmt)
    entity = entity_result.scalars().first()
    
    entity_name = entity.name if entity else 'cette organisation'
    
    if entity and entity.system_prompt:
        system_instruction = entity.system_prompt
        print(f"[Chat] Using custom system prompt for entity: {entity.name}")
    else:
        system_instruction = f"""Tu es un assistant virtuel professionnel et amical pour {entity_name}. 
    
    COMPORTEMENT GÉNÉRAL:
    - Réponds aux questions des utilisateurs en utilisant la base de connaissances
    - Sois naturel et conversationnel
    - IMPORTANT: Ne mets JAMAIS de formattage markdown (pas de gras, pas d'italique, pas d'étoiles *). Le texte sera lu par un outil de synthèse vocale qui lit les caractères spéciaux. Écris en texte brut uniquement.
    """
        print(f"[Chat] Using default system prompt")

    # 6. LLM Interaction Loop (Handle Tools)
    current_text = user_input
    final_response_text = ""
    
    # Initial LLM call
    llm_result = await llm_service.generate_response_with_tools(
        system_instruction, context, history, current_text
    )

    # Max loops for nested tools
    for _ in range(5):
        if llm_result["type"] == "function_call":
            func_name = llm_result["content"]["name"]
            func_args = llm_result["content"]["args"]
            
            # Execute tool
            print(f"🔧 Calling tool: {func_name} with {func_args}")
            func_result = await execute_appointment_function(
                db, instance.entity_id, session.session_id, func_name, func_args
            )
            print(f"✅ Tool result: {func_result}")
            
            func_result_str = json.dumps(func_result, ensure_ascii=False, default=str)

            # PERSIST Tool Result in DB
            tool_msg = Message(
                session_id=session.session_id,
                instance_id=instance_id,
                role="tool",
                content=f"Function: {func_name}\nResult: {func_result_str}",
                audio_path=None
            )
            db.add(tool_msg)
            await db.commit()

            # Append to history for current context
            history += f"\nSystem (Tool Output for {func_name}): {func_result_str}\n"
            
            # Continue conversation
            llm_result = await llm_service.continue_with_function_result(
                system_instruction, # Passing the French system prompt
                func_name,
                func_result_str
            )
        else:
            # Text response
            final_response_text = llm_result["content"]
            break
    
    if not final_response_text:
        final_response_text = "Désolé, je rencontre une erreur technique."
    
    # Wolof handling: translate response back to Wolof
    display_response_text = final_response_text
    if is_wolof:
        print(f"[Wolof] French response: {final_response_text}")
        print(f"[Wolof] Translating response to Wolof...")
        display_response_text = await llm_service.translate_french_to_wolof(final_response_text)
        print(f"[Wolof] Wolof response: {display_response_text}")

    # 7. Generate Audio Response (use specified language TTS)
    response_audio_path = await audio_service.text_to_speech(
        display_response_text, 
        language=lang_to_use
    )

    # 8. Save Assistant Response (save translated version)
    # We save the French version as primary content for LLM context in future
    # But wait, if we save French in content, UI will show French.
    # The requirement is: UI shows Wolof, LLM sees French.
    # So 'content' should be Wolof (display_response_text), 'translated_content' should be French (final_response_text).
    
    assistant_msg = Message(
        session_id=session.session_id,
        instance_id=instance_id,
        role="assistant",
        content=display_response_text, # Wolof (if translated) or French
        translated_content=final_response_text if is_wolof else None, # French source
        audio_path=response_audio_path
    )
    db.add(assistant_msg)
    await db.commit()

    return {
        "speaker_id": str(speaker_uuid),
        "session_id": str(session.session_id),
        "transcription": original_user_input if is_wolof else user_input,
        "user_audio": audio_path,
        "response_text": display_response_text,
        "response_audio": response_audio_path,
        "detected_language": detected_language,
        "forced_language": forced_language
    }

@router.post("/sessions", response_model=dict)
async def create_new_session(
    instance_id: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new chat session for a specific instance.
    Returns the session_id to be used in subsequent requests.
    """
    speaker_uuid = await get_or_create_default_speaker(db)
    
    # Verify instance existence
    instance = await crud_entity.instance.get(db=db, id=instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
        
    # Always create a FRESH session
    new_session = Session(
        entity_id=instance.entity_id, 
        speaker_id=speaker_uuid, 
        is_active=True
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return {
        "success": True, 
        "session_id": str(new_session.session_id),
        "instance_id": str(instance.instance_id),
        "entity_id": str(instance.entity_id)
    }

@router.get("/sessions", response_model=List[Dict[str, Any]])
async def list_sessions(
    instance_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    List all sessions for a specific instance (and default speaker).
    Returns basic info: session_id, created_at, message_count, last_message_preview.
    """
    speaker_uuid = await get_or_create_default_speaker(db)
    
    # Verify instance
    instance = await crud_entity.instance.get(db=db, id=instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    # Fetch sessions
    sessions_stmt = select(Session).filter(
        Session.entity_id == instance.entity_id,
        Session.speaker_id == speaker_uuid
    ).order_by(Session.created_at.desc())
    
    result = await db.execute(sessions_stmt)
    sessions = result.scalars().all()
    
    response = []
    for sess in sessions:
        # Get message count and last message
        msgs_stmt = select(Message).filter(Message.session_id == sess.session_id).order_by(Message.created_at.desc())
        msgs_result = await db.execute(msgs_stmt)
        messages = msgs_result.scalars().all()
        
        count = len(messages)
        if count == 0:
            continue # Skip empty sessions if desired, or keep them
            
        last_msg = messages[0] if messages else None
        preview = last_msg.content[:50] + "..." if last_msg and last_msg.content else "Nouvelle session"
        
        response.append({
            "session_id": str(sess.session_id),
            "created_at": sess.created_at,
            "message_count": count,
            "preview": preview
        })
        
    return response

@router.post("/messages", response_model=dict)
async def handle_voice_message(
    instance_id: str = Form(...),
    audio_file: UploadFile = File(...),
    speaker_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    forced_language: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    audio_service = get_audio_service()
    
    # Save & Transcribe (supports forced language to bypass LID)
    audio_path = await audio_service.save_upload_file(audio_file)
    transcription, final_lang = await audio_service.transcribe(audio_path, forced_language=forced_language)
    
    print(f"[Chat] Voice message - Forced: {forced_language}, Detected: {final_lang}, Text: {transcription[:50]}...")
    
    # Process with language info
    return await process_chat_request(
        db, instance_id, transcription, audio_path, 
        detected_language=final_lang, 
        forced_language=forced_language,
        session_id=session_id
    )

@router.post("/text", response_model=dict)
async def handle_text_message(
    instance_id: str = Body(...),
    text: str = Body(...),
    forced_language: Optional[str] = Body(None),
    session_id: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_db)
):
    if not forced_language or forced_language == "auto":
        llm_service = get_llm_service()
        detected_language = await llm_service.detect_language(text)
    else:
        detected_language = forced_language
    
    import logging
    logger = logging.getLogger("uvicorn")
    logger.info(f"[Chat] Text message - Forced: {forced_language}, Detected: {detected_language}, Text: {text[:50]}...")
    
    # Process with language info (same pipeline as voice)
    return await process_chat_request(
        db, instance_id, text, None, 
        detected_language=detected_language,
        forced_language=forced_language,
        session_id=session_id
    )

def parse_natural_date(date_str: str) -> str:
    """Parse natural language dates to YYYY-MM-DD format"""
    from datetime import datetime, timedelta
    
    date_str = date_str.lower().strip()
    today = datetime.now().date()
    
    # Direct formats
    if date_str in ["aujourd'hui", "auj", "today"]:
        return today.isoformat()
    elif date_str in ["demain", "tomorrow"]:
        return (today + timedelta(days=1)).isoformat()
    elif date_str in ["après-demain", "apres-demain"]:
        return (today + timedelta(days=2)).isoformat()
    
    # Days of week
    days_fr = {
        "lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3,
        "vendredi": 4, "samedi": 5, "dimanche": 6
    }
    
    for day_name, day_num in days_fr.items():
        if day_name in date_str:
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            if "prochain" in date_str or "prochaine" in date_str:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).isoformat()
            
    # Try to parse as YYYY-MM-DD
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except:
        pass
        
    return date_str
