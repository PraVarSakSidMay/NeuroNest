import os
import uuid
import json
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

@app.on_event("startup")
async def startup_event():
    await interaction_repo.create_user()
    logger.info("NeuroNest Backend Started")

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
        user_id = "00000000-0000-0000-0000-000000000000"
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

        # STEP 4 — Generate Response
        ai_response = generate_response(transcript, emotion_dict)

        # STEP 5 — TTS (with selected voice)
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

        # STEP 6 — Log Interaction (Consolidated)
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
        await repo.log_interaction(interaction_data)

        # STEP 7 — Dashboard
        dashboard = update_dashboard(transcript, emotion_dict)

        return {
            "transcript": transcript,
            "audio_features": features_dict,
            "emotion": emotion_dict,
            "response": ai_response,
            "audio_url": tts_audio_url,
            "dashboard": dashboard
        }

    except Exception as e:
        logger.critical(f"Pipeline Crash: {e}")
        return {"error": "Internal Server Error", "detail": str(e)}

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
        return {"error": str(e)}

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    return FileResponse(os.path.join(settings.GENERATED_DIR, filename))