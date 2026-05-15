"""
Journal entry endpoints for the NeuroNest Reflective Journal API.

Endpoints
---------
POST /journal/create            — create a new encrypted journal entry (201)
GET  /journal/history           — fetch all entries for the authenticated user (200)
POST /journal/generate-summary  — generate an AI emotional summary for a date range (200)
GET  /journal/summaries         — fetch all past AI summaries for the authenticated user (200)
"""

import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from database import supabase
from dependencies.auth import User, get_current_user
from models.journal import (
    CreateEntryRequest,
    EmotionalSummaryResponse,
    GenerateSummaryRequest,
    JournalEntryResponse,
    MoodType,
)
from services.ai_orchestrator import generate_emotional_summary
from services.encryption import decrypt_field, encrypt_field
from services.range import resolve_reflection_range

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /journal/create
# ---------------------------------------------------------------------------


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model=JournalEntryResponse,
)
def create_entry(
    payload: CreateEntryRequest,
    current_user: User = Depends(get_current_user),
) -> JournalEntryResponse:
    """Create a new journal entry for the authenticated user.

    Plaintext validation is performed by Pydantic before this handler runs.
    Sensitive fields are encrypted with AES-256-GCM before being written to
    the database.  The response contains the original plaintext values.

    Returns:
        201 with the created entry (plaintext fields + server-generated id /
        created_at).

    Raises:
        400: Pydantic validation failure (handled automatically by FastAPI).
        401: Missing or invalid JWT (raised by get_current_user).
        500: Unexpected database error.
    """
    user_id = current_user.id

    # ── Encrypt sensitive fields before persisting ────────────────────────
    encrypted_row = {
        "user_id": user_id,
        "content": encrypt_field(payload.content, user_id),
        "title": encrypt_field(payload.title, user_id) if payload.title else None,
        "mood": encrypt_field(payload.mood.value, user_id) if payload.mood else None,
    }

    # ── Insert into Supabase ──────────────────────────────────────────────
    result = supabase.table("journal_entries").insert(encrypted_row).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create journal entry.",
        )

    row = result.data[0]

    # ── Return plaintext representation ───────────────────────────────────
    return JournalEntryResponse(
        id=row["id"],
        user_id=row["user_id"],
        title=payload.title,
        content=payload.content,
        mood=payload.mood,
        created_at=_parse_timestamp(row["created_at"]),
    )


# ---------------------------------------------------------------------------
# GET /journal/history
# ---------------------------------------------------------------------------


@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    response_model=List[JournalEntryResponse],
)
def get_history(
    current_user: User = Depends(get_current_user),
) -> List[JournalEntryResponse]:
    """Return all journal entries for the authenticated user.

    Entries are ordered by ``created_at`` descending (newest first).
    Encrypted fields are decrypted before being returned.

    Returns:
        200 with a list of entries (may be empty).

    Raises:
        401: Missing or invalid JWT (raised by get_current_user).
    """
    user_id = current_user.id

    result = (
        supabase.table("journal_entries")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    entries: List[JournalEntryResponse] = []
    for row in result.data or []:
        title = decrypt_field(row["title"], user_id) if row.get("title") else None
        content = decrypt_field(row["content"], user_id)
        mood_raw = decrypt_field(row["mood"], user_id) if row.get("mood") else None
        mood = MoodType(mood_raw) if mood_raw else None

        entries.append(
            JournalEntryResponse(
                id=row["id"],
                user_id=row["user_id"],
                title=title,
                content=content,
                mood=mood,
                created_at=_parse_timestamp(row["created_at"]),
            )
        )

    return entries


# ---------------------------------------------------------------------------
# POST /journal/generate-summary
# ---------------------------------------------------------------------------


@router.post(
    "/generate-summary",
    status_code=status.HTTP_200_OK,
    response_model=EmotionalSummaryResponse,
)
def generate_summary(
    payload: GenerateSummaryRequest,
    current_user: User = Depends(get_current_user),
) -> EmotionalSummaryResponse:
    """Generate an AI emotional summary for the authenticated user's entries
    within the requested date range.

    Returns:
        200 with the plaintext EmotionalSummaryResponse.

    Raises:
        400: Invalid or incomplete range parameters.
        401: Missing or invalid JWT (raised by get_current_user).
        404: No journal entries found for the selected range.
        503: Groq API unavailable or response parsing failed.
    """
    user_id = current_user.id

    # ── 1. Resolve the reflection range ───────────────────────────────────
    try:
        range_info = resolve_reflection_range(
            preset=payload.range_type,  # type: ignore[arg-type]
            custom_start=payload.start_date,
            custom_end=payload.end_date,
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    start_date = range_info["start_date"]
    end_date = range_info["end_date"]

    # ── 2. Fetch encrypted entries for the range ──────────────────────────
    result = (
        supabase.table("journal_entries")
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", start_date.isoformat())
        .lte("created_at", end_date.isoformat())
        .order("created_at", desc=False)
        .execute()
    )

    rows = result.data or []

    # ── 3. Return 404 if no entries found ─────────────────────────────────
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entries found for selected range.",
        )

    # ── 4. Decrypt sensitive fields ───────────────────────────────────────
    decrypted_entries: list[dict] = []
    for row in rows:
        decrypted_entries.append(
            {
                **row,
                "title": decrypt_field(row["title"], user_id) if row.get("title") else None,
                "content": decrypt_field(row["content"], user_id),
                "mood": decrypt_field(row["mood"], user_id) if row.get("mood") else None,
            }
        )

    # ── 5. Generate AI summary ────────────────────────────────────────────
    try:
        summary = generate_emotional_summary(user_id, decrypted_entries, range_info)
    except Exception as exc:
        # Log the actual error for debugging
        import traceback
        print(f"ERROR generating summary: {exc}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI summary generation failed: {str(exc)}",
        ) from exc

    # ── 6. Encrypt sensitive summary fields before persisting ─────────────
    selected_range_plain = {
        "preset": range_info["preset"],
        "start_date": range_info["start_date"].isoformat(),
        "end_date": range_info["end_date"].isoformat(),
    }

    encrypted_row = {
        "user_id": user_id,
        "selected_range": selected_range_plain,
        "generated_summary": encrypt_field(summary["summary_text"], user_id),
        "emotional_patterns": encrypt_field(
            json.dumps(summary["emotional_patterns"]), user_id
        ),
        "positive_observations": encrypt_field(
            json.dumps(summary["positive_observations"]), user_id
        ),
        "gentle_insights": encrypt_field(
            json.dumps(summary["gentle_insights"]), user_id
        ),
    }

    insert_result = supabase.table("emotional_summaries").insert(encrypted_row).execute()

    if not insert_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist emotional summary.",
        )

    saved_row = insert_result.data[0]

    # ── 7. Return plaintext response ──────────────────────────────────────
    return EmotionalSummaryResponse(
        id=saved_row["id"],
        user_id=saved_row["user_id"],
        selected_range=selected_range_plain,
        generated_summary=summary["summary_text"],
        emotional_patterns=summary["emotional_patterns"],
        positive_observations=summary["positive_observations"],
        gentle_insights=summary["gentle_insights"],
        created_at=_parse_timestamp(saved_row["created_at"]),
    )


