# NeuroNest AI 🧠💜

NeuroNest AI is an emotionally intelligent voice assistant that goes far beyond a standard chatbot. It listens to **what you say** and **how you sound**, detects when you're hiding your true feelings, and responds with the warmth of a caring, wise mother — using gentle humor to bring you back to a calm, positive state.

---

## ✨ What Makes It Special

Unlike regular voice assistants, NeuroNest detects **contradiction** between your words and your voice:

- You say: *"I'm fine, everything is okay."*
- But your voice sounds: trembling, whimpering, withdrawn.
- NeuroNest catches this, understands you're hurting, and responds with empathy — not a scripted reply.

If you're **angry, sad, stressed, or anxious**, it responds with warmth and a gentle touch of humor to lift your spirits — like a mom who makes you smile even when you're crying.

- **Personalised Memory (RAG)**: It remembers your past conversations and emotional journey using Supabase pgvector, allowing it to reference previous sessions naturally and greet you based on how you were feeling last time.

---

## 🏗️ Architecture & Pipeline

```
Voice Input (Browser)
        │
        ▼
  FastAPI Backend
        │
   ┌────┴────────────────────────────────────────┐
   │                                             │
   ▼                                             ▼
Groq Whisper (STT)                    Web Audio API Features
   │  └─ fallback: OpenAI Whisper-1   (pitch, jitter, loudness,
   │                                   trembling, crying, etc.)
   ▼
openSMILE / librosa (Acoustic Analysis)
   │  └─ fallback: librosa → mock defaults
   │
   ▼
LLM Emotion Analysis (JSON)
   │  Waterfall: GPT-4o → Groq Llama-3.3-70B → GPT-4o-mini
   │             → Groq Llama-3.1-8B → Gemini 1.5 Flash
   │
   ▼
LLM Response Generation
   │  Same waterfall — empathetic, motherly tone
   │
   ▼
TTS Waterfall
   │  ElevenLabs → Cartesia → Deepgram → OpenAI TTS → LMNT → Murf AI
   │  └─ final fallback: Browser Web Speech API
   │
   ▼
Supabase (PostgreSQL + Storage)
   │  Logs interaction, uploads audio files
   │
   ▼
Voice Output (User)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Supabase](https://supabase.com) project (free tier works)
- At least one API key from the providers listed below

---

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd VoiceAssistant
```

---

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Create `backend/.env`

```ini
# ── LLM & STT Providers ──────────────────────────────────────────────
OPENAI_API_KEY=sk-...          # GPT-4o, GPT-4o-mini, Whisper-1, TTS-1
GROQ_API_KEY=gsk_...           # Llama-3.3-70B, Llama-3.1-8B, Whisper Large V3
GEMINI_API_KEY=AIza...         # Gemini 1.5 Flash (LLM fallback)

# ── TTS Providers (Waterfall) ────────────────────────────────────────
ELEVENLABS_API_KEY=sk_...      # Tier 1 TTS — most human voice
CARTESIA_API_KEY=...           # Tier 2 TTS — ultra-low latency
DEEPGRAM_API_KEY=...           # Tier 3 TTS — Aura-2 realistic voices
LMNT_API_KEY=...               # Tier 5 TTS — warm, soothing voices
MURF_API_KEY=...               # Tier 6 TTS — professional neural voices

# ── Supabase ─────────────────────────────────────────────────────────
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...            # Service role key (from Project Settings → API)
```

> You don't need all keys. The system automatically skips providers with missing keys and falls back to the next one.

#### Run the backend

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

---

### 3. Frontend Setup

```bash
cd frontend
npm install
```

#### Create `frontend/.env`

```ini
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...   # Anon/public key (from Project Settings → API)
VITE_SUPABASE_PUBLISHABLE_KEY=eyJ...  # Same anon key
```

#### Run the frontend

```bash
npm run dev
```

Open **http://localhost:5173** in your browser.

---

### 4. Supabase Setup

#### SQL Schema

Run the following SQL in your Supabase **SQL Editor** (`supabase/migrations/20260513_init.sql`):

```sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT,
    role TEXT DEFAULT 'patient',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS voice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES voice_sessions(id),
    user_id UUID REFERENCES users(id),
    transcript TEXT,
    raw_audio_url TEXT,
    pitch_mean FLOAT,
    jitter FLOAT,
    loudness FLOAT,
    emotion TEXT,
    stress_level INTEGER,
    tone TEXT,
    contradiction_detected BOOLEAN,
    hidden_emotion TEXT,
    response_text TEXT,
    tts_audio_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (open access for development)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public Access" ON users FOR ALL USING (true);
CREATE POLICY "Public Access" ON voice_sessions FOR ALL USING (true);
CREATE POLICY "Public Access" ON interactions FOR ALL USING (true);

-- Insert the default test user
INSERT INTO users (id, full_name, role)
VALUES ('00000000-0000-0000-0000-000000000000', 'Test User', 'patient')
ON CONFLICT (id) DO NOTHING;
```

