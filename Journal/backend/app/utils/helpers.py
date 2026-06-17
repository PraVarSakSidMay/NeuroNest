"""
Utility helper functions.

Provides date range calculation, ObjectId serialization,
and journal entry formatting for AI prompts.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.models.reflection import RangeType


def calculate_date_range(
    range_type: RangeType,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Tuple[datetime, datetime]:
    """Calculate the start and end datetimes for a given range type.

    For preset ranges, the end date is now (UTC) and the start date is
    calculated by subtracting the appropriate number of days.
    For custom ranges, the provided start_date and end_date are used.

    Args:
        range_type: The type of date range to calculate.
        start_date: Custom range start (used only when range_type is CUSTOM).
        end_date: Custom range end (used only when range_type is CUSTOM).

    Returns:
        A tuple of (start_datetime, end_datetime) in UTC.

    Raises:
        ValueError: If range_type is CUSTOM but dates are not provided.
    """
    now = datetime.now(timezone.utc)

    range_days = {
        RangeType.LAST_3_DAYS: 3,
        RangeType.LAST_5_DAYS: 5,
        RangeType.LAST_7_DAYS: 7,
        RangeType.LAST_30_DAYS: 30,
    }

    if range_type == RangeType.CUSTOM:
        if start_date is None or end_date is None:
            raise ValueError(
                "start_date and end_date are required for custom range."
            )
        # Ensure timezone awareness
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        return start_date, end_date

    days = range_days[range_type]
    start = now - timedelta(days=days)
    return start, now


def serialize_object_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB's _id ObjectId to a string 'id' field.

    Removes the '_id' key and adds an 'id' key with the string value.

    Args:
        doc: A MongoDB document dictionary.

    Returns:
        The modified dictionary with 'id' as a string.
    """
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc


def format_entries_for_prompt(entries: List[Dict[str, Any]]) -> str:
    """Format a list of decrypted journal entries into readable text for the AI prompt.

    Each entry is formatted with its date, mood, title, and content.

    Args:
        entries: A list of decrypted journal entry dictionaries.

    Returns:
        A formatted multi-line string ready for the AI prompt.
    """
    if not entries:
        return "No journal entries available."

    lines: List[str] = []
    for i, entry in enumerate(entries, start=1):
        created = entry.get("created_at", "Unknown date")
        if isinstance(created, datetime):
            created = created.strftime("%B %d, %Y at %I:%M %p")

        mood = entry.get("mood", "Unknown")
        title = entry.get("title", "Untitled")
        content = entry.get("content", "")

        lines.append(f"--- Entry {i} ---")
        lines.append(f"Date: {created}")
        lines.append(f"Mood: {mood}")
        lines.append(f"Title: {title}")
        lines.append(f"Content: {content}")
        lines.append("")

    return "\n".join(lines)
