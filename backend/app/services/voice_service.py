"""Voice Analysis Service — Whisper transcription + wellness pipeline."""
import tempfile, os, logging
from openai import AsyncOpenAI
from app.config import get_settings
from app.models.schemas import VoiceAnalysisResponse
from app.agents.mood_detector import detect_mood
from app.agents.wellness_agent import process_chat

settings = get_settings()
logger = logging.getLogger(__name__)

# Whisper supports: mp3, mp4, mpeg, mpga, m4a, wav, webm, ogg
SUPPORTED_AUDIO_FORMATS = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
    "audio/webm;codecs=opus": ".webm",
    "audio/ogg": ".ogg",
    "audio/ogg;codecs=opus": ".ogg",
    "audio/mp4": ".mp4",
    "audio/m4a": ".m4a",
    "audio/x-m4a": ".m4a",
}


async def transcribe_audio(audio_bytes: bytes, content_type: str) -> str:
    """Transcribe audio bytes to text using OpenAI Whisper."""
    # Normalize content type (strip codec params for extension lookup)
    base_type = content_type.split(";")[0].strip().lower()
    extension = SUPPORTED_AUDIO_FORMATS.get(content_type, SUPPORTED_AUDIO_FORMATS.get(base_type, ".webm"))

    logger.info(f"Transcribing audio: content_type={content_type}, extension={extension}, size={len(audio_bytes)} bytes")

    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        with open(tmp_path, "rb") as f:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text",
            )
        text = transcript.strip() if isinstance(transcript, str) else str(transcript).strip()
        logger.info(f"Transcription result: '{text[:100]}'")
        return text
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        raise
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def analyze_voice(
    audio_bytes: bytes,
    content_type: str,
    session_id: str = None,
    conversation_history: list = None,
) -> VoiceAnalysisResponse:
    """Full voice pipeline: transcribe → detect mood → generate response."""
    transcribed_text = await transcribe_audio(audio_bytes, content_type)

    if not transcribed_text or len(transcribed_text.strip()) < 2:
        transcribed_text = "I couldn't quite catch that. Could you try speaking again?"

    mood_result = await detect_mood(transcribed_text, conversation_history or [])
    chat_response = await process_chat(
        user_message=transcribed_text,
        conversation_history=conversation_history or [],
        session_id=session_id,
    )

    return VoiceAnalysisResponse(
        transcribed_text=transcribed_text,
        detected_emotion=mood_result["emotion"],
        mood_level=mood_result["mood_level"],
        confidence=mood_result["confidence"],
        chat_response=chat_response,
    )
