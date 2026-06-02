/**
 * API contracts for frontend-backend communication.
 * Mirrors backend DTOs from backend/models/interaction.py and backend/application/dtos/
 */

// ============================================================================
// Enums
// ============================================================================

export type EmotionType =
  | "neutral"
  | "happy"
  | "sad"
  | "angry"
  | "anxious"
  | "fearful"
  | "surprised"
  | "disgusted"
  | "confused"
  | "excited"
  | "frustrated"
  | "depressed"
  | "calm";

// ============================================================================
// Audio Features
// ============================================================================

export interface AudioFeatures {
  pitch_mean: number;
  jitter: number;
  loudness: number;
  volume_std_dev: number;
  pitch_std_dev: number;
  is_trembling: boolean;
  is_singing: boolean;
  is_crying: boolean;
  is_whispering: boolean;
  voice_description: string;
  audio_emotion_hint?: string;
  source: string;
}

// ============================================================================
// Emotion Data
// ============================================================================

export interface Emotion {
  emotion: EmotionType;
  stress_level: number;
  tone: string;
  contradiction_detected: boolean;
  hidden_emotion: string;
  confidence: number;
}

export interface ExpressionHistoryEntry {
  emotion: EmotionType;
  confidence: number;
  timestamp: number;
  source: "video" | "audio" | "inferred";
  face_quality?: number;
  eye_contact?: boolean;
  head_pose?: { pitch: number; yaw: number; roll: number };
  action_units?: Record<string, number>;
}

// ============================================================================
// Session
// ============================================================================

export interface Session {
  id: string;
  user_id: string;
  started_at: string; // ISO datetime
  ended_at: string | null; // ISO datetime
}

// ============================================================================
// Interaction
// ============================================================================

export interface Interaction {
  id: string;
  session_id: string;
  user_id: string;
  transcript: string;
  raw_audio_url: string | null;
  features: AudioFeatures | null;
  emotion_data: Emotion | null;
  response_text: string | null;
  tts_audio_url: string | null;
  created_at: string; // ISO datetime
}

// ============================================================================
// Process Voice Request
// ============================================================================

export interface ProcessVoiceRequest {
  file: File;
  audio_analysis?: string; // JSON string of AudioFeatures
  video_analysis?: string; // JSON string of VideoEmotion / Telemetry
  expression_history?: ExpressionHistoryEntry[];
  voice_name: string;
}

// ============================================================================
// Process Voice Response
// ============================================================================

export type Dashboard = Array<{
  transcript: string;
  emotion: EmotionType;
  stress_level: number;
}>;

export interface ProcessVoiceResponse {
  transcript: string;
  audio_features: AudioFeatures;
  emotion: Emotion;
  response: string;
  audio_url: string | null;
  memories_used: number;
  session_id: string | null;
  dashboard: Dashboard | null;
}

// ============================================================================
// Session Start Response
// ============================================================================

export interface SessionStartResponse {
  greeting: string | null;
}

// ============================================================================
// Preview Voice Response
// ============================================================================

export interface PreviewVoiceResponse {
  audio_url: string | null;
  error: string | null;
}

// ============================================================================
// API Error
// ============================================================================

export interface ApiError {
  error: string;
  detail: string;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ApiErrorResponse {
  detail: string | ValidationError[];
}
