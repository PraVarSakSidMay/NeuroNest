"""Backward-compatible config module.

DEPRECATED: Use core/config package for new code.
This module is kept for backward compatibility during migration.
"""
# Import from the new config package
from core.config import (
    settings,
    Settings,
    ProviderConfig,
    StorageConfig,
    AudioConfig,
    RAGConfig,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    OPENROUTER_API_KEY,
    ELEVENLABS_API_KEY,
    DEEPGRAM_API_KEY,
    CARTESIA_API_KEY,
    LMNT_API_KEY,
    MURF_API_KEY,
    MONGODB_URI,
    MONGODB_DB,
    UPLOAD_DIR,
    GENERATED_DIR,
    EMBEDDING_MODEL,
    RAG_TOP_K,
)

# Make settings attributes directly accessible for legacy code
# This allows settings.MONGODB_URI to work
class _SettingsProxy:
    def __getattr__(self, name):
        if name in globals():
            return globals()[name]
        return getattr(settings, name)

import sys
sys.modules['core.config'].__dict__['settings'] = _SettingsProxy()

__all__ = [
    "settings",
    "Settings",
    "ProviderConfig",
    "StorageConfig",
    "AudioConfig",
    "RAGConfig",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
    "ELEVENLABS_API_KEY",
    "DEEPGRAM_API_KEY",
    "CARTESIA_API_KEY",
    "LMNT_API_KEY",
    "MURF_API_KEY",
    "MONGODB_URI",
    "MONGODB_DB",
    "UPLOAD_DIR",
    "GENERATED_DIR",
    "EMBEDDING_MODEL",
    "RAG_TOP_K",
]
