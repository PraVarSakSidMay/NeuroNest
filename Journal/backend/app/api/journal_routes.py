"""
Journal API routes.

Provides CRUD endpoints for managing journal entries:
create, list (with search/filter/pagination), get by ID, update, and delete.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from app.models.journal import Mood
from app.schemas.journal import (
    JournalCreateRequest,
    JournalListResponse,
    JournalResponse,
    JournalUpdateRequest,
)
from app.services import journal_service
from app.core.security import get_current_user

router = APIRouter(prefix="/api/journal", tags=["Journal"])


@router.post("/", response_model=dict, status_code=201)
async def create_entry(
    data: JournalCreateRequest, 
    current_user_id: str = Depends(get_current_user)
) -> dict:
    """Create a new journal entry.

    Args:
        data: The journal entry creation payload.
        current_user_id: The ID of the authenticated user.

    Returns:
        A dict with the new entry's id and created_at timestamp.
    """
    try:
        result = await journal_service.create_entry(data, current_user_id)
        return {
            "id": result["id"],
            "created_at": result["created_at"].isoformat(),
            "message": "Journal entry created successfully.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/", response_model=JournalListResponse)
async def list_entries(
    search: Optional[str] = Query(default=None, description="Search text in title/content"),
    mood: Optional[Mood] = Query(default=None, description="Filter by mood"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Entries per page"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user_id: str = Depends(get_current_user),
) -> JournalListResponse:
    """List journal entries with optional search, mood filter, and pagination.

    Args:
        search: Optional text to search in title or content.
        mood: Optional mood to filter by.
        page: Page number (1-indexed).
        page_size: Number of entries per page (1-100).
        sort_order: 'asc' or 'desc' by created_at.
        current_user_id: The ID of the authenticated user.

    Returns:
        Paginated list of journal entries.
    """
    try:
        mood_value = mood.value if mood else None
        entries, total = await journal_service.get_entries(
            current_user_id,
            search=search,
            mood=mood_value,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )

        journal_responses = [
            JournalResponse(
                id=e["id"],
                title=e.get("title", ""),
                content=e.get("content", ""),
                mood=e.get("mood", ""),
                created_at=e["created_at"],
                updated_at=e["updated_at"],
            )
            for e in entries
        ]

        return JournalListResponse(
            entries=journal_responses,
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{entry_id}", response_model=JournalResponse)
async def get_entry(
    entry_id: str, 
    current_user_id: str = Depends(get_current_user)
) -> JournalResponse:
    """Retrieve a single journal entry by its ID.

    Args:
        entry_id: The MongoDB ObjectId string of the entry.
        current_user_id: The ID of the authenticated user.

    Returns:
        The journal entry.

    Raises:
        HTTPException: 404 if the entry is not found.
    """
    entry = await journal_service.get_entry_by_id(entry_id, current_user_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found.")

    return JournalResponse(
        id=entry["id"],
        title=entry.get("title", ""),
        content=entry.get("content", ""),
        mood=entry.get("mood", ""),
        created_at=entry["created_at"],
        updated_at=entry["updated_at"],
    )


@router.put("/{entry_id}", response_model=JournalResponse)
async def update_entry(
    entry_id: str, 
    data: JournalUpdateRequest, 
    current_user_id: str = Depends(get_current_user)
) -> JournalResponse:
    """Update an existing journal entry.

    Args:
        entry_id: The MongoDB ObjectId string of the entry.
        data: The fields to update.
        current_user_id: The ID of the authenticated user.

    Returns:
        The updated journal entry.

    Raises:
        HTTPException: 404 if the entry is not found.
    """
    updated = await journal_service.update_entry(entry_id, data, current_user_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Journal entry not found.")

    return JournalResponse(
        id=updated["id"],
        title=updated.get("title", ""),
        content=updated.get("content", ""),
        mood=updated.get("mood", ""),
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )


@router.delete("/{entry_id}", status_code=200)
async def delete_entry(
    entry_id: str, 
    current_user_id: str = Depends(get_current_user)
) -> dict:
    """Delete a journal entry by its ID.

    Args:
        entry_id: The MongoDB ObjectId string of the entry.
        current_user_id: The ID of the authenticated user.

    Returns:
        A confirmation message.

    Raises:
        HTTPException: 404 if the entry is not found.
    """
    deleted = await journal_service.delete_entry(entry_id, current_user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Journal entry not found.")
    return {"message": "Journal entry deleted successfully."}
