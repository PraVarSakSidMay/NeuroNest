'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { fetchHistory, fetchSummaries, deleteEntry, deleteSummary } from '@/lib/journal-api'
import type { JournalEntry, EmotionalSummary } from '@/types/journal'

export default function JournalHomePage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'entries' | 'summaries'>('entries')
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [summaries, setSummaries] = useState<EmotionalSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadData() {
      try {
        const [entriesData, summariesData] = await Promise.all([
          fetchHistory(),
          fetchSummaries(),
        ])

        if (!cancelled) {
          setEntries(entriesData)
          setSummaries(summariesData)
        }
      } catch (err) {
        console.error('Error loading data:', err)
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadData()

    return () => {
      cancelled = true
    }
  }, [])

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const formatRangeLabel = (selectedRange: EmotionalSummary['selectedRange']): string => {
    if (!selectedRange) return 'Reflection'

    const preset = selectedRange.preset
    if (preset === '3d') return 'Last 3 Days'
    if (preset === '5d') return 'Last 5 Days'
    if (preset === '7d') return 'Last 7 Days'
    if (preset === '30d') return 'Last 30 Days'

    try {
      const start = new Date(selectedRange.startDate).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      })
      const end = new Date(selectedRange.endDate).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
      return `${start} – ${end}`
    } catch {
      return 'Custom Range'
    }
  }

  const handleDeleteEntry = async (entryId: string) => {
    if (!confirm('Are you sure you want to delete this journal entry?')) {
      return
    }

    setDeletingId(entryId)
    try {
      await deleteEntry(entryId)
      setEntries(entries.filter((e) => e.id !== entryId))
    } catch (err) {
      console.error('Error deleting entry:', err)
      alert('Failed to delete entry. Please try again.')
    } finally {
      setDeletingId(null)
    }
  }

  const handleDeleteSummary = async (summaryId: string) => {
    if (!confirm('Are you sure you want to delete this emotional summary?')) {
      return
    }

    setDeletingId(summaryId)
    try {
      await deleteSummary(summaryId)
      setSummaries(summaries.filter((s) => s.id !== summaryId))
    } catch (err) {
      console.error('Error deleting summary:', err)
      alert('Failed to delete summary. Please try again.')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50">
      <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
        {/* Welcome header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-purple-900 tracking-tight">
            Welcome back 🌸
          </h1>
          <p className="text-base text-purple-500">
            How have you been feeling lately?
          </p>
        </div>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={() => router.push('/journal/create')}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-2xl text-sm font-semibold text-white bg-gradient-to-r from-purple-500 to-pink-500 shadow-md shadow-purple-200 hover:shadow-lg hover:shadow-purple-300 hover:from-purple-600 hover:to-pink-600 transition-all duration-200"
          >
            <span>✏️</span>
            Write Today&apos;s Reflection
          </button>

          <button
            onClick={() => router.push('/journal/reflect')}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-2xl text-sm font-semibold text-purple-700 bg-white/70 backdrop-blur-sm border border-purple-100 shadow-sm hover:shadow-md hover:shadow-purple-100/50 hover:border-purple-300 hover:bg-purple-50 transition-all duration-200"
          >
            <span>✨</span>
            View Emotional Summary
          </button>
        </div>

        {/* Tabs */}
        <div className="space-y-4">
          <div className="flex gap-2 border-b border-purple-200">
            <button
              onClick={() => setActiveTab('entries')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'entries'
                  ? 'text-purple-700 border-b-2 border-purple-500'
                  : 'text-purple-400 hover:text-purple-600'
              }`}
            >
              Journal Entries ({entries.length})
            </button>
            <button
              onClick={() => setActiveTab('summaries')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'summaries'
                  ? 'text-purple-700 border-b-2 border-purple-500'
                  : 'text-purple-400 hover:text-purple-600'
              }`}
            >
              Emotional Summaries ({summaries.length})
            </button>
          </div>

          {/* Content */}
          {isLoading ? (
            <div className="text-center py-12 text-purple-400">
              Loading...
            </div>
          ) : (
            <div className="space-y-3">
              {activeTab === 'entries' && (
                <>
                  {entries.length === 0 ? (
                    <div className="text-center py-12 space-y-3">
                      <div className="text-5xl">🌱</div>
                      <p className="text-purple-400">No journal entries yet</p>
                      <p className="text-sm text-purple-300">
                        Start by writing your first reflection
                      </p>
                    </div>
                  ) : (
                    entries.map((entry) => (
                      <div
                        key={entry.id}
                        className="bg-white/60 backdrop-blur-sm rounded-2xl p-5 border border-purple-100 hover:shadow-md hover:border-purple-200 transition-all"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="text-lg font-semibold text-purple-900">
                            {entry.title || 'Untitled Entry'}
                          </h3>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-purple-400">
                              {formatDate(entry.createdAt)}
                            </span>
                            <button
                              onClick={() => handleDeleteEntry(entry.id)}
                              disabled={deletingId === entry.id}
                              className="text-red-400 hover:text-red-600 transition-colors disabled:opacity-50"
                              title="Delete entry"
                            >
                              {deletingId === entry.id ? '⏳' : '🗑️'}
                            </button>
                          </div>
                        </div>
                        <p className="text-purple-600 text-sm line-clamp-2">
                          {entry.content}
                        </p>
                        {entry.mood && (
                          <div className="mt-3">
                            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                              {entry.mood}
                            </span>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </>
              )}

              {activeTab === 'summaries' && (
                <>
                  {summaries.length === 0 ? (
                    <div className="text-center py-12 space-y-3">
                      <div className="text-5xl">✨</div>
                      <p className="text-purple-400">No emotional summaries yet</p>
                      <p className="text-sm text-purple-300">
                        Generate your first reflection summary
                      </p>
                    </div>
                  ) : (
                    summaries.map((summary) => (
                      <div
                        key={summary.id}
                        className="bg-gradient-to-br from-pink-50 to-purple-50 rounded-2xl p-5 border border-pink-200 hover:shadow-md hover:border-pink-300 transition-all"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="text-lg font-semibold text-pink-900 flex items-center gap-2">
                            <span>✨</span>
                            Emotional Reflection
                          </h3>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-pink-400">
                              {formatDate(summary.createdAt)}
                            </span>
                            <button
                              onClick={() => handleDeleteSummary(summary.id)}
                              disabled={deletingId === summary.id}
                              className="text-red-400 hover:text-red-600 transition-colors disabled:opacity-50"
                              title="Delete summary"
                            >
                              {deletingId === summary.id ? '⏳' : '🗑️'}
                            </button>
                          </div>
                        </div>
                        <p className="text-xs text-pink-500 mb-3">
                          {formatRangeLabel(summary.selectedRange)}
                        </p>
                        <p className="text-pink-700 text-sm line-clamp-3">
                          {summary.summaryText}
                        </p>
                        {summary.emotionalPatterns.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {summary.emotionalPatterns.slice(0, 3).map((pattern, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-pink-100 text-pink-700"
                              >
                                {pattern}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
