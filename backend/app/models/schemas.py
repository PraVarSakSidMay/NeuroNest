from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class MoodLevel(str, Enum):
    VERY_BAD = "very_bad"
    BAD = "bad"
    NEUTRAL = "neutral"
    GOOD = "good"
    VERY_GOOD = "very_good"


class EmotionType(str, Enum):
    STRESSED = "stressed"
    ANXIOUS = "anxious"
    SAD = "sad"
    ANGRY = "angry"
    HAPPY = "happy"
    CALM = "calm"
    OVERWHELMED = "overwhelmed"
    LONELY = "lonely"
    EXCITED = "excited"
    NEUTRAL = "neutral"


class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    INDIVIDUAL = "individual"


class ChatMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: Optional[List[ChatMessage]] = []


class ActivitySuggestion(BaseModel):
    title: str
    description: str
    duration: str
    category: str
    emoji: str


class MusicTrack(BaseModel):
    title: str
    artist: str
    spotify_url: str
    youtube_url: str
    reason: str


class ChatResponse(BaseModel):
    response: str
    detected_emotion: EmotionType
    mood_level: MoodLevel
    response_mode: str = "support"
    activities: List[ActivitySuggestion]
    celebration_message: Optional[str] = None
    special_action: Optional[str] = None
    special_content: Optional[str] = None
    music_tracks: Optional[List[MusicTrack]] = None
    joke: Optional[str] = None
    proverb: Optional[str] = None
    proverb_author: Optional[str] = None
    session_id: str
    wellness_tip: Optional[str] = None
    llm_provider: Optional[str] = None


class VoiceAnalysisResponse(BaseModel):
    transcribed_text: str
    detected_emotion: EmotionType
    mood_level: MoodLevel
    confidence: float
    chat_response: ChatResponse


class MoodCheckIn(BaseModel):
    user_id: str
    mood_level: MoodLevel
    emotions: List[EmotionType]
    note: Optional[str] = None


class MoodCheckInResponse(BaseModel):
    message: str
    activities: List[ActivitySuggestion]
    wellness_tip: str
