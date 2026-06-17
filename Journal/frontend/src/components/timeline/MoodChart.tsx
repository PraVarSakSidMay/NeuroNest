/* ──────────────────────────────────────────────────────────────
   MoodChart — Simple mood trend visualization using SVG
   ────────────────────────────────────────────────────────────── */
import { ALL_MOODS, MOOD_CONFIG, type Mood } from "../../types/journal";

interface MoodChartProps {
  moodCounts: Record<Mood, number>;
}

export default function MoodChart({ moodCounts }: MoodChartProps) {
  const maxCount = Math.max(1, ...Object.values(moodCounts));

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-semibold text-surface-800 mb-5">Mood Distribution</h3>
      <div className="space-y-3.5">
        {ALL_MOODS.map((mood) => {
          const count = moodCounts[mood] || 0;
          const pct = (count / maxCount) * 100;
          const config = MOOD_CONFIG[mood];

          return (
            <div key={mood} className="flex items-center gap-3">
              <span className="w-7 text-center text-xl">{config.emoji}</span>
              <span className="w-28 text-sm font-medium text-surface-600 truncate">{mood}</span>
              <div className="flex-1 h-3 bg-surface-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-1000 ease-out"
                  style={{
                    width: `${pct}%`,
                    background: `linear-gradient(90deg, ${config.color}, ${config.color}cc)`,
                    opacity: count > 0 ? 1 : 0.2,
                  }}
                />
              </div>
              <span className="w-8 text-sm font-semibold text-surface-600 text-right">{count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
