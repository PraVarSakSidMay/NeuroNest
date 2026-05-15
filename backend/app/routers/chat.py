"""
Chat Router — /api/chat
Handles text-based wellness chat with RAG memory support.
"""
import uuid, logging
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import ChatRequest, ChatResponse
from app.agents.wellness_agent import process_chat
from app.services.database import save_full_chat_turn

router = APIRouter(prefix="/api/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Send a message to the NeuroNest wellness chatbot.
    Pass user_id to enable RAG memory — the chatbot will remember past sessions.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())

        response = await process_chat(
            user_message=request.message,
            conversation_history=request.conversation_history or [],
            session_id=session_id,
            user_id=request.user_id,   # enables RAG memory
        )

        # Save encrypted to Supabase if user_id provided
        if request.user_id:
            try:
                await save_full_chat_turn(
                    session_id=session_id,
                    user_id=request.user_id,
                    user_message=request.message,
                    response=response,
                )
            except Exception as db_err:
                logger.warning(f"DB save failed (non-critical): {db_err}")

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    return {"status": "healthy", "service": "NeuroNest Chat"}
