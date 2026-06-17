/* ──────────────────────────────────────────────────────────────
   MoodSelector — Emoji-based mood picker with animations
   ────────────────────────────────────────────────────────────── */
import { motion } from "framer-motion";
import { ALL_MOODS, MOOD_CONFIG, type Mood } from "../../types/journal";

interface MoodSelectorProps {
  value?: Mood;
  onChange: (mood: Mood) => void;
  error?: string;
}

export default function MoodSelector({ value, onChange, error }: MoodSelectorProps) {
  return (
    <div className="flex flex-col gap-3">
      <label className="text-sm font-semibold text-surface-700">How are you feeling?</label>
      <div className="flex flex-wrap gap-2.5">
        {ALL_MOODS.map((mood) => {
          const config = MOOD_CONFIG[mood];
          const isSelected = value === mood;

          return (
            <motion.button
              key={mood}
              type="button"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onChange(mood)}
              className="cursor-pointer px-4 py-2.5 rounded-full text-sm font-semibold transition-all duration-300 flex items-center gap-2 border-2"
              style={{
                background: isSelected ? config.bgColor : "white",
                borderColor: isSelected ? config.color : "var(--color-surface-200)",
                color: isSelected ? config.color : "var(--color-surface-600)",
                boxShadow: isSelected ? `0 4px 16px ${config.color}30` : "none",
              }}
            >
              <span className="text-xl">{config.emoji}</span>
              {mood}
            </motion.button>
          );
        })}
      </div>
      {error && <p className="text-xs text-danger-500 font-medium">{error}</p>}
    </div>
  );
}