#### Storage Buckets

Create two **Public** storage buckets in Supabase → Storage:

| Bucket Name | Purpose |
|---|---|
| `voice-recordings` | Stores raw `.webm` audio from the user's mic |
| `ai-responses` | Stores generated TTS `.mp3` responses |

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Frontend** | React 19 + Vite 8 + Tailwind CSS 4 |
| **Backend** | FastAPI (Python 3.11+) |
| **Speech-to-Text** | Groq Whisper Large V3 → OpenAI Whisper-1 |
| **LLM (Emotion + Response)** | GPT-4o → Groq Llama-3.3-70B → GPT-4o-mini → Groq Llama-3.1-8B → Gemini 1.5 Flash |
| **Acoustic Analysis** | openSMILE (eGeMAPSv02) → librosa → Browser Web Audio API |
| **Text-to-Speech** | ElevenLabs → Cartesia → Deepgram → OpenAI TTS → LMNT → Murf AI → Browser |
| **Database** | Supabase (PostgreSQL) |
| **Storage** | Supabase Storage Buckets |

---

## 🔄 API Rate Limit Failover System

NeuroNest uses a **rate-limit-aware waterfall** across all AI providers. When any provider returns a rate-limit error (HTTP 429 / quota exceeded), it is automatically placed in a **60-second cooldown** and skipped on all subsequent requests until the cooldown expires.

This means:
- No wasted latency retrying a provider that's already exhausted
- Instant failover to the next available provider
- Providers automatically recover and re-enter the rotation after cooldown
- Works independently for LLM, STT, and TTS waterfalls

### LLM Waterfall (5 tiers)

| Tier | Provider | Model | Notes |
|---|---|---|---|
| 1 | OpenAI | `gpt-4o` | Best quality |
| 2 | Groq | `llama-3.3-70b-versatile` | Fast, high quality |
| 3 | OpenAI | `gpt-4o-mini` | Lighter OpenAI model |
| 4 | Groq | `llama-3.1-8b-instant` | Ultra-fast, free tier |
| 5 | Google | `gemini-1.5-flash` | Final LLM fallback |

### STT Waterfall (2 tiers)

| Tier | Provider | Model |
|---|---|---|
| 1 | Groq | `whisper-large-v3` |
| 2 | OpenAI | `whisper-1` |

### TTS Waterfall (6 tiers + browser)

| Tier | Provider | Notes |
|---|---|---|
| 1 | ElevenLabs | Most human, best emotional range |
| 2 | Cartesia | Ultra-low latency, `sonic-2` model |
| 3 | Deepgram | Aura-2 ultra-realistic voices |
| 4 | OpenAI TTS | Robust neural voices (`tts-1`) |
| 5 | LMNT | Warm, soothing voices |
| 6 | Murf AI | Professional neural voices |
| 7 | Browser | Web Speech API — free, works offline |

---

## 🎙️ Voice Models

Five AI voice personas are available, each mapped to a voice ID across all TTS providers:

| Name | Gender | ElevenLabs | OpenAI | Deepgram |
|---|---|---|---|---|
| Amelia | Female | Bella | shimmer | aura-2-thalia-en |
| Rachel | Female | Rachel | alloy | aura-2-thalia-en |
| Josh | Male | Dave | echo | aura-2-orion-en |
| Nathan | Male | Charlie | onyx | aura-2-stella-en |
| Sam | Male | Fin | fable | aura-2-arcas-en |

You can preview any voice before starting a session using the **Preview** button in the UI.

---

## 🧠 Emotion Detection

NeuroNest performs a two-layer emotion analysis:

### Layer 1 — Acoustic Features
Extracted from the raw audio using one of three methods (in priority order):

1. **Browser Web Audio API** — real-time RMS volume, spectral centroid, std deviations. Detects: trembling, crying, whispering, singing, shaking voice.
2. **openSMILE** — `eGeMAPSv02` feature set: F0 (pitch), jitter, loudness.
3. **librosa** — pitch tracking, RMS energy, zero-crossing rate.
4. **Mock defaults** — used only if all above fail.

### Layer 2 — LLM Emotion Analysis
The transcript + acoustic features are sent to the LLM waterfall with a structured prompt. The LLM returns a JSON object:

```json
{
  "emotion": "sadness",
  "stress_level": 72,
  "tone": "trembling",
  "contradiction_detected": true,
  "hidden_emotion": "hiding sadness"
}
```

