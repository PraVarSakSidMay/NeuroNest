from supabase import create_client, Client
from core.config import settings
from core.logger import logger
from models.interaction import InteractionCreate
from typing import Optional, List
import json

class InteractionRepository:
    def __init__(self):
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    async def create_user(self, full_name: str = "Test User", role: str = "patient"):
        user_id = "00000000-0000-0000-0000-000000000000"
        try:
            self.supabase.table("users").upsert({
                "id": user_id,
                "full_name": full_name,
                "role": role
            }).execute()
        except Exception as e:
            logger.error(f"Error creating dummy user: {e}")
        return user_id

    async def create_session(self, user_id: str):
        try:
            response = self.supabase.table("voice_sessions").insert({"user_id": user_id}).execute()
            return response.data[0]["id"] if response.data else None
        except Exception as e:
            logger.error(f"Failed to create voice session: {e}")
            return None

    async def log_interaction(self, interaction: InteractionCreate):
        """
        Logs a consolidated interaction using the InteractionCreate model.
        """
        try:
            data = {
                "session_id": interaction.session_id,
                "user_id": interaction.user_id,
                "transcript": interaction.transcript,
                "raw_audio_url": interaction.raw_audio_url,
                
                # Audio Features
                "pitch_mean": interaction.features.pitch_mean if interaction.features else None,
                "jitter": interaction.features.jitter if interaction.features else None,
                "loudness": interaction.features.loudness if interaction.features else None,
                
                # Emotional Analysis
                "emotion": interaction.emotion_data.emotion if interaction.emotion_data else None,
                "stress_level": interaction.emotion_data.stress_level if interaction.emotion_data else None,
                "tone": interaction.emotion_data.tone if interaction.emotion_data else None,
                "contradiction_detected": interaction.emotion_data.contradiction_detected if interaction.emotion_data else False,
                "hidden_emotion": interaction.emotion_data.hidden_emotion if interaction.emotion_data else None,
                
                # AI Response
                "response_text": interaction.response_text,
                "tts_audio_url": interaction.tts_audio_url
            }
            
            response = self.supabase.table("interactions").insert(data).execute()
            return response.data[0]["id"] if response.data else None
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return None

    async def upload_file(self, bucket: str, path: str, file_data: bytes):
        try:
            self.supabase.storage.from_(bucket).upload(
                path,
                file_data,
                {"content-type": "audio/mpeg"}
            )
            return self.supabase.storage.from_(bucket).get_public_url(path)
        except Exception as e:
            logger.error(f"Error uploading to Supabase {bucket}: {e}")
            return None

    # ── RAG methods ────────────────────────────────────────────────────────

    async def store_embedding(self, interaction_id: str, embedding: list) -> bool:
        """
        Updates the interactions row with its pgvector embedding.
        Called asynchronously after the response is returned to the user.
        """
        try:
            self.supabase.table("interactions").update(
                {"embedding": embedding}
            ).eq("id", interaction_id).execute()
            logger.info(f"RAG: Stored embedding for interaction {interaction_id}")
            return True
        except Exception as e:
            logger.error(f"RAG: Failed to store embedding for {interaction_id} — {e}")
            return False

    def get_supabase_client(self):
        """Expose the raw Supabase client so services can call RPC functions."""
        return self.supabase

interaction_repo = InteractionRepository()
