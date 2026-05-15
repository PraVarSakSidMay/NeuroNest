"""NeuroNest Wellness Agent — LangGraph 4-node pipeline with RAG memory."""
import uuid, random
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.models.schemas import ChatMessage, ChatResponse, EmotionType, MoodLevel, ActivitySuggestion, MusicTrack
from app.agents.mood_detector import detect_mood
from app.agents.activity_generator import get_activities, get_wellness_tip
from app.agents.special_actions import get_special_action, get_joke, get_proverb, get_music_tracks
from app.agents.llm_router import invoke_with_fallback
from app.config import get_settings

settings = get_settings()


class WellnessState(TypedDict):
    user_message: str
    user_id: Optional[str]
    conversation_history: List[ChatMessage]
    detected_emotion: Optional[EmotionType]
    mood_level: Optional[MoodLevel]
    mood_confidence: float
    memory_context: str          # RAG: retrieved past session summaries
    ai_response: str
    response_mode: str
    activities: List[ActivitySuggestion]
    celebration_message: Optional[str]
    special_action: Optional[str]
    special_content: Optional[str]
    music_tracks: List[MusicTrack]
    joke: Optional[str]
    proverb: Optional[str]
    proverb_author: Optional[str]
    wellness_tip: str
    session_id: str
    llm_provider: str
    error: Optional[str]

def get_system_prompt(emotion: Optional[EmotionType]) -> str:
    emotion_str = emotion.value if emotion else "neutral"
    return f"""You are NeuroNest — a warm, supportive AI wellness companion.
The user is currently feeling {emotion_str.upper()}.

CORE RULES — NEVER BREAK:
1. ONLY discuss mental wellness, emotions, stress, relationships, self-care, personal growth.
   For anything else say: "I'm here just for your emotional wellbeing. Is there something on your mind?"
2. NEVER diagnose any mental health condition.
3. If user mentions self-harm or suicide, IMMEDIATELY respond:
   "Please don't give up. You matter so much. Please reach out right now — iCall: 9152987821 (India) | 988 Suicide & Crisis Lifeline (US). I'm here with you."
4. Read the user's message carefully and understand their context deeply. Respond to the SPECIFIC situation they described.
5. Write 4-6 warm, natural sentences. Conversational, like a caring friend or supportive parent. 
   The response will be read aloud by a voice assistant, so write in a natural spoken style.
6. DO NOT suggest activities in your response — those are shown separately.
7. Be genuine. Avoid sounding robotic, repetitive, or like you are reading from a script. Do not start every sentence with "Oh sweetheart".
8. End with ONE gentle question that invites them to share more.
"""


def get_response_mode(emotion: Optional[EmotionType]) -> str:
    CELEBRATE_EMOTIONS = {EmotionType.HAPPY, EmotionType.EXCITED}
    REFLECT_EMOTIONS = {EmotionType.CALM}
    if emotion in CELEBRATE_EMOTIONS:
        return "celebrate"
    if emotion in REFLECT_EMOTIONS:
        return "reflect"
    return "support"


