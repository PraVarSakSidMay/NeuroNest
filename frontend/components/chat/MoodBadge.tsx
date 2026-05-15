"use client";
import { useChatStore } from "@/store/chatStore";
import { MOOD_EMOJI, MOOD_COLOR, EMOTION_EMOJI, formatMoodLabel } from "@/lib/utils";

export function MoodBadge() {
  const { currentEmotion, currentMood } = useChatStore();
  if (!currentEmotion || !currentMood) return null;
  return (
    <div className="flex items-center gap-3 px-3 py-1.5 bg-white/5 border border-white/10 rounded-full">
      <span className="text-sm">{EMOTION_EMOJI[currentEmotion] || "💭"}</span>
      <span className="text-xs text-slate-400 capitalize">{currentEmotion}</span>
      <span className="text-slate-600">·</span>
      <span className={`text-xs font-medium ${MOOD_COLOR[currentMood] || "text-slate-400"}`}>{MOOD_EMOJI[currentMood]} {formatMoodLabel(currentMood)}</span>
    </div>
  );
}
