"""Domain value objects with invariants and validation."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum
from uuid import uuid4
from datetime import datetime, timezone


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

class Goal(BaseModel):
    """Represents a user goal or objective."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    progress: int = Field(default=0, ge=0, le=100)
    is_completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Project(BaseModel):
    """Represents an active project the user is working on."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InteractionStyle(str, Enum):
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    DIRECT = "direct"
    EMPATHETIC = "empathetic"
    SUPPORTIVE = "supportive"
    HUMOROUS = "humorous"

class MemoryType(str, Enum):
    EPISODIC = "episodic"
    GOAL = "goal"
    PREFERENCE = "preference"
    EMOTIONAL = "emotional"
    REFLECTION = "reflection"

class MemoryImportance(int, Enum):
    LOW = 1
    MEDIUM = 3
    HIGH = 5
    CRITICAL = 10

class MemoryLifecycle(BaseModel):
    """Metadata for memory lifecycle management."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    decay_rate: float = 0.01  # Rate at which importance decreases
    is_consolidated: bool = False  # Has this been moved to long-term reflection?
    expires_at: Optional[datetime] = None

class ReflectionType(str, Enum):
    INSIGHT = "insight"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    PREFERENCE = "preference"
    GOAL_DETECTED = "goal_detected"
    EMOTIONAL_TRIGGER = "emotional_trigger"

class ReflectionScore(BaseModel):
    """Scoring system for reflections based on confidence and evidence strength."""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_count: int = 1
    relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    last_validated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Task(BaseModel):
    """Represents a specific task in working memory."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    status: str = "pending"
    turn_id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EntityMention(BaseModel):
    """Represents a named entity mentioned in conversation."""
    name: str
    type: str  # e.g., Person, Place, Tech, Concept
    last_mentioned_turn: int
    count: int = 1

class Decision(BaseModel):
    """Represents a choice or decision made during a project/problem."""
    content: str
    rationale: Optional[str] = None
    turn_id: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConversationStrategy(str, Enum):
    COACHING = "coaching"
    TEACHING = "teaching"
    EMOTIONAL_SUPPORT = "emotional_support"
    DEBUGGING = "debugging"
    BRAINSTORMING = "brainstorming"
    MOTIVATION = "motivation"
    CASUAL = "casual"

class ConversationPlan(BaseModel):
    """The strategic plan for the upcoming AI response."""
    intent: str
    emotional_need: str
    conversation_strategy: ConversationStrategy
    response_goal: str
    risk_level: int = Field(default=1, ge=1, le=5)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    planned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompiledContext(BaseModel):
    """The final token-efficient, deduplicated context for the LLM."""
    user_summary: str
    current_state: str
    relevant_memories: str
    active_goals: str
    emotional_state: str
    planner_strategy: str
    response_constraints: str
    total_estimated_tokens: int
    compiled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EngagementMetrics(BaseModel):
    """Fused metrics for user engagement and confidence."""
    confidence_level: int = Field(default=50, ge=0, le=100)
    engagement_level: int = Field(default=50, ge=0, le=100)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))