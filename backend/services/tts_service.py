"""
TTS Waterfall Service — Rate-Limit-Aware Failover
==================================================
Tries TTS providers in priority order. When a provider returns a
rate-limit error (HTTP 429 / quota exceeded), it is placed in a
cooldown for RATE_LIMIT_COOLDOWN_SECONDS and skipped on subsequent
requests until the cooldown expires.

Priority order:
  1. ElevenLabs   — most human, best emotional range
  2. Cartesia     — very low latency, natural sound
  3. Deepgram     — ultra-realistic Aura-2 voices
  4. OpenAI TTS   — robust neural voices
  5. LMNT         — warm, soothing voices
  6. Murf AI      — professional neural voices
  7. None         → frontend falls back to Web Speech API (browser)
"""

import os
import time
import uuid
import requests
from core.config import settings
from core.logger import logger

GENERATED_DIR = settings.GENERATED_DIR
os.makedirs(GENERATED_DIR, exist_ok=True)

# How long (seconds) to skip a TTS provider after a rate-limit hit
RATE_LIMIT_COOLDOWN_SECONDS = 60


# ─────────────────────────────────────────────────────────────────────
# Rate-Limit Tracker (shared with model_manager via separate instance)
# ─────────────────────────────────────────────────────────────────────

class _TtsRateLimitTracker:
    def __init__(self):
        self._cooldowns: dict[str, float] = {}

    def mark_rate_limited(self, provider: str) -> None:
        expires_at = time.time() + RATE_LIMIT_COOLDOWN_SECONDS
        self._cooldowns[provider] = expires_at
        logger.warning(
            f"TTS rate-limit hit on '{provider}'. "
            f"Cooling down for {RATE_LIMIT_COOLDOWN_SECONDS}s "
            f"(until {time.strftime('%H:%M:%S', time.localtime(expires_at))})."
        )

    def is_rate_limited(self, provider: str) -> bool:
        expires_at = self._cooldowns.get(provider)
        if expires_at is None:
            return False
        if time.time() < expires_at:
            remaining = int(expires_at - time.time())
            logger.info(f"TTS: Skipping '{provider}' — rate-limited for {remaining}s more.")
            return True
        del self._cooldowns[provider]
        return False

    def clear(self, provider: str) -> None:
        self._cooldowns.pop(provider, None)


_tts_rate_tracker = _TtsRateLimitTracker()


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "rate limit" in msg
        or "429" in msg
        or "quota" in msg
        or "too many requests" in msg
        or "resource_exhausted" in msg
        or "credits" in msg
        or "billing" in msg
    )


# ─────────────────────────────────────────────────────────────────────
# VOICE MAPPING (Stable Premade IDs)
# ─────────────────────────────────────────────────────────────────────
VOICE_MAPPING = {
    "Amelia": {
        "elevenlabs": "EXAVITQu4vr4xnSDxMaL",   # Bella
        "openai": "shimmer",
        "deepgram": "aura-2-thalia-en",
        "lmnt": "lily",
        "gender": "female",
    },
    "Rachel": {
        "elevenlabs": "21m00Tcm4TlvDq8ikWAM",   # Rachel
        "openai": "alloy",
        "deepgram": "aura-2-thalia-en",
        "lmnt": "lily",
        "gender": "female",
    },
    "Josh": {
        "elevenlabs": "CYw3kZgh2UMsS6E9HLBI",   # Dave
        "openai": "echo",
        "deepgram": "aura-2-orion-en",
        "lmnt": "ryan",
        "gender": "male",
    },
    "Nathan": {
        "elevenlabs": "IKne3meq5a9XoH5mC5Bq",   # Charlie
        "openai": "onyx",
        "deepgram": "aura-2-stella-en",
        "lmnt": "ryan",
        "gender": "male",
    },
    "Sam": {
        "elevenlabs": "D38z5qBF8C9GjznvC6tw",   # Fin
        "openai": "fable",
        "deepgram": "aura-2-arcas-en",
        "lmnt": "ryan",
        "gender": "male",
    },
}


