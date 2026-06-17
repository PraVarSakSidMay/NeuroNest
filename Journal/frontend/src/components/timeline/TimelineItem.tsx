/* ──────────────────────────────────────────────────────────────
   TimelineItem — Single timeline event (journal or reflection)
   ────────────────────────────────────────────────────────────── */
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { MOOD_CONFIG, type JournalEntry } from "../../types/journal";
import type { EmotionalSummary } from "../../types/reflection";

type TimelineEvent =
  | { type: "journal"; data: JournalEntry }
  | { type: "reflection"; data: EmotionalSummary };

interface TimelineItemProps {
  event: TimelineEvent;
  index?: number;
}

export default function TimelineItem({ event, index = 0 }: TimelineItemProps) {
  const date = new Date(event.data.created_at);
  const formattedDate = date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  const formattedTime = date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: index * 0.04 }}
      className="relative flex gap-6 pb-10 last:pb-0"
    >
      {/* Vertical line */}
      <div className="flex flex-col items-center">
        <div
          className="w-4 h-4 rounded-full flex-shrink-0 mt-1.5 ring-4 ring-white shadow-md"
          style={{
            background: event.type === "journal"
              ? MOOD_CONFIG[(event.data as JournalEntry).mood]?.color || "#7c6de3"
              : "linear-gradient(135deg, #7c6de3, #ec4899)",
          }}
        />
        <div className="w-0.5 flex-1 bg-gradient-to-b from-primary-200 to-transparent mt-2" />
      </div>

      {/* Content */}
      <div className="flex-1 glass-card p-6">
        <div className="flex items-center gap-3 mb-3 text-sm text-surface-500 font-medium">
          <span>{formattedDate}</span>
          <span>·</span>
          <span>{formattedTime}</span>
          <span className={`ml-auto px-3 py-1 rounded-full text-xs font-semibold ${
            event.type === "journal"
              ? "bg-gradient-to-r from-primary-100 to-accent-100 text-primary-700"
              : "bg-gradient-to-r from-accent-100 to-primary-100 text-accent-700"
          }`}>
            {event.type === "journal" ? "Journal" : "Reflection"}
          </span>
        </div>

        {event.type === "journal" ? (
          <>
            <Link
              to={`/journal/${event.data.id}`}
              className="text-lg font-bold text-surface-800 hover:text-primary-600 transition-colors"
            >
              {(event.data as JournalEntry).title}
            </Link>
            <p className="text-sm text-surface-600 line-clamp-2 mt-2">
              {(event.data as JournalEntry).content}
            </p>
            <span
              className="inline-flex items-center gap-2 mt-4 px-3 py-1.5 rounded-full text-sm font-semibold"
              style={{
                background: MOOD_CONFIG[(event.data as JournalEntry).mood]?.bgColor,
                color: MOOD_CONFIG[(event.data as JournalEntry).mood]?.color,
              }}
            >
              {MOOD_CONFIG[(event.data as JournalEntry).mood]?.emoji} {(event.data as JournalEntry).mood}
            </span>
          </>
        ) : (
          <>
            <h4 className="text-lg font-bold text-surface-800 flex items-center gap-2">
              <span className="text-lg">🧠</span> AI Reflection
            </h4>
            <p className="text-sm text-surface-600 line-clamp-3 mt-2">
              {(event.data as EmotionalSummary).summary}
            </p>
          </>
        )}
      </div>
    </motion.div>
  );
}

export type { TimelineEvent };
