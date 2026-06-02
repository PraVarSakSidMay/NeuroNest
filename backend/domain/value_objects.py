"""Domain value objects with invariants and validation."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class EmotionEnum(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    CONFUSED = "confused"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    DEPRESSED = "depressed"
    CALM = "calm"


class Emotion(BaseModel):
    """Emotion value object with confidence tracking."""
    emotion: EmotionEnum = Field(default=EmotionEnum.NEUTRAL)
    stress_level: int = Field(default=50, ge=0, le=100)
    tone: str = Field(default="calm")
    contradiction_detected: bool = False
    hidden_emotion: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    # Gaze & head-pose telemetry (from video pipeline)
    eye_contact_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    head_pose: Optional[dict] = None  # {"pitch": float, "yaw": float, "roll": float}
    
    @field_validator('emotion', mode='before')
    @classmethod
    def validate_emotion_enum(cls, v):
        if isinstance(v, str):
            val = v.lower().strip()
            # Map common off-enum variations
            if val in ("conflicted", "masking", "contradiction", "mixed"):
                return EmotionEnum.CONFUSED
            try:
                return EmotionEnum(val)
            except ValueError:
                # Return neutral as safe fallback for any other unknown emotion
                return EmotionEnum.NEUTRAL
        return v

    @field_validator('stress_level')
    @classmethod
    def validate_stress_level(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError('stress_level must be between 0 and 100')
        return v


class AudioFeatures(BaseModel):
    """Audio features extracted from voice analysis."""
    pitch_mean: float = 0.0
    jitter: float = 0.0
    loudness: float = 0.0
    volume_std_dev: float = 0.0
    pitch_std_dev: float = 0.0
    is_trembling: bool = False
    is_singing: bool = False
    is_crying: bool = False
    is_whispering: bool = False
    voice_description: str = "stable voice"
    audio_emotion_hint: str = ""
    source: str = "unknown"
    
    def has_emotional_indicators(self) -> bool:
        return any([
            self.is_trembling,
            self.is_crying,
            self.is_whispering,
            self.jitter > 0.01,
        ])


class Transcript(BaseModel):
    """Transcript value object with validation."""
    text: str
    language: Optional[str] = "en"
    confidence: Optional[float] = None
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('transcript cannot be empty')
        return v.strip()
    
    def is_empty(self) -> bool:
        return not self.text or not self.text.strip()


class AudioURL(BaseModel):
    """Audio URL value object."""
    url: str
    bucket: Optional[str] = None
    path: Optional[str] = None
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v:
            raise ValueError('URL cannot be empty')
        return v