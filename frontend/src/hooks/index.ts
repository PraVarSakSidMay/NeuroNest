// ============================================================================
// Audio Hooks - Public API
// ============================================================================

export { useAudioRecorder } from "./useAudioRecorder";
export type { AudioRecorderState, AudioRecorderResult } from "./useAudioRecorder";

export { useAudioAnalysis, startStreamAnalysis, analyzeAudioBuffer } from "./useAudioAnalysis";
export type { AudioAnalysisResult, StreamAnalysisController } from "./useAudioAnalysis";