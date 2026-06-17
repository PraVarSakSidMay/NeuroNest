/* ──────────────────────────────────────────────────────────────
   ToastContainer — Renders toast notifications from AppContext
   ────────────────────────────────────────────────────────────── */
import { motion, AnimatePresence } from "framer-motion";
import { useAppContext } from "../../context/AppContext";

const typeStyles = {
  success: "border-success-200 bg-success-50 text-success-700",
  error: "border-danger-200 bg-danger-50 text-danger-700",
  info: "border-primary-200 bg-primary-50 text-primary-700",
};

const typeIcons = {
  success: "✓",
  error: "✕",
  info: "ℹ",
};

export default function ToastContainer() {
  const { toasts, dismissToast } = useAppContext();

  return (
    <div className="fixed bottom-6 right-6 z-[60] flex flex-col gap-3 max-w-md w-full pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 350, damping: 25 }}
            className={`
              pointer-events-auto flex items-center gap-4
              px-5 py-4 rounded-2xl border backdrop-blur-xl
              shadow-lg text-sm font-semibold
              ${typeStyles[toast.type]}
            `}
          >
            <span className="text-xl flex-shrink-0">{typeIcons[toast.type]}</span>
            <span className="flex-1">{toast.message}</span>
            <button
              onClick={() => dismissToast(toast.id)}
              className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity cursor-pointer p-1 rounded-full hover:bg-black/5"
            >
              ✕
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
