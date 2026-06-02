"""Provider interface protocols for AI/external services."""
from typing import Protocol, Optional, List
from domain.value_objects import Emotion


class ILLMProvider(Protocol):
    """Provider for LLM text generation."""
    
    def generate_response(
        self,
        transcript: str,
        emotion: dict,
        memories: List[dict],
        expression_history: List[str] = None,
        persona_name: str = None,
        learned_experiences: str = "",
    ) -> str:
        """Generate a text response based on transcript, emotion, memories, and expression history."""
        ...


class ITTSProvider(Protocol):
    """Provider for text-to-speech synthesis."""
    
    def synthesize(
        self,
        text: str,
        emotion: str,
        voice_name: str,
    ) -> Optional[str]:
        """Generate audio from text and return file path."""
        ...


class ITranscriptionProvider(Protocol):
    """Provider for audio transcription."""
    
    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file to text."""
        ...


class IEmbeddingProvider(Protocol):
    """Provider for text embeddings."""
    
    def generate(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for text."""
        ...


class IAudioFeatureProvider(Protocol):
    """Provider for audio feature extraction."""
    
    def extract(
        self,
        audio_path: str,
        frontend_features: Optional[dict] = None,
    ) -> dict:
        """Extract audio features from audio file."""
        ...