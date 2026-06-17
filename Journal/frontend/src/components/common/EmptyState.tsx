/* ──────────────────────────────────────────────────────────────
   EmptyState — Illustrated empty content placeholder
   ────────────────────────────────────────────────────────────── */
import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center justify-center py-20 px-4 text-center"
    >
      {/* Default icon if none provided */}
      {icon || (
        <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center mb-6 shadow-sm">
          <svg className="w-12 h-12 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12H9.75m3 0l-3-3m3 3l-3 3M3.375 7.5h3.75c.621 0 1.125-.504 1.125-1.125V2.625" />
          </svg>
        </div>
      )}

      <h3 className="text-2xl font-bold text-surface-800 mb-3">{title}</h3>
      {description && (
        <p className="text-base text-surface-500 max-w-md mb-8">{description}</p>
      )}
      {action && <div>{action}</div>}
    </motion.div>
  );
}
