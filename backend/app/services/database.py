"""Supabase encrypted storage — direct HTTP REST API (no supabase package needed)."""
import logging, httpx
from typing import Optional, List
from app.config import get_settings
from app.services.encryption import encrypt, decrypt, is_encrypted
from app.models.schemas import ChatMessage, ChatResponse

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_headers() -> dict:
    return {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _is_configured() -> bool:
    return (
        bool(settings.supabase_url)
        and "your_supabase" not in settings.supabase_url
        and bool(settings.supabase_service_key)
        and "your_supabase" not in settings.supabase_service_key
    )


def _rest_url(table: str) -> str:
    return f"{settings.supabase_url.rstrip('/')}/rest/v1/{table}"


async def save_chat_message(
    session_id: str,
    user_id: str,
    role: str,
    content: str,
    emotion: Optional[str] = None,
    mood_level: Optional[str] = None,
    response_mode: Optional[str] = None,
) -> Optional[str]:
    if not _is_configured():
        return None
    try:
        # Do NOT send created_at — let Supabase use DEFAULT NOW() (correct UTC time)
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content_encrypted": encrypt(content, user_id),
            "emotion": emotion,
            "mood_level": mood_level,
            "response_mode": response_mode,
            # created_at intentionally omitted — Supabase DEFAULT NOW() handles it
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(_rest_url("chat_messages"), headers=_get_headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data[0].get("id") if data else None
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        return None


async def save_session(session_id: str, user_id: str) -> bool:
    if not _is_configured():
        return False
    try:
        # Do NOT send updated_at — let Supabase DEFAULT NOW() handle it
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            # updated_at intentionally omitted — Supabase DEFAULT NOW() handles it
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                _rest_url("chat_sessions"),
                headers={**_get_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
                json=payload,
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Failed to save session: {e}")
        return False


async def get_session_history(session_id: str, user_id: str, limit: int = 20) -> List[ChatMessage]:
    if not _is_configured():
        return []
    try:
        params = {"session_id": f"eq.{session_id}", "user_id": f"eq.{user_id}", "order": "created_at.asc", "limit": str(limit), "select": "role,content_encrypted,created_at"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_rest_url("chat_messages"), headers=_get_headers(), params=params)
            resp.raise_for_status()
            rows = resp.json()
        messages = []
        for row in rows:
            try:
                messages.append(ChatMessage(role=row["role"], content=decrypt(row["content_encrypted"], user_id)))
            except ValueError as e:
                logger.error(f"Decryption failed: {e}")
        return messages
    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}")
        return []


async def save_full_chat_turn(session_id: str, user_id: str, user_message: str, response: ChatResponse) -> bool:
    if not user_id:
        return False
    await save_session(session_id, user_id)
    u = await save_chat_message(session_id, user_id, "user", user_message, response.detected_emotion.value, response.mood_level.value)
    a = await save_chat_message(session_id, user_id, "assistant", response.response, response.detected_emotion.value, response.mood_level.value, response.response_mode)
    return bool(u and a)


async def verify_encryption_in_db(session_id: str, user_id: str, limit: int = 5) -> dict:
    if not _is_configured():
        return {"error": "Supabase not configured — add SUPABASE_URL and SUPABASE_SERVICE_KEY to .env"}
    try:
        params = {"session_id": f"eq.{session_id}", "user_id": f"eq.{user_id}", "order": "created_at.asc", "limit": str(limit), "select": "id,role,content_encrypted,emotion,created_at"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_rest_url("chat_messages"), headers=_get_headers(), params=params)
            resp.raise_for_status()
            rows = resp.json()
        if not rows:
            return {"message": "No messages found. Send a chat message with this session_id and user_id first.", "session_id": session_id, "user_id": user_id}
        report = []
        for row in rows:
            raw = row["content_encrypted"]
            try:
                decrypted = decrypt(raw, user_id)
                decrypt_status = "✅ Decrypted successfully"
                preview = decrypted[:100] + "..." if len(decrypted) > 100 else decrypted
            except ValueError:
                decrypt_status = "❌ Decryption failed"
                preview = None
            report.append({"row_id": row["id"], "role": row["role"], "emotion": row["emotion"], "stored_in_db_raw": raw[:80] + "...", "looks_encrypted": is_encrypted(raw), "decrypt_status": decrypt_status, "decrypted_preview": preview, "created_at": row["created_at"]})
        return {"session_id": session_id, "total_messages": len(rows), "encryption_algorithm": "AES-256-GCM", "key_derivation": "HKDF-SHA256 per user", "all_encrypted": all(r["looks_encrypted"] for r in report), "messages": report}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": "Table not found. Run supabase_setup.sql in Supabase SQL Editor first."}
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}
