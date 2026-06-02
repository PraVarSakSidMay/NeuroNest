"""Simple DI container and bindings for incremental refactor.

This module wires the adapters to interface names that use-cases will import.
Keep bindings explicit and simple to avoid hidden magic.
"""
from adapters.mongodb_adapter import MongoDBAdapter
from adapters.openai_adapter import OpenAIAdapter
from application.use_cases.process_voice import ProcessVoiceUseCase
from application.orchestrators.conversation_orchestrator import ConversationOrchestrator
from infrastructure.mongodb_repositories import (
    MongoInteractionRepository,
    MongoSessionRepository,
    MongoUserRepository,
    MongoEmbeddingRepository,
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

        # Provider instances
        self.llm_provider = OpenAILLMProvider()
        self.tts_provider = TTSServiceAdapter()
        self.transcription_provider = WhisperTranscriptionAdapter()
        self.audio_feature_provider = OpenAudioFeatureAdapter()
        self.embedding_provider = OpenAIEmbeddingProvider()

        # Use case with legacy interfaces
        self.process_voice_usecase = ProcessVoiceUseCase(
            repo=self.mongodb,
            embedding_provider=self.openai,
            llm_client=self.openai,
            tts_provider=self.openai,
            user_id=self.user_id,
        )

        # Orchestrator with new interfaces
        self.conversation_orchestrator = ConversationOrchestrator(
            transcription_provider=self.transcription_provider,
            audio_feature_provider=self.audio_feature_provider,
            llm_provider=self.llm_provider,
            tts_provider=self.tts_provider,
            embedding_provider=self.embedding_provider,
            interaction_repo=self.interaction_repo,
            session_repo=self.session_repo,
            user_repo=self.user_repo,
            embedding_repo=self.embedding_repo,
            user_id=self.user_id,
        )


container = Container()
