"""Provider adapters implementing AI service interfaces."""
from typing import Optional, List
from core.logger import logger
from services.tts_service import generate_tts as service_generate_tts
from services.whisper_service import transcribe_audio
from services.opensmile_service import extract_audio_features
from services.response_service import generate_response as service_generate_response
from services.rag_service import rag_service


class LLMProvider:
    """LLM provider adapter — routes through OpenRouter waterfall."""
    
    def generate_response(
        self,
        transcript: str,
        emotion: dict,
        memories: List[dict],
        expression_history: List[str] = None,
        persona_name: str = None,
        learned_experiences: str = "",
        user_state=None,
        memory_layers: dict = None,
        working_memory=None,
        conversation_plan=None,
        compiled_context=None,
        rl_prompt_instructions: str = "",
    ) -> str:
        try:
            expression_history = expression_history or []
            return service_generate_response(
                transcript, 
                emotion, 
                memories, 
                expression_history, 
                persona_name,
                learned_experiences,
                user_state,
                memory_layers,
                working_memory,
                conversation_plan,
                compiled_context,
                rl_prompt_instructions,
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "I am here and listening. Tell me more about how you are feeling."


class TTSServiceAdapter:
    """TTS service adapter."""
    
    def synthesize(
        self,
        text: str,
        emotion: str,
        voice_name: str = "Rachel",
    ) -> Optional[str]:
        try:
            return service_generate_tts(text, emotion, voice_name)
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return None

    # Backward-compat alias for legacy use-case port contract
    generate_tts = synthesize


class TranscriptionAdapter:
    """Audio transcription adapter — uses Deepgram Nova-2."""
    
    def transcribe(self, audio_path: str) -> str:
        try:
            return transcribe_audio(audio_path)
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""


class OpenAudioFeatureAdapter:
    """OpenSMILE audio feature extraction adapter."""
    
    def extract(
        self,
        audio_path: str,
        frontend_features: Optional[dict] = None,
    ) -> dict:
        try:
            return extract_audio_features(audio_path, frontend_features)
        except Exception as e:
            logger.error(f"Audio feature extraction failed: {e}")
            return {}


class EmbeddingProvider:
    """Embedding provider adapter — uses OpenRouter text-embedding-3-small."""
    
    def generate(self, text: str) -> Optional[List[float]]:
        try:
            return rag_service.generate_embedding(text)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    # Backward-compat alias for legacy use-case port contract
    generate_embedding = generate


# Backward-compat aliases
OpenAILLMProvider = LLMProvider
OpenAIEmbeddingProvider = EmbeddingProvider
WhisperTranscriptionAdapter = TranscriptionAdapter