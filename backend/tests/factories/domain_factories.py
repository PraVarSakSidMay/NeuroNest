"""Test factories for creating domain objects."""
from domain.entities import Interaction, Session, User
from domain.value_objects import Emotion, AudioFeatures, Transcript


def create_test_user(user_id: str = None, full_name: str = "Test User") -> User:
    return User.create(user_id=user_id, full_name=full_name)


def create_test_session(user_id: str = None) -> Session:
    if user_id is None:
        user = create_test_user()
        user_id = user.id
    return Session.create(user_id=user_id)


def create_test_emotion(
    emotion: str = "neutral",
    stress_level: int = 50,
    confidence: float = 0.85,
) -> Emotion:
    return Emotion(
        emotion=emotion,
        stress_level=stress_level,
        tone="calm",
        contradiction_detected=False,
        hidden_emotion="",
        confidence=confidence,
    )


def create_test_audio_features(**kwargs) -> AudioFeatures:
    defaults = {
        "pitch_mean": 200.0,
        "jitter": 0.01,
        "loudness": 0.5,
        "volume_std_dev": 0.1,
        "pitch_std_dev": 50.0,
        "is_trembling": False,
        "is_singing": False,
        "is_crying": False,
        "is_whispering": False,
        "voice_description": "stable voice",
        "audio_emotion_hint": "",
        "source": "unknown",
    }
    defaults.update(kwargs)
    return AudioFeatures(**defaults)


def create_test_transcript(text: str = "Test transcript") -> Transcript:
    return Transcript(text=text)


def create_test_interaction(
    session_id: str = None,
    user_id: str = None,
    transcript: str = "Test transcript",
    emotion: Emotion = None,
    features: AudioFeatures = None,
) -> Interaction:
    if session_id is None:
        session = create_test_session(user_id)
        session_id = session.id
    if user_id is None:
        user = create_test_user()
        user_id = user.id
    if emotion is None:
        emotion = create_test_emotion()
    if features is None:
        features = create_test_audio_features()
    
    return Interaction(
        id="",
        session_id=session_id,
        user_id=user_id,
        transcript=transcript,
        features=features,
        emotion_data=emotion,
    )