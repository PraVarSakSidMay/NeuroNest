"""Unit tests for ConversationOrchestrator."""
import pytest
from unittest.mock import patch, mock_open
from application.orchestrators.conversation_orchestrator import ConversationOrchestrator


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
        # Create orchestrator instance
        orchestrator = ConversationOrchestrator(
            transcription_provider=mock_transcription_provider,
            audio_feature_provider=mock_audio_feature_provider,
            llm_provider=mock_llm_provider,
            tts_provider=mock_tts_provider,
            embedding_provider=mock_embedding_provider,
            interaction_repo=mock_interaction_repo,
            session_repo=mock_session_repo,
            user_repo=mock_user_repo,
            embedding_repo=mock_embedding_repo,
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
        assert session.user_id == orchestrator.user_id