def _build_emotional_journey(history: list) -> str:
    """
    Extract the emotional journey from conversation history.
    Returns a context string that tells the LLM what the user has shared so far,
    so it can acknowledge contrasts and connections in its response.

    Example output:
    "EMOTIONAL JOURNEY IN THIS CONVERSATION:
    - Earlier: User shared they were HAPPY because they passed their examination
    - Now: User is expressing LONELINESS
    → Acknowledge this contrast warmly: 'Even though you just had this wonderful achievement...'"
    """
    if not history or len(history) < 2:
        return ""

    # Extract user messages and their emotional content
    user_messages = []
    for msg in history:
        role = msg.role if hasattr(msg, 'role') else msg.get('role', '')
        content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
        if role == "user" and content:
            user_messages.append(content)

    if not user_messages:
        return ""

    # Build a summary of what was shared
    journey_lines = ["EMOTIONAL JOURNEY IN THIS CONVERSATION SO FAR:"]

    for i, msg in enumerate(user_messages[-4:], 1):  # Last 4 user messages
        msg_lower = msg.lower()
        # Detect emotion + situation in each message
        emotion_hint = ""
        situation_hint = ""

        if any(kw in msg_lower for kw in ["happy", "happiness", "great", "wonderful", "amazing", "passed", "got a job", "secured", "graduated", "won", "achieved"]):
            emotion_hint = "HAPPY/POSITIVE"
        elif any(kw in msg_lower for kw in ["sad", "sadness", "crying", "heartbroken", "depressed"]):
            emotion_hint = "SAD"
        elif any(kw in msg_lower for kw in ["stressed", "stress", "pressure", "overwhelmed", "anxious", "worried"]):
            emotion_hint = "STRESSED/ANXIOUS"
        elif any(kw in msg_lower for kw in ["lonely", "alone", "isolated", "no one"]):
            emotion_hint = "LONELY"
        elif any(kw in msg_lower for kw in ["angry", "anger", "mad", "frustrated"]):
            emotion_hint = "ANGRY"

        if any(kw in msg_lower for kw in ["exam", "examination", "test", "passed", "cleared"]):
            situation_hint = "passing an exam"
        elif any(kw in msg_lower for kw in ["job", "offer", "selected", "hired", "placed"]):
            situation_hint = "getting a job"
        elif any(kw in msg_lower for kw in ["promotion", "promoted"]):
            situation_hint = "getting promoted"
        elif any(kw in msg_lower for kw in ["graduation", "graduated", "degree"]):
            situation_hint = "graduating"

        label = f"Message {i}"
        if emotion_hint and situation_hint:
            journey_lines.append(f"- {label}: User expressed {emotion_hint} about {situation_hint}")
        elif emotion_hint:
            journey_lines.append(f"- {label}: User expressed {emotion_hint} — '{msg[:80]}...' " if len(msg) > 80 else f"- {label}: User expressed {emotion_hint} — '{msg}'")
        else:
            journey_lines.append(f"- {label}: '{msg[:80]}...'" if len(msg) > 80 else f"- {label}: '{msg}'")

    # Add instruction for how to use this context
    journey_lines.append("")
    journey_lines.append("USE THIS JOURNEY to make your response feel connected and human:")
    journey_lines.append("- If there's a CONTRAST (was happy, now sad) → acknowledge both: 'Even though you just had such a wonderful achievement with [situation], it's really touching that you're feeling [current emotion] now...'")
    journey_lines.append("- If there's CONTINUITY (same emotion) → build on what was shared before")
    journey_lines.append("- If they SHIFTED emotions → acknowledge the shift warmly and naturally")
    journey_lines.append("- Always make the person feel like you've been listening to their whole story, not just the last message")

    return "\n".join(journey_lines)


async def detect_mood_node(state: WellnessState) -> WellnessState:
    mood_result = await detect_mood(
        user_message=state["user_message"],
        conversation_history=state.get("conversation_history", []),
    )
    return {
        **state,
        "detected_emotion": mood_result["emotion"],
        "mood_level": mood_result["mood_level"],
        "mood_confidence": mood_result["confidence"],
    }


async def retrieve_memory_node(state: WellnessState) -> WellnessState:
    """
    Node 1.5: RAG memory node — disabled for live responses.
    Memory is still SAVED to disk after each message (for history),
    but NOT injected into the prompt so the AI responds purely from
    the live conversation context, giving deeper and more relevant answers.
    """
    # Always return empty memory_context — AI uses only live conversation history
    return {**state, "memory_context": ""}


async def generate_response_node(state: WellnessState) -> WellnessState:
    emotion = state.get("detected_emotion")
    system_prompt = get_system_prompt(emotion)
    history = state.get("conversation_history", [])

    # ── Build emotional journey context from live conversation history ────────
    # This uses ONLY what the user has shared in THIS conversation — no stored data
    # Extract what the user has shared in this session so far
    emotional_journey = _build_emotional_journey(history)
    if emotional_journey:
        system_prompt = system_prompt + f"\n\n{emotional_journey}\n"

    # Detect follow-up and inject context
    is_followup = len(history) >= 2
    last_assistant = None
    if is_followup:
        for msg in reversed(history):
            role = msg.role if hasattr(msg, 'role') else msg.get('role', '')
            if role == "assistant":
                content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                last_assistant = content
                break

    if is_followup and last_assistant:
        followup_context = f"""
IMPORTANT — THIS IS A FOLLOW-UP MESSAGE IN AN ONGOING CONVERSATION:
Your last message was: "{last_assistant[:300]}..."

The user is now sharing something new or different. Your response MUST:
1. Acknowledge the CONTRAST or CONNECTION to what was shared before
   - If they were happy before and are now sad/lonely → acknowledge both: "Even though you just had such a wonderful achievement, it's really touching that you're feeling lonely right now..."
   - If they were stressed before and are now better → celebrate the shift
   - If they're continuing the same emotion → build on what was said
2. React to the SPECIFIC thing they're sharing NOW
3. Be warm, motherly, and genuinely engaged with their full story
4. Give a rich, detailed response — the user will hear this via voice so longer is better
"""
        system_prompt = system_prompt + followup_context

    messages = [SystemMessage(content=system_prompt)]
    for msg in history[-8:]:
        role = msg.role if hasattr(msg, 'role') else msg.get('role', 'user')
        content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=state["user_message"]))

    emotion_value = emotion.value if emotion else "neutral"
    ai_response = await invoke_with_fallback(
        messages,
        temperature=0.85,
        max_tokens=800,
        emotion_value=emotion_value,
        user_message=state["user_message"],
        conversation_history=history,
    )

    return {**state, "ai_response": ai_response, "llm_provider": "auto"}


