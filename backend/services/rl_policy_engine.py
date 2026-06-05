"""
RL Policy Engine — Production-Grade Multi-Armed Bandit System
=============================================================
Replaces the single-dimension persona bandit with a full joint
action space across five independent dimensions.  Three policies
run in parallel so their performance can be compared live.

ACTION SPACE (combinatorial, each dimension is an independent arm)
------------------------------------------------------------------
  persona           : 5 arms
  response_length   : 3 arms  (brief | moderate | detailed)
  questioning_style : 4 arms  (none | open | reflective | socratic)
  motivation_style  : 4 arms  (none | encouragement | challenge | reframe)
  detail_level      : 3 arms  (concise | balanced | thorough)

  Total joint arms = 5 × 3 × 4 × 4 × 3 = 720
  We factorise the problem into 5 independent bandits (one per
  dimension) to keep it tractable — each dimension selects its
  best arm independently, then the actions are composed.

POLICIES (run concurrently, 1 chosen per request by policy_selector)
---------------------------------------------------------------------
  ThompsonSampling  — Beta-distribution posterior, zero hyper-params
  EpsilonGreedy     — Classic ε-greedy with linear decay
  UCB1              — Upper-Confidence-Bound (bonus for low N arms)

REWARD SIGNALS (composited into a single scalar in [−1, +1])
------------------------------------------------------------
  user_feedback     : explicit thumbs up/down    weight 0.40
  sentiment_delta   : emotion improvement        weight 0.30
  session_duration  : normalised engagement time weight 0.20
  turn_engagement   : implicit (response played) weight 0.10

ONLINE LEARNING
---------------
  Every time `record_reward()` is called the posterior / stats
  of the winning arm are updated immediately — no batch step needed.

PERSISTENCE
-----------
  Bandit state (alpha/beta counts, arm means/counts) is stored in
  MongoDB collection `rl_bandit_state` via MongoRLRepository so
  the policy survives server restarts.

POLICY COMPARISON
-----------------
  All three policies are tracked separately.  `get_policy_report()`
  returns per-policy cumulative reward, regret proxy, and win rate
  so you can see which policy is outperforming the others in prod.
"""

from __future__ import annotations

import math
import random
import time
import asyncio
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.logger import logger


# ──────────────────────────────────────────────────────────────────────────────
# ACTION SPACE DEFINITIONS
# ──────────────────────────────────────────────────────────────────────────────

class Persona(str, Enum):
    EMPATHETIC_FRIEND    = "the_empathetic_friend"
    HUMOROUS_FRIEND      = "the_humorous_friend"
    DIRECT_FRIEND        = "the_direct_friend"
    PHILOSOPHICAL_FRIEND = "the_philosophical_friend"
    CHEERLEADER_FRIEND   = "the_cheerleader_friend"


class ResponseLength(str, Enum):
    BRIEF    = "brief"       # 1-2 sentences
    MODERATE = "moderate"    # 2-3 sentences  (default)
    DETAILED = "detailed"    # 3-5 sentences


class QuestioningStyle(str, Enum):
    NONE        = "none"         # No question asked
    OPEN        = "open"         # Open-ended "How did that make you feel?"
    REFLECTIVE  = "reflective"   # Mirror back  "So you're saying…?"
    SOCRATIC    = "socratic"     # Guided discovery "What do you think caused…?"


class MotivationStyle(str, Enum):
    NONE          = "none"
    ENCOURAGEMENT = "encouragement"   # "You've got this."
    CHALLENGE     = "challenge"       # "What would you do if you weren't afraid?"
    REFRAME       = "reframe"         # "What if this is an opportunity?"


class DetailLevel(str, Enum):
    CONCISE   = "concise"    # Key point only
    BALANCED  = "balanced"   # Key point + brief reasoning
    THOROUGH  = "thorough"   # Key point + reasoning + example


