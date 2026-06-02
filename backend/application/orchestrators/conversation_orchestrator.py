"""Conversation orchestration layer for coordinating services and repositories."""
from typing import Optional
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

        # Step 5: Analyze emotion (using existing service for now)
        from services.emotion_service import analyze_emotion
        emotion_dict = analyze_emotion(transcript_text, features_dict, video_features)
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
        
        # Step 7a: RL Persona Selection
        from services.rl_service import rl_service
        persona_stats = await self.interaction_repo.get_persona_performance()
        applied_persona = await rl_service.select_persona(persona_stats)

        # Step 7b: Experience Learning (Few-shot training)
        successful_exps = await self.interaction_repo.get_successful_interactions(limit=3)
        learned_experiences = rl_service.format_experiences(successful_exps)

        ai_response = self.llm_provider.generate_response(
            transcript=transcript_text,
            emotion=emotion_dict,
            memories=memories,
            expression_history=expression_list,
            persona_name=applied_persona,
            learned_experiences=learned_experiences,
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
        
        # Step 10: Log interaction
        interaction = Interaction.create(
            session_id=session_id,
            user_id=self.user_id,
            transcript=transcript_text,
            features=audio_features,
            emotion_data=emotion,
            applied_persona=applied_persona,
        ).with_response(
            response_text=ai_response,
            tts_url=tts_audio_url,
        )
        interaction_id = await self.interaction_repo.create(interaction)
        
        return {
            "interaction_id": interaction_id,
            "transcript": transcript_text,
            "audio_features": features_dict,
            "emotion": emotion_dict,
            "response": ai_response,
            "audio_url": tts_audio_url,
            "applied_persona": applied_persona,
            "memories_used": len(memories),
            "session_id": session_id,
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
    
