/* ──────────────────────────────────────────────────────────────
   JournalList — Browse, search, and filter journal entries
   ────────────────────────────────────────────────────────────── */
import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useJournalEntries } from "../../hooks/useJournalEntries";
import { ALL_MOODS, MOOD_CONFIG, type Mood } from "../../types/journal";
import JournalCard from "../../components/journal/JournalCard";
import SearchBar from "../../components/common/SearchBar";
import Pagination from "../../components/common/Pagination";
import Modal from "../../components/common/Modal";
import Button from "../../components/common/Button";
import EmptyState from "../../components/common/EmptyState";
import { CardSkeleton } from "../../components/common/Loader";
import { useAppContext } from "../../context/AppContext";

export default function JournalList() {
  const {
    entries, total, page, pageSize,
    loading, search, moodFilter,
    setSearch, setMoodFilter, setPage,
    removeEntry,
  } = useJournalEntries();
  const { addToast } = useAppContext();
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await removeEntry(deleteId);
      addToast("Entry deleted successfully", "success");
    } catch {
      addToast("Failed to delete entry", "error");
    } finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-7">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h2 className="text-3xl font-bold gradient-text">Your Journal</h2>
          <p className="text-base text-surface-500 mt-1">{total} {total === 1 ? "entry" : "entries"}</p>
        </div>
        <Link to="/journal/new">
          <Button icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
          }>
            New Entry
          </Button>
        </Link>
      </motion.div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <SearchBar value={search} onChange={setSearch} placeholder="Search your entries..." />
        </div>

        {/* Mood filter */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setMoodFilter(undefined)}
            className={`px-4 py-2 rounded-full text-xs font-semibold transition-all duration-300 cursor-pointer border-2 ${
              !moodFilter
                ? "bg-gradient-to-r from-primary-500 to-accent-500 border-transparent text-white shadow-md shadow-primary-500/20"
                : "bg-white border-surface-200 text-surface-600 hover:bg-surface-50"
            }`}
          >
            All
          </button>
          {ALL_MOODS.map((mood) => {
            const config = MOOD_CONFIG[mood];
            const isSelected = moodFilter === mood;
            return (
              <button
                key={mood}
                onClick={() => setMoodFilter(mood as Mood)}
                className={`px-4 py-2 rounded-full text-xs font-semibold transition-all duration-300 cursor-pointer border-2 flex items-center gap-1.5 ${
                  isSelected
                    ? "border-transparent"
                    : "bg-white border-surface-200 hover:bg-surface-50"
                }`}
                style={
                  isSelected
                    ? {
                        background: config.bgColor,
                        borderColor: config.color,
                        color: config.color,
                        boxShadow: `0 4px 12px ${config.color}25`,
                      }
                    : { color: "var(--color-surface-600)" }
                }
              >
                {config.emoji} {mood}
              </button>
            );
          })}
        </div>
      </div>

      {/* Entries Grid */}
      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : entries.length > 0 ? (
        <>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {entries.map((entry, i) => (
              <JournalCard
                key={entry.id}
                entry={entry}
                index={i}
                onDelete={(id) => setDeleteId(id)}
              />
            ))}
          </div>
          <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
        </>
      ) : (
        <EmptyState
          title={search || moodFilter ? "No matching entries" : "No journal entries yet"}
          description={
            search || moodFilter
              ? "Try adjusting your search or filters."
              : "Start your journaling journey by creating your first entry."
          }
          action={
            !search && !moodFilter ? (
              <Link to="/journal/new">
                <Button>Write your first entry</Button>
              </Link>
            ) : undefined
          }
        />
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        title="Delete Entry"
      >
        <p className="text-base text-surface-600 mb-7">
          Are you sure you want to delete this entry? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" onClick={() => setDeleteId(null)}>Cancel</Button>
          <Button variant="danger" loading={deleting} onClick={handleDelete}>Delete</Button>
        </div>
      </Modal>
    </div>
  );
}
