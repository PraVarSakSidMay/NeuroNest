"use client";

import { useState } from "react";
import { Mic, MicOff, Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";

const transcripts = [
  { role: "user", text: "I've been feeling really anxious about my upcoming presentation at work." },
  { role: "ai",   text: "I hear you. Work presentations can feel very stressful. Let's take a moment to breathe together. Inhale slowly for 4 counts..." },
  { role: "user", text: "Okay, I'm trying the breathing exercise." },
  { role: "ai",   text: "That's wonderful. You're doing great. Remember — you've prepared for this. Your feelings are valid, and anxiety often means you care deeply about doing well." },
];

const prompts = ["How do I manage anxiety?", "I need to vent", "Help me relax", "Daily check-in"];

export default function VoicePage() {
  const [recording, setRecording]   = useState(false);
  const [hasSession, setHasSession] = useState(false);

  function toggle() {
    if (!recording) { setRecording(true); setTimeout(() => { setRecording(false); setHasSession(true); }, 3000); }
    else setRecording(false);
  }

  return (
    <div className="max-w-2xl mx-auto space-y-10">

      {/* Header */}
      <div>
        <h1 className="text-[1.75rem] font-bold text-gray-900">Voice Assistant 🎙️</h1>
        <p className="text-base text-gray-500 mt-1.5">Speak your mind — NeuroBot is listening</p>
      </div>

      {/* Mic card */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-sm px-10 py-14 flex flex-col items-center gap-10">

        {/* Waveform */}
        <div className="flex items-end gap-1.5 h-16">
          {Array.from({ length: 28 }).map((_, i) => (
            <div key={i}
              className={cn("w-1.5 rounded-full transition-all duration-300", recording ? "bg-violet-500" : "bg-gray-200")}
              style={{
                height: recording ? `${14 + Math.abs(Math.sin(i * 0.7)) * 38}px` : `${6 + Math.abs(Math.sin(i * 0.5)) * 10}px`,
                animation: recording ? `wave 0.9s ease ${i * 0.04}s infinite` : "none",
              }}
            />
          ))}
        </div>

        {/* Mic button */}
        <div className="relative flex items-center justify-center">
          {recording && (
            <>
              <div className="absolute w-36 h-36 rounded-full bg-violet-400 opacity-20" style={{ animation: "pulse-ring 1.5s ease-out infinite" }} />
              <div className="absolute w-36 h-36 rounded-full bg-violet-400 opacity-10" style={{ animation: "pulse-ring 1.5s ease-out 0.6s infinite" }} />
            </>
          )}
          <button onClick={toggle}
            className={cn(
              "relative w-32 h-32 rounded-full flex items-center justify-center shadow-2xl transition-all duration-300",
              recording ? "bg-red-500 hover:bg-red-600 scale-110 shadow-red-200" : "bg-gradient-to-br from-violet-600 to-blue-500 hover:scale-105 shadow-violet-200"
            )}>
            {recording ? <MicOff size={44} className="text-white" /> : <Mic size={44} className="text-white" />}
          </button>
        </div>

        {/* Status */}
        <div className="text-center">
          <p className="text-xl font-semibold text-gray-900">{recording ? "Listening..." : "Tap to speak"}</p>
          <p className="text-[15px] text-gray-500 mt-1.5">
            {recording ? "Speak naturally — I'm here for you" : "Hold a conversation with NeuroBot"}
          </p>
        </div>

        {/* Quick prompts */}
        {!recording && !hasSession && (
          <div className="flex flex-wrap gap-3 justify-center">
            {prompts.map(p => (
              <button key={p} onClick={toggle}
                className="text-[15px] bg-violet-50 text-violet-700 px-5 py-2.5 rounded-full font-medium hover:bg-violet-100 transition-colors">
                {p}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Transcript */}
      {hasSession && (
        <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 text-lg flex items-center gap-2">
              <Volume2 size={20} className="text-violet-600" /> Session Transcript
            </h3>
            <span className="text-sm text-gray-400">Today, {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
          </div>

          <div className="space-y-5">
            {transcripts.map((t, i) => (
              <div key={i} className={cn("flex gap-4", t.role === "user" && "flex-row-reverse")}>
                <div className={cn(
                  "max-w-[80%] px-5 py-3.5 rounded-3xl text-[15px] leading-relaxed",
                  t.role === "ai" ? "bg-gray-100 text-gray-800 rounded-bl-lg" : "bg-gradient-to-br from-violet-600 to-blue-500 text-white rounded-br-lg"
                )}>
                  {t.text}
                </div>
              </div>
            ))}
          </div>

      <button onClick={toggle}
        style={{
          display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
          width: "100%", padding: "16px", borderRadius: "16px", border: "none",
          background: "linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)",
          color: "#fff", fontSize: "15px", fontWeight: 600, cursor: "pointer",
        }}>
        <Mic size={17} /> Continue Session
      </button>
        </div>
      )}
    </div>
  );
}
