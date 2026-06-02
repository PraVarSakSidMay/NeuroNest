"""MongoDB adapter — thin wrapper matching the SupabaseAdapter public API."""
from __future__ import annotations

from typing import Optional, List

from core.logger import logger
from models.interaction import InteractionCreate
from domain.entities import Interaction
from domain.value_objects import AudioFeatures, Emotion

from infrastructure.repositories import (
    IInteractionRepository,
    ISessionRepository,
    IUserRepository,
    IEmbeddingRepository,
)
from infrastructure.mongodb_repositories import (
    MongoInteractionRepository,
    MongoSessionRepository,
    MongoUserRepository,
    MongoEmbeddingRepository,
)


class MongoDBAdapter:
    """Thin adapter that delegates to the clean MongoDB repository instances.

    Keeps the same public surface as the former SupabaseAdapter so that
    legacy call-sites in main.py / rag_service.py need minimal edits.
    """

    def __init__(self):
        self._interaction_repo = MongoInteractionRepository()
        self._session_repo = MongoSessionRepository()
        self._user_repo = MongoUserRepository()
        self._embedding_repo = MongoEmbeddingRepository()

    # ── Legacy-compatible methods ──────────────────────────────────────────

    async def create_user(self, full_name: str = "Test User") -> str:
        return await self._user_repo.create(full_name)

    async def create_session(self, user_id: str) -> Optional[str]:
        session = await self._session_repo.create(user_id)
        return session.id if session else None

    async def log_interaction(self, interaction: InteractionCreate) -> Optional[str]:
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
        return await self._interaction_repo.create(domain_interaction)

    async def store_embedding(self, interaction_id: str, embedding: List[float]) -> bool:
        return await self._embedding_repo.store(interaction_id, embedding)

    async def upload_file(self, bucket: str, path: str, file_data: bytes) -> Optional[str]:
        return await self._interaction_repo.upload_file(bucket, path, file_data)

    # ── New repository property accessors ─────────────────────────────────

    @property
    def interaction(self) -> IInteractionRepository:
        return self._interaction_repo

    @property
    def session(self) -> ISessionRepository:
        return self._session_repo

    @property
    def user(self) -> IUserRepository:
        return self._user_repo

    @property
    def embedding(self) -> IEmbeddingRepository:
        return self._embedding_repo
