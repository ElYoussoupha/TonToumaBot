from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import crud_chat
from app.schemas import chat as schemas

router = APIRouter()

# --- Sessions ---
@router.post("/sessions", response_model=schemas.SessionResponse)
async def create_session(
    *,
    db: AsyncSession = Depends(get_db),
    session_in: schemas.SessionCreate
) -> Any:
    """
    Create new session.
    """
    return await crud_chat.session.create(db=db, obj_in=session_in)

@router.get("/sessions", response_model=List[schemas.SessionResponse])
async def read_sessions(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve sessions.
    """
    return await crud_chat.session.get_multi(db=db, skip=skip, limit=limit)

@router.get("/sessions/{session_id}", response_model=schemas.SessionResponse)
async def read_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get session by ID.
    """
    session = await crud_chat.session.get(db=db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/sessions/{session_id}", response_model=schemas.SessionResponse)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a session.
    """
    session = await crud_chat.session.get(db=db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await crud_chat.session.remove(db=db, id=session_id)

# --- Messages ---
@router.post("/messages", response_model=schemas.MessageResponse)
async def create_message(
    *,
    db: AsyncSession = Depends(get_db),
    message_in: schemas.MessageCreate
) -> Any:
    """
    Create new message.
    """
    return await crud_chat.message.create(db=db, obj_in=message_in)

@router.get("/messages/{session_id}", response_model=List[schemas.MessageResponse])
async def read_messages(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retrieve messages for a session.
    """
    return await crud_chat.message.get_by_session_id(db=db, session_id=session_id)

@router.delete("/messages/{message_id}", response_model=schemas.MessageResponse)
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a message.
    """
    message = await crud_chat.message.get(db=db, id=message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return await crud_chat.message.remove(db=db, id=message_id)
