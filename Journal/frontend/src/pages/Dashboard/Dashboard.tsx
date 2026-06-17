/* ──────────────────────────────────────────────────────────────
   Dashboard — Overview page with stats, mood chart, recent entries
   ────────────────────────────────────────────────────────────── */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { type JournalEntry, type Mood, ALL_MOODS, MOOD_CONFIG } from "../../types/journal";
import type { EmotionalSummary } from "../../types/reflection";
import * as journalService from "../../services/journalService";
import * as reflectionService from "../../services/reflectionService";
import JournalCard from "../../components/journal/JournalCard";
import MoodChart from "../../components/timeline/MoodChart";
import { CardSkeleton, PageLoader } from "../../components/common/Loader";
import Button from "../../components/common/Button";

export default function Dashboard() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [reflections, setReflections] = useState<EmotionalSummary[]>([]);
  const [totalEntries, setTotalEntries] = useState(0);
  const [totalReflections, setTotalReflections] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [journalData, reflData] = await Promise.all([
          journalService.getEntries({ page: 1, page_size: 50, sort_order: "desc" }),
          reflectionService.getReflections(1, 50),
        ]);
        setEntries(journalData.entries);
        setTotalEntries(journalData.total);
        setReflections(reflData.reflections);
        setTotalReflections(reflData.total);
      } catch {
        // Errors handled silently — dashboard shows empty state
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <PageLoader />;

  // Calculate mood distribution
  const moodCounts = ALL_MOODS.reduce((acc, m) => {
    acc[m] = entries.filter((e) => e.mood === m).length;
    return acc;
  }, {} as Record<Mood, number>);

  // Most common mood
  const topMood = ALL_MOODS.reduce((a, b) => (moodCounts[a] >= moodCounts[b] ? a : b));

  const recentEntries = entries.slice(0, 4);

  const stats = [
    {
      label: "Total Entries",
      value: totalEntries,
      icon: "📝",
      gradient: "from-primary-100 to-primary-50",
      iconBg: "bg-primary-500/10",
      iconColor: "text-primary-600",
    },
    {
      label: "Reflections",
      value: totalReflections,
      icon: "🧠",
      gradient: "from-accent-100 to-accent-50",
      iconBg: "bg-accent-500/10",
      iconColor: "text-accent-600",
    },
    {
      label: "Top Mood",
      value: totalEntries > 0 ? `${MOOD_CONFIG[topMood].emoji} ${topMood}` : "—",
      icon: "",
      gradient: "from-success-100 to-success-50",
      iconBg: "bg-success-500/10",
      iconColor: "text-success-600",
    },
    {
      label: "This Week",
      value: entries.filter(
        (e) => new Date(e.created_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
      ).length,
      icon: "📅",
      gradient: "from-warning-100 to-warning-50",
      iconBg: "bg-warning-500/10",
      iconColor: "text-warning-600",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Welcome */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h2 className="text-3xl font-bold gradient-text">Welcome back!</h2>
          <p className="text-base text-surface-500 mt-2">Here's how your journaling journey looks today.</p>
        </div>
        <div className="flex gap-3">
          <Link to="/journal/new">
            <Button icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            }>
              New Entry
            </Button>
          </Link>
          <Link to="/reflections">
            <Button variant="secondary" icon={<span>✨</span>}>
              Reflect
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className={`glass-card p-6 bg-gradient-to-br ${stat.gradient}`}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-surface-500 uppercase tracking-wider">{stat.label}</span>
              {stat.icon && (
                <div className={`w-10 h-10 rounded-xl ${stat.iconBg} flex items-center justify-center ${stat.iconColor} text-xl`}>
                  {stat.icon}
                </div>
              )}
            </div>
            <p className="text-3xl font-bold text-surface-800">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Recent Entries */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold text-surface-800">Recent Entries</h3>
            <Link to="/journal" className="text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors">
              View all →
            </Link>
          </div>

          {recentEntries.length > 0 ? (
            <div className="grid sm:grid-cols-2 gap-5">
              {recentEntries.map((entry, i) => (
                <JournalCard key={entry.id} entry={entry} index={i} />
              ))}
            </div>
          ) : (
            <div className="glass-card p-12 text-center">
              <p className="text-5xl mb-4">📓</p>
              <p className="text-base text-surface-600 mb-4">No journal entries yet.</p>
              <Link to="/journal/new">
                <Button variant="secondary">Write your first entry</Button>
              </Link>
            </div>
          )}
        </div>

        {/* Mood Distribution */}
        <div>
          <MoodChart moodCounts={moodCounts} />
        </div>
      </div>
    </div>
  );
}
