/* ──────────────────────────────────────────────────────────────
   useJournalEntries — Custom hook for journal CRUD & filtering
   ────────────────────────────────────────────────────────────── */
import { useState, useEffect, useCallback } from "react";
import type { JournalEntry, JournalQueryParams, Mood, SortOrder } from "../types/journal";
import * as journalService from "../services/journalService";

interface UseJournalEntriesReturn {
  entries: JournalEntry[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error: string | null;
  search: string;
  moodFilter: Mood | undefined;
  sortOrder: SortOrder;
  setSearch: (s: string) => void;
  setMoodFilter: (m: Mood | undefined) => void;
  setSortOrder: (o: SortOrder) => void;
  setPage: (p: number) => void;
  refresh: () => void;
  removeEntry: (id: string) => Promise<void>;
}

export function useJournalEntries(initialPageSize = 9): UseJournalEntriesReturn {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(initialPageSize);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [moodFilter, setMoodFilter] = useState<Mood | undefined>();
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: JournalQueryParams = {
        page,
        page_size: pageSize,
        sort_order: sortOrder,
      };
      if (search) params.search = search;
      if (moodFilter) params.mood = moodFilter;

      const data = await journalService.getEntries(params);
      setEntries(data.entries);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load entries");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, moodFilter, sortOrder]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
  }, [search, moodFilter, sortOrder]);

  const removeEntry = useCallback(async (id: string) => {
    await journalService.deleteEntry(id);
    await fetchEntries();
  }, [fetchEntries]);

  return {
    entries, total, page, pageSize,
    loading, error,
    search, moodFilter, sortOrder,
    setSearch, setMoodFilter, setSortOrder, setPage,
    refresh: fetchEntries, removeEntry,
  };
}
