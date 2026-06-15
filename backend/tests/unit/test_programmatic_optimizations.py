import pytest
import json
from unittest.mock import patch, mock_open, AsyncMock, MagicMock
from application.orchestrators.conversation_orchestrator import build_orchestrator
from domain.entities import UserState, WorkingMemory, Memory
from domain.value_objects import MemoryType, MemoryImportance, EmotionEnum, ConversationPlan, ConversationStrategy
from services.rl_policy_engine import ActionVector, Persona, ResponseLength, QuestioningStyle, MotivationStyle, DetailLevel, PolicyName
from services.context_compiler import ContextCompiler
from services.context_ranking_engine import ContextRankingEngine

class TestProgrammaticOptimizations:

    @pytest.mark.asyncio
    @patch("application.orchestrators.conversation_orchestrator.open", new_callable=mock_open, read_data=b"dummy audio data")
    async def test_crisis_bypass_triggered(
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
        # Override transcript to trigger crisis bypass
        mock_transcription_provider.transcript = "I want to end my life, please help"
        
        # Wrap plain method in MagicMock so we can inspect calls
        mock_llm_provider.generate_response = MagicMock(return_value="should not be called")
        
        # Setup mocks
        mock_user_state_repo = AsyncMock()
        mock_user_state_repo.get_by_user_id.return_value = UserState.create("00000000-0000-0000-0000-000000000000")
        mock_user_state_repo.update.return_value = True

        mock_memory_repo = AsyncMock()
        mock_memory_repo.save.return_value = "mem-id"

        mock_reflection_repo = AsyncMock()
        mock_reflection_repo.save.return_value = "ref-id"

        mock_working_memory_repo = AsyncMock()
        mock_working_memory_repo.get_by_session.return_value = WorkingMemory.create("00000000-0000-0000-0000-000000000000", "sess-id")
        mock_working_memory_repo.update.return_value = True

        mock_rl_service = MagicMock()
        mock_rl_service.select_action_vector = AsyncMock(return_value=(None, None))

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

        result = await orchestrator.process_conversation(
            audio_path="dummy_input.webm",
            audio_analysis='{"pitch_mean": 120.0}',
            voice_name="Rachel",
        )

        # Assertions for bypass
        assert result is not None
        assert "988" in result["response"]
        assert "Suicide & Crisis Lifeline" in result["response"]
        assert result["metrics"]["degraded"] is True
        
        # Verify LLM was NOT called
        mock_llm_provider.generate_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("application.orchestrators.conversation_orchestrator.open", new_callable=mock_open, read_data=b"dummy audio data")
    async def test_json_cogen_extraction_success(
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
        # Setup mock LLM response returning JSON block wrapped in MagicMock
        json_data = json.dumps({
            "response": "I see you are working on python.",
            "working_memory_updates": {
                "active_project": "Python Voice Assistant",
                "active_problem": "Type check warnings",
                "new_tasks": ["Fix warnings"],
                "new_decisions": [{"content": "Use json parsing", "rationale": "Saves API calls"}]
            }
        })
        mock_llm_provider.generate_response = MagicMock(return_value=json_data)
        
        # Setup mocks
        mock_user_state_repo = AsyncMock()
        mock_user_state_repo.get_by_user_id.return_value = UserState.create("00000000-0000-0000-0000-000000000000")
        mock_user_state_repo.update.return_value = True

        mock_memory_repo = AsyncMock()
        mock_memory_repo.save.return_value = "mem-id"

        mock_reflection_repo = AsyncMock()
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
        mock_rl_service.build_prompt_instructions.return_value = "instructions"
        mock_rl_service.record_reward = AsyncMock()
        mock_rl_service.format_experiences.return_value = "experiences"

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

        result = await orchestrator.process_conversation(
            audio_path="dummy_input.webm",
            audio_analysis='{"pitch_mean": 120.0}',
            voice_name="Rachel",
        )

        # Assertions for JSON parsing
        assert result is not None
        assert result["response"] == "I see you are working on python."
        
        # Verify the background update task was scheduled
        # To verify the memory repository update was called with correct data:
        # Since it runs in an async task, wait briefly for task execution
        await asyncio.sleep(0.1)
        mock_working_memory_repo.update.assert_called()
        last_arg = mock_working_memory_repo.update.call_args[0][0]
        assert last_arg.active_project == "Python Voice Assistant"
        assert last_arg.active_problem == "Type check warnings"
        assert len(last_arg.recent_tasks) > 0
        assert last_arg.recent_tasks[0].description == "Fix warnings"

    def test_context_ranking_pruning(self):
        engine = ContextRankingEngine()
        user_state = UserState(user_id="test_user")
        
        m_low_sim_no_overlap = Memory.create(user_id="test_user", type=MemoryType.EPISODIC, content="My cat likes fish food.")
        m_low_sim_no_overlap.embedding = [0.0] * 1536
        # Cosine similarity will be 0.0
        
        m_low_sim_with_overlap = Memory.create(user_id="test_user", type=MemoryType.EPISODIC, content="Debugging python exceptions.")
        m_low_sim_with_overlap.embedding = [0.0] * 1536
        
        query_embedding = [1.0] * 1536
        
        # Pruning check without query_text
        ranked = engine.rank_memories(
            query_embedding=query_embedding,
            memories=[m_low_sim_no_overlap, m_low_sim_with_overlap],
            user_state=user_state,
            query_text=None
        )
        assert len(ranked) == 0 # both pruned because similarity < 0.35
        
        # Pruning check with query_text (keyword overlap on "python")
        ranked_overlap = engine.rank_memories(
            query_embedding=query_embedding,
            memories=[m_low_sim_no_overlap, m_low_sim_with_overlap],
            user_state=user_state,
            query_text="How to solve python bugs"
        )
        assert len(ranked_overlap) == 1
        assert ranked_overlap[0].id == m_low_sim_with_overlap.id

    def test_context_compiler_stress_delta_alert(self):
        compiler = ContextCompiler()
        user_state = UserState(user_id="test_user")
        user_state.dominant_emotion = EmotionEnum.NEUTRAL
        
        # Compile with low prior stress -> stress surged from 30 to 75 (+45)
        wm = WorkingMemory.create("test_user", "sess-id")
        plan = ConversationPlan(
            intent="talk",
            emotional_need="grounding",
            conversation_strategy=ConversationStrategy.CASUAL,
            response_goal="respond",
            risk_level=1,
            confidence=0.9
        )
        compiled = compiler.compile(
            user_state=user_state,
            working_memory=wm,
            memories={},
            planner_output=plan,
            emotion_profile={"emotion": "neutral", "stress_level": 75, "tone": "calm"},
            prior_stress=30
        )
        
        assert "ALERT: User stress level has surged significantly" in compiled.emotional_state
        assert "by 45%" in compiled.emotional_state

    @patch("services.tts_service.settings")
    @patch("elevenlabs.client.ElevenLabs")
    @patch("elevenlabs.VoiceSettings")
    def test_tts_elevenlabs_settings(self, mock_voice_settings, mock_elevenlabs, mock_settings):
        mock_settings.ELEVENLABS_API_KEY = "dummy_key"
        mock_settings.GENERATED_DIR = "dummy_dir"
        
        mock_client = MagicMock()
        mock_elevenlabs.return_value = mock_client
        mock_client.text_to_speech.convert.return_value = [b"audio_chunk"]
        
        with patch("services.tts_service.open", mock_open()) as mock_file, \
             patch("services.tts_service.os.path.exists", return_value=True), \
             patch("services.tts_service.os.path.getsize", return_value=2000):
            
            from services.tts_service import tts_elevenlabs
            
            # 1. Test "sad"
            res = tts_elevenlabs("hello", "dummy.mp3", "Rachel", "sad")
            assert res == "dummy.mp3"
            mock_voice_settings.assert_called_with(
                stability=0.35,
                similarity_boost=0.75,
                style=0.20,
                use_speaker_boost=True
            )
            
            # 2. Test "anxious"
            tts_elevenlabs("hello", "dummy.mp3", "Rachel", "anxious")
            mock_voice_settings.assert_called_with(
                stability=0.40,
                similarity_boost=0.75,
                style=0.15,
                use_speaker_boost=True
            )
            
            # 3. Test "happy"
            tts_elevenlabs("hello", "dummy.mp3", "Rachel", "happy")
            mock_voice_settings.assert_called_with(
                stability=0.45,
                similarity_boost=0.75,
                style=0.15,
                use_speaker_boost=True
            )
            
            # 4. Test "angry"
            tts_elevenlabs("hello", "dummy.mp3", "Rachel", "angry")
            mock_voice_settings.assert_called_with(
                stability=0.30,
                similarity_boost=0.75,
                style=0.25,
                use_speaker_boost=True
            )
            
            # 5. Test "neutral"
            tts_elevenlabs("hello", "dummy.mp3", "Rachel", "neutral")
            mock_voice_settings.assert_called_with(
                stability=0.50,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )

    @patch("services.tts_service.settings")
    @patch("openai.OpenAI")
    def test_tts_openai_voice_swapping(self, mock_openai, mock_settings):
        mock_settings.OPENAI_API_KEY = "dummy_key"
        mock_settings.GENERATED_DIR = "dummy_dir"
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_client.audio.speech.create.return_value = mock_response
        
        with patch("services.tts_service.os.path.exists", return_value=True), \
             patch("services.tts_service.os.path.getsize", return_value=2000):
            
            from services.tts_service import tts_openai
            
            # 1. Female sad/anxious -> alloy
            tts_openai("hello", "dummy.mp3", "Rachel", "sad")
            mock_client.audio.speech.create.assert_called_with(
                model="tts-1",
                voice="alloy",
                input="hello"
            )
            
            # 2. Female happy/excited -> shimmer
            tts_openai("hello", "dummy.mp3", "Rachel", "happy")
            mock_client.audio.speech.create.assert_called_with(
                model="tts-1",
                voice="shimmer",
                input="hello"
            )
            
            # 3. Female neutral -> Rachel's default is alloy
            tts_openai("hello", "dummy.mp3", "Rachel", "neutral")
            mock_client.audio.speech.create.assert_called_with(
                model="tts-1",
                voice="alloy",
                input="hello"
            )
            
            # 4. Female neutral with another default, e.g. Amelia default is shimmer
            tts_openai("hello", "dummy.mp3", "Amelia", "neutral")
            mock_client.audio.speech.create.assert_called_with(
                model="tts-1",
                voice="shimmer",
                input="hello"
            )
            
            # 5. Male sad/anxious -> echo
            tts_openai("hello", "dummy.mp3", "Josh", "sad")
            mock_client.audio.speech.create.assert_called_with(
                model="tts-1",
                voice="echo",
                input="hello"
            )
            
            # 6. Male happy/excited -> nova
            tts_openai("hello", "dummy.mp3", "Josh", "happy")
            mock_client.audio.speech.create.assert_called_with(
                model="tts-1",
                voice="nova",
                input="hello"
            )
            
            # 7. Male neutral -> Josh's default is echo, Nathan's default is onyx
            tts_openai("hello", "dummy.mp3", "Nathan", "neutral")
            mock_client.audio.speech.create.assert_called_with(
                model="tts-1",
                voice="onyx",
                input="hello"
            )

    def test_emotion_service_lexical_matching(self):
        from services.emotion_service import EmotionService
        
        mock_mm = MagicMock()
        service = EmotionService(mock_mm)
        
        # Test depressed/sad words
        res = service.analyze_emotion("I feel empty and worthless", audio_features=None)
        assert res["emotion"] == "sad"
        assert res["stress_level"] == 60
        assert res["tone"] == "subdued"
        
        # Test anxious words
        res = service.analyze_emotion("I am feeling jittery and uneasy", audio_features=None)
        assert res["emotion"] == "anxious"
        assert res["stress_level"] == 70
        assert res["tone"] == "nervous"
        
        # Test angry words
        res = service.analyze_emotion("This is fuming and hostile", audio_features=None)
        assert res["emotion"] == "frustrated"
        assert res["stress_level"] == 65
        assert res["tone"] == "tense"
        
        # Test crisis words
        res = service.analyze_emotion("I want to end my life", audio_features=None)
        assert res["emotion"] == "depressed"
        assert res["stress_level"] == 95
        assert res["tone"] == "flat"

    def test_emotion_service_acoustic_stress(self):
        from services.emotion_service import EmotionService
        
        mock_mm = MagicMock()
        service = EmotionService(mock_mm)
        
        audio_feats = {
            "jitter": 0.06,
            "volume_std_dev": 16.0,
            "is_trembling": True
        }
        res = service.analyze_emotion("I am fine", audio_features=audio_feats)
        # Expected stress: 50 (baseline) + 15 (jitter > 0.05) + 10 (vol_std > 15) + 15 (is_trembling) = 90
        assert res["stress_level"] == 90
        assert res["tone"] == "trembling"
        
        audio_feats_2 = {
            "pitch_std_dev": 30.0,
            "is_whispering": True
        }
        res_2 = service.analyze_emotion("hello", audio_features=audio_feats_2)
        # Expected stress: 50 + 10 = 60
        assert res_2["stress_level"] == 60
        assert res_2["tone"] == "whispering"

    def test_emotion_service_disgust_vs_sadness(self):
        """
        Verify that the backend FACS fusion correctly separates disgust from sadness.
        - Disgust = AU9 (nose wrinkle) must fire BEFORE sadness is considered
        - Sadness = AU15 (lip depressor) + AU1 (inner brow) with NO nose wrinkle
        """
        from services.emotion_service import EmotionService

        mock_mm = MagicMock()
        service = EmotionService(mock_mm)

        # Case 1: Strong AU9 (nose wrinkle) alone → disgusted
        res = service.analyze_emotion(
            "It smells horrible",
            audio_features=None,
            video_features={
                "eye_contact_ratio": 0.8,
                "head_pose": {"pitch": 0, "yaw": 0, "roll": 0},
                "actionUnits": {"AU09": 0.55, "AU15": 0.0, "AU01": 0.0, "AU04": 0.0},
            },
        )
        assert res["emotion"] == "disgusted", f"Expected disgusted, got {res['emotion']}"

        # Case 2: AU9 + AU10 geometric mean (dual markers) → disgusted
        res = service.analyze_emotion(
            "That is repulsive",
            audio_features=None,
            video_features={
                "eye_contact_ratio": 0.8,
                "head_pose": {"pitch": 0, "yaw": 0, "roll": 0},
                "actionUnits": {"AU09": 0.25, "AU10": 0.30, "AU15": 0.1, "AU01": 0.0},
            },
        )
        assert res["emotion"] == "disgusted", f"Expected disgusted, got {res['emotion']}"

        # Case 3: AU15 alone (no AU9) → sad (not disgusted)
        res = service.analyze_emotion(
            "I feel really sad today",
            audio_features=None,
            video_features={
                "eye_contact_ratio": 0.7,
                "head_pose": {"pitch": 0, "yaw": 0, "roll": 0},
                "actionUnits": {"AU15": 0.55, "AU09": 0.0, "AU01": 0.0},
            },
        )
        assert res["emotion"] == "sad", f"Expected sad, got {res['emotion']}"

        # Case 4: AU4+AU15 but with AU9 present → disgusted (not sad)
        res = service.analyze_emotion(
            "I just saw something disgusting",
            audio_features=None,
            video_features={
                "eye_contact_ratio": 0.8,
                "head_pose": {"pitch": 0, "yaw": 0, "roll": 0},
                "actionUnits": {"AU04": 0.45, "AU15": 0.50, "AU09": 0.40, "AU01": 0.0},
            },
        )
        assert res["emotion"] == "disgusted", f"Expected disgusted, got {res['emotion']}"

        # Case 5: AU1+AU15 grief pattern (no AU9) → sad confirmed
        res = service.analyze_emotion(
            "I miss them so much",
            audio_features=None,
            video_features={
                "eye_contact_ratio": 0.5,
                "head_pose": {"pitch": 0, "yaw": 0, "roll": 0},
                "actionUnits": {"AU01": 0.55, "AU15": 0.60, "AU09": 0.0, "AU04": 0.0},
            },
        )
        assert res["emotion"] == "sad", f"Expected sad, got {res['emotion']}"

    def test_emotion_service_visual_overrides(self):
        from services.emotion_service import EmotionService
        
        mock_mm = MagicMock()
        service = EmotionService(mock_mm)
        
        video_feats = {
            "eye_contact_ratio": 0.40,
            "head_pose": {"pitch": 5.0, "yaw": 0, "roll": 0}
        }
        res = service.analyze_emotion("I am fine", audio_features=None, video_features=video_feats)
        # Baseline 50 + 15 = 65. Since tone was calm/unknown, tone -> avoidant
        assert res["stress_level"] == 65
        assert res["tone"] == "avoidant"
        
        video_feats_2 = {
            "eye_contact_ratio": 0.90,
            "head_pose": {"pitch": 18.0, "yaw": 0, "roll": 0}
        }
        res_2 = service.analyze_emotion("I am fine", audio_features=None, video_features=video_feats_2)
        assert res_2["emotion"] == "sad"
        assert res_2["stress_level"] == 60
        assert res_2["tone"] == "subdued"

import asyncio
