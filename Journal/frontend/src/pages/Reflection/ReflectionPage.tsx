/* ──────────────────────────────────────────────────────────────
   ReflectionPage — Generate and view AI reflections
   ────────────────────────────────────────────────────────────── */
import { useState } from "react";
import { motion } from "framer-motion";
import { useReflections } from "../../hooks/useReflections";
import type { RangeType } from "../../types/reflection";
import RangeSelector from "../../components/reflection/RangeSelector";
import ReflectionCard from "../../components/reflection/ReflectionCard";
import Button from "../../components/common/Button";
import Modal from "../../components/common/Modal";
import EmptyState from "../../components/common/EmptyState";
import { CardSkeleton } from "../../components/common/Loader";
import { useAppContext } from "../../context/AppContext";

export default function ReflectionPage() {
  const { reflections, loading, generating, generate, remove } = useReflections();
  const { addToast } = useAppContext();
  const [rangeType, setRangeType] = useState<RangeType>("last_7_days");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const handleGenerate = async () => {
    try {
      await generate({
        range_type: rangeType,
        ...(rangeType === "custom" ? { start_date: startDate, end_date: endDate } : {}),
      });
      addToast("Reflection generated successfully!", "success");
    } catch {
      addToast("Failed to generate reflection. Make sure you have journal entries in the selected period.", "error");
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await remove(deleteId);
      addToast("Reflection deleted", "success");
    } catch {
      addToast("Failed to delete reflection", "error");
    } finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-10">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h2 className="text-3xl font-bold gradient-text">AI Reflections</h2>
        <p className="text-base text-surface-500 mt-2">
          Let AI analyze your journal entries and provide emotional insights.
        </p>
      </motion.div>

      {/* Generator Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-7 space-y-6"
      >
        <div className="flex items-center gap-4 mb-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center">
            <span className="text-2xl">✨</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-surface-800">Generate New Reflection</h3>
            <p className="text-sm text-surface-500">Select a time period to analyze your emotional patterns</p>
          </div>
        </div>

        <RangeSelector
          value={rangeType}
          onChange={setRangeType}
          startDate={startDate}
          endDate={endDate}
          onStartDateChange={setStartDate}
          onEndDateChange={setEndDate}
        />

        <div className="flex justify-end">
          <Button
            onClick={handleGenerate}
            loading={generating}
            size="lg"
            icon={<span>🧠</span>}
          >
            {generating ? "Analyzing..." : "Generate Reflection"}
          </Button>
        </div>
      </motion.div>

      {/* Past Reflections */}
      <div>
        <h3 className="text-xl font-semibold text-surface-800 mb-6">Past Reflections</h3>

        {loading ? (
          <div className="space-y-5">
            {Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)}
          </div>
        ) : reflections.length > 0 ? (
          <div className="space-y-6">
            {reflections.map((r, i) => (
              <ReflectionCard
                key={r.id}
                reflection={r}
                index={i}
                onDelete={(id) => setDeleteId(id)}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No reflections yet"
            description="Generate your first AI reflection to get emotional insights from your journal entries."
          />
        )}
      </div>

      {/* Delete Modal */}
      <Modal isOpen={!!deleteId} onClose={() => setDeleteId(null)} title="Delete Reflection">
        <p className="text-base text-surface-500 mb-7">
          Are you sure you want to delete this reflection? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" onClick={() => setDeleteId(null)}>Cancel</Button>
          <Button variant="danger" loading={deleting} onClick={handleDelete}>Delete</Button>
        </div>
      </Modal>
    </div>
  );
}
