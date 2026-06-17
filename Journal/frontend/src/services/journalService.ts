/* ──────────────────────────────────────────────────────────────
   Journal Service — API calls for journal entries
   ────────────────────────────────────────────────────────────── */
import api from "./api";
import type {
  JournalEntry,
  JournalCreateRequest,
  JournalUpdateRequest,
  JournalListResponse,
  JournalQueryParams,
} from "../types/journal";

/** Create a new journal entry */
export async function createEntry(data: JournalCreateRequest): Promise<JournalEntry> {
  const res = await api.post<JournalEntry>("/journal/", data);
  return res.data;
}

/** Fetch paginated journal entries with optional filters */
export async function getEntries(params: JournalQueryParams = {}): Promise<JournalListResponse> {
  const res = await api.get<JournalListResponse>("/journal/", { params });
  return res.data;
}

/** Fetch a single journal entry by ID */
export async function getEntry(id: string): Promise<JournalEntry> {
  const res = await api.get<JournalEntry>(`/journal/${id}`);
  return res.data;
}

/** Update a journal entry */
export async function updateEntry(id: string, data: JournalUpdateRequest): Promise<JournalEntry> {
  const res = await api.put<JournalEntry>(`/journal/${id}`, data);
  return res.data;
}

/** Delete a journal entry */
export async function deleteEntry(id: string): Promise<void> {
  await api.delete(`/journal/${id}`);
}
