'use client'

import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { JournalEditor } from '@/components/journal'
import { createEntry } from '@/lib/journal-api'
import type { CreateEntryPayload } from '@/types/journal'

export default function CreateEntryPage() {
  const [isSaving, setIsSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleSave = async (payload: CreateEntryPayload) => {
    setIsSaving(true)
    setErrorMessage(null)

    try {
      await createEntry(payload)
      // Navigate to journal home on success
      window.location.href = '/journal'
    } catch (err) {
      setIsSaving(false)
      const message = err instanceof Error ? err.message : 'Something went wrong. Please try again.'
      setErrorMessage(message)
    }
  }

  return (
    // JournalEditor renders its own full-page gradient background.
    // We overlay the back button and error toast on top of it using
    // a relative wrapper so they appear within the same visual space.
    <div className="relative">
      {/* Back button — positioned above the editor card */}
      <div className="absolute top-0 left-0 right-0 z-10 max-w-2xl mx-auto px-4 pt-8">
        <a
          href="/journal"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-purple-500 hover:text-purple-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-purple-200 rounded-lg px-1"
        >
          ← Back
        </a>

        {/* Toast-like error message */}
        <AnimatePresence>
          {errorMessage && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
              className="mt-3 flex items-start gap-3 px-4 py-3 rounded-2xl bg-red-50 border border-red-100 text-sm text-red-600 shadow-sm"
            >
              <span className="flex-shrink-0 mt-0.5">⚠️</span>
              <span>{errorMessage}</span>
              <button
                type="button"
                onClick={() => setErrorMessage(null)}
                className="ml-auto flex-shrink-0 text-red-400 hover:text-red-600 transition-colors focus:outline-none"
                aria-label="Dismiss error"
              >
                ✕
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* The editor renders its own full-page gradient + card layout */}
      <JournalEditor
        onSave={handleSave}
        isSaving={isSaving}
      />
    </div>
  )
}
