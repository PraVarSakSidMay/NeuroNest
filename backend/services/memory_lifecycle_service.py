
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from domain.entities import Memory
from domain.value_objects import MemoryType, MemoryImportance
from infrastructure.repositories import IMemoryRepository
from core.logger import logger

class MemoryLifecycleService:
    """
    Manages the 'health' of the memory system.
    Handles expiration, importance decay, and identifies candidates for consolidation.
    """
    
    def __init__(self, memory_repo: IMemoryRepository):
        self.memory_repo = memory_repo

    async def run_cleanup(self):
        """Removes expired memories from the system."""
        expired = await self.memory_repo.get_expired_memories()
        count = 0
        for m in expired:
            if await self.memory_repo.delete(m.id):
                count += 1
        logger.info(f"Memory Cleanup: Removed {count} expired memories.")
        return count

    async def consolidate_episodic_memories(self, user_id: str):
        """
        Identifies high-access episodic memories and marks them for LLM-based reflection.
        This is a precursor to creating 'Reflection Memory' types.
        """
        candidates = await self.memory_repo.get_consolidation_candidates(MemoryType.EPISODIC)
        # In a real system, these would be passed to an LLM to generate a summary/reflection
        # For now, we just mark them as consolidated
        for m in candidates:
            m.lifecycle.is_consolidated = True
            await self.memory_repo.save(m)
        
        logger.info(f"Memory Consolidation: Processed {len(candidates)} candidates for user {user_id}.")
        return candidates

    def calculate_expiration(self, type: MemoryType, importance: MemoryImportance) -> Optional[datetime]:
        """Calculates expiration dates based on memory type and importance."""
        now = datetime.now(timezone.utc)
        
        # Critical memories never expire
        if importance == MemoryImportance.CRITICAL:
            return None
            
        # Retention policies
        if type == MemoryType.EPISODIC:
            days = 7 * importance.value  # Low=7d, High=35d
            return now + timedelta(days=days)
        elif type == MemoryType.EMOTIONAL:
            days = 14 * importance.value
            return now + timedelta(days=days)
        
        # Goals, Preferences, and Reflections are persistent by default
        return None
