"""
NeuroNest RAG Memory Agent
==========================
Stores conversation summaries locally and retrieves relevant past context
to make responses more personalized and connected across sessions.

How it works:
1. After each conversation session, a summary is generated and saved to a JSON file
2. When a user sends a new message, the agent searches past summaries for relevant context
3. Relevant context is injected into the LLM prompt so it can reference past patterns
4. Uses TF-IDF + cosine similarity for retrieval (no heavy ML dependencies needed)

Storage: backend/data/memory/{user_id}.json
Format: list of session summaries with embeddings (TF-IDF vectors)
"""

import json
import math
import logging
import re
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from collections import Counter

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Local storage directory
MEMORY_DIR = Path(__file__).parent.parent.parent / "data" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# How many past summaries to retrieve per query
TOP_K = 3
# Minimum similarity score to include a memory (0.0 to 1.0)
MIN_SIMILARITY = 0.05


# ── TF-IDF Vectorizer (lightweight, no dependencies) ─────────────────────────

def _tokenize(text: str) -> list[str]:
    """Simple tokenizer — lowercase, remove punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return [w for w in text.split() if len(w) > 2]


def _tfidf_vector(text: str, corpus_tokens: list[list[str]]) -> dict[str, float]:
    """
    Compute TF-IDF vector for a text given a corpus.
    Returns a dict of {term: tfidf_score}.
    """
    tokens = _tokenize(text)
    if not tokens:
        return {}

    # Term frequency
    tf = Counter(tokens)
    total = len(tokens)
    tf = {t: c / total for t, c in tf.items()}

    # Inverse document frequency
    n_docs = len(corpus_tokens) + 1  # +1 to avoid division by zero
    idf = {}
    for term in tf:
        doc_count = sum(1 for doc in corpus_tokens if term in doc) + 1
        idf[term] = math.log(n_docs / doc_count)

    return {t: tf[t] * idf[t] for t in tf}


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Compute cosine similarity between two TF-IDF vectors."""
    if not vec_a or not vec_b:
        return 0.0

    common = set(vec_a.keys()) & set(vec_b.keys())
    dot = sum(vec_a[t] * vec_b[t] for t in common)

    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


# ── Memory Storage ────────────────────────────────────────────────────────────

def _get_memory_path(user_id: str) -> Path:
    """Get the memory file path for a user."""
    # Sanitize user_id for use as filename
    safe_id = re.sub(r'[^\w\-]', '_', user_id)
    return MEMORY_DIR / f"{safe_id}.json"


def _load_memories(user_id: str) -> list[dict]:
    """Load all stored memories for a user."""
    path = _get_memory_path(user_id)
    if not path.exists():
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load memories for {user_id}: {e}")
        return []


def _save_memories(user_id: str, memories: list[dict]) -> None:
    """Save memories for a user."""
    path = _get_memory_path(user_id)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(memories, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save memories for {user_id}: {e}")


# ── Summary Generation ────────────────────────────────────────────────────────

async def generate_session_summary(
    user_id: str,
    session_id: str,
    conversation_history: list,
    detected_emotions: list[str],
) -> Optional[str]:
    """
    Generate a concise summary of a conversation session using the LLM.
    Saves the summary to local storage for future retrieval.
    """
    if not conversation_history or len(conversation_history) < 2:
        return None

    # Build conversation text for summarization
    conv_text = "\n".join([
        f"{msg.role if hasattr(msg, 'role') else msg.get('role', 'user')}: "
        f"{msg.content if hasattr(msg, 'content') else msg.get('content', '')}"
        for msg in conversation_history[-20:]  # Last 20 messages
    ])

    summary_prompt = f"""Summarize this mental wellness conversation in 3-4 sentences.
Focus on:
- What emotions the user expressed
- What situation or events they shared
- What support was provided
- Any patterns or recurring themes

Be specific and factual. This summary will be used to provide personalized support in future conversations.

Conversation:
{conv_text}

Summary:"""

    try:
        from app.agents.llm_router import invoke_with_fallback
        from langchain_core.messages import HumanMessage

        summary = await invoke_with_fallback(
            [HumanMessage(content=summary_prompt)],
            temperature=0.3,
            max_tokens=200,
        )

        # Store the summary
        await store_memory(
            user_id=user_id,
            session_id=session_id,
            summary=summary,
            emotions=detected_emotions,
            conversation_length=len(conversation_history),
        )

        logger.info(f"Session summary saved for user {user_id}, session {session_id}")
        return summary

    except Exception as e:
        logger.error(f"Failed to generate session summary: {e}")
        return None


async def store_memory(
    user_id: str,
    session_id: str,
    summary: str,
    emotions: list[str],
    conversation_length: int,
) -> None:
    """Store a session memory for a user."""
    memories = _load_memories(user_id)

    memory_entry = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "emotions": emotions,
        "conversation_length": conversation_length,
        # Store tokenized form for fast retrieval
        "tokens": _tokenize(summary + " " + " ".join(emotions)),
    }

    # Keep only the last 50 sessions to avoid unbounded growth
    memories.append(memory_entry)
    if len(memories) > 50:
        memories = memories[-50:]

    _save_memories(user_id, memories)


