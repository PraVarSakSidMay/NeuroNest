'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import type { JournalEntryPreview, EmotionalSummaryPreview } from '@/types/journal'

interface JournalTimelineProps {
  entries: JournalEntryPreview[]
  summaries: EmotionalSummaryPreview[]
  onEntryClick: (id: string) => void
  onSummaryClick: (id: string) => void
  isLoading?: boolean
}

const MOOD_EMOJI: Record<string, string> = {
  calm: '😌',
  stressed: '😰',
  tired: '😴',
  happy: '😊',
  anxious: '😟',
  overwhelmed: '😵',
}

const PAGE_SIZE = 10

// ---------------------------------------------------------------------------
// Unified timeline item type
// ---------------------------------------------------------------------------

type TimelineItem =
  | { kind: 'entry'; data: JournalEntryPreview }
  | { kind: 'summary'; data: EmotionalSummaryPreview }

function getCreatedAt(item: TimelineItem): Date {
  return item.data.createdAt
}

// ---------------------------------------------------------------------------
// Skeleton card
// ---------------------------------------------------------------------------

function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-purple-100 bg-white/60 p-5 space-y-3 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-4 w-1/3 rounded-full bg-purple-100" />
        <div className="h-3 w-16 rounded-full bg-purple-50" />
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full rounded-full bg-purple-50" />
        <div className="h-3 w-4/5 rounded-full bg-purple-50" />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Entry card
// ---------------------------------------------------------------------------

function EntryCard({
  entry,
  onClick,
}: {
  entry: JournalEntryPreview
  onClick: () => void
}) {
  const snippet =
    entry.contentSnippet.length > 120
      ? entry.contentSnippet.slice(0, 120) + '…'
      : entry.contentSnippet

  const dateLabel = entry.createdAt.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ scale: 1.01 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className={cn(
        'w-full text-left rounded-2xl border p-5 space-y-2',
        'bg-white/70 backdrop-blur-sm',
        'border-purple-100 hover:border-purple-200',
        'shadow-sm hover:shadow-md hover:shadow-purple-100/50',
        'transition-shadow duration-200',
        'focus:outline-none focus:ring-2 focus:ring-purple-200 focus:ring-offset-1'
      )}
    >
      {/* Top row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {/* Lavender accent dot */}
          <div className="w-2 h-2 rounded-full bg-gradient-to-br from-purple-400 to-lavender-400 flex-shrink-0" />
          <span className="text-sm font-semibold text-purple-800 truncate">
            {entry.title || 'Untitled Reflection'}
          </span>
          {entry.mood && (
            <span className="text-base flex-shrink-0" title={entry.mood}>
              {MOOD_EMOJI[entry.mood] ?? ''}
            </span>
          )}
        </div>
        <span className="text-xs text-purple-300 flex-shrink-0 whitespace-nowrap">{dateLabel}</span>
      </div>

      {/* Snippet */}
      <p className="text-sm text-purple-600/80 leading-relaxed line-clamp-2">{snippet}</p>
    </motion.button>
  )
}

// ---------------------------------------------------------------------------
// Summary card
// ---------------------------------------------------------------------------

function SummaryCard({
  summary,
  onClick,
}: {
  summary: EmotionalSummaryPreview
  onClick: () => void
}) {
  const snippet =
    summary.summarySnippet.length > 120
      ? summary.summarySnippet.slice(0, 120) + '…'
      : summary.summarySnippet

  const dateLabel = summary.createdAt.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ scale: 1.01 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className={cn(
        'w-full text-left rounded-2xl border p-5 space-y-2',
        'bg-white/70 backdrop-blur-sm',
        'border-pink-100 hover:border-pink-200',
        'shadow-sm hover:shadow-md hover:shadow-pink-100/50',
        'transition-shadow duration-200',
        'focus:outline-none focus:ring-2 focus:ring-pink-200 focus:ring-offset-1'
      )}
    >
      {/* Top row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {/* Rose accent dot */}
          <div className="w-2 h-2 rounded-full bg-gradient-to-br from-pink-400 to-rose-400 flex-shrink-0" />
          <span className="text-sm font-semibold text-pink-800">✨ Emotional Reflection</span>
        </div>
        <span className="text-xs text-pink-300 flex-shrink-0 whitespace-nowrap">{dateLabel}</span>
      </div>

      {/* Range label */}
      <p className="text-xs font-medium text-pink-400">{summary.rangeLabel}</p>

      {/* Snippet */}
      <p className="text-sm text-pink-600/80 leading-relaxed line-clamp-2">{snippet}</p>
    </motion.button>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function JournalTimeline({
  entries,
  summaries,
  onEntryClick,
  onSummaryClick,
  isLoading,
}: JournalTimelineProps) {
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)

  // Merge and sort descending by createdAt
  const allItems: TimelineItem[] = [
    ...entries.map((e): TimelineItem => ({ kind: 'entry', data: e })),
    ...summaries.map((s): TimelineItem => ({ kind: 'summary', data: s })),
  ].sort((a, b) => getCreatedAt(b).getTime() - getCreatedAt(a).getTime())

  const visibleItems = allItems.slice(0, visibleCount)
  const hasMore = visibleCount < allItems.length

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-3">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  // Empty state
  if (allItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center space-y-3">
        <span className="text-4xl">🌱</span>
        <p className="text-base text-purple-500 font-medium leading-relaxed max-w-xs">
          Your journal is waiting for its first entry. Start writing today 🌱
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {visibleItems.map((item) => {
        if (item.kind === 'entry') {
          return (
            <EntryCard
              key={`entry-${item.data.id}`}
              entry={item.data}
              onClick={() => onEntryClick(item.data.id)}
            />
          )
        }
        return (
          <SummaryCard
            key={`summary-${item.data.id}`}
            summary={item.data}
            onClick={() => onSummaryClick(item.data.id)}
          />
        )
      })}

      {/* Load more */}
      {hasMore && (
        <div className="flex justify-center pt-2">
          <button
            type="button"
            onClick={() => setVisibleCount((c) => c + PAGE_SIZE)}
            className={cn(
              'px-6 py-2.5 rounded-full text-sm font-medium',
              'bg-white/70 backdrop-blur-sm border border-purple-100',
              'text-purple-600 hover:text-purple-800 hover:border-purple-300 hover:bg-purple-50',
              'transition-all duration-200 shadow-sm hover:shadow-md hover:shadow-purple-100/50',
              'focus:outline-none focus:ring-2 focus:ring-purple-200 focus:ring-offset-1'
            )}
          >
            Load more
          </button>
        </div>
      )}
    </div>
  )
}