@dataclass(frozen=True)
class ActionVector:
    """The full action chosen by the policy for one turn."""
    persona:           Persona
    response_length:   ResponseLength
    questioning_style: QuestioningStyle
    motivation_style:  MotivationStyle
    detail_level:      DetailLevel

    def to_dict(self) -> Dict[str, str]:
        return {
            "persona":           self.persona.value,
            "response_length":   self.response_length.value,
            "questioning_style": self.questioning_style.value,
            "motivation_style":  self.motivation_style.value,
            "detail_level":      self.detail_level.value,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> "ActionVector":
        return cls(
            persona           = Persona(d["persona"]),
            response_length   = ResponseLength(d["response_length"]),
            questioning_style = QuestioningStyle(d["questioning_style"]),
            motivation_style  = MotivationStyle(d["motivation_style"]),
            detail_level      = DetailLevel(d["detail_level"]),
        )


# Ordered lists of arms per dimension — used for indexing
_PERSONA_ARMS:           List[Persona]           = list(Persona)
_RESPONSE_LENGTH_ARMS:   List[ResponseLength]    = list(ResponseLength)
_QUESTIONING_STYLE_ARMS: List[QuestioningStyle]  = list(QuestioningStyle)
_MOTIVATION_STYLE_ARMS:  List[MotivationStyle]   = list(MotivationStyle)
_DETAIL_LEVEL_ARMS:      List[DetailLevel]       = list(DetailLevel)

_ALL_DIMENSIONS: List[Tuple[str, List[Any]]] = [
    ("persona",           _PERSONA_ARMS),
    ("response_length",   _RESPONSE_LENGTH_ARMS),
    ("questioning_style", _QUESTIONING_STYLE_ARMS),
    ("motivation_style",  _MOTIVATION_STYLE_ARMS),
    ("detail_level",      _DETAIL_LEVEL_ARMS),
]


# ──────────────────────────────────────────────────────────────────────────────
# REWARD SIGNAL COMPOSITION
# ──────────────────────────────────────────────────────────────────────────────

_REWARD_WEIGHTS = {
    "user_feedback":     0.40,
    "sentiment_delta":   0.30,
    "session_duration":  0.20,
    "turn_engagement":   0.10,
}

# Sentiment ordinal mapping (higher = more positive)
_EMOTION_VALENCE: Dict[str, float] = {
    "happy": 1.0, "excited": 0.9, "calm": 0.7, "surprised": 0.5,
    "neutral": 0.0,
    "confused": -0.2, "anxious": -0.4, "frustrated": -0.5,
    "sad": -0.6, "angry": -0.7, "fearful": -0.8, "depressed": -0.9,
}


def compose_reward(
    user_feedback: Optional[float] = None,     # −1 / 0 / +1
    emotion_before: Optional[str] = None,
    emotion_after: Optional[str] = None,
    session_duration_seconds: Optional[float] = None,
    turn_completed: bool = True,
) -> float:
    """
    Composite reward in [−1, +1].

    Parameters
    ----------
    user_feedback           : explicit signal from /feedback endpoint (−1 or +1)
    emotion_before          : detected emotion string before this turn
    emotion_after           : detected emotion string after this turn
    session_duration_seconds: how long the current session has lasted
    turn_completed          : was the turn completed without error?
    """
    components: Dict[str, float] = {}

    # 1. Explicit user feedback (most important)
    if user_feedback is not None:
        components["user_feedback"] = max(-1.0, min(1.0, float(user_feedback)))
    else:
        components["user_feedback"] = 0.0  # neutral when unknown

    # 2. Sentiment improvement
    if emotion_before is not None and emotion_after is not None:
        v_before = _EMOTION_VALENCE.get(emotion_before.lower(), 0.0)
        v_after  = _EMOTION_VALENCE.get(emotion_after.lower(), 0.0)
        delta    = v_after - v_before
        components["sentiment_delta"] = max(-1.0, min(1.0, delta))
    else:
        components["sentiment_delta"] = 0.0

    # 3. Session duration (normalise: 10-min session = full credit)
    if session_duration_seconds is not None:
        normalised = min(1.0, session_duration_seconds / 600.0)
        components["session_duration"] = (normalised * 2.0) - 1.0  # map [0,1] → [−1,+1]
    else:
        components["session_duration"] = 0.0

    # 4. Turn engagement (implicit: did the turn complete without error?)
    components["turn_engagement"] = 1.0 if turn_completed else -0.5

    # Weighted sum
    reward = sum(
        _REWARD_WEIGHTS[k] * v for k, v in components.items()
    )
    return round(max(-1.0, min(1.0, reward)), 4)


# ──────────────────────────────────────────────────────────────────────────────
# ARM STATE  (shared by all policies — policies maintain their own counters)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ArmState:
    """Per-arm statistics stored in MongoDB."""
    arm_id:   str           # e.g. "persona::the_empathetic_friend"
    n:        int   = 0     # number of times this arm was pulled
    total:    float = 0.0   # cumulative reward
    mean:     float = 0.0   # running mean reward
    alpha:    float = 1.0   # Beta-posterior successes  (Thompson)
    beta:     float = 1.0   # Beta-posterior failures   (Thompson)
    sq_total: float = 0.0   # sum of reward² (for variance)

    def update(self, reward: float) -> None:
        """Online update of all statistics."""
        self.n       += 1
        self.total   += reward
        self.sq_total += reward * reward
        self.mean     = self.total / self.n
        # Map reward [−1,+1] → [0,1] for Beta posterior
        p = (reward + 1.0) / 2.0
        self.alpha   += p
        self.beta    += (1.0 - p)

    @property
    def variance(self) -> float:
        if self.n < 2:
            return 1.0
        mean_sq = self.sq_total / self.n
        return max(0.0, mean_sq - self.mean ** 2)

    @property
    def ucb(self) -> float:
        """UCB1 score (requires total_pulls to be set externally)."""
        return self.mean  # caller injects bonus

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ArmState":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class PolicyState:
    """State for one policy across all dimensions."""
    policy_name:     str
    arms:            Dict[str, ArmState]    = field(default_factory=dict)
    total_pulls:     int                    = 0
    cumulative_reward: float                = 0.0
    # Epsilon decay (only used by EpsilonGreedy)
    epsilon:         float                  = 0.20
    epsilon_min:     float                  = 0.02
    epsilon_decay:   float                  = 0.9995

    def get_arm(self, arm_id: str) -> ArmState:
        if arm_id not in self.arms:
            self.arms[arm_id] = ArmState(arm_id=arm_id)
        return self.arms[arm_id]

    def record(self, action: ActionVector, reward: float) -> None:
        self.total_pulls      += 1
        self.cumulative_reward += reward
        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        # Update each dimension's arm
        for dim, arms_list in _ALL_DIMENSIONS:
            arm_value = getattr(action, dim).value
            arm_id    = f"{dim}::{arm_value}"
            self.get_arm(arm_id).update(reward)

    def win_rate(self) -> float:
        if self.total_pulls == 0:
            return 0.0
        return (self.cumulative_reward / self.total_pulls + 1.0) / 2.0


# ──────────────────────────────────────────────────────────────────────────────
# SELECTION ALGORITHMS
# ──────────────────────────────────────────────────────────────────────────────

def _thompson_select_arm(arms_list: List[Any], policy_state: PolicyState, dim: str) -> Any:
    """
    Thompson Sampling — sample from Beta(alpha, beta) posterior for each arm
    and return the arm with the highest sample.
    """
    best_arm  = None
    best_draw = -float("inf")
    for arm_value in arms_list:
        arm_id    = f"{dim}::{arm_value.value}"
        arm       = policy_state.get_arm(arm_id)
        draw      = random.betavariate(arm.alpha, arm.beta)
        if draw > best_draw:
            best_draw = draw
            best_arm  = arm_value
    return best_arm


def _epsilon_greedy_select_arm(
    arms_list: List[Any], policy_state: PolicyState, dim: str
) -> Any:
    """
    Epsilon-Greedy with linear decay.
    With probability ε → random arm (explore).
    With probability 1-ε → arm with highest mean reward (exploit).
    """
    if random.random() < policy_state.epsilon:
        return random.choice(arms_list)

    best_arm  = None
    best_mean = -float("inf")
    for arm_value in arms_list:
        arm_id = f"{dim}::{arm_value.value}"
        arm    = policy_state.get_arm(arm_id)
        # Favour arms with high mean AND a small uncertainty bonus to
        # prevent permanent lock-in on an arm pulled only once early on
        adjusted = arm.mean + (0.1 if arm.n < 3 else 0.0)
        if adjusted > best_mean:
            best_mean = adjusted
            best_arm  = arm_value
    return best_arm


def _ucb1_select_arm(
    arms_list: List[Any], policy_state: PolicyState, dim: str
) -> Any:
    """
    UCB1 — always pick the arm maximising mean + exploration bonus.
    bonus = sqrt(2 * ln(total_pulls) / arm_n)
    Unvisited arms get +∞ so they are always tried first.
    """
    total = max(1, policy_state.total_pulls)
    best_arm   = None
    best_score = -float("inf")
    for arm_value in arms_list:
        arm_id = f"{dim}::{arm_value.value}"
        arm    = policy_state.get_arm(arm_id)
        if arm.n == 0:
            score = float("inf")
        else:
            bonus = math.sqrt(2.0 * math.log(total) / arm.n)
            score = arm.mean + bonus
        if score > best_score:
            best_score = score
            best_arm   = arm_value
    return best_arm


# ──────────────────────────────────────────────────────────────────────────────
# POLICY COMPARISON FRAMEWORK
# ──────────────────────────────────────────────────────────────────────────────

class PolicyName(str, Enum):
    THOMPSON        = "thompson_sampling"
    EPSILON_GREEDY  = "epsilon_greedy"
    UCB1            = "ucb1"


_SELECTOR_MAP = {
    PolicyName.THOMPSON:       _thompson_select_arm,
    PolicyName.EPSILON_GREEDY: _epsilon_greedy_select_arm,
    PolicyName.UCB1:           _ucb1_select_arm,
}


# ──────────────────────────────────────────────────────────────────────────────
# POLICY ENGINE  (main public interface)
# ──────────────────────────────────────────────────────────────────────────────

class RLPolicyEngine:
    """
    Production-grade RL Policy Engine.

    Usage
    -----
    engine = RLPolicyEngine(repo=mongo_rl_repo)
    await engine.load()                        # restore state from DB

    action, policy_used = await engine.select_action(context)
    # … run the conversation turn …
    reward = compose_reward(user_feedback=+1, emotion_before="sad", emotion_after="calm")
    await engine.record_reward(action, policy_used, reward, interaction_id)

    report = engine.get_policy_report()        # compare policies
    prompt_instructions = engine.build_prompt_instructions(action)
    """

    def __init__(self, repo=None):
        self._repo = repo  # MongoRLRepository — injected, optional for tests
        self._policies: Dict[PolicyName, PolicyState] = {
            p: PolicyState(policy_name=p.value) for p in PolicyName
        }
        self._active_policy: PolicyName = PolicyName.THOMPSON
        self._lock = asyncio.Lock()
        self._loaded = False

    # ── Persistence ──────────────────────────────────────────────────

    async def load(self) -> None:
        """Restore bandit state from MongoDB. Safe to call on every startup."""
        if self._repo is None:
            logger.info("RL: No repo configured — running in-memory only.")
            self._loaded = True
            return
        try:
            saved = await self._repo.load_state()
            if saved:
                for policy_name_str, policy_data in saved.items():
                    try:
                        pn = PolicyName(policy_name_str)
                    except ValueError:
                        continue
                    ps = self._policies[pn]
                    ps.total_pulls       = policy_data.get("total_pulls", 0)
                    ps.cumulative_reward = policy_data.get("cumulative_reward", 0.0)
                    ps.epsilon           = policy_data.get("epsilon", ps.epsilon)
                    for arm_id, arm_data in policy_data.get("arms", {}).items():
                        ps.arms[arm_id] = ArmState.from_dict(arm_data)
                # Decide which policy is currently winning
                self._active_policy = self._best_policy()
                logger.info(
                    f"RL: State loaded from DB — active policy: {self._active_policy.value}"
                )
        except Exception as e:
            logger.warning(f"RL: Could not load state from DB ({e}). Starting fresh.")
        self._loaded = True

    async def _persist(self) -> None:
        if self._repo is None:
            return
        try:
            snapshot = {}
            for pn, ps in self._policies.items():
                snapshot[pn.value] = {
                    "total_pulls":       ps.total_pulls,
                    "cumulative_reward": ps.cumulative_reward,
                    "epsilon":           ps.epsilon,
                    "arms":              {k: v.to_dict() for k, v in ps.arms.items()},
                }
            await self._repo.save_state(snapshot)
        except Exception as e:
            logger.error(f"RL: Failed to persist state — {e}")

    # ── Policy Selection ─────────────────────────────────────────────

    def _best_policy(self) -> PolicyName:
        """Returns the policy with the highest win-rate (min 10 pulls required)."""
        candidates = [
            (pn, ps.win_rate())
            for pn, ps in self._policies.items()
            if ps.total_pulls >= 10
        ]
        if not candidates:
            return PolicyName.THOMPSON  # safe default before enough data
        return max(candidates, key=lambda x: x[1])[0]

    def _select_policy(self) -> PolicyName:
        """
        Policy router:
          80 % of traffic → current winning policy
          20 % split equally between the other two (exploration across policies)
        """
        roll = random.random()
        if roll < 0.80:
            return self._active_policy
        others = [p for p in PolicyName if p != self._active_policy]
        return random.choice(others)

    # ── Action Selection ─────────────────────────────────────────────

    async def select_action(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ActionVector, PolicyName]:
        """
        Select the best action vector using the chosen policy.

        Parameters
        ----------
        context : optional dict with keys like 'emotion', 'stress_level',
                  'is_first_turn' that can bias warm-start priors (reserved
                  for future context-aware bandits).

        Returns
        -------
        (ActionVector, PolicyName) — the chosen action and which policy made it.
        """
        async with self._lock:
            chosen_policy = self._select_policy()
            selector       = _SELECTOR_MAP[chosen_policy]
            ps             = self._policies[chosen_policy]

            action = ActionVector(
                persona           = selector(_PERSONA_ARMS,           ps, "persona"),
                response_length   = selector(_RESPONSE_LENGTH_ARMS,   ps, "response_length"),
                questioning_style = selector(_QUESTIONING_STYLE_ARMS, ps, "questioning_style"),
                motivation_style  = selector(_MOTIVATION_STYLE_ARMS,  ps, "motivation_style"),
                detail_level      = selector(_DETAIL_LEVEL_ARMS,      ps, "detail_level"),
            )

            logger.info(
                f"RL: [{chosen_policy.value}] "
                f"persona={action.persona.value} "
                f"len={action.response_length.value} "
                f"q={action.questioning_style.value} "
                f"m={action.motivation_style.value} "
                f"d={action.detail_level.value}"
            )
            return action, chosen_policy

    # ── Reward Recording ─────────────────────────────────────────────

    async def record_reward(
        self,
        action:         ActionVector,
        policy_used:    PolicyName,
        reward:         float,
        interaction_id: Optional[str] = None,
    ) -> None:
        """
        Update the bandit state for the policy that took the action.
        Also updates ALL OTHER policies for the same arms so they share
        signal (cooperative update — accelerates learning).
        """
        async with self._lock:
            for pn, ps in self._policies.items():
                ps.record(action, reward)

            # Re-evaluate which policy is best after update
            self._active_policy = self._best_policy()

        # Persist asynchronously (non-blocking)
        asyncio.create_task(self._persist())

        if interaction_id:
            logger.info(
                f"RL: Reward {reward:+.4f} recorded for interaction {interaction_id} "
                f"(policy={policy_used.value})"
            )

    # ── Policy Report ────────────────────────────────────────────────

    def get_policy_report(self) -> Dict[str, Any]:
        """
        Returns a structured comparison report across all three policies.
        Includes per-arm statistics for each dimension.
        """
        report: Dict[str, Any] = {
            "active_policy": self._active_policy.value,
            "policies":      {},
        }

        for pn, ps in self._policies.items():
            arm_summaries: Dict[str, Any] = {}
            for dim, arms_list in _ALL_DIMENSIONS:
                dim_arms = []
                for arm_value in arms_list:
                    arm_id  = f"{dim}::{arm_value.value}"
                    arm     = ps.get_arm(arm_id)
                    dim_arms.append({
                        "arm":      arm_value.value,
                        "pulls":    arm.n,
                        "mean":     round(arm.mean, 4),
                        "alpha":    round(arm.alpha, 2),
                        "beta_val": round(arm.beta, 2),
                        "variance": round(arm.variance, 4),
                    })
                arm_summaries[dim] = sorted(dim_arms, key=lambda x: x["mean"], reverse=True)

            report["policies"][pn.value] = {
                "total_pulls":       ps.total_pulls,
                "cumulative_reward": round(ps.cumulative_reward, 4),
                "win_rate":          round(ps.win_rate(), 4),
                "epsilon":           round(ps.epsilon, 4) if pn == PolicyName.EPSILON_GREEDY else None,
                "arms":              arm_summaries,
            }

        return report

    def get_arm_rankings(self) -> Dict[str, List[Dict]]:
        """
        Returns per-dimension arm rankings aggregated across all policies
        (averaged mean reward).  Useful for dashboards.
        """
        rankings: Dict[str, List[Dict]] = {}
        for dim, arms_list in _ALL_DIMENSIONS:
            rows = []
            for arm_value in arms_list:
                arm_id   = f"{dim}::{arm_value.value}"
                means    = []
                total_n  = 0
                for ps in self._policies.values():
                    arm = ps.get_arm(arm_id)
                    if arm.n > 0:
                        means.append(arm.mean)
                        total_n += arm.n
                rows.append({
                    "arm":           arm_value.value,
                    "avg_mean":      round(sum(means) / len(means), 4) if means else 0.0,
                    "total_pulls":   total_n,
                })
            rankings[dim] = sorted(rows, key=lambda x: x["avg_mean"], reverse=True)
        return rankings

    # ── Prompt Instruction Builder ───────────────────────────────────

    def build_prompt_instructions(self, action: ActionVector) -> str:
        """
        Converts an ActionVector into concrete LLM system-prompt instructions.
        These are injected into `response_service.py` alongside the persona.
        """
        instructions: List[str] = []

        # Response length
        length_map = {
            ResponseLength.BRIEF:    "Keep your response to 1-2 sentences maximum.",
            ResponseLength.MODERATE: "Keep your response to 2-3 sentences.",
            ResponseLength.DETAILED: "Use 3-5 sentences. Include a brief reasoning or example.",
        }
        instructions.append(length_map[action.response_length])

        # Questioning style
        question_map = {
            QuestioningStyle.NONE:       "",
            QuestioningStyle.OPEN:       "End with one open-ended question to invite them to share more.",
            QuestioningStyle.REFLECTIVE: "Include a reflective question that mirrors what they said back to them.",
            QuestioningStyle.SOCRATIC:   "Include a Socratic question that gently guides them to their own insight.",
        }
        q_instr = question_map[action.questioning_style]
        if q_instr:
            instructions.append(q_instr)

        # Motivation style
        motivation_map = {
            MotivationStyle.NONE:          "",
            MotivationStyle.ENCOURAGEMENT: "Include a brief, genuine word of encouragement.",
            MotivationStyle.CHALLENGE:     "Gently challenge them with a thought-provoking perspective.",
            MotivationStyle.REFRAME:       "Offer a positive reframe of their situation.",
        }
        m_instr = motivation_map[action.motivation_style]
        if m_instr:
            instructions.append(m_instr)

        # Detail level
        detail_map = {
            DetailLevel.CONCISE:  "Be concise — give the core message only.",
            DetailLevel.BALANCED: "Give the core message and one supporting reason.",
            DetailLevel.THOROUGH: "Give the core message, a reason, and a concrete example or analogy.",
        }
        instructions.append(detail_map[action.detail_level])

        return "\n".join(f"- {i}" for i in instructions if i)

    # ── Warm-Start Context Priors ─────────────────────────────────────

    def warm_start_from_emotion(self, emotion: str, stress_level: int) -> Dict[str, Any]:
        """
        Returns a suggested action bias based on emotion context.
        Used as a soft prior hint — does NOT override the bandit selection.
        Only meaningful before any data is collected (n=0 arms).
        """
        is_distressed = stress_level > 65 or emotion in {
            "sad", "angry", "anxious", "fearful", "depressed", "frustrated"
        }
        if is_distressed:
            return {
                "persona_hint":           Persona.EMPATHETIC_FRIEND.value,
                "response_length_hint":   ResponseLength.MODERATE.value,
                "questioning_style_hint": QuestioningStyle.REFLECTIVE.value,
                "motivation_style_hint":  MotivationStyle.ENCOURAGEMENT.value,
                "detail_level_hint":      DetailLevel.BALANCED.value,
            }
        return {
            "persona_hint":           Persona.CHEERLEADER_FRIEND.value,
            "response_length_hint":   ResponseLength.BRIEF.value,
            "questioning_style_hint": QuestioningStyle.OPEN.value,
            "motivation_style_hint":  MotivationStyle.NONE.value,
            "detail_level_hint":      DetailLevel.CONCISE.value,
        }


# ──────────────────────────────────────────────────────────────────────────────
# PERSONA PROMPT REGISTRY  (expanded with full action vector)
# ──────────────────────────────────────────────────────────────────────────────

PERSONA_PROMPTS: Dict[str, str] = {
    Persona.EMPATHETIC_FRIEND.value: (
        "You are a deeply empathetic friend. "
        "Your primary focus is validation and active listening. "
        "Let the user feel truly heard before offering any advice."
    ),
    Persona.HUMOROUS_FRIEND.value: (
        "You are a witty, humorous friend. "
        "Use lighthearted observations and gentle jokes to lift the mood, "
        "but never at the user's expense."
    ),
    Persona.DIRECT_FRIEND.value: (
        "You are a direct, honest friend. "
        "Cut straight to practical advice and honest perspectives. "
        "Avoid filler — say exactly what needs to be said."
    ),
    Persona.PHILOSOPHICAL_FRIEND.value: (
        "You are a thoughtful, philosophical friend. "
        "Explore the deeper meaning and broader context of what they share. "
        "Offer wisdom, not just comfort."
    ),
    Persona.CHEERLEADER_FRIEND.value: (
        "You are an ultra-supportive cheerleader. "
        "Radiate belief in the user's ability to handle whatever they face. "
        "Focus on strengths, wins, and possibilities."
    ),
}


def get_persona_prompt(persona: str) -> str:
    return PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS[Persona.EMPATHETIC_FRIEND.value])
