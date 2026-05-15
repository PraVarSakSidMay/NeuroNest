"use client";

import { useState, useEffect } from "react";
import { Plus, Tag, Calendar, X, BookOpen, Loader2 } from "lucide-react";
import { api, type JournalEntry } from "@/lib/api";
import { cn } from "@/lib/utils";

const moods = [
  { emoji: "😄", label: "Great" },
  { emoji: "🙂", label: "Good"  },
  { emoji: "😐", label: "Okay"  },
  { emoji: "😔", label: "Low"   },
  { emoji: "😢", label: "Rough" },
];

const ic = "w-full px-5 py-3.5 rounded-2xl border-2 border-gray-200 bg-gray-50/80 text-[15px] text-gray-800 placeholder:text-gray-400 outline-none focus:border-violet-400 focus:bg-white transition-all duration-200";

export default function JournalPage() {
  const [entries, setEntries]   = useState<JournalEntry[]>([]);
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [title, setTitle]       = useState("");
  const [content, setContent]   = useState("");
  const [mood, setMood]         = useState<number | null>(null);
  const [tag, setTag]           = useState("");
  const [tags, setTags]         = useState<string[]>([]);

  // Load entries from Supabase on mount
  useEffect(() => {
    api.user.getJournals()
      .then(data => setEntries(data))
      .catch(e => console.error("Failed to load journals:", e))
      .finally(() => setLoading(false));
  }, []);

  function addTag() {
    if (tag.trim() && !tags.includes(tag.trim())) {
      setTags(p => [...p, tag.trim()]);
      setTag("");
    }
  }

  async function save() {
    if (!title.trim() || !content.trim()) return;
    setSaving(true);
    setSaveError(null);
    try {
      const newEntry = await api.user.createJournal({
        title,
        content,
        mood:      mood !== null ? moods[mood].emoji : "😐",
        moodLabel: mood !== null ? moods[mood].label : "Okay",
        tags,
      });
      // Prepend to list (newest first)
      setEntries(p => [newEntry, ...p]);
      // Reset form
      setTitle(""); setContent(""); setMood(null); setTags([]); setShowForm(false);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "Failed to save entry.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-10">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[1.75rem] font-bold text-gray-900">My Journal 📓</h1>
          <p className="text-base text-gray-500 mt-1.5">Your private space to reflect and heal</p>
        </div>
        <button
          onClick={() => { setShowForm(v => !v); setSaveError(null); }}
          style={{
            display: "flex", alignItems: "center", gap: "8px",
            padding: "12px 24px", borderRadius: "14px", border: "none",
            background: "linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)",
            color: "#fff", fontSize: "15px", fontWeight: 600, cursor: "pointer",
          }}>
          <Plus size={17} /> New Entry
        </button>
      </div>

      {/* New entry form */}
      {showForm && (
        <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-8 space-y-6">
          <h3 className="text-lg font-semibold text-gray-900">New Journal Entry</h3>

          <input
            className={ic}
            placeholder="Entry title..."
            value={title}
            onChange={e => setTitle(e.target.value)}
          />

          <div>
            <p className="text-sm font-semibold text-gray-600 mb-3">How are you feeling?</p>
            <div className="flex gap-3">
              {moods.map((m, i) => (
                <button key={i} onClick={() => setMood(i)}
                  className={cn(
                    "flex-1 flex flex-col items-center gap-2 py-4 rounded-2xl border-2 transition-all text-sm font-medium",
                    mood === i
                      ? "border-violet-400 bg-violet-50 text-violet-700"
                      : "border-transparent hover:bg-gray-50 text-gray-500"
                  )}>
                  <span className="text-2xl">{m.emoji}</span>
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <textarea
            className={cn(ic, "resize-none")}
            rows={5}
            placeholder="Write your thoughts, feelings, reflections..."
            value={content}
            onChange={e => setContent(e.target.value)}
          />

          <div>
            <p className="text-sm font-semibold text-gray-600 mb-3">Tags</p>
            <div className="flex flex-wrap gap-2 mb-3">
              {tags.map(t => (
                <span key={t} className="flex items-center gap-1.5 bg-violet-50 text-violet-700 text-sm px-3.5 py-1.5 rounded-full font-medium">
                  #{t}
                  <button onClick={() => setTags(p => p.filter(x => x !== t))} className="hover:text-red-500 transition-colors">
                    <X size={12} />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-3">
              <input
                className={cn(ic, "flex-1")}
                placeholder="e.g. anxiety, gratitude"
                value={tag}
                onChange={e => setTag(e.target.value)}
                onKeyDown={e => e.key === "Enter" && addTag()}
              />
              <button onClick={addTag} className="px-5 py-3.5 rounded-2xl border-2 border-violet-400 text-violet-600 text-sm font-semibold hover:bg-violet-50 transition-colors">
                Add
              </button>
            </div>
          </div>

          {/* Save error */}
          {saveError && (
            <p style={{
              fontSize: "14px", color: "#ef4444", background: "#fef2f2",
              border: "1px solid #fecaca", borderRadius: "10px",
              padding: "10px 14px", textAlign: "center",
            }}>
              ⚠ {saveError}
            </p>
          )}

          <div className="flex gap-4 pt-1">
            <button
              onClick={() => { setShowForm(false); setSaveError(null); }}
              className="flex-1 py-3.5 rounded-2xl border-2 border-gray-200 text-gray-600 text-[15px] font-semibold hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={save}
              disabled={saving || !title.trim() || !content.trim()}
              style={{
                flex: 1, height: "52px", borderRadius: "14px", border: "none",
                background: "linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)",
                color: "#fff", fontSize: "15px", fontWeight: 600,
                cursor: saving ? "not-allowed" : "pointer",
                opacity: saving ? 0.7 : 1,
                display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
              }}>
              {saving ? <><Loader2 size={16} className="animate-spin" /> Saving...</> : "Save Entry"}
            </button>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-20 text-gray-400 gap-3">
          <Loader2 size={24} className="animate-spin" />
          <p className="text-base">Loading your journal...</p>
        </div>
      )}

      {/* Entries list */}
      {!loading && (
        <div className="space-y-5">
          {entries.map(entry => (
            <div key={entry.id} className="bg-white rounded-3xl border border-gray-100 shadow-sm p-7 hover:shadow-md transition-shadow duration-200">
              <div className="flex items-start gap-5">
                <div className="w-14 h-14 rounded-2xl bg-violet-50 flex items-center justify-center text-3xl shrink-0">
                  {entry.mood}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <h4 className="text-lg font-semibold text-gray-900">{entry.title}</h4>
                    <div className="text-right shrink-0">
                      <p className="text-sm text-gray-400 flex items-center gap-1.5 justify-end">
                        <Calendar size={12} /> {entry.date}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">{entry.time}</p>
                    </div>
                  </div>
                  <p className="text-[15px] text-gray-600 mt-2 leading-relaxed line-clamp-2">{entry.content}</p>
                  <div className="flex flex-wrap items-center gap-2 mt-4">
                    <span className="text-xs bg-violet-50 text-violet-600 px-3 py-1 rounded-full font-semibold">
                      {entry.moodLabel}
                    </span>
                    {entry.tags.map(t => (
                      <span key={t} className="flex items-center gap-1 bg-gray-100 text-gray-500 text-xs px-3 py-1 rounded-full">
                        <Tag size={9} /> {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && entries.length === 0 && (
        <div className="text-center py-20 text-gray-400">
          <BookOpen size={44} className="mx-auto mb-4 opacity-25" />
          <p className="font-semibold text-base">No journal entries yet</p>
          <p className="text-sm mt-1">Start writing your first entry above</p>
        </div>
      )}
    </div>
  );
}
