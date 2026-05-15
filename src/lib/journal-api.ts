/**
 * API client for the NeuroNest Reflective Journal backend.
 *
 * All functions attach a Supabase JWT Authorization header and map
 * snake_case API responses to camelCase TypeScript interfaces.
 *
 * 401 responses redirect the user to /login.
 * Other non-OK responses throw an Error with a descriptive message.
 */

import { supabase } from '@/lib/supabase'
import type {
  CreateEntryPayload,
  EmotionalSummary,
  JournalEntry,
  ReflectionRange,
} from '@/types/journal'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

/**
 * Returns headers for API requests.
 * DEMO MODE: No authentication required.
 */
async function getAuthHeaders(): Promise<HeadersInit> {
  // DEMO MODE: Skip authentication
  return {
    'Content-Type': 'application/json',
  }
  
  // PRODUCTION CODE (commented out for demo):
  // const {
  //   data: { session },
  // } = await supabase.auth.getSession()
  //
  // if (!session?.access_token) {
  //   // Redirect to login — works in both browser and Next.js middleware context
  //   if (typeof window !== 'undefined') {
  //     window.location.href = '/login'
  //   }
  //   throw new Error('No active session. Redirecting to login.')
  // }
  //
  // return {
  //   'Content-Type': 'application/json',
  //   Authorization: `Bearer ${session.access_token}`,
  // }
}

/**
 * Handles a fetch Response, throwing on errors.
 * Returns the parsed JSON body on success.
 * DEMO MODE: No auth redirect.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`
    try {
      const body = await response.json()
      if (body?.detail) {
        message = body.detail
      }
    } catch {
      // ignore JSON parse errors — use the default message
    }
    throw new Error(message)
  }

  return response.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// Response mappers (snake_case → camelCase)
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapJournalEntry(raw: any): JournalEntry {
  return {
    id: raw.id,
    userId: raw.user_id,
    title: raw.title ?? undefined,
    content: raw.content,
    mood: raw.mood ?? undefined,
    createdAt: new Date(raw.created_at),
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapEmotionalSummary(raw: any): EmotionalSummary {
  return {
    id: raw.id,
    userId: raw.user_id,
    selectedRange: {
      preset: raw.selected_range?.preset,
      startDate: raw.selected_range?.start_date,
      endDate: raw.selected_range?.end_date,
    },
    summaryText: raw.generated_summary ?? raw.summary_text ?? '',
    emotionalPatterns: raw.emotional_patterns ?? [],
    positiveObservations: raw.positive_observations ?? [],
    gentleInsights: raw.gentle_insights ?? [],
    createdAt: new Date(raw.created_at),
  }
}

// ---------------------------------------------------------------------------
// Public API functions
// ---------------------------------------------------------------------------

/**
 * Creates a new journal entry.
 * POST /journal/create
 */
export async function createEntry(payload: CreateEntryPayload): Promise<JournalEntry> {
  const headers = await getAuthHeaders()

  const response = await fetch(`${API_BASE}/journal/create`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      title: payload.title,
      content: payload.content,
      mood: payload.mood,
    }),
  })

  const raw = await handleResponse<unknown>(response)
  return mapJournalEntry(raw)
}

/**
 * Fetches all journal entries for the authenticated user in descending order.
 * GET /journal/history
 */
export async function fetchHistory(): Promise<JournalEntry[]> {
  const headers = await getAuthHeaders()

  const response = await fetch(`${API_BASE}/journal/history`, {
    method: 'GET',
    headers,
  })

  const raw = await handleResponse<unknown[]>(response)
  return raw.map(mapJournalEntry)
}

/**
 * Generates an AI emotional summary for the given reflection range.
 * POST /journal/generate-summary
 */
export async function generateSummary(range: ReflectionRange): Promise<EmotionalSummary> {
  const headers = await getAuthHeaders()

  const response = await fetch(`${API_BASE}/journal/generate-summary`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      range_type: range.preset,
      start_date: range.startDate.toISOString(),
      end_date: range.endDate.toISOString(),
    }),
  })

  const raw = await handleResponse<unknown>(response)
  return mapEmotionalSummary(raw)
}

/**
 * Fetches all previously generated emotional summaries for the authenticated user.
 * GET /journal/summaries
 */
export async function fetchSummaries(): Promise<EmotionalSummary[]> {
  const headers = await getAuthHeaders()

  const response = await fetch(`${API_BASE}/journal/summaries`, {
    method: 'GET',
    headers,
  })

  const raw = await handleResponse<unknown[]>(response)
  return raw.map(mapEmotionalSummary)
}


/**
 * Deletes a journal entry.
 * DELETE /journal/entry/{entry_id}
 */
export async function deleteEntry(entryId: string): Promise<void> {
  const headers = await getAuthHeaders()

  const response = await fetch(`${API_BASE}/journal/entry/${entryId}`, {
    method: 'DELETE',
    headers,
  })

  if (response.status === 204) {
    return // Success
  }

  await handleResponse<void>(response)
}

/**
 * Deletes an emotional summary.
 * DELETE /journal/summary/{summary_id}
 */
export async function deleteSummary(summaryId: string): Promise<void> {
  const headers = await getAuthHeaders()

  const response = await fetch(`${API_BASE}/journal/summary/${summaryId}`, {
    method: 'DELETE',
    headers,
  })

  if (response.status === 204) {
    return // Success
  }

  await handleResponse<void>(response)
}
