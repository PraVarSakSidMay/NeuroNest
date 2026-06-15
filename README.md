# NeuroNest AI 🧠💜

NeuroNest AI is an emotionally intelligent, multimodal voice assistant that goes far beyond standard chatbots. It listens to **what you say** (transcript), **how you sound** (vocal acoustics via librosa/Web Audio), and **how you look** (facial micro-expressions via browser MediaPipe landmarkers). By fusing these inputs, NeuroNest detects contradiction between words and emotional cues, adapts its personality in real-time using **Reinforcement Learning**, maintains **multi-layered cognitive memory**, and behaves with the warmth of a supportive, empathetic friend.

---

## ✨ Key Innovations & Features

*   **Multimodal Emotion Fusion**: Integrates acoustic metrics (pitch, jitter, loudness, trembling, crying, whispering) and facial Action Units (e.g., AU12 for smiles, AU15 for frowns, eye contact, head pose) to detect when a user is masking their true feelings.
*   **Adaptive Reinforcement Learning (RL) Personality**: Factored multi-armed bandit running Thompson Sampling, Epsilon-Greedy, and UCB1 policies in parallel to dynamically select a joint response action across 5 dimensions:
    *   *Persona* (Empathetic, Humorous, Direct, Philosophical, Cheerleader)
    *   *Response Length* (Brief, Moderate, Detailed)
    *   *Questioning Style* (None, Open, Reflective, Socratic)
    *   *Motivation Style* (None, Encouragement, Challenge, Reframe)
    *   *Detail Level* (Concise, Balanced, Thorough)
*   **Unified Multi-Layer Memory (RAG)**: Coordinates five specialized cognitive memory layers:
    1.  *Episodic*: Chat interaction history.
    2.  *Goal*: Short and long-term user objectives.
    3.  *Preference*: User communication style preferences.
    4.  *Emotional*: Tracking stress levels, triggers, and dominant moods.
    5.  *Reflection*: High-level, abstract insights generated asynchronously in the background.
*   **Context Ranking & Reranking Engine**: Prioritizes memory candidates using a weighted scoring formula based on semantic similarity, recency decay (exponential), emotional relevance, and goal alignment. Weights adapt in real-time (e.g., prioritizing emotional relevance under high stress).
*   **Conversation Planning & Token Compiling**: Selects a strategic intent strategy (coaching, teaching, emotional support, debugging, brainstorming, motivation, casual) and condenses all cognitive inputs into a token-efficient, deduplicated prompt package before generation.
*   **Local Wellness MCP Server**: Implements the Model Context Protocol (MCP) over standard I/O to expose wellness telemetry resources and clinical export tools to local assistant clients (like Claude Desktop).
*   **Privacy-First Design (HIPAA/GDPR Compliant)**: Processes video frames locally in the browser's GPU/CPU thread via MediaPipe. Only aggregated telemetry scores and classifications are sent to the backend. No raw images or coordinate geometry ever leave the client.
*   **API Rate-Limit Failover (Waterfall)**: Low-latency rate-limit tracking. Instantly skips and cools down (for 60s) any provider returning HTTP 429, transitioning LLM calls through OpenRouter models (Gemini Flash, Claude 3.5 Haiku, Llama 3.3 70B, Mistral Small).
*   **Offline Grounding Mode**: If network connectivity drops, the client triggers offline grounding mode—guiding the user through a local box-breathing exercise (4s Inhale, 4s Hold, 4s Exhale, 4s Hold) using local Web Speech synthesis.

---

## 🏗️ Architecture & Pipeline

NeuroNest is built on **Clean Architecture** principles, separating concerns into strict layers: Domain, Application (Orchestrators/Services), Infrastructure (Adapters/MongoDB Repositories), and Presentation (FastAPI/Next.js).

