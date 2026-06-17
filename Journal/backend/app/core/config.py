"""
Application configuration module.

Loads environment variables from .env file and provides
a cached settings singleton for use throughout the application.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    MONGODB_URI: str
    MONGODB_DATABASE: str = "journal"
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "nvidia/nemotron-3-super-120b-a12b:free"
    ENCRYPTION_MASTER_KEY: str
    FRONTEND_URL: str = "http://localhost:5173"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton of the application settings.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()
