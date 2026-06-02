"""Mock providers for deterministic testing."""
from typing import Optional, List
from unittest.mock import AsyncMock, MagicMock


class MockLLMProvider:
    """Mock LLM provider returning deterministic responses."""
    
    def __init__(
        self,
        response: str = "This is a test response",
        fail: bool = False,
        delay: float = 0,
    ):
        self.response = response
        self.fail = fail
        self.delay = delay
    
    def generate_response(
        self,
        transcript: str,
        emotion: dict,
        memories: List[dict],
        expression_history: List[str] = None,
    ) -> str:
        if self.fail:
            raise Exception("Mock LLM failure")
        return self.response


class MockTTSProvider:
    """Mock TTS provider returning test audio paths."""
    
    def __init__(
        self,
        audio_path: str = "/tmp/test_output.mp3",
        fail: bool = False,
    ):
        self.audio_path = audio_path
        self.fail = fail
    
    def synthesize(self, text: str, emotion: str, voice_name: str) -> Optional[str]:
        if self.fail:
            return None
        return self.audio_path


class MockTranscriptionProvider:
    """Mock transcription provider returning deterministic text."""
    
    def __init__(
        self,
        transcript: str = "This is a test transcript",
        fail: bool = False,
    ):
        self.transcript = transcript
        self.fail = fail
    
    def transcribe(self, audio_path: str) -> str:
        if self.fail:
            return ""
        return self.transcript


class MockEmbeddingProvider:
    """Mock embedding provider returning fixed vectors."""
    
    def __init__(self, vector_size: int = 1536, fail: bool = False):
        self.vector_size = vector_size
        self.fail = fail
    
    def generate(self, text: str) -> Optional[List[float]]:
        if self.fail:
            return None
        return [0.1] * self.vector_size


class MockAudioFeatureProvider:
    """Mock audio feature extractor returning test features."""
    
    def __init__(self, fail: bool = False):
        self.fail = fail
    
    def extract(self, audio_path: str, frontend_features: Optional[dict] = None) -> dict:
        if self.fail:
            return {}
        return {
            "pitch_mean": 200.0,
            "jitter": 0.01,
            "loudness": 0.5,
            "volume_std_dev": 0.1,
            "pitch_std_dev": 50.0,
            "is_trembling": False,
            "is_singing": False,
            "is_crying": False,
            "is_whispering": False,
            "voice_description": "test voice",
            "source": "test",
        }


# Factory functions
def create_mock_llm(response: str = "test response") -> MockLLMProvider:
    return MockLLMProvider(response=response)


def create_mock_tts(audio_path: str = "/tmp/test.mp3") -> MockTTSProvider:
    return MockTTSProvider(audio_path=audio_path)


def create_mock_transcription(transcript: str = "test transcript") -> MockTranscriptionProvider:
    return MockTranscriptionProvider(transcript=transcript)


def create_mock_embedding(size: int = 1536) -> MockEmbeddingProvider:
    return MockEmbeddingProvider(vector_size=size)