/**
 * Voice store - manages voice/audio state.
 * Pure state container, no recording/analysis logic.
 */
import { create } from "zustand";
import type { AudioFeatures } from "../types";

export interface VoiceState {
  isRecording: boolean;
  isProcessing: boolean;
  audioBlob: Blob | null;
  audioFeatures: AudioFeatures | null;
  selectedVoice: string;
}

export interface VoiceActions {
  setIsRecording: (isRecording: boolean) => void;
  setIsProcessing: (isProcessing: boolean) => void;
  setAudioBlob: (audioBlob: Blob | null) => void;
  setAudioFeatures: (audioFeatures: AudioFeatures | null) => void;
  setSelectedVoice: (voice: string) => void;
  reset: () => void;
}

export type VoiceStore = VoiceState & VoiceActions;

const initialState: VoiceState = {
  isRecording: false,
  isProcessing: false,
  audioBlob: null,
  audioFeatures: null,
  selectedVoice: "Rachel",
};

export const useVoiceStore = create<VoiceStore>()((set) => ({
  ...initialState,

  setIsRecording: (isRecording) => set({ isRecording }),

  setIsProcessing: (isProcessing) => set({ isProcessing }),

  setAudioBlob: (audioBlob) => set({ audioBlob }),

  setAudioFeatures: (audioFeatures) => set({ audioFeatures }),

  setSelectedVoice: (selectedVoice) => set({ selectedVoice }),

  reset: () => set(initialState),
}));