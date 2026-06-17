/* ──────────────────────────────────────────────────────────────
   Reflection Service — API calls for AI reflections
   ────────────────────────────────────────────────────────────── */
import api from "./api";
import type {
  EmotionalSummary,
  ReflectionGenerateRequest,
  ReflectionListResponse,
} from "../types/reflection";

/** Generate a new AI reflection for a given date range */
export async function generateReflection(
  data: ReflectionGenerateRequest
): Promise<EmotionalSummary> {
  const res = await api.post<EmotionalSummary>("/reflections/generate", data);
  return res.data;
}

/** Fetch all saved reflections */
export async function getReflections(
  page = 1,
  pageSize = 20
): Promise<ReflectionListResponse> {
  const res = await api.get<ReflectionListResponse>("/reflections/", {
    params: { page, page_size: pageSize },
  });
  return res.data;
}

/** Delete a reflection by ID */
export async function deleteReflection(id: string): Promise<void> {
  await api.delete(`/reflections/${id}`);
}
