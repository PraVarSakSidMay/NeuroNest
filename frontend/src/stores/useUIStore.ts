/**
 * UI store - manages UI state and flags.
 * Pure state container, no business logic.
 */
import { create } from "zustand";

export interface UIState {
  isLoading: boolean;
  isSpeaking: boolean;
  isThinking: boolean;
  isPreviewLoading: boolean;
  error: string | null;
}

export interface UIActions {
  setLoading: (isLoading: boolean) => void;
  setSpeaking: (isSpeaking: boolean) => void;
  setThinking: (isThinking: boolean) => void;
  setPreviewLoading: (isPreviewLoading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  reset: () => void;
}

export type UIStore = UIState & UIActions;

const initialState: UIState = {
  isLoading: false,
  isSpeaking: false,
  isThinking: false,
  isPreviewLoading: false,
  error: null,
};

export const useUIStore = create<UIStore>()((set) => ({
  ...initialState,

  setLoading: (isLoading) => set({ isLoading }),

  setSpeaking: (isSpeaking) => set({ isSpeaking }),

  setThinking: (isThinking) => set({ isThinking }),

  setPreviewLoading: (isPreviewLoading) => set({ isPreviewLoading }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),

  reset: () => set(initialState),
}));