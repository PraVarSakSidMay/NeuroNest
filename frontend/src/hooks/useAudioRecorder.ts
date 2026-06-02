/**
 * Audio recorder hook - handles microphone access and recording.
 * SSR-safe via dynamic import and browser-only APIs.
 */
import { useRef, useCallback, useState } from "react";

export interface AudioRecorderState {
  isRecording: boolean;
  error: string | null;
}

export interface AudioRecorderResult {
  state: AudioRecorderState;
  startRecording: () => Promise<MediaRecorder>;
  stopRecording: () => Promise<Blob | null>;
  reset: () => void;
}

// ============================================================================
// Browser-safe helpers
// ============================================================================

function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof navigator !== "undefined";
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useAudioRecorder(): AudioRecorderResult {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [state, setState] = useState<AudioRecorderState>({
    isRecording: false,
    error: null,
  });

  const reset = useCallback(() => {
    setState({ isRecording: false, error: null });
  }, []);

  const startRecording = useCallback(async (): Promise<MediaRecorder> => {
    if (!isBrowser()) {
      setState({ isRecording: false, error: "Not available in server context" });
      throw new Error("Recording not available in server context");
    }

    // If already recording, return existing recorder
    if (mediaRecorderRef.current?.state === "recording") {
      return mediaRecorderRef.current;
    }

    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      audioChunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        // Clean up stream tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.start(250); // Collect data every 250ms
      setState({ isRecording: true, error: null });

      return mediaRecorder;
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message.includes("Permission denied")
            ? "Microphone access denied. Please allow microphone access."
            : err.message
          : "Failed to start recording";
      setState({ isRecording: false, error: message });
      throw err;
    }
  }, []);

  const stopRecording = useCallback((): Promise<Blob | null> => {
    if (!mediaRecorderRef.current) {
      return Promise.resolve(null);
    }

    return new Promise<Blob | null>((resolve) => {
      const recorder = mediaRecorderRef.current;

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        audioChunksRef.current = [];
        mediaRecorderRef.current = null;

        // Ensure stream is stopped
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        setState((s) => ({ ...s, isRecording: false }));
        resolve(blob);
      };

      if (recorder.state !== "inactive") {
        recorder.stop();
      } else {
        resolve(null);
      }
    });
  }, []);

  return {
    state,
    startRecording,
    stopRecording,
    reset,
  };
}