"""
Database Router — /api/db
Encryption verification and chat history endpoints.
Tests both that data IS stored in Supabase AND that it IS encrypted.
"""
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional, List
import httpx

from app.services.database import get_session_history, verify_encryption_in_db, save_full_chat_turn
from app.services.encryption import encrypt, decrypt, is_encrypted
from app.models.schemas import ChatMessage
from app.config import get_settings

router = APIRouter(prefix="/api/db", tags=["Database & Encryption"])
settings = get_settings()


# ── Request / Response models ─────────────────────────────────────────────────

class EncryptionTestRequest(BaseModel):
    text: str
    user_id: str


class EncryptionTestResponse(BaseModel):
    original_text: str
    encrypted_stored_in_db: str
    decrypted_back: str
    round_trip_success: bool
    algorithm: str
    what_supabase_sees: str
    what_user_sees: str


class SessionHistoryResponse(BaseModel):
    session_id: str
    user_id: str
    messages: List[ChatMessage]
    total: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/test-encryption",
    response_model=EncryptionTestResponse,
    summary="Test AES-256-GCM encryption",
    description="""
Encrypts any text and shows you exactly what gets stored in Supabase vs what the user sees.

**How to use:**
- Enter any text and a user_id
- The response shows the ciphertext (what Supabase stores) and the decrypted text (what the user sees)
- Same text encrypted twice produces DIFFERENT ciphertext (unique nonces)
- Different user_id = different key = different ciphertext
    """
)
async def test_encryption(request: EncryptionTestRequest):
    """
    Encrypt text and show what Supabase stores vs what the user sees.
    """
    try:
        encrypted = encrypt(request.text, request.user_id)
        decrypted = decrypt(encrypted, request.user_id)
        success = decrypted == request.text

        return EncryptionTestResponse(
            original_text=request.text,
            encrypted_stored_in_db=encrypted,
            decrypted_back=decrypted,
            round_trip_success=success,
            algorithm="AES-256-GCM with HKDF-SHA256 per-user key derivation",
            what_supabase_sees=f"Random-looking ciphertext: {encrypted[:60]}...",
            what_user_sees=f"Original readable text: {decrypted}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption test failed: {e}")


@router.get(
    "/raw/{session_id}",
    summary="View RAW encrypted data in Supabase",
    description="""
Shows the ACTUAL raw data stored in Supabase for a session — the encrypted ciphertext.
This proves the database contains only unreadable ciphertext, not plaintext.

**What you'll see:**
- `content_encrypted`: The AES-256-GCM ciphertext stored in Supabase (unreadable)
- `emotion`, `mood_level`: Stored in plaintext (not sensitive, used for analytics)
    """
)
async def view_raw_supabase_data(
    session_id: str,
    user_id: str = Query(..., description="User ID to filter messages"),
    limit: int = Query(5, ge=1, le=20),
):
    """
    View the raw encrypted data exactly as stored in Supabase.
    """
    if not settings.supabase_url or "your_supabase" in settings.supabase_url:
        raise HTTPException(
            status_code=503,
            detail="Supabase not configured. Add SUPABASE_URL and SUPABASE_SERVICE_KEY to .env"
        )

    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
    }
    params = {
        "session_id": f"eq.{session_id}",
        "user_id": f"eq.{user_id}",
        "order": "created_at.asc",
        "limit": str(limit),
        "select": "id,role,content_encrypted,emotion,mood_level,created_at",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.supabase_url.rstrip('/')}/rest/v1/chat_messages",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            rows = resp.json()

        if not rows:
            return {
                "message": "No data found. Send a chat message with this session_id and user_id first.",
                "how_to_send": "Use POST /api/chat/ with message, user_id, and session_id fields",
                "session_id": session_id,
                "user_id": user_id,
            }

        return {
            "session_id": session_id,
            "user_id": user_id,
            "total_rows": len(rows),
            "proof_of_encryption": "The content_encrypted column contains AES-256-GCM ciphertext — unreadable without the correct key",
            "raw_database_rows": [
                {
                    "id": row["id"],
                    "role": row["role"],
                    "content_encrypted": row["content_encrypted"],  # This is what Supabase stores
                    "is_encrypted": is_encrypted(row["content_encrypted"]),
                    "emotion": row["emotion"],
                    "mood_level": row["mood_level"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Table not found. Run supabase_setup.sql first.")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/verify/{session_id}",
    summary="Verify encryption — shows ciphertext vs plaintext side by side",
    description="""
The most useful endpoint for proving end-to-end encryption.

**Shows for each message:**
- What Supabase stores (ciphertext — unreadable)
- What the user sees after decryption (plaintext — readable)
- Confirmation that all data is properly encrypted
    """
)
async def verify_session_encryption(
    session_id: str,
    user_id: str = Query(..., description="User ID — must match the session owner"),
    limit: int = Query(5, ge=1, le=20),
):
    """
    Prove that Supabase stores only ciphertext, but the correct user can decrypt it.
    """
    result = await verify_encryption_in_db(session_id, user_id, limit)
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return result


@router.get(
    "/history/{session_id}",
    response_model=SessionHistoryResponse,
    summary="Get decrypted chat history",
    description="""
Retrieves and DECRYPTS the conversation history for a session.
Only works with the correct user_id — wrong user_id = decryption fails.
    """
)
async def get_history(
    session_id: str,
    user_id: str = Query(..., description="User ID — must match the session owner"),
):
    """
    Retrieve and decrypt conversation history. Wrong user_id = access denied.
    """
    messages = await get_session_history(session_id, user_id)
    return SessionHistoryResponse(
        session_id=session_id,
        user_id=user_id,
        messages=messages,
        total=len(messages),
    )


@router.get(
    "/health",
    summary="Check Supabase connection and encryption status",
)
async def db_health():
    """Check if Supabase is configured and reachable."""
    configured = (
        bool(settings.supabase_url)
        and "your_supabase" not in settings.supabase_url
        and bool(settings.supabase_service_key)
        and "your_supabase" not in settings.supabase_service_key
    )

    result = {
        "supabase_configured": configured,
        "encryption_algorithm": "AES-256-GCM",
        "key_derivation": "HKDF-SHA256 per user",
        "status": "ready" if configured else "supabase_not_configured",
    }

    if not configured:
        result["fix"] = "Add SUPABASE_URL and SUPABASE_SERVICE_KEY to backend/.env"
        return result

    # Test actual connection
    try:
        headers = {
            "apikey": settings.supabase_service_key,
            "Authorization": f"Bearer {settings.supabase_service_key}",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.supabase_url.rstrip('/')}/rest/v1/chat_messages",
                headers=headers,
                params={"limit": "1"},
            )
        if resp.status_code == 200:
            result["connection"] = "✅ Connected to Supabase successfully"
            result["tables"] = "✅ chat_messages table exists"
        elif resp.status_code == 404:
            result["connection"] = "✅ Supabase reachable"
            result["tables"] = "❌ Tables not found — run supabase_setup.sql in SQL Editor"
        else:
            result["connection"] = f"⚠️ HTTP {resp.status_code}"
    except Exception as e:
        result["connection"] = f"❌ Cannot reach Supabase: {e}"

    return result
