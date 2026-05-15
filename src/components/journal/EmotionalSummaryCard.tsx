'use client'

import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { DIAGNOSTIC_LANGUAGE_BLOCKLIST } from '@/types/journal'
import type { EmotionalSummary } from '@/types/journal'

interface EmotionalSummaryCardProps {
  summary: EmotionalSummary
  isLoading: boolean
}

/**
 * Replaces any diagnostic language blocklist terms in a string with "...".
 * Case-insensitive matching.
 */
function sanitizeText(text: string): string {
  let result = text
  for (const term of DIAGNOSTIC_LANGUAGE_BLOCKLIST) {
    // Escape special regex characters in the term
    const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    result = result.replace(new RegExp(escaped, 'gi'), '...')
  }
  return result
}

function sanitizeArray(items: string[]): string[] {
  return items.map(sanitizeText)
}

// ---------------------------------------------------------------------------
// Skeleton loading state
// ---------------------------------------------------------------------------

function SkeletonLine({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'h-4 rounded-full bg-gradient-to-r from-purple-100 via-pink-100 to-purple-100',
        'animate-pulse bg-[length:200%_100%]',
        className
      )}
    />
  )
}

function SummaryCardSkeleton() {
  return (
    <div className="bg-white/70 backdrop-blur-sm rounded-3xl border border-purple-100/60 p-8 space-y-6 shadow-xl shadow-purple-100/40">
      {/* Header skeleton */}
      <div className="space-y-2">
        <SkeletonLine className="w-1/3" />
        <SkeletonLine className="w-1/2 h-3" />
      </div>

      {/* Summary text skeleton */}
      <div className="space-y-2">
        <SkeletonLine className="w-full" />
        <SkeletonLine className="w-5/6" />
        <SkeletonLine className="w-4/6" />
      </div>

      {/* Patterns skeleton */}
      <div className="flex flex-wrap gap-2">
        {[80, 100, 70, 90].map((w, i) => (
          <div
            key={i}
            className="h-7 rounded-full bg-purple-100 animate-pulse"
            style={{ width: `${w}px` }}
          />
        ))}
      </div>

      {/* Sections skeleton */}
      <div className="space-y-3">
        <SkeletonLine className="w-1/4 h-3" />
        <SkeletonLine className="w-full" />
        <SkeletonLine className="w-3/4" />
      </div>
      <div className="space-y-3">
        <SkeletonLine className="w-1/4 h-3" />
        <SkeletonLine className="w-full" />
        <SkeletonLine className="w-2/3" />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function EmotionalSummaryCard({ summary, isLoading }: EmotionalSummaryCardProps) {
  if (isLoading) {
    return <SummaryCardSkeleton />
  }

  const summaryText = sanitizeText(summary.summaryText)
  const emotionalPatterns = sanitizeArray(summary.emotionalPatterns)
  const positiveObservations = sanitizeArray(summary.positiveObservations)
  const gentleInsights = sanitizeArray(summary.gentleInsights)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className={cn(
        'relative overflow-hidden rounded-3xl p-8 space-y-6',
        // Glassmorphism
        'bg-white/70 backdrop-blur-md',
        // Soft gradient border via box-shadow + pseudo-border trick
        'border border-white/80',
        'shadow-xl shadow-purple-100/50',
        // Subtle gradient overlay
        'before:absolute before:inset-0 before:rounded-3xl',
        'before:bg-gradient-to-br before:from-purple-50/40 before:via-transparent before:to-pink-50/40',
        'before:pointer-events-none'
      )}
    >
      {/* Header */}
      <div className="relative space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-xl">✨</span>
          <h2 className="text-xl font-semibold text-purple-900 tracking-tight">
            Your Emotional Reflection
          </h2>
        </div>
        {summary.selectedRange && (
          <p className="text-xs text-purple-400 font-medium">
            {new Date(summary.selectedRange.startDate).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            })}{' '}
            –{' '}
            {new Date(summary.selectedRange.endDate).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            })}
          </p>
        )}
      </div>

      {/* Summary text */}
      <div className="relative">
        <p className="text-lg text-purple-800 leading-relaxed font-light">{summaryText}</p>
      </div>

      {/* Emotional patterns */}
      {emotionalPatterns.length > 0 && (
        <div className="relative space-y-3">
          <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider">
            Emotional Patterns
          </p>
          <div className="flex flex-wrap gap-2">
            {emotionalPatterns.map((pattern, i) => (
              <span
                key={i}
                className={cn(
                  'px-3 py-1 rounded-full text-sm font-medium',
                  'bg-gradient-to-r from-purple-100 to-pink-100',
                  'text-purple-700 border border-purple-100'
                )}
              >
                {pattern}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Positive observations */}
      {positiveObservations.length > 0 && (
        <div className="relative space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-1 h-4 rounded-full bg-gradient-to-b from-teal-400 to-green-400" />
            <p className="text-xs font-semibold text-teal-600 uppercase tracking-wider">
              Positive Observations
            </p>
          </div>
          <ul className="space-y-2">
            {positiveObservations.map((obs, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-teal-800 leading-relaxed">
                <span className="mt-0.5 text-teal-400 flex-shrink-0">🌿</span>
                <span>{obs}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Gentle insights */}
      {gentleInsights.length > 0 && (
        <div className="relative space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-1 h-4 rounded-full bg-gradient-to-b from-amber-400 to-orange-400" />
            <p className="text-xs font-semibold text-amber-600 uppercase tracking-wider">
              Gentle Insights
            </p>
          </div>
          <ul className="space-y-2">
            {gentleInsights.map((insight, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-amber-800 leading-relaxed">
                <span className="mt-0.5 text-amber-400 flex-shrink-0">🕯️</span>
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  )
}
