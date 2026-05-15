# NeuroNest Backend — Complete Technical Documentation

## Overview

The NeuroNest backend is a **FastAPI** application built in Python 3.14. It powers the AI wellness chatbot with a multi-node LangGraph pipeline, multi-LLM fallback routing, context-aware mood detection, RAG memory, and AES-256-GCM encrypted Supabase storage.

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Web Framework** | FastAPI | 0.136+ | REST API, async request handling, auto Swagger docs |
| **ASGI Server** | Uvicorn | 0.46+ | Production-grade async server with hot reload |
| **Language** | Python | 3.14 | Runtime |
| **AI Orchestration** | LangGraph | 1.2+ | 5-node stateful pipeline for wellness conversations |
| **LLM Framework** | LangChain | 1.3+ | LLM abstraction, message formatting |
| **LLM Primary** | OpenAI GPT-4o | via API | Main language model for responses |
| **LLM Fallback 1** | Groq Llama-3.3-70B | via API | Fast fallback when OpenAI quota runs out |
| **LLM Fallback 2** | Google Gemini 1.5 Flash | via API | Second fallback |
| **LLM Fallback 3** | Built-in local responses | — | Works with zero API keys |
| **Voice STT** | OpenAI Whisper | whisper-1 | Speech-to-text transcription |
| **Encryption** | cryptography (AES-256-GCM) | 48.0+ | End-to-end message encryption |
| **Key Derivation** | HKDF-SHA256 | built-in | Per-user unique encryption keys |
| **Database Client** | httpx (direct REST) | 0.28+ | Supabase REST API calls |
| **Data Validation** | Pydantic v2 | 2.13+ | Request/response schemas |
| **Settings** | pydantic-settings | 2.14+ | .env file loading |
| **HTTP Client** | httpx | 0.28+ | Async HTTP for Supabase |

---

## Architecture — A to Z

```
HTTP Request
     │
     ▼
FastAPI (main.py)
     │
     ├── CORS Middleware
     ├── Global Exception Handler
     │
     ├── /api/chat/     ──► ChatRouter
     ├── /api/voice/    ──► VoiceRouter
     ├── /api/mood/     ──► MoodRouter
     ├── /api/db/       ──► DatabaseRouter
     └── /api/memory/   ──► MemoryRouter
              │
              ▼
     process_chat() ──► LangGraph Pipeline
              │
    ┌─────────┼──────────────────────────────┐
    │         │                              │
    ▼         ▼                              ▼
Node 1    Node 2              Node 3      Node 4      Node 5
detect_   retrieve_           generate_   generate_   special_
mood      memory(RAG)         response    activities  action
    │         │                   │           │           │
    ▼         ▼                   ▼           ▼           ▼
mood_     memory_            llm_router  activity_   special_
detector  agent.py           .py         generator   actions
    │         │                   │           │           │
    ▼         ▼                   ▼           ▼           ▼
keyword   TF-IDF             OpenAI→     emotion-    jokes+
+GPT-4o   cosine             Groq→       specific    proverbs+
detect    similarity         Gemini→     activities  music+
          search             Local                   breathing
              │
              ▼
     ChatResponse (Pydantic)
              │
              ▼
     save_full_chat_turn()
              │
              ▼
     encrypt(content, user_id)  ← AES-256-GCM
              │
              ▼
     Supabase REST API
     (stores ciphertext only)
```

---

## File Structure — Every File Explained

```
backend/
├── run.py                          # Entry point — starts Uvicorn server
├── requirements.txt                # Python dependencies
├── .env                            # API keys and config (never commit)
├── .env.example                    # Template for .env
├── supabase_setup.sql              # SQL to create tables in Supabase
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, CORS, routers, lifespan
│   ├── config.py                   # Settings loaded from .env via pydantic-settings
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # All Pydantic models (request/response schemas)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── wellness_agent.py       # LangGraph 5-node pipeline — core of the chatbot
│   │   ├── mood_detector.py        # Emotion detection: priority override + GPT-4o + keywords
│   │   ├── llm_router.py           # Multi-LLM fallback: OpenAI → Groq → Gemini → Local
│   │   ├── activity_generator.py   # Emotion-specific activity suggestions
│   │   ├── special_actions.py      # Jokes, proverbs, music tracks, breathing exercises
│   │   └── memory_agent.py         # RAG memory: TF-IDF storage and retrieval
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py                 # POST /api/chat/ — main chat endpoint
│   │   ├── voice.py                # POST /api/voice/analyze — Whisper STT
│   │   ├── mood.py                 # POST /api/mood/checkin — mood check-in
│   │   ├── db.py                   # GET/POST /api/db/* — encryption verification
│   │   └── memory.py               # GET /api/memory/* — RAG memory management
│   │
│   └── services/
│       ├── __init__.py
│       ├── encryption.py           # AES-256-GCM encrypt/decrypt functions
│       ├── database.py             # Supabase REST API client (direct HTTP)
│       └── voice_service.py        # Whisper transcription pipeline
│
└── data/
    └── memory/                     # Local RAG memory storage (auto-created)
        └── {user_id}.json          # Per-user conversation summaries
```

