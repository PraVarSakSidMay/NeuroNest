"""
RAG Service — Retrieval-Augmented Generation Memory Layer
==========================================================
Handles:
  - Generating text embeddings via OpenRouter (text-embedding-3-small)
  - Storing embeddings in MongoDB after each interaction
  - Retrieving semantically similar past memories before response generation
    (cosine similarity computed in Python via MongoEmbeddingRepository)
  - Computing the session-start greeting based on last session's emotion
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from openai import OpenAI
from services.model_manager import OPENROUTER_BASE_URL, OPENROUTER_SITE_URL, OPENROUTER_APP_NAME

from core.config import settings
from core.logger import logger


# ─────────────────────────────────────────────────────────────────────────────
# Emotion classification helpers
# ─────────────────────────────────────────────────────────────────────────────

NEGATIVE_EMOTIONS = {
    "sad", "sadness", "anxious", "anxiety", "angry", "anger", "anger",
    "distressed", "distress", "fear", "fearful", "worried", "frustrated",
    "upset", "depressed", "lonely", "nervous", "overwhelmed", "hopeless",
    "grief", "guilty", "shame", "panic", "stressed", "denial", "crying",
}


def _is_negative(emotion: str, stress_level: int) -> bool:
    """Returns True if the emotion is negative or stress is high."""
    emotion_lower = emotion.lower().strip()
    return any(neg in emotion_lower for neg in NEGATIVE_EMOTIONS) or stress_level > 55


def _relative_time(created_at_str: str) -> str:
    """Convert an ISO timestamp to a human-readable relative string."""
    try:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - created_at
        days = delta.days
        if days == 0:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago" if hours > 0 else "just now"
        if days == 1:
            return "yesterday"
        if days < 7:
            return f"{days} days ago"
        weeks = days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    except Exception:
        return "some time ago"





# ─────────────────────────────────────────────────────────────────────────────
# RAG Service class
# ─────────────────────────────────────────────────────────────────────────────

class RAGService:
    def __init__(self):
        self._embedding_client: Optional[OpenAI] = None

    @property
    def openai_client(self) -> OpenAI:
        """OpenAI-compatible client pointed at OpenRouter for embeddings."""
        if self._embedding_client is None:
            self._embedding_client = OpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": OPENROUTER_SITE_URL,
                    "X-Title": OPENROUTER_APP_NAME,
                },
            )
        return self._embedding_client

    # ── Embedding generation ────────────────────────────────────────────────

    def generate_embedding(self, text: str) -> Optional[list[float]]:
        """
        Generate a 1536-dim embedding for the given text using
        text-embedding-3-small via OpenRouter. Returns None on failure.
        """
        if not text or not text.strip():
            return None
        try:
            response = self.openai_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text.strip(),
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"RAG: Failed to generate embedding — {e}")
            return None

    # ── Memory retrieval ────────────────────────────────────────────────────

    async def retrieve_memories(
        self,
        supabase_client,  # kept for signature compatibility; ignored — we use MongoDB
        user_id: str,
        query_text: str,
        current_session_id: Optional[str] = None,
        k: int = None,
    ) -> list[dict]:
        """
        Retrieve the top-k semantically similar past interactions for this user.
        Uses MongoDB cosine-similarity search (MongoEmbeddingRepository).
        Returns a list of memory dicts formatted for prompt injection.
        """
        if k is None:
            k = settings.RAG_TOP_K

        embedding = self.generate_embedding(query_text)
        if embedding is None:
            logger.warning("RAG: Skipping memory retrieval — embedding generation failed.")
            return []

        try:
            from infrastructure.mongodb_repositories import MongoEmbeddingRepository
            repo = MongoEmbeddingRepository()
            # Await the async method directly (safe in async context)
            memories_raw = await repo.find_similar(
                user_id=user_id,
                query_embedding=embedding,
                k=k,
                exclude_session=current_session_id,
            )
            memories = []
            for row in memories_raw:
                memories.append({
                    **row,
                    "relative_time": _relative_time(row.get("created_at", "")),
                })
            logger.info(f"RAG: Retrieved {len(memories)} relevant memories for user {user_id}.")
            return memories
        except Exception as e:
            logger.error(f"RAG: Memory retrieval failed — {e}")
            return []

    # ── Session-start greeting ───────────────────────────────────────────────

    async def get_session_opener(
        self,
        supabase_client,  # kept for signature compatibility; ignored — we use MongoDB
        user_id: str,
        current_session_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Returns a warm, personalised greeting text based on the user's last
        known emotional state (from a previous session).

        - Negative / high-stress → "Are you still feeling [emotion]?"
        - Positive / calm       → "Hi! I hope you're still feeling [emotion]!"
        - No previous data      → None (frontend shows default welcome)

        Now queries MongoDB directly for the last interaction outside the
        current session.
        """
        try:
            from infrastructure.mongodb_client import get_db
            from pymongo import DESCENDING

            db = get_db()
            query: dict = {"user_id": user_id, "emotion": {"$ne": None}}
            if current_session_id:
                query["session_id"] = {"$ne": current_session_id}

            # Await async query directly (safe in async context)
            doc = await db["interactions"].find_one(
                query,
                sort=[("created_at", DESCENDING)],
            )

            if not doc:
                logger.info("RAG: No previous session emotion found — showing default greeting.")
                return None

            emotion: str = doc.get("emotion", "neutral") or "neutral"
            stress_level: int = doc.get("stress_level", 0) or 0
            relative = _relative_time(doc.get("created_at", ""))

            emotion_display = emotion.strip().lower()

            if _is_negative(emotion_display, stress_level):
                greeting = (
                    f"Hey… {relative} you were feeling {emotion_display}. "
                    f"Are you still feeling that way? I'm here for you. 💙"
                )
            else:
                greeting = (
                    f"Hi there! 😊 {relative} you were feeling {emotion_display}. "
                    f"I hope you're still riding that wave! How are you doing today?"
                )

            logger.info(f"RAG: Session opener generated — emotion='{emotion_display}', stress={stress_level}")
            return greeting

        except Exception as e:
            logger.error(f"RAG: Failed to get session opener — {e}")
            return None

    # ── Format memories for prompt injection ────────────────────────────────

    @staticmethod
    def format_memories_for_prompt(memories: list[dict]) -> str:
        """
        Converts retrieved memories into a concise, readable block
        that can be injected into the LLM system prompt.
        """
        if not memories:
            return ""

        lines = ["MEMORY CONTEXT (your past conversations with this user — reference naturally when relevant):"]
        for i, mem in enumerate(memories, 1):
            emotion_str = mem["emotion"]
            if mem.get("hidden_emotion"):
                emotion_str += f" (hidden: {mem['hidden_emotion']})"
            stress_str = f"stress {mem['stress_level']}%" if mem.get("stress_level") else ""

            lines.append(
                f"\n[Memory {i} — {mem['relative_time']}]"
                f"\n  User said: \"{mem['transcript'][:200]}\""
                f"\n  Felt: {emotion_str} {stress_str}"
                f"\n  You responded: \"{mem['response_text'][:200]}\""
            )

        lines.append(
            "\nUse these memories to provide continuity — e.g., 'I remember you mentioned...' "
            "Only reference them when genuinely relevant. Do not force it."
        )
        return "\n".join(lines)


# Module-level singleton
rag_service = RAGService()
