/**
 * Conversation store - manages conversation state.
 * Pure state container, no business logic.
 */
import { create } from "zustand";
import type { Emotion } from "../types";

export interface Interaction {
  id: string;
  transcript: string;
  response: string;
  emotion: Emotion | null;
  timestamp: number;
}

export interface ConversationState {
  transcript: string;
  response: string;
  emotion: Emotion | null;
  sessionId: string | null;
  interactions: Interaction[];
}

export interface ConversationActions {
  setTranscript: (transcript: string) => void;
  setResponse: (response: string) => void;
  setEmotion: (emotion: Emotion | null) => void;
  setSessionId: (sessionId: string) => void;
  appendInteraction: (interaction: Interaction) => void;
  updateResponse: (partialResponse: string) => void;
  reset: () => void;
}

export type ConversationStore = ConversationState & ConversationActions;

const initialState: ConversationState = {
  transcript: "",
  response: "",
  emotion: null,
  sessionId: null,
  interactions: [],
};

export const useConversationStore = create<ConversationStore>()((set) => ({
  ...initialState,

  setTranscript: (transcript) => set({ transcript }),

  setResponse: (response) => set({ response }),

  setEmotion: (emotion) => set({ emotion }),

  setSessionId: (sessionId) => set({ sessionId }),

  appendInteraction: (interaction) =>
    set((state) => ({
      interactions: [...state.interactions, interaction],
    })),

  updateResponse: (partialResponse) =>
    set((state) => ({
      response: state.response + partialResponse,
    })),

  reset: () => set(initialState),
}));