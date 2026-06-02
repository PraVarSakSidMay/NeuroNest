"""MongoDB infrastructure adapters implementing repository interfaces."""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

import numpy as np
from pymongo import DESCENDING

from core.config import settings
from core.logger import logger
from domain.entities import Interaction, Session, User
from domain.value_objects import Emotion, AudioFeatures
from infrastructure.mongodb_client import get_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    va = np.array(a, dtype=float)
    vb = np.array(b, dtype=float)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# Interaction Repository
# ---------------------------------------------------------------------------

class MongoInteractionRepository:
    """MongoDB adapter for interaction persistence."""

    @property
    def _col(self):
        return get_db()["interactions"]

    async def create(self, interaction: Interaction) -> Optional[str]:
        doc = {
            "_id": interaction.id or str(uuid4()),
            "session_id": interaction.session_id,
            "user_id": interaction.user_id,
            "transcript": interaction.transcript,
            "raw_audio_url": interaction.raw_audio_url,
            # Audio features
            "pitch_mean": interaction.features.pitch_mean if interaction.features else None,
            "jitter": interaction.features.jitter if interaction.features else None,
            "loudness": interaction.features.loudness if interaction.features else None,
            # Emotion
            "emotion": interaction.emotion_data.emotion if interaction.emotion_data else None,
            "stress_level": interaction.emotion_data.stress_level if interaction.emotion_data else None,
            "tone": interaction.emotion_data.tone if interaction.emotion_data else None,
            "contradiction_detected": (
                interaction.emotion_data.contradiction_detected if interaction.emotion_data else False
            ),
            "hidden_emotion": interaction.emotion_data.hidden_emotion if interaction.emotion_data else None,
            # Gaze telemetry (from video pipeline)
            "eye_contact_ratio": (
                interaction.emotion_data.eye_contact_ratio if interaction.emotion_data else None
            ),
            "head_pose": interaction.emotion_data.head_pose if interaction.emotion_data else None,
            # Response
            "response_text": interaction.response_text,
            "tts_audio_url": interaction.tts_audio_url,
            "feedback_score": interaction.feedback_score,
            "feedback_text": interaction.feedback_text,
            "applied_persona": interaction.applied_persona,
            "embedding": None,
            "created_at": _now_iso(),
        }
        try:
            await self._col.insert_one(doc)
            return doc["_id"]
        except Exception as e:
            logger.error(f"Failed to create interaction: {e}")
            return None

    async def get_by_id(self, interaction_id: str) -> Optional[Interaction]:
        try:
            doc = await self._col.find_one({"_id": interaction_id})
            if doc:
                return self._to_entity(doc)
        except Exception as e:
            logger.error(f"Failed to get interaction {interaction_id}: {e}")
        return None

    async def get_by_session(
        self, session_id: str, limit: int = 50, offset: int = 0
    ) -> List[Interaction]:
        try:
            cursor = (
                self._col.find({"session_id": session_id})
                .sort("created_at", DESCENDING)
                .skip(offset)
                .limit(limit)
            )
            return [self._to_entity(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"Failed to get interactions for session {session_id}: {e}")
            return []

    async def update_emotion(self, interaction_id: str, emotion: Emotion) -> bool:
        try:
            await self._col.update_one(
                {"_id": interaction_id},
                {"$set": {
                    "emotion": emotion.emotion,
                    "stress_level": emotion.stress_level,
                    "tone": emotion.tone,
                }},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update emotion for {interaction_id}: {e}")
            return False

    async def update_embedding(self, interaction_id: str, embedding: List[float]) -> bool:
        try:
            await self._col.update_one(
                {"_id": interaction_id},
                {"$set": {"embedding": embedding}},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store embedding for {interaction_id}: {e}")
            return False

    async def submit_feedback(
        self, interaction_id: str, score: float, text: Optional[str] = None
    ) -> bool:
        """Submit feedback for an interaction (Reward Signal for RL)."""
        try:
            await self._col.update_one(
                {"_id": interaction_id},
                {"$set": {
                    "feedback_score": score,
                    "feedback_text": text,
                    "updated_at": _now_iso()
                }},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to submit feedback for {interaction_id}: {e}")
            return False

    async def get_persona_performance(self) -> dict:
        """Get performance statistics for different personas (for RL selection)."""
        try:
            pipeline = [
                {"$match": {"applied_persona": {"$ne": None}, "feedback_score": {"$ne": None}}},
                {"$group": {
                    "_id": "$applied_persona",
                    "avg_score": {"$avg": "$feedback_score"},
                    "count": {"$sum": 1}
                }}
            ]
            cursor = self._col.aggregate(pipeline)
            return {doc["_id"]: {"avg_score": doc["avg_score"], "count": doc["count"]} async for doc in cursor}
        except Exception as e:
            logger.error(f"Failed to get persona performance: {e}")
            return {}

    async def get_successful_interactions(self, limit: int = 5) -> List[Interaction]:
        """Fetch interactions with high feedback scores for few-shot learning."""
        try:
            cursor = (
                self._col.find({"feedback_score": {"$gte": 0.5}})
                .sort("feedback_score", DESCENDING)
                .limit(limit)
            )
            return [self._to_entity(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"Failed to get successful interactions: {e}")
            return []

    async def upload_file(self, bucket: str, path: str, file_data: bytes) -> Optional[str]:
        """
        Save file locally (replacing Supabase Storage).
        Files are served via the existing GET /audio/{filename} route.
        """
        try:
            dest_dir = settings.GENERATED_DIR or "generated"
            os.makedirs(dest_dir, exist_ok=True)
            filename = os.path.basename(path)
            dest_path = os.path.join(dest_dir, filename)
            with open(dest_path, "wb") as f:
                f.write(file_data)
            url = f"http://localhost:8000/audio/{filename}"
            logger.info(f"File saved locally: {dest_path} → {url}")
            return url
        except Exception as e:
            logger.error(f"Error saving file locally ({bucket}/{path}): {e}")
            return None

    def _to_entity(self, doc: dict) -> Interaction:
        features = (
            AudioFeatures(
                pitch_mean=doc.get("pitch_mean", 0.0),
                jitter=doc.get("jitter", 0.0),
                loudness=doc.get("loudness", 0.0),
            )
            if doc.get("pitch_mean") is not None
            else None
        )
        emotion = (
            Emotion(
                emotion=doc.get("emotion", "neutral"),
                stress_level=doc.get("stress_level", 50),
                tone=doc.get("tone", "calm"),
                contradiction_detected=doc.get("contradiction_detected", False),
                hidden_emotion=doc.get("hidden_emotion", "") or "",
                eye_contact_ratio=doc.get("eye_contact_ratio"),
                head_pose=doc.get("head_pose"),
            )
            if doc.get("emotion")
            else None
        )
        return Interaction(
            id=doc.get("_id", ""),
            session_id=doc.get("session_id", ""),
            user_id=doc.get("user_id", ""),
            transcript=doc.get("transcript", ""),
            raw_audio_url=doc.get("raw_audio_url"),
            features=features,
            emotion_data=emotion,
            response_text=doc.get("response_text"),
            tts_audio_url=doc.get("tts_audio_url"),
            feedback_score=doc.get("feedback_score"),
            feedback_text=doc.get("feedback_text"),
            applied_persona=doc.get("applied_persona"),
            created_at=doc.get("created_at", ""),
        )


# ---------------------------------------------------------------------------
# Session Repository
# ---------------------------------------------------------------------------

class MongoSessionRepository:
    """MongoDB adapter for session management."""

    @property
    def _col(self):
        return get_db()["sessions"]

    async def create(self, user_id: str) -> Optional[Session]:
        doc = {
            "_id": str(uuid4()),
            "user_id": user_id,
            "started_at": _now_iso(),
            "ended_at": None,
        }
        try:
            await self._col.insert_one(doc)
            return Session(id=doc["_id"], user_id=user_id, started_at=doc["started_at"])
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None

    async def get_by_id(self, session_id: str) -> Optional[Session]:
        try:
            doc = await self._col.find_one({"_id": session_id})
            if doc:
                return Session(
                    id=doc["_id"],
                    user_id=doc["user_id"],
                    started_at=doc.get("started_at"),
                )
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
        return None

    async def get_last_by_user(self, user_id: str) -> Optional[Session]:
        try:
            doc = await self._col.find_one(
                {"user_id": user_id},
                sort=[("started_at", DESCENDING)],
            )
            if doc:
                return Session(
                    id=doc["_id"],
                    user_id=user_id,
                    started_at=doc.get("started_at"),
                )
        except Exception as e:
            logger.error(f"Failed to get last session for user {user_id}: {e}")
        return None

    async def end(self, session_id: str) -> bool:
        try:
            await self._col.update_one(
                {"_id": session_id},
                {"$set": {"ended_at": _now_iso()}},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            return False


# ---------------------------------------------------------------------------
# User Repository
# ---------------------------------------------------------------------------

class MongoUserRepository:
    """MongoDB adapter for user management."""

    DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"

    @property
    def _col(self):
        return get_db()["users"]

    async def create(self, full_name: Optional[str] = None) -> str:
        doc = {
            "_id": self.DEFAULT_USER_ID,
            "full_name": full_name or "Test User",
            "created_at": _now_iso(),
        }
        try:
            # upsert so re-running startup doesn't fail on duplicate key
            await self._col.replace_one({"_id": self.DEFAULT_USER_ID}, doc, upsert=True)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
        return self.DEFAULT_USER_ID

    async def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            doc = await self._col.find_one({"_id": user_id})
            if doc:
                return User(id=doc["_id"], full_name=doc.get("full_name"))
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
        return None

    async def get_default_user(self) -> str:
        return self.DEFAULT_USER_ID


# ---------------------------------------------------------------------------
# Embedding Repository (cosine similarity in Python)
# ---------------------------------------------------------------------------

class MongoEmbeddingRepository:
    """MongoDB adapter for embedding operations using in-process cosine similarity."""

    @property
    def _col(self):
        return get_db()["interactions"]

    async def find_similar(
        self,
        user_id: str,
        query_embedding: List[float],
        k: int = 5,
        exclude_session: Optional[str] = None,
    ) -> List[dict]:
        """
        Find the top-k most similar past interactions for this user using
        cosine similarity computed in Python (numpy).
        Only interactions that have a stored embedding are considered.
        """
        if not query_embedding:
            return []

        try:
            query: dict = {"user_id": user_id, "embedding": {"$ne": None}}
            if exclude_session:
                query["session_id"] = {"$ne": exclude_session}

            cursor = self._col.find(query, {"embedding": 1, "transcript": 1, "emotion": 1,
                                            "stress_level": 1, "tone": 1, "hidden_emotion": 1,
                                            "response_text": 1, "created_at": 1,
                                            "eye_contact_ratio": 1, "head_pose": 1})
            scored = []
            async for doc in cursor:
                emb = doc.get("embedding")
                if not emb:
                    continue
                sim = _cosine_similarity(query_embedding, emb)
                if sim >= 0.3:
                    scored.append((sim, doc))

            # Sort descending by similarity, take top-k
            scored.sort(key=lambda x: x[0], reverse=True)
            results = []
            for sim, doc in scored[:k]:
                results.append({
                    "transcript": doc.get("transcript", ""),
                    "emotion": doc.get("emotion", "unknown"),
                    "stress_level": doc.get("stress_level", 0),
                    "tone": doc.get("tone", ""),
                    "hidden_emotion": doc.get("hidden_emotion", ""),
                    "eye_contact_ratio": doc.get("eye_contact_ratio"),
                    "head_pose": doc.get("head_pose"),
                    "response_text": doc.get("response_text", ""),
                    "created_at": doc.get("created_at", ""),
                    "similarity": sim,
                })
            logger.info(f"RAG: Retrieved {len(results)} relevant memories for user {user_id}.")
            return results
        except Exception as e:
            logger.error(f"RAG: Memory retrieval failed — {e}")
            return []

    async def store(self, interaction_id: str, embedding: List[float]) -> bool:
        try:
            await self._col.update_one(
                {"_id": interaction_id},
                {"$set": {"embedding": embedding}},
            )
            return True
        except Exception as e:
            logger.error(f"RAG: Failed to store embedding for {interaction_id} — {e}")
            return False
