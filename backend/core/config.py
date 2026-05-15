import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    CARTESIA_API_KEY: str = os.getenv("CARTESIA_API_KEY", "")
    LMNT_API_KEY: str = os.getenv("LMNT_API_KEY", "")
    MURF_API_KEY: str = os.getenv("MURF_API_KEY", "")
    
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Storage Buckets
    VOICE_BUCKET: str = "voice-recordings"
    TTS_BUCKET: str = "ai-responses"
    
    # Dirs
    UPLOAD_DIR: str = "uploads"
    GENERATED_DIR: str = "generated"

    # RAG / Embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    RAG_TOP_K: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
