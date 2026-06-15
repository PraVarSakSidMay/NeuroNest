
import json
from typing import List, Dict, Optional
from domain.entities import UserState, Memory
from domain.value_objects import ConversationPlan, ConversationStrategy, Emotion
from services.model_manager import ModelManager
from core.logger import logger

class ConversationPlanningEngine:
    """
    Engine responsible for high-level conversation planning.
    Analyzes user message and context to select a response strategy before LLM generation.
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
        Determines the optimal conversation strategy and response goal.
        """
        logger.info("Planning: Generating strategic plan for response")
        
        # 1. Prepare Context Summary for the Planner
        memory_summary = self._summarize_memories(retrieved_memories)
        
        # 2. Build Planner Prompt
        planner_prompt = f"""
        You are a Conversation Planning Architect. Analyze the current turn and context to decide on the best strategy.
        
        INPUT:
        - User Message: "{user_message}"
        - User State (Dominant Emotion): {user_state.dominant_emotion}
        - User State (Active Projects): {[p.name for p in user_state.active_projects]}
        - Emotion Profile (Fused): {emotion_profile}
        - Relevant Memories: {memory_summary}
        
        STRATEGIES:
        - coaching: Helping the user grow, find their own solutions, or improve skills.
        - teaching: Explaining complex concepts, providing new information, or tutoring.
        - emotional_support: Prioritizing validation, comfort, empathy, and active listening.
        - debugging: Helping solve a technical, logical, or step-by-step problem.
        - brainstorming: Generating creative ideas, exploring possibilities, and divergent thinking.
        - motivation: Providing energy, encouragement, drive, and accountability.
        - casual: General friendly, low-stakes conversation.
        
        TASK:
        Identify the user's intent and emotional need, then select the most effective strategy.
        
        Return JSON strictly in this format:
        {{
          "intent": "Brief description of what the user wants",
          "emotional_need": "Brief description of the user's emotional state/need",
          "conversation_strategy": "one of the strategies listed above",
          "response_goal": "The specific objective of the upcoming AI response",
          "risk_level": 1-5 (5 is highest risk/sensitivity),
          "confidence": 0.0 - 1.0
        }}
        """
        
        # 3. Use LLM to generate the plan
        response_text = self.model_manager.get_llm_response(
            transcript=user_message,
            system_prompt=planner_prompt,
            json_mode=True
        )
        
        # 4. Parse and return the plan
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            
            plan_data = json.loads(response_text)
            
            return ConversationPlan(
                intent=plan_data.get("intent", "General interaction"),
                emotional_need=plan_data.get("emotional_need", "None detected"),
                conversation_strategy=ConversationStrategy(plan_data.get("conversation_strategy", "casual")),
                response_goal=plan_data.get("response_goal", "Maintain friendly conversation"),
                risk_level=plan_data.get("risk_level", 1),
                confidence=plan_data.get("confidence", 0.5)
            )
        except Exception as e:
            logger.error(f"Planning: Failed to generate plan, falling back to casual: {e}")
            return ConversationPlan(
                intent="General chat",
                emotional_need="Unknown",
                conversation_strategy=ConversationStrategy.CASUAL,
                response_goal="Respond naturally",
                confidence=0.1
            )

    def _summarize_memories(self, memories: Dict[str, List[Memory]]) -> str:
        """Helper to create a concise summary of retrieved memories for the planner."""
        summary = []
        for m_type, items in memories.items():
            for m in items[:2]: # Top 2 of each type
                summary.append(f"[{m_type}] {m.content}")
        return " | ".join(summary)
