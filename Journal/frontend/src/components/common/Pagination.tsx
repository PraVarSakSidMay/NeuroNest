/* ──────────────────────────────────────────────────────────────
   Pagination — Page navigation with prev/next
   ────────────────────────────────────────────────────────────── */

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const totalPages = Math.ceil(total / pageSize);

  if (totalPages <= 1) return null;

  // Generate page numbers to show
  const pages: (number | "...")[] = [];
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= page - 1 && i <= page + 1)) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== "...") {
      pages.push("...");
    }
  }

  return (
    <div className="flex items-center justify-center gap-2 pt-8">
      {/* Prev */}
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="px-4 py-2.5 text-sm rounded-2xl bg-white text-surface-600 border border-surface-200 hover:bg-surface-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 cursor-pointer font-medium"
      >
        ← Prev
      </button>

      {/* Page numbers */}
      {pages.map((p, idx) =>
        p === "..." ? (
          <span key={`ellipsis-${idx}`} className="px-2 text-surface-400 text-base">…</span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`
              w-11 h-11 text-sm rounded-2xl font-semibold transition-all duration-200 cursor-pointer
              ${p === page
                ? "bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-md shadow-primary-500/20"
                : "bg-white text-surface-600 border border-surface-200 hover:bg-surface-50"
              }
            `}
          >
            {p}
          </button>
        )
      )}

      {/* Next */}
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="px-4 py-2.5 text-sm rounded-2xl bg-white text-surface-600 border border-surface-200 hover:bg-surface-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 cursor-pointer font-medium"
      >
        Next →
      </button>
    </div>
  );
}
