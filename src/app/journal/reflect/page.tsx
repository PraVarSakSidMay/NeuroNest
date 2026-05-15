'use client'

import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ReflectionRangeSelector, EmotionalSummaryCard } from '@/components/journal'
import { generateSummary } from '@/lib/journal-api'
import type { EmotionalSummary, ReflectionRange } from '@/types/journal'

// A placeholder summary object used while loading so EmotionalSummaryCard
// receives a valid (but unused) summary prop alongside isLoading=true.
const LOADING_PLACEHOLDER: EmotionalSummary = {
  id: '',
  userId: '',
  selectedRange: { preset: '7d', startDate: '', endDate: '' },
  summaryText: '',
  emotionalPatterns: [],
  positiveObservations: [],
  gentleInsights: [],
  createdAt: new Date(),
}

export default function ReflectPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [summary, setSummary] = useState<EmotionalSummary | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSelect = async (range: ReflectionRange) => {
    setIsLoading(true)
    setSummary(null)
    setError(null)

    try {
      const result = await generateSummary(range)
      setSummary(result)
    } catch (err) {
      const message = err instanceof Error ? err.message : ''

      if (message.includes('404') || message.toLowerCase().includes('no entries found')) {
        setError('No entries found for this period. Try writing a few reflections first.')
      } else if (message.includes('503') || message.toLowerCase().includes('unavailable')) {
        setError(
          "We couldn't generate your reflection right now. Your entries are safe — please try again in a moment."
        )
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setSummary(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50">
      <div className="max-w-2xl mx-auto px-4 pt-8 pb-12 space-y-8">
        {/* Back button */}
        <a
          href="/journal"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-purple-500 hover:text-purple-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-purple-200 rounded-lg px-1"
        >
          ← Back
        </a>

        {/* Page header */}
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold text-purple-900 tracking-tight">
            Your Emotional Reflection 🌙
          </h1>
          <p className="text-base text-purple-500">
            Choose a time period and let the AI gently reflect on your journey.
          </p>
        </div>

        {/* Range selector */}
        <ReflectionRangeSelector
          onSelect={handleSelect}
          isLoading={isLoading}
        />

        {/* Loading state */}
        <AnimatePresence>
          {isLoading && (
            <motion.div
              key="loading"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              transition={{ duration: 0.3 }}
            >
              <EmotionalSummaryCard
                summary={LOADING_PLACEHOLDER}
                isLoading={true}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Summary result */}
        <AnimatePresence>
          {!isLoading && summary && (
            <motion.div
              key="summary"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              transition={{ duration: 0.3 }}
            >
              <EmotionalSummaryCard
                summary={summary}
                isLoading={false}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error state */}
        <AnimatePresence>
          {!isLoading && error && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              transition={{ duration: 0.3 }}
              className="rounded-3xl bg-white/70 backdrop-blur-sm border border-rose-100 shadow-xl shadow-rose-100/40 p-8 space-y-4"
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl flex-shrink-0">🌿</span>
                <p className="text-base text-rose-700 leading-relaxed">{error}</p>
              </div>
              <button
                type="button"
                onClick={handleReset}
                className="px-5 py-2.5 rounded-full text-sm font-semibold text-purple-700 bg-white/80 border border-purple-100 hover:border-purple-300 hover:bg-purple-50 shadow-sm hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:ring-offset-2"
              >
                Try again
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
