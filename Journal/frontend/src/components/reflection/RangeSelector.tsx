/* ──────────────────────────────────────────────────────────────
   RangeSelector — Date range picker for reflections
   ────────────────────────────────────────────────────────────── */
import { motion } from "framer-motion";
import { ALL_RANGES, RANGE_LABELS, type RangeType } from "../../types/reflection";

interface RangeSelectorProps {
  value: RangeType;
  onChange: (range: RangeType) => void;
  startDate?: string;
  endDate?: string;
  onStartDateChange?: (date: string) => void;
  onEndDateChange?: (date: string) => void;
}

export default function RangeSelector({
  value,
  onChange,
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
}: RangeSelectorProps) {
  return (
    <div className="space-y-5">
      <label className="text-sm font-semibold text-surface-700">Select Reflection Period</label>

      <div className="flex flex-wrap gap-2.5">
        {ALL_RANGES.map((range) => {
          const isSelected = value === range;
          return (
            <motion.button
              key={range}
              type="button"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => onChange(range)}
              className={`
                px-5 py-2.5 rounded-2xl text-sm font-semibold transition-all duration-300 cursor-pointer border-2
                ${isSelected
                  ? "bg-gradient-to-r from-primary-500 to-accent-500 border-transparent text-white shadow-md shadow-primary-500/20"
                  : "bg-white border-surface-200 text-surface-600 hover:bg-surface-50"
                }
              `}
            >
              {RANGE_LABELS[range]}
            </motion.button>
          );
        })}
      </div>

      {/* Custom date inputs */}
      {value === "custom" && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="flex flex-col sm:flex-row gap-4"
        >
          <div className="flex-1">
            <label className="block text-sm text-surface-600 mb-2 font-medium">Start Date</label>
            <input
              type="date"
              value={startDate || ""}
              onChange={(e) => onStartDateChange?.(e.target.value)}
              className="w-full px-4 py-3 bg-white border border-surface-200 rounded-2xl text-surface-800 text-sm focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-400 transition-all duration-300"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm text-surface-600 mb-2 font-medium">End Date</label>
            <input
              type="date"
              value={endDate || ""}
              onChange={(e) => onEndDateChange?.(e.target.value)}
              className="w-full px-4 py-3 bg-white border border-surface-200 rounded-2xl text-surface-800 text-sm focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-400 transition-all duration-300"
            />
          </div>
        </motion.div>
      )}
    </div>
  );
}