```
                 [ User Mic & Camera ]
                          │
                          ▼
            [ Next.js Frontend (Next 15) ]
     (MediaPipe Video Processing & Web Audio API)
                          │ (HTTPS POST /process-voice)
                          ▼
           [ FastAPI Backend (Port 8000) ]
                          │
            [ Master ConversationOrchestrator ]
                          │
  ┌───────────────────────┼───────────────────────┐
  ▼ (Phase 1: Perception)  ▼ (Phase 2: Cognition)  ▼ (Phase 3: Memory & RL)
  - Transcription (STT)   - Emotion Fusion        - Vector Search (RAG)
  - Acoustic Analysis     - UserState Updates     - Bandit Arm Selection
  - AU Timeline           - Working Memory        - Few-shot Experiences
  └───────────────────────┼───────────────────────┘
                          │
                          ▼ (Phase 4: Planning & Compiling)
                          - Strategic Plan (ConversationPlanningEngine)
                          - Context Compacting & Token Deduplication
                          │
                          ▼ (Phase 5: Generation)
                          - OpenRouter LLM System Prompt Injection
                          - TTS Waterfall (ElevenLabs/Cartesia/Deepgram/etc.)
                          │
  ┌───────────────────────┴───────────────────────┐
  ▼ (Phase 6: Persistence)                        ▼ (Phase 7: Background Tasks)
  - Save Interaction to MongoDB                   - Async Reflection Engine
  - Log Implicit Reward Policy Update             - Memory Lifecycle Cleanup
                                                  - Working Memory Pruning
```

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.11+
*   Node.js 18+
*   MongoDB Instance (running locally on port 27017, or a remote URI)

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
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Create `backend/.env`
Create a `.env` file in the `backend/` directory and populate it with your credentials:
```ini
# ── AI Provider Keys ─────────────────────────────────────────────────
OPENAI_API_KEY=sk-proj-...
GROQ_API_KEY=gsk_...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
CARTESIA_API_KEY=...
LMNT_API_KEY=...
MURF_API_KEY=...
OPENROUTER_API_KEY=sk-or-v1-...  # Required for LLM & Embedding waterfalls

# ── Storage & DB Config ──────────────────────────────────────────────
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=neuronest

# ── Feature Flags & Logging ──────────────────────────────────────────
LOG_LEVEL=INFO
DEBUG=false
```
*Note: The backend automatically falls back to lower priority services if keys are missing.*

#### Running the Backend
```bash
uvicorn main:app --reload --port 8000
```
The FastAPI server will boot up and start listening at `http://localhost:8000`.

---

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

#### Create `frontend/.env`
Create a `.env` file in the `frontend/` directory:
```ini
# Supabase config (Optional / Legacy fallback)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_SUPABASE_PUBLISHABLE_KEY=eyJ...
```

#### Running the Frontend
```bash
npm run dev
```
Open **http://localhost:3000** in your browser.

---

## 🧠 Deep Dive: Cognitive Services & RL

### Master ConversationOrchestrator
Located in `backend/application/orchestrators/conversation_orchestrator.py`, this master component coordinates each turn context sequentially:
1.  **Phase 0 (Infra)**: Uploads raw WebM and initializes user session concurrently.
2.  **Phase 1 (Perception)**: Performs Whisper Transcription (transcription adapter) and vocal acoustics extraction (librosa adapter) in parallel.
3.  **Phase 2 (Cognition)**: Invokes `EmotionService` to fuse text, voice characteristics, and MediaPipe Action Units. Updates `UserState` and loads `WorkingMemory`.
4.  **Phase 3 (Memory & RL)**: Queries semantic candidates from MongoDB, groups multi-layer memories, and requests bandit arm choices from the `RLService`.
5.  **Phase 4 (Planning)**: Selects a response strategy (Coaching, Teaching, Emotional Support, etc.) via `ConversationPlanningEngine` and compacts inputs via `ContextCompiler`.
6.  **Phase 5 (Generation)**: Generates the LLM response text and synthesizes the speech using the highest priority functional TTS provider.
7.  **Phase 6 (Persistence)**: Records the interaction document and applies an implicit reward signal to the RL policy state.
8.  **Phase 7 (Background)**: Triggers async tasks to update working memory entities, run the reflection engine, and prune expired memory.

