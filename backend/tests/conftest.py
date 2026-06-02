"""Pytest configuration and fixtures."""
import pytest
import asyncio
from tests.mocks.mock_repositories import (
    MockInteractionRepository,
    MockSessionRepository,
    MockUserRepository,
    MockEmbeddingRepository,
)
from tests.mocks.mock_providers import (
    MockLLMProvider,
    MockTTSProvider,
    MockTranscriptionProvider,
    MockEmbeddingProvider,
    MockAudioFeatureProvider,
)
from tests.factories.domain_factories import (
    create_test_user,
    create_test_session,
    create_test_emotion,
)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_interaction_repo():
    return MockInteractionRepository()


@pytest.fixture
def mock_session_repo():
    return MockSessionRepository()


@pytest.fixture
def mock_user_repo():
    return MockUserRepository()


@pytest.fixture
def mock_embedding_repo():
    return MockEmbeddingRepository()


@pytest.fixture
def mock_llm_provider():
    return MockLLMProvider()


@pytest.fixture
def mock_tts_provider():
    return MockTTSProvider()


@pytest.fixture
def mock_transcription_provider():
    return MockTranscriptionProvider()


@pytest.fixture
def mock_embedding_provider():
    return MockEmbeddingProvider()


@pytest.fixture
def mock_audio_feature_provider():
    return MockAudioFeatureProvider()


@pytest.fixture
def test_user():
    return create_test_user()


@pytest.fixture
def test_session():
    return create_test_session()


@pytest.fixture
def test_emotion():
    return create_test_emotion()