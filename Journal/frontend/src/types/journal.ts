/* ──────────────────────────────────────────────────────────────
   Journal Types
   ────────────────────────────────────────────────────────────── */

/** Supported mood categories for journal entries */
export type Mood =
  | "Happy"
  | "Calm"
  | "Excited"
  | "Motivated"
  | "Tired"
  | "Sad"
  | "Anxious"
  | "Stressed"
  | "Overwhelmed";

/** All available moods with their emoji and color mappings */
export const MOOD_CONFIG: Record<Mood, { emoji: string; color: string; bgColor: string }> = {
  Happy:       { emoji: "😊", color: "#fbbf24", bgColor: "rgba(251, 191, 36, 0.15)" },
  Calm:        { emoji: "😌", color: "#34d399", bgColor: "rgba(52, 211, 153, 0.15)" },
  Excited:     { emoji: "🎉", color: "#f97316", bgColor: "rgba(249, 115, 22, 0.15)" },
  Motivated:   { emoji: "💪", color: "#8b5cf6", bgColor: "rgba(139, 92, 246, 0.15)" },
  Tired:       { emoji: "😴", color: "#94a3b8", bgColor: "rgba(148, 163, 184, 0.15)" },
  Sad:         { emoji: "😢", color: "#60a5fa", bgColor: "rgba(96, 165, 250, 0.15)" },
  Anxious:     { emoji: "😰", color: "#fb7185", bgColor: "rgba(251, 113, 133, 0.15)" },
  Stressed:    { emoji: "😤", color: "#f43f5e", bgColor: "rgba(244, 63, 94, 0.15)" },
  Overwhelmed: { emoji: "🤯", color: "#e879f9", bgColor: "rgba(232, 121, 249, 0.15)" },
};

/** All mood values as an array for iteration */
export const ALL_MOODS: Mood[] = [
  "Happy", "Calm", "Excited", "Motivated", "Tired",
  "Sad", "Anxious", "Stressed", "Overwhelmed",
];

/** A single journal entry as returned by the API */
export interface JournalEntry {
  id: string;
  title: string;
  content: string;
  mood: Mood;
  created_at: string;
  updated_at: string;
}

/** Request body for creating a journal entry */
export interface JournalCreateRequest {
  title: string;
  content: string;
  mood: Mood;
}

/** Request body for updating a journal entry */
export interface JournalUpdateRequest {
  title?: string;
  content?: string;
  mood?: Mood;
}

/** Paginated list of journal entries */
export interface JournalListResponse {
  entries: JournalEntry[];
  total: number;
  page: number;
  page_size: number;
}

/** Sort direction for journal entries */
export type SortOrder = "desc" | "asc";

/** Query parameters for fetching journal entries */
export interface JournalQueryParams {
  search?: string;
  mood?: Mood;
  page?: number;
  page_size?: number;
  sort_order?: SortOrder;
}
