"""
RL Service — Public Façade
==========================
Wraps RLPolicyEngine and exposes the same interface that
`response_service.py` and `conversation_orchestrator.py` already call,
so zero changes are needed in those files.

Also exposes the new `select_action_vector()` API used by the orchestrator
to get the full 5-dimension action and the prompt instruction string.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Tuple

from core.logger import logger
from services.rl_policy_engine import (
    RLPolicyEngine,
    ActionVector,
    PolicyName,
    compose_reward,
    get_persona_prompt,
    PERSONA_PROMPTS,
)


class RLService:
    """
    Public interface for the RL policy engine.

    Maintains full backward compatibility with the original API
    (`select_persona`, `get_persona_prompt`, `format_experiences`) while
    adding the new multi-dimensional action selection.
    """

    def __init__(self):
        # Engine is lazy-initialised so the DB repo can be injected after
        # startup without circular import issues.
        self._engine: Optional[RLPolicyEngine] = None
        self._initialised = False

    # ── Lifecycle ────────────────────────────────────────────────────

    def initialise(self, repo=None) -> None:
        """
        Wire the MongoDB repo and create the engine.
        Called once from startup_event in main.py.
        """
        from infrastructure.mongodb_repositories import MongoRLRepository
        self._engine = RLPolicyEngine(repo=repo or MongoRLRepository())

    async def load(self) -> None:
        """Restore bandit state from DB. Called after initialise()."""
        if self._engine and not self._initialised:
            await self._engine.load()
            self._initialised = True

    def _get_engine(self) -> RLPolicyEngine:
        if self._engine is None:
            # Fallback: create a memory-only engine (no persistence).
            # This prevents crashes if initialise() was not called.
            logger.warning("RL: Engine not initialised — running memory-only fallback.")
            self._engine = RLPolicyEngine(repo=None)
            asyncio.get_event_loop().run_until_complete(self._engine.load())
        return self._engine

    # ── New API: full action vector ──────────────────────────────────

    async def select_action_vector(
        self, context: Optional[Dict] = None
    ) -> Tuple[ActionVector, PolicyName]:
        """
        Select a full 5-dimension action.
        Returns (ActionVector, PolicyName).
        """
        return await self._get_engine().select_action(context)

    async def record_reward(
        self,
        action:         ActionVector,
        policy_used:    PolicyName,
        reward:         float,
        interaction_id: Optional[str] = None,
    ) -> None:
        """Feed a reward signal back to the bandit."""
        await self._get_engine().record_reward(action, policy_used, reward, interaction_id)

    def build_prompt_instructions(self, action: ActionVector) -> str:
        """Convert action vector → LLM system-prompt instruction block."""
        return self._get_engine().build_prompt_instructions(action)

    def get_policy_report(self) -> Dict:
        """Full policy comparison report (for /rl/stats endpoint)."""
        return self._get_engine().get_policy_report()

    def get_arm_rankings(self) -> Dict:
        """Per-dimension arm rankings (for /rl/rankings endpoint)."""
        return self._get_engine().get_arm_rankings()

    # ── Backward-Compatible API (used by existing orchestrator) ──────

    async def select_persona(self, persona_stats: Dict[str, Dict]) -> str:
        """
        Legacy API — returns just the persona name string.
        persona_stats arg is IGNORED; the bandit handles its own stats.
        """
        action, _ = await self._get_engine().select_action()
        return action.persona.value

    def get_persona_prompt(self, persona_name: str) -> str:
        """Returns the system prompt for a given persona name."""
        return get_persona_prompt(persona_name)

    def format_experiences(self, experiences: List) -> str:
        """Formats successful past interactions as few-shot training examples."""
        if not experiences:
            return ""
        formatted = "\n--- LEARNED EXPERIENCES (High-Rated Past Interactions) ---\n"
        for exp in experiences:
            formatted += f"User: {exp.transcript}\n"
            formatted += f"AI (Successful Response): {exp.response_text}\n\n"
        formatted += "Follow the tone and success of these examples when responding.\n"
        return formatted

    # ── Reward Composition Helper ────────────────────────────────────

    @staticmethod
    def compose_reward(
        user_feedback: Optional[float] = None,
        emotion_before: Optional[str]  = None,
        emotion_after:  Optional[str]  = None,
        session_duration_seconds: Optional[float] = None,
        turn_completed: bool = True,
    ) -> float:
        """Convenience wrapper around compose_reward()."""
        return compose_reward(
            user_feedback=user_feedback,
            emotion_before=emotion_before,
            emotion_after=emotion_after,
            session_duration_seconds=session_duration_seconds,
            turn_completed=turn_completed,
        )


# Module-level singleton
rl_service = RLService()
