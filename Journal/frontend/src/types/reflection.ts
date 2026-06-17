/* ──────────────────────────────────────────────────────────────
   Reflection / AI Summary Types
   ────────────────────────────────────────────────────────────── */

/** Predefined date range options for generating reflections */
export type RangeType =
  | "last_3_days"
  | "last_5_days"
  | "last_7_days"
  | "last_30_days"
  | "custom";

/** Human-readable labels for range types */
export const RANGE_LABELS: Record<RangeType, string> = {
  last_3_days:  "Last 3 Days",
  last_5_days:  "Last 5 Days",
  last_7_days:  "Last 7 Days",
  last_30_days: "Last 30 Days",
  custom:       "Custom Range",
};

/** All range types as an array */
export const ALL_RANGES: RangeType[] = [
  "last_3_days", "last_5_days", "last_7_days", "last_30_days", "custom",
];

/** Request body for generating an AI reflection */
export interface ReflectionGenerateRequest {
  range_type: RangeType;
  start_date?: string;
  end_date?: string;
}

/** A single AI-generated emotional reflection */
export interface EmotionalSummary {
  id: string;
  summary: string;
  emotional_patterns: string[];
  positive_observations: string[];
  gentle_insights: string[];
  growth_suggestions: string[];
  selected_range: {
    range_type: RangeType;
    start_date: string;
    end_date: string;
  };
  created_at: string;
}

/** Paginated list of reflections */
export interface ReflectionListResponse {
  reflections: EmotionalSummary[];
  total: number;
}
