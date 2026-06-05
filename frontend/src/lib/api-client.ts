/**
 * Centralized API client for frontend-backend communication.
 * All HTTP requests go through this module.
 */
import axios, { AxiosError, AxiosInstance } from "axios";
import type {
  ProcessVoiceRequest,
  ProcessVoiceResponse,
  SessionStartResponse,
  PreviewVoiceResponse,
  ApiError,
  ApiErrorResponse,
  ValidationError,
} from "../types";

// ============================================================================
// Configuration
// ============================================================================

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================================================
// Error Normalization
// ============================================================================

export function normalizeError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const response = error.response;
    const status = response?.status || 0;

    // Handle FastAPI validation errors
    const data = response?.data as ApiErrorResponse | undefined;

    if (data?.detail) {
      if (Array.isArray(data.detail)) {
        // Validation error array
        const firstError = data.detail[0] as ValidationError;
        return {
          error: `Validation failed: ${firstError.msg}`,
          detail: JSON.stringify(data.detail),
        };
      }
      return {
        error: data.detail,
        detail: `HTTP ${status}`,
      };
    }

    return {
      error: response?.statusText || error.message,
      detail: `HTTP ${status}: ${error.message}`,
    };
  }

  if (error instanceof Error) {
    return {
      error: error.message,
      detail: "An unexpected error occurred",
    };
  }

  return {
    error: "Unknown error",
    detail: "An unexpected error occurred",
  };
}

// ============================================================================
// Axios Instance
// ============================================================================

let client: AxiosInstance | null = null;

function getClient(): AxiosInstance {
  if (!client) {
    client = axios.create({
      baseURL: BASE_URL,
      timeout: 60000, // 60s for voice processing
    });

    // Request interceptor for correlation IDs
    client.interceptors.request.use((config) => {
      config.headers["X-Correlation-ID"] =
        config.headers["X-Correlation-ID"] || crypto.randomUUID();
      return config;
    });

    // Response error interceptor for normalization
    client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(normalizeError(error)),
    );
  }
  return client;
}

// ============================================================================
// Endpoint Functions
// ============================================================================

/**
 * Start a new session and get greeting (RAG-based)
 */
export async function startSession(): Promise<SessionStartResponse> {
  const response = await getClient().post<SessionStartResponse>(
    "/session-start",
  );
  return response.data;
}

/**
 * Process voice recording and get AI response
 */
export async function processVoice(
  request: ProcessVoiceRequest,
): Promise<ProcessVoiceResponse> {
  const formData = new FormData();
  formData.append("file", request.file);
  if (request.audio_analysis) {
    formData.append("audio_analysis", request.audio_analysis);
  }
  if (request.video_analysis) {
    formData.append("video_analysis", request.video_analysis);
  }
  if (request.expression_history) {
    formData.append("expression_history", JSON.stringify(request.expression_history));
  }
  formData.append("voice_name", request.voice_name);

  const response = await getClient().post<ProcessVoiceResponse>(
    "/process-voice",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );
  return response.data;
}

/**
 * Preview a voice without recording
 */
export async function previewVoice(
  voiceName: string,
): Promise<PreviewVoiceResponse> {
  const formData = new FormData();
  formData.append("voice_name", voiceName);

  const response = await getClient().post<PreviewVoiceResponse>(
    "/preview-voice",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );
  return response.data;
}

// ============================================================================
// WebSocket Streaming (Scaffold - Future Implementation)
// ============================================================================

export interface VoiceStreamCallbacks {
  onTranscriptChunk: (text: string) => void;
  onEmotionUpdate: (emotion: {
    emotion: string;
    stress_level: number;
    contradiction_detected: boolean;
  }) => void;
  onResponseChunk: (chunk: { text: string; complete: boolean }) => void;
  onAudioReady: (url: string | null) => void;
  onError: (error: string) => void;
  onComplete: (sessionId: string) => void;
}

/**
 * Placeholder for future WebSocket streaming implementation.
 * Will support real-time streaming of transcription, emotion analysis,
 * and response generation for voice + video pipelines.
 */
export async function connectVoiceStream(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _request: ProcessVoiceRequest,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _callbacks: VoiceStreamCallbacks,
): Promise<() => void> {
  // TODO: Implement WebSocket streaming
  // 1. Open WebSocket to /ws/stream
  // 2. Send audio chunks
  // 3. Handle streaming events:
  //    - transcript_chunk: real-time transcription
  //    - emotion_update: live emotion analysis
  //    - response_chunk: streaming AI response
  //    - audio_stream_ready: TTS audio URL
  //    - complete: final session ID
  throw new Error("WebSocket streaming not yet implemented");
}

// ============================================================================
// RL Policy Engine Endpoints
// ============================================================================

import type {
  FeedbackRequest,
  FeedbackResponse,
  RLPolicyReport,
  RLRankings,
  RLActivePolicyResponse,
} from "../types";

/**
 * Submit explicit user feedback — primary RL reward signal.
 * score: +1 (thumbs up) or -1 (thumbs down)
 */
export async function submitFeedback(
  request: FeedbackRequest,
): Promise<FeedbackResponse> {
  const formData = new FormData();
  formData.append("interaction_id", request.interaction_id);
  formData.append("score", String(request.score));
  if (request.text) formData.append("text", request.text);
  if (request.session_duration != null)
    formData.append("session_duration", String(request.session_duration));

  const response = await getClient().post<FeedbackResponse>(
    "/feedback",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

/**
 * Get full RL policy comparison report (all three policies + arm stats).
 */
export async function getRLStats(): Promise<RLPolicyReport> {
  const response = await getClient().get<RLPolicyReport>("/rl/stats");
  return response.data;
}

/**
 * Get per-dimension arm rankings aggregated across all policies.
 */
export async function getRLRankings(): Promise<RLRankings> {
  const response = await getClient().get<RLRankings>("/rl/rankings");
  return response.data;
}

/**
 * Get the currently active (best-performing) policy and win rates.
 */
export async function getRLActivePolicy(): Promise<RLActivePolicyResponse> {
  const response =
    await getClient().get<RLActivePolicyResponse>("/rl/policy");
  return response.data;
}

/**
 * Reset RL bandit state to uniform priors (dev/testing only).
 */
export async function resetRLState(): Promise<{ status: string; message: string }> {
  const response = await getClient().post<{ status: string; message: string }>(
    "/rl/reset",
  );
  return response.data;
}
