"""
Journal API request/response schemas.

Defines Pydantic schemas for validating incoming requests
and serializing outgoing responses for journal endpoints.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.journal import Mood


class JournalCreateRequest(BaseModel):
    """Schema for creating a new journal entry.

    Attributes:
        title: The title of the journal entry (1-200 characters).
        content: The body content (1-10000 characters).
        mood: The mood to associate with the entry.
    """

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    mood: Mood


class JournalUpdateRequest(BaseModel):
    """Schema for updating an existing journal entry.

    All fields are optional; only provided fields are updated.

    Attributes:
        title: Updated title (1-200 characters).
        content: Updated body content (1-10000 characters).
        mood: Updated mood value.
    """

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    mood: Optional[Mood] = None


class JournalResponse(BaseModel):
    """Schema for a single journal entry response.

    Attributes:
        id: The entry's unique identifier.
        title: The entry title.
        content: The entry body content.
        mood: The mood string.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str
    title: str
    content: str
    mood: str
    created_at: datetime
    updated_at: datetime


class JournalListResponse(BaseModel):
    """Schema for a paginated list of journal entries.

    Attributes:
        entries: The list of journal entry responses.
        total: Total number of matching entries.
        page: Current page number.
        page_size: Number of entries per page.
    """

    entries: List[JournalResponse]
    total: int
    page: int
    page_size: int
