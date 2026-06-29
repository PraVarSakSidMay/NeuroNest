"use client";

import { useRef, useState, useEffect } from "react";
import {
  Mic,
  Square,
  Activity,
  Sparkles,
  BrainCircuit,
  HeartPulse,
  Zap,
  BookOpen,
  Brain,
  Camera,
  CameraOff,
  AlertCircle,
  ShieldCheck,
  Lock,
  WifiOff,
  X,
  Wind,
  Volume2,
  Heart,
} from "lucide-react";
import { startSession, processVoice, previewVoice as previewVoiceApi } from "../lib/api-client";
import { Emotion } from "../types";
import type { RLAction, PolicyName } from "../types";
import { useEmotionStore } from "../stores/useEmotionStore";
import { useVoiceStore } from "../stores/useVoiceStore";
import { useConversationStore } from "../stores/useConversationStore";
import { useVideoEmotionDetection } from "../hooks/useVideoEmotionDetection";
import { PrivacyConsent } from "./privacy/PrivacyConsent";
import FeedbackWidget from "./FeedbackWidget";

const DAILY_REQUEST_LIMIT = 100;
const USAGE_STORAGE_KEY = "neuronest_api_usage";
const LEGACY_GROQ_USAGE_KEY = "groq_usage";

function getUsageData() {
  const today = new Date().toISOString().split("T")[0];
  const stored = JSON.parse(
    localStorage.getItem(USAGE_STORAGE_KEY) ||
      localStorage.getItem(LEGACY_GROQ_USAGE_KEY) ||
      "{}"
  );
  if (stored.date !== today) {
    const fresh = { date: today, requests: 0 };
    localStorage.setItem(USAGE_STORAGE_KEY, JSON.stringify(fresh));
    return fresh;
  }
  localStorage.setItem(USAGE_STORAGE_KEY, JSON.stringify(stored));
  return stored;
}

function incrementUsage() {
  const usage = getUsageData();
  usage.requests = (usage.requests || 0) + 1;
  localStorage.setItem(USAGE_STORAGE_KEY, JSON.stringify(usage));
  return usage;
}

