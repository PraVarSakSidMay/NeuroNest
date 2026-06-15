# NeuroNest AI 🧠💜

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15.0-black.svg)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19.0-blue.svg)](https://react.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Active-green.svg)](https://www.mongodb.com/)

NeuroNest AI is a production-ready, emotionally intelligent, and multimodal voice assistant that integrates voice synthesis, facial micro-expression analysis, vocal acoustics, and cognitive reinforcement learning. It acts as an empathetic, supportive, and adaptive companion.

By cross-referencing **what you say** (lexical analysis), **how you sound** (vocal acoustics), and **how you look** (facial Action Units), NeuroNest detects contradiction between verbal expressions and bodily cues. It adjusts its personality dynamically via **Multi-Armed Bandit Reinforcement Learning**, coordinates a **5-layer memory system** (with cosine similarity RAG), and synthesizes expressive voices via a failover waterfall.

---

## ✨ Key Innovations & Features

*   **Multimodal Emotion Fusion**: Fuses 3 distinct input channels:
    *   *Lexical (Text)*: Sentiment evaluation utilizing clinical wordlists to flags triggers, mood words, and self-harm phrases.
    *   *Acoustic (Voice)*: Analyzes vocal features (pitch variation, loudness variation, jitter, trembling, whispering, crying) via `librosa`.
    *   *Visual (FACS)*: Analyzes 52 facial blendshapes and landmarks via MediaPipe and `face-api.js` local neural networks.
*   **Programmatic & High-Speed Performance**: Low-latency, rule-based heuristics replace slow sequential LLM calls:
    *   **Programmatic Emotion Fusion**: Fuses signals instantly ($<1\text{ ms}$ latency vs $\sim5\text{ s}$ LLM).
    *   **Programmatic Strategy Selector**: Determines dialog intent rules-based instantly.
    *   **Programmatic telemetry summary**: Computes stress metrics, gaze avoidance, and therapist discussion points dynamically ($<1\text{ ms}$).
*   **Adaptive Reinforcement Learning (RL) Bandit Engine**: Dynamically selects response behavior across a 5-dimensional joint action space:
    *   *Persona* (Empathetic, Humorous, Direct, Philosophical, Cheerleader)
    *   *Response Length* (Brief, Moderate, Detailed)
    *   *Questioning Style* (None, Open, Reflective, Socratic)
    *   *Motivation Style* (None, Encouragement, Challenge, Reframe)
    *   *Detail Level* (Concise, Balanced, Thorough)
*   **5-Layer Cognitive Memory (RAG)**: Organizes information across episodic, goal, preference, emotional, and asynchronous background reflection layers.
*   **Model Rate-Limit & Cooldown Waterfall**:
    *   *LLM Waterfall*: OpenRouter failover routing (Gemini 2.0 Flash Free $\rightarrow$ Gemini 1.5 Flash $\rightarrow$ Claude 3.5 Haiku $\rightarrow$ Llama 3.3 70B $\rightarrow$ Mistral Small).
    *   *TTS Waterfall*: High-fidelity failover (ElevenLabs $\rightarrow$ Cartesia $\rightarrow$ Deepgram Aura-2 $\rightarrow$ OpenAI TTS $\rightarrow$ LMNT $\rightarrow$ Murf AI $\rightarrow$ local Web Speech synthesis fallback).
*   **Programmatic Crisis Bypass**: Immediately catches self-harm keywords to bypass LLM generation, delivering a warm pre-formatted clinical safety statement with the **988 Lifeline**.
*   **Co-Generation Schema Integration**: Combines dialogue response generation and working memory extraction into a single, structured JSON LLM call.
*   **Context Compiling & Stress Deltas**: Compresses memories based on similarity and lexical overlap, programmatically inserts stress alerts, and prunes system prompts based on current dialogue intent.
*   **Offline Grounding Mode**: Local box-breathing exercise (4s Inhale, 4s Hold, 4s Exhale, 4s Hold) driven by browser Web Speech API during network disconnection.
*   **Wellness MCP Server**: Exposes secure local wellness data resources and clinical report generators to MCP clients (like Claude Desktop).
*   **Privacy-First GPU Processing**: MediaPipe and `face-api.js` run on-device inside the browser's sandbox. Zero raw video/coordinate geometry leaves the client.

---

## 🏗️ Architecture & Pipeline

NeuroNest uses a clean architecture dividing domain models, application orchestrators, infrastructure adapters, and FastAPI/Next.js presentation layers.

```
                 [ User Mic & Camera ]
                           │
                           ▼
             [ Next.js Frontend (Next 15) ]
      (MediaPipe Video Processing & face-api.js)
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
                           ▼ (Phase 5: Generation / Bypass)
                           - Dynamic system prompt pruning / System Prompt
                           - Single-turn JSON Co-Generation LLM call
                           - Programmatic Crisis Bypass (988)
                           - TTS Waterfall (ElevenLabs/Cartesia/Deepgram/etc.)
                           │
   ┌───────────────────────┴───────────────────────┐
   ▼ (Phase 6: Persistence)                        ▼ (Phase 7: Background Tasks)
   - Save Interaction to MongoDB                   - Async Reflection Engine (Batch)
   - Log Implicit Reward Policy Update             - Memory Lifecycle Cleanup
                                                   - Working Memory Pruning
```

### Turn Pipeline (Phase 0 - 7)

1.  **Phase 0 (Infra)**: Uploads the raw WebM voice payload and registers the active user session.
2.  **Phase 1 (Perception)**: Performs Deepgram Nova-2 transcription and extracts vocal acoustics (jitter, standard deviation of volume and pitch, trembling, whispering) in parallel.
3.  **Phase 2 (Cognition)**: Evaluates input metrics programmatically inside [emotion_service.py](file:///c:/Users/Dell/Downloads/VoiceAssistant/backend/services/emotion_service.py) to fuse text, voice, and facial metrics. Updates the persistent user state and volatile working memory.
4.  **Phase 3: Memory & RL**: Queries vector memory via MongoDB cosine similarity search and calls the Reinforcement Learning Bandit service to pull composed response parameters.
5.  **Phase 4 (Planning & Compiling)**: Determines conversational strategy. Deduplicates context tokens, checks for keyword overlap, and compiles the system prompt.
6.  **Phase 5 (Generation & Failover)**: Checks for crisis triggers (immediate 988 redirect). Otherwise, invokes the LLM waterfall for co-generation (response + working memory update). Routes audio synthesis through the TTS waterfall.
7.  **Phase 6 (Persistence)**: Saves the interaction document to MongoDB and schedules an implicit turn-engagement reward update.
8.  **Phase 7 (Background Tasks)**: Executes batch reflection summaries (runs every 5 turns), handles memory lifecycle decay, and trims volatile working memory.

---

## 🎙️ Emotional Voice Synthesis (TTS)

Vocal synthesis integrates emotional state settings dynamically to alter stability, expressive styling, and speaker personas.

### ElevenLabs Dynamic settings
Adjusts the voice characteristics in ElevenLabs dynamically:

| Emotion Class | Stability | Style Exaggeration | Vocal Tone Characteristics |
| :--- | :--- | :--- | :--- |
| `sad`, `depressed`, `grief` | `0.35` | `0.20` | Softer, breathier, high emotional range |
| `anxious`, `fearful`, `panic` | `0.40` | `0.15` | Grounded, careful, sympathetic pacing |
| `happy`, `excited` | `0.45` | `0.15` | Bright, energetic, positive uplift |
| `angry`, `frustrated` | `0.30` | `0.25` | Intense, dynamic emphasis, tense |
| `neutral`, `calm` (Default) | `0.50` | `0.00` | Consistent, balanced, professional |

### OpenAI Dynamic Voice Swapping
For the OpenAI TTS fallbacks, the system swaps voice models to match gender preferences and emotional targets:

| User Voice Gender | Detected Emotion | Chosen Voice ID | Sound Profile |
| :--- | :--- | :--- | :--- |
| **Female Persona** | Sad / Anxious / Fearful / Depressed | `alloy` | Soft, warm, and highly comforting |
| **Female Persona** | Happy / Excited | `shimmer` | Energetic, bright, and enthusiastic |
| **Female Persona** | Neutral / Calm / Other | *User Default* (e.g., `shimmer`/`alloy`) | Balanced conversational |
| **Male Persona** | Sad / Anxious / Fearful / Depressed | `echo` | Deep, comforting, and warm resonance |
| **Male Persona** | Happy / Excited | `nova` | Bright, clear, and positive |
| **Male Persona** | Neutral / Calm / Other | *User Default* (e.g., `onyx`/`fable`) | Clear, standard speaking |

---

## 📹 Video Emotion Pipeline

Facial landmarks and Action Unit (AU) intensities are calculated directly in the browser via MediaPipe Facelandmarker and `face-api.js` models.

```
       [ Browser Camera Stream ] ──► [ MediaPipe 52 Blendshapes ] ──┐
                                                                   ├──► [ Softmax Perceptron Classifier ] ──► 13 Emotion Probabilities
       [ Browser Camera Stream ] ──► [ face-api.js Neural Net ] ────┘
```

### 13 Emotion Classifications
The perceptual layer maps weights across MediaPipe blendshapes, gaze vectors, and head poses to classify 13 distinct classes:
`happy`, `sad`, `angry`, `fearful`, `anxious`, `surprised`, `disgusted`, `confused`, `excited`, `frustrated`, `depressed`, `calm`, and `neutral`.

### Key Video Processing Mechanics
1.  **Dual-Marker Disgust Gate**:
    To prevent mouth-shape or talking-frown movement from generating false disgust triggers, disgust classification uses a **geometric mean** of AU9 (nose sneer) and AU10 (upper lip raise):
    $$\text{Disgust Factor} = \sqrt{\text{AU09 (threshold } > 0.18) \times \text{AU10 (threshold } > 0.12)}$$
    Both landmarks must activate simultaneously for the disgust classification to scale.
2.  **Sadness Upper-Face Verification**:
    To distinguish generic speaking-mouth frowning from genuine sadness, the engine checks for co-activation of **AU1 (inner brow raise)** or eye blinks. If brow inner elevation is absent, generic speaking frowns are down-weighted to prevent false positives.
3.  **Neutral Baseline Calibration**:
    At start, the user can run a **15-frame neutral calibration** sequence. Averages of baseline Action Units are saved to `localStorage`. Subsequent frames evaluate raw values relative to this custom baseline:
    $$\text{Normalized AU} = \frac{\text{Raw AU} - \text{Baseline AU}}{\max(0.01, 1.0 - \text{Baseline AU})}$$
4.  **Temporal Filtering**:
    Applies a **Kalman Filter** and Exponential Moving Average (EMA) smoothing over frame predictions, preventing flickering and stabilizing emotion labels before transmission.

---

## 🧠 Reinforcement Learning (RL) Bandit Engine

NeuroNest models its response configuration as a Multi-Armed Bandit problem. It optimizes actions across five dimensions concurrently (persona, response length, questioning style, motivation style, detail level), yielding **720 possible configurations**.

```
                ┌──► Thompson Sampling Posterior (Beta posterior alpha/beta)
   [ RL Policy ]┼──► Epsilon-Greedy (80/20 exploration decay)
                └──► UCB1 Policy (Uncertainty exploration bonus)
```

The system runs three bandit models concurrently to compare performance metrics in real-time.

### Composite Reward Function
Bandit weights are optimized utilizing a combined reward score calculated in the interval $[-1.0, +1.0]$:

| Reward Component | Metric Target | Weight | Trigger Description |
| :--- | :--- | :---: | :--- |
| **Explicit User Feedback** | Explicit thumbs up/down | `0.40` | Direct user feedback submitted via frontend widget |
| **Sentiment Delta** | Emotion improvement | `0.30` | Programmatic delta tracking user stress recovery |
| **Session Duration** | Chronological duration | `0.20` | Length of dialogue session normalized up to 10 minutes |
| **Turn Engagement** | Turn completion | `0.10` | Implicit success metric awarded on turn audio play |

---

## 💾 Multi-Layer Cognitive Memory

Past events, context preferences, and self-reflection metrics are stored across five distinct layers in MongoDB:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Unified Cognitive Memory                        │
├───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│ Episodic Memory   │ Goal Memory       │ Preference Memory │ Emotional Memory│
│ Chat transcript   │ Active tasks,     │ Conversational    │ Stress levels,  │
│ history list      │ user objectives   │ style settings    │ trigger words   │
└───────────────────┴───────────────────┴───────────────────┴─────────────────┘
                                   ▲
                                   │ (Asynchronous Batch Run)
                        ┌──────────┴──────────┐
                        │  Reflection Engine  │
                        │ Long-term insights  │
                        └─────────────────────┘
```

| Memory Layer | Type | Target Scope | Persistence Mechanism |
| :--- | :--- | :--- | :--- |
| **Episodic** | Vector RAG | Full historical chat interaction turns | MongoDB vector cosine similarity search |
| **Goal** | Structured JSON | Short-term tasks and long-term user objectives | Co-generation parsing into user state doc |
| **Preference** | Structured JSON | Communication detail, tone, and language options | Saved programmatically in user state profiles |
| **Emotional** | Telemetry logs | Dominant emotions, stress spikes, and triggers | Persistent time-series database mapping |
| **Reflection** | Asymmetric LLM | Macro behavioral insights and long-term habits | Asynchronous batch task running every 5 turns |

---

## 🔌 API Endpoints

### Session Management
*   `POST /session-start`
    Fetches the customized welcome message referencing the user's emotional state from their last session.

### Core Processing Pipelines
*   `POST /process-voice` (and aliases `/process-voice-v2`, `/process-voice-v3`)
    Evaluates WebM payloads and client metrics. Returns transcribed text, fused emotion, stress levels, target response text, and TTS audio URL.
    *Form Parameters:*
    *   `file`: WebM audio stream file.
    *   `audio_analysis`: Web Audio API acoustic JSON.
    *   `video_analysis`: Summarized MediaPipe/face-api facial metrics JSON.
    *   `voice_name`: TTS persona name (e.g. `Rachel`, `Josh`).
    *   `expression_history`: Emotion history timeline array.

### Reinforcement Learning & Feedback
*   `POST /feedback`
    Stores explicit user ratings ($+1$ or $-1$) and recalculates composite rewards to update bandit posteriors.
    *Form Parameters:*
    *   `interaction_id`: Interaction database UUID.
    *   `score`: Positive ($1.0$) or negative ($-1.0$).
    *   `session_duration`: Session duration in seconds.
*   `GET /rl/stats`
    Returns total pulls, cumulative rewards, win rates, and alpha/beta values for all three bandit models.
*   `GET /rl/rankings`
    Returns arm rankings per dimension sorted by mean reward.
*   `GET /rl/policy`
    Returns current active policy and win rates.
*   `POST /rl/reset`
    Resets bandit alphas/betas to uniform priors (wipes learned values).

### Audio & Utility
*   `POST /preview-voice`
    Synthesizes a short greeting for the specified voice.
*   `GET /audio/{filename}`
    Streams synthesized TTS audio files.

---

## 🛠️ Getting Started

### Prerequisites
*   **Python**: Version 3.11 or higher
*   **Node.js**: Version 18 or higher (Next.js 15 compatible)
*   **MongoDB**: Run locally (port 27017) or configure a connection string

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

# Create and activate virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

#### Create `backend/.env`
Create a `.env` file in the `backend/` directory:
```ini
# ── AI Provider Keys ──────────────────────────────────────────────────
OPENROUTER_API_KEY=sk-or-v1-...  # Required for LLM & Embedding waterfalls
DEEPGRAM_API_KEY=...             # Required for Transcription (STT)
OPENAI_API_KEY=sk-proj-...       # Optional fallback TTS & LLM
ELEVENLABS_API_KEY=...           # Optional fallback TTS
CARTESIA_API_KEY=...             # Optional fallback TTS
LMNT_API_KEY=...                 # Optional fallback TTS
MURF_API_KEY=...                 # Optional fallback TTS

# ── Storage & DB Config ───────────────────────────────────────────────
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=neuronest

# ── Feature Flags & Logging ───────────────────────────────────────────
LOG_LEVEL=INFO
DEBUG=false
```
*Note: Waterfalls automatically skip providers whose API keys are omitted.*

#### Start Backend
```bash
uvicorn main:app --reload --port 8000
```
FastAPI runs on `http://localhost:8000`.

---

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

#### Create `frontend/.env`
Create a `.env` file in the `frontend/` directory (note that Supabase is legacy; configure the API url):
```ini
# API endpoint for backend communications (defaults to http://localhost:8000)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Start Frontend
```bash
npm run dev
```
Open **http://localhost:3000** in your browser.

---

## 📦 Core Dependencies

| Module / Package | Purpose | Scope |
| :--- | :--- | :---: |
| `fastapi` / `uvicorn` | Web API Framework and server runtime | Backend |
| `motor` / `pymongo` | Async MongoDB database client driver | Backend |
| `openai` | API client configured for OpenRouter LLMs | Backend |
| `librosa` / `soundfile` | Vocal feature acoustics extraction | Backend |
| `elevenlabs` | Voice synthesis (TTS) provider SDK | Backend |
| `cartesia` | Low-latency voice synthesis API client | Backend |
| `mcp` | Model Context Protocol SDK implementation | Backend |
| `next` / `react` | Next.js 15 App router structure / React 19 UI | Frontend |
| `zustand` | State management stores | Frontend |
| `@mediapipe/tasks-vision` | Landmark facial landmarker & blendshape outputs | Frontend |
| `@vladmandic/face-api` | Deep learning face detection & expression model | Frontend |
| `lucide-react` | Dashboard UI Iconography | Frontend |

---

## 🔒 Privacy & HIPAA/GDPR Compliance

NeuroNest utilizes a **Privacy-by-Design** framework:
*   **Local Processing**: Camera streams, face bounding boxes, iris tracking, and 52 facial blendshapes are processed locally via WebGL/WASM in the client browser thread.
*   **No Image Transmission**: Raw video frames, coordinates, and pixel streams never leave the client device.
*   **Aggregated Telemetry**: The backend receives only numerical Action Unit scores and classified emotion categories.
*   **Audit-Ready**: Compliance-aligned database design for wellness metrics satisfies security and confidentiality requirements.

---

*Built with 💜 — Empowered by Clean Architecture, Multi-Armed Bandits, and cognitive RAG memories.*
