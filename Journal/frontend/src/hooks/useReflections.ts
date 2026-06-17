/* ──────────────────────────────────────────────────────────────
   useReflections — Custom hook for AI reflection management
   ────────────────────────────────────────────────────────────── */
import { useState, useEffect, useCallback } from "react";
import type { EmotionalSummary, ReflectionGenerateRequest } from "../types/reflection";
import * as reflectionService from "../services/reflectionService";

interface UseReflectionsReturn {
  reflections: EmotionalSummary[];
  total: number;
  loading: boolean;
  generating: boolean;
  error: string | null;
  refresh: () => void;
  generate: (req: ReflectionGenerateRequest) => Promise<EmotionalSummary>;
  remove: (id: string) => Promise<void>;
}

export function useReflections(): UseReflectionsReturn {
  const [reflections, setReflections] = useState<EmotionalSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReflections = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await reflectionService.getReflections();
      setReflections(data.reflections);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reflections");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReflections();
  }, [fetchReflections]);

  const generate = useCallback(async (req: ReflectionGenerateRequest) => {
    setGenerating(true);
    setError(null);
    try {
      const result = await reflectionService.generateReflection(req);
      await fetchReflections(); // Refresh list
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to generate reflection";
      setError(message);
      throw err;
    } finally {
      setGenerating(false);
    }
  }, [fetchReflections]);

  const remove = useCallback(async (id: string) => {
    await reflectionService.deleteReflection(id);
    await fetchReflections();
  }, [fetchReflections]);

  return {
    reflections, total, loading, generating, error,
    refresh: fetchReflections, generate, remove,
  };
}
