'use client'

import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import type { CreateEntryPayload, MoodType } from '@/types/journal'

interface JournalEditorProps {
  onSave: (entry: CreateEntryPayload) => Promise<void>
  isSaving: boolean
  promptExamples?: string[]
}

const MOOD_OPTIONS: { value: MoodType; emoji: string; label: string }[] = [
  { value: 'calm', emoji: '😌', label: 'Calm' },
  { value: 'stressed', emoji: '😰', label: 'Stressed' },
  { value: 'tired', emoji: '😴', label: 'Tired' },
  { value: 'happy', emoji: '😊', label: 'Happy' },
  { value: 'anxious', emoji: '😟', label: 'Anxious' },
  { value: 'overwhelmed', emoji: '😵', label: 'Overwhelmed' },
]

const MAX_CHARS = 10_000
const WARN_THRESHOLD = 9_500

export function JournalEditor({ onSave, isSaving, promptExamples }: JournalEditorProps) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [mood, setMood] = useState<MoodType | undefined>(undefined)
  const [error, setError] = useState('')
  const [showSuccess, setShowSuccess] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const charCount = content.length
  const isContentEmpty = content.trim().length === 0
  const isOverLimit = charCount > MAX_CHARS

  const placeholder =
    promptExamples && promptExamples.length > 0
      ? promptExamples[0]
      : 'How was your day today? What\'s been on your mind lately?'

  const handleSave = async () => {
    if (isContentEmpty) {
      setError('Your reflection needs some words before saving.')
      textareaRef.current?.focus()
      return
    }
    if (isOverLimit) return

    setError('')

    try {
      setShowSuccess(true)
      // Brief success animation, then call onSave
      await new Promise<void>((resolve) => setTimeout(resolve, 800))
      await onSave({
        title: title.trim() || undefined,
        content: content.trim(),
        mood,
      })
    } catch {
      setShowSuccess(false)
      setError('Something went wrong saving your reflection. Please try again.')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 flex items-start justify-center p-6 pt-12">
      <div className="w-full max-w-2xl">
        {/* Card */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl shadow-purple-100/50 border border-purple-100/60 p-8 space-y-6">
          {/* Header */}
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-purple-900 tracking-tight">
              Today&apos;s Reflection
            </h1>
            <p className="text-sm text-purple-400">
              This is your private space. Write freely.
            </p>
          </div>

          {/* Title input */}
          <div>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Give your entry a title (optional)"
              maxLength={200}
              className={cn(
                'w-full bg-transparent border-0 border-b border-purple-100',
                'text-purple-800 placeholder-purple-300 text-base font-medium',
                'focus:outline-none focus:border-purple-300 transition-colors duration-200',
                'pb-2'
              )}
            />
          </div>

          {/* Mood selector */}
          <div className="space-y-2">
            <p className="text-xs font-medium text-purple-400 uppercase tracking-wider">
              How are you feeling?
            </p>
            <div className="flex flex-wrap gap-2">
              {MOOD_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setMood(mood === option.value ? undefined : option.value)}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium',
                    'transition-all duration-200 border',
                    mood === option.value
                      ? 'bg-gradient-to-r from-purple-400 to-pink-400 text-white border-transparent shadow-md shadow-purple-200'
                      : 'bg-white/60 text-purple-600 border-purple-100 hover:border-purple-300 hover:bg-purple-50'
                  )}
                >
                  <span>{option.emoji}</span>
                  <span>{option.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Textarea */}
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => {
                setContent(e.target.value)
                if (error && e.target.value.trim().length > 0) setError('')
              }}
              placeholder={placeholder}
              rows={10}
              style={{ minHeight: '300px' }}
              className={cn(
                'w-full resize-none rounded-2xl bg-purple-50/50 border border-purple-100',
                'text-purple-900 placeholder-purple-300 text-base leading-relaxed',
                'p-4 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-200',
                'transition-all duration-200',
                error ? 'border-red-200 focus:ring-red-100' : ''
              )}
            />

            {/* Character counter */}
            <div
              className={cn(
                'absolute bottom-3 right-3 text-xs font-medium tabular-nums',
                charCount >= WARN_THRESHOLD ? 'text-red-400' : 'text-purple-300'
              )}
            >
              {charCount.toLocaleString()}/{MAX_CHARS.toLocaleString()}
            </div>
          </div>

          {/* Inline error */}
          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.2 }}
                className="text-sm text-red-400 font-medium"
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>

          {/* Save button */}
          <div className="flex items-center justify-between pt-2">
            <p className="text-xs text-purple-300">
              Your words are private and encrypted.
            </p>

            <AnimatePresence mode="wait">
              {showSuccess ? (
                <motion.div
                  key="success"
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-green-400 to-emerald-400 text-white text-sm font-medium shadow-md shadow-green-200"
                >
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.1, type: 'spring', stiffness: 400 }}
                  >
                    ✓
                  </motion.span>
                  Saved!
                </motion.div>
              ) : (
                <motion.button
                  key="save"
                  initial={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  type="button"
                  onClick={handleSave}
                  disabled={isContentEmpty || isSaving || isOverLimit}
                  className={cn(
                    'px-6 py-2.5 rounded-full text-sm font-semibold transition-all duration-200',
                    'bg-gradient-to-r from-purple-500 to-pink-500 text-white',
                    'shadow-md shadow-purple-200 hover:shadow-lg hover:shadow-purple-300',
                    'hover:from-purple-600 hover:to-pink-600',
                    'disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none',
                    'focus:outline-none focus:ring-2 focus:ring-purple-300 focus:ring-offset-2'
                  )}
                >
                  {isSaving ? 'Saving…' : 'Save Reflection'}
                </motion.button>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}
