import json
from typing import List, Dict, Optional
from domain.entities import UserState, Memory
from domain.value_objects import ConversationPlan, ConversationStrategy
from services.model_manager import ModelManager
from core.logger import logger

class ConversationPlanningEngine:
    """
    Engine responsible for high-level conversation planning.
    Analyzes user message and context to select a response strategy programmatically.
    """
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager

    def plan_response(
        self,
        user_message: str,
        user_state: UserState,
        retrieved_memories: Dict[str, List[Memory]],
        emotion_profile: dict
    ) -> ConversationPlan:
        """
        Determines the optimal conversation strategy and response goal programmatically.
        """
        logger.info("Planning: Generating strategic plan programmatically")
        
        msg_lower = user_message.lower()
        
        # 1. Detect Intent Category
        intent_desc = "General conversation"
        strategy = ConversationStrategy.CASUAL
        response_goal = "Respond naturally and maintain the conversation"
        risk_level = 1
        
        # Keyword list match helpers
        is_debug = any(w in msg_lower for w in ["error", "exception", "bug", "crash", "fail", "broken", "issue", "debug", "doesn't work", "not working", "traceback", "syntax", "code", "programming", "python", "javascript", "typescript", "c++", "c#", "java"])
        is_teach = any(w in msg_lower for w in ["how does", "why does", "explain", "teach me", "what is", "what are", "how to", "tutorial", "learn", "concept", "define", "meaning of"])
        is_brainstorm = any(w in msg_lower for w in ["ideas", "brainstorm", "suggest", "alternatives", "invent", "create", "innovate", "what if", "generate ideas", "creative options"])
        is_motivate = any(w in msg_lower for w in ["lazy", "stuck", "unmotivated", "procrastinat", "cannot focus", "tired", "don't want to", "help me start", "discipline", "lack energy"])
        is_coach = any(w in msg_lower for w in ["improve", "grow", "better", "plan", "career", "life goal", "habit", "advice", "guide", "how do i handle", "feedback", "routine"])
        
        user_emotion = emotion_profile.get("emotion", "neutral").lower()
        is_emotional = user_emotion in ["sad", "depressed", "anxious", "fearful", "frustrated", "angry"] or any(w in msg_lower for w in ["feel", "feeling", "upset", "hurt", "grief", "lonely", "worried", "sad", "scared", "pain", "panic"])

        # Crisis check (safety first)
        is_crisis = any(w in msg_lower for w in ["kill myself", "suicide", "end my life", "hurt myself"])
        
        # Determine strategy priority
        if is_crisis:
            strategy = ConversationStrategy.EMOTIONAL_SUPPORT
            intent_desc = "Crisis self-harm statement"
            response_goal = "Provide immediate, unconditional safety validation and point to resources"
            risk_level = 5
        elif is_emotional:
            strategy = ConversationStrategy.EMOTIONAL_SUPPORT
            intent_desc = f"Discussing feelings of {user_emotion}"
            response_goal = "Validate emotional state, offer active listening, comfort, and support"
            risk_level = 3 if user_emotion in ["sad", "depressed", "angry"] else 2
        elif is_debug:
            strategy = ConversationStrategy.DEBUGGING
            intent_desc = "Solve a technical or coding issue"
            response_goal = "Help step-by-step to diagnose, debug, and correct the error/bug"
            risk_level = 1
        elif is_teach:
            strategy = ConversationStrategy.TEACHING
            intent_desc = "Learn about a concept or mechanism"
            response_goal = "Explain the topic clearly and conceptually, checking for understanding"
            risk_level = 1
        elif is_brainstorm:
            strategy = ConversationStrategy.BRAINSTORMING
            intent_desc = "Generate creative ideas or plans"
            response_goal = "Explore divergent possibilities and present creative suggestions"
            risk_level = 1
        elif is_motivate:
            strategy = ConversationStrategy.MOTIVATION
            intent_desc = "Seeking motivation or focus assistance"
            response_goal = "Provide encouragement, accountability, and a small starting action step"
            risk_level = 1
        elif is_coach:
            strategy = ConversationStrategy.COACHING
            intent_desc = "Personal growth or goal guidance"
            response_goal = "Ask open-ended coaching questions to guide the user towards their own solution"
            risk_level = 1
        else:
            strategy = ConversationStrategy.CASUAL
            intent_desc = "General chat"
            response_goal = "Respond with warm, casual, and friendly engagement"
            risk_level = 1

        # Map emotional need based on emotion and strategy
        emotional_need = "Cognitive engagement"
        if is_crisis:
            emotional_need = "Immediate safety support"
        elif user_emotion in ["sad", "depressed"]:
            emotional_need = "Empathy and validation"
        elif user_emotion in ["anxious", "fearful"]:
            emotional_need = "Grounding and reassurance"
        elif user_emotion in ["angry", "frustrated"]:
            emotional_need = "Vent release and de-escalation"
        elif user_emotion in ["happy", "excited"]:
            emotional_need = "Shared positive validation"

        return ConversationPlan(
            intent=intent_desc,
            emotional_need=emotional_need,
            conversation_strategy=strategy,
            response_goal=response_goal,
            risk_level=risk_level,
            confidence=0.9
        )

    def _summarize_memories(self, memories: Dict[str, List[Memory]]) -> str:
        """Helper to create a concise summary of retrieved memories for the planner."""
        summary = []
        for m_type, items in memories.items():
            for m in items[:2]: # Top 2 of each type
                summary.append(f"[{m_type}] {m.content}")
        return " | ".join(summary)