---

## Detailed File Descriptions

### `run.py`
Entry point for the development server. Runs Uvicorn with hot reload enabled.
```python
uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

---

### `app/main.py`
The FastAPI application instance. Responsibilities:
- Creates the FastAPI app with title, description, version
- Adds CORS middleware (allows localhost:3000 and Vercel deployments)
- Registers all 5 routers (chat, voice, mood, db, memory)
- Lifespan handler: prints startup status for all configured services
- Global exception handler: returns clean JSON errors

---

### `app/config.py`
Loads all environment variables from `.env` using pydantic-settings.
Fields: `openai_api_key`, `groq_api_key`, `gemini_api_key`, `supabase_url`, `supabase_anon_key`, `supabase_service_key`, `secret_key`, `environment`.
Uses `@lru_cache` so settings are loaded once and reused.

---

### `app/models/schemas.py`
All Pydantic v2 data models:

| Model | Purpose |
|-------|---------|
| `EmotionType` | Enum: stressed, anxious, sad, angry, happy, calm, overwhelmed, lonely, excited, neutral |
| `MoodLevel` | Enum: very_bad, bad, neutral, good, very_good |
| `ChatMessage` | Single message: role + content |
| `ChatRequest` | Incoming chat: message, user_id, session_id, conversation_history |
| `ActivitySuggestion` | Single activity: title, description, duration, category, emoji |
| `MusicTrack` | Single track: title, artist, spotify_url, youtube_url, reason |
| `ChatResponse` | Full AI response with all fields |
| `VoiceAnalysisResponse` | Voice pipeline result |
| `MoodCheckIn` | Mood check-in request |

---

### `app/agents/wellness_agent.py`
The core of the chatbot. A **LangGraph StateGraph** with 5 nodes:

**Node 1 — `detect_mood_node`**
Calls `mood_detector.detect_mood()` with the user message and conversation history.
Returns detected emotion and mood level.

**Node 2 — `retrieve_memory_node`**
If `user_id` is provided, calls `memory_agent.retrieve_relevant_memories()`.
Uses TF-IDF cosine similarity to find relevant past sessions.
Injects retrieved context into the system prompt.

**Node 3 — `generate_response_node`**
Builds the LLM prompt with:
- Emotion-specific system prompt (10 different prompts, one per emotion)
- RAG memory context (past sessions)
- Emotional journey context (what the user shared earlier in this conversation)
- Follow-up context (if this is a reply to a previous question)
Calls `llm_router.invoke_with_fallback()`.

**Node 4 — `generate_activities_node`**
Determines `response_mode` (support/celebrate/reflect).
- `support` → returns 5 emotion-specific activities
- `celebrate` (happy/excited) → returns celebration message, NO activities
- `reflect` (calm) → returns reflection message, NO activities

**Node 5 — `special_action_node`**
Generates: joke (emotion-specific), proverb (from mental wellness scientists), music tracks (3 with Spotify/YouTube links), breathing exercise (for high-distress states).

Also contains:
- `EMOTION_PROMPTS` — 10 detailed system prompts, one per emotion
- `_build_emotional_journey()` — extracts emotional arc from conversation history
- `_detect_situation()` — detects specific situations (job, exam, promotion, etc.)
- `get_celebration_message()` — situation-aware celebration cards

---

### `app/agents/mood_detector.py`
Context-aware emotion detection with three layers:

**Layer 1 — Priority Override**
Achievement phrases like "I passed my exam", "I got a job", "feeling good today" always return happy regardless of other words. Prevents "exam" from triggering stressed when context is positive.

**Layer 2 — Keyword Detection**
`EMOTION_KEYWORDS` dict maps 9 emotions to keyword lists.
`MOOD_KEYWORDS` dict maps 5 mood levels to keyword lists.
Scores each emotion by counting keyword matches. Highest score wins.

**Layer 3 — GPT-4o API Detection**
Sends the message + conversation history to GPT-4o for nuanced detection.
Falls back to keyword result if API fails.

**Context inheritance**: If current message has no emotion signal, inherits prior emotion from conversation history. But positive emotions (happy/excited/calm) are NEVER overridden by prior negative context.

---

### `app/agents/llm_router.py`
Multi-provider LLM fallback chain:

```
OpenAI GPT-4o → Groq Llama-3.3-70B → Gemini 1.5 Flash → Local responses
```

`LOCAL_FALLBACKS` — 4 unique responses per emotion (10 emotions × 4 = 40 responses).
`_get_contextual_followup()` — situation-specific responses (job, exam, promotion, celebrity, etc.).
All local responses are natural, warm, and varied — no "Oh sweetheart" openers.

---

### `app/agents/activity_generator.py`
`ACTIVITY_BANK` — 6-7 unique activities per emotion (7 emotions × 7 = ~49 activities).
Activities are shuffled on every response for variety.
`NO_ACTIVITY_EMOTIONS` — happy, excited, calm return empty list (celebration card shown instead).
Very bad mood always leads with emergency breathing exercise.

---

### `app/agents/special_actions.py`
Four types of special content:

| Type | Content |
|------|---------|
| `EMOTION_JOKES` | 3-5 jokes per emotion, wellness-themed |
| `EMOTION_PROVERBS` | 3-5 quotes per emotion from real mental health experts |
| `MUSIC_TRACKS` | 3 tracks per emotion with Spotify + YouTube URLs |
| `BREATHING_EXERCISES` | 3 exercises: 4-7-8, Box Breathing, Physiological Sigh |

---

### `app/agents/memory_agent.py`
Local RAG (Retrieval-Augmented Generation) memory system:

**Storage**: `backend/data/memory/{user_id}.json`

**How it works**:
1. `save_message_to_memory()` — saves each message with emotion tags
2. `generate_session_summary()` — LLM generates 3-4 sentence summary after session
3. `retrieve_relevant_memories()` — TF-IDF cosine similarity search
4. `format_memory_context()` — formats retrieved memories for LLM injection

**TF-IDF implementation**: Pure Python, no external ML libraries. Tokenizes text, computes term frequency × inverse document frequency, calculates cosine similarity between query and stored memories.

---

### `app/routers/chat.py`
`POST /api/chat/` — Main chat endpoint.
1. Generates session_id if not provided
2. Calls `process_chat()` with user_id for RAG memory
3. Saves encrypted conversation to Supabase if user_id provided
4. Returns full `ChatResponse`

---

### `app/routers/voice.py`
`POST /api/voice/analyze` — Voice check-in endpoint.
Accepts audio file (webm, wav, mp3, ogg, mp4).
Calls `voice_service.analyze_voice()` → Whisper → wellness pipeline.
Returns `VoiceAnalysisResponse` with transcription + full chat response.

---

### `app/routers/mood.py`
`POST /api/mood/checkin` — Simple mood check-in.
Accepts mood level + emotion list.
Returns activities and wellness tip without LLM call.

---

### `app/routers/db.py`
Encryption verification and history endpoints:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/db/test-encryption` | Encrypt any text, show ciphertext vs plaintext |
| `GET /api/db/raw/{session_id}` | View raw encrypted data in Supabase |
| `GET /api/db/verify/{session_id}` | Side-by-side ciphertext vs decrypted |
| `GET /api/db/history/{session_id}` | Decrypted conversation history |
| `GET /api/db/health` | Supabase connection status |