### Reinforcement Learning (RL) Policy Engine
The bandit system (`backend/services/rl_policy_engine.py`) factorizes a joint action space across five dimensions. It balances exploration and exploitation using three policies running in parallel:
*   **Thompson Sampling**: Generates arm pulls from a Beta posterior distribution representing reward likelihood.
*   **Epsilon-Greedy**: Selects the top-performing arm 80% of the time, decaying exploration rate (epsilon) over time.
*   **UCB1 (Upper Confidence Bound)**: Adds an uncertainty exploration bonus to arm averages to ensure under-explored configurations are tested.

#### Composite Reward Function
Reward calculations range from `[-1, +1]` based on four metrics:
*   *Explicit Feedback* (weight 0.40): Direct user thumbs up/down (+1 or -1) via the frontend widget.
*   *Sentiment Delta* (weight 0.30): Improvement or deterioration of user emotion relative to the last turn.
*   *Session Duration* (weight 0.20): Chronological session length normalized up to 10 minutes.
*   *Turn Engagement* (weight 0.10): Standard implicit credit for completing a turn successfully.

---

## Wellness MCP Server

NeuroNest includes a local Model Context Protocol (MCP) server running over stdio from `backend/mcp_server.py`. It reads the local MongoDB interaction database and exposes wellness telemetry safely.

### Exposed Resources & Tools
*   **Resource `wellness://summary`**: JSON summary of recent session frequency and emotional telemetry.
*   **Resource `wellness://trends`**: Aggregated daily trend rows.
*   **Tool `get_wellness_summary`**: Retrieves structured stats for clinical review.
*   **Tool `get_daily_trends`**: Chronological list of daily average stress, dominant emotion, and eye-contact ratios.
*   **Tool `export_clinical_report`**: Writes a print-friendly `HTML` format clinical report (containing tables and graphs) or a raw `JSON` export file to the `generated/` directory.
*   **Tool `generate_clinical_summary`**: Invokes the LLM to compose a therapist-facing, non-diagnostic overview of user wellness trends.

### Example Claude Desktop Client Config
To integrate NeuroNest Wellness into your Claude Desktop, add the server to your configuration file (typically `%APPDATA%\Claude\claude_desktop_config.json` on Windows):
```json
{
  "mcpServers": {
    "neuronest-wellness": {
      "command": "python",
      "args": [
        "c:/Users/Dell/Downloads/VoiceAssistant/backend/mcp_server.py"
      ]
    }
  }
}
```

---

## 🔌 API Endpoints

### `POST /session-start`
Called at app launch. Returns a customized text opener referencing the user's emotional state from their last session.

### `POST /process-voice` (or `/process-voice-v3`)
The primary voice processing pipeline. Accepts multipart form data.
*   `file`: The `.webm` recording file.
*   `audio_analysis`: Browser Web Audio features.
*   `video_analysis`: Summarized face/expression history.
*   `voice_name`: Requested TTS speaker persona.

### `POST /feedback`
Submits explicit user feedback. Updates the RL Policy Engine posteriors.
*   `interaction_id`: Target interaction UUID.
*   `score`: `+1` (positive) or `-1` (negative).
*   `session_duration`: Total active time in seconds.

### `GET /rl/stats`
Returns the cumulative reward, regret proxy, win rate, and arm alphas/betas for Thompson Sampling, Epsilon Greedy, and UCB1.

---

## 📦 Core Dependencies

### Backend
*   `fastapi` & `uvicorn` (ASGI presentation layer)
*   `motor` & `pymongo` (Async MongoDB access)
*   `openai` (OpenRouter API client)
*   `librosa` & `soundfile` (Acoustic analysis)
*   `mcp` (Model Context Protocol SDK)
*   `pydantic-settings` (Config management)

### Frontend
*   `next` (App Router UI frame)
*   `react` & `react-dom` (React 19)
*   `zustand` (State management stores)
*   `@mediapipe/tasks-vision` (On-device face landmarking)
*   `lucide-react` (Iconography)

---

*Built with 💜 — Empowered by Clean Architecture, Multi-Armed Bandits, and cognitive RAG memories.*
