from typing import Optional, List
from infrastructure.ai_providers import (
    OpenAILLMProvider,
    TTSServiceAdapter,
    OpenAIEmbeddingProvider,
)


class OpenAIAdapter:
    """Adapter implementing multiple ports: embedding, LLM, and TTS."""
    
    def __init__(self):
        self._llm = OpenAILLMProvider()
        self._tts = TTSServiceAdapter()
        self._embedding = OpenAIEmbeddingProvider()
        
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        return self._embedding.generate(text)

    def generate_response(self, transcript: str, emotion: dict, memories: list, expression_history: list = None) -> str:
        return self._llm.generate_response(transcript, emotion, memories, expression_history)
    
    def generate_tts(self, text: str, emotion: str, voice_name: str) -> Optional[str]:
        return self._tts.synthesize(text, emotion, voice_name)
