"""
Model Manager — LLM & STT Waterfall with Rate-Limit-Aware Failover
===================================================================
All LLM calls now route through OpenRouter (openai-compatible SDK).
When a provider returns a rate-limit error (HTTP 429), it is placed
in a cooldown for RATE_LIMIT_COOLDOWN_SECONDS seconds so the next
tier is tried immediately — no wasted latency, no burned retries.

LLM Waterfall (via OpenRouter):
  Tier 1 — google/gemini-2.0-flash-exp:free (Google / OpenRouter — free)
  Tier 2 — google/gemini-flash-1.5       (Google / OpenRouter)
  Tier 3 — anthropic/claude-3.5-haiku    (Anthropic / OpenRouter)
  Tier 4 — meta-llama/llama-3.3-70b-instruct (Meta / OpenRouter)
  Tier 5 — mistralai/mistral-small-3.1   (Mistral / OpenRouter)

STT Waterfall:
  Tier 1 — Deepgram Nova-2               (Deepgram)
"""

import base64
import os
import time
from openai import OpenAI, RateLimitError as OpenAIRateLimitError
import requests
from core.config import settings
from core.logger import logger

# How long (seconds) to skip a provider after it hits a rate limit
RATE_LIMIT_COOLDOWN_SECONDS = 60

# OpenRouter base URL (OpenAI-compatible)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_STT_URL = f"{OPENROUTER_BASE_URL}/audio/transcriptions"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OPENROUTER_SITE_URL = "https://neuronest.app"
OPENROUTER_APP_NAME = "NeuroNest"
STT_CONTEXT_PROMPT = (
    "The user is testing a voice assistant. Common phrases include: "
    "'hey, am I audible?', 'can you hear me?', and 'is my voice clear?'. "
    "Prefer literal question wording over converting 'am I' into 'I'm'."
)


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
    Handles OpenAI SDK (also used for OpenRouter), and generic HTTP errors.
    """
    if isinstance(exc, OpenAIRateLimitError):
        return True
    msg = str(exc).lower()
    return (
        "rate limit" in msg
        or "429" in msg
        or "quota" in msg
        or "too many requests" in msg
        or "resource_exhausted" in msg  # Google / Gemini
        or "insufficient credits" in msg
    )


def _make_openrouter_client() -> OpenAI:
    """Create an OpenAI-compatible client pointed at OpenRouter."""
    return OpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": OPENROUTER_SITE_URL,
            "X-Title": OPENROUTER_APP_NAME,
        },
    )


def _audio_format_from_path(audio_path: str) -> str:
    ext = os.path.splitext(audio_path)[1].lower().lstrip(".")
    if ext in {"mp3", "wav", "flac", "m4a", "ogg", "webm", "aac", "mp4"}:
        return ext
    return "webm"


class ModelManager:
    def __init__(self):
        # Single OpenRouter client handles all LLM tiers
        self._openrouter_client: OpenAI | None = None

        # Deepgram for STT
        self._deepgram_client = None

    @property
    def openrouter_client(self) -> OpenAI:
        if self._openrouter_client is None:
            self._openrouter_client = _make_openrouter_client()
        return self._openrouter_client

    def _call_openrouter(
        self,
        model: str,
        provider_key: str,
        system_prompt: str,
        user_message: str,
        json_mode: bool = False,
        timeout: int = 15,
    ) -> str | None:
        """
        Helper: call a single OpenRouter model. Returns the response text
        or None if it failed (sets rate-limit cooldown when appropriate).
        """
        if _rate_tracker.is_rate_limited(provider_key):
            return None
        try:
            kwargs: dict = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "timeout": timeout,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = self.openrouter_client.chat.completions.create(**kwargs)
            _rate_tracker.clear(provider_key)
            return response.choices[0].message.content
        except Exception as e:
            if _is_rate_limit_error(e):
                _rate_tracker.mark_rate_limited(provider_key)
            else:
                logger.warning(f"OpenRouter model '{model}' failed: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────
    # LLM WATERFALL
    # ──────────────────────────────────────────────────────────────────

    def get_llm_response(
        self, transcript: str, system_prompt: str, json_mode: bool = False
    ) -> str:
        """
        Tries LLM providers via OpenRouter in priority order.
        Rate-limited providers are skipped until their cooldown expires.
        """
        if not settings.OPENROUTER_API_KEY:
            logger.error("AI: OPENROUTER_API_KEY not set — cannot call any LLM.")
            return (
                "I'm here for you, but I'm having trouble connecting right now. "
                "Can you tell me more?"
            )

        tiers = [
            # (display_name, model_id, provider_key, supports_json, timeout)
            (
                "Gemini 2.0 Flash Exp (free)",
                "google/gemini-2.0-flash-exp:free",
                "or_gemini_2_flash_exp",
                False,
                10,
            ),
            (
                "Gemini Flash 1.5",
                "google/gemini-flash-1.5",
                "or_gemini_flash_1_5",
                False,
                10,
            ),
            (
                "Claude 3.5 Haiku",
                "anthropic/claude-3.5-haiku",
                "or_claude_haiku",
                False,
                12,
            ),
            (
                "Llama 3.3 70B",
                "meta-llama/llama-3.3-70b-instruct",
                "or_llama_70b",
                True,
                15,
            ),
            (
                "Mistral Small 3.1",
                "mistralai/mistral-small-3.1-24b-instruct:free",
                "or_mistral_small",
                True,
                12,
            ),
        ]

        for display_name, model_id, provider_key, supports_json, timeout in tiers:
            logger.info(f"AI: Trying {display_name} via OpenRouter")
            # Only pass json_mode if this model supports it; otherwise the
            # system_prompt already asks for JSON so the model will comply.
            result = self._call_openrouter(
                model=model_id,
                provider_key=provider_key,
                system_prompt=system_prompt,
                user_message=transcript,
                json_mode=(json_mode and supports_json),
                timeout=timeout,
            )
            if result is not None:
                logger.info(f"AI: ✅ Response from {display_name}")
                return result

        # ── Final Fallback ────────────────────────────────────────────
        logger.error("AI: ❌ All LLM providers exhausted or rate-limited.")
        return (
            "I'm here for you, but I'm having a bit of trouble processing that right now. "
            "Can you tell me more?"
        )

    # ──────────────────────────────────────────────────────────────────
    # STT — Deepgram Nova-2
    # ──────────────────────────────────────────────────────────────────

    def get_transcription(self, audio_path: str) -> str:
        """
        Transcribes audio using Deepgram Nova-2.
        Falls back to a placeholder message if Deepgram is unavailable.
        """

        # ── Tier 1: Deepgram Nova-2 ──────────────────────────────────
        if settings.DEEPGRAM_API_KEY and not _rate_tracker.is_rate_limited("deepgram_stt"):
            try:
                logger.info("STT: Trying Deepgram Nova-2")
                from deepgram import DeepgramClient

                client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)

                with open(audio_path, "rb") as audio_file:
                    audio_data = audio_file.read()

                response = client.listen.v1.media.transcribe_file(
                    request=audio_data,
                    model="nova-2",
                    smart_format=True,
                    language="en",
                )
                transcript = (
                    response.results.channels[0].alternatives[0].transcript
                )
                if transcript and transcript.strip():
                    _rate_tracker.clear("deepgram_stt")
                    logger.info("STT: ✅ Deepgram Nova-2 succeeded")
                    return transcript.strip()
                logger.warning("STT: Deepgram returned empty transcript")
            except Exception as e:
                if _is_rate_limit_error(e):
                    _rate_tracker.mark_rate_limited("deepgram_stt")
                else:
                    logger.warning(f"STT: Deepgram failed: {e}")

        logger.error("STT: ❌ All STT providers exhausted or unavailable.")
        return "[Inaudible or audio error — transcription unavailable]"

    def get_transcription(self, audio_path: str) -> str:
        """Transcribe audio with OpenRouter, Groq Whisper, then Deepgram."""

        if settings.OPENROUTER_API_KEY:
            for model in ("openai/gpt-4o-mini-transcribe", "openai/whisper-large-v3-turbo"):
                provider_key = f"openrouter_stt:{model}"
                if _rate_tracker.is_rate_limited(provider_key):
                    continue
                try:
                    logger.info(f"STT: Trying OpenRouter {model}")
                    with open(audio_path, "rb") as audio_file:
                        audio_data = base64.b64encode(audio_file.read()).decode("ascii")

                    response = requests.post(
                        OPENROUTER_STT_URL,
                        headers={
                            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": OPENROUTER_SITE_URL,
                            "X-Title": OPENROUTER_APP_NAME,
                        },
                        json={
                            "model": model,
                            "input_audio": {
                                "data": audio_data,
                                "format": _audio_format_from_path(audio_path),
                            },
                            "language": "en",
                            "temperature": 0,
                            "provider": {
                                "options": {
                                    "openai": {"prompt": STT_CONTEXT_PROMPT},
                                    "groq": {"prompt": STT_CONTEXT_PROMPT},
                                }
                            },
                        },
                        timeout=12,
                    )
                    response.raise_for_status()
                    transcript = (response.json().get("text") or "").strip()
                    if transcript:
                        _rate_tracker.clear(provider_key)
                        logger.info(f"STT: OpenRouter {model} succeeded")
                        return transcript
                    logger.warning(f"STT: OpenRouter {model} returned empty transcript")
                except Exception as e:
                    if _is_rate_limit_error(e):
                        _rate_tracker.mark_rate_limited(provider_key)
                    else:
                        logger.warning(f"STT: OpenRouter {model} failed: {e}")

        if settings.GROQ_API_KEY and not _rate_tracker.is_rate_limited("groq_whisper_large_v3"):
            try:
                logger.info("STT: Trying Groq Whisper Large V3")
                groq_client = OpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url=GROQ_BASE_URL,
                )
                with open(audio_path, "rb") as audio_file:
                    response = groq_client.audio.transcriptions.create(
                        file=(os.path.basename(audio_path), audio_file),
                        model="whisper-large-v3",
                        language="en",
                        temperature=0,
                        prompt=STT_CONTEXT_PROMPT,
                        timeout=10,
                    )
                transcript = (getattr(response, "text", None) or "").strip()
                if transcript:
                    _rate_tracker.clear("groq_whisper_large_v3")
                    logger.info("STT: Groq Whisper Large V3 succeeded")
                    return transcript
                logger.warning("STT: Groq Whisper returned empty transcript")
            except Exception as e:
                if _is_rate_limit_error(e):
                    _rate_tracker.mark_rate_limited("groq_whisper_large_v3")
                else:
                    logger.warning(f"STT: Groq Whisper failed: {e}")

        if settings.DEEPGRAM_API_KEY and not _rate_tracker.is_rate_limited("deepgram_stt"):
            from deepgram import DeepgramClient

            for model in ("nova-3", "nova-2"):
                try:
                    logger.info(f"STT: Trying Deepgram {model}")
                    client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
                    with open(audio_path, "rb") as audio_file:
                        audio_data = audio_file.read()

                    response = client.listen.v1.media.transcribe_file(
                        request=audio_data,
                        model=model,
                        smart_format=True,
                        language="en",
                    )
                    transcript = (
                        response.results.channels[0].alternatives[0].transcript
                    )
                    if transcript and transcript.strip():
                        _rate_tracker.clear("deepgram_stt")
                        logger.info(f"STT: Deepgram {model} succeeded")
                        return transcript.strip()
                    logger.warning(f"STT: Deepgram {model} returned empty transcript")
                except Exception as e:
                    if _is_rate_limit_error(e):
                        _rate_tracker.mark_rate_limited("deepgram_stt")
                        break
                    logger.warning(f"STT: Deepgram {model} failed: {e}")

        logger.error("STT: All providers exhausted or unavailable.")
        return "[Inaudible or audio error - transcription unavailable]"


model_manager = ModelManager()
