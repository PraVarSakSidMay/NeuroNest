# NeuroNest AI Architecture Diagram

This document contains a comprehensive system architecture diagram of the NeuroNest AI system using Mermaid.js. It details the data flows, processing steps, and integrations between the frontend Next.js 15 client, the FastAPI backend orchestrator, MongoDB, and external API providers.

---

## 🗺️ System Architecture

```mermaid
graph TD
    %% Define Styles
    classDef frontend fill:#5D3FD3,stroke:#3b1e85,stroke-width:2px,color:#fff;
    classDef backend fill:#8A2BE2,stroke:#5c1fa6,stroke-width:2px,color:#fff;
    classDef database fill:#2E8B57,stroke:#1e5a38,stroke-width:2px,color:#fff;
    classDef external fill:#4682B4,stroke:#2a5d84,stroke-width:2px,color:#fff;
    
    subgraph Frontend ["Next.js 15 Client (Browser)"]
        UserDevice["User Media (Mic & Camera)"]
        MP["MediaPipe Face Landmarker"]
        FA["face-api.js Local NN"]
        AcousticAPI["Web Audio API Capture"]
        Zustand["Zustand State Store"]
        UI["React 19 UI Dashboard"]
        OfflineUI["Offline Box-Breathing (Web Speech API)"]
    end
    
    subgraph Backend ["FastAPI Application (Port 8000)"]
        Orchestrator["Master ConversationOrchestrator"]
        
        subgraph Perception ["Perception Layer"]
            DG_STT["STT Service (Deepgram Nova-2 / Fallbacks)"]
            Librosa["Acoustic Feature Extractor (librosa)"]
            Fusion["Emotion Fusion Service"]
        end
        
        subgraph Cognition ["Cognition & Memory Layer"]
            RLBandit["RL Bandit Engine (Thompson/UCB1/Epsilon)"]
            MemoryMgr["Memory Manager"]
            Episodic["Episodic Memory (Vector RAG)"]
            StateMemory["Goal, Preference & Emotional Memory"]
            Reflection["Asynchronous Reflection Engine"]
        end
        
        subgraph Planning ["Planning & Generation Layer"]
            Planner["Conversation Planning Engine"]
            Crisis["Programmatic Crisis Bypass (988)"]
            LLM_Water["LLM Waterfall Router"]
            TTS_Water["TTS Waterfall Router"]
        end
        
        MCPServer["Wellness MCP Server"]
    end

    subgraph Data ["Data Storage"]
        MongoDB[("MongoDB Database")]
    end
    
    subgraph Providers ["External API Providers"]
        OpenRouter["OpenRouter (Gemini, Claude, Llama)"]
        Groq["Groq API (Whisper)"]
        DeepgramAPI["Deepgram STT & TTS"]
        ElevenLabs["ElevenLabs API"]
        Cartesia["Cartesia API"]
        OpenAI["OpenAI API"]
    end

    %% Flows
    UserDevice -->|"Camera Frame"| MP
    UserDevice -->|"Camera Frame"| FA
    UserDevice -->|"Audio Stream"| AcousticAPI
    
    MP & FA -->|"Action Units & Emotions"| Zustand
    AcousticAPI -->|"Raw Audio Payload"| Zustand
    
    Zustand -->|"POST /process-voice (Audio + FACS + Metadata)"| Orchestrator
    
    %% Orchestrator routing
    Orchestrator --> DG_STT
    Orchestrator --> Librosa
    
    DG_STT -->|"Transcription"| Fusion
    Librosa -->|"Vocal Acoustics"| Fusion
    
    Fusion -->|"Fused UserState & Emotion"| RLBandit
    Fusion -->|"Update State"| MemoryMgr
    
    RLBandit -->|"Bandit Arm Selections"| Planner
    MemoryMgr -->|"Retrieve Episodic Memory"| Episodic
    MemoryMgr -->|"Read Goals & Preferences"| StateMemory
    
    Episodic -->|"Context Pass"| Planner
    StateMemory -->|"Context Pass"| Planner
    
    Planner -->|"Check Triggers"| Crisis
    Crisis -->|"If Self-Harm Detected"| TTS_Water
    Crisis -->|"Else (System Prompt Compiler)"| LLM_Water
    
    LLM_Water -->|"Route via API"| OpenRouter
    LLM_Water -->|"Structured LLM Response"| TTS_Water
    
    TTS_Water -->|"Synthesize Audio"| ElevenLabs
    TTS_Water -->|"Synthesize Audio"| Cartesia
    TTS_Water -->|"Synthesize Audio"| OpenAI
    TTS_Water -->|"Synthesize Audio"| DeepgramAPI
    
    TTS_Water -->|"Audio Payload URL"| Zustand
    Zustand -->|"Play Audio"| UI
    
    %% Storage links
    MemoryMgr <-->|"Read/Write Collection"| MongoDB
    Reflection <-->|"Batch Processes"| MongoDB
    
    class MP,FA,AcousticAPI,Zustand,UI,OfflineUI,UserDevice frontend;
    class Orchestrator,DG_STT,Librosa,Fusion,RLBandit,MemoryMgr,Episodic,StateMemory,Reflection,Planner,Crisis,LLM_Water,TTS_Water,MCPServer backend;
    class MongoDB database;
    class OpenRouter,Groq,DeepgramAPI,ElevenLabs,Cartesia,OpenAI external;
```

---

## 🧩 Architectural Breakdown

### 1. Perception Layer
- **MediaPipe & face-api.js**: Calculates facial landmarks and 52 Action Unit intensities locally inside the browser's sandbox to maintain HIPAA/GDPR alignment.
- **Speech-to-Text (STT)**: Utilizes a rate-limit-aware waterfall routing through OpenRouter's transcript endpoint, Groq's Whisper Large, and Deepgram Nova-2.
- **Acoustic Analysis (`librosa`)**: Processes vocal features like pitch variations, volume changes, trembling, and crying metrics on-device or server-side.
- **Emotion Fusion**: Programmatically merges lexical signals, acoustic signals, and visual blendshape markers into a single unified emotional vector.

### 2. Cognition & Memory
- **RL Bandit Engine**: Automatically chooses personality parameters (e.g. persona tone, length, questioning style, detail level) via three concurrently running Multi-Armed Bandit models: Thompson Sampling, Upper Confidence Bound 1 (UCB1), and Epsilon-Greedy.
- **Cognitive RAG Memory**: Organizes state across episodic, goal, preference, emotional, and reflection layers using MongoDB vector cosine similarity searches.
- **Asynchronous Reflection**: Scheduled jobs summarize conversations offline every 5 turns to construct macro-level memory and updates.

### 3. Planning & Generation
- **Conversation Planner**: Programmatically compiles dynamic system prompts, prunes tokens to minimize latency, and checks constraints.
- **Programmatic Crisis Bypass**: A rule-based scanner that immediately intercepts self-harm trigger words and serves pre-compiled safety statements (including the **988 Lifeline**) without calling any LLM.
- **TTS synthesis**: Dynamically routes responses to synthesis engines (ElevenLabs, Cartesia, Deepgram, OpenAI) with dynamic fallback and emotion-specific configuration models.
