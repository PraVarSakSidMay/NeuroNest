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
// RL Policy Engine Types
// ============================================================================

export type PolicyName = "thompson_sampling" | "epsilon_greedy" | "ucb1";

export interface RLAction {
  persona: string;
  response_length: "brief" | "moderate" | "detailed";
  questioning_style: "none" | "open" | "reflective" | "socratic";
  motivation_style: "none" | "encouragement" | "challenge" | "reframe";
  detail_level: "concise" | "balanced" | "thorough";
}

export interface RLArmStats {
  arm: string;
  pulls: number;
  mean: number;
  alpha: number;
  beta_val: number;
  variance: number;
}

export interface RLPolicyStats {
  total_pulls: number;
  cumulative_reward: number;
  win_rate: number;
  epsilon: number | null;
  arms: Record<string, RLArmStats[]>;
}

export interface RLPolicyReport {
  active_policy: PolicyName;
  policies: Record<PolicyName, RLPolicyStats>;
}

export interface RLRankings {
  persona: Array<{ arm: string; avg_mean: number; total_pulls: number }>;
  response_length: Array<{ arm: string; avg_mean: number; total_pulls: number }>;
  questioning_style: Array<{ arm: string; avg_mean: number; total_pulls: number }>;
  motivation_style: Array<{ arm: string; avg_mean: number; total_pulls: number }>;
  detail_level: Array<{ arm: string; avg_mean: number; total_pulls: number }>;
}

export interface RLActivePolicyResponse {
  active_policy: PolicyName;
  policy_win_rates: Record<PolicyName, number>;
}

// Extended ProcessVoiceResponse with RL fields
export interface ProcessVoiceResponseRL extends ProcessVoiceResponse {
  interaction_id: string;
  applied_action: RLAction | null;
  applied_policy: PolicyName | null;
  implicit_reward: number;
}

// Feedback submission
export interface FeedbackRequest {
  interaction_id: string;
  score: 1 | -1;
  text?: string;
  session_duration?: number;
}

export interface FeedbackResponse {
  status: "success" | "error";
  reward?: number;
  message?: string;
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
