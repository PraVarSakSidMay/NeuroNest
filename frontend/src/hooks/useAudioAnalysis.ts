/**
 * Audio analysis hook - extracts voice features using Web Audio API.
 * Runs entirely in browser, SSR-safe via dynamic import pattern.
 */
import { useRef, useCallback } from "react";
import type { AudioFeatures } from "../types";

const ANALYSIS_INTERVAL = 80; // ms between samples

// ============================================================================
// Pure Audio Analysis Functions
// ============================================================================

/**
 * Compute RMS (root mean square) for volume approximation
 */
function computeRMS(data: Uint8Array): number {
  const sum = data.reduce((acc, v) => acc + v * v, 0);
  return Math.sqrt(sum / data.length);
}

/**
 * Compute spectral centroid as pitch approximation
 */
function computeSpectralCentroid(data: Uint8Array): number {
  const totalPower = data.reduce((s, v) => s + v, 0) + 0.001;
  return data.reduce((s, v, i) => s + v * i, 0) / totalPower;
}

/**
 * Compute statistics from samples
 */
function computeStats(samples: number[]): { mean: number; stdDev: number } {
  if (samples.length === 0) return { mean: 0, stdDev: 0 };
  const mean = samples.reduce((a, b) => a + b, 0) / samples.length;
  const variance =
    samples.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / samples.length;
  return { mean, stdDev: Math.sqrt(variance) };
}

// ============================================================================
// Audio Feature Extraction
// ============================================================================

export interface AudioAnalysisResult {
  pitch_mean: number;
  jitter: number;
  loudness: number;
  volume_std_dev: number;
  pitch_std_dev: number;
  is_trembling: boolean;
  is_singing: boolean;
  is_crying: boolean;
  is_whispering: boolean;
  voice_description: string;
  source: string;
}

/**
 * Analyze audio buffer and compute voice features.
 * Pure function - can be tested independently.
 */
export function analyzeAudioBuffer(
  buffer: AudioBuffer,
  sampleRate: number,
): AudioAnalysisResult {
  const channelData = buffer.getChannelData(0);
  const length = channelData.length;

  // RMS volume
  let sum = 0;
  for (let i = 0; i < length; i++) {
    sum += channelData[i] * channelData[i];
  }
  const rms = Math.sqrt(sum / length);

  // Zero crossing rate for pitch approximation
  let crossings = 0;
  for (let i = 1; i < length; i++) {
    if (channelData[i] >= 0 && channelData[i - 1] < 0) {
      crossings++;
    }
  }
  const pitchEstimate = (crossings * sampleRate) / (2 * length);

  // Convert to features
  const loudness = Math.min(1, Math.abs(rms) * 10);
  const jitter = 0;
  const volumeStdDev = 0;
  const pitchStdDev = 0;

  const isTrembling = false;
  const isSinging = false;
  const isCrying = false;
  const isWhispering = loudness < 0.1;

  const voiceDescription =
    isTrembling || isSinging || isCrying || isWhispering
      ? `${isTrembling ? "trembling " : ""}${isSinging ? "singing " : ""}${isCrying ? "crying " : ""}${isWhispering ? "whispering" : ""}`.trim()
      : "stable voice";

  return {
    pitch_mean: parseFloat(pitchEstimate.toFixed(2)),
    jitter: parseFloat(jitter.toFixed(4)),
    loudness: parseFloat(loudness.toFixed(4)),
    volume_std_dev: parseFloat(volumeStdDev.toFixed(2)),
    pitch_std_dev: parseFloat(pitchStdDev.toFixed(2)),
    is_trembling: isTrembling,
    is_singing: isSinging,
    is_crying: isCrying,
    is_whispering: isWhispering,
    voice_description: voiceDescription,
    source: "audio-buffer",
  };
}

// ============================================================================
// Stream Analysis (Real-time)
// ============================================================================

export interface StreamAnalysisController {
  stop: () => AudioFeatures | null;
}

