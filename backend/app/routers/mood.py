"""Mood Router — POST /api/mood/checkin"""
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import MoodCheckIn, MoodCheckInResponse
from app.agents.activity_generator import get_activities, get_wellness_tip

router = APIRouter(prefix="/api/mood", tags=["Mood"])


@router.post("/checkin", response_model=MoodCheckInResponse, status_code=status.HTTP_200_OK)
async def mood_checkin(checkin: MoodCheckIn):
    try:
        if not checkin.emotions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one emotion must be provided.")
        primary_emotion = checkin.emotions[0]
        activities = get_activities(emotion=primary_emotion, mood_level=checkin.mood_level, count=4)
        wellness_tip = get_wellness_tip(checkin.mood_level)
        mood_messages = {
            "very_bad": "Thank you for checking in. It takes courage to acknowledge how you're feeling. You're not alone in this.",
            "bad": "I hear you. It's okay to not be okay. Let's take it one small step at a time.",
            "neutral": "Thanks for checking in! Neutral days are a great foundation to build something positive.",
            "good": "That's wonderful to hear! Keep nurturing what's working for you.",
            "very_good": "You're doing amazing! Celebrate this feeling and remember it on harder days.",
        }
        message = mood_messages.get(checkin.mood_level.value, "Thank you for checking in with yourself today.")
        return MoodCheckInResponse(message=message, activities=activities, wellness_tip=wellness_tip)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}")


@router.get("/health")
async def mood_health():
    return {"status": "healthy", "service": "NeuroNest Mood"}
