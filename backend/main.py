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
from models.interaction import InteractionCreate, AudioFeatures, EmotionData
from repositories.interaction_repo import interaction_repo, InteractionRepository

from services.whisper_service import transcribe_audio
from services.opensmile_service import extract_audio_features
from services.emotion_service import analyze_emotion
from services.response_service import generate_response
from services.tts_service import generate_tts
from services.dashboard_service import update_dashboard
from services.rag_service import rag_service

app = FastAPI(title="NeuroNest Voice Assistant")

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
    await interaction_repo.create_user()
    logger.info("NeuroNest Backend Started")


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
        supabase = repo.get_supabase_client()
        greeting = rag_service.get_session_opener(
            supabase_client=supabase,
            user_id=DEFAULT_USER_ID,
            current_session_id=None,  # No active session yet
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
    voice_name: Optional[str] = Form("Rachel"),
    repo: InteractionRepository = Depends(lambda: interaction_repo)
):
    try:
        file_id = str(uuid.uuid4())
        input_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.webm")

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 0. Upload to Supabase Storage
        raw_audio_url = None
        try:
            with open(input_path, "rb") as f:
                raw_audio_url = await repo.upload_file(settings.VOICE_BUCKET, f"{file_id}.webm", f.read())
        except Exception as e:
            logger.error(f"Failed to upload raw audio: {e}")

        # Create session
        user_id = DEFAULT_USER_ID
        session_id = await repo.create_session(user_id)

        # STEP 1 — Transcribe
        transcript = transcribe_audio(input_path)

        # STEP 2 — Audio Features
        frontend_features = None
        if audio_analysis:
            try:
                frontend_features = json.loads(audio_analysis)
            except Exception:
                pass
        
        features_dict = extract_audio_features(input_path, frontend_features)
        features_model = AudioFeatures(**features_dict)

        # STEP 3 — Emotion Analysis
        emotion_dict = analyze_emotion(transcript, features_dict)
        emotion_model = EmotionData(**emotion_dict)

        # STEP 4 — RAG: Retrieve relevant memories in parallel with prompt prep
        supabase = repo.get_supabase_client()
        memories = rag_service.retrieve_memories(
            supabase_client=supabase,
            user_id=user_id,
            query_text=transcript,
            current_session_id=session_id,
            k=settings.RAG_TOP_K,
        )

        # STEP 5 — Generate Response (with memory context)
        ai_response = generate_response(transcript, emotion_dict, memories)

        # STEP 6 — TTS (with selected voice)
        audio_output_path = generate_tts(ai_response, emotion_model.emotion, voice_name)

        tts_audio_url = None
        if audio_output_path:
            try:
                with open(audio_output_path, "rb") as f:
                    tts_audio_url = await repo.upload_file(settings.TTS_BUCKET, f"{file_id}_response.mp3", f.read())
            except Exception as e:
                logger.error(f"Failed to upload TTS audio: {e}")

            if not tts_audio_url:
                tts_audio_url = f"http://localhost:8000/audio/{os.path.basename(audio_output_path)}"

        # STEP 7 — Log Interaction (Consolidated)
        interaction_data = InteractionCreate(
            session_id=session_id,
            user_id=user_id,
            transcript=transcript,
            raw_audio_url=raw_audio_url,
            features=features_model,
            emotion_data=emotion_model,
            response_text=ai_response,
            tts_audio_url=tts_audio_url
        )
        interaction_id = await repo.log_interaction(interaction_data)

        # STEP 8 — Dashboard
        dashboard = update_dashboard(transcript, emotion_dict)

        # STEP 9 — Generate & store embedding ASYNCHRONOUSLY (fire-and-forget)
        # This happens after the response is returned so it never adds latency.
        if interaction_id:
            asyncio.create_task(_store_embedding_async(repo, interaction_id, transcript))

        return {
            "transcript": transcript,
            "audio_features": features_dict,
            "emotion": emotion_dict,
            "response": ai_response,
            "audio_url": tts_audio_url,
            "dashboard": dashboard,
            "memories_used": len(memories),
        }

    except Exception as e:
        logger.critical(f"Pipeline Crash: {e}")
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
        audio_path = generate_tts(preview_text, "neutral", voice_name)
        if audio_path:
            return {"audio_url": f"http://localhost:8000/audio/{os.path.basename(audio_path)}"}
        return {"error": "Failed to generate preview"}
    except Exception as e:
        logger.error(f"Preview Error: {e}")
        return {{"error": str(e)}}


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    return FileResponse(os.path.join(settings.GENERATED_DIR, filename))