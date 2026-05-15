import { create } from "zustand";
import { ChatMessage, ChatResponse } from "@/lib/api";

export interface DisplayMessage {
  id: string; role: "user" | "assistant"; content: string;
  timestamp: Date; chatResponse?: ChatResponse;
}

interface ChatStore {
  messages: DisplayMessage[]; sessionId: string | null;
  isLoading: boolean; isRecording: boolean;
  currentEmotion: string | null; currentMood: string | null;
  addUserMessage: (content: string) => void;
  addAssistantMessage: (content: string, response: ChatResponse) => void;
  setLoading: (loading: boolean) => void;
  setRecording: (recording: boolean) => void;
  setSessionId: (id: string) => void;
  setCurrentMood: (emotion: string, mood: string) => void;
  getHistory: () => ChatMessage[];
  clearChat: () => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [], sessionId: null, isLoading: false, isRecording: false,
  currentEmotion: null, currentMood: null,
  addUserMessage: (content) => set((s) => ({ messages: [...s.messages, { id: crypto.randomUUID(), role: "user", content, timestamp: new Date() }] })),
  addAssistantMessage: (content, response) => set((s) => ({ messages: [...s.messages, { id: crypto.randomUUID(), role: "assistant", content, timestamp: new Date(), chatResponse: response }] })),
  setLoading: (isLoading) => set({ isLoading }),
  setRecording: (isRecording) => set({ isRecording }),
  setSessionId: (sessionId) => set({ sessionId }),
  setCurrentMood: (currentEmotion, currentMood) => set({ currentEmotion, currentMood }),
  getHistory: () => get().messages.map((m) => ({ role: m.role, content: m.content })),
  clearChat: () => set({ messages: [], sessionId: null, currentEmotion: null, currentMood: null }),
}));
