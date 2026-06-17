"""
Journal entry CRUD service.

Handles creation, retrieval, update, and deletion of journal entries
with encryption and pagination support.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId

from app.database.collections import get_journal_collection
from app.models.journal import Mood
from app.schemas.journal import JournalCreateRequest, JournalUpdateRequest
from app.services.encryption_service import decrypt_journal_entry, encrypt_journal_entry
from app.utils.helpers import serialize_object_id


async def create_entry(data: JournalCreateRequest, user_id: str) -> Dict[str, Any]:
    """Create a new journal entry.

    Encrypts sensitive fields and inserts the document into MongoDB.

    Args:
        data: Validated journal creation request.
        user_id: The ID of the user creating the entry.

    Returns:
        A dict containing the new entry's 'id' and 'created_at'.
    """
    now = datetime.now(timezone.utc)
    entry_doc = {
        "user_id": user_id,
        "title": data.title,
        "content": data.content,
        "mood": data.mood.value,
        "created_at": now,
        "updated_at": now,
    }

    entry_doc = encrypt_journal_entry(entry_doc)

    collection = get_journal_collection()
    result = await collection.insert_one(entry_doc)

    return {
        "id": str(result.inserted_id),
        "created_at": now,
    }


async def get_entries(
    user_id: str,
    search: Optional[str] = None,
    mood: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    sort_order: str = "desc",
) -> Tuple[List[Dict[str, Any]], int]:
    """Retrieve paginated journal entries with optional filters.

    Because fields are encrypted, search and mood filtering happen
    after decryption in application memory.

    Args:
        user_id: The ID of the user whose entries to retrieve.
        search: Optional text to search for in title or content.
        mood: Optional mood value to filter by.
        page: The page number (1-indexed).
        page_size: Number of entries per page.
        sort_order: Sort direction for created_at ('asc' or 'desc').

    Returns:
        A tuple of (list of decrypted entry dicts, total matching count).
    """
    collection = get_journal_collection()
    query: Dict[str, Any] = {"user_id": user_id}

    sort_direction = -1 if sort_order == "desc" else 1

    # Fetch all entries for this user (required because encrypted fields
    # cannot be filtered at the database level)
    cursor = collection.find(query).sort("created_at", sort_direction)
    all_entries_raw = await cursor.to_list(length=None)

    # Decrypt all entries
    decrypted_entries: List[Dict[str, Any]] = []
    for entry in all_entries_raw:
        entry = serialize_object_id(entry)
        entry = decrypt_journal_entry(entry)
        decrypted_entries.append(entry)

    # Apply in-memory filters
    filtered_entries = decrypted_entries

    if mood:
        filtered_entries = [e for e in filtered_entries if e.get("mood") == mood]

    if search:
        search_lower = search.lower()
        filtered_entries = [
            e
            for e in filtered_entries
            if search_lower in (e.get("title", "")).lower()
            or search_lower in (e.get("content", "")).lower()
        ]

    total = len(filtered_entries)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered_entries[start:end]

    return paginated, total


async def get_entry_by_id(entry_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single journal entry by its ID.

    Args:
        entry_id: The string representation of the MongoDB ObjectId.
        user_id: The ID of the user who owns the entry.

    Returns:
        The decrypted entry dict, or None if not found.
    """
    collection = get_journal_collection()
    try:
        doc = await collection.find_one(
            {"_id": ObjectId(entry_id), "user_id": user_id}
        )
    except Exception:
        return None

    if doc is None:
        return None

    doc = serialize_object_id(doc)
    doc = decrypt_journal_entry(doc)
    return doc


async def update_entry(
    entry_id: str, data: JournalUpdateRequest, user_id: str
) -> Optional[Dict[str, Any]]:
    """Update an existing journal entry.

    Only fields provided in the request are updated. Updated fields are
    encrypted before being persisted.

    Args:
        entry_id: The string representation of the MongoDB ObjectId.
        data: Validated journal update request with optional fields.
        user_id: The ID of the user who owns the entry.

    Returns:
        The updated and decrypted entry dict, or None if not found.
    """
    collection = get_journal_collection()

    update_fields: Dict[str, Any] = {}
    if data.title is not None:
        update_fields["title"] = data.title
    if data.content is not None:
        update_fields["content"] = data.content
    if data.mood is not None:
        update_fields["mood"] = data.mood.value

    if not update_fields:
        return await get_entry_by_id(entry_id, user_id)

    update_fields["updated_at"] = datetime.now(timezone.utc)

    # Encrypt only the changed sensitive fields
    encrypted_fields = encrypt_journal_entry(
        {k: v for k, v in update_fields.items() if k in ("title", "content", "mood")}
    )
    update_fields.update(encrypted_fields)

    try:
        result = await collection.update_one(
            {"_id": ObjectId(entry_id), "user_id": user_id},
            {"$set": update_fields},
        )
    except Exception:
        return None

    if result.matched_count == 0:
        return None

    return await get_entry_by_id(entry_id, user_id)


async def delete_entry(entry_id: str, user_id: str) -> bool:
    """Delete a journal entry by its ID.

    Args:
        entry_id: The string representation of the MongoDB ObjectId.
        user_id: The ID of the user who owns the entry.

    Returns:
        True if an entry was deleted, False otherwise.
    """
    collection = get_journal_collection()
    try:
        result = await collection.delete_one(
            {"_id": ObjectId(entry_id), "user_id": user_id}
        )
    except Exception:
        return False
    return result.deleted_count > 0
