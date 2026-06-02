from pydantic import BaseModel, Field
from typing import Optional, List

class AudioFeatures(BaseModel):
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

class EmotionData(BaseModel):
    emotion: str = "neutral"
    stress_level: int = Field(0, ge=0, le=100)
    tone: str = "calm"
    contradiction_detected: bool = False
    hidden_emotion: str = ""

class InteractionBase(BaseModel):
    session_id: str
    user_id: str
    transcript: str
    raw_audio_url: Optional[str] = None
    
    # Audio Features
    features: Optional[AudioFeatures] = None
    
    # Emotional Analysis
    emotion_data: Optional[EmotionData] = None
    
    # AI Response
    response_text: Optional[str] = None
    tts_audio_url: Optional[str] = None

class InteractionCreate(InteractionBase):
    pass

class Interaction(InteractionBase):
    id: str
    created_at: str