**Contradiction detection** is the key feature: if the words say "I'm fine" but the voice features indicate distress, `contradiction_detected` is `true` and `hidden_emotion` describes what's really going on.

---

## 💬 Response Generation

The AI response is generated by the same LLM waterfall using a carefully crafted system prompt that:

- Adapts tone based on detected emotion and stress level
- For **negative emotions** (anger, sadness, anxiety, fear, stress > 60): uses a warm, motherly tone with one gentle joke to de-escalate
- For **neutral/positive emotions**: warm, encouraging, conversational
- If **contradiction is detected**: gently acknowledges the hidden emotion and creates a safe space to open up
- Keeps responses short (2–4 sentences) — optimized for spoken delivery
- Never sounds clinical or robotic

---

## 📊 Session Dashboard

Each voice interaction is logged to an in-memory dashboard (resets on server restart) and persisted to Supabase. The dashboard tracks:

- Transcript text
- Detected emotion
- Stress level (0–100)

The full interaction record in Supabase includes all audio features, emotion data, AI response text, and URLs to both the raw audio and TTS response audio.

---

## 🔌 API Endpoints

All endpoints are served at `http://localhost:8000`.

### `POST /process-voice`

The main pipeline endpoint. Accepts `multipart/form-data`.

**Request fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | ✅ | `.webm` audio recording from the browser |
| `audio_analysis` | String (JSON) | ❌ | Web Audio API features from the frontend |
| `voice_name` | String | ❌ | TTS voice to use (default: `Rachel`) |

**Response:**

```json
{
  "transcript": "I'm fine, everything is okay.",
  "audio_features": {
    "pitch_mean": 45.2,
    "jitter": 0.08,
    "loudness": 0.12,
    "is_trembling": true,
    "is_crying": false,
    "voice_description": "trembling or unstable voice",
    "source": "browser_web_audio_api"
  },
  "emotion": {
    "emotion": "sadness",
    "stress_level": 72,
    "tone": "trembling",
    "contradiction_detected": true,
    "hidden_emotion": "hiding sadness"
  },
  "response": "I hear you saying you're okay, but your voice tells me something else...",
  "audio_url": "http://localhost:8000/audio/abc123.mp3",
  "dashboard": [...]
}
```

---

### `POST /preview-voice`

Generates a short TTS preview for the selected voice.

**Request fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `voice_name` | String | ✅ | Voice to preview (e.g., `Rachel`, `Josh`) |

**Response:**

```json
{
  "audio_url": "http://localhost:8000/audio/preview-abc123.mp3"
}
```

---

### `GET /audio/{filename}`

Serves a generated MP3 file from the `backend/generated/` directory.

**Example:** `GET /audio/abc123.mp3`

---

## 📁 Project Structure

```
VoiceAssistant/
├── README.md
├── .gitignore
│
├── backend/
│   ├── main.py                    # FastAPI app — 3 routes
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # API keys (do not commit)
│   │
│   ├── core/
│   │   ├── config.py              # Pydantic settings, loads .env
│   │   └── logger.py              # Structured stdout logger
│   │
│   ├── models/
│   │   └── interaction.py         # Pydantic models: AudioFeatures, EmotionData, InteractionCreate
│   │
│   ├── repositories/
│   │   └── interaction_repo.py    # Supabase client — DB + Storage operations
│   │
│   ├── services/
│   │   ├── model_manager.py       # LLM + STT waterfall with rate-limit failover ⭐
│   │   ├── whisper_service.py     # STT entry point → model_manager
│   │   ├── opensmile_service.py   # Acoustic feature extraction (3-tier fallback)
│   │   ├── emotion_service.py     # LLM-based emotion analysis → JSON
│   │   ├── response_service.py    # LLM-based empathetic response generation
│   │   ├── tts_service.py         # TTS waterfall with rate-limit failover ⭐
│   │   ├── rag_service.py         # Personalized memory (OpenAI embeddings + pgvector) ⭐
│   │   └── dashboard_service.py   # In-memory session history
│   │
│   ├── debug_deepgram.py          # Diagnostic for Deepgram Aura-2
│   ├── test_rag_rpc.py            # Diagnostic for Supabase RAG functions
│   ├── test_tts_voices.py         # Comprehensive TTS waterfall stress test
│   ├── generated/                 # TTS output MP3 files (auto-created)
│   └── uploads/                   # Temporary audio uploads (auto-created)
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── .env                       # Supabase anon key (do not commit)
│   └── src/
│       ├── main.jsx               # React entry point
│       ├── App.jsx                # App shell
│       └── components/
│           └── VoiceAssistant.jsx # Main UI component
│
└── supabase/
    └── migrations/
        ├── 20260513_init.sql      # Database schema
        └── 20260515_rag.sql       # RAG memory & pgvector schema
```

