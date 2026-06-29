
import json
from typing import Optional, List
from datetime import datetime, timezone
from domain.entities import WorkingMemory, Interaction
from domain.value_objects import Task, EntityMention, Decision
from infrastructure.repositories import IWorkingMemoryRepository
from services.model_manager import ModelManager
from core.logger import logger

class WorkingMemoryService:
    """
    Application Service for managing short-term Working Memory.
    Handles updates, pruning, and LLM-based summarization of active context.
    """
    
    def __init__(
        self, 
        working_repo: IWorkingMemoryRepository, 
        model_manager: ModelManager
    ):
        self.working_repo = working_repo
        self.model_manager = model_manager
        self.window_limit = 15  # Turns before summarization/pruning

    async def get_memory(self, user_id: str, session_id: str) -> WorkingMemory:
        """Fetch working memory, creating a fresh one if needed."""
        memory = await self.working_repo.get_by_session(user_id, session_id)
        if not memory:
            memory = WorkingMemory.create(user_id, session_id)
            await self.working_repo.update(memory)
        return memory

    async def update_from_interaction(
        self, 
        user_id: str, 
        session_id: str, 
        interaction: Interaction,
        pre_extracted_updates: Optional[dict] = None
    ) -> WorkingMemory:
        """
        Updates working memory based on a new interaction.
        Uses the LLM to extract tasks, entities, and decisions.
        """
        memory = await self.get_memory(user_id, session_id)
        memory.turn_count += 1
        
        # 1. Extraction via LLM or Pre-extracted Updates
        if pre_extracted_updates and isinstance(pre_extracted_updates, dict):
            updates = pre_extracted_updates
            logger.info("WorkingMemory: Using pre-extracted updates, skipping background LLM call.")
        else:
            updates = await self._extract_working_context(interaction, memory)
        
        # 2. Apply Updates
        memory.active_project = updates.get("active_project") or memory.active_project
        memory.active_problem = updates.get("active_problem") or memory.active_problem
        memory.active_topic = updates.get("active_topic") or memory.active_topic
        memory.current_goal = updates.get("current_goal") or memory.current_goal
        
        # Merge Tasks
        for t_desc in updates.get("new_tasks", []):
            memory.recent_tasks.append(Task(description=t_desc, turn_id=memory.turn_count))
            
        # Merge Decisions
        for d_data in updates.get("new_decisions", []):
            memory.recent_decisions.append(Decision(
                content=d_data["content"], 
                rationale=d_data.get("rationale"), 
                turn_id=memory.turn_count
            ))
            
        # Merge Entities (with frequency tracking)
        for e_data in updates.get("entities", []):
            found = False
            for existing in memory.recent_entities:
                if existing.name.lower() == e_data["name"].lower():
                    existing.count += 1
                    existing.last_mentioned_turn = memory.turn_count
                    found = True
                    break
            if not found:
                memory.recent_entities.append(EntityMention(
                    name=e_data["name"], 
                    type=e_data["type"], 
                    last_mentioned_turn=memory.turn_count
                ))

        # 3. Pruning & Summarization if window exceeded
        if memory.turn_count >= self.window_limit:
            await self._prune_and_summarize(memory)

        memory.last_updated = datetime.now(timezone.utc)
        await self.working_repo.update(memory)
        return memory

    async def _extract_working_context(self, interaction: Interaction, memory: WorkingMemory) -> dict:
        """Calls LLM to parse the interaction for working memory updates, with heuristic batching."""
        transcript_lower = interaction.transcript.lower()
        keywords = ["todo", "task", "decide", "decision", "project", "goal", "solve", "plan", "finish", "done", "complete", "need to"]
        has_keywords = any(kw in transcript_lower for kw in keywords)
        
        # Trigger LLM extraction only if keywords are found or on every 3rd turn
        if has_keywords or (memory.turn_count % 3 == 0):
            prompt = f"""
            You are a Working Memory Extractor. Analyze the current turn and update the working context.
            
            CURRENT CONTEXT:
            - Active Project: {memory.active_project}
            - Active Problem: {memory.active_problem}
            - Current Goal: {memory.current_goal}
            
            NEW TURN:
            - User: "{interaction.transcript}"
            - AI: "{interaction.response_text}"
            
            TASK:
            Identify if any of the following changed or were mentioned:
            1. active_project: The high-level project (e.g., "Building a birdhouse").
            2. active_problem: The specific roadblock (e.g., "Missing nails").
            3. active_topic: The current subject of talk.
            4. current_goal: What the user is trying to achieve right now.
            5. new_tasks: Specific actionable items mentioned.
            6. new_decisions: Choices made by the user.
            7. entities: Named entities (People, Tech, Places).
            
            Return JSON strictly in this format:
            {{
              "active_project": "string or null",
              "active_problem": "string or null",
              "active_topic": "string or null",
              "current_goal": "string or null",
              "new_tasks": ["string"],
              "new_decisions": [{{ "content": "string", "rationale": "string" }}],
              "entities": [{{ "name": "string", "type": "string" }}]
            }}
            """
            
            try:
                response = self.model_manager.get_llm_response(
                    transcript=interaction.transcript,
                    system_prompt=prompt,
                    json_mode=True
                )
                from core.utils import parse_robust_json
                parsed = parse_robust_json(response)
                if isinstance(parsed, dict):
                    return parsed
                return {}
            except Exception as e:
                logger.error(f"WorkingMemory: LLM extraction failed: {e}")
                return {}
        else:
            # Lightweight programmatic entity extraction
            entities = []
            tech_keywords = ["python", "react", "mongodb", "supabase", "docker", "git", "fastapi", "next.js", "nodejs", "sql", "openai", "gemini"]
            for word in interaction.transcript.split():
                clean_word = word.strip(".,?!()\"'").lower()
                if clean_word in tech_keywords:
                    entities.append({"name": clean_word.capitalize(), "type": "Technology"})
                elif word.istitle() and len(clean_word) > 3:
                    entities.append({"name": clean_word.capitalize(), "type": "Concept"})

            return {
                "active_project": None,
                "active_problem": None,
                "active_topic": None,
                "current_goal": None,
                "new_tasks": [],
                "new_decisions": [],
                "entities": entities[:3]
            }

    async def _prune_and_summarize(self, memory: WorkingMemory):
        """
        Keeps working memory within bounds.
        1. Prunes old tasks/decisions/entities (older than 10 turns).
        2. Summarizes the long-term context if it's getting too complex.
        """
        current_turn = memory.turn_count
        
        # Prune old entities not mentioned in last 10 turns
        memory.recent_entities = [e for e in memory.recent_entities if current_turn - e.last_mentioned_turn < 10]
        
        # Prune tasks older than 15 turns
        memory.recent_tasks = memory.recent_tasks[-10:]
        
        # Prune decisions older than 15 turns
        memory.recent_decisions = memory.recent_decisions[-10:]
        
        logger.info(f"WorkingMemory: Pruned state for session {memory.session_id}")
