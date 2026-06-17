"""
Emotional reflection / summary data models.

Defines the RangeType enumeration and the Pydantic model
representing an emotional summary document in MongoDB.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RangeType(str, Enum):
    """Enumeration of supported date range types for reflections."""

    LAST_3_DAYS = "last_3_days"
    LAST_5_DAYS = "last_5_days"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    CUSTOM = "custom"


class EmotionalSummaryModel(BaseModel):
    """Represents an emotional summary document stored in MongoDB.

    Attributes:
        id: The string representation of the MongoDB ObjectId.
        user_id: The ID of the user who owns this summary.
        selected_range: The date range type used to generate the summary.
        generated_summary: AI-generated overall emotional summary.
        emotional_patterns: List of detected emotional patterns.
        positive_observations: List of positive observations noted.
        gentle_insights: List of gentle insights for the user.
        growth_suggestions: List of growth suggestions.
        created_at: Timestamp when the summary was created.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    selected_range: str
    generated_summary: str
    emotional_patterns: List[str] = Field(default_factory=list)
    positive_observations: List[str] = Field(default_factory=list)
    gentle_insights: List[str] = Field(default_factory=list)
    growth_suggestions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