---

## 🖥️ Frontend Features

The React frontend (`VoiceAssistant.jsx`) provides:

- **Mic recording** — one-click record/stop with visual feedback
- **Real-time audio analysis** — Web Audio API samples voice features every 80ms during recording
- **Personalised Greetings** — shows a warm welcome based on your last session's emotion ⭐
- **Voice selector** — choose from 5 AI voice personas with a live preview button
- **Emotion display** — shows detected emotion, stress level (0–100), tone, and contradiction alerts
- **AI response display** — shows the text response alongside the audio playback
- **Speaking indicator** — animated waveform while TTS audio plays
- **Credits tracker** — tracks daily API request count in `localStorage` (resets at midnight)
- **Browser TTS fallback** — if all backend TTS providers fail, uses `window.speechSynthesis`
- **Error handling** — clear error messages if the backend is unreachable

---

## ⚙️ Configuration Reference

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Recommended | GPT-4o, GPT-4o-mini, Whisper-1, TTS-1 |
| `GROQ_API_KEY` | Recommended | Llama-3.3-70B, Llama-3.1-8B, Whisper Large V3 (free tier) |
| `GEMINI_API_KEY` | Optional | Gemini 1.5 Flash — LLM last resort |
| `ELEVENLABS_API_KEY` | Optional | TTS Tier 1 — best voice quality |
| `CARTESIA_API_KEY` | Optional | TTS Tier 2 — low latency |
| `DEEPGRAM_API_KEY` | Optional | TTS Tier 3 — Aura-2 voices |
| `LMNT_API_KEY` | Optional | TTS Tier 5 — warm voices |
| `MURF_API_KEY` | Optional | TTS Tier 6 — professional voices |
| `SUPABASE_URL` | Required | Your Supabase project URL |
| `SUPABASE_KEY` | Required | Supabase service role key |

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|---|---|---|
| `VITE_SUPABASE_URL` | Required | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Required | Supabase anon/public key |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Required | Same as anon key |

---

## 🔒 Security Notes

- **Never commit `.env` files** to version control. Add them to `.gitignore`.
- The `SUPABASE_KEY` (service role key) has full database access — keep it server-side only.
- The `VITE_SUPABASE_ANON_KEY` is safe to expose in the frontend (it's the public key).
- CORS is currently set to `allow_origins=["*"]` — restrict this to your frontend domain in production.

---

## 🐛 Troubleshooting

**Backend won't start**
- Make sure your virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check that `SUPABASE_URL` and `SUPABASE_KEY` are set in `.env`

**"Failed to process voice. Is the backend running?"**
- Ensure the backend is running on port 8000: `uvicorn main:app --reload --port 8000`
- Check browser console for CORS errors

**No audio plays after response**
- If all TTS providers fail, the browser Web Speech API is used as fallback
- Check backend logs for which TTS provider succeeded or failed
- Verify at least one TTS API key is set in `.env`

**Transcription returns "[Inaudible or audio error]"**
- Both Groq Whisper and OpenAI Whisper failed — check your API keys
- Ensure the audio recording is not empty (speak for at least 1–2 seconds)

**Rate limit errors in logs**
- This is expected behavior — the system automatically switches to the next provider
- Providers recover after a 60-second cooldown
- Add more API keys to increase resilience

**openSMILE not working**
- openSMILE requires native binaries. If it fails, the system falls back to librosa automatically.
- The browser Web Audio API features (sent from the frontend) take priority over both.

---

## 📦 Dependencies

### Backend

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `openai` | GPT-4o, Whisper-1, TTS-1 |
| `groq` | Llama models, Whisper Large V3 |
| `google-generativeai` | Gemini 1.5 Flash |
| `elevenlabs` | TTS Tier 1 |
| `cartesia` | TTS Tier 2 |
| `deepgram-sdk` | TTS Tier 3 |
| `opensmile` | Acoustic feature extraction |
| `librosa` | Audio analysis fallback |
| `supabase` | Database + Storage client |
| `pydantic-settings` | Config management |
| `python-dotenv` | `.env` file loading |

### Frontend

| Package | Purpose |
|---|---|
| `react` + `react-dom` | UI framework |
| `vite` | Build tool + dev server |
| `tailwindcss` | Utility-first CSS |
| `axios` | HTTP client for API calls |
| `lucide-react` | Icon library |
| `@supabase/supabase-js` | Supabase client |

---

*Built with ❤️ — Powered by Groq's free tier, with multi-provider fallback for zero-downtime AI.*
