from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from typing import Optional

import shutil
import uuid
import os
import json

from services.whisper_service import transcribe_audio
from services.opensmile_service import extract_audio_features
from services.emotion_service import analyze_emotion
from services.response_service import generate_response
from services.tts_service import generate_tts
from services.dashboard_service import update_dashboard

import services.db_service as db_service

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#done
UPLOAD_DIR = "uploads"
GENERATED_DIR = "generated"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    db_service.create_dummy_user()

@app.post("/process-voice")
async def process_voice(
    file: UploadFile = File(...),
    audio_analysis: Optional[str] = Form(None)  # Real audio features from browser Web Audio API
):

    file_id = str(uuid.uuid4())
    input_path = f"{UPLOAD_DIR}/{file_id}.webm"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 0. Upload to Supabase Storage
    with open(input_path, "rb") as audio_file:
        raw_audio_url = db_service.upload_audio("voice-recordings", f"{file_id}.webm", audio_file.read())

    # Create session
    user_id = "00000000-0000-0000-0000-000000000000"
    session_id = db_service.create_voice_session(user_id)

    # STEP 1 — Transcribe (Groq Whisper → OpenAI fallback)
    transcript = transcribe_audio(input_path)

    # Log voice
    voice_log_id = db_service.log_voice(session_id, user_id, raw_audio_url, transcript)

    # STEP 2 — Audio Features
    # Priority: Real frontend Web Audio API features → openSMILE → mock
    frontend_features = None
    if audio_analysis:
        try:
            frontend_features = json.loads(audio_analysis)
            print(f"Using real browser audio features: {frontend_features.get('voice_description', 'N/A')}")
        except Exception:
            pass

    audio_features = extract_audio_features(input_path, frontend_features)

    if voice_log_id:
        db_service.store_audio_features(voice_log_id, audio_features)

    # STEP 3 — Emotion Analysis (Groq Llama → Gemini fallback)
    emotion_data = analyze_emotion(transcript, audio_features)
    if voice_log_id:
        db_service.store_emotional_analysis(voice_log_id, emotion_data)

    # STEP 4 — Generate Response (Groq Llama → Gemini fallback)
    ai_response = generate_response(transcript, emotion_data)

    # STEP 5 — TTS (ElevenLabs → Deepgram → Cartesia → LMNT → Murf → browser)
    audio_output_path = generate_tts(ai_response, emotion_data.get("emotion", "neutral"))

    tts_audio_url = None
    if audio_output_path:
        with open(audio_output_path, "rb") as tts_file:
            tts_audio_url = db_service.upload_audio("ai-responses", f"{file_id}_response.mp3", tts_file.read())

        if voice_log_id:
            db_service.store_ai_response(voice_log_id, ai_response, tts_audio_url)

        # Use local URL if Supabase upload failed
        if not tts_audio_url:
            tts_audio_url = f"http://localhost:8000/audio/{os.path.basename(audio_output_path)}"

    # STEP 6 — Dashboard
    dashboard = update_dashboard(transcript, emotion_data)

    return {
        "transcript": transcript,
        "audio_features": audio_features,
        "emotion": emotion_data,
        "response": ai_response,
        "audio_url": tts_audio_url,  # None = frontend uses Web Speech API
        "dashboard": dashboard
    }

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    return FileResponse(f"generated/{filename}")