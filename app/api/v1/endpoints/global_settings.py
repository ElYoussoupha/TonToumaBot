"""
Global Settings Endpoints
Manages server-wide configuration like global forced language.
"""
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Optional, Literal

router = APIRouter()

# In-memory storage for global settings (simple approach)
_global_settings = {
    "forced_language": None  # None means auto-detect
}

class GlobalLanguageResponse(BaseModel):
    forced_language: Optional[str] = None
    available_languages: list[str] = ["none", "wo", "fr", "en", "ar", "es"]

class SetGlobalLanguageRequest(BaseModel):
    language: Literal["none", "wo", "fr", "en", "ar", "es"]

def get_global_forced_language() -> Optional[str]:
    """Get the current global forced language. Returns None if 'none' or not set."""
    lang = _global_settings.get("forced_language")
    return lang if lang and lang != "none" else None

@router.get("/global_language", response_model=GlobalLanguageResponse)
async def get_global_language():
    """Get the current global forced language setting."""
    return GlobalLanguageResponse(
        forced_language=_global_settings.get("forced_language"),
        available_languages=["none", "wo", "fr", "en", "ar", "es"]
    )

@router.post("/global_language", response_model=GlobalLanguageResponse)
async def set_global_language(request: SetGlobalLanguageRequest):
    """Set the global forced language. Use 'none' for auto-detect."""
    _global_settings["forced_language"] = request.language if request.language != "none" else None
    print(f"[Settings] Global forced language set to: {request.language}")
    return GlobalLanguageResponse(
        forced_language=_global_settings.get("forced_language"),
        available_languages=["none", "wo", "fr", "en", "ar", "es"]
    )
