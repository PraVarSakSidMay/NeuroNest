import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_audio(bucket: str, path: str, file_data: bytes):
    try:
        supabase.storage.from_(bucket).upload(
            path,
            file_data,
            {"content-type": "audio/mpeg"}
        )
        return supabase.storage.from_(bucket).get_public_url(path)
    except Exception as e:
        print(f"Error uploading to Supabase {bucket}: {e}")
        return None

def create_dummy_user():
    user_id = "00000000-0000-0000-0000-000000000000"
    try:
        supabase.table("users").upsert({
            "id": user_id,
            "full_name": "Test User",
            "role": "patient"
        }).execute()
    except Exception as e:
        print(f"Error creating dummy user: {e}")
    return user_id

def create_voice_session(user_id: str):
    try:
        response = supabase.table("voice_sessions").insert({"user_id": user_id}).execute()
        return response.data[0]["id"] if response.data else None
    except Exception as e:
        print(f"Fallback: Supabase failed to create voice session. {e}")
        return None

def log_voice(session_id: str, user_id: str, audio_url: str, transcript: str):
    try:
        response = supabase.table("voice_logs").insert({
            "session_id": session_id,
            "user_id": user_id,
            "audio_url": audio_url,
            "transcript": transcript
        }).execute()
        return response.data[0]["id"] if response.data else None
    except Exception as e:
        print(f"Fallback: Supabase failed to log voice. {e}")
        return None

def store_audio_features(voice_log_id: str, features: dict):
    try:
        supabase.table("audio_features").insert({
            "voice_log_id": voice_log_id,
            "pitch_mean": features.get("pitch_mean"),
            "jitter": features.get("jitter"),
            "loudness": features.get("loudness")
        }).execute()
    except Exception as e:
        print(f"Fallback: Supabase failed to store audio features. {e}")

def store_emotional_analysis(voice_log_id: str, emotion_data: dict):
    try:
        supabase.table("emotional_analysis").insert({
            "voice_log_id": voice_log_id,
            "emotion": emotion_data.get("emotion"),
            "stress_level": emotion_data.get("stress_level"),
            "emotional_tone": emotion_data.get("tone")
        }).execute()
    except Exception as e:
        print(f"Fallback: Supabase failed to store emotional analysis. {e}")

def store_ai_response(voice_log_id: str, response_text: str, tts_audio_url: str):
    try:
        supabase.table("ai_responses").insert({
            "voice_log_id": voice_log_id,
            "response_text": response_text,
            "tts_audio_url": tts_audio_url
        }).execute()
    except Exception as e:
        print(f"Fallback: Supabase failed to store AI response. {e}")

