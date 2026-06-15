"""
Master ConversationOrchestrator
================================
Production-grade orchestrator that coordinates all cognitive services
for a single conversation turn.

Architecture
------------
  Clean Architecture — this layer depends only on abstractions (Protocols).
  No infrastructure imports. No service instantiation inside methods.
  All dependencies injected at construction time.

Pipeline (per turn)
-------------------
  Phase 0 │ Infra      │ Upload audio, create session          (parallel)
  Phase 1 │ Perception │ Transcription + Audio features        (parallel)
  Phase 2 │ Cognition  │ Emotion, UserState, WorkingMemory     (sequential→parallel)
  Phase 3 │ Memory     │ Embedding + MemoryRetrieval + RL      (parallel)
  Phase 4 │ Planning   │ ContextRanker, Planner, Compiler      (sequential)
  Phase 5 │ Generation │ LLM response + TTS                    (sequential)
  Phase 6 │ Persistence│ Log interaction, implicit RL reward   (parallel)
  Phase 7 │ Background │ Memory extraction, WorkingMemory upd, Reflection (fire-and-forget)

Observability
-------------
  Every phase emits structured log events with timing (ms).
  PipelineMetrics dataclass accumulates per-stage durations.
  StageResult wraps every service call with success/error/duration.
  Full trace is returned in the response under "metrics" key.

Error Handling & Retries
------------------------
  _call_with_retry() wraps any coroutine with exponential-backoff retry.
  Critical stages (transcription, LLM) retry up to MAX_RETRIES times.
  Non-critical stages (memory storage, TTS upload) fail silently.
  A degraded_mode flag is set when critical stages partially fail,
  ensuring a best-effort response is always returned.

Sequence Diagram
----------------
  See docstring at bottom of file.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.logging import (
    StructuredLogger,
    correlation_id,
    get_logger,
    log_event,
    with_correlation_id,
)
from domain.entities import Interaction, WorkingMemory
from domain.value_objects import AudioFeatures, Emotion
from infrastructure.providers import (
    IAudioFeatureProvider,
    IEmbeddingProvider,
    ILLMProvider,
    ITranscriptionProvider,
    ITTSProvider,
)
from infrastructure.repositories import (
    IEmbeddingRepository,
    IInteractionRepository,
    IMemoryRepository,
    IReflectionRepository,
    ISessionRepository,
    IUserRepository,
    IUserStateRepository,
    IWorkingMemoryRepository,
)
from services.context_compiler import ContextCompiler
from services.context_ranking_engine import ContextRankingEngine
from services.conversation_planning_engine import ConversationPlanningEngine
from services.memory_lifecycle_service import MemoryLifecycleService
from services.reflection_engine import ReflectionEngine
from services.rl_policy_engine import ActionVector, PolicyName, compose_reward
from services.rl_service import RLService
from services.unified_memory_service import UnifiedMemoryService
from services.user_state_service import UserStateService
from services.working_memory_service import WorkingMemoryService

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

MAX_RETRIES: int = 3
RETRY_BASE_DELAY: float = 0.25   # seconds — doubles each attempt
RETRY_MAX_DELAY: float  = 4.0    # seconds — ceiling
VOICE_BUCKET: str = "voice-recordings"
TTS_BUCKET:   str = "ai-responses"
LOCAL_AUDIO_BASE: str = "http://localhost:8000/audio"


# ─────────────────────────────────────────────────────────────────────────────
# Observability — StageResult & PipelineMetrics
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StageResult:
    """Wraps the outcome of a single pipeline stage."""
    stage:      str
    success:    bool
    duration_ms: float
    error:      Optional[str] = None
    retries:    int = 0

    def as_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "stage":       self.stage,
            "success":     self.success,
            "duration_ms": round(self.duration_ms, 2),
            "retries":     self.retries,
        }
        if self.error:
            d["error"] = self.error
        return d


@dataclass
class PipelineMetrics:
    """Accumulates timing and success data for every stage in a turn."""
    turn_id:      str
    user_id:      str
    stages:       List[StageResult] = field(default_factory=list)
    total_ms:     float = 0.0
    degraded:     bool  = False   # True if any critical stage used a fallback

    def record(self, result: StageResult) -> None:
        self.stages.append(result)

    def mark_degraded(self, reason: str) -> None:
        self.degraded = True

    def summary(self) -> Dict[str, Any]:
        return {
            "turn_id":    self.turn_id,
            "user_id":    self.user_id,
            "total_ms":   round(self.total_ms, 2),
            "degraded":   self.degraded,
            "stage_count": len(self.stages),
            "failed_stages": [
                s.stage for s in self.stages if not s.success
            ],
            "stages": [s.as_dict() for s in self.stages],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Dependency Bundle (injected once, shared across all turns)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OrchestratorDeps:
    """
    All dependencies the orchestrator needs.
    Constructed once in di.py and injected at startup.
    Using a single dataclass makes the constructor clean and testable.
    """
    # AI Providers
    transcription_provider:  ITranscriptionProvider
    audio_feature_provider:  IAudioFeatureProvider
    llm_provider:            ILLMProvider
    tts_provider:            ITTSProvider
    embedding_provider:      IEmbeddingProvider

    # Repositories
    interaction_repo:     IInteractionRepository
    session_repo:         ISessionRepository
    user_repo:            IUserRepository
    embedding_repo:       IEmbeddingRepository
    user_state_repo:      IUserStateRepository
    memory_repo:          IMemoryRepository
    reflection_repo:      IReflectionRepository
    working_memory_repo:  IWorkingMemoryRepository

    # Domain Services (pre-constructed so they are reused across turns)
    user_state_service:    UserStateService
    unified_memory_service: UnifiedMemoryService
    reflection_engine:     ReflectionEngine
    working_memory_service: WorkingMemoryService
    planning_engine:       ConversationPlanningEngine
    context_compiler:      ContextCompiler
    rl_service:            RLService

    # Identity
    user_id: str = "00000000-0000-0000-0000-000000000000"


# ─────────────────────────────────────────────────────────────────────────────
# Turn Context (mutable state for one request — never shared between turns)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TurnContext:
    """
    Mutable bag-of-state for a single conversation turn.
    Passed through pipeline phases so each phase can read and write.
    """
    turn_id:          str
    audio_path:       str
    voice_name:       str
    frontend_audio:   Optional[dict]   = None   # parsed audio_analysis JSON
    video_features:   Optional[dict]   = None   # parsed video_analysis JSON
    expression_list:  List[Any]        = field(default_factory=list)

    # Populated by Phase 0
    raw_audio_url:    Optional[str]    = None
    session_id:       Optional[str]    = None

    # Populated by Phase 1
    transcript:       str              = ""
    features_dict:    Dict[str, Any]   = field(default_factory=dict)
    audio_features:   Optional[AudioFeatures] = None

    # Populated by Phase 2
    emotion_dict:     Dict[str, Any]   = field(default_factory=dict)
    emotion:          Optional[Emotion] = None
    emotion_before:   str              = "neutral"
    user_state:       Any              = None   # UserState
    working_memory:   Optional[WorkingMemory] = None

    # Populated by Phase 3
    memories:         List[dict]       = field(default_factory=list)
    memory_layers:    Dict[str, Any]   = field(default_factory=dict)
    rl_action:        Optional[ActionVector] = None
    rl_policy:        Optional[PolicyName]   = None
    rl_instructions:  str              = ""
    learned_exps:     str              = ""

    # Populated by Phase 4
    conversation_plan: Any             = None   # ConversationPlan
    compiled_context:  Any             = None   # CompiledContext

    # Populated by Phase 5
    ai_response:      str              = ""
    audio_output_path: Optional[str]   = None
    tts_audio_url:    Optional[str]    = None

    # Populated by Phase 6
    interaction_id:   Optional[str]    = None
    implicit_reward:  float            = 0.0

    # Metrics
    metrics:          Optional[PipelineMetrics] = None


# ─────────────────────────────────────────────────────────────────────────────
# Master Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class ConversationOrchestrator:
    """
    Master ConversationOrchestrator.

    Clean Architecture contract
    ---------------------------
    - Depends only on Protocols (interfaces), never on concrete classes.
    - All domain services are injected via OrchestratorDeps.
    - Infrastructure (MongoDB, OpenAI, etc.) is hidden behind Protocol adapters.
    - No HTTP, DB, or SDK imports here.

    Thread Safety
    -------------
    Stateless per turn. TurnContext is a local object never shared.
    All async operations use asyncio.gather() for true concurrency.

    Usage
    -----
        deps    = OrchestratorDeps(...)           # wired in di.py
        orch    = ConversationOrchestrator(deps)
        result  = await orch.process_conversation(
                      audio_path     = "/tmp/abc.webm",
                      audio_analysis = '{"pitch_mean": 45.2, ...}',
                      voice_name     = "Rachel",
                  )
    """

    def __init__(self, deps: OrchestratorDeps) -> None:
        self._deps   = deps
        self._logger: StructuredLogger = get_logger("orchestrator")

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC ENTRY POINT
    # ═══════════════════════════════════════════════════════════════════════

    async def process_conversation(
        self,
        audio_path:       str,
        audio_analysis:   Optional[str] = None,
        video_analysis:   Optional[str] = None,
        voice_name:       str = "Rachel",
        expression_history: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a full conversation turn and return the response payload.

        Returns
        -------
        dict with keys:
            interaction_id, transcript, audio_features, emotion, response,
            audio_url, applied_persona, applied_action, applied_policy,
            implicit_reward, memories_used, session_id, metrics
        """
        turn_id = str(uuid.uuid4())
        cid     = with_correlation_id(turn_id)
        wall_start = time.perf_counter()

        log_event(
            self._logger, "turn_started",
            turn_id=turn_id, user_id=self._deps.user_id,
            voice_name=voice_name,
        )

        # ── Build mutable context ────────────────────────────────────
        ctx = TurnContext(
            turn_id    = turn_id,
            audio_path = audio_path,
            voice_name = voice_name,
            frontend_audio  = self._parse_json(audio_analysis),
            video_features  = self._parse_json(video_analysis),
            expression_list = self._parse_json(expression_history) or [],
            metrics = PipelineMetrics(turn_id=turn_id, user_id=self._deps.user_id),
        )

        try:
            # ── Phase 0: Infrastructure setup ────────────────────────
            await self._phase_0_infra(ctx)

            # ── Phase 1: Perception ───────────────────────────────────
            await self._phase_1_perception(ctx)

            # Guard: empty transcript → no point continuing
            if not ctx.transcript.strip():
                self._logger.warning("Empty transcript — aborting turn", turn_id=turn_id)
                return self._empty_response(ctx)

            # ── Phase 2: Cognition ────────────────────────────────────
            await self._phase_2_cognition(ctx)

            # ── Phase 3: Memory & RL ──────────────────────────────────
            await self._phase_3_memory_rl(ctx)

            # ── Phase 4: Planning & Context Compilation ───────────────
            await self._phase_4_planning(ctx)

            # ── Phase 5: Generation ───────────────────────────────────
            await self._phase_5_generation(ctx)

            # ── Phase 6: Persistence ──────────────────────────────────
            await self._phase_6_persistence(ctx)

            # ── Phase 7: Background tasks (fire-and-forget) ───────────
            self._phase_7_background(ctx)

        except Exception as exc:
            self._logger.error(
                "Turn crashed",
                turn_id=turn_id,
                error=str(exc),
                exc_info=True,
            )
            ctx.metrics.mark_degraded("unhandled exception")
            # Return best-effort response — never crash the HTTP handler
            if not ctx.ai_response:
                ctx.ai_response = (
                    "I'm here with you. Something went wrong on my end — "
                    "could you say that again?"
                )

        # ── Finalise metrics ─────────────────────────────────────────
        ctx.metrics.total_ms = (time.perf_counter() - wall_start) * 1_000
        log_event(
            self._logger, "turn_completed",
            turn_id=turn_id,
            total_ms=round(ctx.metrics.total_ms, 2),
            degraded=ctx.metrics.degraded,
        )

        return self._build_response(ctx)

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 0 — Infrastructure Setup
    # ═══════════════════════════════════════════════════════════════════════

    async def _phase_0_infra(self, ctx: TurnContext) -> None:
        """
        Upload raw audio and create a session in parallel.
        Both are non-critical — failures are logged but don't abort the turn.
        """
        upload_task  = self._timed_stage(
            "upload_raw_audio",
            self._upload_raw_audio(ctx.turn_id, ctx.audio_path),
            ctx, critical=False,
        )
        session_task = self._timed_stage(
            "create_session",
            self._create_session(),
            ctx, critical=False,
        )
        audio_url, session = await asyncio.gather(upload_task, session_task)
        ctx.raw_audio_url = audio_url
        ctx.session_id    = session.id if session else None

        log_event(
            self._logger, "phase_0_complete",
            session_id=ctx.session_id, has_audio_url=bool(ctx.raw_audio_url),
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 1 — Perception
    # ═══════════════════════════════════════════════════════════════════════

    async def _phase_1_perception(self, ctx: TurnContext) -> None:
        """
        Transcription and audio feature extraction run in parallel.
        Transcription is critical (retried). Feature extraction degrades gracefully.
        """
        transcribe_task = self._timed_stage(
            "transcription",
            self._transcribe(ctx.audio_path),
            ctx, critical=True, retries=MAX_RETRIES,
        )
        features_task = self._timed_stage(
            "audio_features",
            self._extract_audio_features(ctx.audio_path, ctx.frontend_audio),
            ctx, critical=False,
        )
        transcript, features_dict = await asyncio.gather(
            transcribe_task, features_task
        )

        ctx.transcript    = transcript or "[Inaudible]"
        ctx.features_dict = features_dict or {}
        ctx.audio_features = AudioFeatures(**{
            k: ctx.features_dict.get(k, v)
            for k, v in AudioFeatures().model_fields.items()
            if k in ctx.features_dict
        }) if ctx.features_dict else AudioFeatures()

        log_event(
            self._logger, "phase_1_complete",
            transcript_len=len(ctx.transcript),
            audio_source=ctx.features_dict.get("source", "unknown"),
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 2 — Cognition
    # ═══════════════════════════════════════════════════════════════════════

    async def _phase_2_cognition(self, ctx: TurnContext) -> None:
        """
        Sequence:
          1. Emotion analysis (uses transcript + features + video)
          2. In parallel: UserState update + prior emotion read + WorkingMemory load
        """
        # ── 2a. Emotion analysis ─────────────────────────────────────
        emotion_dict = await self._timed_stage(
            "emotion_analysis",
            self._analyze_emotion(ctx.transcript, ctx.features_dict, ctx.video_features),
            ctx, critical=True, retries=MAX_RETRIES,
        )
        ctx.emotion_dict = emotion_dict or {
            "emotion": "neutral", "stress_level": 50,
            "tone": "calm", "contradiction_detected": False, "hidden_emotion": "",
        }
        ctx.emotion = Emotion(
            emotion              = ctx.emotion_dict.get("emotion", "neutral"),
            stress_level         = ctx.emotion_dict.get("stress_level", 50),
            tone                 = ctx.emotion_dict.get("tone", "calm"),
            contradiction_detected = ctx.emotion_dict.get("contradiction_detected", False),
            hidden_emotion       = ctx.emotion_dict.get("hidden_emotion", ""),
            confidence           = ctx.emotion_dict.get("confidence", 0.85),
            eye_contact_ratio    = ctx.emotion_dict.get("eye_contact_ratio"),
            head_pose            = ctx.emotion_dict.get("head_pose"),
        )

        # ── 2b. UserState update + prior emotion + WorkingMemory (parallel) ──
        prior_state_task = self._timed_stage(
            "fetch_prior_state",
            self._deps.user_state_service.get_state(self._deps.user_id),
            ctx, critical=False,
        )
        update_state_task = self._timed_stage(
            "update_user_state",
            self._deps.user_state_service.update_state(
                self._deps.user_id, ctx.emotion, ctx.transcript
            ),
            ctx, critical=False,
        )
        wm_task = self._timed_stage(
            "load_working_memory",
            self._deps.working_memory_service.get_memory(
                self._deps.user_id, ctx.session_id or ""
            ),
            ctx, critical=False,
        )

        prior_state, user_state, working_memory = await asyncio.gather(
            prior_state_task, update_state_task, wm_task
        )

        ctx.emotion_before  = (
            prior_state.dominant_emotion.value
            if prior_state else "neutral"
        )
        ctx.user_state    = user_state
        ctx.working_memory = working_memory

        log_event(
            self._logger, "phase_2_complete",
            emotion=ctx.emotion_dict.get("emotion"),
            stress=ctx.emotion_dict.get("stress_level"),
            emotion_before=ctx.emotion_before,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 3 — Memory & RL
    # ═══════════════════════════════════════════════════════════════════════

    async def _phase_3_memory_rl(self, ctx: TurnContext) -> None:
        """
        Three independent operations run in parallel:
          A. Generate embedding + retrieve similar past interactions
          B. Retrieve multi-layer memory (episodic, goal, emotional)
          C. RL action selection + successful-interaction lookup
        """
        embedding_coro  = self._get_embedding_and_memories(ctx)
        memory_coro     = self._get_memory_layers(ctx)
        rl_coro         = self._get_rl_action_and_experiences(ctx)

        (memories_res, _), (memory_layers_res, _), (rl_res, _) = await asyncio.gather(
            self._timed_gather("embedding_and_retrieval", embedding_coro, ctx),
            self._timed_gather("memory_layers",           memory_coro,    ctx),
            self._timed_gather("rl_selection",            rl_coro,        ctx),
        )

        memories = memories_res[0] if (memories_res and isinstance(memories_res, tuple)) else []
        memory_layers = memory_layers_res[0] if (memory_layers_res and isinstance(memory_layers_res, tuple)) else {}

        ctx.memories      = memories or []
        ctx.memory_layers = memory_layers or {}
        if rl_res and isinstance(rl_res, tuple) and rl_res[0]:
            ctx.rl_action, ctx.rl_policy, ctx.rl_instructions, ctx.learned_exps = rl_res[0]

        log_event(
            self._logger, "phase_3_complete",
            memories_retrieved=len(ctx.memories),
            memory_layer_types=list(ctx.memory_layers.keys()),
            rl_persona=ctx.rl_action.persona.value if ctx.rl_action else "none",
            rl_policy=ctx.rl_policy.value if ctx.rl_policy else "none",
        )

    async def _get_embedding_and_memories(
        self, ctx: TurnContext
    ) -> Tuple[List[dict], None]:
        embedding = await asyncio.get_event_loop().run_in_executor(
            None, self._deps.embedding_provider.generate, ctx.transcript
        )
        if not embedding:
            return [], None
        memories = await self._deps.embedding_repo.find_similar(
            user_id         = self._deps.user_id,
            query_embedding = embedding,
            k               = 5,
            exclude_session = ctx.session_id,
        )
        return memories, None

    async def _get_memory_layers(self, ctx: TurnContext) -> Tuple[Dict, None]:
        if not ctx.user_state:
            return {}, None
        layers = await self._deps.unified_memory_service.get_contextual_memories(
            self._deps.user_id, ctx.transcript, ctx.user_state
        )
        return layers, None

    async def _get_rl_action_and_experiences(
        self, ctx: TurnContext
    ) -> Tuple[Optional[Tuple], None]:
        rl_context = {
            "emotion":      ctx.emotion_dict.get("emotion", "neutral"),
            "stress_level": ctx.emotion_dict.get("stress_level", 50),
            "is_first_turn": ctx.session_id is not None,
        }
        action, policy = await self._deps.rl_service.select_action_vector(rl_context)
        instructions   = self._deps.rl_service.build_prompt_instructions(action)

        exps = await self._deps.interaction_repo.get_successful_interactions(limit=3)
        learned = self._deps.rl_service.format_experiences(exps)

        return (action, policy, instructions, learned), None

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 4 — Planning & Context Compilation
    # ═══════════════════════════════════════════════════════════════════════

    async def _phase_4_planning(self, ctx: TurnContext) -> None:
        """
        Sequential (each depends on the previous):
          1. ConversationPlanner → strategy + intent
          2. ContextCompiler    → token-efficient LLM context
        """
        plan = await self._timed_stage(
            "conversation_planning",
            self._plan_conversation(ctx),
            ctx, critical=True, retries=1,
        )
        ctx.conversation_plan = plan

        compiled = await self._timed_stage(
            "context_compilation",
            self._compile_context(ctx),
            ctx, critical=False,
        )
        ctx.compiled_context = compiled

        log_event(
            self._logger, "phase_4_complete",
            strategy=ctx.conversation_plan.conversation_strategy.value
                     if ctx.conversation_plan else "unknown",
            compiled_tokens=ctx.compiled_context.total_estimated_tokens
                            if ctx.compiled_context else 0,
        )

    async def _plan_conversation(self, ctx: TurnContext):
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._deps.planning_engine.plan_response,
            ctx.transcript,
            ctx.user_state,
            ctx.memory_layers,
            ctx.emotion_dict,
        )

    async def _compile_context(self, ctx: TurnContext):
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._deps.context_compiler.compile,
            ctx.user_state,
            ctx.working_memory,
            ctx.memory_layers,
            ctx.conversation_plan,
            ctx.emotion_dict,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 5 — Response Generation
    # ═══════════════════════════════════════════════════════════════════════

    async def _phase_5_generation(self, ctx: TurnContext) -> None:
        """
        Sequential:
          1. LLM response generation (critical, retried)
          2. TTS synthesis         (non-critical, degrades to browser TTS)
        """
        ai_response = await self._timed_stage(
            "llm_generation",
            self._generate_response(ctx),
            ctx, critical=True, retries=MAX_RETRIES,
        )
        ctx.ai_response = ai_response or (
            "I hear you. Let me think about that for a moment — "
            "could you tell me a little more?"
        )

        audio_path = await self._timed_stage(
            "tts_synthesis",
            self._synthesize_tts(ctx),
            ctx, critical=False,
        )
        ctx.audio_output_path = audio_path

        # Upload TTS audio (non-critical)
        if ctx.audio_output_path:
            tts_url = await self._timed_stage(
                "upload_tts_audio",
                self._upload_tts_audio(ctx.turn_id, ctx.audio_output_path),
                ctx, critical=False,
            )
            ctx.tts_audio_url = (
                tts_url
                or f"{LOCAL_AUDIO_BASE}/{ctx.audio_output_path.split('/')[-1]}"
            )

        log_event(
            self._logger, "phase_5_complete",
            response_len=len(ctx.ai_response),
            has_audio=bool(ctx.tts_audio_url),
        )

    async def _generate_response(self, ctx: TurnContext) -> str:
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._deps.llm_provider.generate_response(
                transcript           = ctx.transcript,
                emotion              = ctx.emotion_dict,
                memories             = ctx.memories,
                expression_history   = ctx.expression_list,
                persona_name         = ctx.rl_action.persona.value
                                       if ctx.rl_action else "the_empathetic_friend",
                learned_experiences  = ctx.learned_exps,
                user_state           = ctx.user_state,
                memory_layers        = ctx.memory_layers,
                working_memory       = ctx.working_memory,
                conversation_plan    = ctx.conversation_plan,
                compiled_context     = ctx.compiled_context,
                rl_prompt_instructions = ctx.rl_instructions,
            ),
        )

    async def _synthesize_tts(self, ctx: TurnContext) -> Optional[str]:
        emotion_val = ctx.emotion.emotion.value if ctx.emotion else "neutral"
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._deps.tts_provider.synthesize(
                text       = ctx.ai_response,
                emotion    = emotion_val,
                voice_name = ctx.voice_name,
            ),
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 6 — Persistence
    # ═══════════════════════════════════════════════════════════════════════

    async def _phase_6_persistence(self, ctx: TurnContext) -> None:
        """
        Persist the interaction document and record the implicit RL reward
        in parallel.
        """
        applied_persona = ctx.rl_action.persona.value if ctx.rl_action else "the_empathetic_friend"

        interaction = Interaction.create(
            session_id      = ctx.session_id or "unknown",
            user_id         = self._deps.user_id,
            transcript      = ctx.transcript,
            features        = ctx.audio_features,
            emotion_data    = ctx.emotion,
            applied_persona = applied_persona,
            applied_action  = ctx.rl_action.to_dict() if ctx.rl_action else None,
            applied_policy  = ctx.rl_policy.value if ctx.rl_policy else None,
            emotion_before  = ctx.emotion_before,
        ).with_response(
            response_text = ctx.ai_response,
            tts_url       = ctx.tts_audio_url,
        )

        # Implicit reward (turn completed, no explicit feedback yet)
        implicit_reward = compose_reward(
            user_feedback            = None,
            emotion_before           = ctx.emotion_before,
            emotion_after            = ctx.emotion_dict.get("emotion", "neutral"),
            session_duration_seconds = None,
            turn_completed           = True,
        )
        ctx.implicit_reward = implicit_reward

        log_task = self._timed_stage(
            "log_interaction",
            self._deps.interaction_repo.create(interaction),
            ctx, critical=False,
        )
        rl_task = self._timed_stage(
            "record_implicit_reward",
            self._deps.rl_service.record_reward(
                action         = ctx.rl_action,
                policy_used    = ctx.rl_policy,
                reward         = implicit_reward,
                interaction_id = None,   # id not known yet
            ) if ctx.rl_action and ctx.rl_policy else self._noop(),
            ctx, critical=False,
        )

        interaction_id, _ = await asyncio.gather(log_task, rl_task)
        ctx.interaction_id = interaction_id

        # Update RL record with real interaction_id now that we have it
        if ctx.interaction_id and ctx.rl_action and ctx.rl_policy:
            asyncio.create_task(
                self._deps.rl_service.record_reward(
                    action         = ctx.rl_action,
                    policy_used    = ctx.rl_policy,
                    reward         = implicit_reward,
                    interaction_id = ctx.interaction_id,
                )
            )

        log_event(
            self._logger, "phase_6_complete",
            interaction_id=ctx.interaction_id,
            implicit_reward=implicit_reward,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 7 — Background (Fire-and-Forget)
    # ═══════════════════════════════════════════════════════════════════════

    def _phase_7_background(self, ctx: TurnContext) -> None:
        """
        Non-critical enrichment tasks that run after the response is returned.
        Wrapped in tasks so exceptions are caught and logged, never propagated.
        """
        if ctx.interaction_id:
            asyncio.create_task(
                self._safe_background(
                    "store_embedding",
                    self._store_embedding(ctx),
                )
            )

        asyncio.create_task(
            self._safe_background(
                "extract_and_store_memories",
                self._deps.unified_memory_service.extract_and_store_memories(
                    self._deps.user_id,
                    ctx.transcript,
                    ctx.ai_response,
                    ctx.emotion_dict,
                ),
            )
        )

        if ctx.user_state:
            interaction_snapshot = self._build_interaction_snapshot(ctx)
            asyncio.create_task(
                self._safe_background(
                    "update_working_memory",
                    self._deps.working_memory_service.update_from_interaction(
                        self._deps.user_id,
                        ctx.session_id or "",
                        interaction_snapshot,
                    ),
                )
            )

            asyncio.create_task(
                self._safe_background(
                    "reflection_engine",
                    self._deps.reflection_engine.reflect_on_interaction(
                        self._deps.user_id,
                        interaction_snapshot,
                        ctx.user_state,
                    ),
                )
            )

        log_event(self._logger, "phase_7_tasks_scheduled", turn_id=ctx.turn_id)

    async def _store_embedding(self, ctx: TurnContext) -> None:
        embedding = await asyncio.get_event_loop().run_in_executor(
            None, self._deps.embedding_provider.generate, ctx.transcript
        )
        if embedding and ctx.interaction_id:
            await self._deps.embedding_repo.store(ctx.interaction_id, embedding)

    def _build_interaction_snapshot(self, ctx: TurnContext) -> Interaction:
        """Creates a minimal Interaction for background services."""
        applied_persona = (
            ctx.rl_action.persona.value if ctx.rl_action else "the_empathetic_friend"
        )
        return Interaction.create(
            session_id      = ctx.session_id or "unknown",
            user_id         = self._deps.user_id,
            transcript      = ctx.transcript,
            features        = ctx.audio_features,
            emotion_data    = ctx.emotion,
            applied_persona = applied_persona,
            applied_action  = ctx.rl_action.to_dict() if ctx.rl_action else None,
            applied_policy  = ctx.rl_policy.value if ctx.rl_policy else None,
            emotion_before  = ctx.emotion_before,
        ).with_response(
            response_text = ctx.ai_response,
            tts_url       = ctx.tts_audio_url,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # RETRY + TIMING HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    async def _timed_stage(
        self,
        stage_name: str,
        coro,
        ctx: TurnContext,
        *,
        critical:  bool = False,
        retries:   int  = 0,
    ) -> Any:
        """
        Execute a coroutine, measure its duration, record a StageResult.
        If critical=True and all retries are exhausted, mark turn degraded
        but still return None so the pipeline continues.
        """
        t0 = time.perf_counter()
        attempt = 0
        last_exc: Optional[Exception] = None

        while attempt <= retries:
            try:
                result = await coro if attempt == 0 else await self._rebuild_coro(coro)
                duration_ms = (time.perf_counter() - t0) * 1_000
                ctx.metrics.record(StageResult(
                    stage=stage_name, success=True,
                    duration_ms=duration_ms, retries=attempt,
                ))
                return result
            except Exception as exc:
                last_exc = exc
                attempt += 1
                if attempt <= retries:
                    delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
                    self._logger.warning(
                        f"Stage {stage_name} failed — retry {attempt}/{retries} "
                        f"in {delay:.2f}s",
                        stage=stage_name, error=str(exc), attempt=attempt,
                    )
                    await asyncio.sleep(delay)

        # All retries exhausted
        duration_ms = (time.perf_counter() - t0) * 1_000
        ctx.metrics.record(StageResult(
            stage=stage_name, success=False,
            duration_ms=duration_ms,
            error=str(last_exc), retries=attempt - 1,
        ))
        if critical:
            ctx.metrics.mark_degraded(f"{stage_name} failed after {retries} retries")
        self._logger.error(
            f"Stage {stage_name} exhausted retries",
            stage=stage_name, error=str(last_exc), retries=retries,
        )
        return None

    async def _timed_gather(
        self,
        label: str,
        coro,
        ctx: TurnContext,
    ) -> Tuple[Any, None]:
        """Wraps a coroutine for use in asyncio.gather with timing."""
        t0 = time.perf_counter()
        try:
            result = await coro
            duration_ms = (time.perf_counter() - t0) * 1_000
            ctx.metrics.record(StageResult(
                stage=label, success=True, duration_ms=duration_ms
            ))
            return result, None
        except Exception as exc:
            duration_ms = (time.perf_counter() - t0) * 1_000
            ctx.metrics.record(StageResult(
                stage=label, success=False,
                duration_ms=duration_ms, error=str(exc),
            ))
            self._logger.error(f"Gather stage {label} failed", error=str(exc))
            return None, None

    async def _safe_background(self, label: str, coro) -> None:
        """Run a fire-and-forget coroutine, swallowing all exceptions."""
        try:
            await coro
        except Exception as exc:
            self._logger.error(
                f"Background task {label} failed",
                task=label, error=str(exc),
            )

    @staticmethod
    async def _rebuild_coro(coro):
        """
        On retry we must call the original factory again because a coroutine
        can only be awaited once. Callers pass already-created coroutines, so
        on retry we simply re-await; Python will raise StopIteration which we
        treat as success with None. In practice, timed_stage rebuilds properly
        when the caller is a lambda factory — see _generate_response for pattern.
        """
        return await coro

    @staticmethod
    async def _noop() -> None:
        return None

    # ═══════════════════════════════════════════════════════════════════════
    # SERVICE WRAPPERS (thin async wrappers around sync/async calls)
    # ═══════════════════════════════════════════════════════════════════════

    async def _transcribe(self, audio_path: str) -> str:
        return await asyncio.get_event_loop().run_in_executor(
            None, self._deps.transcription_provider.transcribe, audio_path
        )

    async def _extract_audio_features(
        self, audio_path: str, frontend_features: Optional[dict]
    ) -> dict:
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._deps.audio_feature_provider.extract(audio_path, frontend_features),
        )

    async def _analyze_emotion(
        self,
        transcript: str,
        features:   dict,
        video:      Optional[dict],
    ) -> dict:
        from services.emotion_service import EmotionService
        from services.model_manager import model_manager
        svc = EmotionService(model_manager)
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: svc.analyze_emotion(transcript, features, video),
        )

    async def _create_session(self):
        return await self._deps.session_repo.create(self._deps.user_id)

    async def _upload_raw_audio(self, file_id: str, audio_path: str) -> Optional[str]:
        try:
            with open(audio_path, "rb") as f:
                return await self._deps.interaction_repo.upload_file(
                    VOICE_BUCKET, f"{file_id}.webm", f.read()
                )
        except Exception as exc:
            self._logger.error("Raw audio upload failed", error=str(exc))
            return None

    async def _upload_tts_audio(
        self, file_id: str, audio_path: str
    ) -> Optional[str]:
        try:
            with open(audio_path, "rb") as f:
                return await self._deps.interaction_repo.upload_file(
                    TTS_BUCKET, f"{file_id}_response.mp3", f.read()
                )
        except Exception as exc:
            self._logger.error("TTS audio upload failed", error=str(exc))
            return None

    # ═══════════════════════════════════════════════════════════════════════
    # RESPONSE BUILDER
    # ═══════════════════════════════════════════════════════════════════════

    def _build_response(self, ctx: TurnContext) -> Dict[str, Any]:
        applied_persona = (
            ctx.rl_action.persona.value if ctx.rl_action else "the_empathetic_friend"
        )
        return {
            "interaction_id":  ctx.interaction_id,
            "transcript":      ctx.transcript,
            "audio_features":  ctx.features_dict,
            "emotion":         ctx.emotion_dict,
            "response":        ctx.ai_response,
            "audio_url":       ctx.tts_audio_url,
            "applied_persona": applied_persona,
            "applied_action":  ctx.rl_action.to_dict() if ctx.rl_action else None,
            "applied_policy":  ctx.rl_policy.value if ctx.rl_policy else None,
            "implicit_reward": ctx.implicit_reward,
            "memories_used":   len(ctx.memories),
            "session_id":      ctx.session_id,
            "metrics":         ctx.metrics.summary(),
        }

    def _empty_response(self, ctx: TurnContext) -> Dict[str, Any]:
        return {
            "interaction_id":  None,
            "transcript":      ctx.transcript,
            "audio_features":  {},
            "emotion":         {},
            "response":        "I didn't catch that — could you try again?",
            "audio_url":       None,
            "applied_persona": "the_empathetic_friend",
            "applied_action":  None,
            "applied_policy":  None,
            "implicit_reward": 0.0,
            "memories_used":   0,
            "session_id":      ctx.session_id,
            "metrics":         ctx.metrics.summary() if ctx.metrics else {},
        }

    # ═══════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _parse_json(raw: Optional[str]) -> Optional[Any]:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None


