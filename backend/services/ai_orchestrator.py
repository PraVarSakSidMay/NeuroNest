"""
AI Orchestration layer for the NeuroNest Reflective Journal.

Responsibilities:
- Build structured prompts from decrypted journal entries
- Call the Groq API (llama3-8b-8192)
- Parse and sanitize the raw AI response
- Enforce safe-tone rules via a diagnostic language blocklist

Public API
----------
- ``build_groq_prompt(entries, range_label)``  → str
- ``parse_groq_response(raw_text)``            → dict
- ``generate_emotional_summary(user_id, entries, range_info)`` → dict
"""

import json
import os
import re
from typing import Any

import groq

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Conservative character limit for the total prompt sent to Groq.
# Keeps us well within the llama3-8b-8192 context window.
GROQ_CONTEXT_LIMIT: int = 6000

# Terms that must never appear in AI output.  Checked case-insensitively.
DIAGNOSTIC_LANGUAGE_BLOCKLIST: list[str] = [
    "depression",
    "anxiety disorder",
    "bipolar",
    "schizophrenia",
    "ptsd",
    "post-traumatic",
    "borderline personality",
    "ocd",
    "obsessive-compulsive",
    "adhd",
    "attention deficit",
    "autism",
    "diagnose",
    "diagnosis",
    "disorder",
    "clinical",
    "psychiatric",
    "therapy",
    "therapist",
    "medication",
    "prescribe",
    "symptom",
    "treatment plan",
    "mental illness",
    "suicidal",
    "self-harm",
]

# Pre-compiled regex patterns for each blocklist term (case-insensitive).
# Sorted longest-first so that multi-word phrases are matched before their
# constituent words (e.g. "anxiety disorder" before "disorder").
_BLOCKLIST_PATTERNS: list[re.Pattern] = [
    re.compile(re.escape(term), re.IGNORECASE)
    for term in sorted(DIAGNOSTIC_LANGUAGE_BLOCKLIST, key=len, reverse=True)
]

# ---------------------------------------------------------------------------
# System instruction block (shared between build and prompt assembly)
# ---------------------------------------------------------------------------

