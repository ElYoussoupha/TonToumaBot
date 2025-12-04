from fastapi import APIRouter
from app.api.v1.endpoints import entities, users, sessions, knowledge, chat

api_router = APIRouter()
api_router.include_router(entities.router, tags=["entities", "instances"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(sessions.router, tags=["sessions", "messages"])
api_router.include_router(knowledge.router, prefix="/kb", tags=["knowledge-base"])
api_router.include_router(chat.router, prefix="/chat", tags=["voice-chat"])
