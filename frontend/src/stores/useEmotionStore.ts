/**
 * Emotion store - manages real-time video emotion, landmarks tracking,
 * and multimodal fusion state.
 */
import { create } from "zustand";
import type { ExpressionHistoryEntry } from "../types";

export interface VideoEmotion {
  emotion: string;
  confidence: number;
  actionUnits: Record<string, number>;
}

export interface FusedEmotion {
  emotion: string;
  confidence: number;
  isMasked: boolean;
  maskConfidence: number;
  recommendation: string;
}

export interface EmotionState {
  videoEmotion: VideoEmotion | null;
  fusedEmotion: FusedEmotion | null;
  faceQuality: number;
  trackingStatus: "off" | "loading" | "tracking" | "no-face" | "error";
  fps: number;
  cameraActive: boolean;
  isCalibrating: boolean;
  calibrationProgress: number;
  neutralBaseline: Record<string, number> | null;
  eyeContact: boolean;
  headPose: { pitch: number; yaw: number; roll: number };
  eyeContactHistory: boolean[];
  expressionHistory: ExpressionHistoryEntry[];
}

export interface EmotionActions {
  setVideoEmotion: (videoEmotion: VideoEmotion | null) => void;
  setFusedEmotion: (fusedEmotion: FusedEmotion | null) => void;
  setFaceQuality: (faceQuality: number) => void;
  setTrackingStatus: (status: EmotionState["trackingStatus"]) => void;
  setFps: (fps: number) => void;
  setCameraActive: (active: boolean) => void;
  setIsCalibrating: (isCalibrating: boolean) => void;
  setCalibrationProgress: (progress: number) => void;
  setNeutralBaseline: (baseline: Record<string, number> | null) => void;
  startCalibration: () => void;
  cancelCalibration: () => void;
  setEyeContact: (contact: boolean) => void;
  setHeadPose: (pose: { pitch: number; yaw: number; roll: number }) => void;
  addEyeContactHistory: (contact: boolean) => void;
  clearEyeContactHistory: () => void;
  addExpressionHistory: (expression: ExpressionHistoryEntry) => void;
  clearExpressionHistory: () => void;
  reset: () => void;
}

export type EmotionStore = EmotionState & EmotionActions;

const initialState: EmotionState = {
  videoEmotion: null,
  fusedEmotion: null,
  faceQuality: 0,
  trackingStatus: "off",
  fps: 0,
  cameraActive: false,
  isCalibrating: false,
  calibrationProgress: 0,
  neutralBaseline: null,
  eyeContact: true,
  headPose: { pitch: 0, yaw: 0, roll: 0 },
  eyeContactHistory: [],
  expressionHistory: [],
};

export const useEmotionStore = create<EmotionStore>()((set) => ({
  ...initialState,

  setVideoEmotion: (videoEmotion) => set({ videoEmotion }),

  setFusedEmotion: (fusedEmotion) => set({ fusedEmotion }),

  setFaceQuality: (faceQuality) => set({ faceQuality }),

  setTrackingStatus: (trackingStatus) => set({ trackingStatus }),

  setFps: (fps) => set({ fps }),

  setCameraActive: (cameraActive) => set({ cameraActive }),

  setIsCalibrating: (isCalibrating) => set({ isCalibrating }),

  setCalibrationProgress: (calibrationProgress) => set({ calibrationProgress }),

  setNeutralBaseline: (neutralBaseline) => set({ neutralBaseline }),

  startCalibration: () => set({ isCalibrating: true, calibrationProgress: 0 }),

  cancelCalibration: () => set({ isCalibrating: false, calibrationProgress: 0 }),

  setEyeContact: (eyeContact) => set({ eyeContact }),

  setHeadPose: (headPose) => set({ headPose }),

  addEyeContactHistory: (contact) => set((state) => ({ 
    eyeContactHistory: [...state.eyeContactHistory, contact] 
  })),

  clearEyeContactHistory: () => set({ eyeContactHistory: [] }),

  addExpressionHistory: (expression) => set((state) => ({
    expressionHistory: [...state.expressionHistory, expression],
  })),

  clearExpressionHistory: () => set({ expressionHistory: [] }),

  reset: () => set((state) => ({
    ...initialState,
    neutralBaseline: state.neutralBaseline, // Preserve baseline across normal resets
  })),
}));
