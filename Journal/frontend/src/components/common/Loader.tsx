/* ──────────────────────────────────────────────────────────────
   Loader — Skeleton and spinner loading indicators
   ────────────────────────────────────────────────────────────── */

/** Pulsing skeleton placeholder */
export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`skeleton-pulse rounded-xl ${className}`} />
  );
}

/** Card-shaped skeleton for journal/reflection cards */
export function CardSkeleton() {
  return (
    <div className="glass-card p-6 space-y-4">
      <Skeleton className="h-5 w-2/5" />
      <Skeleton className="h-4 w-4/5" />
      <Skeleton className="h-4 w-3/5" />
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-7 w-20 rounded-full" />
        <Skeleton className="h-7 w-24 rounded-full" />
      </div>
    </div>
  );
}

/** Full-page centered spinner */
export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="flex flex-col items-center gap-5">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-3 border-surface-200" />
          <div className="absolute inset-0 rounded-full border-3 border-primary-500 border-t-transparent animate-spin" />
        </div>
        <p className="text-base text-surface-500 animate-pulse font-medium">Loading...</p>
      </div>
    </div>
  );
}

/** Inline spinner */
export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <svg className="animate-spin" width={size} height={size} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
