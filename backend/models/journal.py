"""
Pydantic models for the NeuroNest Reflective Journal API.

Defines request/response schemas and shared enums used by the journal
endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MoodType(str, Enum):
    """Valid mood labels a user may attach to a journal entry."""

    calm = "calm"
    stressed = "stressed"
    tired = "tired"
    happy = "happy"
    anxious = "anxious"
    overwhelmed = "overwhelmed"


class CreateEntryRequest(BaseModel):
    """Payload accepted by POST /journal/create."""

    title: Optional[str] = Field(default=None, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    mood: Optional[MoodType] = None


class JournalEntryResponse(BaseModel):
    """Full journal entry returned to the frontend (plaintext fields)."""

    id: str
    user_id: str
    title: Optional[str]
    content: str
    mood: Optional[MoodType]
    created_at: datetime


class JournalEntryPreview(BaseModel):
    """Lightweight entry preview used in timeline / list views."""

    id: str
    title: Optional[str]
    content_snippet: str
    mood: Optional[MoodType]
    created_at: datetime


class GenerateSummaryRequest(BaseModel):
    """Payload accepted by POST /journal/generate-summary."""

    range_type: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class EmotionalSummaryResponse(BaseModel):
    """AI-generated emotional summary returned to the frontend (plaintext fields)."""

    id: str
    user_id: str
    selected_range: Dict
    generated_summary: str
    emotional_patterns: List[str]
    positive_observations: List[str]
    gentle_insights: List[str]
    created_at: datetime
