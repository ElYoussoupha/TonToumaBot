from fastapi import APIRouter
from app.api.v1.endpoints import entities, users, sessions, knowledge, chat
from app.api.v1.endpoints import specialties, doctors, timeslots, appointments
from app.api.v1.endpoints import custom_chat, global_settings

api_router = APIRouter()
api_router.include_router(entities.router, tags=["entities", "instances"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(sessions.router, tags=["sessions", "messages"])
api_router.include_router(knowledge.router, prefix="/kb", tags=["knowledge-base"])
api_router.include_router(chat.router, prefix="/chat", tags=["voice-chat"])

# Appointment system routes
api_router.include_router(specialties.router, prefix="/specialties", tags=["specialties"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
api_router.include_router(timeslots.router, prefix="/timeslots", tags=["timeslots"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])

# Custom chatbot (temporary)
api_router.include_router(custom_chat.router)

# Global settings
api_router.include_router(global_settings.router, prefix="/settings", tags=["settings"])
