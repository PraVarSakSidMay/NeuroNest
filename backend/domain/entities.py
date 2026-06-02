"""Domain entities with behavior and invariants."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from uuid import uuid4
from domain.value_objects import Emotion, AudioFeatures


class User(BaseModel):
    """User entity."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    full_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def create(cls, user_id: Optional[str] = None, full_name: Optional[str] = None) -> "User":
        return cls(id=user_id or str(uuid4()), full_name=full_name)


class Session(BaseModel):
    """Session entity for interaction grouping."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, user_id: str) -> "Session":
        return cls(user_id=user_id)


class InteractionBase(BaseModel):
    """Base interaction data."""
    session_id: str
    user_id: str
    transcript: str
    raw_audio_url: Optional[str] = None
    features: Optional[AudioFeatures] = None
    emotion_data: Optional[Emotion] = None
    response_text: Optional[str] = None
    tts_audio_url: Optional[str] = None
    feedback_score: Optional[float] = None  # RL Reward: -1 to +1
    feedback_text: Optional[str] = None
    applied_persona: Optional[str] = None  # Which RL-selected persona was used


class InteractionCreate(InteractionBase):
    """Data required to create an interaction."""
    pass


class Interaction(InteractionBase):
    """Interaction entity with ID and timestamp."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def create(
        cls,
        session_id: str,
        user_id: str,
        transcript: str,
        features: Optional[AudioFeatures] = None,
        emotion_data: Optional[Emotion] = None,
        applied_persona: Optional[str] = None,
    ) -> "Interaction":
        return cls(
            session_id=session_id,
            user_id=user_id,
            transcript=transcript,
            features=features,
            emotion_data=emotion_data,
            applied_persona=applied_persona,
        )
    
    def with_response(self, response_text: str, tts_url: Optional[str] = None) -> "Interaction":
        self.response_text = response_text
        self.tts_audio_url = tts_url
        return self