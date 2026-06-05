"""Domain entities with behavior and invariants."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from uuid import uuid4
from domain.value_objects import (
    Emotion, 
    AudioFeatures, 
    Goal, 
    Project, 
    InteractionStyle, 
    EngagementMetrics, 
    EmotionEnum,
    MemoryType,
    MemoryImportance,
    MemoryLifecycle,
    ReflectionType,
    ReflectionScore,
    Task,
    EntityMention,
    Decision
)


class WorkingMemory(BaseModel):
    """
    Highly volatile, short-term memory (10-20 turns).
    Tracks active context, problems, and recent decisions.
    """
    user_id: str
    session_id: str
    turn_count: int = 0
    active_project: Optional[str] = None
    active_problem: Optional[str] = None
    active_topic: Optional[str] = None
    current_goal: Optional[str] = None
    recent_tasks: List[Task] = Field(default_factory=list)
    recent_entities: List[EntityMention] = Field(default_factory=list)
    recent_decisions: List[Decision] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, user_id: str, session_id: str) -> "WorkingMemory":
        return cls(user_id=user_id, session_id=session_id)

class Reflection(BaseModel):
    """Reflective insight entity derived from conversation analysis."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    type: ReflectionType
    content: str
    score: ReflectionScore = Field(default_factory=ReflectionScore)
    source_interaction_ids: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls, 
        user_id: str, 
        type: ReflectionType, 
        content: str, 
        interaction_id: str,
        confidence: float = 0.5
    ) -> "Reflection":
        return cls(
            user_id=user_id,
            type=type,
            content=content,
            score=ReflectionScore(confidence=confidence),
            source_interaction_ids=[interaction_id]
        )

    def merge_with(self, other: "Reflection"):
        """Merge a similar reflection, updating evidence and confidence."""
        if other.interaction_id not in self.source_interaction_ids:
            self.source_interaction_ids.extend(other.source_interaction_ids)
            self.score.evidence_count += 1
            # Increase confidence with more evidence (diminishing returns)
            self.score.confidence = min(0.99, self.score.confidence + (1 - self.score.confidence) * 0.2)
            self.score.last_validated = datetime.now(timezone.utc)

class Memory(BaseModel):
    """Unified Memory Entity for all layers (Episodic, Goal, etc.)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    type: MemoryType
    content: str
    importance: MemoryImportance = MemoryImportance.MEDIUM
    metadata: dict = Field(default_factory=dict)
    lifecycle: MemoryLifecycle = Field(default_factory=MemoryLifecycle)
    embedding: Optional[List[float]] = None

    @classmethod
    def create(
        cls, 
        user_id: str, 
        type: MemoryType, 
        content: str, 
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        metadata: Optional[dict] = None
    ) -> "Memory":
        return cls(
            user_id=user_id,
            type=type,
            content=content,
            importance=importance,
            metadata=metadata or {}
        )

    def access(self):
        """Update access metadata for retention logic."""
        self.lifecycle.last_accessed = datetime.now(timezone.utc)
        self.lifecycle.access_count += 1

class UserState(BaseModel):
    """Persistent user state entity."""
    user_id: str
    current_emotion: EmotionEnum = EmotionEnum.NEUTRAL
    dominant_emotion: EmotionEnum = EmotionEnum.NEUTRAL
    stress_level: int = Field(default=50, ge=0, le=100)
    confidence_level: int = Field(default=50, ge=0, le=100)
    engagement_level: int = Field(default=50, ge=0, le=100)
    current_goals: List[Goal] = Field(default_factory=list)
    preferred_interaction_style: InteractionStyle = InteractionStyle.CASUAL
    preferred_persona: str = "the_empathetic_friend"
    active_projects: List[Project] = Field(default_factory=list)
    recent_topics: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, user_id: str) -> "UserState":
        return cls(user_id=user_id)


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
    feedback_score: Optional[float] = None   # RL Reward: -1 to +1
    feedback_text: Optional[str] = None
    # RL fields — full action vector stored for offline analysis
    applied_persona: Optional[str] = None    # Which RL-selected persona was used
    applied_action:  Optional[dict] = None   # Full 5-dim ActionVector as dict
    applied_policy:  Optional[str] = None    # Which policy made the selection
    # Emotion before this turn (for sentiment-delta reward signal)
    emotion_before:  Optional[str] = None


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
        applied_action:  Optional[dict] = None,
        applied_policy:  Optional[str] = None,
        emotion_before:  Optional[str] = None,
    ) -> "Interaction":
        return cls(
            session_id=session_id,
            user_id=user_id,
            transcript=transcript,
            features=features,
            emotion_data=emotion_data,
            applied_persona=applied_persona,
            applied_action=applied_action,
            applied_policy=applied_policy,
            emotion_before=emotion_before,
        )
    
    def with_response(self, response_text: str, tts_url: Optional[str] = None) -> "Interaction":
        self.response_text = response_text
        self.tts_audio_url = tts_url
        return self