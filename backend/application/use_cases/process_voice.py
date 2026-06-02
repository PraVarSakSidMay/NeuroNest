import os
import uuid
import shutil
import asyncio
import json
from typing import Optional

from ports import IInteractionRepository, IEmbeddingProvider, ILLMClient, ITTSProvider
from models.interaction import InteractionCreate, AudioFeatures as LegacyAudioFeatures, EmotionData
from domain.entities import Interaction, Session
from domain.value_objects import Transcript, AudioFeatures, Emotion
from domain.services import IEmotionAnalyzer
from application.dtos.voice_request import VoiceRequestDTO
from application.dtos.voice_response import VoiceResponseDTO
from core.config import settings
from core.logger import logger


class ProcessVoiceUseCase:
    def __init__(
        self,
        repo: IInteractionRepository,
        embedding_provider: IEmbeddingProvider,
        llm_client: ILLMClient,
        tts_provider: ITTSProvider,
        emotion_analyzer: Optional[IEmotionAnalyzer] = None,
        user_id: str = "00000000-0000-0000-0000-000000000000",
    ):
        self.repo = repo
        self.embedding_provider = embedding_provider
        self.llm = llm_client
        self.tts = tts_provider
        self.emotion_analyzer = emotion_analyzer
        self.user_id = user_id

    async def execute(self, upload_file_obj, audio_analysis: Optional[str], voice_name: str = "Rachel"):
        return await self.execute_with_dto(VoiceRequestDTO(
            file=upload_file_obj,
            audio_analysis=audio_analysis,
            voice_name=voice_name,
        ))

    async def execute_with_dto(self, request: VoiceRequestDTO) -> dict:
        file_id = str(uuid.uuid4())
        input_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.webm")
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(request.file.file, buffer)

        raw_audio_url = await self._upload_raw_audio(file_id, input_path)
        session_id = await self.repo.create_session(self.user_id)

        from services.whisper_service import transcribe_audio
        from services.opensmile_service import extract_audio_features
        from services.emotion_service import analyze_emotion
        from services.rag_service import rag_service
        from services.dashboard_service import update_dashboard

        transcript = transcribe_audio(input_path)
        frontend_features = None
        if request.audio_analysis:
            try:
                frontend_features = json.loads(request.audio_analysis)
            except Exception:
                pass

        features_dict = extract_audio_features(input_path, frontend_features)
        domain_features = AudioFeatures(**features_dict)
        
        emotion_dict = analyze_emotion(transcript, features_dict)
        domain_emotion = Emotion(
            emotion=emotion_dict.get("emotion", "neutral"),
            stress_level=emotion_dict.get("stress_level", 50),
            tone=emotion_dict.get("tone", "calm"),
            contradiction_detected=emotion_dict.get("contradiction_detected", False),
            hidden_emotion=emotion_dict.get("hidden_emotion", ""),
            confidence=0.85,
        )

        supabase = self.repo.get_supabase_client()
        memories = await rag_service.retrieve_memories(
            supabase_client=supabase,
            user_id=self.user_id,
            query_text=transcript,
            current_session_id=session_id,
            k=settings.RAG_TOP_K,
        )

        ai_response = self.llm.generate_response(transcript, emotion_dict, memories)
        legacy_emotion = EmotionData(
            emotion=domain_emotion.emotion,
            stress_level=domain_emotion.stress_level,
            tone=domain_emotion.tone,
            contradiction_detected=domain_emotion.contradiction_detected,
            hidden_emotion=domain_emotion.hidden_emotion,
        )
        legacy_features = LegacyAudioFeatures(**features_dict)

        audio_output_path = self.tts.generate_tts(ai_response, domain_emotion.emotion, request.voice_name)
        tts_audio_url = await self._upload_tts_audio(file_id, audio_output_path, session_id)

        interaction_data = InteractionCreate(
            session_id=session_id,
            user_id=self.user_id,
            transcript=transcript,
            raw_audio_url=raw_audio_url,
            features=legacy_features,
            emotion_data=legacy_emotion,
            response_text=ai_response,
            tts_audio_url=tts_audio_url,
        )

        interaction_id = await self.repo.log_interaction(interaction_data)
        dashboard = update_dashboard(transcript, emotion_dict)

        if interaction_id:
            asyncio.create_task(self._store_embedding_async(interaction_id, transcript))

        return {
            "transcript": transcript,
            "audio_features": features_dict,
            "emotion": emotion_dict,
            "response": ai_response,
            "audio_url": tts_audio_url,
            "memories_used": len(memories),
            "session_id": session_id,
            "dashboard": dashboard,
        }

    async def _upload_raw_audio(self, file_id: str, input_path: str) -> Optional[str]:
        try:
            with open(input_path, "rb") as f:
                return await self.repo.upload_file(settings.VOICE_BUCKET, f"{file_id}.webm", f.read())
        except Exception as e:
            logger.error(f"Adapter upload failed: {e}")
            return None

    async def _upload_tts_audio(self, file_id: str, audio_output_path: Optional[str], session_id: str) -> Optional[str]:
        if not audio_output_path:
            return None
        try:
            with open(audio_output_path, "rb") as f:
                url = await self.repo.upload_file(settings.TTS_BUCKET, f"{file_id}_response.mp3", f.read())
                return url
        except Exception as e:
            logger.error(f"Failed to upload TTS audio: {e}")
            return f"http://localhost:8000/audio/{os.path.basename(audio_output_path)}"

    async def _store_embedding_async(self, interaction_id: str, transcript: str):
        try:
            embedding = await asyncio.get_event_loop().run_in_executor(
                None, self.embedding_provider.generate_embedding, transcript
            )
            if embedding:
                await self.repo.store_embedding(interaction_id, embedding)
        except Exception as e:
            logger.error(f"Background embedding failed: {e}")