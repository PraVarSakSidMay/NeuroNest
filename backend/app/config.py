from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_model: str = "inclusionai/ring-2.6-1t:free"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "dev-secret-key"
    environment: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
