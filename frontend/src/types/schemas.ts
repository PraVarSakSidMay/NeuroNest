/**
 * Zod validation schemas for runtime validation.
 * Used for frontend audio analysis data and request validation.
 */
import { z } from "zod";

// ============================================================================
// Audio Features Schema
// ============================================================================

export const AudioFeaturesSchema = z.object({
  pitch_mean: z.number(),
  jitter: z.number(),
  loudness: z.number(),
  volume_std_dev: z.number(),
  pitch_std_dev: z.number(),
  is_trembling: z.boolean(),
  is_singing: z.boolean(),
  is_crying: z.boolean(),
  is_whispering: z.boolean(),
  voice_description: z.string(),
  audio_emotion_hint: z.string().optional(),
  source: z.string(),
});

export type AudioFeaturesSchema = z.infer<typeof AudioFeaturesSchema>;

// ============================================================================
// Emotion Schema
// ============================================================================

const EmotionTypeEnum = z.enum([
  "neutral",
  "happy",
  "sad",
  "angry",
  "anxious",
  "fearful",
  "surprised",
  "disgusted",
  "confused",
  "excited",
  "frustrated",
  "depressed",
  "calm",
]);

export const EmotionSchema = z.object({
  emotion: EmotionTypeEnum,
  stress_level: z.number().int().min(0).max(100),
  tone: z.string(),
  contradiction_detected: z.boolean(),
  hidden_emotion: z.string(),
  confidence: z.number().min(0).max(1),
});

export type EmotionSchema = z.infer<typeof EmotionSchema>;

// ============================================================================
// Voice Name Schema (validated options)
// ============================================================================

export const VoiceNameSchema = z.enum(["Amelia", "Rachel", "Josh", "Nathan", "Sam"]);

export const VoicePreviewSchema = z.object({
  voice_name: VoiceNameSchema,
});

export type VoicePreviewSchema = z.infer<typeof VoicePreviewSchema>;

// ============================================================================
// WebSocket Event Schemas (for future streaming)
// ============================================================================

export const WsEventTypes = z.enum([
  "transcript_chunk",
  "emotion_update",
  "response_chunk",
  "audio_stream_ready",
  "error",
  "complete",
]);

export const WsTranscriptChunkSchema = z.object({
  type: z.literal("transcript_chunk"),
  data: z.string(),
  timestamp: z.number(),
});

export const WsEmotionUpdateSchema = z.object({
  type: z.literal("emotion_update"),
  data: EmotionSchema,
});

export const WsResponseChunkSchema = z.object({
  type: z.literal("response_chunk"),
  data: z.string(),
  complete: z.boolean(),
});

export const WsAudioStreamSchema = z.object({
  type: z.literal("audio_stream_ready"),
  data: z.object({
    audio_url: z.string().nullable(),
    session_id: z.string(),
  }),
});

export const WsErrorSchema = z.object({
  type: z.literal("error"),
  data: z.object({
    message: z.string(),
    code: z.string().optional(),
  }),
});

export const WsCompleteSchema = z.object({
  type: z.literal("complete"),
  data: z.object({
    session_id: z.string(),
  }),
});

// Union type for all WebSocket events
export const WsEventSchema = z.discriminatedUnion("type", [
  WsTranscriptChunkSchema,
  WsEmotionUpdateSchema,
  WsResponseChunkSchema,
  WsAudioStreamSchema,
  WsErrorSchema,
  WsCompleteSchema,
]);

export type WsEvent = z.infer<typeof WsEventSchema>;