async def generate_activities_node(state: WellnessState) -> WellnessState:
    emotion    = state["detected_emotion"] or EmotionType.NEUTRAL
    mood_level = state["mood_level"] or MoodLevel.NEUTRAL
    mode       = get_response_mode(emotion)
    wellness_tip = get_wellness_tip(mood_level)

    if mode in ("celebrate", "reflect"):
        return {**state, "response_mode": mode, "activities": [], "celebration_message": None, "wellness_tip": wellness_tip}

    return {**state, "response_mode": "support", "activities": get_activities(emotion=emotion, mood_level=mood_level, count=5), "celebration_message": None, "wellness_tip": wellness_tip}


async def special_action_node(state: WellnessState) -> WellnessState:
    emotion = state["detected_emotion"] or EmotionType.NEUTRAL
    mood_level = state["mood_level"] or MoodLevel.NEUTRAL
    action_type, action_content = get_special_action(emotion, mood_level)
    joke = get_joke(emotion)
    proverb, proverb_author = get_proverb(emotion)
    music_tracks = get_music_tracks(emotion)
    return {**state, "special_action": action_type, "special_content": action_content, "joke": joke, "proverb": proverb, "proverb_author": proverb_author, "music_tracks": music_tracks}


def build_wellness_graph():
    graph = StateGraph(WellnessState)
    graph.add_node("detect_mood",         detect_mood_node)
    graph.add_node("retrieve_memory",     retrieve_memory_node)   # RAG node
    graph.add_node("generate_response",   generate_response_node)
    graph.add_node("generate_activities", generate_activities_node)
    graph.add_node("special_action",      special_action_node)

    graph.set_entry_point("detect_mood")
    graph.add_edge("detect_mood",         "retrieve_memory")      # mood → RAG
    graph.add_edge("retrieve_memory",     "generate_response")    # RAG → response
    graph.add_edge("generate_response",   "generate_activities")
    graph.add_edge("generate_activities", "special_action")
    graph.add_edge("special_action",      END)
    return graph.compile()


wellness_graph = build_wellness_graph()


async def process_chat(
    user_message: str,
    conversation_history: List[ChatMessage] = None,
    session_id: str = None,
    user_id: str = None,
) -> ChatResponse:
    if session_id is None:
        session_id = str(uuid.uuid4())
    if conversation_history is None:
        conversation_history = []

    initial_state: WellnessState = {
        "user_message":        user_message,
        "user_id":             user_id,
        "conversation_history": conversation_history,
        "detected_emotion":    None,
        "mood_level":          None,
        "mood_confidence":     0.0,
        "memory_context":      "",
        "ai_response":         "",
        "response_mode":       "support",
        "activities":          [],
        "celebration_message": None,
        "special_action":      None,
        "special_content":     None,
        "music_tracks":        [],
        "joke":                None,
        "proverb":             None,
        "proverb_author":      None,
        "wellness_tip":        "",
        "session_id":          session_id,
        "llm_provider":        "auto",
        "error":               None,
    }

    final_state = await wellness_graph.ainvoke(initial_state)

    return ChatResponse(
        response=            final_state["ai_response"],
        detected_emotion=    final_state["detected_emotion"] or EmotionType.NEUTRAL,
        mood_level=          final_state["mood_level"] or MoodLevel.NEUTRAL,
        response_mode=       final_state.get("response_mode", "support"),
        activities=          final_state["activities"],
        celebration_message= final_state.get("celebration_message"),
        special_action=      final_state["special_action"],
        special_content=     final_state["special_content"],
        music_tracks=        final_state["music_tracks"],
        joke=                final_state["joke"],
        proverb=             final_state["proverb"],
        proverb_author=      final_state["proverb_author"],
        session_id=          session_id,
        wellness_tip=        final_state["wellness_tip"],
        llm_provider=        final_state["llm_provider"],
    )
