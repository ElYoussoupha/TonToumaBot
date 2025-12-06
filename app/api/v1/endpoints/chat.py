import json
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.crud import crud_chat, crud_entity
from app.models.chat import Session, Message, Speaker
from app.schemas import chat as schemas

router = APIRouter()

# Fixed speaker ID for demo/testing purposes
# In production, implement real speaker identification
DEFAULT_SPEAKER_ID = None  # Cached value
FIXED_SPEAKER_UUID = UUID("11111111-1111-1111-1111-111111111111")

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

from typing import Optional, Annotated

async def get_or_create_default_speaker(db: AsyncSession) -> UUID:
    """Get or create a fixed default speaker for all users using a specific UUID"""
    global DEFAULT_SPEAKER_ID
    if DEFAULT_SPEAKER_ID:
        return DEFAULT_SPEAKER_ID

    from sqlalchemy import select
    # Try to fetch by fixed UUID
    stmt = select(Speaker).filter(Speaker.speaker_id == FIXED_SPEAKER_UUID)
    result = await db.execute(stmt)
    speaker = result.scalars().first()

    if not speaker:
        # Create with fixed UUID
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

@router.post("/messages", response_model=dict)
async def handle_voice_message(
    instance_id: Annotated[str, Form(...)],
    audio_file: Annotated[UploadFile, File(...)],
    speaker_id: Annotated[Optional[str], Form()] = None,
    metadata: Annotated[Optional[str], Form()] = None,
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
    
    # 3. Use fixed speaker ID for everyone
    speaker_uuid = await get_or_create_default_speaker(db)
    
    # 4. Get Entity & Session
    instance = await crud_entity.instance.get(db=db, id=instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Find active session
    from sqlalchemy import select
    stmt = select(Session).filter(
        Session.entity_id == instance.entity_id,
        Session.speaker_id == speaker_uuid,
        Session.is_active == True
    ).order_by(Session.created_at.desc())
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        session = Session(entity_id=instance.entity_id, speaker_id=speaker_uuid, is_active=True)
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
    query_embedding = await rag_service.embed_text(transcription)
    chunks = await rag_service.search_kb(db, instance.entity_id, query_embedding)
    
    context = ""
    if chunks:
        context = "\n\n".join([f"Source: {chunk.document.title}\nContent: {chunk.content}" for chunk in chunks])
    else:
        context = "Aucune information pertinente trouvée dans la base de connaissances."
    
    # 7. LLM
    # Get history
    previous_messages = await crud_chat.message.get_by_session_id(db=db, session_id=session.session_id)
    # Format history for LLM (last 10 messages)
    history = ""
    for msg in previous_messages[-10:]:
        role_label = "User" if msg.role == "user" else "Assistant"
        history += f"{role_label}: {msg.content}\n"

    system_instruction = """Tu es un assistant virtuel utile et professionnel pour l'Hôpital Fann. 
    Utilise le contexte fourni pour répondre aux questions. 
    Si la réponse n'est pas dans le contexte, dis poliment que tu ne sais pas ou propose de contacter le secrétariat.
    Sois concis et clair."""
    
    response_text = await llm_service.generate_response(
        system_instruction, context, history, transcription
    )
    
    # 8. Save Assistant Message
    response_audio_path = await audio_service.text_to_speech(response_text)
    
    assistant_msg = Message(
        session_id=session.session_id,
        instance_id=instance_id,
        role="assistant",
        content=response_text,
        audio_path=response_audio_path
    )
    db.add(assistant_msg)
    await db.commit()
    
    return {
        "speaker_id": str(speaker_uuid),
        "session_id": str(session.session_id),
        "transcription": transcription,  # User's transcribed text
        "user_audio": audio_path,  # User's audio path
        "response_text": response_text,
        "response_audio": response_audio_path
    }

@router.post("/text", response_model=dict)
async def handle_text_message(
    *,
    instance_id: str = Body(...),
    text: str = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """Process a text message for the chatbot with appointment booking support."""
    # Get services
    audio_service = get_audio_service()
    rag_service = get_rag_service()
    llm_service = get_llm_service()

    # 1. Use fixed speaker ID
    speaker_uuid = await get_or_create_default_speaker(db)

    # 2. Get Entity & Session
    instance = await crud_entity.instance.get(db=db, id=instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    from sqlalchemy import select
    stmt = select(Session).filter(
        Session.entity_id == instance.entity_id,
        Session.speaker_id == speaker_uuid,
        Session.is_active == True
    ).order_by(Session.created_at.desc())
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        session = Session(entity_id=instance.entity_id, speaker_id=speaker_uuid, is_active=True)
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # 3. Save User Message (text only)
    user_msg = Message(
        session_id=session.session_id,
        instance_id=instance_id,
        role="user",
        content=text,
        audio_path=None
    )
    db.add(user_msg)
    await db.commit()

    # 4. RAG
    query_embedding = await rag_service.embed_text(text)
    chunks = await rag_service.search_kb(db, instance.entity_id, query_embedding)

    context = ""
    if chunks:
        context = "\n\n".join([f"Source: {chunk.document.title}\nContent: {chunk.content}" for chunk in chunks])
    else:
        context = "Aucune information pertinente trouvée dans la base de connaissances."

    # 5. LLM with history and function calling
    previous_messages = await crud_chat.message.get_by_session_id(db=db, session_id=session.session_id)
    history = ""
    for msg in previous_messages[-10:]:
        role_label = "User" if msg.role == "user" else "Assistant"
        history += f"{role_label}: {msg.content}\n"

    system_instruction = """Tu es un assistant virtuel professionnel et amical pour l'Hôpital Fann. 
    
    COMPORTEMENT GÉNÉRAL:
    - Réponds aux questions des utilisateurs en utilisant la base de connaissances
    - Sois naturel et conversationnel
    - N'insiste PAS sur les rendez-vous si l'utilisateur ne le demande pas
    - Attends que l'utilisateur exprime clairement le besoin d'un rendez-vous
    
    PRISE DE RENDEZ-VOUS (uniquement si demandé):
    - Si l'utilisateur demande un rendez-vous, guide-le naturellement
    - Accepte les dates en langage naturel ("lundi", "demain", "la semaine prochaine")
    - Utilise parse_natural_date pour convertir les dates naturelles
    - Collecte les informations progressivement sans bombarder de questions
    - Confirme clairement quand le rendez-vous est réservé
    
    Sois concis, professionnel et à l'écoute."""


    # Try with function calling first
    llm_result = await llm_service.generate_response_with_tools(
        system_instruction, context, history, text
    )
    
    response_text = ""
    
    # Handle function calls
    if llm_result["type"] == "function_call":
        func_name = llm_result["content"]["name"]
        func_args = llm_result["content"]["args"]
        
        func_result = await execute_appointment_function(
            db, instance.entity_id, session.session_id, func_name, func_args
        )
        
        # Continue conversation with function result
        continuation = await llm_service.continue_with_function_result(
            f"System: {system_instruction}\nContext: {context}\nHistory: {history}\nUser: {text}",
            func_name,
            json.dumps(func_result, ensure_ascii=False, default=str)
        )
        
        # Handle nested function calls (max 3 iterations)
        for _ in range(3):
            if continuation["type"] == "function_call":
                nested_func_name = continuation["content"]["name"]
                nested_func_args = continuation["content"]["args"]
                nested_result = await execute_appointment_function(
                    db, instance.entity_id, session.session_id, nested_func_name, nested_func_args
                )
                continuation = await llm_service.continue_with_function_result(
                    f"Previous result for {nested_func_name}",
                    nested_func_name,
                    json.dumps(nested_result, ensure_ascii=False, default=str)
                )
            else:
                break
        
        response_text = continuation["content"]
    else:
        response_text = llm_result["content"]

    # 6. Save Assistant Message (with TTS)
    response_audio_path = await audio_service.text_to_speech(response_text)

    assistant_msg = Message(
        session_id=session.session_id,
        instance_id=instance_id,
        role="assistant",
        content=response_text,
        audio_path=response_audio_path
    )
    db.add(assistant_msg)
    await db.commit()

    return {
        "speaker_id": str(speaker_uuid),
        "session_id": str(session.session_id),
        "transcription": text,
        "user_audio": None,
        "response_text": response_text,
        "response_audio": response_audio_path
    }


def parse_natural_date(date_str: str) -> str:
    """Parse natural language dates to YYYY-MM-DD format"""
    from datetime import datetime, timedelta
    import re
    
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
            # Find next occurrence of this day
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            if "prochain" in date_str or "prochaine" in date_str:
                days_ahead += 7  # Next week
            return (today + timedelta(days=days_ahead)).isoformat()
    
    # Try to parse as YYYY-MM-DD
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except:
        pass
    
    # Default: return as-is and let the backend handle it
    return date_str


async def execute_appointment_function(
    db: AsyncSession, 
    entity_id, 
    session_id,
    func_name: str, 
    func_args: dict
) -> dict:
    """Execute an appointment-related function call"""
    from datetime import datetime, date, time
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
            
            if not date_str:
                return {"success": False, "message": "Veuillez préciser une date."}
            
            # Parse natural language date
            parsed_date_str = parse_natural_date(date_str)
            
            try:
                target_date = datetime.strptime(parsed_date_str, "%Y-%m-%d").date()
            except:
                return {"success": False, "message": f"Je n'ai pas compris la date '{date_str}'. Pouvez-vous préciser (ex: lundi, demain, 2025-01-15)?"}
            
            # Search by specialty name if no doctor_id
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
                return {"success": False, "message": "Aucun créneau disponible à cette date."}
        
        elif func_name == "book_appointment":
            required = ["doctor_id", "date", "time", "patient_name", "patient_email", "reason"]
            missing = [f for f in required if not func_args.get(f)]
            if missing:
                return {"success": False, "message": f"Informations manquantes: {', '.join(missing)}"}
            
            # Parse natural language date
            parsed_date_str = parse_natural_date(func_args["date"])
            
            try:
                target_date = datetime.strptime(parsed_date_str, "%Y-%m-%d").date()
                target_time = datetime.strptime(func_args["time"], "%H:%M").time()
            except Exception as e:
                return {"success": False, "message": f"Format de date ou heure invalide: {str(e)}"}
            
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
                "success": result.success,
                "message": result.message,
                "appointment_id": str(result.appointment_id) if result.appointment_id else None,
                "doctor_name": result.doctor_name,
                "date": result.date.isoformat() if result.date else None,
                "time": result.time.strftime("%H:%M") if result.time else None
            }
        
        else:
            return {"success": False, "message": f"Fonction inconnue: {func_name}"}
            
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}