function CreditsBar({ requests }) {
  const used = requests || 0;
  const remaining = Math.max(0, DAILY_REQUEST_LIMIT - used);
  const pct = Math.max(0, Math.min(100, (remaining / DAILY_REQUEST_LIMIT) * 100));

  const barColor =
    pct > 50
      ? "from-emerald-400 to-green-500"
      : pct > 20
      ? "from-amber-400 to-yellow-500"
      : "from-red-400 to-rose-500";
  const textColor = pct > 50 ? "text-emerald-600" : pct > 20 ? "text-amber-600" : "text-rose-600";
  const bgColor =
    pct > 50
      ? "bg-emerald-50 border-emerald-200"
      : pct > 20
      ? "bg-amber-50 border-amber-200"
      : "bg-rose-50 border-rose-200";

  return (
    <div className={`relative z-10 mb-6 p-4 rounded-2xl border ${bgColor}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Zap className={`w-4 h-4 ${textColor}`} />
          <span className={`text-xs font-bold uppercase tracking-wider ${textColor}`}>
            AI Request Budget
          </span>
        </div>
        <span className={`text-sm font-bold ${textColor}`}>{pct.toFixed(0)}% remaining</span>
      </div>
      <div className="w-full h-2.5 bg-white/60 rounded-full overflow-hidden border border-white/80">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${barColor} transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex items-center justify-between mt-2">
        <span className="text-xs text-slate-400">{used} requests used today</span>
        <span className="text-xs text-slate-400">~{remaining} remaining</span>
      </div>
    </div>
  );
}

function analyzeAudioStream(stream, onFeatures) {
  const ctx = new AudioContext();
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 2048;
  const source = ctx.createMediaStreamSource(stream);
  source.connect(analyser);

  const bufferLen = analyser.frequencyBinCount;
  const freqData = new Uint8Array(bufferLen);
  const timeData = new Uint8Array(analyser.fftSize);

  const volumeSamples = [];
  const pitchSamples = [];

  const interval = setInterval(() => {
    analyser.getByteFrequencyData(freqData);
    analyser.getByteTimeDomainData(timeData);

    const rms = Math.sqrt(freqData.reduce((sum, v) => sum + v * v, 0) / freqData.length);
    volumeSamples.push(rms);

    const totalPower = freqData.reduce((s, v) => s + v, 0) + 0.001;
    const centroid = freqData.reduce((s, v, i) => s + v * i, 0) / totalPower;
    pitchSamples.push(centroid);
  }, 80);

  const stop = () => {
    clearInterval(interval);
    ctx.close();

    if (volumeSamples.length < 2) return null;

    // Filter samples to exclude silent/low-volume frames (noise floor)
    const voiceSamples = volumeSamples.filter(v => v > 12.0);
    const activeVolumeSamples = voiceSamples.length >= 2 ? voiceSamples : volumeSamples;

    // For pitch, we only look at frames where voice is active
    const activePitchSamples = [];
    for (let i = 0; i < volumeSamples.length; i++) {
      if (volumeSamples[i] > 12.0) {
        activePitchSamples.push(pitchSamples[i]);
      }
    }
    if (activePitchSamples.length < 2) {
      activePitchSamples.push(...pitchSamples);
    }

    const avgVol = activeVolumeSamples.reduce((a, b) => a + b, 0) / activeVolumeSamples.length;
    const volVariance =
      activeVolumeSamples.reduce((s, v) => s + Math.pow(v - avgVol, 2), 0) / activeVolumeSamples.length;
    const volStdDev = Math.sqrt(volVariance);

    const avgPitch = activePitchSamples.reduce((a, b) => a + b, 0) / activePitchSamples.length;
    const pitchVariance =
      activePitchSamples.reduce((s, v) => s + Math.pow(v - avgPitch, 2), 0) / activePitchSamples.length;
    const pitchStdDev = Math.sqrt(pitchVariance);

    const loudness = avgVol / 255;
    const jitter = pitchStdDev / Math.max(1, avgPitch);

    const isTrembling = volStdDev > 18;
    const isSinging = pitchStdDev > 30 && avgVol > 40;
    const isCrying = volStdDev > 15 && pitchStdDev > 20 && avgVol > 20;
    const isWhispering = avgVol < 15;
    const isShakingVoice = volStdDev > 25;

    let voiceDescription = [];
    if (isSinging) voiceDescription.push("melodic/singing voice pattern with wide pitch variation");
    if (isCrying) voiceDescription.push("crying or tearful — irregular volume with unstable pitch");
    if (isTrembling) voiceDescription.push("trembling or shaking voice — high amplitude instability");
    if (isWhispering) voiceDescription.push("very quiet, almost whispering");
    if (isShakingVoice) voiceDescription.push("severely unstable voice suggesting strong emotion");
    if (voiceDescription.length === 0) voiceDescription.push("stable and composed voice");

    const features = {
      pitch_mean: parseFloat((avgPitch * 0.5).toFixed(2)),
      jitter: parseFloat(jitter.toFixed(4)),
      loudness: parseFloat(loudness.toFixed(4)),
      volume_std_dev: parseFloat(volStdDev.toFixed(2)),
      pitch_std_dev: parseFloat(pitchStdDev.toFixed(2)),
      is_trembling: isTrembling,
      is_singing: isSinging,
      is_crying: isCrying,
      is_whispering: isWhispering,
      voice_description: voiceDescription.join("; "),
      source: "browser_web_audio_api",
    };

    onFeatures(features);
    return features;
  };

  return stop;
}

function summarizeVideoTimeline(history: any[] = [], fallback: any = {}) {
  const samples: any[] = Array.isArray(history) ? history : [];
  const emotionCounts: Record<string, number> = {};
  const confidenceTotals: Record<string, number> = {};
  const faceQualities: number[] = [];
  const eyeContactSamples: boolean[] = [];
  const headPoseTotals = { pitch: 0, yaw: 0, roll: 0, count: 0 };
  const actionUnitTotals: Record<string, { total: number; count: number }> = {};
  let firstTs: number | null = null;
  let lastTs: number | null = null;

  samples.forEach((sample) => {
    if (!sample) return;
    const emotion = sample.emotion || "neutral";
    const confidence = Number(sample.confidence || 0);
    emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
    confidenceTotals[emotion] = (confidenceTotals[emotion] || 0) + confidence;

    if (typeof sample.face_quality === "number") faceQualities.push(sample.face_quality);
    if (typeof sample.eye_contact === "boolean") eyeContactSamples.push(sample.eye_contact);
    if (sample.head_pose) {
      headPoseTotals.pitch += Number(sample.head_pose.pitch || 0);
      headPoseTotals.yaw += Number(sample.head_pose.yaw || 0);
      headPoseTotals.roll += Number(sample.head_pose.roll || 0);
      headPoseTotals.count += 1;
    }
    if (sample.action_units) {
      Object.entries(sample.action_units).forEach(([key, value]) => {
        if (!actionUnitTotals[key]) actionUnitTotals[key] = { total: 0, count: 0 };
        actionUnitTotals[key].total += Number(value || 0);
        actionUnitTotals[key].count += 1;
      });
    }
    if (!firstTs || sample.timestamp < firstTs) firstTs = sample.timestamp;
    if (!lastTs || sample.timestamp > lastTs) lastTs = sample.timestamp;
  });

  const dominantEmotion =
    Object.entries(emotionCounts).sort((a, b) => Number(b[1]) - Number(a[1]))[0]?.[0] ||
    fallback.emotion ||
    "neutral";
  const dominantCount = emotionCounts[dominantEmotion] || 0;
  const averageConfidence =
    dominantCount > 0
      ? confidenceTotals[dominantEmotion] / dominantCount
      : Number(fallback.confidence || 0);
  const avg = (values: number[]) =>
    values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
  const timeline =
    samples.length <= 24
      ? samples
      : samples.filter((_, index) => index % Math.ceil(samples.length / 24) === 0).slice(0, 24);

  const actionUnits: Record<string, number> = {};
  Object.entries(actionUnitTotals).forEach(([key, stats]) => {
    actionUnits[key] = Number((stats.total / Math.max(1, stats.count)).toFixed(3));
  });

  return {
    emotion: dominantEmotion,
    confidence: Number(averageConfidence.toFixed(3)),
    sample_count: samples.length,
    duration_ms: firstTs && lastTs ? lastTs - firstTs : 0,
    emotion_distribution: emotionCounts,
    face_quality: Number((avg(faceQualities) ?? fallback.face_quality ?? 0).toFixed(3)),
    action_units: actionUnits,
    eye_contact_ratio:
      eyeContactSamples.length > 0
        ? Number((eyeContactSamples.filter(Boolean).length / eyeContactSamples.length).toFixed(3))
        : fallback.eye_contact_ratio ?? 1.0,
    head_pose:
      headPoseTotals.count > 0
        ? {
            pitch: Number((headPoseTotals.pitch / headPoseTotals.count).toFixed(2)),
            yaw: Number((headPoseTotals.yaw / headPoseTotals.count).toFixed(2)),
            roll: Number((headPoseTotals.roll / headPoseTotals.count).toFixed(2)),
          }
        : fallback.head_pose || { pitch: 0, yaw: 0, roll: 0 },
    timeline: timeline.map((sample) => ({
      emotion: sample.emotion,
      confidence: sample.confidence,
      timestamp: sample.timestamp,
      face_quality: sample.face_quality,
      eye_contact: sample.eye_contact,
      head_pose: sample.head_pose,
    })),
  };
}

export default function VoiceAssistant() {
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const stopAudioAnalysisRef = useRef(null);
  const audioFeaturesRef = useRef(null);
  const recordingStartedAtRef = useRef<number | null>(null);

  // Video Ref & Canvas Ref
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Voice assistant state
  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [emotionData, setEmotionData] = useState<Emotion | null>(null);
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [requests, setRequests] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState("Rachel");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [sessionGreeting, setSessionGreeting] = useState(null);
  const [memoriesUsed, setMemoriesUsed] = useState(0);
  // RL state — tracks last action vector and policy for FeedbackWidget
  const [lastInteractionId, setLastInteractionId] = useState<string | null>(null);
  const [lastRLAction, setLastRLAction] = useState<RLAction | null>(null);
  const [lastRLPolicy, setLastRLPolicy] = useState<PolicyName | null>(null);
  const sessionStartTimeRef = useRef<number>(Date.now());

  // Client-side Video Emotion Store
  const {
    videoEmotion,
    fusedEmotion,
    trackingStatus,
    faceQuality,
    fps: videoFps,
    cameraActive,
    reset: resetEmotionStore,
    isCalibrating,
    calibrationProgress,
    neutralBaseline,
    startCalibration,
    cancelCalibration,
    eyeContact,
    headPose,
    clearEyeContactHistory,
    clearExpressionHistory,
  } = useEmotionStore();

  // Consent local storage state
  const [hasCameraConsent, setHasCameraConsent] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("camera_consent") === "true";
    }
    return false;
  });
  const [videoCaptureEnabled, setVideoCaptureEnabled] = useState(hasCameraConsent);

  // Offline Grounding States
  const [isOnline, setIsOnline] = useState(() => {
    if (typeof window !== "undefined") {
      return navigator.onLine;
    }
    return true;
  });
  const [showOfflineGrounding, setShowOfflineGrounding] = useState(false);
  const [breathingState, setBreathingState] = useState<'inhale' | 'hold-in' | 'exhale' | 'hold-out'>('inhale');
  const [breathingTimer, setBreathingTimer] = useState(4);

  // Activate the real-time hook
  useVideoEmotionDetection(videoRef, canvasRef, hasCameraConsent && videoCaptureEnabled);

  const voices = [
    { name: "Amelia", gender: "female", icon: "👩‍💼" },
    { name: "Rachel", gender: "female", icon: "👩" },
    { name: "Josh", gender: "male", icon: "🧔" },
    { name: "Nathan", gender: "male", icon: "👨" },
    { name: "Sam", gender: "male", icon: "🧑" },
  ];

  useEffect(() => {
    const usage = getUsageData();
    setRequests(usage.requests || 0);

    const fetchGreeting = async () => {
      try {
        const res = await startSession();
        if (res.greeting) {
          setSessionGreeting(res.greeting);
        }
      } catch (err: any) {
        console.warn("Session greeting unavailable:", err.error || err.message);
      }
    };
    fetchGreeting();

    return () => {
      resetEmotionStore();
    };
  }, [resetEmotionStore]);

  // Service Worker Registration
  useEffect(() => {
    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js")
        .then((reg) => console.log("Service Worker registered scope:", reg.scope))
        .catch((err) => console.error("Service Worker registration failed:", err));
    }
  }, []);

  // Online / Offline Connectivity Event Listeners
  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleOnline = () => {
      setIsOnline(true);
      setError("");
    };
    const handleOffline = () => {
      setIsOnline(false);
      setError("Network connection is offline. Running in local offline mode.");
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    // Sync current online status
    setIsOnline(navigator.onLine);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Breathing ground timer loop & Soothing audio guidelines
  useEffect(() => {
    if (!showOfflineGrounding) {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      return;
    }

    // Set initial timer & state on enter
    setBreathingTimer(4);
    setBreathingState("inhale");

    // Soothing voice TTS helper
    const speakGrounding = (text: string) => {
      if (typeof window === "undefined" || !window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const voicesList = window.speechSynthesis.getVoices();
      const femaleVoice = voicesList.find(
        (v) =>
          v.name.toLowerCase().includes("samantha") ||
          v.name.toLowerCase().includes("karen") ||
          v.name.toLowerCase().includes("victoria") ||
          v.name.toLowerCase().includes("zira") ||
          v.name.toLowerCase().includes("female") ||
          (v.lang.startsWith("en") && v.name.toLowerCase().includes("google"))
      );
      if (femaleVoice) {
        utterance.voice = femaleVoice;
      }
      utterance.rate = 0.82;
      utterance.pitch = 1.05;
      utterance.volume = 1.0;
      window.speechSynthesis.speak(utterance);
    };

    const phaseVoices: Record<typeof breathingState, string> = {
      'inhale': "Inhale slowly and fill your lungs.",
      'hold-in': "Hold your breath. Keep your mind calm.",
      'exhale': "Exhale slowly. Let go of all tension.",
      'hold-out': "Hold, and rest in this peaceful moment."
    };
    
    speakGrounding(phaseVoices[breathingState]);

    const interval = setInterval(() => {
      setBreathingTimer((prev) => {
        if (prev <= 1) {
          setBreathingState((currState) => {
            const nextState: Record<typeof breathingState, typeof breathingState> = {
              'inhale': 'hold-in',
              'hold-in': 'exhale',
              'exhale': 'hold-out',
              'hold-out': 'inhale',
            };
            return nextState[currState];
          });
          return 4;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      clearInterval(interval);
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [showOfflineGrounding, breathingState]);

  const previewVoice = async () => {
    setPreviewLoading(true);
    try {
      const res = await previewVoiceApi(selectedVoice);
      if (res.audio_url) {
        const audio = new Audio(res.audio_url);
        audio.play();
      }
    } catch (err) {
      console.error("Preview failed", err);
    }
    setPreviewLoading(false);
  };

  const speakResponse = (text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const voicesList = window.speechSynthesis.getVoices();
    const femaleVoice = voicesList.find(
      (v) =>
        v.name.toLowerCase().includes("samantha") ||
        v.name.toLowerCase().includes("karen") ||
        v.name.toLowerCase().includes("victoria") ||
        v.name.toLowerCase().includes("zira") ||
        v.name.toLowerCase().includes("female") ||
        (v.lang.startsWith("en") && v.name.toLowerCase().includes("google"))
    );
    if (femaleVoice) utterance.voice = femaleVoice;
    utterance.rate = 0.92;
    utterance.pitch = 1.1;
    utterance.volume = 1.0;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  };

  const startRecording = async () => {
    if (!isOnline) {
      setError("Network connection is offline. Launching local box-breathing grounding mode.");
      setShowOfflineGrounding(true);
      return;
    }
    if (!hasCameraConsent) {
      setError("Turn on camera consent first so NeuroNest can assess audio and facial expression together.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      audioFeaturesRef.current = null;

      // Update voice store to notify fusion of recording
      const { setAudioFeatures, setIsRecording } = useVoiceStore.getState();
      setIsRecording(true);
      clearEyeContactHistory();
      clearExpressionHistory();
      recordingStartedAtRef.current = Date.now();

      stopAudioAnalysisRef.current = analyzeAudioStream(stream, (features) => {
        audioFeaturesRef.current = features;
        setAudioFeatures(features);
      });

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        if (stopAudioAnalysisRef.current) {
          stopAudioAnalysisRef.current();
          stopAudioAnalysisRef.current = null;
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const audioFile = new File([audioBlob], "recording.webm", { type: "audio/webm" });

        setLoading(true);
        setError("");

        // Collect local video analysis across the active recording window.
        const latestVideoEmotion = useEmotionStore.getState().videoEmotion;
        const latestFusedEmotion = useEmotionStore.getState().fusedEmotion;
        const latestFaceQuality = useEmotionStore.getState().faceQuality;
        const latestCameraActive = useEmotionStore.getState().cameraActive;
        const expressionHistory = useEmotionStore.getState().expressionHistory || [];

        // Calculate eye contact ratio
        const history = useEmotionStore.getState().eyeContactHistory;
        const eyeContactRatio = history.length > 0 ? history.filter(Boolean).length / history.length : 1.0;
        const latestHeadPose = useEmotionStore.getState().headPose;
        const videoSummary = summarizeVideoTimeline(expressionHistory, {
          emotion: latestVideoEmotion?.emotion || "neutral",
          confidence: latestVideoEmotion?.confidence || 0,
          face_quality: latestFaceQuality,
          eye_contact_ratio: parseFloat(eyeContactRatio.toFixed(3)),
          head_pose: latestHeadPose,
        });

        const videoAnalysisPayload = latestCameraActive
          ? JSON.stringify({
              ...videoSummary,
              latest_emotion: latestVideoEmotion,
              fused_emotion: latestFusedEmotion,
              is_masked: latestFusedEmotion?.isMasked || false,
              mask_confidence: latestFusedEmotion?.maskConfidence || 0,
              recording_started_at: recordingStartedAtRef.current,
              recording_stopped_at: Date.now(),
            })
          : undefined;

        // Clear voice store features
        setAudioFeatures(null);
        setIsRecording(false);

        try {
          const res = await processVoice({
            file: audioFile,
            audio_analysis: audioFeaturesRef.current
              ? JSON.stringify(audioFeaturesRef.current)
              : undefined,
            video_analysis: videoAnalysisPayload,
            expression_history: expressionHistory.length > 0 ? expressionHistory : undefined,
            voice_name: selectedVoice,
          });

          setTranscript(res.transcript);
          setEmotionData(res.emotion);
          setResponse(res.response);
          setMemoriesUsed(res.memories_used || 0);

          // Capture RL metadata for FeedbackWidget
          const rlRes = res as any;
          if (rlRes.interaction_id) setLastInteractionId(rlRes.interaction_id);
          if (rlRes.applied_action)  setLastRLAction(rlRes.applied_action);
          if (rlRes.applied_policy)  setLastRLPolicy(rlRes.applied_policy);

          const updated = incrementUsage();
          setRequests(updated.requests);

          // Update conversation context store with response emotion
          useConversationStore.getState().setEmotion(res.emotion);

          if (res.audio_url) {
            const audio = new Audio(res.audio_url);
            audio.onplay = () => setIsSpeaking(true);
            audio.onended = () => setIsSpeaking(false);
            audio.onerror = () => speakResponse(res.response);
            audio.play().catch(() => speakResponse(res.response));
          } else {
            speakResponse(res.response);
          }
        } catch (err: any) {
          console.error(err);
          const errMsg = err.error || err.message || "";
          const isNetworkError =
            !isOnline ||
            errMsg.toLowerCase().includes("network") ||
            errMsg.toLowerCase().includes("timeout") ||
            errMsg.toLowerCase().includes("conn") ||
            errMsg.toLowerCase().includes("failed to fetch");

          if (isNetworkError) {
            setError("Connection offline. Activating local offline grounding mode.");
            setShowOfflineGrounding(true);
          } else {
            setError(errMsg || "Failed to process voice. Is the backend running?");
          }
        }

        setLoading(false);
      };

      mediaRecorder.start(250);
      setRecording(true);
    } catch (err) {
      setError("Microphone access denied. Please allow microphone access and try again.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setRecording(false);
  };

  const emotion = emotionData?.emotion || "";
  const contradiction = emotionData?.contradiction_detected;
  const hiddenEmotion = emotionData?.hidden_emotion;

  // Determine glow outline based on current fused emotion
  const getFusedGlow = () => {
    if (!hasCameraConsent || !fusedEmotion) return "border-slate-200";
    switch (fusedEmotion.emotion.toLowerCase()) {
      case "happy":
        return "border-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.3)]";
      case "sad":
        return "border-blue-400 shadow-[0_0_20px_rgba(59,130,246,0.3)]";
      case "angry":
        return "border-red-400 shadow-[0_0_20px_rgba(239,68,68,0.3)]";
      case "fearful":
      case "anxious":
        return "border-amber-400 shadow-[0_0_20px_rgba(245,158,11,0.3)]";
      default:
        return "border-indigo-400 shadow-[0_0_20px_rgba(129,140,248,0.25)]";
    }
  };

  const auLabels: Record<string, string> = {
    AU1: "Brow Raiser (Inner)",
    AU4: "Brow Furrower (Tension)",
    AU6: "Cheek Raiser (Squint)",
    AU12: "Lip Corner Puller (Smile)",
    AU15: "Lip Corner Depressor (Frown)",
    AU25: "Mouth Part (Speech)",
  };

  // Determine bubble scale dynamically based on box-breathing state
  const getBubbleScale = () => {
    switch (breathingState) {
      case "inhale":
        return 1.45;
      case "hold-in":
        return 1.48; // slight expansion hold
      case "exhale":
        return 0.95;
      case "hold-out":
        return 0.92; // slight compression hold
      default:
        return 1.0;
    }
  };

  // Determine bubble gradient style dynamically based on box-breathing state
  const getBubbleGradient = () => {
    switch (breathingState) {
      case "inhale":
        return "from-emerald-400 via-teal-500 to-indigo-500 shadow-[0_0_50px_rgba(16,185,129,0.4)]";
      case "hold-in":
        return "from-violet-500 via-purple-500 to-pink-500 shadow-[0_0_50px_rgba(168,85,247,0.4)]";
      case "exhale":
        return "from-sky-400 via-blue-500 to-indigo-600 shadow-[0_0_50px_rgba(59,130,246,0.4)]";
      case "hold-out":
        return "from-slate-400 via-slate-500 to-slate-600 shadow-[0_0_50px_rgba(100,116,139,0.3)]";
      default:
        return "from-indigo-500 to-purple-600 shadow-[0_0_40px_rgba(99,102,241,0.3)]";
    }
  };

  return (
    <div className="w-full max-w-6xl flex flex-col lg:flex-row gap-6 items-stretch justify-center relative px-4">
      {/* COLUMN 1: Speech interface & response (NeuroNest Voice Assistant) */}
      <div className="w-full lg:w-3/5 relative flex flex-col">
        <div className="absolute -inset-1 bg-gradient-to-r from-indigo-300 via-purple-300 to-pink-300 rounded-[2.5rem] blur opacity-40"></div>

        <div className="flex-1 relative bg-white/70 backdrop-blur-2xl rounded-3xl p-6 sm:p-8 shadow-2xl border border-white/50 overflow-hidden flex flex-col justify-between">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>

          {showOfflineGrounding ? (
            <div className="relative z-10 flex flex-col flex-1 justify-between h-full min-h-[500px]">
              {/* Header */}
              <div className="flex items-center justify-between pb-4 border-b border-indigo-100/50">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 animate-pulse">
                    <WifiOff className="w-5 h-5" />
                  </div>
                  <div className="text-left">
                    <h2 className="text-lg font-bold text-slate-800 flex items-center gap-1.5">
                      Offline Care Mode
                    </h2>
                    <p className="text-xs text-amber-600 font-medium">Box-Breathing Grounding Active</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowOfflineGrounding(false)}
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100/80 rounded-xl transition-all"
                  title="Return to assistant"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Main breathing exercise area */}
              <div className="flex flex-col items-center justify-center py-8 flex-1">
                {/* Visual breathing bubble container */}
                <div className="relative w-72 h-72 flex items-center justify-center">
                  {/* Concentric ambient breathing rings */}
                  <div 
                    className={`absolute inset-0 rounded-full bg-gradient-to-br ${getBubbleGradient()} opacity-10 transition-all duration-[4000ms] ease-in-out`}
                    style={{ transform: `scale(${getBubbleScale() * 1.3})` }}
                  />
                  <div 
                    className={`absolute inset-0 rounded-full bg-gradient-to-br ${getBubbleGradient()} opacity-20 transition-all duration-[4000ms] ease-in-out`}
                    style={{ transform: `scale(${getBubbleScale() * 1.15})` }}
                  />
                  
                  {/* Central bubble */}
                  <div
                    className={`w-48 h-48 rounded-full bg-gradient-to-br ${getBubbleGradient()} flex flex-col items-center justify-center transition-transform duration-[4000ms] ease-in-out relative border-4 border-white/30 text-white select-none`}
                    style={{ transform: `scale(${getBubbleScale()})` }}
                  >
                    <div className="text-center">
                      <Wind className="w-8 h-8 mx-auto mb-1 animate-pulse opacity-80" />
                      <span className="block text-2xl font-extrabold capitalize tracking-wider drop-shadow-md">
                        {breathingState === 'hold-in' || breathingState === 'hold-out' ? 'Hold' : breathingState}
                      </span>
                      <span className="block text-4xl font-black mt-1 drop-shadow-md">
                        {breathingTimer}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Grounding instruction subtitle */}
                <div className="mt-8 text-center px-4 max-w-md">
                  <p className="text-lg font-bold text-slate-700 transition-all duration-300 min-h-[28px]">
                    {breathingState === 'inhale' && "Inhale slowly and fill your lungs."}
                    {breathingState === 'hold-in' && "Hold your breath. Keep your mind calm."}
                    {breathingState === 'exhale' && "Exhale slowly. Let go of all tension."}
                    {breathingState === 'hold-out' && "Hold, and rest in this peaceful moment."}
                  </p>
                  <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                    Box breathing regulates the autonomic nervous system, lowering heart rate and centering your attention.
                  </p>
                </div>
              </div>

              {/* Control Actions & voice info */}
              <div className="pt-6 border-t border-indigo-100/50 flex flex-col sm:flex-row gap-4 items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                  <Volume2 className="w-4 h-4 text-indigo-500" />
                  <span>Soothing Audio Guide: <strong className="text-slate-700">Active (Samantha/Karen)</strong></span>
                </div>
                
                <div className="flex items-center gap-3">
                  <button
                    onClick={startCalibration}
                    disabled={trackingStatus !== "tracking" || isCalibrating}
                    className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider rounded-xl transition-all shadow-sm flex items-center gap-1.5
                      ${trackingStatus !== "tracking" || isCalibrating
                        ? "bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200"
                        : "bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 hover:scale-105 active:scale-95"
                      }`}
                  >
                    Recalibrate Camera
                  </button>
                  <button
                    onClick={() => setShowOfflineGrounding(false)}
                    className="px-5 py-2.5 bg-gradient-to-b from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition-all shadow-md hover:scale-105 active:scale-95"
                  >
                    End Grounding
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <>
              <div>
                <div className="text-center mb-6 relative z-10">
                  <div className="inline-flex items-center justify-center p-3 bg-indigo-50 rounded-2xl mb-4 border border-indigo-100 shadow-sm">
                    <BrainCircuit className="text-indigo-600 w-8 h-8" />
                  </div>
                  <h1 className="text-3xl sm:text-4xl font-extrabold mb-2 tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-700 via-purple-700 to-indigo-700">
                    NeuroNest AI
                  </h1>
                  <p className="text-indigo-900/60 font-medium text-sm flex items-center justify-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-pink-500" />
                    Empathetic companion listening for you
                    <Sparkles className="w-3.5 h-3.5 text-pink-500" />
                  </p>
                </div>

                {!isOnline && (
                  <div className="relative z-10 mb-6 animate-fade-in">
                    <div className="flex items-center justify-between bg-amber-50 border border-amber-200 rounded-2xl p-4 shadow-sm">
                      <div className="flex items-center gap-3">
                        <WifiOff className="w-5 h-5 text-amber-500 animate-pulse" />
                        <div className="text-left">
                          <p className="text-xs font-bold text-amber-800">Running Offline</p>
                          <p className="text-[10px] text-amber-600 font-medium leading-tight">Local camera tracking is active. Microphone interactions will trigger box breathing.</p>
                        </div>
                      </div>
                      <button
                        onClick={() => setShowOfflineGrounding(true)}
                        className="flex-shrink-0 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white font-extrabold text-[10px] uppercase tracking-wider rounded-xl transition-all shadow-sm active:scale-95"
                      >
                        Start Breathing
                      </button>
                    </div>
                  </div>
                )}

                <CreditsBar requests={requests} />

                {sessionGreeting && (
                  <div className="relative z-10 mb-6 animate-fade-in">
                    <div className="flex items-start gap-3 bg-gradient-to-br from-violet-50 to-indigo-50 border border-violet-200/70 rounded-2xl p-4 shadow-sm">
                      <div className="flex-shrink-0 w-9 h-9 bg-gradient-to-br from-violet-500 to-indigo-500 rounded-xl flex items-center justify-center shadow-sm mt-0.5">
                        <Brain className="w-4 h-4 text-white" />
                      </div>
                      <div className="flex-1">
                        <p className="text-[10px] font-bold uppercase tracking-widest text-violet-400 mb-1">
                          NeuroNest remembers
                        </p>
                        <p className="text-slate-700 text-sm leading-relaxed">{sessionGreeting}</p>
                      </div>
                      <button
                        onClick={() => setSessionGreeting(null)}
                        className="flex-shrink-0 text-slate-300 hover:text-slate-500 transition-colors text-lg leading-none mt-0.5"
                        title="Dismiss"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                )}

                <div className="relative z-10 mb-6 bg-indigo-50/50 p-4 rounded-2xl border border-indigo-100/50">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex-1">
                      <label className="block text-[10px] font-bold uppercase tracking-wider text-indigo-400 mb-1.5 ml-1">
                        Choose AI Voice Model
                      </label>
                      <div className="relative">
                        <select
                          value={selectedVoice}
                          onChange={(e) => setSelectedVoice(e.target.value)}
                          className="w-full bg-white border border-indigo-200 text-indigo-900 text-sm rounded-xl focus:ring-indigo-500 focus:border-indigo-500 block p-3 shadow-sm appearance-none cursor-pointer hover:border-indigo-300 transition-colors"
                        >
                          {voices.map((v) => (
                            <option key={v.name} value={v.name}>
                              {v.icon} {v.name} ({v.gender})
                            </option>
                          ))}
                        </select>
                        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-indigo-400">
                          <Zap size={14} />
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={previewVoice}
                      disabled={previewLoading}
                      className={`mt-5 px-5 py-3 rounded-xl font-bold text-xs uppercase tracking-widest transition-all flex items-center gap-2 shadow-sm
                        ${
                          previewLoading
                            ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                            : "bg-white text-indigo-600 border border-indigo-100 hover:bg-indigo-50 hover:scale-105 active:scale-95"
                        }`}
                    >
                      {previewLoading ? (
                        <Activity className="w-3 h-3 animate-spin" />
                      ) : (
                        <Sparkles className="w-3 h-3" />
                      )}
                      Preview
                    </button>
                  </div>
                </div>

                <div className="flex justify-center mb-4 relative z-10">
                  <div className="relative">
                    {recording && (
                      <div className="absolute -inset-4 bg-red-400/30 rounded-full blur-xl animate-pulse"></div>
                    )}
                    {!recording ? (
                      <button
                        onClick={startRecording}
                        className="relative bg-gradient-to-b from-indigo-500 to-indigo-600 hover:from-indigo-400 hover:to-indigo-500 p-8 rounded-full transition-all duration-300 shadow-[0_10px_40px_rgba(99,102,241,0.3)] hover:shadow-[0_10px_60px_rgba(99,102,241,0.5)] hover:scale-105"
                      >
                        <Mic size={40} className="text-white drop-shadow-sm" />
                      </button>
                    ) : (
                      <button
                        onClick={stopRecording}
                        className="relative bg-gradient-to-b from-red-500 to-rose-600 hover:from-red-400 hover:to-rose-500 p-8 rounded-full transition-all duration-300 shadow-[0_10px_40px_rgba(239,68,68,0.4)] animate-pulse"
                      >
                        <Square size={40} className="text-white fill-white drop-shadow-sm" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="text-center mb-6 text-sm text-indigo-400 font-medium">
                  {recording
                    ? "🔴 Recording — speak freely, then click stop"
                    : "🎙️ Click mic to start conversing"}
                </div>

                {loading && (
                  <div className="flex flex-col items-center justify-center text-indigo-600 mb-8 space-y-4 animate-pulse">
                    <Activity className="w-8 h-8 text-indigo-500" />
                    <span className="font-medium tracking-wide">
                      Fusing voice, transcript, and facial micro-expressions...
                    </span>
                  </div>
                )}

                {isSpeaking && !loading && (
                  <div className="flex flex-col items-center justify-center mb-6 space-y-3">
                    <div className="flex items-end gap-1 h-8">
                      {[0.4, 0.7, 1.0, 0.8, 0.6, 0.9, 0.5].map((h, i) => (
                        <div
                          key={i}
                          className="w-1.5 bg-gradient-to-t from-indigo-500 to-purple-400 rounded-full animate-pulse"
                          style={{ height: `${h * 100}%`, animationDelay: `${i * 0.12}s` }}
                        />
                      ))}
                    </div>
                    <span className="text-sm font-medium text-indigo-600 tracking-wide">
                      NeuroNest is speaking...
                    </span>
                  </div>
                )}

                {error && (
                  <div className="bg-red-50/80 p-4 rounded-xl border border-red-200 text-center mb-6">
                    <p className="text-red-600 font-medium">{error}</p>
                  </div>
                )}
              </div>

              {transcript && !loading && (
                <div className="space-y-4 mt-4 relative z-10">
                  <div className="bg-white/80 backdrop-blur-md p-5 rounded-2xl border border-indigo-50 shadow-sm hover:shadow-md transition-all">
                    <h2 className="text-xs font-bold uppercase tracking-wider mb-2 text-indigo-600 flex items-center gap-2">
                      <Mic className="w-3.5 h-3.5" /> Transcript
                    </h2>
                    <p className="text-slate-700 leading-relaxed text-md">{transcript}</p>
                  </div>

                  <div className="bg-white/80 backdrop-blur-md p-5 rounded-2xl border border-pink-100 shadow-sm hover:shadow-md transition-all">
                    <h2 className="text-xs font-bold uppercase tracking-wider mb-2 text-pink-600 flex items-center gap-2">
                      <HeartPulse className="w-3.5 h-3.5" /> Fused Emotional Response
                    </h2>
                    <div className="flex flex-wrap gap-3 items-center">
                      <div className="inline-block bg-pink-50 px-3.5 py-1.5 rounded-xl border border-pink-200">
                        <p className="capitalize text-pink-600 font-semibold text-md tracking-wide">
                          {emotion}
                        </p>
                      </div>
                      {emotionData?.stress_level !== undefined && (
                        <div className="text-xs text-slate-500 font-medium">
                          Stress Level:{" "}
                          <span className="font-semibold text-slate-700">
                            {emotionData.stress_level}/100
                          </span>
                        </div>
                      )}
                      {emotionData?.tone && (
                        <div className="text-xs text-slate-500 font-medium">
                          Vocal Tone:{" "}
                          <span className="font-semibold text-slate-700 capitalize">
                            {emotionData.tone}
                          </span>
                        </div>
                      )}
                    </div>
                    {contradiction && hiddenEmotion && (
                      <div className="mt-3 p-3 bg-amber-50 border border-amber-200/80 rounded-xl">
                        <p className="text-amber-700 text-xs font-medium flex items-center gap-1.5">
                          <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0" />
                          Emotional contradiction detected. Underlying stress:{" "}
                          <span className="font-bold capitalize">{hiddenEmotion}</span>
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="bg-indigo-50/85 backdrop-blur-md p-5 rounded-2xl border border-indigo-200/80 shadow-sm hover:shadow-md relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-200/40 rounded-full blur-3xl"></div>
                    <div className="flex items-center justify-between mb-2">
                      <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-700 flex items-center gap-2">
                        <BrainCircuit className="w-3.5 h-3.5" /> AI Response
                      </h2>
                      {memoriesUsed > 0 && (
                        <div className="flex items-center gap-1 bg-violet-100 border border-violet-200 px-2.5 py-0.5 rounded-full">
                          <BookOpen className="w-3 h-3 text-violet-500" />
                          <span className="text-[9px] font-bold text-violet-600 uppercase tracking-wide">
                            {memoriesUsed} recall{memoriesUsed === 1 ? "ed" : "s"}
                          </span>
                        </div>
                      )}
                    </div>
                    <p className="text-indigo-950 leading-relaxed text-md relative z-10">{response}</p>
                    {/* ── RL Feedback Widget ─────────────────────────── */}
                    {lastInteractionId && (
                      <FeedbackWidget
                        interactionId={lastInteractionId}
                        sessionStartTime={sessionStartTimeRef.current}
                        appliedAction={lastRLAction}
                        appliedPolicy={lastRLPolicy}
                      />
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* COLUMN 2: Emotion Analysis & Video Feed (Local ML dashboard) */}
      <div className="w-full lg:w-2/5 flex flex-col">
        {!hasCameraConsent ? (
          <PrivacyConsent
            onAccept={() => {
              localStorage.setItem("camera_consent", "true");
              setHasCameraConsent(true);
              setVideoCaptureEnabled(true);
            }}
            onDecline={() => {
              localStorage.setItem("camera_consent", "false");
              setHasCameraConsent(false);
              setVideoCaptureEnabled(false);
            }}
          />
        ) : (
          <div className="relative bg-white/70 backdrop-blur-2xl rounded-3xl p-5 sm:p-6 border border-white/50 shadow-2xl overflow-hidden flex flex-col h-full justify-between">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-400 to-indigo-500"></div>

            {/* Header info */}
            <div className="flex items-center justify-between mb-3 relative z-10">
              <div className="flex items-center gap-2">
                <Camera className="w-5 h-5 text-indigo-600" />
                <h2 className="text-md font-bold text-slate-800">Local Camera Assistant</h2>
              </div>
              <button
                onClick={() => {
                  localStorage.removeItem("camera_consent");
                  setHasCameraConsent(false);
                  setVideoCaptureEnabled(false);
                }}
                className="text-[10px] font-extrabold text-red-500 hover:text-red-700 bg-red-50 border border-red-100 hover:bg-red-100/50 py-1.5 px-3 rounded-lg transition-colors uppercase tracking-wider"
              >
                Disable Camera
              </button>
            </div>

            {/* Calibration Banner / Status */}
            <div className="mb-4 bg-indigo-50/40 border border-indigo-100/60 p-3.5 rounded-2xl flex items-center justify-between gap-4">
              <div className="flex items-center gap-2.5">
                <div className={`p-1.5 rounded-xl ${neutralBaseline ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"}`}>
                  <ShieldCheck size={16} />
                </div>
                <div className="text-left">
                  <h4 className="text-[10px] font-extrabold text-slate-700 uppercase tracking-widest leading-none mb-1">
                    {neutralBaseline ? "Face Calibrated" : "Calibration Recommended"}
                  </h4>
                  <p className="text-[10px] text-slate-400 font-medium leading-none">
                    {neutralBaseline 
                      ? "Custom facial baseline is active." 
                      : "Adjust tracking to your unique facial geometry."}
                  </p>
                </div>
              </div>
              
              <button
                onClick={startCalibration}
                disabled={trackingStatus !== "tracking" || isCalibrating}
                className={`px-3 py-1.5 text-[9px] font-extrabold uppercase tracking-widest rounded-xl transition-all shadow-sm
                  ${trackingStatus !== "tracking" || isCalibrating
                    ? "bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200"
                    : "bg-white hover:bg-indigo-50 text-indigo-600 border border-indigo-100 hover:scale-105 active:scale-95"
                  }`}
              >
                {neutralBaseline ? "Recalibrate" : "Calibrate"}
              </button>
            </div>

            {/* Video container with dynamic glow aura */}
            <div className="relative w-full aspect-video sm:h-[220px] rounded-2xl overflow-hidden border-2 bg-slate-950 transition-all duration-500 ease-in-out flex items-center justify-center mb-4 shadow-inner">
              <div className={`absolute inset-0 border-2 rounded-2xl transition-all duration-500 ${getFusedGlow()}`} />

              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover scale-x-[-1] rounded-2xl"
              />

              <canvas
                ref={canvasRef}
                width={320}
                height={240}
                className="absolute inset-0 w-full h-full pointer-events-none scale-x-[-1] rounded-2xl"
              />

              {/* Calibration wizard overlay */}
              {isCalibrating && (
                <div className="absolute inset-0 bg-indigo-950/80 backdrop-blur-sm flex flex-col items-center justify-center text-center p-4 z-20 animate-fade-in">
                  <Sparkles className="w-8 h-8 text-indigo-400 mb-2 animate-pulse" />
                  <p className="text-sm font-bold text-white uppercase tracking-wider">Calibrating Baseline</p>
                  <p className="text-xs text-indigo-200 mt-1 max-w-[220px] mb-3 leading-relaxed">
                    Keep a relaxed, neutral expression and look at the camera.
                  </p>
                  <div className="w-40 bg-white/20 h-2 rounded-full overflow-hidden border border-white/10 mb-4">
                    <div
                      className="bg-gradient-to-r from-cyan-400 to-indigo-400 h-full rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${calibrationProgress}%` }}
                    />
                  </div>
                  <button
                    onClick={cancelCalibration}
                    className="px-4 py-1.5 bg-white/10 hover:bg-white/20 border border-white/20 rounded-xl text-[10px] text-white font-bold uppercase tracking-wider transition-all"
                  >
                    Cancel
                  </button>
                </div>
              )}

              {/* Status overlays */}
              <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-lg border border-white/10 flex items-center gap-1.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    trackingStatus === "tracking"
                      ? "bg-emerald-500 animate-pulse"
                      : trackingStatus === "loading"
                      ? "bg-indigo-500 animate-ping"
                      : trackingStatus === "no-face"
                      ? "bg-amber-500"
                      : "bg-red-500"
                  }`}
                />
                <span className="text-[10px] font-bold text-white uppercase tracking-wider">
                  {trackingStatus === "tracking"
                    ? "Active Tracking"
                    : trackingStatus === "loading"
                    ? "Loading ML..."
                    : trackingStatus === "no-face"
                    ? "Align Face"
                    : "Inactive"}
                </span>
              </div>

              {trackingStatus === "tracking" && (
                <div className="absolute bottom-3 right-3 bg-black/60 backdrop-blur-md px-2 py-0.5 rounded border border-white/10 text-[9px] font-bold text-slate-300">
                  FPS: {videoFps} | Quality: {(faceQuality * 100).toFixed(0)}%
                </div>
              )}

              {trackingStatus === "no-face" && (
                <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center text-center p-4">
                  <CameraOff className="w-8 h-8 text-amber-500 mb-2 animate-bounce" />
                  <p className="text-sm font-bold text-slate-200">Face Not Found</p>
                  <p className="text-xs text-slate-400 mt-1 max-w-[200px]">
                    Ensure your face is clearly lit and centered in front of the camera.
                  </p>
                </div>
              )}

              {trackingStatus === "loading" && (
                <div className="absolute inset-0 bg-slate-950/90 flex flex-col items-center justify-center text-center p-4">
                  <Activity className="w-8 h-8 text-indigo-500 mb-2 animate-spin" />
                  <p className="text-sm font-bold text-slate-200">Initializing Local TFJS...</p>
                  <p className="text-xs text-slate-400 mt-1 max-w-[220px]">
                    Loading models inside your browser. No files are uploaded.
                  </p>
                </div>
              )}
            </div>

            {/* Action Units visualizer */}
            {trackingStatus === "tracking" && videoEmotion && (
              <div className="bg-slate-50/50 border border-slate-100 rounded-2xl p-4 mb-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center justify-between">
                  <span>Facial Micro-Expressions (FACS)</span>
                  <span className="text-[10px] text-indigo-500">Local computation</span>
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2">
                  {Object.entries(videoEmotion.actionUnits).map(([au, val]) => (
                    <div key={au} className="flex flex-col">
                      <div className="flex justify-between text-[10px] font-semibold text-slate-600 mb-0.5">
                        <span>{auLabels[au] || au}</span>
                        <span>{(val * 100).toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-slate-200/60 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-indigo-500 to-violet-500 h-full rounded-full transition-all duration-300 ease-out"
                          style={{ width: `${val * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Attention Tracking Panel */}
            {trackingStatus === "tracking" && (
              <div className="bg-slate-50/50 border border-slate-100 rounded-2xl p-4 mb-4 backdrop-blur-md">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center justify-between">
                  <span>Visual Attention & Gaze</span>
                  <span className="text-[10px] text-indigo-500">Live Telemetry</span>
                </h3>

                <div className="flex flex-col sm:flex-row gap-4 items-center">
                  {/* Gaze/Headpose radar */}
                  <div className="relative w-28 h-28 rounded-full bg-slate-950/95 border-2 border-slate-800 flex items-center justify-center overflow-hidden shadow-inner flex-shrink-0">
                    {/* Grid lines */}
                    <div className="absolute inset-x-0 h-0.5 bg-slate-800/40" />
                    <div className="absolute inset-y-0 w-0.5 bg-slate-800/40" />
                    <div className="absolute w-20 h-20 rounded-full border border-slate-800/40" />
                    <div className="absolute w-10 h-10 rounded-full border border-slate-800/40" />
                    
                    {/* Radar Sweep Animation */}
                    <div className="absolute inset-0 bg-[conic-gradient(from_0deg,transparent_50%,rgba(99,102,241,0.15))] rounded-full animate-[spin_4s_linear_infinite] pointer-events-none" />

                    {/* Target Dot */}
                    <div
                      className="absolute w-3.5 h-3.5 rounded-full bg-indigo-500 border-2 border-white shadow-[0_0_10px_#6366f1] transition-all duration-200 ease-out flex items-center justify-center"
                      style={{
                        left: `calc(${Math.max(5, Math.min(95, 50 + (headPose?.yaw || 0)))}% - 7px)`,
                        top: `calc(${Math.max(5, Math.min(95, 50 + (headPose?.pitch || 0)))}% - 7px)`,
                      }}
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
                    </div>
                  </div>

                  {/* Status & Indicators */}
                  <div className="flex-1 w-full space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-500 font-medium">Eye Contact:</span>
                      {eyeContact ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-200/80 px-2.5 py-1 rounded-xl shadow-sm animate-pulse">
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                          Focused Connection
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-600 bg-amber-50 border border-amber-200/80 px-2.5 py-1 rounded-xl shadow-sm">
                          <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping" />
                          Averted Gaze
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="bg-white/80 border border-slate-100 rounded-xl p-1.5 shadow-sm">
                        <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Pitch</div>
                        <div className="text-xs font-extrabold text-slate-700">{headPose?.pitch || 0}°</div>
                      </div>
                      <div className="bg-white/80 border border-slate-100 rounded-xl p-1.5 shadow-sm">
                        <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Yaw</div>
                        <div className="text-xs font-extrabold text-slate-700">{headPose?.yaw || 0}°</div>
                      </div>
                      <div className="bg-white/80 border border-slate-100 rounded-xl p-1.5 shadow-sm">
                        <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Roll</div>
                        <div className="text-xs font-extrabold text-slate-700">{headPose?.roll || 0}°</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Fused real-time feedback */}
            {hasCameraConsent && fusedEmotion && (
              <div className="bg-gradient-to-br from-indigo-50/50 to-violet-50/50 border border-indigo-100/50 rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <HeartPulse className="w-4 h-4 text-indigo-600" />
                  <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider">
                    Client Multimodal Analysis
                  </h4>
                </div>

                <div className="flex items-center gap-2.5 mb-2.5">
                  <span className="text-xs text-slate-500 font-medium">Real-Time Emotion:</span>
                  <span className="capitalize text-slate-800 font-extrabold text-sm flex items-center gap-1.5">
                    {fusedEmotion.emotion}
                    <span className="text-[10px] font-bold text-indigo-500 bg-indigo-50 border border-indigo-100 px-1.5 py-0.5 rounded-md">
                      {(fusedEmotion.confidence * 100).toFixed(0)}% accuracy
                    </span>
                  </span>
                </div>

                {fusedEmotion.isMasked && (
                  <div className="bg-amber-50/80 border border-amber-200/80 p-2.5 rounded-xl mb-2.5 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                    <p className="text-[11px] text-amber-800 leading-normal font-medium">
                      <strong className="text-amber-900">Masking Contradiction:</strong> Voice tone or
                      lyrics contradict facial cues (smile & frown blend). Hidden stress detected.
                    </p>
                  </div>
                )}

                {fusedEmotion.recommendation && (
                  <div className="text-xs text-slate-600 leading-relaxed bg-white/70 border border-white/50 p-2.5 rounded-xl">
                    <strong className="text-indigo-950 font-bold block mb-0.5">Empathetic Tip:</strong>
                    {fusedEmotion.recommendation}
                  </div>
                )}
              </div>
            )}

            {/* Privacy details */}
            <div className="mt-4 pt-3 border-t border-slate-100/80 flex items-center justify-between text-[9px] text-slate-400 font-bold uppercase tracking-wider">
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" /> Local Processing
              </span>
              <span className="flex items-center gap-1">
                <Lock className="w-3.5 h-3.5 text-emerald-500" /> Zero Raw Transmission
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
