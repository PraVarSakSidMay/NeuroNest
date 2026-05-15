# 🧠 NeuroNest — AI-Powered Mental Wellness Companion

> An AI-powered mental wellness chatbot built for a 24-hour hackathon. Conversations feel warm and human — like talking to a caring friend or supportive parent, never a robot.

---

## 🚀 Quick Start

### Terminal 1 — Backend
```cmd
cd backend
venv\Scripts\activate
python run.py
```
Backend: **http://localhost:8000** | Swagger Docs: **http://localhost:8000/docs**

### Terminal 2 — Frontend
```cmd
cd frontend
npm run dev
```
Frontend: **http://localhost:3000**

> Both terminals must stay open simultaneously.

---

## ⚙️ Environment Setup

Open `backend\.env` and fill in your keys:

```env
# ── AI Provider Keys — fallback order: OpenRouter → OpenAI → Groq → Gemini ──────────────
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-proj-...
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...

# Supabase — encrypted chat storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# Encryption master key
SECRET_KEY=neuronest-aes256-secret-change-this-in-production-use-32-chars-min

```

### Free API Keys

| Provider | URL | Notes |
|----------|-----|-------|
| OpenRouter | [openrouter.ai](https://openrouter.ai/) | Free models available, primary API |
| OpenAI | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | $5 credit on signup |
| Groq | [console.groq.com](https://console.groq.com) | Very generous free tier, very fast |
| Gemini | [aistudio.google.com](https://aistudio.google.com) | Free tier available |
| Supabase | [supabase.com](https://supabase.com) | Free tier, no credit card needed |

---

## ✨ Features

### 1. AI Wellness Chatbot — Natural, Human Tone
- Responses feel like a caring friend or supportive parent — warm, genuine, never robotic
- Reads the user's **specific situation** and responds to it directly
- If you say "I am happy that I passed my exam" → it reacts to the **exam** specifically, not just "happiness"
- If you say "I am happy" without a reason → it asks what's making you feel that way
- 10 emotion types: stressed, anxious, sad, angry, happy, calm, overwhelmed, lonely, excited, neutral

### 2. Smart Emotion Detection with Priority Override
- **Achievement phrases always map to happy** — "I passed my exam", "I got a job", "I graduated" are never misdetected as stressed
- Context-aware: "exam" in a happy context (passed exam) ≠ "exam" in a stressed context
- Keyword detection with conversation history inheritance
- GPT-4o structured detection with keyword fallback (works even without API)

### 3. Conversation Context Awareness
- Remembers the full conversation — follow-up messages stay in context
- Builds an **emotional journey** from the conversation history
- If user was happy about passing exam, then says "I feel lonely" → response acknowledges the contrast: *"Even though you just had such a wonderful achievement, it's really touching that you're feeling lonely now..."*
- Prior emotion inherited when current message has no strong signal

### 4. Smart Response Modes

| Mode | Triggered by | What appears |
|------|-------------|--------------|
| **Support** | stressed, anxious, sad, angry, overwhelmed, lonely, neutral | Proverb + Breathing/Joke + Music + Wellness tip + 5 activities |
| **Celebrate** | happy, excited | Proverb + **Situation-aware celebration** + Music + Joke |
| **Reflect** | calm | Proverb + Reflection message + Music + Joke |

### 5. AI-Generated Celebration Cards
When you're happy, the celebration card reacts to your **specific situation** organically. Instead of relying on hardcoded templates, the AI directly crafts genuine celebration messages based on your exact situation (passing an exam, getting a job, etc.) and avoids canned responses.

### 6. Emotion-Specific Activities (Support Mode Only)
Activities are deeply matched to each emotion — not generic wellness advice:

| Emotion | Sample activities |
|---------|-----------------|
| Stressed | Brain dump, 4-7-8 breathing, walk away, cancel one thing |
| Anxious | 5-4-3-2-1 grounding, fact-check the worry, box breathing |
| Sad | Feel it fully, text someone, write to yourself, child's pose |
| Angry | Burn adrenaline, anger letter, long exhale, 10-min rule |
| Overwhelmed | 2-min task, brain dump, step away, ask for help |
| Lonely | Go somewhere with people, start a conversation, join a community |
| Happy / Excited / Calm | ❌ No activities — celebration/reflection card shown instead |

### 7. Multi-LLM Fallback (OpenRouter → OpenAI → Groq → Gemini)
- Tries OpenRouter (e.g. `inclusionai/ring-2.6-1t:free`) first
- If quota runs out → automatically falls back to OpenAI GPT-4o
- If OpenAI fails → falls back to Groq Llama-3.3-70B
- If Groq fails → falls back to Google Gemini 1.5 Flash
- If all APIs fail → returns a clean connectivity error message rather than pretending to be the AI.
- Zero downtime — user is smoothly transitioned between providers automatically.

### 9. End-to-End Encrypted Storage (Supabase)
- All conversation data is **AES-256-GCM encrypted before being sent to Supabase**
- Supabase only ever stores ciphertext — even admins cannot read it
- Each user gets a unique encryption key derived via HKDF-SHA256
- Uses direct HTTP REST API — no supabase Python package dependency issues
- Verification endpoint proves the DB contains only ciphertext

### 10. Voice Check-ins (Whisper)
- Click the 🎙️ mic button and speak how you're feeling
- Audio transcribed via OpenAI Whisper
- Transcribed text goes through the full wellness pipeline

### 11. Text-to-Speech — Auto-Speaks Every Response
- Every AI response **automatically speaks** when it arrives
- Choose **Female** (♀) or **Male** (♂) voice
- **🔊 Auto** toggle — turn auto-speak on/off
- **Replay** button to hear the response again
- Uses browser's Web Speech API — no extra cost
- Responses are longer since they're read aloud (800 tokens)

### 12. Emotion-Specific Jokes
- Every response includes a joke matched to the user's emotion
- Angry → jokes about letting go and perspective
- Stressed → jokes about rest and taking breaks
- Never offensive, always wellness-themed

### 13. Music with Spotify + YouTube Buttons
- 3 tracks recommended per emotion with direct clickable buttons
- **Green Spotify button** → opens Spotify directly
- **Red YouTube button** → opens YouTube search as fallback
- Angry → peaceful instrumental | Anxious → nature sounds | Lonely → connection songs

### 14. Proverbs from Mental Wellness Scientists
- Every response includes a real quote from a mental health expert
- Angry → Ralph Waldo Emerson, Buddha, Seneca
- Lonely → Dr. Vivek Murthy, Brené Brown
- Sad → Rumi, Victor Hugo
- Anxious → Dr. Daniel Siegel, Walter Anderson

---

## 🏗️ Architecture

```
User (Browser)
      │
      ▼
Next.js Frontend (port 3000)
  ├── ChatInput — text + voice + quick prompts
  ├── MessageBubble — mode-aware renderer
  │     ├── TTSControls — auto-speak + replay + ♀/♂ voice
  │     ├── ProverbCard — scientist quote
  │     ├── SpecialActionCard — breathing exercise
  │     ├── JokeCard — emotion-specific joke
  │     ├── MusicCard — Spotify + YouTube buttons
  │     ├── CelebrationCard — situation-aware (replaces activities for happy/excited/calm)
  │     ├── WellnessTip — mood-level tip
  │     └── ActivityCard × 5 — emotion-specific activities (support mode only)
  └── VoiceRecorder — mic → Whisper
      │
      ▼
FastAPI Backend (port 8000)
      │
      ▼
LangGraph Pipeline (5 nodes)
  1. detect_mood       — Priority override + GPT-4o + keyword fallback + history context
  2. retrieve_memory   — Pass-through node (disabled for live responses, ensuring direct AI access)
  3. generate_response — LLM Router (OpenRouter → OpenAI → Groq → Gemini) + emotional journey context
  4. generate_activities — mode-aware (support=5 activities, celebrate/reflect=0)
  5. special_action    — joke + proverb + situation-aware music + breathing
      │
      ▼
Supabase (AES-256-GCM encrypted)
  ├── chat_sessions
  └── chat_messages (content_encrypted column — ciphertext only)
```

---

## 📁 Project Structure

```
ChatBot-Neuro/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── llm_router.py          # Multi-LLM fallback system
│   │   │   ├── memory_agent.py        # Legacy memory summaries
│   │   │   ├── mood_detector.py       # Priority override + context-aware detection
│   │   │   ├── wellness_agent.py      # LangGraph 5-node pipeline
│   │   │   ├── activity_generator.py  # Emotion-specific activities
│   │   │   └── special_actions.py     # Jokes, proverbs, music, breathing
│   │   ├── models/schemas.py          # Pydantic models
│   │   ├── routers/
│   │   │   ├── chat.py                # POST /api/chat/ (auto-saves encrypted)
│   │   │   ├── voice.py               # POST /api/voice/analyze
│   │   │   ├── mood.py                # POST /api/mood/checkin
│   │   │   ├── db.py                  # Encryption verification endpoints
│   │   │   └── memory.py              # Legacy memory endpoints
│   │   ├── services/
│   │   │   ├── encryption.py          # AES-256-GCM encrypt/decrypt
│   │   │   ├── database.py            # Supabase REST API (direct HTTP)
│   │   │   └── voice_service.py       # Whisper transcription
│   │   ├── config.py
│   │   └── main.py
│   ├── data/memory/                   # Local RAG memory storage (auto-created)
│   ├── supabase_setup.sql             # Run in Supabase SQL Editor
│   ├── .env                           # Your API keys
│   ├── .env.example                   # Template
│   └── run.py
│
├── frontend/
│   ├── app/page.tsx                   # Main chat page
│   ├── components/chat/               # All 12 chat UI components
│   ├── hooks/useTTS.ts                # Auto-speak TTS hook
│   ├── store/chatStore.ts             # Zustand state
│   └── lib/api.ts                     # API client
│
├── DATABASE.md                        # Database schema and relationships
├── start-backend.bat                  # Double-click to start backend
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/` | Send a wellness chat message (auto-saves encrypted, uses RAG memory) |
| POST | `/api/voice/analyze` | Upload audio for voice check-in |
| POST | `/api/mood/checkin` | Submit a mood check-in |
| POST | `/api/db/test-encryption` | Test encryption with any text |
| GET | `/api/db/verify/{session_id}` | Verify DB data is encrypted |
| GET | `/api/db/history/{session_id}` | Get decrypted chat history |
| GET | `/api/db/health` | Check Supabase connection |
| GET | `/health` | Backend health check |
| GET | `/docs` | Swagger API documentation |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, Zustand |
| Backend | FastAPI, Python 3.14 |
| AI Orchestration | LangGraph 5-node pipeline, LangChain |
| LLM Primary | OpenRouter (`inclusionai/ring-2.6-1t:free`) |
| LLM Fallback 1 | OpenAI GPT-4o |
| LLM Fallback 2 | Groq Llama-3.3-70B |
| LLM Fallback 3 | Google Gemini 1.5 Flash |
| Voice Input | OpenAI Whisper |
| Voice Output | Web Speech API (browser-native, auto-speaks) |
| Database | Supabase (PostgreSQL) |
| Encryption | AES-256-GCM + HKDF-SHA256 per user |
| DB Client | Direct HTTP REST API |

---

## 💡 Conversation Flow Examples

```
User: "I am happy that I passed my examination"
  → Detected: happy / good  (priority override — "passed my exam" = always happy)
  → Response: "That's absolutely wonderful — passing your exams is such a big achievement!
               All that studying and hard work really paid off. You should be incredibly
               proud of yourself. Share this news with your family and friends..."
  → Shows: Proverb + Exam-specific celebration card + Music + Joke

User: "I feel so lonely"  (after the happy message above)
  → Detected: lonely / bad
  → Emotional journey injected: "User was HAPPY about passing exam, now LONELY"
  → Response: "Even though you just had such a wonderful achievement with your exams,
               it's really touching that you're feeling lonely now. That contrast can
               actually make the loneliness feel even sharper sometimes..."
  → Shows: Proverb + Joke + Music + Wellness tip + 5 connection-building activities

User: "I am feeling very stressed"
  → Detected: stressed / bad
  → Response: "That's a lot to carry. It makes complete sense you feel this way..."
  → Shows: Proverb + Breathing exercise + Joke + Music + Wellness tip + 5 stress activities

User: "I got a job!"  (after saying "I am happy")
  → Detected: happy (keyword override — "got a job" = always happy)
  → Prior context: happy → stays happy
  → Response: "That's absolutely incredible news! All that hard work finally paid off..."
  → Shows: Job-specific celebration card + Music + Joke
```

---

## 🔐 Supabase Encrypted Storage

### Setup (one-time)
1. Create project at [supabase.com](https://supabase.com)
2. Go to **Settings → API → Legacy anon, service_role API keys**
3. Copy **Project URL**, **anon key**, **service_role key** into `.env`
4. Go to **SQL Editor → New Query**, paste `backend/supabase_setup.sql`, click **Run**
5. Restart backend — you'll see `Supabase: ✅ (encrypted storage active)`

### Verify encryption
```
POST http://localhost:8000/api/db/test-encryption
{ "text": "I am feeling stressed", "user_id": "user-123" }

GET http://localhost:8000/api/db/verify/{session_id}?user_id=user-123
```

---

## 🧠 AI Model Configuration

Models and providers can easily be updated in your `.env` file:
```env
OPENROUTER_MODEL=inclusionai/ring-2.6-1t:free
OPENAI_MODEL=gpt-4o
GROQ_MODEL=llama-3.3-70b-versatile
GEMINI_MODEL=gemini-1.5-flash
```

---

## 🆘 Crisis Resources

- **India:** iCall: **9152987821** | Vandrevala Foundation: **1860-2662-345**
- **US:** **988** Suicide & Crisis Lifeline
- **International:** [findahelpline.com](https://findahelpline.com)

---

## ⚠️ Disclaimer

NeuroNest is an AI wellness companion, not a substitute for professional mental health care. If you are experiencing a mental health crisis, please contact a licensed professional or crisis helpline.