_SYSTEM_INSTRUCTION = """\
You are a gentle, emotionally supportive reflection assistant.
Analyze the following journal entries and provide a JSON response with exactly these keys:
- "summary_text": A 2-3 sentence emotional summary (warm, supportive tone)
- "emotional_patterns": A list of short phrases describing emotional patterns
- "positive_observations": A list of short phrases about positive moments
- "gentle_insights": A list of short phrases with gentle, non-judgmental insights

IMPORTANT RULES:
- Never diagnose the user
- Never mention mental health disorders or conditions by name
- Never give medical advice
- Always use calm, supportive, non-clinical language
- Focus on patterns and observations, not judgments
- Do NOT include any personally identifying information
- Respond ONLY with valid JSON, no other text\
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sanitize_string(text: str) -> str:
    """Replace every blocklist term in *text* with ``'...'``."""
    for pattern in _BLOCKLIST_PATTERNS:
        text = pattern.sub("...", text)
    return text


def _sanitize_list(items: list[str]) -> list[str]:
    """Apply blocklist sanitization to every string in *items*."""
    return [_sanitize_string(item) for item in items]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_groq_prompt(entries: list[dict], range_label: str) -> str:
    """Build the structured prompt sent to the Groq API.

    Entry blocks are appended in chronological order.  If the total prompt
    length would exceed :data:`GROQ_CONTEXT_LIMIT`, the oldest entries are
    dropped first so that the most recent context is preserved.

    Args:
        entries:     A list of decrypted journal entry dicts.  Each dict is
                     expected to have at least ``created_at`` (str or
                     datetime), ``mood`` (str | None), and ``content`` (str).
        range_label: A human-readable label for the date range (e.g.
                     ``"Last 7 days"``).  Included in the prompt header.

    Returns:
        The complete prompt string ready to be sent to the Groq API.
    """
    header = (
        _SYSTEM_INSTRUCTION
        + f"\n\nJournal entries from {range_label}:\n"
    )

    # Build individual entry blocks
    entry_blocks: list[str] = []
    for entry in entries:
        created_at = entry.get("created_at", "")
        mood = entry.get("mood") or "not specified"
        content = entry.get("content", "")
        block = f"[Date: {created_at}] [Mood: {mood}]\n{content}\n---\n"
        entry_blocks.append(block)

    # Truncate oldest entries first if the prompt would exceed the limit.
    # We keep as many *recent* entries as possible.
    available_chars = GROQ_CONTEXT_LIMIT - len(header)
    kept_blocks: list[str] = []
    remaining = available_chars

    # Iterate in reverse (newest first) to keep the most recent entries
    for block in reversed(entry_blocks):
        if len(block) <= remaining:
            kept_blocks.insert(0, block)
            remaining -= len(block)
        # If a single block is larger than the remaining budget, skip it
        # (oldest entries are dropped first, so we continue to newer ones)

    return header + "".join(kept_blocks)


def parse_groq_response(raw_text: str) -> dict:
    """Parse and sanitize the raw text returned by the Groq API.

    Args:
        raw_text: The raw string content from the Groq API response.

    Returns:
        A dict with keys:
        - ``"summary_text"``          — str
        - ``"emotional_patterns"``    — list[str]
        - ``"positive_observations"`` — list[str]
        - ``"gentle_insights"``       — list[str]

    Raises:
        ValueError: ``"Malformed AI response"`` if JSON parsing fails or any
                    required key is missing / has the wrong type.
        ValueError: ``"Empty summary after sanitization"`` if ``summary_text``
                    is empty after applying the blocklist.
    """
    # ── 1. Parse JSON ─────────────────────────────────────────────────────
    try:
        data: Any = json.loads(raw_text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("Malformed AI response") from exc

    if not isinstance(data, dict):
        raise ValueError("Malformed AI response")

    # ── 2. Extract required keys ──────────────────────────────────────────
    required_keys = (
        "summary_text",
        "emotional_patterns",
        "positive_observations",
        "gentle_insights",
    )
    for key in required_keys:
        if key not in data:
            raise ValueError("Malformed AI response")

    summary_text: Any = data["summary_text"]
    emotional_patterns: Any = data["emotional_patterns"]
    positive_observations: Any = data["positive_observations"]
    gentle_insights: Any = data["gentle_insights"]

    # ── 3. Type validation ────────────────────────────────────────────────
    if not isinstance(summary_text, str):
        raise ValueError("Malformed AI response")
    if not isinstance(emotional_patterns, list):
        raise ValueError("Malformed AI response")
    if not isinstance(positive_observations, list):
        raise ValueError("Malformed AI response")
    if not isinstance(gentle_insights, list):
        raise ValueError("Malformed AI response")

    # Ensure all list items are strings
    for lst in (emotional_patterns, positive_observations, gentle_insights):
        if not all(isinstance(item, str) for item in lst):
            raise ValueError("Malformed AI response")

    # ── 4. Sanitize diagnostic language ───────────────────────────────────
    summary_text = _sanitize_string(summary_text)
    emotional_patterns = _sanitize_list(emotional_patterns)
    positive_observations = _sanitize_list(positive_observations)
    gentle_insights = _sanitize_list(gentle_insights)

    # ── 5. Guard against empty summary after sanitization ─────────────────
    if not summary_text.strip():
        raise ValueError("Empty summary after sanitization")

    return {
        "summary_text": summary_text,
        "emotional_patterns": emotional_patterns,
        "positive_observations": positive_observations,
        "gentle_insights": gentle_insights,
    }


def generate_emotional_summary(
    user_id: str,
    entries: list[dict],
    range_info: dict,
) -> dict:
    """Orchestrate the full AI summary generation pipeline.

    Builds the prompt, calls the Groq API, and returns the parsed +
    sanitized summary dict.

    Args:
        user_id:    The authenticated user's UUID (used for logging context
                    only — never included in the prompt).
        entries:    A list of decrypted journal entry dicts (plaintext
                    ``content``, ``mood``, ``created_at``).
        range_info: The resolved range dict from
                    :func:`~backend.services.range.resolve_reflection_range`,
                    containing ``preset``, ``start_date``, and ``end_date``.

    Returns:
        A dict with keys ``summary_text``, ``emotional_patterns``,
        ``positive_observations``, and ``gentle_insights``.

    Raises:
        Any exception from the Groq client or :func:`parse_groq_response`
        propagates to the caller (the router maps these to ``503``).
    """
    # Build a human-readable range label from the range_info dict
    start = range_info.get("start_date", "")
    end = range_info.get("end_date", "")
    range_label = f"{start} to {end}"

    prompt = build_groq_prompt(entries, range_label)

    # Call the Groq API with an updated model
    client = groq.Groq(api_key=os.environ["GROQ_API_KEY"])
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Updated model (replaces llama3-8b-8192)
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    raw_text: str = completion.choices[0].message.content

    return parse_groq_response(raw_text)