/**
 * Start real-time audio analysis from MediaStream.
 * Returns a controller to stop analysis and get final features.
 */
export function startStreamAnalysis(
  stream: MediaStream,
  onFrame?: (features: Partial<AudioFeatures>) => void,
): StreamAnalysisController {
  const ctx = new AudioContext();
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 2048;

  const source = ctx.createMediaStreamSource(stream);
  source.connect(analyser);

  const bufferLen = analyser.frequencyBinCount;
  const freqData = new Uint8Array(bufferLen);
  const timeData = new Uint8Array(analyser.fftSize);

  const volumeSamples: number[] = [];
  const pitchSamples: number[] = [];

  let intervalId: NodeJS.Timeout | null = null;

  // Sampling loop
  intervalId = setInterval(() => {
    analyser.getByteFrequencyData(freqData);
    analyser.getByteTimeDomainData(timeData);

    // RMS Volume
    const rms = computeRMS(freqData);
    volumeSamples.push(rms);

    // Spectral centroid (pitch approximation)
    const centroid = computeSpectralCentroid(freqData);
    pitchSamples.push(centroid);

    // Real-time frame callback
    if (onFrame && volumeSamples.length < 10) {
      onFrame({
        loudness: rms / 255,
        pitch_mean: centroid * 0.5,
      });
    }
  }, ANALYSIS_INTERVAL);

  // Stop function - computes final features
  const stop = (): AudioFeatures | null => {
    if (intervalId) {
      clearInterval(intervalId);
    }
    ctx.close();

    if (volumeSamples.length < 2) return null;

    const { mean: avgVol, stdDev: volStdDev } = computeStats(volumeSamples);
    const { mean: avgPitch, stdDev: pitchStdDev } = computeStats(pitchSamples);

    const loudness = avgVol / 255;
    const jitter = volStdDev / 255;

    const isTrembling = volStdDev > 18;
    const isSinging = pitchStdDev > 30 && avgVol > 40;
    const isCrying = volStdDev > 15 && pitchStdDev > 20 && avgVol > 20;
    const isWhispering = avgVol < 15;
    const isShakingVoice = volStdDev > 25;

    const voiceDescription = [
      isSinging && "melodic/singing voice pattern with wide pitch variation",
      isCrying && "crying or tearful — irregular volume with unstable pitch",
      isTrembling && "trembling or shaking voice — high amplitude instability",
      isWhispering && "very quiet, almost whispering",
      isShakingVoice && "severely unstable voice suggesting strong emotion",
    ]
      .filter(Boolean)
      .join("; ") || "stable and composed voice";

    return {
      pitch_mean: parseFloat((avgPitch * 0.5).toFixed(2)),
      jitter: parseFloat(jitter.toFixed(4)),
      loudness: parseFloat(loudness.toFixed(4)),
      volume_std_dev: parseFloat(volStdDev.toFixed(2)),
      pitch_std_dev: parseFloat(pitchStdDev.toFixed(2)),
      is_trembling: isTrembling,
      is_singing: isSinging,
      is_crying: isCrying,
      is_whispering: isWhispering,
      voice_description: voiceDescription,
      source: "web-audio-api",
    };
  };

  return { stop };
}

// ============================================================================
// React Hook Wrapper
// ============================================================================

export function useAudioAnalysis() {
  const controllerRef = useRef<StreamAnalysisController | null>(null);

  const startAnalysis = useCallback(
    (stream: MediaStream, onFrame?: (features: Partial<AudioFeatures>) => void) => {
      controllerRef.current = startStreamAnalysis(stream, onFrame);
    },
    [],
  );

  const stopAnalysis = useCallback((): AudioFeatures | null => {
    if (controllerRef.current) {
      const features = controllerRef.current.stop();
      controllerRef.current = null;
      return features;
    }
    return null;
  }, []);

  return { startAnalysis, stopAnalysis };
}