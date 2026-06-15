"""Unit tests for ConversationOrchestrator."""
import pytest
from unittest.mock import patch, mock_open, AsyncMock, MagicMock
from application.orchestrators.conversation_orchestrator import build_orchestrator
from domain.entities import UserState, WorkingMemory
from services.rl_policy_engine import ActionVector, Persona, ResponseLength, QuestioningStyle, MotivationStyle, DetailLevel, PolicyName


class TestConversationOrchestrator:
    @pytest.mark.asyncio
    @patch("application.orchestrators.conversation_orchestrator.open", new_callable=mock_open, read_data=b"dummy audio data")
    async def test_process_conversation_success(
        self,
        mock_file,
        mock_transcription_provider,
        mock_audio_feature_provider,
        mock_llm_provider,
        mock_tts_provider,
        mock_embedding_provider,
        mock_interaction_repo,
        mock_session_repo,
        mock_user_repo,
        mock_embedding_repo,
    ):
        # Additional new dependencies for the multi-layer cognitive systems
        mock_user_state_repo = AsyncMock()
        mock_user_state_repo.get_by_user_id.return_value = UserState.create("00000000-0000-0000-0000-000000000000")
        mock_user_state_repo.update.return_value = True

        mock_memory_repo = AsyncMock()
        mock_memory_repo.find_relevant.return_value = []
        mock_memory_repo.get_expired_memories.return_value = []
        mock_memory_repo.get_consolidation_candidates.return_value = []
        mock_memory_repo.save.return_value = "mem-id"

        mock_reflection_repo = AsyncMock()
        mock_reflection_repo.find_similar.return_value = []
        mock_reflection_repo.save.return_value = "ref-id"

        mock_working_memory_repo = AsyncMock()
        mock_working_memory_repo.get_by_session.return_value = WorkingMemory.create("00000000-0000-0000-0000-000000000000", "sess-id")
        mock_working_memory_repo.update.return_value = True

        mock_rl_service = MagicMock()
        action_vector = ActionVector(
            persona=Persona.EMPATHETIC_FRIEND,
            response_length=ResponseLength.MODERATE,
            questioning_style=QuestioningStyle.OPEN,
            motivation_style=MotivationStyle.ENCOURAGEMENT,
            detail_level=DetailLevel.BALANCED,
        )
        mock_rl_service.select_action_vector = AsyncMock(return_value=(action_vector, PolicyName.THOMPSON))
        mock_rl_service.build_prompt_instructions.return_value = "- Be empathetic\n- Be moderate\n- Ask open questions"
        mock_rl_service.record_reward = AsyncMock()
        mock_rl_service.format_experiences.return_value = "learned experiences"

        # Create orchestrator instance via the build_orchestrator factory
        orchestrator = build_orchestrator(
            transcription_provider=mock_transcription_provider,
            audio_feature_provider=mock_audio_feature_provider,
            llm_provider=mock_llm_provider,
            tts_provider=mock_tts_provider,
            embedding_provider=mock_embedding_provider,
            interaction_repo=mock_interaction_repo,
            session_repo=mock_session_repo,
            user_repo=mock_user_repo,
            embedding_repo=mock_embedding_repo,
            user_state_repo=mock_user_state_repo,
            memory_repo=mock_memory_repo,
            reflection_repo=mock_reflection_repo,
            working_memory_repo=mock_working_memory_repo,
            rl_service=mock_rl_service,
            user_id="00000000-0000-0000-0000-000000000000",
        )
        
        # Run conversation process
        result = await orchestrator.process_conversation(
            audio_path="dummy_input.webm",
            audio_analysis='{"pitch_mean": 220.0}',
            voice_name="Rachel",
        )
        
        # Assertions
        assert result is not None
        assert result["transcript"] == mock_transcription_provider.transcript
        assert result["response"] == mock_llm_provider.response
        assert "audio_url" in result
        assert result["session_id"] is not None
        assert result["audio_features"]["pitch_mean"] == 200.0
        
        # Verify repository states
        session = await mock_session_repo.get_by_id(result["session_id"])
        assert session is not None
        assert session.user_id == orchestrator._deps.user_id