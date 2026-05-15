// StatCard.tsx — Shows a single metric (score, streak, sleep, etc.)
// Props:
//   title    → label e.g. "Wellness Score"
//   value    → main number e.g. "82"
//   unit     → suffix e.g. "/100"
//   icon     → lucide icon element
//   color    → "violet" | "orange" | "blue" | "green"
//   change   → small text below e.g. "+5 from last week"
//   positive → true = green change text, false = red

import { cn } from "@/lib/utils";

type StatCardProps = {
  title: string;
  value: string;
  unit?: string;
  icon: React.ReactNode;
  color?: "violet" | "orange" | "blue" | "green";
  change?: string;
  positive?: boolean;
};

// Color maps for icon background and icon color
const colorMap = {
  violet: { bg: "bg-violet-100", text: "text-violet-600" },
  orange: { bg: "bg-orange-100", text: "text-orange-500" },
  blue:   { bg: "bg-blue-100",   text: "text-blue-500"   },
  green:  { bg: "bg-emerald-100",text: "text-emerald-600" },
};

export default function StatCard({
  title,
  value,
  unit,
  icon,
  color = "violet",
  change,
  positive = true,
}: StatCardProps) {
  const { bg, text } = colorMap[color];

  return (
    <div className="soft-card p-5 flex flex-col gap-3">
      {/* Icon + title row */}
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-[var(--color-muted)]">{title}</p>
        <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center", bg)}>
          <span className={text}>{icon}</span>
        </div>
      </div>

      {/* Value */}
      <div className="flex items-end gap-1">
        <span className="text-3xl font-bold text-[var(--color-text)]">{value}</span>
        {unit && (
          <span className="text-sm text-[var(--color-muted)] mb-1">{unit}</span>
        )}
      </div>

      {/* Change indicator */}
      {change && (
        <p className={cn("text-xs font-medium", positive ? "text-emerald-600" : "text-red-500")}>
          {positive ? "↑" : "↓"} {change}
        </p>
      )}
    </div>
  );
}
