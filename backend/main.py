import os
import uuid
import json
import asyncio
import shutil
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from core.config import settings
from core.logger import logger
from core.exceptions import domain_error_handler, http_exception_handler, unhandled_exception_handler
from domain.exceptions import DomainError
from models.interaction import InteractionCreate, AudioFeatures, EmotionData
from repositories.interaction_repo import interaction_repo, InteractionRepository
from infrastructure.mongodb_client import init_db, close_db

from services.dashboard_service import update_dashboard
from services.rag_service import rag_service
from di import container

app = FastAPI(title="NeuroNest Voice Assistant")

app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.GENERATED_DIR, exist_ok=True)

# Hardcoded user_id for the single-user hackathon build
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"


@app.on_event("startup")
async def startup_event():
    await init_db()                    # ensure MongoDB indexes exist
    await interaction_repo.create_user()  # upsert the default user
    logger.info("NeuroNest Backend Started — MongoDB backend active")


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
    logger.info("NeuroNest Backend Shutdown — MongoDB connection closed")


# ──────────────────────────────────────────────────────────────────────────────
# /session-start — Returns a personalised text greeting based on last emotion
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/session-start")
async def session_start(
    repo: InteractionRepository = Depends(lambda: interaction_repo)
):
    """
    Called by the frontend when the app loads / a new session begins.
    Returns a personalised text greeting derived from the user's last known
    emotional state. No TTS — displayed as a chat message only.
    """
    try:
        greeting = await rag_service.get_session_opener(
            supabase_client=None,  # MongoDB — rag_service ignores this arg now
            user_id=DEFAULT_USER_ID,
            current_session_id=None,
        )
        return {"greeting": greeting}
    except Exception as e:
        logger.error(f"Session-start error: {e}")
        return {"greeting": None}


# ──────────────────────────────────────────────────────────────────────────────
# /process-voice — Main voice pipeline with RAG memory
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/process-voice")
async def process_voice(
    file: UploadFile = File(...),
    audio_analysis: Optional[str] = Form(None),
    video_analysis: Optional[str] = Form(None),
    voice_name: Optional[str] = Form("Rachel"),
    expression_history: Optional[str] = Form(None),
):
    """Main voice processing pipeline. Delegates to clean ConversationOrchestrator."""
    try:
        file_id = str(uuid.uuid4())
        input_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.webm")

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        orchestrator = container.conversation_orchestrator
        result = await orchestrator.process_conversation(
            audio_path=input_path,
            audio_analysis=audio_analysis,
            video_analysis=video_analysis,
            voice_name=voice_name,
        )
        
        # Add legacy dashboard key for backward compatibility
        result["dashboard"] = update_dashboard(result["transcript"], result["emotion"])
        return result

    except Exception as e:
        logger.critical(f"Pipeline Crash: {e}")
        return {"error": "Internal Server Error", "detail": str(e)}


# New incremental endpoint using the Clean Architecture use-case (non-breaking)
@app.post("/process-voice-v2")
async def process_voice_v2(
    file: UploadFile = File(...),
    audio_analysis: Optional[str] = Form(None),
    video_analysis: Optional[str] = Form(None),
    voice_name: Optional[str] = Form("Rachel"),
    expression_history: Optional[str] = Form(None),
):
    """Legacy v2 endpoint, now alias for v3."""
    return await process_voice_v3(file, audio_analysis, video_analysis, voice_name, expression_history)


# New route using the conversation orchestrator (clean architecture)
@app.post("/process-voice-v3")
async def process_voice_v3(
    file: UploadFile = File(...),
    audio_analysis: Optional[str] = Form(None),
    video_analysis: Optional[str] = Form(None),
    voice_name: Optional[str] = Form("Rachel"),
    expression_history: Optional[str] = Form(None),
):
    """New route using the conversation orchestrator with clean architecture."""
    try:
        import uuid
        import shutil
        
        file_id = str(uuid.uuid4())
        input_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.webm")
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        orchestrator = container.conversation_orchestrator
        result = await orchestrator.process_conversation(
            audio_path=input_path,
            audio_analysis=audio_analysis,
            video_analysis=video_analysis,
            voice_name=voice_name,
            expression_history=expression_history,
        )
        return result
    except Exception as e:
        logger.critical(f"Process-Voice-V3 Crash: {e}")
        return {"error": "Internal Server Error", "detail": str(e)}


async def _store_embedding_async(
    repo: InteractionRepository,
    interaction_id: str,
    transcript: str,
):
    """
    Fire-and-forget coroutine: generate an embedding for the transcript
    and persist it to Supabase. Runs after the response is already sent.
    """
    try:
        embedding = await asyncio.get_event_loop().run_in_executor(
            None, rag_service.generate_embedding, transcript
        )
        if embedding:
            await repo.store_embedding(interaction_id, embedding)
    except Exception as e:
        logger.error(f"RAG: Background embedding task failed — {e}")


@app.post("/preview-voice")
async def preview_voice(voice_name: str = Form(...)):
    try:
        preview_text = f"Hello! I am {voice_name}, your NeuroNest assistant. I am ready to help you."
        audio_path = container.tts_provider.synthesize(preview_text, "neutral", voice_name)
        if audio_path:
            return {"audio_url": f"http://localhost:8000/audio/{os.path.basename(audio_path)}"}
        return {"error": "Failed to generate preview"}
    except Exception as e:
        logger.error(f"Preview Error: {e}")
        return {"error": str(e)}


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    return FileResponse(os.path.join(settings.GENERATED_DIR, filename))


# ──────────────────────────────────────────────────────────────────────────────
# /feedback — RL Reward Signal
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/feedback")
async def submit_feedback(
    interaction_id: str = Form(...),
    score: float = Form(...),  # Expecting 1 for positive, -1 for negative
    text: Optional[str] = Form(None),
):
    """
    Submits user feedback for an interaction.
    This serves as the 'Reward' signal for the Reinforcement Learning loop.
    """
    try:
        success = await interaction_repo.submit_feedback(interaction_id, score, text)
        if success:
            logger.info(f"RL: Feedback received for {interaction_id}: {score}")
            return {"status": "success"}
        return {"status": "error", "message": "Failed to store feedback"}
    except Exception as e:
        logger.error(f"Feedback Error: {e}")
        return {"status": "error", "message": str(e)}