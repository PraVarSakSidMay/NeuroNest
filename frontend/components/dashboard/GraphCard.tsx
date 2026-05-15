// GraphCard.tsx — Mood trend graph for the week
// Uses pure CSS bars (no chart library needed).
// When you're ready to add Recharts, replace the bar section with a <LineChart>.

const weekData = [
  { day: "Mon", score: 60 },
  { day: "Tue", score: 75 },
  { day: "Wed", score: 55 },
  { day: "Thu", score: 80 },
  { day: "Fri", score: 70 },
  { day: "Sat", score: 85 },
  { day: "Sun", score: 82 },
];

export default function GraphCard() {
  const max = Math.max(...weekData.map((d) => d.score));

  return (
    <div className="soft-card p-5 h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-[var(--color-text)]">Mood Trend</h3>
          <p className="text-xs text-[var(--color-muted)]">This week&apos;s wellness scores</p>
        </div>
        <span className="text-xs bg-violet-100 text-violet-600 font-medium px-2.5 py-1 rounded-full">
          This Week
        </span>
      </div>

      {/* Bar chart */}
      <div className="flex items-end gap-2 h-32 mt-2">
        {weekData.map(({ day, score }) => {
          const heightPct = (score / max) * 100;
          return (
            <div key={day} className="flex-1 flex flex-col items-center gap-1">
              {/* Score tooltip on hover */}
              <div className="relative group flex flex-col items-center w-full">
                {/* Tooltip */}
                <span className="absolute -top-6 text-[10px] bg-violet-600 text-white px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                  {score}
                </span>
                {/* Bar */}
                <div
                  className="w-full rounded-t-md bg-violet-200 group-hover:bg-violet-500 transition-colors duration-200"
                  style={{ height: `${heightPct}%`, minHeight: "8px" }}
                />
              </div>
              {/* Day label */}
              <span className="text-[10px] text-[var(--color-muted)]">{day}</span>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-2 text-xs text-[var(--color-muted)]">
        <span className="w-3 h-3 rounded-sm bg-violet-500 inline-block" />
        Wellness score (0–100)
      </div>
    </div>
  );
}
