'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { ReflectionRange, RangePreset } from '@/types/journal'

interface ReflectionRangeSelectorProps {
  onSelect: (range: ReflectionRange) => void
  isLoading?: boolean
}

const PRESET_OPTIONS: { value: RangePreset; label: string; days?: number }[] = [
  { value: '3d', label: 'Last 3 Days', days: 3 },
  { value: '5d', label: 'Last 5 Days', days: 5 },
  { value: '7d', label: 'Last 7 Days', days: 7 },
  { value: '30d', label: 'Last 30 Days', days: 30 },
  { value: 'custom', label: 'Custom' },
]

function subtractDays(date: Date, days: number): Date {
  const result = new Date(date)
  result.setDate(result.getDate() - days)
  return result
}

function toDateInputValue(date: Date): string {
  return date.toISOString().split('T')[0]
}

export function ReflectionRangeSelector({ onSelect, isLoading }: ReflectionRangeSelectorProps) {
  const [selected, setSelected] = useState<RangePreset | null>(null)
  const [customStart, setCustomStart] = useState('')
  const [customEnd, setCustomEnd] = useState('')
  const [customError, setCustomError] = useState('')

  const handlePresetClick = (preset: RangePreset, days?: number) => {
    setSelected(preset)
    setCustomError('')

    if (preset !== 'custom' && days !== undefined) {
      const now = new Date()
      const start = subtractDays(now, days)
      onSelect({ preset, startDate: start, endDate: now })
    }
  }

  const handleCustomGenerate = () => {
    setCustomError('')

    if (!customStart || !customEnd) {
      setCustomError('Please select both a start and end date.')
      return
    }

    const start = new Date(customStart)
    const end = new Date(customEnd)

    // Set end to end of day for inclusive range
    end.setHours(23, 59, 59, 999)

    if (start > end) {
      setCustomError('Start date must be before end date.')
      return
    }

    onSelect({ preset: 'custom', startDate: start, endDate: end })
  }

  const today = toDateInputValue(new Date())

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl shadow-purple-100/50 border border-purple-100/60 p-8 space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <h2 className="text-xl font-semibold text-purple-900 tracking-tight">
          Choose a Reflection Period
        </h2>
        <p className="text-sm text-purple-400">
          Select a time window to generate your emotional reflection.
        </p>
      </div>

      {/* Preset buttons */}
      <div className="flex flex-wrap gap-2">
        {PRESET_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => handlePresetClick(option.value, option.days)}
            disabled={isLoading}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 border',
              'focus:outline-none focus:ring-2 focus:ring-purple-200 focus:ring-offset-1',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              selected === option.value
                ? 'bg-gradient-to-r from-purple-400 to-pink-400 text-white border-transparent shadow-md shadow-purple-200'
                : 'bg-white/60 text-purple-600 border-purple-100 hover:border-purple-300 hover:bg-purple-50'
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* Custom date picker */}
      {selected === 'custom' && (
        <div className="space-y-4 pt-2 border-t border-purple-50">
          <p className="text-sm font-medium text-purple-500">Select your custom date range</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-purple-400 uppercase tracking-wider">
                Start Date
              </label>
              <input
                type="date"
                value={customStart}
                max={customEnd || today}
                onChange={(e) => {
                  setCustomStart(e.target.value)
                  setCustomError('')
                }}
                className={cn(
                  'w-full rounded-xl border border-purple-100 bg-purple-50/50',
                  'text-purple-800 text-sm px-3 py-2',
                  'focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-200',
                  'transition-all duration-200'
                )}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-purple-400 uppercase tracking-wider">
                End Date
              </label>
              <input
                type="date"
                value={customEnd}
                min={customStart || undefined}
                max={today}
                onChange={(e) => {
                  setCustomEnd(e.target.value)
                  setCustomError('')
                }}
                className={cn(
                  'w-full rounded-xl border border-purple-100 bg-purple-50/50',
                  'text-purple-800 text-sm px-3 py-2',
                  'focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-200',
                  'transition-all duration-200'
                )}
              />
            </div>
          </div>

          {/* Validation error */}
          {customError && (
            <p className="text-sm text-red-400 font-medium">{customError}</p>
          )}

          {/* Generate button */}
          <button
            type="button"
            onClick={handleCustomGenerate}
            disabled={isLoading || !customStart || !customEnd}
            className={cn(
              'w-full py-2.5 rounded-xl text-sm font-semibold transition-all duration-200',
              'bg-gradient-to-r from-purple-500 to-pink-500 text-white',
              'shadow-md shadow-purple-200 hover:shadow-lg hover:shadow-purple-300',
              'hover:from-purple-600 hover:to-pink-600',
              'disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none',
              'focus:outline-none focus:ring-2 focus:ring-purple-300 focus:ring-offset-2'
            )}
          >
            {isLoading ? 'Generating…' : 'Generate Reflection'}
          </button>
        </div>
      )}
    </div>
  )
}
