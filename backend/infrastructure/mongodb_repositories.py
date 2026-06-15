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
from domain.entities import Interaction, Session, User, UserState, Memory, Reflection, WorkingMemory
from domain.value_objects import (
    Emotion, 
    AudioFeatures, 
    Goal, 
    Project, 
    InteractionStyle, 
    EmotionEnum,
    MemoryType,
    MemoryImportance,
    MemoryLifecycle,
    ReflectionType,
    ReflectionScore,
    Task,
    EntityMention,
    Decision
)
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
    """
    Implementation of the interaction repository using MongoDB.
    Handles storage and retrieval of user-AI turns, including RL data.
    """

    @property
    def _col(self):
        return get_db()["interactions"]

    async def create(self, interaction: Interaction) -> Optional[str]:
        """Stores a new interaction turn in the database."""
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
            "feedback_text":  interaction.feedback_text,
            # RL fields
            "applied_persona": interaction.applied_persona,
            "applied_action":  interaction.applied_action,
            "applied_policy":  interaction.applied_policy,
            "emotion_before":  interaction.emotion_before,
            "embedding": None,
            "created_at": _now_iso(),
        }
        try:
            await self._col.insert_one(doc)
            return str(doc["_id"])
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
        """
        Aggregates performance data (average feedback scores) for each RL persona.
        This data is used by the RLService to make optimal personality choices.
        """
        try:
            # Aggregation pipeline to calculate average score and total count per persona
            pipeline = [
                {"$match": {"applied_persona": {"$ne": None}, "feedback_score": {"$ne": None}}},
                {"$group": {
                    "_id": "$applied_persona",
                    "avg_score": {"$avg": "$feedback_score"},
                    "count": {"$sum": 1}
                }}
            ]
            cursor = self._col.aggregate(pipeline)
            results = {}
            async for doc in cursor:
                results[doc["_id"]] = {"avg_score": doc["avg_score"], "count": doc["count"]}
            return results
        except Exception as e:
            logger.error(f"Failed to get persona performance: {e}")
            return {}

    async def get_successful_interactions(self, limit: int = 5) -> List[Interaction]:
        """
        Fetches the highest-rated interactions to be used as few-shot training examples.
        This allows the AI to learn from its own past successes.
        """
        try:
            cursor = (
                self._col.find({"feedback_score": {"$gte": 0.5}})
                .sort("feedback_score", DESCENDING)
                .limit(limit)
            )
            interactions = []
            async for doc in cursor:
                interactions.append(self._to_entity(doc))
            return interactions
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
            applied_action=doc.get("applied_action"),
            applied_policy=doc.get("applied_policy"),
            emotion_before=doc.get("emotion_before"),
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


# ---------------------------------------------------------------------------
# User State Repository
# ---------------------------------------------------------------------------

class MongoUserStateRepository:
    """MongoDB adapter for user state persistence."""

    @property
    def _col(self):
        return get_db()["user_states"]

    async def get_by_user_id(self, user_id: str) -> Optional[UserState]:
        """Fetch the persistent state for a user."""
        try:
            doc = await self._col.find_one({"_id": user_id})
            if doc:
                return self._to_entity(doc)
        except Exception as e:
            logger.error(f"Failed to get user state for {user_id}: {e}")
        return None

    async def update(self, user_id: str, state: UserState) -> bool:
        """Persist the user state using an upsert strategy."""
        try:
            doc = {
                "_id": user_id,
                "current_emotion": state.current_emotion,
                "dominant_emotion": state.dominant_emotion,
                "stress_level": state.stress_level,
                "confidence_level": state.confidence_level,
                "engagement_level": state.engagement_level,
                "current_goals": [g.__dict__ for g in state.current_goals],
                "preferred_interaction_style": state.preferred_interaction_style,
                "preferred_persona": state.preferred_persona,
                "active_projects": [p.__dict__ for p in state.active_projects],
                "recent_topics": state.recent_topics,
                "last_updated": state.last_updated.isoformat() if isinstance(state.last_updated, datetime) else state.last_updated,
            }
            await self._col.replace_one({"_id": user_id}, doc, upsert=True)
            return True
        except Exception as e:
            logger.error(f"Failed to update user state for {user_id}: {e}")
            return False

    def _to_entity(self, doc: dict) -> UserState:
        """Convert a MongoDB document back into a UserState domain entity."""
        return UserState(
            user_id=doc["_id"],
            current_emotion=EmotionEnum(doc.get("current_emotion", "neutral")),
            dominant_emotion=EmotionEnum(doc.get("dominant_emotion", "neutral")),
            stress_level=doc.get("stress_level", 50),
            confidence_level=doc.get("confidence_level", 50),
            engagement_level=doc.get("engagement_level", 50),
            current_goals=[Goal(**g) for g in doc.get("current_goals", [])],
            preferred_interaction_style=InteractionStyle(doc.get("preferred_interaction_style", "casual")),
            preferred_persona=doc.get("preferred_persona", "the_empathetic_friend"),
            active_projects=[Project(**p) for p in doc.get("active_projects", [])],
            recent_topics=doc.get("recent_topics", []),
            last_updated=doc.get("last_updated") or _now_iso(),
        )


