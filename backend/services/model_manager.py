"""
Model Manager — LLM & STT Waterfall with Rate-Limit-Aware Failover
===================================================================
When a provider returns a rate-limit error (HTTP 429 / RateLimitError),
it is placed in a cooldown for RATE_LIMIT_COOLDOWN_SECONDS seconds.
During cooldown that provider is skipped entirely so the next tier is
tried immediately — no wasted latency, no burned retries.

LLM Waterfall (effectiveness-first):
  Tier 1 — GPT-4o              (OpenAI)
  Tier 2 — Llama-3.3-70B       (Groq)
  Tier 3 — GPT-4o-mini         (OpenAI)
  Tier 4 — Llama-3.1-8B        (Groq)
  Tier 5 — Gemini 1.5 Flash    (Google)

STT Waterfall:
  Tier 1 — Whisper Large V3    (Groq)
  Tier 2 — Whisper-1           (OpenAI)
"""

import os
import time
import json
from openai import OpenAI, RateLimitError as OpenAIRateLimitError
from groq import Groq, RateLimitError as GroqRateLimitError
import google.generativeai as genai
from core.config import settings
from core.logger import logger

# How long (seconds) to skip a provider after it hits a rate limit
RATE_LIMIT_COOLDOWN_SECONDS = 60


class RateLimitTracker:
    """
    Tracks per-provider rate-limit cooldowns.
    Thread-safe enough for single-worker uvicorn; for multi-worker
    deployments use Redis or a shared cache instead.
    """

    def __init__(self):
        # { provider_key: unix_timestamp_when_cooldown_expires }
        self._cooldowns: dict[str, float] = {}

    def mark_rate_limited(self, provider: str) -> None:
        expires_at = time.time() + RATE_LIMIT_COOLDOWN_SECONDS
        self._cooldowns[provider] = expires_at
        logger.warning(
            f"⏳ Rate-limit hit on '{provider}'. "
            f"Cooling down for {RATE_LIMIT_COOLDOWN_SECONDS}s "
            f"(until {time.strftime('%H:%M:%S', time.localtime(expires_at))})."
        )

    def is_rate_limited(self, provider: str) -> bool:
        expires_at = self._cooldowns.get(provider)
        if expires_at is None:
            return False
        if time.time() < expires_at:
            remaining = int(expires_at - time.time())
            logger.info(f"⏭️  Skipping '{provider}' — rate-limited for {remaining}s more.")
            return True
        # Cooldown expired — clear it
        del self._cooldowns[provider]
        return False

    def clear(self, provider: str) -> None:
        self._cooldowns.pop(provider, None)


# Module-level singleton shared across all requests
_rate_tracker = RateLimitTracker()


def _is_rate_limit_error(exc: Exception) -> bool:
    """
    Returns True if the exception represents an API rate-limit (HTTP 429).
    Handles OpenAI, Groq, and generic HTTP errors.
    """
    if isinstance(exc, (OpenAIRateLimitError, GroqRateLimitError)):
        return True
    msg = str(exc).lower()
    return (
        "rate limit" in msg
        or "429" in msg
        or "quota" in msg
        or "too many requests" in msg
        or "resource_exhausted" in msg  # Google / Gemini
    )


