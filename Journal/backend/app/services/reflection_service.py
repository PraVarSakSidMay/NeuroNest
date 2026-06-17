"""
Reflection (emotional summary) service.

Orchestrates date range calculation, journal entry retrieval,
AI reflection generation, encryption, and storage.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId

from app.database.collections import get_journal_collection, get_summaries_collection
from app.schemas.reflection import ReflectionGenerateRequest
from app.services.ai_service import ai_reflection_service
from app.services.encryption_service import (
    decrypt_journal_entry,
    decrypt_summary,
    encrypt_summary,
)
from app.utils.helpers import calculate_date_range, format_entries_for_prompt, serialize_object_id


async def generate_reflection(
    data: ReflectionGenerateRequest, user_id: str
) -> Dict[str, Any]:
    """Generate an AI-powered emotional reflection.

    Fetches journal entries within the requested date range, formats them
    for the AI prompt, calls the AI service, encrypts the result, and
    stores it in MongoDB.

    Args:
        data: Validated reflection generation request.
        user_id: The ID of the user generating the reflection.

    Returns:
        A dict representing the stored and decrypted reflection.

    Raises:
        ValueError: If no journal entries exist in the requested date range.
    """
    start_date, end_date = calculate_date_range(
        data.range_type, data.start_date, data.end_date
    )

    # Fetch journal entries in range
    journal_col = get_journal_collection()
    cursor = journal_col.find(
        {
            "user_id": user_id,
            "created_at": {"$gte": start_date, "$lte": end_date},
        }
    ).sort("created_at", 1)

    entries_raw = await cursor.to_list(length=None)

    if not entries_raw:
        raise ValueError("No journal entries found in the selected date range.")

    # Decrypt entries for AI processing
    decrypted_entries: List[Dict[str, Any]] = []
    for entry in entries_raw:
        entry = serialize_object_id(entry)
        entry = decrypt_journal_entry(entry)
        decrypted_entries.append(entry)

    # Build prompt text and call AI
    entries_text = format_entries_for_prompt(decrypted_entries)
    ai_result = await ai_reflection_service.generate_reflection(entries_text)

    # Build summary document
    now = datetime.now(timezone.utc)
    summary_doc: Dict[str, Any] = {
        "user_id": user_id,
        "selected_range": data.range_type.value,
        "generated_summary": ai_result["summary"],
        "emotional_patterns": ai_result["emotional_patterns"],
        "positive_observations": ai_result["positive_observations"],
        "gentle_insights": ai_result["gentle_insights"],
        "growth_suggestions": ai_result["growth_suggestions"],
        "created_at": now,
    }

    # Encrypt and store
    encrypted_doc = encrypt_summary(summary_doc.copy())
    summaries_col = get_summaries_collection()
    result = await summaries_col.insert_one(encrypted_doc)

    # Return the unencrypted version with ID
    summary_doc["id"] = str(result.inserted_id)
    return summary_doc


async def get_reflections(
    user_id: str, page: int = 1, page_size: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    """Retrieve paginated emotional reflections for the current user.

    Args:
        user_id: The ID of the user whose reflections to retrieve.
        page: The page number (1-indexed).
        page_size: Number of reflections per page.

    Returns:
        A tuple of (list of decrypted reflection dicts, total count).
    """
    summaries_col = get_summaries_collection()
    query = {"user_id": user_id}

    total = await summaries_col.count_documents(query)

    skip = (page - 1) * page_size
    cursor = (
        summaries_col.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    docs = await cursor.to_list(length=page_size)

    reflections: List[Dict[str, Any]] = []
    for doc in docs:
        doc = serialize_object_id(doc)
        doc = decrypt_summary(doc)
        reflections.append(doc)

    return reflections, total


async def delete_reflection(reflection_id: str, user_id: str) -> bool:
    """Delete an emotional reflection by its ID.

    Args:
        reflection_id: The string representation of the MongoDB ObjectId.
        user_id: The ID of the user who owns the reflection.

    Returns:
        True if a reflection was deleted, False otherwise.
    """
    summaries_col = get_summaries_collection()
    try:
        result = await summaries_col.delete_one(
            {"_id": ObjectId(reflection_id), "user_id": user_id}
        )
    except Exception:
        return False
    return result.deleted_count > 0
