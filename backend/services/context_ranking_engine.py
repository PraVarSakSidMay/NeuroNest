
import math
import time
from typing import List, Dict, Optional
from datetime import datetime, timezone
from domain.entities import Memory, UserState
from domain.value_objects import MemoryType, EmotionEnum
from core.logger import logger

class RankingWeights:
    """Configuration for ranking factor weights."""
    def __init__(
        self,
        semantic: float = 0.40,
        recency: float = 0.15,
        emotional: float = 0.15,
        goal: float = 0.20,
        importance: float = 0.10
    ):
        self.semantic = semantic
        self.recency = recency
        self.emotional = emotional
        self.goal = goal
        self.importance = importance

class ContextRankingEngine:
    """
    Advanced Reranking Engine for AI Memory.
    Uses a multi-factor scoring algorithm to prioritize context.
    """

    def __init__(self, base_weights: Optional[RankingWeights] = None):
        self.base_weights = base_weights or RankingWeights()

    def rank_memories(
        self, 
        query_embedding: List[float], 
        memories: List[Memory], 
        user_state: UserState,
        limit: int = 5
    ) -> List[Memory]:
        """
        Reranks a list of candidate memories using the multi-factor scoring formula.
        """
        if not memories:
            return []

        # 1. Determine dynamic weights based on user state
        weights = self._calculate_dynamic_weights(user_state)
        
        scored_memories = []
        for memory in memories:
            score = self._calculate_final_score(
                query_embedding, memory, user_state, weights
            )
            scored_memories.append((score, memory))

        # 2. Sort by final score descending
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        logger.info(f"Ranking: Reranked {len(memories)} memories. Top score: {scored_memories[0][0]:.4f}")
        
        return [m for _, m in scored_memories[:limit]]

    def _calculate_dynamic_weights(self, user_state: UserState) -> RankingWeights:
        """
        Adjusts weights dynamically based on the user's current situation.
        Example: If stress is high, increase emotional relevance weight.
        """
        weights = RankingWeights(
            semantic=self.base_weights.semantic,
            recency=self.base_weights.recency,
            emotional=self.base_weights.emotional,
            goal=self.base_weights.goal,
            importance=self.base_weights.importance
        )

        # Heuristic: High stress -> prioritize emotional and recent context
        if user_state.stress_level > 70:
            weights.emotional += 0.10
            weights.recency += 0.05
            weights.semantic -= 0.15
            
        # Heuristic: Active projects -> prioritize goal alignment
        if user_state.active_projects:
            weights.goal += 0.10
            weights.semantic -= 0.10

        return weights

    def _calculate_final_score(
        self, 
        query_embedding: List[float], 
        memory: Memory, 
        user_state: UserState,
        weights: RankingWeights
    ) -> float:
        """
        Calculates: final_score = Σ(factor_score * factor_weight)
        """
        # 1. Semantic Similarity (0.0 - 1.0)
        semantic_score = 0.0
        if memory.embedding:
            # Cosine similarity helper (assuming it exists in a utils file or similar)
            from infrastructure.mongodb_repositories import _cosine_similarity
            semantic_score = _cosine_similarity(query_embedding, memory.embedding)

        # 2. Recency Score (Decay function)
        recency_score = self._calculate_recency_score(memory)

        # 3. Emotional Relevance
        emotional_score = self._calculate_emotional_relevance(memory, user_state)

        # 4. Goal Alignment
        goal_score = self._calculate_goal_alignment(memory, user_state)

        # 5. Importance Score (Normalized 0.0 - 1.0)
        importance_score = memory.importance.value / 10.0

        # Weighted Sum
        final_score = (
            (semantic_score * weights.semantic) +
            (recency_score * weights.recency) +
            (emotional_score * weights.emotional) +
            (goal_score * weights.goal) +
            (importance_score * weights.importance)
        )

        return final_score

    def _calculate_recency_score(self, memory: Memory) -> float:
        """Exponential time decay: score = exp(-decay_constant * days_passed)"""
        now = datetime.now(timezone.utc)
        created_at = memory.lifecycle.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
        delta_days = (now - created_at).total_seconds() / 86400.0
        # Decay half-life of 7 days
        decay_constant = 0.1
        return math.exp(-decay_constant * delta_days)

    def _calculate_emotional_relevance(self, memory: Memory, user_state: UserState) -> float:
        """Scores higher if the memory's emotion matches the user's current or dominant emotion."""
        score = 0.0
        memory_emotion = memory.metadata.get("emotion")
        
        if not memory_emotion:
            return 0.5 # Neutral baseline

        if memory_emotion == user_state.current_emotion:
            score = 1.0
        elif memory_emotion == user_state.dominant_emotion:
            score = 0.8
        
        # High stress memories are relevant when current stress is high
        if user_state.stress_level > 60 and memory.metadata.get("stress_level", 0) > 60:
            score = max(score, 0.9)

        return score

    def _calculate_goal_alignment(self, memory: Memory, user_state: UserState) -> float:
        """Scores higher if the memory is related to active goals or projects."""
        if memory.type == MemoryType.GOAL:
            return 1.0
            
        score = 0.0
        content_lower = memory.content.lower()
        
        # Check against active projects
        for project in user_state.active_projects:
            if project.name.lower() in content_lower:
                score = max(score, 0.9)
                
        # Check against recent topics
        for topic in user_state.recent_topics:
            if topic.lower() in content_lower:
                score = max(score, 0.7)
                
        return score
