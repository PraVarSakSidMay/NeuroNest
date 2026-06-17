/* ──────────────────────────────────────────────────────────────
   CreateEntry — New journal entry page
   ────────────────────────────────────────────────────────────── */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import JournalForm, { type JournalFormData } from "../../components/journal/JournalForm";
import * as journalService from "../../services/journalService";
import { useAppContext } from "../../context/AppContext";

export default function CreateEntry() {
  const navigate = useNavigate();
  const { addToast } = useAppContext();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (data: JournalFormData) => {
    setLoading(true);
    try {
      await journalService.createEntry(data);
      addToast("Entry created successfully!", "success");
      navigate("/journal");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Failed to create entry", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="mb-8">
          <h2 className="text-3xl font-bold gradient-text">New Journal Entry</h2>
          <p className="text-base text-surface-500 mt-2">
            Take a moment to reflect on your day. Write freely — your thoughts are encrypted and private.
          </p>
        </div>

        <div className="glass-card p-7 lg:p-9">
          <JournalForm onSubmit={handleSubmit} loading={loading} submitLabel="Create Entry" />
        </div>
      </motion.div>
    </div>
  );
}
