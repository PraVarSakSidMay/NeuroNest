# Future Roadmap: NeuroNest Evolution

This document outlines the long-term technical and clinical vision for NeuroNest, focusing on providing high-empathy, privacy-preserving therapeutic support for troubled or distressed individuals.

---

## Completed Milestones

### 1. Personalized Baseline Calibration (Emotion Adaptability) — [COMPLETED]
*   **Neutral Calibration Routine**: Implemented a 3-second interactive wizard on webcam activation that establishes a user-specific baseline.
*   **Normalized Thresholding**: Scaled raw Action Unit (AU) activation relative to the neutral baseline, significantly improving classification accuracy.
*   **Adaptive Sensitivity**: Preserved calibration baseline inside local browser storage to keep user preferences persistent.

### 2. Context-Aware Visual Cues (Gaze & Body Language Adaptation) — [COMPLETED]
*   **Avoidance Detection**: Monitored eye contact durations and head orientation (yaw/pitch). If a distressed user repeatedly looks down or away, "cognitive avoidance" / "averted gaze" is flagged.
*   **Conversational Adaptation**: Passed gaze cues and eye contact telemetry to the LLM response service. The backend adapts its responses with greater empathy and support when visual distress cues are present.

### 3. Lightweight Local Neural Classification & Server Optimization — [COMPLETED]
*   **Softmax Perceptron Neural Network**: Replaced the rule-based emotion heuristics with a single-layer feed-forward neural network operating in the browser, mapping 6 Action Units, eye contact, and head pitch deflection to mathematically normalized emotion probabilities.
*   **Zero-Overhead Backend**: Completely removed `openSMILE` and `librosa` dependencies from the backend Python server, reducing container sizes from >1.2GB to <150MB, speeding up deployments, and resolving package toolchain lock issues.
*   **Pure-Python Fallback**: Configured a lightweight pure-Python audio analyzer using FFmpeg and the standard `wave` module as a server fallback when client-side features are missing.

### 4. Dynamic Resiliency Local Offline Mode — [COMPLETED]
*   **Connectivity Event Monitoring**: Setup window online/offline event listeners and status hooks to adapt the UI in real-time when the network is lost.
*   **Seamless Intercept**: Caught errors during microphone/voice processing requests and redirected the user instantly to local offline coping care.
*   **Visual Breathing Bubble**: Built a premium glassmorphic box-breathing interface featuring dynamic scale animations and transitions.
*   **Local TTS Guidance**: Leveraged browser-native `window.speechSynthesis` to vocalize phase instructions using calming female English voices.
*   **Offline Service Worker caching**: Implemented `sw.js` with a cache-first routing strategy for external jsdelivr MediaPipe CDN WASM assets and network-first logic for local static bundles.

### 5. Standardized Wellness MCP Server - [COMPLETED]
*   **Local MCP Server**: Added `backend/mcp_server.py`, a stdio Model Context Protocol server exposing local wellness summary and trend resources.
*   **Clinical Sharing Tools**: Added tools for wellness summaries, daily trends, print-friendly HTML/JSON clinical report export, and LLM-assisted therapist-facing summaries.
*   **Longitudinal Telemetry**: Persisted visual attention telemetry (`eye_contact_ratio` and `head_pose`) alongside emotion data so clinical reports can include gaze and avoidance trends.

---

## Future Goals

New roadmap items will be added here as the next product and clinical integration priorities are defined.
