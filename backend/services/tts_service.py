"""
TTS Waterfall Service
=====================
Tries providers in priority order until one succeeds.
Priority:
  1. ElevenLabs   — most human, best emotional range
  2. Deepgram     — ultra-realistic Aura-2 voices
  3. Cartesia     — very low latency, natural sound
  4. LMNT         — warm, soothing voices
  5. Murf AI      — professional neural voices
  6. None         → frontend falls back to Web Speech API (browser, free, always works)
"""

import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DEEPGRAM_API_KEY   = os.getenv("DEEPGRAM_API_KEY")
CARTESIA_API_KEY   = os.getenv("CARTESIA_API_KEY")
LMNT_API_KEY       = os.getenv("LMNT_API_KEY")
MURF_API_KEY       = os.getenv("MURF_API_KEY")

GENERATED_DIR = "generated"
os.makedirs(GENERATED_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────
# 1. ElevenLabs — most human, best emotional voice
#    Voice: Rachel (JBFqnCBsd6RMkjVDRZzb) — warm, calm, caring
#    Free: 10,000 chars/month
# ─────────────────────────────────────────────────────────────────────
def tts_elevenlabs(text: str, filename: str) -> str | None:
    if not ELEVENLABS_API_KEY:
        return None
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio = client.text_to_speech.convert(
            voice_id="JBFqnCBsd6RMkjVDRZzb",  # Rachel — warm, empathetic female
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        with open(filename, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
        if os.path.getsize(filename) > 1000:
            print("✅ TTS: ElevenLabs (Rachel)")
            return filename
        os.remove(filename)
        return None
    except Exception as e:
        print(f"⚠️  ElevenLabs failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# 2. Deepgram Aura-2 — ultra-realistic voices
#    Voice: aura-2-thalia-en — warm, conversational female
#    Free: generous free credits
# ─────────────────────────────────────────────────────────────────────
def tts_deepgram(text: str, filename: str) -> str | None:
    if not DEEPGRAM_API_KEY:
        return None
    try:
        from deepgram import DeepgramClient, SpeakOptions
        client = DeepgramClient(DEEPGRAM_API_KEY)
        options = SpeakOptions(model="aura-2-thalia-en")
        response = client.speak.v("1").save(filename, {"text": text}, options)
        if os.path.exists(filename) and os.path.getsize(filename) > 1000:
            print("✅ TTS: Deepgram (Thalia Aura-2)")
            return filename
        return None
    except Exception as e:
        print(f"⚠️  Deepgram failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# 3. Cartesia — very low latency, natural voices
#    Voice: Friendly Southern Belle — warm, comforting
#    Free: trial credits
# ─────────────────────────────────────────────────────────────────────
def tts_cartesia(text: str, filename: str) -> str | None:
    if not CARTESIA_API_KEY:
        return None
    try:
        from cartesia import Cartesia
        client = Cartesia(api_key=CARTESIA_API_KEY)
        audio_bytes = client.tts.bytes(
            model_id="sonic-2",
            transcript=text,
            voice={
                "mode": "id",
                "id": "694f9389-aac1-45b6-b726-9d9369183238"  # Friendly Southern Belle
            },
            output_format={
                "container": "mp3",
                "sample_rate": 44100,
                "bit_rate": 128000
            }
        )
        with open(filename, "wb") as f:
            f.write(audio_bytes)
        if os.path.getsize(filename) > 1000:
            print("✅ TTS: Cartesia (Sonic-2)")
            return filename
        os.remove(filename)
        return None
    except Exception as e:
        print(f"⚠️  Cartesia failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# 4. LMNT — warm, soothing AI voices
#    Voice: lily — gentle, caring
#    Free: ~5,000 chars/month
# ─────────────────────────────────────────────────────────────────────
def tts_lmnt(text: str, filename: str) -> str | None:
    if not LMNT_API_KEY:
        return None
    try:
        response = requests.post(
            "https://api.lmnt.com/v1/ai/speech",
            headers={"X-API-Key": LMNT_API_KEY},
            json={"text": text, "voice": "lily", "format": "mp3", "speed": 0.95},
            timeout=20
        )
        response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(response.content)
        if os.path.getsize(filename) > 1000:
            print("✅ TTS: LMNT (Lily)")
            return filename
        os.remove(filename)
        return None
    except Exception as e:
        print(f"⚠️  LMNT failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# 5. Murf AI — professional neural voices
#    Voice: en-US-natalie — warm, professional
#    Free: ~10,000 chars/month
# ─────────────────────────────────────────────────────────────────────
def tts_murf(text: str, filename: str) -> str | None:
    if not MURF_API_KEY:
        return None
    try:
        response = requests.post(
            "https://api.murf.ai/v1/speech/generate",
            headers={"api-key": MURF_API_KEY, "Content-Type": "application/json"},
            json={"voiceId": "en-US-natalie", "text": text, "format": "MP3", "rate": -5, "pitch": 5},
            timeout=20
        )
        response.raise_for_status()
        data = response.json()
        audio_url = data.get("audioFile") or data.get("audio_file")
        if not audio_url:
            raise Exception("No audio URL in Murf response")
        audio_response = requests.get(audio_url, timeout=20)
        audio_response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(audio_response.content)
        if os.path.getsize(filename) > 1000:
            print("✅ TTS: Murf AI (Natalie)")
            return filename
        os.remove(filename)
        return None
    except Exception as e:
        print(f"⚠️  Murf AI failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# WATERFALL ORCHESTRATOR
# Returns a local file path on success, None if all providers exhausted.
# Frontend Web Speech API (browser) is the ultimate fallback.
# ─────────────────────────────────────────────────────────────────────
def generate_tts(text: str, emotion: str) -> str | None:
    file_id = str(uuid.uuid4())
    filename = f"{GENERATED_DIR}/{file_id}.mp3"

    providers = [
        tts_elevenlabs,
        tts_deepgram,
        tts_cartesia,
        tts_lmnt,
        tts_murf,
    ]

    for provider_fn in providers:
        result = provider_fn(text, filename)
        if result:
            return result

    print("⚠️  All TTS providers exhausted — frontend will use Web Speech API (browser).")
    return None