# ---------------------------------------------------------------------------
# GET /journal/summaries
# ---------------------------------------------------------------------------


@router.get(
    "/summaries",
    status_code=status.HTTP_200_OK,
    response_model=List[EmotionalSummaryResponse],
)
def get_summaries(
    current_user: User = Depends(get_current_user),
) -> List[EmotionalSummaryResponse]:
    """Return all AI-generated emotional summaries for the authenticated user.

    Summaries are ordered by ``created_at`` descending (newest first).
    Encrypted fields are decrypted and JSON arrays are deserialized before
    being returned.

    Returns:
        200 with a list of summaries (may be empty).

    Raises:
        401: Missing or invalid JWT (raised by get_current_user).
    """
    user_id = current_user.id

    result = (
        supabase.table("emotional_summaries")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    summaries: List[EmotionalSummaryResponse] = []
    for row in result.data or []:
        generated_summary = decrypt_field(row["generated_summary"], user_id)
        emotional_patterns: list[str] = json.loads(
            decrypt_field(row["emotional_patterns"], user_id)
        )
        positive_observations: list[str] = json.loads(
            decrypt_field(row["positive_observations"], user_id)
        )
        gentle_insights: list[str] = json.loads(
            decrypt_field(row["gentle_insights"], user_id)
        )

        summaries.append(
            EmotionalSummaryResponse(
                id=row["id"],
                user_id=row["user_id"],
                selected_range=row["selected_range"],
                generated_summary=generated_summary,
                emotional_patterns=emotional_patterns,
                positive_observations=positive_observations,
                gentle_insights=gentle_insights,
                created_at=_parse_timestamp(row["created_at"]),
            )
        )

    return summaries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_timestamp(value: str | datetime) -> datetime:
    """Normalise a Supabase timestamp to a :class:`datetime` object."""
    if isinstance(value, datetime):
        return value
    # Supabase returns ISO-8601 strings; strip trailing 'Z' for fromisoformat
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# DELETE /journal/entry/{entry_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/entry/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a journal entry.

    Returns:
        204 No Content on success.

    Raises:
        401: Missing or invalid JWT (raised by get_current_user).
        404: Entry not found or doesn't belong to user.
    """
    user_id = current_user.id

    # Delete the entry (only if it belongs to the user)
    result = (
        supabase.table("journal_entries")
        .delete()
        .eq("id", entry_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found or access denied.",
        )

    return None


# ---------------------------------------------------------------------------
# DELETE /journal/summary/{summary_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/summary/{summary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_summary(
    summary_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete an emotional summary.

    Returns:
        204 No Content on success.

    Raises:
        401: Missing or invalid JWT (raised by get_current_user).
        404: Summary not found or doesn't belong to user.
    """
    user_id = current_user.id

    # Delete the summary (only if it belongs to the user)
    result = (
        supabase.table("emotional_summaries")
        .delete()
        .eq("id", summary_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found or access denied.",
        )

    return None