# ─────────────────────────────────────────────────────────────────────
# 1. ElevenLabs — most human, best emotional voice
# ─────────────────────────────────────────────────────────────────────
def tts_elevenlabs(text: str, filename: str, voice_name: str = "Rachel") -> str | None:
    if not settings.ELEVENLABS_API_KEY:
        return None
    if _tts_rate_tracker.is_rate_limited("elevenlabs"):
        return None
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        voice_id = VOICE_MAPPING.get(voice_name, VOICE_MAPPING["Rachel"])["elevenlabs"]
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        with open(filename, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
        if os.path.exists(filename) and os.path.getsize(filename) > 1000:
            logger.info(f"TTS: OK ElevenLabs ({voice_name})")
            _tts_rate_tracker.clear("elevenlabs")
            return filename
        if os.path.exists(filename):
            os.remove(filename)
        return None
    except Exception as e:
        if _is_rate_limit_error(e):
            _tts_rate_tracker.mark_rate_limited("elevenlabs")
        else:
            logger.warning(f"TTS: ElevenLabs failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# 2. Cartesia — low latency
# ─────────────────────────────────────────────────────────────────────
def tts_cartesia(text: str, filename: str, voice_name: str = "Rachel") -> str | None:
    if not settings.CARTESIA_API_KEY:
        return None
    if _tts_rate_tracker.is_rate_limited("cartesia"):
        return None
    try:
        from cartesia import Cartesia
        client = Cartesia(api_key=settings.CARTESIA_API_KEY)
        voice_id = "694f9389-aac1-45b6-b726-9d9369183238"  # Default Female
        if VOICE_MAPPING.get(voice_name, {}).get("gender") == "male":
            voice_id = "79a125e8-cd45-4c13-8a25-39665a324572"  # Default Male
        audio_response = client.tts.bytes(
            model_id="sonic-2",
            transcript=text,
            voice={"mode": "id", "id": voice_id},
            output_format={"container": "mp3", "sample_rate": 44100, "bit_rate": 128000},
        )
        with open(filename, "wb") as f:
            if hasattr(audio_response, "__iter__") and not isinstance(
                audio_response, (bytes, bytearray)
            ):
                for chunk in audio_response:
                    f.write(chunk)
            else:
                f.write(audio_response)
        if os.path.exists(filename) and os.path.getsize(filename) > 1000:
            logger.info(f"TTS: OK Cartesia ({voice_name})")
            _tts_rate_tracker.clear("cartesia")
            return filename
        if os.path.exists(filename):
            os.remove(filename)
        return None
    except Exception as e:
        if _is_rate_limit_error(e):
            _tts_rate_tracker.mark_rate_limited("cartesia")
        else:
            logger.warning(f"TTS: Cartesia failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# 3. Deepgram Aura-2 — ultra-realistic voices
# ─────────────────────────────────────────────────────────────────────
def tts_deepgram(text: str, filename: str, voice_name: str = "Rachel") -> str | None:
    if not settings.DEEPGRAM_API_KEY:
        return None
    if _tts_rate_tracker.is_rate_limited("deepgram"):
        return None
    try:
        from deepgram import DeepgramClient
        
        client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
        model_id = VOICE_MAPPING.get(voice_name, VOICE_MAPPING["Rachel"])["deepgram"]
        
        # In SDK 7.x, the generate method returns an iterator of bytes.
        # We must specify encoding="mp3" to match our expected file format.
        audio_iterator = client.speak.v1.audio.generate(
            text=text,
            model=model_id,
            encoding="mp3"
        )
        
        with open(filename, "wb") as f:
            for chunk in audio_iterator:
                f.write(chunk)
                
        if os.path.exists(filename) and os.path.getsize(filename) > 1000:
            logger.info(f"TTS: OK Deepgram ({voice_name} Aura-2)")
            _tts_rate_tracker.clear("deepgram")
            return filename
        
        if os.path.exists(filename):
            os.remove(filename)
        return None
    except Exception as e:
        if _is_rate_limit_error(e):
            _tts_rate_tracker.mark_rate_limited("deepgram")
        else:
            logger.warning(f"TTS: Deepgram failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# 4. OpenAI TTS — robust fallback
# ─────────────────────────────────────────────────────────────────────
def tts_openai(text: str, filename: str, voice_name: str = "Rachel") -> str | None:
    if not settings.OPENAI_API_KEY:
        return None
    if _tts_rate_tracker.is_rate_limited("openai_tts"):
        return None
    try:
        from openai import OpenAI, RateLimitError as OpenAIRateLimitError
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        voice_id = VOICE_MAPPING.get(voice_name, VOICE_MAPPING["Rachel"])["openai"]
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice_id,
            input=text,
        )
        response.stream_to_file(filename)
        if os.path.exists(filename) and os.path.getsize(filename) > 1000:
            logger.info(f"TTS: OK OpenAI ({voice_name})")
            _tts_rate_tracker.clear("openai_tts")
            return filename
        return None
    except Exception as e:
        if _is_rate_limit_error(e):
            _tts_rate_tracker.mark_rate_limited("openai_tts")
        else:
            logger.warning(f"TTS: OpenAI TTS failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# 5. LMNT — warm, soothing voices
# ─────────────────────────────────────────────────────────────────────
def tts_lmnt(text: str, filename: str, voice_name: str = "Rachel") -> str | None:
    if not settings.LMNT_API_KEY:
        return None
    if _tts_rate_tracker.is_rate_limited("lmnt"):
        return None
    try:
        voice_id = VOICE_MAPPING.get(voice_name, VOICE_MAPPING["Rachel"]).get("lmnt", "lily")
        response = requests.post(
            "https://api.lmnt.com/v1/ai/speech",
            headers={
                "X-API-Key": settings.LMNT_API_KEY,
                "Content-Type": "application/json",
            },
            json={"voice": voice_id, "text": text, "format": "mp3"},
            timeout=30,
        )
        if response.status_code == 429:
            _tts_rate_tracker.mark_rate_limited("lmnt")
            return None
        response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(response.content)
        if os.path.exists(filename) and os.path.getsize(filename) > 1000:
            logger.info(f"TTS: OK LMNT ({voice_name})")
            _tts_rate_tracker.clear("lmnt")
            return filename
        if os.path.exists(filename):
            os.remove(filename)
        return None
    except Exception as e:
        if _is_rate_limit_error(e):
            _tts_rate_tracker.mark_rate_limited("lmnt")
        else:
            logger.warning(f"TTS: LMNT failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# 6. Murf AI — professional neural voices
# ─────────────────────────────────────────────────────────────────────
def tts_murf(text: str, filename: str, voice_name: str = "Rachel") -> str | None:
    if not settings.MURF_API_KEY:
        return None
    if _tts_rate_tracker.is_rate_limited("murf"):
        return None
    try:
        is_male = VOICE_MAPPING.get(voice_name, {}).get("gender") == "male"
        voice_id = "en-US-marcus" if is_male else "en-US-natalie"
        response = requests.post(
            "https://api.murf.ai/v1/speech/generate",
            headers={
                "api-key": settings.MURF_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "voiceId": voice_id,
                "text": text,
                "format": "MP3",
                "sampleRate": 44100,
            },
            timeout=30,
        )
        if response.status_code == 429:
            _tts_rate_tracker.mark_rate_limited("murf")
            return None
        response.raise_for_status()
        data = response.json()
        audio_url = data.get("audioFile") or data.get("audio_file")
        if not audio_url:
            return None
        # Download the audio file
        audio_resp = requests.get(audio_url, timeout=30)
        audio_resp.raise_for_status()
        with open(filename, "wb") as f:
            f.write(audio_resp.content)
        if os.path.exists(filename) and os.path.getsize(filename) > 1000:
            logger.info(f"TTS: OK Murf AI ({voice_name})")
            _tts_rate_tracker.clear("murf")
            return filename
        if os.path.exists(filename):
            os.remove(filename)
        return None
    except Exception as e:
        if _is_rate_limit_error(e):
            _tts_rate_tracker.mark_rate_limited("murf")
        else:
            logger.warning(f"TTS: Murf AI failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# WATERFALL ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────
def generate_tts(text: str, emotion: str, voice_name: str = "Rachel") -> str | None:
    """
    Runs the TTS waterfall. Rate-limited providers are automatically
    skipped. Returns the path to the generated MP3, or None if all
    providers fail (frontend will use browser Web Speech API).
    """
    file_id = str(uuid.uuid4())
    filename = f"{GENERATED_DIR}/{file_id}.mp3"

    providers = [
        tts_elevenlabs,
        tts_cartesia,
        tts_deepgram,
        tts_openai,
        tts_lmnt,
        tts_murf,
    ]

    for provider_fn in providers:
        try:
            result = provider_fn(text, filename, voice_name)
            if result:
                return result
        except Exception as e:
            logger.error(f"TTS Orchestrator: {provider_fn.__name__} crashed unexpectedly: {e}")

    logger.error("TTS: All providers exhausted or rate-limited. Frontend will use browser TTS.")
    return None
