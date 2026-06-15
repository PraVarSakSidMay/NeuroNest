import unittest
from datetime import datetime, timezone, timedelta

from domain.entities import Memory, UserState
from domain.value_objects import MemoryType, MemoryImportance, EmotionEnum
from services.context_ranking_engine import ContextRankingEngine

class TestContextRankingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ContextRankingEngine()
        self.user_state = UserState(user_id="test_user")

    def test_ranking_by_importance(self):
        # Create two memories, identical except for importance
        m1 = Memory.create(
            user_id="test_user",
            type=MemoryType.EPISODIC,
            content="Memory 1",
            importance=MemoryImportance.LOW
        )
        m2 = Memory.create(
            user_id="test_user",
            type=MemoryType.EPISODIC,
            content="Memory 2",
            importance=MemoryImportance.CRITICAL
        )
        
        # Add mock embeddings (identical)
        m1.embedding = [0.1] * 1536
        m2.embedding = [0.1] * 1536
        query_embedding = [0.1] * 1536
        
        ranked = self.engine.rank_memories(query_embedding, [m1, m2], self.user_state)
        
        self.assertEqual(ranked[0].id, m2.id)
        self.assertEqual(ranked[1].id, m1.id)

    def test_ranking_by_recency(self):
        # Create two memories, one recent, one old
        m_old = Memory.create(user_id="test_user", type=MemoryType.EPISODIC, content="Old")
        m_old.lifecycle.created_at = datetime.now(timezone.utc) - timedelta(days=30)
        
        m_new = Memory.create(user_id="test_user", type=MemoryType.EPISODIC, content="New")
        m_new.lifecycle.created_at = datetime.now(timezone.utc)
        
        m_old.embedding = [0.1] * 1536
        m_new.embedding = [0.1] * 1536
        query_embedding = [0.1] * 1536
        
        ranked = self.engine.rank_memories(query_embedding, [m_old, m_new], self.user_state)
        
        self.assertEqual(ranked[0].id, m_new.id)

    def test_dynamic_weighting_high_stress(self):
        # High stress should prioritize emotional memories
        self.user_state.stress_level = 90
        self.user_state.current_emotion = EmotionEnum.ANXIOUS
        
        m_neutral = Memory.create(user_id="test_user", type=MemoryType.EPISODIC, content="Neutral")
        m_neutral.metadata["emotion"] = "neutral"
        
        m_emotional = Memory.create(user_id="test_user", type=MemoryType.EMOTIONAL, content="Stress trigger")
        m_emotional.metadata["emotion"] = "anxious"
        m_emotional.metadata["stress_level"] = 80
        
        m_neutral.embedding = [0.1] * 1536
        m_emotional.embedding = [0.1] * 1536
        query_embedding = [0.1] * 1536
        
        ranked = self.engine.rank_memories(query_embedding, [m_neutral, m_emotional], self.user_state)
        
        self.assertEqual(ranked[0].id, m_emotional.id)
