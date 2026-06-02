"""Supabase infrastructure adapters implementing repository interfaces."""
from typing import Optional, List
from supabase import create_client, Client
from core.config import settings
from core.logger import logger
from domain.entities import Interaction, Session, User
from domain.value_objects import Emotion, AudioFeatures


class SupabaseInteractionRepository:
    """Supabase adapter for interaction persistence."""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    async def create(self, interaction: Interaction) -> Optional[str]:
        data = {
            "session_id": interaction.session_id,
            "user_id": interaction.user_id,
            "transcript": interaction.transcript,
            "raw_audio_url": interaction.raw_audio_url,
            "pitch_mean": interaction.features.pitch_mean if interaction.features else None,
            "jitter": interaction.features.jitter if interaction.features else None,
            "loudness": interaction.features.loudness if interaction.features else None,
            "emotion": interaction.emotion_data.emotion if interaction.emotion_data else None,
            "stress_level": interaction.emotion_data.stress_level if interaction.emotion_data else None,
            "tone": interaction.emotion_data.tone if interaction.emotion_data else None,
            "contradiction_detected": interaction.emotion_data.contradiction_detected if interaction.emotion_data else False,
            "hidden_emotion": interaction.emotion_data.hidden_emotion if interaction.emotion_data else None,
            "response_text": interaction.response_text,
            "tts_audio_url": interaction.tts_audio_url,
        }
        try:
            response = self.client.table("interactions").insert(data).execute()
            return response.data[0]["id"] if response.data else None
        except Exception as e:
            logger.error(f"Failed to create interaction: {e}")
            return None
    
    async def get_by_id(self, interaction_id: str) -> Optional[Interaction]:
        try:
            response = self.client.table("interactions").select("*").eq("id", interaction_id).execute()
            if response.data:
                return self._to_entity(response.data[0])
        except Exception as e:
            logger.error(f"Failed to get interaction {interaction_id}: {e}")
        return None
    
    async def get_by_session(
        self, session_id: str, limit: int = 50, offset: int = 0
    ) -> List[Interaction]:
        try:
            response = (
                self.client.table("interactions")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return [self._to_entity(row) for row in (response.data or [])]
        except Exception as e:
            logger.error(f"Failed to get interactions for session {session_id}: {e}")
            return []
    
    async def update_emotion(self, interaction_id: str, emotion: Emotion) -> bool:
        try:
            self.client.table("interactions").update({
                "emotion": emotion.emotion,
                "stress_level": emotion.stress_level,
                "tone": emotion.tone,
            }).eq("id", interaction_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to update emotion for {interaction_id}: {e}")
            return False
    
    async def update_embedding(self, interaction_id: str, embedding: List[float]) -> bool:
        try:
            self.client.table("interactions").update({
                "embedding": embedding
            }).eq("id", interaction_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to store embedding for {interaction_id}: {e}")
            return False
    
    async def upload_file(self, bucket: str, path: str, file_data: bytes) -> Optional[str]:
        try:
            self.client.storage.from_(bucket).upload(
                path, file_data, {"content-type": "audio/mpeg"}
            )
            return self.client.storage.from_(bucket).get_public_url(path)
        except Exception as e:
            logger.error(f"Error uploading to Supabase {bucket}: {e}")
            return None
    
    def _to_entity(self, row: dict) -> Interaction:
        features = AudioFeatures(
            pitch_mean=row.get("pitch_mean", 0.0),
            jitter=row.get("jitter", 0.0),
            loudness=row.get("loudness", 0.0),
        ) if row.get("pitch_mean") is not None else None
        
        emotion = Emotion(
            emotion=row.get("emotion", "neutral"),
            stress_level=row.get("stress_level", 50),
            tone=row.get("tone", "calm"),
        ) if row.get("emotion") else None
        
        return Interaction(
            id=row.get("id", ""),
            session_id=row.get("session_id", ""),
            user_id=row.get("user_id", ""),
            transcript=row.get("transcript", ""),
            raw_audio_url=row.get("raw_audio_url"),
            features=features,
            emotion_data=emotion,
            response_text=row.get("response_text"),
            tts_audio_url=row.get("tts_audio_url"),
            created_at=row.get("created_at", ""),
        )


class SupabaseSessionRepository:
    """Supabase adapter for session management."""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    async def create(self, user_id: str) -> Optional[Session]:
        try:
            response = self.client.table("voice_sessions").insert({"user_id": user_id}).execute()
            if response.data:
                return Session(id=response.data[0]["id"], user_id=user_id)
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
        return None
    
    async def get_by_id(self, session_id: str) -> Optional[Session]:
        try:
            response = self.client.table("voice_sessions").select("*").eq("id", session_id).execute()
            if response.data:
                return Session(
                    id=response.data[0]["id"],
                    user_id=response.data[0]["user_id"],
                    started_at=response.data[0].get("started_at"),
                )
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
        return None
    
    async def get_last_by_user(self, user_id: str) -> Optional[Session]:
        try:
            response = (
                self.client.table("voice_sessions")
                .select("*")
                .eq("user_id", user_id)
                .order("started_at", desc=True)
                .limit(1)
                .execute()
            )
            if response.data:
                return Session(
                    id=response.data[0]["id"],
                    user_id=user_id,
                    started_at=response.data[0].get("started_at"),
                )
        except Exception as e:
            logger.error(f"Failed to get last session for user {user_id}: {e}")
        return None
    
    async def end(self, session_id: str) -> bool:
        try:
            self.client.table("voice_sessions").update({
                "ended_at": "now()"
            }).eq("id", session_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            return False


class SupabaseUserRepository:
    """Supabase adapter for user management."""
    
    DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    async def create(self, full_name: Optional[str] = None) -> str:
        try:
            self.client.table("users").upsert({
                "id": self.DEFAULT_USER_ID,
                "full_name": full_name or "Test User",
            }).execute()
        except Exception as e:
            logger.error(f"Error creating user: {e}")
        return self.DEFAULT_USER_ID
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            response = self.client.table("users").select("*").eq("id", user_id).execute()
            if response.data:
                return User(
                    id=response.data[0]["id"],
                    full_name=response.data[0].get("full_name"),
                )
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
        return None
    
    async def get_default_user(self) -> str:
        return self.DEFAULT_USER_ID


class SupabaseEmbeddingRepository:
    """Supabase adapter for embedding operations."""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    async def find_similar(
        self,
        user_id: str,
        query_embedding: List[float],
        k: int = 5,
        exclude_session: Optional[str] = None,
    ) -> List[dict]:
        try:
            result = self.client.rpc(
                "match_interactions",
                {
                    "query_embedding": query_embedding,
                    "match_user_id": user_id,
                    "match_count": k,
                    "exclude_session": exclude_session,
                },
            ).execute()
            
            memories = []
            for row in (result.data or []):
                if row.get("similarity", 0) < 0.3:
                    continue
                memories.append({
                    "transcript": row.get("transcript", ""),
                    "emotion": row.get("emotion", "unknown"),
                    "stress_level": row.get("stress_level", 0),
                    "tone": row.get("tone", ""),
                    "hidden_emotion": row.get("hidden_emotion", ""),
                    "response_text": row.get("response_text", ""),
                    "created_at": row.get("created_at", ""),
                    "similarity": row.get("similarity", 0),
                })
            return memories
        except Exception as e:
            logger.error(f"RAG: Memory retrieval failed — {e}")
            return []
    
    async def store(self, interaction_id: str, embedding: List[float]) -> bool:
        try:
            self.client.table("interactions").update({
                "embedding": embedding
            }).eq("id", interaction_id).execute()
            return True
        except Exception as e:
            logger.error(f"RAG: Failed to store embedding for {interaction_id} — {e}")
            return False