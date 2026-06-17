"""
Journal entry data models.

Defines the Mood enumeration and the Pydantic model
representing a journal entry document in MongoDB.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Mood(str, Enum):
    """Enumeration of supported mood types for journal entries."""

    HAPPY = "Happy"
    CALM = "Calm"
    EXCITED = "Excited"
    MOTIVATED = "Motivated"
    TIRED = "Tired"
    SAD = "Sad"
    ANXIOUS = "Anxious"
    STRESSED = "Stressed"
    OVERWHELMED = "Overwhelmed"


class JournalEntryModel(BaseModel):
    """Represents a journal entry document stored in MongoDB.

    Attributes:
        id: The string representation of the MongoDB ObjectId.
        user_id: The ID of the user who owns this entry.
        title: The title of the journal entry.
        content: The body content of the journal entry.
        mood: The mood associated with this entry.
        created_at: Timestamp when the entry was created.
        updated_at: Timestamp when the entry was last updated.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    title: str
    content: str
    mood: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