# ── Memory Retrieval (RAG) ────────────────────────────────────────────────────

def retrieve_relevant_memories(
    user_id: str,
    current_message: str,
    current_emotion: str = "",
    top_k: int = TOP_K,
) -> list[dict]:
    """
    Retrieve the most relevant past memories for the current message.
    Uses TF-IDF cosine similarity for retrieval.

    Returns list of relevant memory dicts, sorted by relevance.
    """
    memories = _load_memories(user_id)
    if not memories:
        return []

    # Build query from current message + emotion
    query = f"{current_message} {current_emotion}"
    query_tokens = _tokenize(query)

    if not query_tokens:
        # Return most recent memories if no query signal
        return memories[-top_k:]

    # Get all corpus tokens for IDF calculation
    corpus_tokens = [m.get("tokens", []) for m in memories]

    # Compute query vector
    query_vec = _tfidf_vector(query, corpus_tokens)

    # Score each memory
    scored = []
    for memory in memories:
        memory_text = memory.get("summary", "") + " " + " ".join(memory.get("emotions", []))
        memory_vec = _tfidf_vector(memory_text, corpus_tokens)
        score = _cosine_similarity(query_vec, memory_vec)
        scored.append((score, memory))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Return top_k above minimum similarity
    results = [m for score, m in scored[:top_k] if score >= MIN_SIMILARITY]

    if results:
        logger.info(f"Retrieved {len(results)} relevant memories for user {user_id}")

    return results


def format_memory_context(memories: list[dict]) -> str:
    """
    Format retrieved memories into a context string for the LLM prompt.
    """
    if not memories:
        return ""

    lines = ["PAST CONVERSATION CONTEXT (from previous sessions with this user):"]
    for i, memory in enumerate(memories, 1):
        timestamp = memory.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime("%B %d, %Y")
            except Exception:
                date_str = "Previously"
        else:
            date_str = "Previously"

        emotions = memory.get("emotions", [])
        emotion_str = ", ".join(emotions) if emotions else "unknown"
        summary = memory.get("summary", "")

        lines.append(f"\n[Session {i} — {date_str}]")
        lines.append(f"Emotions expressed: {emotion_str}")
        lines.append(f"Summary: {summary}")

    lines.append("\nUSE THIS CONTEXT to:")
    lines.append("- Reference patterns you've noticed (e.g., 'I've noticed you've been feeling stressed about work lately')")
    lines.append("- Show continuity (e.g., 'Last time we talked about your exam anxiety...')")
    lines.append("- Personalize your response based on what you know about this person")
    lines.append("- Only reference past context if it's genuinely relevant to what they're sharing now")

    return "\n".join(lines)


# ── Quick memory save for each message ───────────────────────────────────────

def save_message_to_memory(
    user_id: str,
    session_id: str,
    user_message: str,
    emotion: str,
    mood_level: str,
) -> None:
    """
    Save individual message metadata to memory for pattern tracking.
    This is a lightweight operation called after each message.
    """
    if not user_id:
        return

    memories = _load_memories(user_id)

    # Find existing session entry or create new one
    session_entry = None
    for m in memories:
        if m.get("session_id") == session_id and m.get("type") == "message_log":
            session_entry = m
            break

    if session_entry is None:
        session_entry = {
            "type": "message_log",
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "messages": [],
            "emotions": [],
            "tokens": [],
        }
        memories.append(session_entry)

    # Add this message
    session_entry["messages"].append({
        "content": user_message[:200],  # Truncate for storage efficiency
        "emotion": emotion,
        "mood_level": mood_level,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Track unique emotions
    if emotion and emotion not in session_entry["emotions"]:
        session_entry["emotions"].append(emotion)

    # Update tokens for retrieval
    all_text = " ".join([m["content"] for m in session_entry["messages"]])
    session_entry["tokens"] = _tokenize(all_text + " " + " ".join(session_entry["emotions"]))

    # Keep only last 50 entries
    if len(memories) > 50:
        memories = memories[-50:]

    _save_memories(user_id, memories)
