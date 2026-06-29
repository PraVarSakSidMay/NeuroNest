# NeuroNest AI 🧠💜

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15.0-black.svg)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19.0-blue.svg)](https://react.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Active-green.svg)](https://www.mongodb.com/)

NeuroNest AI is a production-ready, emotionally intelligent, and multimodal voice assistant. By combining voice synthesis, facial micro-expression analysis, vocal acoustics, and cognitive reinforcement learning, NeuroNest acts as a highly adaptive, empathetic, and supportive digital companion.

By cross-referencing **what you say** (lexical analysis), **how you sound** (vocal acoustics via `librosa`), and **how you look** (facial Action Units via local neural networks), NeuroNest detects subtle discrepancies in human expression. It dynamically optimizes its personality, questioning style, and communication detail through **Multi-Armed Bandit Reinforcement Learning**, coordinates a **5-layer cognitive memory system**, and uses robust, rate-limit-aware **waterfall failover pipelines** for LLM, STT, and TTS.

---

## ✨ Key Innovations & Features

*   **Multimodal Emotion Fusion**: Seamlessly integrates three perceptual streams in real time ($<1\text{ ms}$ processing latency):
    *   *Lexical (Text)*: Evaluates sentiment using clinical wordlists to flag triggers, emotional markers, and self-harm keywords.
    *   *Acoustic (Voice)*: Extracts key vocal features (pitch/volume variance, jitter, trembling, whispering, crying) using `librosa`.
    *   *Visual (FACS)*: Tracks 52 facial blendshapes and landmark geometry on-device via MediaPipe and `face-api.js`.
*   **Adaptive Reinforcement Learning (RL) Bandit Engine**: Uses Multi-Armed Bandits (Thompson Sampling, Epsilon-Greedy, and UCB1 running concurrently) to optimize conversation settings across a 5-dimensional joint action space:
    *   *Persona* (Empathetic, Humorous, Direct, Philosophical, Cheerleader)
    *   *Response Length* (Brief, Moderate, Detailed)
    *   *Questioning Style* (None, Open, Reflective, Socratic)
    *   *Motivation Style* (None, Encouragement, Challenge, Reframe)
    *   *Detail Level* (Concise, Balanced, Thorough)
*   **5-Layer Cognitive Memory (RAG)**: Keeps context highly grounded via episodic, goal, preference, emotional, and long-term reflection memory layers backed by MongoDB vector similarity.
*   **Rate-Limit-Aware Waterfall Pipelines**:
    *   *LLM Waterfall (via OpenRouter)*: Directs queries to the best available model with zero-latency cooldown skip (Gemini 2.0 Flash Free $\rightarrow$ Gemini 1.5 Flash $\rightarrow$ Claude 3.5 Haiku $\rightarrow$ Llama 3.3 70B $\rightarrow$ Mistral Small).
    *   *STT Waterfall*: OpenRouter Transcription $\rightarrow$ Groq Whisper $\rightarrow$ Deepgram Nova-2.
    *   *TTS Waterfall*: ElevenLabs (dynamic emotional styling) $\rightarrow$ Cartesia $\rightarrow$ Deepgram Aura-2 $\rightarrow$ OpenAI TTS (dynamic voice swapping) $\rightarrow$ LMNT $\rightarrow$ Murf AI $\rightarrow$ local Web Speech fallback.
*   **Programmatic Crisis Bypass**: Detects distress or self-harm keywords instantly, bypassing model processing entirely to deliver a warm, clinical safety message featuring the **988 Lifeline**.
*   **Offline Grounding Mode**: Displays a local guided box-breathing widget (4s Inhale, 4s Hold, 4s Exhale, 4s Hold) powered by the browser's native Web Speech API during network outages.
*   **Wellness MCP Server**: Exposes secure local wellness telemetry and clinical report summaries to Model Context Protocol clients (e.g., Claude Desktop).
*   **On-Device Processing for Privacy**: All video and camera landmarks run completely locally in the browser sandbox. Zero raw video feeds or face coordinate geometries are sent to the cloud.

---

## 🏗️ System Architecture & Pipeline

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
                           - Dynamic system prompt pruning
                           - Single-turn JSON Co-Generation LLM call
                           - Programmatic Crisis Bypass (988)
                           - TTS Waterfall Routing
                           │
   ┌───────────────────────┴───────────────────────┐
   ▼ (Phase 6: Persistence)                        ▼ (Phase 7: Background Tasks)
   - Save Interaction to MongoDB                   - Async Reflection Engine (Batch)
   - Log Implicit Reward Policy Update             - Memory Lifecycle Cleanup
                                                   - Working Memory Pruning
```

---

## 📂 Project Directory Structure

```
VoiceAssistant/
├── backend/               # FastAPI Backend Application
│   ├── adapters/          # Implementation adapters for databases & API layers
│   ├── application/       # Orchestrator core and turn execution logic
│   ├── core/              # Global configuration, logger, and security settings
│   ├── domain/            # Core business models, schemas, and entity classes
│   ├── infrastructure/    # Port implementations and external AI provider interfaces
│   ├── services/          # Memory managers, emotion fusion, bandit RL, & TTS services
│   ├── tests/             # Pytest suite (mocks, integration, & logic tests)
│   └── main.py            # FastAPI main application entry point
│
├── frontend/              # Next.js 15 Frontend Client
│   ├── app/               # React App Router pages and styling layouts
│   ├── public/            # Static assets and browser-side model weights
│   ├── src/               # UI components, icons, and state stores (Zustand)
│   └── package.json       # Node package manager configurations
│
└── README.md              # Unified project documentation
```

---

## 🛠️ Getting Started

### Prerequisites
*   **Python**: Version 3.11+
*   **Node.js**: Version 18+ (Next.js 15 compatible)
*   **MongoDB**: Running locally on port `27017` or configured via a connection string URI.

---

### 1. Clone & Initialize
```bash
git clone <your-repo-url>
cd VoiceAssistant
```

---

### 2. Backend Setup
1. Navigate into the backend directory and set up a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the `backend/` folder:
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
   *Note: Waterfall queues automatically bypass any service providers whose API keys are missing or invalid.*
4. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend API documentation will be available at `http://localhost:8000/docs`.

---

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file in the `frontend/` folder:
   ```ini
   # API endpoint pointing to the running backend
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Boot up the local Next.js client server:
   ```bash
   npm run dev
   ```
   Open **`http://localhost:3000`** in your browser.

---

## 🔒 Privacy & HIPAA/GDPR Alignment

*   **Zero-Trace Camera Streams**: Video processing, face boundary box calculation, facial landmark alignment, and 52 Action Unit (AU) detections occur entirely in the client-side JavaScript sandbox via WebGL/WASM.
*   **Aggregation Only**: Only numerical emotion metrics and summarized Action Unit probabilities are transmitted to the backend API. No facial images, raw pixels, or geometric spatial maps are stored or uploaded.
*   **Secure Telemetry Logging**: Database models segment session logs with encryption support, aligning with modern security and HIPAA-ready configuration options.

---

*Developed with 💜 — Powered by Clean Architecture, Multi-Armed Bandits, and Multimodal Emotion Perception.*
