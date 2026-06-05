/**
 * Public API for types module.
 * Import from this file to get all types and schemas.
 */

// Type definitions
export type {
  EmotionType,
  AudioFeatures,
  Emotion,
  Session,
  Interaction,
  ProcessVoiceRequest,
  ProcessVoiceResponse,
  SessionStartResponse,
  PreviewVoiceResponse,
  Dashboard,
  ApiError,
  ValidationError,
  ApiErrorResponse,
  ExpressionHistoryEntry,
  // RL Policy Engine types
  PolicyName,
  RLAction,
  RLArmStats,
  RLPolicyStats,
  RLPolicyReport,
  RLRankings,
  RLActivePolicyResponse,
  ProcessVoiceResponseRL,
  FeedbackRequest,
  FeedbackResponse,
} from "./api";

// Zod schemas
export {
  AudioFeaturesSchema,
  EmotionSchema,
  VoiceNameSchema,
  VoicePreviewSchema,
  WsEventTypes,
  WsEventSchema,
  WsTranscriptChunkSchema,
  WsEmotionUpdateSchema,
  WsResponseChunkSchema,
  WsAudioStreamSchema,
  WsErrorSchema,
  WsCompleteSchema,
} from "./schemas";

export type {
  AudioFeaturesSchema as AudioFeaturesValidation,
  EmotionSchema as EmotionValidation,
  VoicePreviewSchema as VoicePreviewValidation,
  WsEvent,
} from "./schemas";