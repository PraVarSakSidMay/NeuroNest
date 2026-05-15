"use client";
import { useState, useRef, useCallback } from "react";
import { Mic, MicOff, Loader2 } from "lucide-react";
import { analyzeVoice } from "@/lib/api";
import { useChatStore } from "@/store/chatStore";

// Pick the best supported MIME type for this browser
function getSupportedMimeType(): string {
  const types = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/ogg",
    "audio/mp4",
  ];
  for (const type of types) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return ""; // browser default
}

export function VoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const { sessionId, setSessionId, addUserMessage, addAssistantMessage, setCurrentMood, getHistory } = useChatStore();

  const startRecording = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = getSupportedMimeType();
      const options = mimeType ? { mimeType } : {};
      const mr = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mr;
      chunksRef.current = [];

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const actualMime = mr.mimeType || mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: actualMime });

        setIsProcessing(true);
        try {
          const history = getHistory();
          const result = await analyzeVoice(blob, sessionId || undefined);
          addUserMessage(`🎙️ "${result.transcribed_text}"`);
          if (!sessionId) setSessionId(result.chat_response.session_id);
          addAssistantMessage(result.chat_response.response, result.chat_response);
          setCurrentMood(result.detected_emotion, result.mood_level);
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : "Voice analysis failed";
          setError(msg);
        } finally {
          setIsProcessing(false);
        }
      };

      mr.start(250); // collect data every 250ms for reliability
      setIsRecording(true);
    } catch (err) {
      setError("Microphone access denied. Please allow microphone access and try again.");
    }
  }, [sessionId, setSessionId, addUserMessage, addAssistantMessage, setCurrentMood, getHistory]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);

  if (isProcessing) {
    return (
      <button disabled className="p-3 rounded-full bg-purple-500/20 border border-purple-500/30 text-purple-400" title="Processing...">
        <Loader2 size={20} className="animate-spin" />
      </button>
    );
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        onClick={isRecording ? stopRecording : startRecording}
        className={`p-3 rounded-full border transition-all duration-200 ${
          isRecording
            ? "bg-red-500/20 border-red-500/50 text-red-400 animate-pulse hover:bg-red-500/30"
            : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white hover:border-white/20"
        }`}
        title={isRecording ? "Stop recording" : "Start voice check-in"}
      >
        {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
      </button>
      {isRecording && (
        <span className="text-xs text-red-400 animate-pulse">Recording...</span>
      )}
      {error && (
        <p className="text-red-400 text-xs max-w-[200px] text-center">{error}</p>
      )}
    </div>
  );
}
