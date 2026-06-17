"""
Encryption service for journal entries and emotional summaries.

Wraps the core EncryptionService to provide high-level helpers
for encrypting and decrypting specific document fields.
"""

import json
from typing import Any, Dict

from app.core.config import get_settings
from app.core.security import EncryptionService

# Singleton encryption service instance
_encryption_service: EncryptionService | None = None


def _get_encryption_service() -> EncryptionService:
    """Return the singleton EncryptionService, creating it on first call.

    Returns:
        The EncryptionService instance.
    """
    global _encryption_service
    if _encryption_service is None:
        settings = get_settings()
        _encryption_service = EncryptionService(settings.ENCRYPTION_MASTER_KEY)
    return _encryption_service


def encrypt_journal_entry(entry_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt sensitive fields of a journal entry document.

    Encrypts the 'title', 'content', and 'mood' fields in-place.

    Args:
        entry_dict: A dictionary representing the journal entry.

    Returns:
        The same dictionary with encrypted field values.
    """
    svc = _get_encryption_service()
    for field in ("title", "content", "mood"):
        if field in entry_dict and entry_dict[field] is not None:
            entry_dict[field] = svc.encrypt(str(entry_dict[field]))
    return entry_dict


def decrypt_journal_entry(entry_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt sensitive fields of a journal entry document.

    Decrypts the 'title', 'content', and 'mood' fields in-place.

    Args:
        entry_dict: A dictionary representing the journal entry with encrypted fields.

    Returns:
        The same dictionary with decrypted field values.
    """
    svc = _get_encryption_service()
    for field in ("title", "content", "mood"):
        if field in entry_dict and entry_dict[field] is not None:
            try:
                entry_dict[field] = svc.decrypt(entry_dict[field])
            except Exception:
                # If decryption fails, keep the original value
                pass
    return entry_dict


def encrypt_summary(summary_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt sensitive fields of an emotional summary document.

    Encrypts 'generated_summary' as a string, and JSON-serializes then encrypts
    list fields: 'emotional_patterns', 'positive_observations',
    'gentle_insights', 'growth_suggestions'.

    Args:
        summary_dict: A dictionary representing the emotional summary.

    Returns:
        The same dictionary with encrypted field values.
    """
    svc = _get_encryption_service()

    if "generated_summary" in summary_dict and summary_dict["generated_summary"] is not None:
        summary_dict["generated_summary"] = svc.encrypt(summary_dict["generated_summary"])

    list_fields = (
        "emotional_patterns",
        "positive_observations",
        "gentle_insights",
        "growth_suggestions",
    )
    for field in list_fields:
        if field in summary_dict and summary_dict[field] is not None:
            serialized = json.dumps(summary_dict[field])
            summary_dict[field] = svc.encrypt(serialized)

    return summary_dict


def decrypt_summary(summary_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt sensitive fields of an emotional summary document.

    Decrypts 'generated_summary' as a string, and decrypts then JSON-deserializes
    list fields: 'emotional_patterns', 'positive_observations',
    'gentle_insights', 'growth_suggestions'.

    Args:
        summary_dict: A dictionary representing the emotional summary with encrypted fields.

    Returns:
        The same dictionary with decrypted field values.
    """
    svc = _get_encryption_service()

    if "generated_summary" in summary_dict and summary_dict["generated_summary"] is not None:
        try:
            summary_dict["generated_summary"] = svc.decrypt(summary_dict["generated_summary"])
        except Exception:
            pass

    list_fields = (
        "emotional_patterns",
        "positive_observations",
        "gentle_insights",
        "growth_suggestions",
    )
    for field in list_fields:
        if field in summary_dict and summary_dict[field] is not None:
            try:
                decrypted = svc.decrypt(summary_dict[field])
                summary_dict[field] = json.loads(decrypted)
            except Exception:
                # If decryption or JSON parsing fails, keep the original value
                pass

    return summary_dict