# ---------------------------------------------------------------------------
# Multi-Layer Memory Repository
# ---------------------------------------------------------------------------

class MongoMemoryRepository:
    """MongoDB adapter for multi-layer memory management."""

    @property
    def _col(self):
        return get_db()["memories"]

    async def save(self, memory: Memory) -> str:
        """Save a new memory to the unified memories collection."""
        try:
            doc = {
                "_id": memory.id,
                "user_id": memory.user_id,
                "type": memory.type,
                "content": memory.content,
                "importance": memory.importance,
                "metadata": memory.metadata,
                "lifecycle": memory.lifecycle.__dict__,
                "embedding": memory.embedding,
                "updated_at": _now_iso()
            }
            await self._col.replace_one({"_id": memory.id}, doc, upsert=True)
            return memory.id
        except Exception as e:
            logger.error(f"Memory: Failed to save memory {memory.id} — {e}")
            return ""

    async def get_by_id(self, memory_id: str) -> Optional[Memory]:
        try:
            doc = await self._col.find_one({"_id": memory_id})
            if doc:
                return self._to_entity(doc)
        except Exception as e:
            logger.error(f"Memory: Failed to get memory {memory_id} — {e}")
        return None

    async def find_relevant(
        self, 
        user_id: str, 
        embedding: List[float], 
        types: Optional[List[MemoryType]] = None,
        k: int = 5
    ) -> List[Memory]:
        """Vector similarity search for memories across specific layers."""
        try:
            query = {"user_id": user_id, "embedding": {"$ne": None}}
            if types:
                query["type"] = {"$in": types}
            
            cursor = self._col.find(query)
            scored = []
            async for doc in cursor:
                emb = doc.get("embedding")
                if not emb: continue
                sim = _cosine_similarity(embedding, emb)
                if sim > 0.4:  # Threshold for relevance
                    scored.append((sim, doc))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            return [self._to_entity(doc) for _, doc in scored[:k]]
        except Exception as e:
            logger.error(f"Memory: Relevance search failed — {e}")
            return []

    async def delete(self, memory_id: str) -> bool:
        try:
            await self._col.delete_one({"_id": memory_id})
            return True
        except Exception as e:
            logger.error(f"Memory: Failed to delete {memory_id} — {e}")
            return False

    async def list_by_user(
        self, 
        user_id: str, 
        type: Optional[MemoryType] = None,
        limit: int = 50
    ) -> List[Memory]:
        try:
            query = {"user_id": user_id}
            if type:
                query["type"] = type
            cursor = self._col.find(query).sort("lifecycle.created_at", DESCENDING).limit(limit)
            return [self._to_entity(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"Memory: List failed for user {user_id} — {e}")
            return []

    async def get_expired_memories(self) -> List[Memory]:
        """Fetch memories that have passed their 'expires_at' date."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            cursor = self._col.find({"lifecycle.expires_at": {"$lt": now}})
            return [self._to_entity(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"Memory: Failed to get expired memories — {e}")
            return []

    async def get_consolidation_candidates(self, type: MemoryType, min_access: int = 5) -> List[Memory]:
        """Fetch memories (usually episodic) that are high-access and ready for abstraction."""
        try:
            query = {
                "type": type,
                "lifecycle.is_consolidated": False,
                "lifecycle.access_count": {"$gte": min_access}
            }
            cursor = self._col.find(query).sort("importance", DESCENDING)
            return [self._to_entity(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"Memory: Consolidation candidate search failed — {e}")
            return []

    def _to_entity(self, doc: dict) -> Memory:
        lifecycle_data = doc.get("lifecycle", {})
        # Handle ISO strings back to datetime
        def _to_dt(iso_str):
            if not iso_str: return None
            if isinstance(iso_str, datetime): return iso_str
            return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))

        lifecycle = MemoryLifecycle(
            created_at=_to_dt(lifecycle_data.get("created_at")),
            last_accessed=_to_dt(lifecycle_data.get("last_accessed")),
            access_count=lifecycle_data.get("access_count", 0),
            decay_rate=lifecycle_data.get("decay_rate", 0.01),
            is_consolidated=lifecycle_data.get("is_consolidated", False),
            expires_at=_to_dt(lifecycle_data.get("expires_at"))
        )
        return Memory(
            id=doc["_id"],
            user_id=doc["user_id"],
            type=MemoryType(doc["type"]),
            content=doc["content"],
            importance=MemoryImportance(doc.get("importance", 3)),
            metadata=doc.get("metadata", {}),
            lifecycle=lifecycle,
            embedding=doc.get("embedding")
        )


# ---------------------------------------------------------------------------
# Reflection Repository
# ---------------------------------------------------------------------------

class MongoReflectionRepository:
    """MongoDB adapter for managing long-term reflective insights."""

    @property
    def _col(self):
        return get_db()["reflections"]

    async def save(self, reflection: Reflection) -> str:
        """Save or update a reflection using upsert."""
        try:
            doc = {
                "_id": reflection.id,
                "user_id": reflection.user_id,
                "type": reflection.type,
                "content": reflection.content,
                "score": reflection.score.__dict__,
                "source_interaction_ids": reflection.source_interaction_ids,
                "embedding": reflection.embedding,
                "created_at": reflection.created_at.isoformat() if isinstance(reflection.created_at, datetime) else reflection.created_at,
            }
            await self._col.replace_one({"_id": reflection.id}, doc, upsert=True)
            return reflection.id
        except Exception as e:
            logger.error(f"Reflection: Failed to save {reflection.id} — {e}")
            return ""

    async def get_by_user(self, user_id: str, type: Optional[ReflectionType] = None) -> List[Reflection]:
        try:
            query = {"user_id": user_id}
            if type:
                query["type"] = type
            cursor = self._col.find(query).sort("score.confidence", DESCENDING)
            return [self._to_entity(doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"Reflection: Get by user failed — {e}")
            return []

    async def find_similar(self, user_id: str, embedding: List[float], k: int = 3) -> List[Reflection]:
        """Find similar existing reflections to avoid duplicates and allow merging."""
        try:
            query = {"user_id": user_id, "embedding": {"$ne": None}}
            cursor = self._col.find(query)
            scored = []
            async for doc in cursor:
                emb = doc.get("embedding")
                if not emb: continue
                sim = _cosine_similarity(embedding, emb)
                if sim > 0.85: # High threshold for duplication/merging
                    scored.append((sim, doc))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            return [self._to_entity(doc) for _, doc in scored[:k]]
        except Exception as e:
            logger.error(f"Reflection: Similarity search failed — {e}")
            return []

    async def delete(self, reflection_id: str) -> bool:
        try:
            await self._col.delete_one({"_id": reflection_id})
            return True
        except Exception as e:
            logger.error(f"Reflection: Delete failed — {e}")
            return False

    def _to_entity(self, doc: dict) -> Reflection:
        score_data = doc.get("score", {})
        # Handle ISO strings back to datetime
        def _to_dt(iso_str):
            if not iso_str: return datetime.now(timezone.utc)
            if isinstance(iso_str, datetime): return iso_str
            return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))

        score = ReflectionScore(
            confidence=score_data.get("confidence", 0.5),
            evidence_count=score_data.get("evidence_count", 1),
            relevance=score_data.get("relevance", 0.5),
            last_validated=_to_dt(score_data.get("last_validated"))
        )
        return Reflection(
            id=doc["_id"],
            user_id=doc["user_id"],
            type=ReflectionType(doc["type"]),
            content=doc["content"],
            score=score,
            source_interaction_ids=doc.get("source_interaction_ids", []),
            embedding=doc.get("embedding"),
            created_at=_to_dt(doc.get("created_at"))
        )


# ---------------------------------------------------------------------------
# Working Memory Repository
# ---------------------------------------------------------------------------

class MongoWorkingMemoryRepository:
    """MongoDB adapter for managing volatile session-based working memory."""

    @property
    def _col(self):
        return get_db()["working_memories"]

    async def get_by_session(self, user_id: str, session_id: str) -> Optional[WorkingMemory]:
        """Fetch working memory for a user session."""
        try:
            doc = await self._col.find_one({"user_id": user_id, "session_id": session_id})
            if doc:
                return self._to_entity(doc)
        except Exception as e:
            logger.error(f"WorkingMemory: Failed to get memory — {e}")
        return None

    async def update(self, memory: WorkingMemory) -> bool:
        """Update or create working memory state."""
        try:
            doc = {
                "user_id": memory.user_id,
                "session_id": memory.session_id,
                "turn_count": memory.turn_count,
                "active_project": memory.active_project,
                "active_problem": memory.active_problem,
                "active_topic": memory.active_topic,
                "current_goal": memory.current_goal,
                "recent_tasks": [t.__dict__ for t in memory.recent_tasks],
                "recent_entities": [e.__dict__ for e in memory.recent_entities],
                "recent_decisions": [d.__dict__ for d in memory.recent_decisions],
                "last_updated": memory.last_updated.isoformat() if isinstance(memory.last_updated, datetime) else memory.last_updated,
            }
            await self._col.replace_one(
                {"user_id": memory.user_id, "session_id": memory.session_id},
                doc,
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"WorkingMemory: Failed to update — {e}")
            return False

    def _to_entity(self, doc: dict) -> WorkingMemory:
        return WorkingMemory(
            user_id=doc["user_id"],
            session_id=doc["session_id"],
            turn_count=doc.get("turn_count", 0),
            active_project=doc.get("active_project"),
            active_problem=doc.get("active_problem"),
            active_topic=doc.get("active_topic"),
            current_goal=doc.get("current_goal"),
            recent_tasks=[Task(**t) for t in doc.get("recent_tasks", [])],
            recent_entities=[EntityMention(**e) for e in doc.get("recent_entities", [])],
            recent_decisions=[Decision(**d) for d in doc.get("recent_decisions", [])],
            last_updated=doc.get("last_updated") or _now_iso()
        )


# ---------------------------------------------------------------------------
# RL Bandit State Repository
# ---------------------------------------------------------------------------

class MongoRLRepository:
    """
    Persists and restores the full RL bandit state (all three policies,
    all arm alpha/beta counts) to MongoDB collection `rl_bandit_state`.

    Schema
    ------
    { _id: "singleton",
      updated_at: <iso>,
      state: { "thompson_sampling": { total_pulls, cumulative_reward, epsilon,
                                      arms: { arm_id: { n, total, mean, alpha,
                                                         beta, sq_total } } },
               "epsilon_greedy": { … },
               "ucb1":           { … } }
    }
    """

    _DOC_ID = "singleton"

    @property
    def _col(self):
        return get_db()["rl_bandit_state"]

    async def save_state(self, snapshot: dict) -> bool:
        """Upsert the full bandit state snapshot."""
        try:
            doc = {
                "_id":        self._DOC_ID,
                "updated_at": _now_iso(),
                "state":      snapshot,
            }
            await self._col.replace_one({"_id": self._DOC_ID}, doc, upsert=True)
            return True
        except Exception as e:
            logger.error(f"RL: Failed to save bandit state — {e}")
            return False

    async def load_state(self) -> Optional[dict]:
        """Load the bandit state snapshot. Returns None if not found."""
        try:
            doc = await self._col.find_one({"_id": self._DOC_ID})
            if doc:
                logger.info(f"RL: Loaded bandit state (updated {doc.get('updated_at', 'unknown')})")
                return doc.get("state")
        except Exception as e:
            logger.error(f"RL: Failed to load bandit state — {e}")
        return None

    async def get_reward_history(self, limit: int = 200) -> List[dict]:
        """
        Retrieve the last N reward events from the interactions collection.
        Used for the policy comparison report.
        """
        try:
            col = get_db()["interactions"]
            cursor = (
                col.find(
                    {"feedback_score": {"$ne": None}, "applied_action": {"$ne": None}},
                    {"feedback_score": 1, "applied_action": 1, "applied_persona": 1,
                     "applied_policy": 1, "created_at": 1},
                )
                .sort("created_at", DESCENDING)
                .limit(limit)
            )
            return [doc async for doc in cursor]
        except Exception as e:
            logger.error(f"RL: Failed to get reward history — {e}")
            return []
