"""Centralized configuration management with environment isolation."""
import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Fix problematic DEBUG env var before pydantic processes it
if os.environ.get("DEBUG", "").lower() not in ("true", "false", "1", "0", "yes", "no", ""):
    os.environ["DEBUG"] = "false"


class ProviderConfig(BaseSettings):
    """AI provider configuration group."""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    elevenlabs_api_key: str = ""
    deepgram_api_key: str = ""
    cartesia_api_key: str = ""
    lmnt_api_key: str = ""
    murf_api_key: str = ""
    
    model_config = SettingsConfigDict(extra="ignore")


class StorageConfig(BaseSettings):
    """Storage and database configuration."""
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "neuronest"
    
    model_config = SettingsConfigDict(extra="ignore")


class AudioConfig(BaseSettings):
    """Audio pipeline configuration."""
    upload_dir: str = "uploads"
    generated_dir: str = "generated"
    
    model_config = SettingsConfigDict(extra="ignore")


class RAGConfig(BaseSettings):
    """RAG configuration."""
    embedding_model: str = "text-embedding-3-small"
    top_k: int = 5
    
    model_config = SettingsConfigDict(extra="ignore")


class Settings(BaseSettings):
    """Main application settings combining all config groups."""
    # Provider configs
    providers: ProviderConfig = Field(default_factory=ProviderConfig)
    
    # Storage configs
    storage: StorageConfig = Field(default_factory=StorageConfig)
    
    # Audio configs
    audio: AudioConfig = Field(default_factory=AudioConfig)
    
    # RAG configs
    rag: RAGConfig = Field(default_factory=RAGConfig)
    
    # Feature flags
    enable_emotion_analysis: bool = True
    enable_rag: bool = True
    enable_dashboard: bool = True
    
    # App settings
    debug: bool = False
    log_level: str = "INFO"
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    model_config = SettingsConfigDict(env_file=None, extra="ignore")
    
    def validate_production(self) -> bool:
        """Validate critical configuration for production."""
        required = [
            self.providers.openrouter_api_key,
            self.storage.mongodb_uri,
        ]
        return all(bool(v) for v in required)


# Global settings instance - load from env vars directly
_settings_instance = Settings()

# Convenience accessors for backward compatibility
OPENAI_API_KEY = _settings_instance.providers.openai_api_key
GEMINI_API_KEY = _settings_instance.providers.gemini_api_key
GROQ_API_KEY = _settings_instance.providers.groq_api_key
OPENROUTER_API_KEY = _settings_instance.providers.openrouter_api_key
ELEVENLABS_API_KEY = _settings_instance.providers.elevenlabs_api_key
DEEPGRAM_API_KEY = _settings_instance.providers.deepgram_api_key
CARTESIA_API_KEY = _settings_instance.providers.cartesia_api_key
LMNT_API_KEY = _settings_instance.providers.lmnt_api_key
MURF_API_KEY = _settings_instance.providers.murf_api_key
MONGODB_URI = _settings_instance.storage.mongodb_uri
MONGODB_DB = _settings_instance.storage.mongodb_db
UPLOAD_DIR = _settings_instance.audio.upload_dir
GENERATED_DIR = _settings_instance.audio.generated_dir
EMBEDDING_MODEL = _settings_instance.rag.embedding_model
RAG_TOP_K = _settings_instance.rag.top_k

# Make settings work with attribute access for legacy code (settings.MONGODB_URI)
class _SettingsProxy:
    """Proxy allowing attribute-style access to settings and flat config keys."""
    __slots__ = ()
    def __getattr__(self, name):
        if name.startswith('_'):
             raise AttributeError(name)
        # First try to get from global scope (convenience accessors), then from _settings_instance
        return globals().get(name) or getattr(_settings_instance, name, None)

# Define settings as a module-level variable so it's discoverable by static analysis
settings = _SettingsProxy()