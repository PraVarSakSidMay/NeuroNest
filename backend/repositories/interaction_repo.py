"""Legacy interaction repository — now backed by MongoDB via Motor.

Keeps the same public API so main.py call-sites need no changes.
"""
from __future__ import annotations

import os
from typing import Optional, List

from core.config import settings
from core.logger import logger
from models.interaction import InteractionCreate
from infrastructure.mongodb_client import get_db
from infrastructure.mongodb_repositories import MongoInteractionRepository, _now_iso
from uuid import uuid4


class InteractionRepository:
    """Legacy-compatible repository now backed by MongoDB."""

    def __init__(self):
        self._repo = MongoInteractionRepository()

    @property
    def _users(self):
        return get_db()["users"]

    @property
    def _sessions(self):
        return get_db()["sessions"]

    async def create_user(self, full_name: str = "Test User", role: str = "patient") -> str:
        user_id = "00000000-0000-0000-0000-000000000000"
        try:
            await self._users.replace_one(
                {"_id": user_id},
                {"_id": user_id, "full_name": full_name, "role": role, "created_at": _now_iso()},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Error creating dummy user: {e}")
        return user_id

    async def create_session(self, user_id: str) -> Optional[str]:
        try:
            doc = {
                "_id": str(uuid4()),
                "user_id": user_id,
                "started_at": _now_iso(),
                "ended_at": None,
            }
            await self._sessions.insert_one(doc)
            return doc["_id"]
        except Exception as e:
            logger.error(f"Failed to create voice session: {e}")
            return None

    async def log_interaction(self, interaction: InteractionCreate) -> Optional[str]:
        """Logs a consolidated interaction using the InteractionCreate model."""
        try:
            from domain.entities import Interaction
            from domain.value_objects import AudioFeatures, Emotion

            features = None
            if interaction.features:
                features = AudioFeatures(
                    pitch_mean=interaction.features.pitch_mean,
                    jitter=interaction.features.jitter,
                    loudness=interaction.features.loudness,
                )
            emotion = None
            if interaction.emotion_data:
                emotion = Emotion(
                    emotion=interaction.emotion_data.emotion,
                    stress_level=interaction.emotion_data.stress_level,
                    tone=interaction.emotion_data.tone,
                    contradiction_detected=interaction.emotion_data.contradiction_detected,
                    hidden_emotion=interaction.emotion_data.hidden_emotion,
                )
            domain_interaction = Interaction.create(
                session_id=interaction.session_id,
                user_id=interaction.user_id,
                transcript=interaction.transcript,
                features=features,
                emotion_data=emotion,
            )
            if interaction.response_text:
                domain_interaction = domain_interaction.with_response(
                    interaction.response_text, interaction.tts_audio_url
                )
            return await self._repo.create(domain_interaction)
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return None

    async def upload_file(self, bucket: str, path: str, file_data: bytes) -> Optional[str]:
        return await self._repo.upload_file(bucket, path, file_data)

    async def store_embedding(self, interaction_id: str, embedding: list) -> bool:
        """Updates the interaction with its embedding vector."""
        result = await self._repo.update_embedding(interaction_id, embedding)
        if result:
            logger.info(f"RAG: Stored embedding for interaction {interaction_id}")
        return result

    def get_db(self):
        """Expose the MongoDB database handle (replaces get_supabase_client)."""
        return get_db()

    # Keep legacy name as alias for backward compatibility
    def get_supabase_client(self):
        """Deprecated alias — returns the MongoDB database handle instead."""
        logger.warning("get_supabase_client() is deprecated; use get_db() — returning MongoDB db.")
        return get_db()


interaction_repo = InteractionRepository()

