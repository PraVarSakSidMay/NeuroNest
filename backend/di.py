"""Simple DI container and bindings for incremental refactor.

This module wires the adapters to interface names that use-cases will import.
Keep bindings explicit and simple to avoid hidden magic.
"""
from adapters.mongodb_adapter import MongoDBAdapter
from adapters.openai_adapter import OpenAIAdapter
from application.orchestrators.conversation_orchestrator import (
    build_orchestrator,
)
from infrastructure.mongodb_repositories import (
    MongoInteractionRepository,
    MongoSessionRepository,
    MongoUserRepository,
    MongoEmbeddingRepository,
    MongoUserStateRepository,
    MongoMemoryRepository,
    MongoReflectionRepository,
    MongoWorkingMemoryRepository,
    MongoRLRepository,
)
from infrastructure.ai_providers import (
    OpenAILLMProvider,
    TTSServiceAdapter,
    WhisperTranscriptionAdapter,
    OpenAudioFeatureAdapter,
    OpenAIEmbeddingProvider,
)


class Container:
    def __init__(self):
        self.mongodb = MongoDBAdapter()
        self.openai = OpenAIAdapter()
        self.user_id = "00000000-0000-0000-0000-000000000000"

        # Repository instances
        self.interaction_repo = MongoInteractionRepository()
        self.session_repo = MongoSessionRepository()
        self.user_repo = MongoUserRepository()
        self.embedding_repo = MongoEmbeddingRepository()
        self.user_state_repo = MongoUserStateRepository()
        self.memory_repo = MongoMemoryRepository()
        self.reflection_repo = MongoReflectionRepository()
        self.working_memory_repo = MongoWorkingMemoryRepository()
        self.rl_repo = MongoRLRepository()

        # Provider instances
        self.llm_provider = OpenAILLMProvider()
        self.tts_provider = TTSServiceAdapter()
        self.transcription_provider = WhisperTranscriptionAdapter()
        self.audio_feature_provider = OpenAudioFeatureAdapter()
        self.embedding_provider = OpenAIEmbeddingProvider()

        # Orchestrator wired via factory (services constructed inside)
        from services.rl_service import rl_service as _rl_svc
        self.conversation_orchestrator = build_orchestrator(
            transcription_provider = self.transcription_provider,
            audio_feature_provider = self.audio_feature_provider,
            llm_provider           = self.llm_provider,
            tts_provider           = self.tts_provider,
            embedding_provider     = self.embedding_provider,
            interaction_repo       = self.interaction_repo,
            session_repo           = self.session_repo,
            user_repo              = self.user_repo,
            embedding_repo         = self.embedding_repo,
            user_state_repo        = self.user_state_repo,
            memory_repo            = self.memory_repo,
            reflection_repo        = self.reflection_repo,
            working_memory_repo    = self.working_memory_repo,
            rl_service             = _rl_svc,
            user_id                = self.user_id,
        )


container = Container()
