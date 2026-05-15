import { z } from 'zod'

// ---------------------------------------------------------------------------
// Enums / union types
// ---------------------------------------------------------------------------

export type MoodType = 'calm' | 'stressed' | 'tired' | 'happy' | 'anxious' | 'overwhelmed'
export type RangePreset = '3d' | '5d' | '7d' | '30d' | 'custom'

export const MOOD_TYPES: MoodType[] = ['calm', 'stressed', 'tired', 'happy', 'anxious', 'overwhelmed']
export const RANGE_PRESETS: RangePreset[] = ['3d', '5d', '7d', '30d', 'custom']

// ---------------------------------------------------------------------------
// Diagnostic language blocklist (mirrors backend/services/ai_orchestrator.py)
// Used for client-side filtering before rendering AI-generated content.
// ---------------------------------------------------------------------------

export const DIAGNOSTIC_LANGUAGE_BLOCKLIST: string[] = [
  'depression',
  'anxiety disorder',
  'bipolar',
  'schizophrenia',
  'ptsd',
  'post-traumatic',
  'borderline personality',
  'ocd',
  'obsessive-compulsive',
  'adhd',
  'attention deficit',
  'autism',
  'diagnose',
  'diagnosis',
  'disorder',
  'clinical',
  'psychiatric',
  'therapy',
  'therapist',
  'medication',
  'prescribe',
  'symptom',
  'treatment plan',
  'mental illness',
  'suicidal',
  'self-harm',
]

// ---------------------------------------------------------------------------
// Request / payload interfaces
// ---------------------------------------------------------------------------

export interface CreateEntryPayload {
  title?: string
  content: string
  mood?: MoodType
}

// ---------------------------------------------------------------------------
// Journal entry interfaces
// ---------------------------------------------------------------------------

export interface JournalEntry {
  id: string
  userId: string
  title?: string
  content: string
  mood?: MoodType
  createdAt: Date
}

export interface JournalEntryPreview {
  id: string
  title?: string
  contentSnippet: string
  mood?: MoodType
  createdAt: Date
}

// ---------------------------------------------------------------------------
// Reflection range interfaces
// ---------------------------------------------------------------------------

export interface ReflectionRange {
  preset: RangePreset
  startDate: Date
  endDate: Date
}

// ---------------------------------------------------------------------------
// Emotional summary interfaces
// ---------------------------------------------------------------------------

export interface EmotionalSummary {
  id: string
  userId: string
  selectedRange: {
    preset: RangePreset
    startDate: string
    endDate: string
  }
  summaryText: string
  emotionalPatterns: string[]
  positiveObservations: string[]
  gentleInsights: string[]
  createdAt: Date
}

export interface EmotionalSummaryPreview {
  id: string
  rangeLabel: string
  summarySnippet: string
  createdAt: Date
}

// ---------------------------------------------------------------------------
// Zod validation schemas
// ---------------------------------------------------------------------------

export const createEntrySchema = z.object({
  title: z.string().max(200).optional(),
  content: z.string().min(1).max(10000),
  mood: z.enum(['calm', 'stressed', 'tired', 'happy', 'anxious', 'overwhelmed']).optional(),
})

export const reflectionRangeSchema = z
  .object({
    preset: z.enum(['3d', '5d', '7d', '30d', 'custom']),
    startDate: z.date(),
    endDate: z.date(),
  })
  .refine((data: { preset: string; startDate: Date; endDate: Date }) => data.startDate <= data.endDate, {
    message: 'Start date must be before end date',
  })