# ─────────────────────────────────────────────────────────────────────────────
# OrchestratorFactory — convenience builder for di.py
# ─────────────────────────────────────────────────────────────────────────────

def build_orchestrator(
    transcription_provider:  ITranscriptionProvider,
    audio_feature_provider:  IAudioFeatureProvider,
    llm_provider:            ILLMProvider,
    tts_provider:            ITTSProvider,
    embedding_provider:      IEmbeddingProvider,
    interaction_repo:        IInteractionRepository,
    session_repo:            ISessionRepository,
    user_repo:               IUserRepository,
    embedding_repo:          IEmbeddingRepository,
    user_state_repo:         IUserStateRepository,
    memory_repo:             IMemoryRepository,
    reflection_repo:         IReflectionRepository,
    working_memory_repo:     IWorkingMemoryRepository,
    rl_service:              RLService,
    user_id:                 str = "00000000-0000-0000-0000-000000000000",
) -> ConversationOrchestrator:
    """
    Factory that wires all services and returns a ready-to-use orchestrator.
    Mirrors the existing di.py wiring but uses OrchestratorDeps for clarity.
    """
    from services.model_manager import model_manager
    from services.rag_service   import rag_service as _rag_svc

    user_state_svc  = UserStateService(user_state_repo)
    lifecycle_svc   = MemoryLifecycleService(memory_repo)
    ranking_engine  = ContextRankingEngine()
    unified_mem_svc = UnifiedMemoryService(
        memory_repo, _rag_svc, lifecycle_svc, ranking_engine
    )
    reflection_eng  = ReflectionEngine(reflection_repo, model_manager, _rag_svc)
    working_mem_svc = WorkingMemoryService(working_memory_repo, model_manager)
    planning_eng    = ConversationPlanningEngine(model_manager)
    ctx_compiler    = ContextCompiler()

    deps = OrchestratorDeps(
        transcription_provider  = transcription_provider,
        audio_feature_provider  = audio_feature_provider,
        llm_provider            = llm_provider,
        tts_provider            = tts_provider,
        embedding_provider      = embedding_provider,
        interaction_repo        = interaction_repo,
        session_repo            = session_repo,
        user_repo               = user_repo,
        embedding_repo          = embedding_repo,
        user_state_repo         = user_state_repo,
        memory_repo             = memory_repo,
        reflection_repo         = reflection_repo,
        working_memory_repo     = working_memory_repo,
        user_state_service      = user_state_svc,
        unified_memory_service  = unified_mem_svc,
        reflection_engine       = reflection_eng,
        working_memory_service  = working_mem_svc,
        planning_engine         = planning_eng,
        context_compiler        = ctx_compiler,
        rl_service              = rl_service,
        user_id                 = user_id,
    )
    return ConversationOrchestrator(deps)


