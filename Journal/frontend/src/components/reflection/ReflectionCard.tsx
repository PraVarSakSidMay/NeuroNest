/* ──────────────────────────────────────────────────────────────
   ReflectionCard — AI-generated emotional summary card
   ────────────────────────────────────────────────────────────── */
import { motion } from "framer-motion";
import type { EmotionalSummary } from "../../types/reflection";
import { RANGE_LABELS } from "../../types/reflection";

interface ReflectionCardProps {
  reflection: EmotionalSummary;
  onDelete?: (id: string) => void;
  index?: number;
}

function Section({ title, icon, items }: { title: string; icon: string; items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold text-surface-700 flex items-center gap-2">
        <span className="text-lg">{icon}</span> {title}
      </h4>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-surface-600 pl-6 relative before:content-['•'] before:absolute before:left-2 before:text-primary-500 before:text-lg">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ReflectionCard({ reflection, onDelete, index = 0 }: ReflectionCardProps) {
  const formattedDate = new Date(reflection.created_at).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
  const rangeLabel = RANGE_LABELS[reflection.selected_range?.range_type] || "Custom";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
      className="glass-card p-7 space-y-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl">🧠</span>
            <h3 className="text-lg font-bold text-surface-800">AI Reflection</h3>
          </div>
          <div className="flex items-center gap-3 text-sm text-surface-500 font-medium">
            <span className="px-3 py-1 rounded-full bg-gradient-to-r from-primary-100 to-accent-100 text-primary-700">{rangeLabel}</span>
            <span>·</span>
            <span>{formattedDate}</span>
          </div>
        </div>
        {onDelete && (
          <button
            onClick={() => onDelete(reflection.id)}
            className="p-2.5 rounded-2xl text-surface-400 hover:text-danger-500 hover:bg-danger-100 transition-all duration-200 cursor-pointer"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
        )}
      </div>

      {/* Summary */}
      {reflection.summary && (
        <p className="text-base text-surface-700 leading-relaxed bg-gradient-to-br from-primary-50 to-accent-50 rounded-2xl p-5 border border-primary-100">
          {reflection.summary}
        </p>
      )}

      {/* Sections */}
      <div className="grid gap-6 sm:grid-cols-2">
        <Section title="Emotional Patterns" icon="🔄" items={reflection.emotional_patterns} />
        <Section title="Positive Observations" icon="✨" items={reflection.positive_observations} />
        <Section title="Gentle Insights" icon="💡" items={reflection.gentle_insights} />
        <Section title="Growth Suggestions" icon="🌱" items={reflection.growth_suggestions} />
      </div>
    </motion.div>
  );
}
