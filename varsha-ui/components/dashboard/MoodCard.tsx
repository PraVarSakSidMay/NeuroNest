// MoodCard.tsx — Shows today's mood status with emoji selector
// "use client" because it has interactive state (selected mood)

"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

// Each mood: emoji, label, color when selected
const moods = [
  { emoji: "😄", label: "Great",   color: "bg-emerald-100 border-emerald-400" },
  { emoji: "🙂", label: "Good",    color: "bg-blue-100 border-blue-400"       },
  { emoji: "😐", label: "Okay",    color: "bg-yellow-100 border-yellow-400"   },
  { emoji: "😔", label: "Low",     color: "bg-orange-100 border-orange-400"   },
  { emoji: "😢", label: "Rough",   color: "bg-red-100 border-red-400"         },
];

export default function MoodCard() {
  const [selected, setSelected] = useState<number | null>(null);

  return (
    <div className="soft-card p-5 flex flex-col gap-4">
      <div>
        <h3 className="font-semibold text-[var(--color-text)]">Today&apos;s Mood</h3>
        <p className="text-xs text-[var(--color-muted)] mt-0.5">
          How are you feeling right now?
        </p>
      </div>

      {/* Mood emoji buttons */}
      <div className="flex justify-between gap-2">
        {moods.map((mood, i) => (
          <button
            key={i}
            onClick={() => setSelected(i)}
            className={cn(
              "flex-1 flex flex-col items-center gap-1 py-2 rounded-xl border-2 transition-all duration-200",
              selected === i
                ? mood.color + " scale-105"
                : "border-transparent hover:bg-gray-50"
            )}
          >
            <span className="text-2xl">{mood.emoji}</span>
            <span className="text-[10px] text-[var(--color-muted)]">{mood.label}</span>
          </button>
        ))}
      </div>

      {/* Confirmation message */}
      {selected !== null && (
        <p className="text-xs text-center text-violet-600 font-medium">
          Logged: {moods[selected].label} {moods[selected].emoji}
        </p>
      )}

      {/* Log button */}
      <button
        disabled={selected === null}
        className="w-full py-2 rounded-lg bg-violet-600 text-white text-sm font-medium hover:bg-violet-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        Log Mood
      </button>
    </div>
  );
}
