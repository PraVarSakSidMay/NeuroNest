/* ──────────────────────────────────────────────────────────────
   TimelinePage — Chronological feed of entries + reflections
   ────────────────────────────────────────────────────────────── */
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import * as journalService from "../../services/journalService";
import * as reflectionService from "../../services/reflectionService";
import type { JournalEntry, Mood } from "../../types/journal";
import { ALL_MOODS } from "../../types/journal";
import type { EmotionalSummary } from "../../types/reflection";
import TimelineItem, { type TimelineEvent } from "../../components/timeline/TimelineItem";
import MoodChart from "../../components/timeline/MoodChart";
import EmptyState from "../../components/common/EmptyState";
import { PageLoader } from "../../components/common/Loader";
import { Link } from "react-router-dom";
import Button from "../../components/common/Button";

export default function TimelinePage() {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [journalData, reflData] = await Promise.all([
          journalService.getEntries({ page: 1, page_size: 100, sort_order: "desc" }),
          reflectionService.getReflections(1, 100),
        ]);
        setEntries(journalData.entries);

        // Merge and sort by date, newest first
        const allEvents: TimelineEvent[] = [
          ...journalData.entries.map((e) => ({ type: "journal" as const, data: e })),
          ...reflData.reflections.map((r) => ({ type: "reflection" as const, data: r })),
        ].sort(
          (a, b) =>
            new Date(b.data.created_at).getTime() - new Date(a.data.created_at).getTime()
        );
        setEvents(allEvents);
      } catch {
        // Handled silently
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <PageLoader />;

  // Mood distribution
  const moodCounts = ALL_MOODS.reduce((acc, m) => {
    acc[m] = entries.filter((e) => e.mood === m).length;
    return acc;
  }, {} as Record<Mood, number>);

  return (
    <div className="max-w-5xl mx-auto space-y-10">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h2 className="text-3xl font-bold gradient-text">Your Timeline</h2>
        <p className="text-base text-surface-500 mt-2">
          A chronological view of your journaling and reflection journey.
        </p>
      </motion.div>

      {events.length > 0 ? (
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Timeline feed */}
          <div className="lg:col-span-2 space-y-6">
            {events.map((event, i) => (
              <TimelineItem key={`${event.type}-${event.data.id}`} event={event} index={i} />
            ))}
          </div>

          {/* Sidebar — Mood chart */}
          <div className="space-y-6">
            <MoodChart moodCounts={moodCounts} />

            {/* Summary stats */}
            <div className="glass-card p-6 space-y-4">
              <h3 className="text-lg font-semibold text-surface-800">Journey Stats</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-surface-500">Total Events</span>
                  <span className="text-surface-800 font-bold">{events.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-surface-500">Journal Entries</span>
                  <span className="text-surface-800 font-bold">
                    {events.filter((e) => e.type === "journal").length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-surface-500">AI Reflections</span>
                  <span className="text-surface-800 font-bold">
                    {events.filter((e) => e.type === "reflection").length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <EmptyState
          title="Your timeline is empty"
          description="Start writing journal entries and generating reflections to see your journey unfold."
          action={
            <Link to="/journal/new">
              <Button>Create your first entry</Button>
            </Link>
          }
        />
      )}
    </div>
  );
}
