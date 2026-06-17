"""
Reflection API request/response schemas.

Defines Pydantic schemas for validating incoming requests
and serializing outgoing responses for reflection endpoints.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.reflection import RangeType


class ReflectionGenerateRequest(BaseModel):
    """Schema for requesting a new AI-generated reflection.

    Attributes:
        range_type: The date range type to analyse.
        start_date: Custom range start (required when range_type is 'custom').
        end_date: Custom range end (required when range_type is 'custom').
    """

    range_type: RangeType
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ReflectionResponse(BaseModel):
    """Schema for a single reflection / emotional summary response.

    Attributes:
        id: The summary's unique identifier.
        summary: The AI-generated overall summary.
        emotional_patterns: Detected emotional patterns.
        positive_observations: Positive observations noted.
        gentle_insights: Gentle insights for the user.
        growth_suggestions: Growth suggestions.
        selected_range: The date range type used.
        created_at: Creation timestamp.
    """

    id: str
    summary: str
    emotional_patterns: List[str]
    positive_observations: List[str]
    gentle_insights: List[str]
    growth_suggestions: List[str]
    selected_range: str
    created_at: datetime


class ReflectionListResponse(BaseModel):
    """Schema for a list of reflections.

    Attributes:
        reflections: The list of reflection responses.
        total: Total number of reflections.
    """

    reflections: List[ReflectionResponse]
    total: int
