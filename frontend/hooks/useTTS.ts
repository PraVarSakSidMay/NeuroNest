"use client";
import { useCallback, useEffect, useRef, useState } from "react";

export type VoiceGender = "female" | "male";

let globalVoiceGender: VoiceGender = "female";
let globalAutoSpeak = true;

// Voice preference order — Google voices first (Chrome), then other natural voices
const FEMALE_VOICE_PRIORITY = [
  // Google voices (Chrome) — best quality
  "google us english",
  "google uk english female",
  "google hindi",
  "google",
  // Microsoft natural voices (Edge/Windows 11)
  "microsoft aria",
  "microsoft jenny",
  "microsoft zira",
  "microsoft hazel",
  "microsoft susan",
  // Apple voices (Safari/Mac)
  "samantha",
  "karen",
  "moira",
  "tessa",
  "fiona",
  "veena",
  // Generic fallbacks
  "female",
  "woman",
  "girl",
];

const MALE_VOICE_PRIORITY = [
  // Google voices (Chrome)
  "google uk english male",
  "google us english male",
  // Microsoft natural voices
  "microsoft guy",
  "microsoft david",
  "microsoft mark",
  "microsoft ryan",
  // Apple voices
  "alex",
  "daniel",
  "fred",
  "jorge",
  "thomas",
  "lee",
  "rishi",
  // Generic fallbacks
  "male",
  "man",
  "guy",
];

function getBestVoice(gender: VoiceGender): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;

  const priorities = gender === "female" ? FEMALE_VOICE_PRIORITY : MALE_VOICE_PRIORITY;

  // Try each priority in order
  for (const priority of priorities) {
    const match = voices.find((v) =>
      v.name.toLowerCase().includes(priority.toLowerCase())
    );
    if (match) return match;
  }

  // Last resort: any English voice
  const englishVoices = voices.filter((v) => v.lang.startsWith("en"));
  if (englishVoices.length > 0) {
    return gender === "female" ? englishVoices[0] : (englishVoices[1] || englishVoices[0]);
  }

  return voices[0];
}

export function useTTS() {
  const [isSpeaking, setIsSpeaking]        = useState(false);
  const [voiceGender, setVoiceGenderState] = useState<VoiceGender>(globalVoiceGender);
  const [autoSpeak, setAutoSpeakState]     = useState(globalAutoSpeak);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Load voices when they become available
  useEffect(() => {
    if (typeof window === "undefined") return;
    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) setAvailableVoices(voices);
    };
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    return () => { window.speechSynthesis.onvoiceschanged = null; };
  }, []);

  const setVoiceGender = useCallback((g: VoiceGender) => {
    globalVoiceGender = g;
    setVoiceGenderState(g);
  }, []);

  const setAutoSpeak = useCallback((v: boolean) => {
    globalAutoSpeak = v;
    setAutoSpeakState(v);
  }, []);

  const speak = useCallback((text: string) => {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();

    // Clean text for natural speech
    const cleanText = text
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/#{1,6}\s/g, "")
      .replace(/[\u{1F300}-\u{1FAFF}]/gu, "")
      .replace(/[🎵💡🌬️📦🫁✅🗂️☕🚪🤝📉🔍🏙️💬🌐📱💪✍️🤲😊😤😰😢😠😌🤯🥺🤩😐]/g, "")
      .replace(/\s+/g, " ")
      .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utteranceRef.current = utterance;

    const doSpeak = () => {
      const voice = getBestVoice(globalVoiceGender);

      if (voice) {
        utterance.voice = voice;
        // Adjust rate and pitch based on voice type
        const isGoogle = voice.name.toLowerCase().includes("google");
        const isMicrosoft = voice.name.toLowerCase().includes("microsoft");

        if (isGoogle) {
          utterance.rate  = 0.95;  // Google voices sound best slightly slower
          utterance.pitch = globalVoiceGender === "female" ? 1.0 : 0.9;
        } else if (isMicrosoft) {
          utterance.rate  = 0.90;
          utterance.pitch = globalVoiceGender === "female" ? 1.05 : 0.85;
        } else {
          utterance.rate  = 0.92;
          utterance.pitch = globalVoiceGender === "female" ? 1.1 : 0.85;
        }
      } else {
        utterance.rate  = 0.92;
        utterance.pitch = globalVoiceGender === "female" ? 1.1 : 0.85;
      }

      utterance.volume = 1;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend   = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    };

    // If voices not loaded yet, wait for them
    if (!window.speechSynthesis.getVoices().length) {
      window.speechSynthesis.onvoiceschanged = doSpeak;
    } else {
      doSpeak();
    }
  }, []);

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  // Get the name of the currently selected voice for display
  const currentVoiceName = (() => {
    if (typeof window === "undefined") return "";
    const voice = getBestVoice(voiceGender);
    return voice?.name || "Default";
  })();

  return {
    speak, stop, isSpeaking,
    voiceGender, setVoiceGender,
    autoSpeak, setAutoSpeak,
    availableVoices,
    currentVoiceName,
  };
}