class ModelManager:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)

        # Configure Gemini
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.gemini_model = None

    # ──────────────────────────────────────────────────────────────────
    # LLM WATERFALL
    # ──────────────────────────────────────────────────────────────────

    def get_llm_response(
        self, transcript: str, system_prompt: str, json_mode: bool = False
    ) -> str:
        """
        Tries LLM providers in priority order.
        Rate-limited providers are skipped until their cooldown expires.
        """

        # ── Tier 1: GPT-4o ──────────────────────────────────────────
        if not _rate_tracker.is_rate_limited("openai_gpt4o"):
            try:
                logger.info("AI: Trying Tier 1 (GPT-4o)")
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": transcript},
                    ],
                    response_format={"type": "json_object"} if json_mode else None,
                )
                _rate_tracker.clear("openai_gpt4o")
                return response.choices[0].message.content
            except Exception as e:
                if _is_rate_limit_error(e):
                    _rate_tracker.mark_rate_limited("openai_gpt4o")
                else:
                    logger.warning(f"Tier 1 (GPT-4o) failed: {e}")

        # ── Tier 2: Groq Llama-3.3-70B ──────────────────────────────
        if not _rate_tracker.is_rate_limited("groq_llama70b"):
            try:
                logger.info("AI: Trying Tier 2 (Groq Llama-3.3-70B)")
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": transcript},
                    ],
                    response_format={"type": "json_object"} if json_mode else None,
                )
                _rate_tracker.clear("groq_llama70b")
                return response.choices[0].message.content
            except Exception as e:
                if _is_rate_limit_error(e):
                    _rate_tracker.mark_rate_limited("groq_llama70b")
                else:
                    logger.warning(f"Tier 2 (Llama-3.3-70B) failed: {e}")

        # ── Tier 3: GPT-4o-mini ──────────────────────────────────────
        if not _rate_tracker.is_rate_limited("openai_gpt4o_mini"):
            try:
                logger.info("AI: Trying Tier 3 (GPT-4o-mini)")
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": transcript},
                    ],
                    response_format={"type": "json_object"} if json_mode else None,
                )
                _rate_tracker.clear("openai_gpt4o_mini")
                return response.choices[0].message.content
            except Exception as e:
                if _is_rate_limit_error(e):
                    _rate_tracker.mark_rate_limited("openai_gpt4o_mini")
                else:
                    logger.warning(f"Tier 3 (GPT-4o-mini) failed: {e}")

        # ── Tier 4: Groq Llama-3.1-8B ───────────────────────────────
        if not _rate_tracker.is_rate_limited("groq_llama8b"):
            try:
                logger.info("AI: Trying Tier 4 (Groq Llama-3.1-8B)")
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": transcript},
                    ],
                    response_format={"type": "json_object"} if json_mode else None,
                )
                _rate_tracker.clear("groq_llama8b")
                return response.choices[0].message.content
            except Exception as e:
                if _is_rate_limit_error(e):
                    _rate_tracker.mark_rate_limited("groq_llama8b")
                else:
                    logger.warning(f"Tier 4 (Llama-3.1-8B) failed: {e}")

        # ── Tier 5: Gemini 1.5 Flash ─────────────────────────────────
        if self.gemini_model and not _rate_tracker.is_rate_limited("gemini_flash"):
            try:
                logger.info("AI: Trying Tier 5 (Gemini 1.5 Flash)")
                prompt = f"{system_prompt}\n\nUser: {transcript}"
                if json_mode:
                    prompt += "\n\nReturn ONLY a valid JSON object, no markdown."
                response = self.gemini_model.generate_content(prompt)
                _rate_tracker.clear("gemini_flash")
                return response.text
            except Exception as e:
                if _is_rate_limit_error(e):
                    _rate_tracker.mark_rate_limited("gemini_flash")
                else:
                    logger.error(f"Tier 5 (Gemini) failed: {e}")

        # ── Final Fallback ────────────────────────────────────────────
        logger.error("AI: ❌ All LLM providers exhausted or rate-limited.")
        return (
            "I'm here for you, but I'm having a bit of trouble processing that right now. "
            "Can you tell me more?"
        )

    # ──────────────────────────────────────────────────────────────────
    # STT WATERFALL
    # ──────────────────────────────────────────────────────────────────

    def get_transcription(self, audio_path: str) -> str:
        """
        Tries STT providers in priority order.
        Rate-limited providers are skipped until their cooldown expires.
        """

        # ── Tier 1: Groq Whisper Large V3 ───────────────────────────
        if not _rate_tracker.is_rate_limited("groq_whisper"):
            try:
                logger.info("STT: Trying Tier 1 (Groq Whisper Large V3)")
                with open(audio_path, "rb") as file:
                    transcription = self.groq_client.audio.transcriptions.create(
                        file=(os.path.basename(audio_path), file.read()),
                        model="whisper-large-v3",
                    )
                _rate_tracker.clear("groq_whisper")
                return transcription.text
            except Exception as e:
                if _is_rate_limit_error(e):
                    _rate_tracker.mark_rate_limited("groq_whisper")
                else:
                    logger.warning(f"STT: Tier 1 (Groq Whisper) failed: {e}")

        # ── Tier 2: OpenAI Whisper-1 ─────────────────────────────────
        if not _rate_tracker.is_rate_limited("openai_whisper"):
            try:
                logger.info("STT: Trying Tier 2 (OpenAI Whisper-1)")
                with open(audio_path, "rb") as file:
                    transcription = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=file,
                    )
                _rate_tracker.clear("openai_whisper")
                return transcription.text
            except Exception as e:
                if _is_rate_limit_error(e):
                    _rate_tracker.mark_rate_limited("openai_whisper")
                else:
                    logger.error(f"STT: Tier 2 (OpenAI Whisper) failed: {e}")

        logger.error("STT: ❌ All STT providers exhausted or rate-limited.")
        return "[Inaudible or audio error — all transcription providers unavailable]"


model_manager = ModelManager()
