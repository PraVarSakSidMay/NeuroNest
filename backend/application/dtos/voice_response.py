"""Response DTOs for voice processing use case."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class VoiceResponseDTO(BaseModel):
    """Standardized response DTO for voice processing."""
    transcript: str
    audio_features: Dict[str, Any] = Field(default_factory=dict)
    emotion: Dict[str, Any] = Field(default_factory=dict)
    response: str
    audio_url: Optional[str] = None
    memories_used: int = 0
    session_id: Optional[str] = None
    dashboard: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_result(cls, result: dict) -> "VoiceResponseDTO":
        return cls(
            transcript=result.get("transcript", ""),
            audio_features=result.get("audio_features", {}),
            emotion=result.get("emotion", {}),
            response=result.get("response", ""),
            audio_url=result.get("audio_url"),
            memories_used=result.get("memories_used", 0),
            session_id=result.get("session_id"),
            dashboard=result.get("dashboard"),
        )