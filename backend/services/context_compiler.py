import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from domain.entities import UserState, WorkingMemory, Memory, Reflection
from domain.value_objects import CompiledContext, ConversationPlan, ConversationStrategy
from core.logger import logger

class ContextCompiler:
    """
    Compiles disparate cognitive inputs into a token-efficient, 
    deduplicated, and prioritized context for the LLM.
    """
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.char_per_token = 4 # Heuristic: ~4 chars per token

    def compile(
        self,
        user_state: UserState,
        working_memory: WorkingMemory,
        memories: Dict[str, List[Memory]],
        planner_output: ConversationPlan,
        emotion_profile: dict,
        reflections: Optional[List[Reflection]] = None,
        prior_stress: int = 50
    ) -> CompiledContext:
        """
        Orchestrates the compilation process.
        """
        logger.info("ContextCompiler: Compiling cognitive context")
        
        # 1. Compile Emotional State
        emotional_state = self._compile_emotional_state(emotion_profile, user_state, prior_stress)
        
        # 2. Compile User Summary & State
        user_summary = self._compile_user_summary(user_state)
        current_state = self._compile_current_state(working_memory)
        
        # 3. Compile Goals
        active_goals = self._compile_goals(user_state, working_memory)
        
        # 4. Compile Strategy & Constraints
        planner_strategy, response_constraints = self._compile_strategy(planner_output)
        
        # 5. Compile and Prioritize Memories (RAG + Reflections)
        relevant_memories = self._compile_memories(memories, reflections)
        
        # 6. Final Deduplication and Token Pruning
        # (This is where we'd check total tokens and trim if necessary)
        
        total_text = (
            user_summary + current_state + relevant_memories + 
            active_goals + emotional_state + planner_strategy + response_constraints
        )
        estimated_tokens = len(total_text) // self.char_per_token
        
        return CompiledContext(
            user_summary=user_summary,
            current_state=current_state,
            relevant_memories=relevant_memories,
            active_goals=active_goals,
            emotional_state=emotional_state,
            planner_strategy=planner_strategy,
            response_constraints=response_constraints,
            total_estimated_tokens=estimated_tokens
        )

    def _compile_emotional_state(self, profile: dict, state: UserState, prior_stress: int = 50) -> str:
        """Fuses real-time profile with persistent state trends and calculates delta."""
        emotion = profile.get("emotion", "neutral").upper()
        tone = profile.get("tone", "calm")
        stress = profile.get("stress_level", 50)
        
        trend = f"TREND: {state.dominant_emotion}"
        stress_delta = stress - prior_stress
        if stress_delta > 20:
            trend += f" | ALERT: User stress level has surged significantly by {stress_delta}% since last turn!"
        
        return f"EMOTION: {emotion} | TONE: {tone} | STRESS: {stress}/100 | {trend}"

    def _compile_user_summary(self, state: UserState) -> str:
        """Brief summary of the user's interaction style and recent context."""
        topics = ", ".join(state.recent_topics[:3])
        return f"STYLE: {state.preferred_interaction_style} | PERSONA: {state.preferred_persona} | RECENT: {topics}"

    def _compile_current_state(self, wm: WorkingMemory) -> str:
        """Active session focus from working memory."""
        project = wm.active_project or "General chat"
        topic = wm.active_topic or "None"
        decisions = " | ".join([d.content for d in wm.recent_decisions[-2:]])
        return f"PROJECT: {project} | TOPIC: {topic} | RECENT DECISIONS: {decisions}"

    def _compile_goals(self, state: UserState, wm: WorkingMemory) -> str:
        """Merge long-term state goals with short-term working memory tasks."""
        goals = [g.description for g in state.current_goals if not g.is_completed]
        tasks = [t.description for t in wm.recent_tasks if t.status == "pending"]
        
        # Deduplicate and limit
        combined = list(dict.fromkeys(goals + tasks))[:5]
        return " | ".join(combined) if combined else "None"

    def _compile_strategy(self, plan: ConversationPlan) -> tuple:
        """Extract strategy and behavioral constraints."""
        strategy = f"STRATEGY: {plan.conversation_strategy.value.upper()} | GOAL: {plan.response_goal}"
        
        constraints = []
        if plan.risk_level > 3:
            constraints.append("Handle with extreme sensitivity.")
        if plan.confidence < 0.4:
            constraints.append("Be cautious; intent unclear.")
            
        # Strategy-specific behavioral micro-instructions
        from domain.value_objects import ConversationStrategy
        strat = plan.conversation_strategy
        if strat == ConversationStrategy.COACHING:
            constraints.append("Ask powerful open-ended questions. Don't give answers; help them find their own.")
        elif strat == ConversationStrategy.TEACHING:
            constraints.append("Break down concepts simply. Use analogies. Check for understanding.")
        elif strat == ConversationStrategy.EMOTIONAL_SUPPORT:
            constraints.append("Focus entirely on validation and empathy. 'I hear you' and 'That sounds really tough' are your tools.")
        elif strat == ConversationStrategy.DEBUGGING:
            constraints.append("Be systematic. Identify the error, isolate the cause, and test solutions one by one.")
        elif strat == ConversationStrategy.BRAINSTORMING:
            constraints.append("Say 'Yes, and...'. Encourage wild ideas. Don't judge too early.")
        elif strat == ConversationStrategy.MOTIVATION:
            constraints.append("High energy, focus on the 'why', and celebrate small wins.")
        elif strat == ConversationStrategy.CASUAL:
            constraints.append("Keep it low-key and friendly. No pressure.")

        return strategy, " ".join(constraints)

    def _compile_memories(self, memories: Dict[str, List[Memory]], reflections: Optional[List[Reflection]]) -> str:
        """Prioritize, deduplicate, and format memories."""
        formatted = []
        seen_content = set()
        
        # 1. Prioritize Reflections (High-level insights)
        if reflections:
            for r in reflections[:3]:
                if r.content not in seen_content:
                    content = r.content.strip()
                    if len(content) > 150:
                        content = content[:147] + "..."
                    formatted.append(f"[INSIGHT] {content}")
                    seen_content.add(r.content)
        
        # 2. Prioritize specific memory types
        priority_order = ["preference", "goal", "emotional", "episodic"]
        
        for m_type in priority_order:
            items = memories.get(m_type, [])
            for m in items[:3]: # Limit per type for token efficiency
                content = m.content.strip()
                if content not in seen_content:
                    formatted_content = content
                    if len(formatted_content) > 150:
                        formatted_content = formatted_content[:147] + "..."
                    formatted.append(f"[{m_type.upper()}] {formatted_content}")
                    seen_content.add(content)
                    
        return "\n".join(formatted)
