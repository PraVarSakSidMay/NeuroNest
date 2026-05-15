"""
Memory Router — /api/memory
View and manage RAG conversation memories stored locally.
"""
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path

from app.agents.memory_agent import (
    _load_memories, _get_memory_path, retrieve_relevant_memories,
    generate_session_summary, MEMORY_DIR
)

router = APIRouter(prefix="/api/memory", tags=["Memory (RAG)"])


class MemorySummaryRequest(BaseModel):
    user_id: str
    session_id: str
    conversation: List[dict]   # list of {role, content}
    emotions: List[str] = []


@router.get("/user/{user_id}")
async def get_user_memories(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get all stored memories for a user.
    Shows what the chatbot remembers about this person.
    """
    memories = _load_memories(user_id)
    if not memories:
        return {
            "user_id": user_id,
            "total_memories": 0,
            "memories": [],
            "message": "No memories stored yet. Start a conversation with a user_id to build memory."
        }

    # Return most recent first, limited
    recent = list(reversed(memories[-limit:]))
    return {
        "user_id": user_id,
        "total_memories": len(memories),
        "showing": len(recent),
        "memories": recent,
    }


@router.get("/user/{user_id}/search")
async def search_memories(
    user_id: str,
    query: str = Query(..., description="Search query to find relevant memories"),
    emotion: str = Query("", description="Optional emotion filter"),
    top_k: int = Query(3, ge=1, le=10),
):
    """
    Search a user's memories for relevant past context.
    This is what the RAG agent does internally on each message.
    """
    results = retrieve_relevant_memories(
        user_id=user_id,
        current_message=query,
        current_emotion=emotion,
        top_k=top_k,
    )
    return {
        "user_id": user_id,
        "query": query,
        "results_found": len(results),
        "memories": results,
    }


@router.post("/summarize")
async def summarize_session(request: MemorySummaryRequest):
    """
    Manually trigger a session summary and save it to memory.
    Normally this happens automatically, but you can call this endpoint
    to force a summary at the end of a session.
    """
    from app.models.schemas import ChatMessage

    history = [
        ChatMessage(role=m.get("role", "user"), content=m.get("content", ""))
        for m in request.conversation
    ]

    summary = await generate_session_summary(
        user_id=request.user_id,
        session_id=request.session_id,
        conversation_history=history,
        detected_emotions=request.emotions,
    )

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not generate summary — conversation too short or LLM unavailable."
        )

    return {
        "user_id": request.user_id,
        "session_id": request.session_id,
        "summary": summary,
        "message": "Summary saved to local memory successfully."
    }


@router.delete("/user/{user_id}")
async def clear_user_memories(user_id: str):
    """
    Clear all stored memories for a user.
    Use this to reset the chatbot's memory for a specific user.
    """
    path = _get_memory_path(user_id)
    if path.exists():
        path.unlink()
        return {"message": f"All memories cleared for user {user_id}"}
    return {"message": f"No memories found for user {user_id}"}


@router.get("/health")
async def memory_health():
    """Check memory storage status."""
    memory_files = list(MEMORY_DIR.glob("*.json"))
    total_users = len(memory_files)
    total_size_kb = sum(f.stat().st_size for f in memory_files) / 1024

    return {
        "status": "healthy",
        "storage": "local",
        "storage_path": str(MEMORY_DIR),
        "total_users_with_memory": total_users,
        "total_storage_kb": round(total_size_kb, 2),
        "note": "Memory is stored locally in backend/data/memory/*.json"
    }
