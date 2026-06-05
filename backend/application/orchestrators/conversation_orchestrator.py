"""Conversation orchestration layer for coordinating services and repositories."""
from typing import Optional
import asyncio
import uuid
import json

from core.logging import logger, log_event
from domain.entities import Interaction
from domain.value_objects import Transcript, AudioFeatures, Emotion
from infrastructure.providers import (
    ILLMProvider,
    ITTSProvider,
    ITranscriptionProvider,
    IEmbeddingProvider,
    IAudioFeatureProvider,
)
from infrastructure.repositories import (
    IInteractionRepository,
    ISessionRepository,
    IUserRepository,
    IEmbeddingRepository,
    IUserStateRepository,
    IMemoryRepository,
    IReflectionRepository,
    IWorkingMemoryRepository,
)


class ConversationOrchestrator:
    """Orchestrates the conversation pipeline by coordinating services and repositories.
    
    This class manages the flow of conversation processing without containing
    infrastructure-specific logic.
    """
    
    def __init__(
        self,
        transcription_provider: ITranscriptionProvider,
        audio_feature_provider: IAudioFeatureProvider,
        llm_provider: ILLMProvider,
        tts_provider: ITTSProvider,
        embedding_provider: IEmbeddingProvider,
        interaction_repo: IInteractionRepository,
        session_repo: ISessionRepository,
        user_repo: IUserRepository,
        embedding_repo: IEmbeddingRepository,
        user_state_repo: IUserStateRepository,
        memory_repo: IMemoryRepository,
        reflection_repo: IReflectionRepository,
        working_memory_repo: IWorkingMemoryRepository,
        user_id: str = "00000000-0000-0000-0000-000000000000",
    ):
        self.transcription_provider = transcription_provider
        self.audio_feature_provider = audio_feature_provider
        self.llm_provider = llm_provider
        self.tts_provider = tts_provider
        self.embedding_provider = embedding_provider
        self.interaction_repo = interaction_repo
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.embedding_repo = embedding_repo
        self.user_state_repo = user_state_repo
        self.memory_repo = memory_repo
        self.reflection_repo = reflection_repo
        self.working_memory_repo = working_memory_repo
        self.user_id = user_id
        self._voice_bucket = "voice-recordings"
        self._tts_bucket = "ai-responses"
    
    async def process_conversation(
        self,
        audio_path: str,
        audio_analysis: Optional[str] = None,
        video_analysis: Optional[str] = None,
        voice_name: str = "Rachel",
        expression_history: Optional[str] = None,
    ) -> dict:
        """Process a complete conversation turn."""
        file_id = str(uuid.uuid4())
        log_event(logger, "request_started", audio_path=audio_path)
        
        # Step 1: Upload raw audio
        raw_audio_url = await self._upload_raw_audio(file_id, audio_path)
        
        # Step 2: Create session
        session = await self.session_repo.create(self.user_id)
        session_id = session.id if session else None
        
        # Step 3: Transcribe
        transcript_text = self.transcription_provider.transcribe(audio_path)
        
        # Step 4: Extract audio features
        frontend_features = None
        if audio_analysis:
            try:
                frontend_features = json.loads(audio_analysis)
            except Exception:
                pass
        features_dict = self.audio_feature_provider.extract(audio_path, frontend_features)
        audio_features = AudioFeatures(**features_dict)
        log_event(
            logger,
            "audio_features_ready",
            source=features_dict.get("source", "unknown"),
            audio_emotion_hint=features_dict.get("audio_emotion_hint", ""),
            has_frontend_audio_features=frontend_features is not None,
        )
        
        # Step 4b: Extract video features
        video_features = None
        if video_analysis:
            try:
                video_features = json.loads(video_analysis)
            except Exception:
                pass

        # Step 5: Analyze emotion
        from services.emotion_service import EmotionService
        from services.model_manager import model_manager
        from services.user_state_service import UserStateService
        from services.unified_memory_service import UnifiedMemoryService
        from services.memory_lifecycle_service import MemoryLifecycleService
        from services.context_ranking_engine import ContextRankingEngine
        from services.reflection_engine import ReflectionEngine
        from services.working_memory_service import WorkingMemoryService
        from services.conversation_planning_engine import ConversationPlanningEngine
        from services.context_compiler import ContextCompiler
        from services.rag_service import rag_service
        
        emotion_service = EmotionService(model_manager)
        user_state_service = UserStateService(self.user_state_repo)
        
        memory_lifecycle_service = MemoryLifecycleService(self.memory_repo)
        context_ranking_engine = ContextRankingEngine()
        unified_memory_service = UnifiedMemoryService(
            self.memory_repo, 
            rag_service, 
            memory_lifecycle_service,
            context_ranking_engine
        )
        
        reflection_engine = ReflectionEngine(
            self.reflection_repo, 
            model_manager, 
            rag_service
        )
        
        working_memory_service = WorkingMemoryService(
            self.working_memory_repo,
            model_manager
        )

        planning_engine = ConversationPlanningEngine(model_manager)
        context_compiler = ContextCompiler()
        
        emotion_dict = emotion_service.analyze_emotion(transcript_text, features_dict, video_features)
        emotion = Emotion(
            emotion=emotion_dict.get("emotion", "neutral"),
            stress_level=emotion_dict.get("stress_level", 50),
            tone=emotion_dict.get("tone", "calm"),
            contradiction_detected=emotion_dict.get("contradiction_detected", False),
            hidden_emotion=emotion_dict.get("hidden_emotion", ""),
            confidence=0.85,
            eye_contact_ratio=emotion_dict.get("eye_contact_ratio"),
            head_pose=emotion_dict.get("head_pose"),
        )
        
        # Step 5b: Update persistent User State
        user_state = await user_state_service.update_state(self.user_id, emotion, transcript_text)
        log_event(
            logger,
            "user_state_updated",
            dominant_emotion=user_state.dominant_emotion,
            stress_level=user_state.stress_level,
            recent_topics=user_state.recent_topics,
        )
        
        # Step 5c: Fetch Working Memory
        working_memory = await working_memory_service.get_memory(self.user_id, session_id)
        
        # Step 6: Retrieve memories
        memories = await self.embedding_repo.find_similar(
            user_id=self.user_id,
            query_embedding=self.embedding_provider.generate(transcript_text) or [],
            k=5,
            exclude_session=session_id,
        )
        
        # Step 7: Generate response
        expression_list = []
        if expression_history:
            try:
                expression_list = json.loads(expression_history)
            except Exception:
                pass
        
        # Step 7a: RL Full Action Vector Selection
        from services.rl_service import rl_service
        from services.rl_policy_engine import ActionVector, PolicyName

        # Capture emotion *before* this turn for sentiment-delta reward later
        prev_user_state = await user_state_service.get_state(self.user_id)
        emotion_before  = prev_user_state.dominant_emotion.value if prev_user_state else "neutral"

        rl_action, rl_policy = await rl_service.select_action_vector(
            context={
                "emotion":       emotion_dict.get("emotion", "neutral"),
                "stress_level":  emotion_dict.get("stress_level", 50),
                "is_first_turn": (session is not None and session_id is not None),
            }
        )
        applied_persona = rl_action.persona.value
        rl_prompt_instructions = rl_service.build_prompt_instructions(rl_action)

        # Step 7b: Experience Learning (Few-shot training)
        successful_exps = await self.interaction_repo.get_successful_interactions(limit=3)
        learned_experiences = rl_service.format_experiences(successful_exps)

        # Step 7c: Multi-Layer Memory Retrieval
        memory_layers = await unified_memory_service.get_contextual_memories(
            self.user_id, 
            transcript_text,
            user_state
        )

        # Step 7d: Conversation Planning
        conversation_plan = planning_engine.plan_response(
            user_message=transcript_text,
            user_state=user_state,
            retrieved_memories=memory_layers,
            emotion_profile=emotion_dict
        )
        log_event(
            logger,
            "conversation_planned",
            strategy=conversation_plan.conversation_strategy,
            intent=conversation_plan.intent,
            goal=conversation_plan.response_goal
        )
        
        # Step 7e: Compile Context for Response Generation
        compiled_context = context_compiler.compile(
            user_state=user_state,
            working_memory=working_memory,
            memories=memory_layers,
            planner_output=conversation_plan,
            emotion_profile=emotion_dict
        )
        
        ai_response = self.llm_provider.generate_response(
            transcript=transcript_text,
            emotion=emotion_dict,
            memories=memories,
            expression_history=expression_list,
            persona_name=applied_persona,
            learned_experiences=learned_experiences,
            user_state=user_state,
            memory_layers=memory_layers,
            working_memory=working_memory,
            conversation_plan=conversation_plan,
            compiled_context=compiled_context,
            rl_prompt_instructions=rl_prompt_instructions,
        )
        
        # Step 8: Generate TTS
        audio_output_path = self.tts_provider.synthesize(
            text=ai_response,
            emotion=emotion.emotion,
            voice_name=voice_name,
        )
        
        # Step 9: Upload TTS audio
        tts_audio_url = await self._upload_tts_audio(file_id, audio_output_path)
        if not tts_audio_url and audio_output_path:
            tts_audio_url = f"http://localhost:8000/audio/{audio_output_path.split('/')[-1]}"
        
        # Step 10: Log interaction — store full RL action vector
        interaction = Interaction.create(
            session_id=session_id,
            user_id=self.user_id,
            transcript=transcript_text,
            features=audio_features,
            emotion_data=emotion,
            applied_persona=applied_persona,
            applied_action=rl_action.to_dict(),
            applied_policy=rl_policy.value,
            emotion_before=emotion_before,
        ).with_response(
            response_text=ai_response,
            tts_url=tts_audio_url,
        )
        interaction_id = await self.interaction_repo.create(interaction)

        # Step 10b: Immediate implicit reward (turn completed successfully)
        implicit_reward = rl_service.compose_reward(
            user_feedback=None,
            emotion_before=emotion_before,
            emotion_after=emotion_dict.get("emotion", "neutral"),
            turn_completed=True,
        )
        await rl_service.record_reward(
            action=rl_action,
            policy_used=rl_policy,
            reward=implicit_reward,
            interaction_id=interaction_id,
        )
        
        # Step 11: Store Interaction Memory
        await unified_memory_service.extract_and_store_memories(
            self.user_id, 
            transcript_text, 
            ai_response, 
            emotion_dict
        )

        # Step 11b: Update Working Memory
        await working_memory_service.update_from_interaction(
            self.user_id,
            session_id,
            interaction
        )

        # Step 12: Async Reflection Engine (Non-blocking insight generation)
        asyncio.create_task(reflection_engine.reflect_on_interaction(
            self.user_id, 
            interaction, 
            user_state
        ))

        return {
            "interaction_id":  interaction_id,
            "transcript":      transcript_text,
            "audio_features":  features_dict,
            "emotion":         emotion_dict,
            "response":        ai_response,
            "audio_url":       tts_audio_url,
            "applied_persona": applied_persona,
            "applied_action":  rl_action.to_dict(),
            "applied_policy":  rl_policy.value,
            "implicit_reward": implicit_reward,
            "memories_used":   len(memories),
            "session_id":      session_id,
        }
    
    async def _upload_raw_audio(self, file_id: str, audio_path: str) -> Optional[str]:
        try:
            with open(audio_path, "rb") as f:
                return await self.interaction_repo.upload_file(
                    self._voice_bucket,
                    f"{file_id}.webm",
                    f.read(),
                )
        except Exception as e:
            logger.error(f"Adapter upload failed: {e}")
            return None
    
    async def _upload_tts_audio(self, file_id: str, audio_output_path: Optional[str]) -> Optional[str]:
        if not audio_output_path:
            return None
        try:
            with open(audio_output_path, "rb") as f:
                url = await self.interaction_repo.upload_file(
                    self._tts_bucket,
                    f"{file_id}_response.mp3",
                    f.read(),
                )
                return url
        except Exception as e:
            logger.error(f"Failed to upload TTS audio: {e}")
            return None
    