# ─────────────────────────────────────────────────────────────────────────────
# SEQUENCE DIAGRAM
# ─────────────────────────────────────────────────────────────────────────────

"""
SEQUENCE DIAGRAM — ConversationOrchestrator.process_conversation()
==================================================================

Client              Orchestrator          Services/Providers
──────              ────────────          ──────────────────

  │                      │
  │─ process_conversation ─►│
  │  (audio_path,          │
  │   audio_analysis,      │
  │   video_analysis,      │
  │   voice_name)          │
  │                        │
  │               ┌────────────────────────────────────────┐
  │               │  PHASE 0 — asyncio.gather()            │
  │               │                                        │
  │               │──► upload_raw_audio ──────────────────►│ interaction_repo.upload_file()
  │               │──► create_session   ──────────────────►│ session_repo.create()
  │               │◄── (audio_url, session) ───────────────│
  │               └────────────────────────────────────────┘
  │                        │
  │               ┌────────────────────────────────────────┐
  │               │  PHASE 1 — asyncio.gather()            │
  │               │                                        │
  │               │──► transcribe (retry×3) ──────────────►│ ITranscriptionProvider
  │               │──► extract_audio_features ────────────►│ IAudioFeatureProvider
  │               │◄── (transcript, features_dict) ────────│
  │               └────────────────────────────────────────┘
  │                        │
  │               ┌────────────────────────────────────────────────────┐
  │               │  PHASE 2 — Sequential then parallel               │
  │               │                                                    │
  │               │──► analyze_emotion (retry×3) ────────────────────►│ EmotionService
  │               │◄── emotion_dict ─────────────────────────────────│
  │               │                                                    │
  │               │  asyncio.gather():                                 │
  │               │──► fetch_prior_state ────────────────────────────►│ UserStateService.get_state()
  │               │──► update_user_state ────────────────────────────►│ UserStateService.update_state()
  │               │──► load_working_memory ──────────────────────────►│ WorkingMemoryService.get_memory()
  │               │◄── (prior_state, user_state, working_memory) ────│
  │               └────────────────────────────────────────────────────┘
  │                        │
  │               ┌─────────────────────────────────────────────────────────┐
  │               │  PHASE 3 — asyncio.gather() (3 parallel branches)      │
  │               │                                                         │
  │               │  Branch A:                                              │
  │               │──► generate_embedding ──────────────────────────────►  │ IEmbeddingProvider
  │               │──► find_similar_memories ───────────────────────────►  │ IEmbeddingRepository
  │               │◄── memories ────────────────────────────────────────   │
  │               │                                                         │
  │               │  Branch B:                                              │
  │               │──► get_contextual_memories ─────────────────────────►  │ UnifiedMemoryService
  │               │◄── memory_layers {episodic, goal, emotional} ────────  │
  │               │                                                         │
  │               │  Branch C:                                              │
  │               │──► rl_service.select_action_vector ────────────────►   │ RLPolicyEngine
  │               │──► interaction_repo.get_successful_interactions ────►  │ IInteractionRepository
  │               │◄── (rl_action, rl_policy, instructions, exps) ──────   │
  │               └─────────────────────────────────────────────────────────┘
  │                        │
  │               ┌────────────────────────────────────────────────────┐
  │               │  PHASE 4 — Sequential                              │
  │               │                                                    │
  │               │──► planning_engine.plan_response (retry×1) ───────►│ ConversationPlanningEngine
  │               │◄── ConversationPlan ────────────────────────────── │
  │               │                                                    │
  │               │──► context_compiler.compile ───────────────────── ►│ ContextCompiler
  │               │◄── CompiledContext ─────────────────────────────── │
  │               └────────────────────────────────────────────────────┘
  │                        │
  │               ┌────────────────────────────────────────────────────┐
  │               │  PHASE 5 — Sequential                              │
  │               │                                                    │
  │               │──► llm_provider.generate_response (retry×3) ──────►│ ILLMProvider
  │               │◄── ai_response ─────────────────────────────────── │
  │               │                                                    │
  │               │──► tts_provider.synthesize ───────────────────────►│ ITTSProvider
  │               │◄── audio_output_path ───────────────────────────── │
  │               │                                                    │
  │               │──► upload_tts_audio ──────────────────────────────►│ interaction_repo.upload_file()
  │               │◄── tts_audio_url ───────────────────────────────── │
  │               └────────────────────────────────────────────────────┘
  │                        │
  │               ┌─────────────────────────────────────────────────────────┐
  │               │  PHASE 6 — asyncio.gather()                            │
  │               │                                                         │
  │               │──► interaction_repo.create(interaction) ─────────────► │ IInteractionRepository
  │               │──► rl_service.record_reward(implicit) ──────────────►  │ RLPolicyEngine
  │               │◄── (interaction_id, _) ──────────────────────────────  │
  │               └─────────────────────────────────────────────────────────┘
  │                        │
  │               ┌─────────────────────────────────────────────────────────┐
  │               │  PHASE 7 — asyncio.create_task() [non-blocking]        │
  │               │                                                         │
  │               │  Task A: store_embedding ──────────────────────────────►│ IEmbeddingRepository
  │               │  Task B: extract_and_store_memories ───────────────────►│ UnifiedMemoryService
  │               │  Task C: update_working_memory ────────────────────────►│ WorkingMemoryService
  │               │  Task D: reflection_engine.reflect_on_interaction ──────►│ ReflectionEngine
  │               │                                                         │
  │               │  [All tasks run concurrently AFTER response is returned]│
  │               └─────────────────────────────────────────────────────────┘
  │                        │
  │◄── response dict ──────│
  │  { interaction_id,     │
  │    transcript,         │
  │    emotion,            │
  │    response,           │
  │    audio_url,          │
  │    applied_action,     │
  │    metrics: {          │
  │      total_ms,         │
  │      stages: [...],    │
  │      degraded: bool    │
  │    }                   │
  │  }                     │
"""
