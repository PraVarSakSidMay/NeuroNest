
from typing import List, Optional, Dict
from datetime import datetime, timezone
from domain.value_objects import MemoryType, MemoryImportance
from infrastructure.repositories import IMemoryRepository
from services.rag_service import RAGService
from services.memory_lifecycle_service import MemoryLifecycleService
from services.context_ranking_engine import ContextRankingEngine
from domain.entities import Memory, UserState
from core.logger import logger

class UnifiedMemoryService:
    """
    Primary Application Service for the Multi-Layer Memory System.
    Orchestrates ingestion, retrieval, and contextualization of all memory types.
    """
    
    def __init__(
        self, 
        memory_repo: IMemoryRepository, 
        rag_service: RAGService,
        lifecycle_service: MemoryLifecycleService,
        ranking_engine: ContextRankingEngine
    ):
        self.memory_repo = memory_repo
        self.rag_service = rag_service
        self.lifecycle_service = lifecycle_service
        self.ranking_engine = ranking_engine

    async def add_memory(
        self, 
        user_id: str, 
        type: MemoryType, 
        content: str, 
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Ingests a new memory, generates its embedding, and sets its lifecycle.
        """
        memory = Memory.create(
            user_id=user_id,
            type=type,
            content=content,
            importance=importance,
            metadata=metadata
        )
        
        # 1. Set Expiration based on policy
        memory.lifecycle.expires_at = self.lifecycle_service.calculate_expiration(type, importance)
        
        # 2. Generate Embedding for vector search
        memory.embedding = await asyncio.get_event_loop().run_in_executor(
            None, self.rag_service.generate_embedding, content
        )
        
        # 3. Save to Repository
        return await self.memory_repo.save(memory)

    async def get_contextual_memories(
        self, 
        user_id: str, 
        query_text: str, 
        user_state: UserState,
        k: int = 15
    ) -> Dict[str, List[Memory]]:
        """
        Retrieves relevant memories across all layers and applies the Context Ranking Engine.
        Returns a grouped dictionary of the highest-scoring memories.
        """
        embedding = await asyncio.get_event_loop().run_in_executor(
            None, self.rag_service.generate_embedding, query_text
        )
        if not embedding:
            return {}
            
        # 1. Broad Retrieval (k is larger for the reranking stage)
        candidates = await self.memory_repo.find_relevant(
            user_id=user_id,
            embedding=embedding,
            k=k
        )
        
        # 2. Reranking Pipeline
        ranked_memories = self.ranking_engine.rank_memories(
            query_embedding=embedding,
            memories=candidates,
            user_state=user_state,
            limit=5  # Final top-k context window
        )
        
        # 3. Group by type and update access count
        grouped = {}
        for m in ranked_memories:
            m.access() # Track access for lifecycle decay
            await self.memory_repo.save(m)
            
            m_type = m.type.value
            if m_type not in grouped:
                grouped[m_type] = []
            grouped[m_type].append(m)
            
        return grouped

    async def extract_and_store_memories(self, user_id: str, transcript: str, ai_response: str, emotion_data: dict):
        """
        Analyzes a turn and automatically extracts different memory types.
        In a production system, this would use a small LLM call to categorize insights.
        """
        # 1. Store turn as Episodic Memory
        await self.add_memory(
            user_id=user_id,
            type=MemoryType.EPISODIC,
            content=f"User said: {transcript}. I responded: {ai_response}",
            importance=MemoryImportance.MEDIUM,
            metadata={"emotion": emotion_data.get("emotion")}
        )
        
        # 2. Extract Emotional Trend Memory if significant
        if emotion_data.get("stress_level", 0) > 75:
            await self.add_memory(
                user_id=user_id,
                type=MemoryType.EMOTIONAL,
                content=f"User showed high stress ({emotion_data['stress_level']}) when discussing: {transcript}",
                importance=MemoryImportance.HIGH
            )
            
import asyncio
