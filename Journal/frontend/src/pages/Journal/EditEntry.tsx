/* ──────────────────────────────────────────────────────────────
   EditEntry — Edit existing journal entry
   ────────────────────────────────────────────────────────────── */
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import JournalForm, { type JournalFormData } from "../../components/journal/JournalForm";
import * as journalService from "../../services/journalService";
import { useAppContext } from "../../context/AppContext";
import { PageLoader } from "../../components/common/Loader";
import type { JournalEntry } from "../../types/journal";

export default function EditEntry() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useAppContext();
  const [entry, setEntry] = useState<JournalEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

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

  const handleSubmit = async (data: JournalFormData) => {
    setSaving(true);
    try {
      await journalService.updateEntry(id!, data);
      addToast("Entry updated successfully!", "success");
      navigate(`/journal/${id}`);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to update entry", "error");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <PageLoader />;
  if (!entry) return null;

  return (
    <div className="max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="mb-8">
          <h2 className="text-3xl font-bold gradient-text">Edit Entry</h2>
          <p className="text-base text-surface-500 mt-2">Update your journal entry below.</p>
        </div>

        <div className="glass-card p-7 lg:p-9">
          <JournalForm
            defaultValues={{
              title: entry.title,
              content: entry.content,
              mood: entry.mood,
            }}
            onSubmit={handleSubmit}
            loading={saving}
            submitLabel="Save Changes"
          />
        </div>
      </motion.div>
    </div>
  );
}
