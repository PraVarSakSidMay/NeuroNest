"use client";
import { Volume2, VolumeX } from "lucide-react";
import { VoiceGender } from "@/hooks/useTTS";

interface TTSControlsProps {
  text: string;
  isSpeaking: boolean;
  voiceGender: VoiceGender;
  autoSpeak: boolean;
  currentVoiceName?: string;
  onSpeak: (text: string) => void;
  onStop: () => void;
  onGenderChange: (gender: VoiceGender) => void;
  onAutoSpeakChange: (value: boolean) => void;
}

export function TTSControls({
  text, isSpeaking, voiceGender, autoSpeak, currentVoiceName,
  onSpeak, onStop, onGenderChange, onAutoSpeakChange,
}: TTSControlsProps) {
  return (
    <div className="flex items-center gap-2 mt-2 flex-wrap">

      {/* Replay / Stop */}
      <button
        onClick={() => isSpeaking ? onStop() : onSpeak(text)}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-200 ${
          isSpeaking
            ? "bg-teal-500/20 border-teal-500/40 text-teal-300 hover:bg-teal-500/30"
            : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white"
        }`}
        title={isSpeaking ? "Stop speaking" : "Replay response"}
      >
        {isSpeaking
          ? <><VolumeX size={12} className="animate-pulse" />Stop</>
          : <><Volume2 size={12} />Replay</>
        }
      </button>

      {/* Voice gender toggle */}
      <div className="flex items-center bg-white/5 border border-white/10 rounded-full overflow-hidden">
        <button
          onClick={() => onGenderChange("female")}
          className={`px-2.5 py-1.5 text-xs transition-all duration-200 ${
            voiceGender === "female" ? "bg-pink-500/30 text-pink-300" : "text-slate-500 hover:text-slate-300"
          }`}
          title="Female voice"
        >
          ♀ Female
        </button>
        <button
          onClick={() => onGenderChange("male")}
          className={`px-2.5 py-1.5 text-xs transition-all duration-200 ${
            voiceGender === "male" ? "bg-blue-500/30 text-blue-300" : "text-slate-500 hover:text-slate-300"
          }`}
          title="Male voice"
        >
          ♂ Male
        </button>
      </div>

      {/* Auto-speak toggle */}
      <button
        onClick={() => onAutoSpeakChange(!autoSpeak)}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-200 ${
          autoSpeak
            ? "bg-purple-500/20 border-purple-500/30 text-purple-300"
            : "bg-white/5 border-white/10 text-slate-500"
        }`}
        title={autoSpeak ? "Auto-speak ON" : "Auto-speak OFF"}
      >
        {autoSpeak ? "🔊 Auto" : "🔇 Auto"}
      </button>

      {/* Show current voice name */}
      {currentVoiceName && currentVoiceName !== "Default" && (
        <span className="text-xs text-slate-600 truncate max-w-[120px]" title={currentVoiceName}>
          {currentVoiceName.replace("Microsoft ", "").replace(" Online (Natural)", "")}
        </span>
      )}
    </div>
  );
}
