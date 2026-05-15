"""Voice Router — POST /api/voice/analyze"""
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, status
from typing import Optional
from app.models.schemas import VoiceAnalysisResponse
from app.services.voice_service import analyze_voice, SUPPORTED_AUDIO_FORMATS

router = APIRouter(prefix="/api/voice", tags=["Voice"])


@router.post("/analyze", response_model=VoiceAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_voice_message(audio: UploadFile = File(...), session_id: Optional[str] = Form(None), user_id: Optional[str] = Form(None)):
    content_type = audio.content_type or "audio/wav"
    if content_type not in SUPPORTED_AUDIO_FORMATS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Unsupported format: {content_type}")
    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is empty.")
    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio file too large. Max 25MB.")
    try:
        return await analyze_voice(audio_bytes=audio_bytes, content_type=content_type, session_id=session_id or str(uuid.uuid4()), conversation_history=[])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Voice analysis failed: {str(e)}")


@router.get("/health")
async def voice_health():
    return {"status": "healthy", "service": "NeuroNest Voice"}