---

### `app/routers/memory.py`
RAG memory management endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/memory/user/{user_id}` | View all stored memories |
| `GET /api/memory/user/{user_id}/search` | Search memories by query |
| `POST /api/memory/summarize` | Save session summary |
| `DELETE /api/memory/user/{user_id}` | Clear all memories |
| `GET /api/memory/health` | Storage status |

---

### `app/services/encryption.py`
AES-256-GCM encryption with HKDF-SHA256 key derivation.
See `DATABASE_README.md` for full encryption details.

Key functions:
- `encrypt(plaintext, user_id)` → base64 ciphertext
- `decrypt(ciphertext, user_id)` → plaintext
- `is_encrypted(value)` → bool (checks if value looks like valid ciphertext)
- `_derive_key(user_id)` → 32-byte key (private, used internally)

---

### `app/services/database.py`
Supabase REST API client using direct HTTP (no supabase Python package).
All message content is encrypted before storage.
Timestamps are NOT sent from Python — Supabase uses `DEFAULT NOW()` for accuracy.

Key functions:
- `save_chat_message()` — encrypts and saves one message
- `save_session()` — creates/updates session record
- `get_session_history()` — fetches and decrypts conversation
- `save_full_chat_turn()` — saves user + assistant messages together
- `verify_encryption_in_db()` — shows ciphertext vs plaintext for verification

---

### `app/services/voice_service.py`
Whisper transcription pipeline:
1. Detects supported MIME type (webm, wav, mp3, ogg, mp4)
2. Writes audio to temp file
3. Calls OpenAI Whisper API
4. Cleans up temp file
5. Passes transcription through full wellness pipeline

---

## API Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat/` | Send wellness chat message |
| GET | `/api/chat/health` | Chat service health |
| POST | `/api/voice/analyze` | Voice check-in (audio upload) |
| GET | `/api/voice/health` | Voice service health |
| POST | `/api/mood/checkin` | Mood check-in |
| GET | `/api/mood/health` | Mood service health |
| POST | `/api/db/test-encryption` | Test AES-256-GCM encryption |
| GET | `/api/db/raw/{session_id}` | View raw encrypted DB data |
| GET | `/api/db/verify/{session_id}` | Verify encryption side-by-side |
| GET | `/api/db/history/{session_id}` | Get decrypted history |
| GET | `/api/db/health` | Supabase connection status |
| GET | `/api/memory/user/{user_id}` | View RAG memories |
| GET | `/api/memory/user/{user_id}/search` | Search memories |
| POST | `/api/memory/summarize` | Save session summary |
| DELETE | `/api/memory/user/{user_id}` | Clear memories |
| GET | `/api/memory/health` | Memory storage status |
| GET | `/health` | Backend health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc UI |

