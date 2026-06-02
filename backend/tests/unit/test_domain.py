"""Unit tests for domain entities and value objects."""
import pytest
from domain.entities import Interaction, Session, User
from domain.value_objects import Emotion, AudioFeatures, Transcript, AudioURL
from domain.exceptions import ValidationError, ErrorCode
from tests.factories.domain_factories import (
    create_test_user,
    create_test_session,
    create_test_emotion,
    create_test_audio_features,
)


class TestUser:
    def test_create_user_with_defaults(self):
        user = User.create()
        assert user.id is not None
        assert user.full_name is None
    
    def test_create_user_with_name(self):
        user = User.create(full_name="Test User")
        assert user.full_name == "Test User"


class TestSession:
    def test_create_session(self):
        user = create_test_user()
        session = Session.create(user.id)
        assert session.id is not None
        assert session.user_id == user.id
        assert session.ended_at is None


class TestInteraction:
    def test_create_interaction(self):
        interaction = create_test_audio_features()
        assert interaction.pitch_mean == 200.0


class TestEmotion:
    def test_emotion_defaults(self):
        emotion = Emotion()
        assert emotion.emotion.value == "neutral"
        assert emotion.stress_level == 50
        assert emotion.confidence == 0.5
    
    def test_emotion_with_values(self):
        emotion = create_test_emotion(emotion="happy", stress_level=30)
        assert emotion.emotion.value == "happy"
        assert emotion.stress_level == 30
    
    def test_emotion_stress_validation(self):
        with pytest.raises(ValueError):
            Emotion(stress_level=150)


class TestAudioFeatures:
    def test_audio_features_defaults(self):
        features = AudioFeatures()
        assert features.pitch_mean == 0.0
        assert features.is_trembling is False
    
    def test_audio_features_with_values(self):
        features = create_test_audio_features(pitch_mean=300.0)
        assert features.pitch_mean == 300.0
    
    def test_has_emotional_indicators(self):
        features = create_test_audio_features(is_trembling=True)
        assert features.has_emotional_indicators()
        
        features = create_test_audio_features(jitter=0.1)
        assert features.has_emotional_indicators()


class TestTranscript:
    def test_transcript_valid(self):
        transcript = Transcript(text="Hello world")
        assert transcript.text == "Hello world"
        assert transcript.language == "en"
    
    def test_transcript_empty_fails(self):
        with pytest.raises(ValueError):
            Transcript(text="   ")


class TestAudioURL:
    def test_audio_url_valid(self):
        url = AudioURL(url="https://example.com/audio.mp3")
        assert url.url == "https://example.com/audio.mp3"
    
    def test_audio_url_empty_fails(self):
        with pytest.raises(ValueError):
            AudioURL(url="")


class TestDomainExceptions:
    def test_validation_error(self):
        error = ValidationError("Invalid input", field="email")
        assert error.code == ErrorCode.VALIDATION_ERROR
        assert "field" in error.details
    
    def test_domain_error_correlation_id(self):
        error = ValidationError("Test error")
        assert error.correlation_id is not None
        assert len(error.to_dict()["error"]) == 4