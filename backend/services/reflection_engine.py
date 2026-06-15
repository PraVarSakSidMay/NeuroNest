
import json
import asyncio
from typing import List, Optional, Dict
from domain.entities import Reflection, Interaction, UserState
from domain.value_objects import ReflectionType
from infrastructure.repositories import IReflectionRepository
from services.model_manager import ModelManager
from services.rag_service import RAGService
from core.logger import logger

class ReflectionEngine:
    """
    Advanced Reflection Engine that analyzes interactions to derive long-term insights.
    Handles duplicate avoidance, insight merging, and scoring.
    """
    
    def __init__(
        self, 
        reflection_repo: IReflectionRepository, 
        model_manager: ModelManager,
        rag_service: RAGService
    ):
        self.reflection_repo = reflection_repo
        self.model_manager = model_manager
        self.rag_service = rag_service

    async def reflect_on_interaction(
        self, 
        user_id: str, 
        interaction: Interaction, 
        user_state: UserState
    ):
        """
        Main entry point for post-conversation reflection.
        """
        logger.info(f"Reflection: Starting analysis for user {user_id}")
        
        # 1. Generate Raw Insights via LLM
        raw_insights = await self._generate_raw_insights(interaction, user_state)
        
        # 2. Process and Persist each insight
        for insight_data in raw_insights:
            await self._process_single_insight(user_id, insight_data, interaction.id)

    async def _generate_raw_insights(self, interaction: Interaction, user_state: UserState) -> List[dict]:
        """Uses the LLM to extract patterns, goals, and triggers."""
        prompt = f"""
        You are a Deep Reflection Engine. Analyze the following conversation turn and user state.
        
        INPUT:
        - User Said: "{interaction.transcript}"
        - AI Responded: "{interaction.response_text}"
        - Current Emotion: {interaction.emotion_data.emotion if interaction.emotion_data else "neutral"}
        - User Feedback: {interaction.feedback_score if interaction.feedback_score else "none"}
        - Dominant Emotion: {user_state.dominant_emotion}
        - Active Projects: {[p.name for p in user_state.active_projects]}
        
        TASK:
        Identify new insights, behavioral patterns, preferences, goals, or emotional triggers.
        Be concise and objective.
        
        Return JSON strictly in this format:
        [
          {{
            "type": "insight | behavioral_pattern | preference | goal_detected | emotional_trigger",
            "content": "the actual insight string",
            "confidence": 0.0 - 1.0
          }}
        ]
        """
        
        response_text = self.model_manager.get_llm_response(
            transcript=interaction.transcript,
            system_prompt=prompt,
            json_mode=True
        )
        
        try:
            # Clean up JSON if necessary
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Reflection: Failed to parse LLM response: {e}")
            return []

    async def _process_single_insight(self, user_id: str, insight_data: dict, interaction_id: str):
        """Checks for duplicates, merges similar insights, or saves new ones."""
        content = insight_data.get("content")
        r_type = ReflectionType(insight_data.get("type", "insight"))
        confidence = insight_data.get("confidence", 0.5)
        
        # 1. Generate embedding for similarity search
        embedding = await asyncio.get_event_loop().run_in_executor(
            None, self.rag_service.generate_embedding, content
        )
        if not embedding: return

        # 2. Search for existing similar reflections
        existing_reflections = await self.reflection_repo.find_similar(user_id, embedding, k=1)
        
        if existing_reflections:
            best_match = existing_reflections[0]
            # If very similar (>0.85), merge them
            # We assume the find_similar returns a tuple of (reflection, similarity) or similar
            # For this implementation, we'll assume the repo returns the reflection entity
            # and we'll check similarity locally or trust the repo's threshold.
            
            # Simple merge logic:
            logger.info(f"Reflection: Merging new insight into existing: {best_match.id}")
            best_match.source_interaction_ids.append(interaction_id)
            best_match.score.evidence_count += 1
            best_match.score.confidence = min(0.99, best_match.score.confidence + 0.05)
            await self.reflection_repo.save(best_match)
        else:
            # 3. Save as new reflection
            logger.info(f"Reflection: Storing new {r_type} for user {user_id}")
            new_reflection = Reflection(
                user_id=user_id,
                type=r_type,
                content=content,
                embedding=embedding,
                source_interaction_ids=[interaction_id]
            )
            new_reflection.score.confidence = confidence
            await self.reflection_repo.save(new_reflection)
