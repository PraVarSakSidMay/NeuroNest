"""
RAG Service — Retrieval-Augmented Generation Memory Layer
==========================================================
Handles:
  - Generating text embeddings via OpenAI text-embedding-3-small
  - Storing embeddings in Supabase pgvector after each interaction
  - Retrieving semantically similar past memories before response generation
  - Computing the session-start greeting based on last session's emotion
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from openai import OpenAI

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
        self._openai_client: Optional[OpenAI] = None

    @property
    def openai_client(self) -> OpenAI:
        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client

    # ── Embedding generation ────────────────────────────────────────────────

    def generate_embedding(self, text: str) -> Optional[list[float]]:
        """
        Generate a 1536-dim embedding for the given text using
        OpenAI text-embedding-3-small. Returns None on failure.
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

    def retrieve_memories(
        self,
        supabase_client,
        user_id: str,
        query_text: str,
        current_session_id: Optional[str] = None,
        k: int = None,
    ) -> list[dict]:
        """
        Retrieve the top-k semantically similar past interactions for this user.
        Returns a list of memory dicts formatted for prompt injection.
        """
        if k is None:
            k = settings.RAG_TOP_K

        embedding = self.generate_embedding(query_text)
        if embedding is None:
            logger.warning("RAG: Skipping memory retrieval — embedding generation failed.")
            return []

        try:
            result = supabase_client.rpc(
                "match_interactions",
                {
                    "query_embedding": embedding,
                    "match_user_id": user_id,
                    "match_count": k,
                    "exclude_session": current_session_id,
                },
            ).execute()

            memories = []
            for row in (result.data or []):
                # Only include memories with meaningful similarity
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
                    "relative_time": _relative_time(row.get("created_at", "")),
                })

            logger.info(f"RAG: Retrieved {len(memories)} relevant memories for user {user_id}.")
            return memories

        except Exception as e:
            logger.error(f"RAG: Memory retrieval failed — {e}")
            return []

    # ── Session-start greeting ───────────────────────────────────────────────

    def get_session_opener(
        self,
        supabase_client,
        user_id: str,
        current_session_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Returns a warm, personalised greeting text based on the user's last
        known emotional state (from a previous session).

        - Negative / high-stress → "Are you still feeling [emotion]?"
        - Positive / calm       → "Hi! I hope you're still feeling [emotion]!"
        - No previous data      → None (frontend shows default welcome)
        """
        try:
            result = supabase_client.rpc(
                "get_last_session_emotion",
                {
                    "lookup_user_id": user_id,
                    "current_session": current_session_id,
                },
            ).execute()

            if not result.data:
                logger.info("RAG: No previous session emotion found — showing default greeting.")
                return None

            row = result.data[0]
            emotion: str = row.get("emotion", "neutral") or "neutral"
            stress_level: int = row.get("stress_level", 0) or 0
            relative = _relative_time(row.get("created_at", ""))

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
