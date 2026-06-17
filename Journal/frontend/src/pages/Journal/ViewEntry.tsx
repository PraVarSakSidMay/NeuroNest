/* ──────────────────────────────────────────────────────────────
   ViewEntry — Full journal entry detail view
   ────────────────────────────────────────────────────────────── */
import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import * as journalService from "../../services/journalService";
import { MOOD_CONFIG, type JournalEntry } from "../../types/journal";
import { useAppContext } from "../../context/AppContext";
import { PageLoader } from "../../components/common/Loader";
import Modal from "../../components/common/Modal";
import Button from "../../components/common/Button";

export default function ViewEntry() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useAppContext();
  const [entry, setEntry] = useState<JournalEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDelete, setShowDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await journalService.getEntry(id!);
        setEntry(data);
      } catch {
        addToast("Entry not found", "error");
        navigate("/journal");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id, navigate, addToast]);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await journalService.deleteEntry(id!);
      addToast("Entry deleted", "success");
      navigate("/journal");
    } catch {
      addToast("Failed to delete entry", "error");
    } finally {
      setDeleting(false);
    }
  };

  if (loading) return <PageLoader />;
  if (!entry) return null;

  const mood = MOOD_CONFIG[entry.mood];
  const created = new Date(entry.created_at);
  const updated = new Date(entry.updated_at);

  return (
    <div className="max-w-3xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {/* Back link */}
        <Link
          to="/journal"
          className="inline-flex items-center gap-2 text-sm text-surface-500 hover:text-surface-800 transition-colors mb-8 font-medium"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
          Back to Journal
        </Link>

        <div className="glass-card p-7 lg:p-9 space-y-7">
          {/* Header */}
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-3">
              <h2 className="text-3xl font-bold text-surface-800">{entry.title}</h2>
              <div className="flex items-center gap-3 text-sm text-surface-500 font-medium">
                <span>
                  Created {created.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })} at{" "}
                  {created.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}
                </span>
                {entry.updated_at !== entry.created_at && (
                  <>
                    <span>·</span>
                    <span>
                      Updated {updated.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    </span>
                  </>
                )}
              </div>
            </div>

            <span
              className="flex-shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold"
              style={{ background: mood.bgColor, color: mood.color }}
            >
              {mood.emoji} {entry.mood}
            </span>
          </div>

          {/* Content */}
          <div className="bg-surface-50 rounded-2xl p-6 border border-surface-200">
            <p className="text-surface-800 leading-relaxed whitespace-pre-wrap text-base">{entry.content}</p>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-surface-200">
            <Link to={`/journal/${entry.id}/edit`}>
              <Button variant="secondary" icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                </svg>
              }>
                Edit
              </Button>
            </Link>
            <Button variant="danger" onClick={() => setShowDelete(true)} icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
            }>
              Delete
            </Button>
          </div>
        </div>
      </motion.div>

      <Modal isOpen={showDelete} onClose={() => setShowDelete(false)} title="Delete Entry">
        <p className="text-base text-surface-500 mb-7">
          Are you sure you want to delete "{entry.title}"? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" onClick={() => setShowDelete(false)}>Cancel</Button>
          <Button variant="danger" loading={deleting} onClick={handleDelete}>Delete</Button>
        </div>
      </Modal>
    </div>
  );
}