---

## Environment Variables

```env
# AI Providers (at least one required)
OPENAI_API_KEY=sk-proj-...      # platform.openai.com/api-keys
GROQ_API_KEY=gsk_...            # console.groq.com (free, fast)
GEMINI_API_KEY=AIza...          # aistudio.google.com (free)

# Supabase (optional — chat works without it)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# Encryption (required for Supabase storage)
SECRET_KEY=your-32-char-minimum-secret-key

# Server
ENVIRONMENT=development
```

---

## LangGraph Pipeline Flow

```
User Message
     │
     ▼
[Node 1] detect_mood
  - Priority override (achievement/positive phrases → always happy)
  - Keyword scoring (9 emotions × keyword lists)
  - GPT-4o API detection with conversation context
  - Positive emotion guard (happy/excited/calm never overridden by prior negative)
     │
     ▼
[Node 2] retrieve_memory (RAG)
  - Load user's memory file from data/memory/{user_id}.json
  - TF-IDF vectorize current message
  - Cosine similarity search against stored summaries
  - Format top-3 relevant memories as context string
     │
     ▼
[Node 3] generate_response
  - Select emotion-specific system prompt (10 prompts)
  - Inject RAG memory context
  - Build emotional journey from conversation history
  - Add follow-up context if replying to a question
  - Call LLM Router: OpenAI → Groq → Gemini → Local
     │
     ▼
[Node 4] generate_activities
  - Determine response_mode: support / celebrate / reflect
  - support: return 5 shuffled emotion-specific activities
  - celebrate/reflect: return celebration message, empty activities
     │
     ▼
[Node 5] special_action
  - Get emotion-specific joke
  - Get proverb from mental wellness scientist
  - Get 3 music tracks with Spotify + YouTube links
  - Get breathing exercise (for high-distress states only)
     │
     ▼
ChatResponse (returned to frontend)
     │
     ▼
save_full_chat_turn() [async, non-blocking]
  - encrypt(user_message, user_id) → ciphertext
  - encrypt(ai_response, user_id) → ciphertext
  - POST to Supabase REST API
```

---

## Quick Start

```cmd
cd backend
venv\Scripts\activate
python run.py
```

Swagger UI: **http://localhost:8000/docs**
