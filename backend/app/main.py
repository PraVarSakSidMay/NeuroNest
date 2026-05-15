"""NeuroNest Backend — FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.routers import chat, voice, mood, db, memory
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🧠 NeuroNest Backend starting up...")
    print(f"   Environment: {settings.environment}")
    print(f"   OpenAI:   {'✅' if settings.openai_api_key and 'your_' not in settings.openai_api_key else '❌ not set'}")
    print(f"   Groq:     {'✅' if settings.groq_api_key and 'your_' not in settings.groq_api_key else '⚠️  not set'}")
    print(f"   Gemini:   {'✅' if settings.gemini_api_key and 'your_' not in settings.gemini_api_key else '⚠️  not set'}")
    supabase_ok = bool(settings.supabase_url) and "your_supabase" not in settings.supabase_url and bool(settings.supabase_service_key) and "your_supabase" not in settings.supabase_service_key
    print(f"   Supabase: {'✅ (encrypted storage active)' if supabase_ok else '⚠️  not configured (chat still works)'}")
    print(f"   Encryption: AES-256-GCM with HKDF-SHA256 key derivation")
    yield
    print("🧠 NeuroNest Backend shutting down...")


app = FastAPI(title="NeuroNest API", description="🧠 NeuroNest — AI-Powered Mental Wellness Companion", version="1.0.0", lifespan=lifespan, docs_url="/docs", redoc_url="/redoc")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:3001", "https://*.vercel.app", "*" if settings.environment == "development" else ""], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(chat.router)
app.include_router(voice.router)
app.include_router(mood.router)
app.include_router(db.router)
app.include_router(memory.router)


@app.get("/", tags=["Root"])
async def root():
    return {"app": "NeuroNest", "version": "1.0.0", "status": "running", "docs": "/docs", "crisis_resources": {"india": "iCall: 9152987821", "us": "988 Suicide & Crisis Lifeline"}}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "app": "NeuroNest", "environment": settings.environment}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": "An unexpected error occurred.", "detail": str(exc)})
