"use client";

import { useState, useEffect } from "react";
import { Brain, ArrowLeft, Loader2, Lock, MessageSquare, RefreshCw, Shield } from "lucide-react";
import Link from "next/link";
import { getOrCreateUserId } from "@/lib/api";

interface HistoryMessage { role: string; content: string; }
interface SessionHistory { session_id: string; user_id: string; messages: HistoryMessage[]; total: number; }
interface VerifyMessage {
  row_id: string; role: string; emotion: string;
  stored_in_db_raw: string; looks_encrypted: boolean;
  decrypt_status: string; decrypted_preview: string; created_at: string;
}
interface EncryptionVerification {
  session_id: string; total_messages: number;
  encryption_algorithm: string; key_derivation: string;
  all_encrypted: boolean; messages: VerifyMessage[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString(undefined, {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit", hour12: true,
    });
  } catch { return ts; }
}

export default function HistoryPage() {
  const [userId, setUserId]       = useState("");
  const [sessionId, setSessionId] = useState("");
  const [history, setHistory]     = useState<SessionHistory | null>(null);
  const [verification, setVerification] = useState<EncryptionVerification | null>(null);
  const [loading, setLoading]     = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"history" | "verify">("history");

  // Auto-load the user's ID from localStorage on mount
  useEffect(() => {
    const id = getOrCreateUserId();
    setUserId(id);
  }, []);

  const fetchHistory = async () => {
    if (!userId.trim() || !sessionId.trim()) {
      setError("Please enter a Session ID (User ID is auto-filled)");
      return;
    }
    setLoading(true);
    setError(null);
    setHistory(null);
    setVerification(null);
    setActiveTab("history");
    try {
      const res = await fetch(
        `${API_BASE}/api/db/history/${encodeURIComponent(sessionId)}?user_id=${encodeURIComponent(userId)}`
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      setHistory(await res.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to fetch history");
    } finally { setLoading(false); }
  };

  const verifyEncryption = async () => {
    if (!userId.trim() || !sessionId.trim()) {
      setError("Please enter a Session ID (User ID is auto-filled)");
      return;
    }
    setVerifying(true);
    setError(null);
    setHistory(null);
    setVerification(null);
    setActiveTab("verify");
    try {
      const res = await fetch(
        `${API_BASE}/api/db/verify/${encodeURIComponent(sessionId)}?user_id=${encodeURIComponent(userId)}`
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      setVerification(await res.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to verify encryption");
    } finally { setVerifying(false); }
  };

  return (
    <div className="min-h-screen bg-[#0f0f1a] text-slate-100">
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-teal-600/10 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center gap-4 px-6 py-4 border-b border-white/10 bg-slate-900/60 backdrop-blur-sm">
        <Link href="/" className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all">
          <ArrowLeft size={18} />
        </Link>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-teal-500 flex items-center justify-center">
            <Brain size={16} className="text-white" />
          </div>
          <div>
            <h1 className="text-white font-bold text-sm">NeuroNest — Chat History</h1>
            <p className="text-slate-500 text-xs flex items-center gap-1">
              <Lock size={10} /> AES-256-GCM End-to-End Encrypted
            </p>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-3xl mx-auto px-4 py-8">

        {/* How to find session ID */}
        <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4 mb-6">
          <p className="text-indigo-300 text-xs font-semibold mb-1">💡 How to find your Session ID</p>
          <p className="text-slate-400 text-xs">
            After sending a message in the chat, the session ID is returned in the API response.
            You can also check the browser console or use the session ID from the chat URL.
            For testing, use <code className="text-teal-300 bg-black/20 px-1 rounded">test-session-001</code> after sending a message via Swagger.
          </p>
        </div>

        {/* Input section */}
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 mb-6">
          <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
            <MessageSquare size={16} className="text-purple-400" />
            Retrieve Conversation
          </h2>

          <div className="space-y-3">
            {/* User ID — auto-filled, read-only */}
            <div>
              <label className="text-xs text-slate-400 mb-1 block flex items-center gap-1">
                <Lock size={10} className="text-teal-400" />
                Your User ID (auto-filled from your browser)
              </label>
              <div className="flex gap-2">
                <input
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="Loading..."
                  className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-teal-300 font-mono placeholder-slate-500 focus:outline-none focus:border-teal-500/50 transition-colors"
                />
                <button
                  onClick={() => setUserId(getOrCreateUserId())}
                  className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                  title="Reset to your stored user ID"
                >
                  <RefreshCw size={14} />
                </button>
              </div>
              <p className="text-xs text-slate-600 mt-1">This ID is stored in your browser and used to encrypt/decrypt your data</p>
            </div>

            {/* Session ID */}
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Session ID</label>
              <input
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                placeholder="e.g. test-session-001 or the session_id from chat response"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500/50 transition-colors"
              />
            </div>
          </div>

          {error && (
            <p className="text-red-400 text-xs mt-3 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              ⚠️ {error}
            </p>
          )}

          <div className="flex gap-2 mt-4">
            <button
              onClick={fetchHistory}
              disabled={loading || verifying}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <MessageSquare size={14} />}
              View History
            </button>
            <button
              onClick={verifyEncryption}
              disabled={loading || verifying}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-teal-600/80 hover:bg-teal-500 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              {verifying ? <Loader2 size={14} className="animate-spin" /> : <Shield size={14} />}
              Verify Encryption
            </button>
          </div>
        </div>

        {/* ── History view ─────────────────────────────────────────────────── */}
        {activeTab === "history" && history && (
          <div className="space-y-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-white font-semibold">
                {history.total} message{history.total !== 1 ? "s" : ""}
                <span className="text-slate-500 font-normal text-sm ml-2">
                  Session: <span className="text-purple-400 font-mono">{history.session_id}</span>
                </span>
              </h3>
              <span className="text-xs text-teal-400 flex items-center gap-1">
                <Lock size={10} /> Decrypted for you only
              </span>
            </div>

            {history.messages.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <MessageSquare size={32} className="mx-auto mb-3 opacity-30" />
                <p>No messages found for this session.</p>
                <p className="text-xs mt-1">Make sure you sent messages with this session_id.</p>
              </div>
            ) : (
              history.messages.map((msg, i) => (
                <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                  <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold
                    ${msg.role === "user"
                      ? "bg-gradient-to-br from-purple-500 to-pink-500 text-white"
                      : "bg-gradient-to-br from-teal-500 to-cyan-500 text-white"
                    }`}
                  >
                    {msg.role === "user" ? "U" : "N"}
                  </div>
                  <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed
                    ${msg.role === "user"
                      ? "bg-gradient-to-br from-purple-600 to-purple-700 text-white rounded-tr-sm"
                      : "bg-white/8 border border-white/10 text-slate-100 rounded-tl-sm"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* ── Encryption verification view ─────────────────────────────────── */}
        {activeTab === "verify" && verification && (
          <div className="space-y-4">
            <div className={`rounded-2xl border p-5 ${verification.all_encrypted ? "bg-teal-500/10 border-teal-500/20" : "bg-red-500/10 border-red-500/20"}`}>
              <div className="flex items-center gap-3 mb-2">
                <Shield size={20} className={verification.all_encrypted ? "text-teal-400" : "text-red-400"} />
                <div>
                  <p className="text-white font-semibold">
                    {verification.all_encrypted ? "✅ All data is encrypted in Supabase" : "❌ Some data is not encrypted"}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {verification.encryption_algorithm} · {verification.key_derivation}
                  </p>
                </div>
              </div>
              <p className="text-xs text-slate-400">
                {verification.total_messages} message{verification.total_messages !== 1 ? "s" : ""} checked ·
                Each user has a unique derived key — even the same message looks different for different users
              </p>
            </div>

            {verification.messages.map((msg, i) => (
              <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${msg.role === "user" ? "bg-purple-500/20 text-purple-300" : "bg-teal-500/20 text-teal-300"}`}>
                    {msg.role}
                  </span>
                  <span className="text-xs text-slate-500">{formatTimestamp(msg.created_at)}</span>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">📦 Stored in Supabase (ciphertext — unreadable by anyone):</p>
                  <code className="text-xs text-orange-300 bg-black/30 rounded px-2 py-1 block break-all font-mono">
                    {msg.stored_in_db_raw}
                  </code>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">{msg.decrypt_status}</p>
                  {msg.decrypted_preview && (
                    <p className="text-xs text-green-300 bg-green-500/10 rounded px-2 py-1">
                      &ldquo;{msg.decrypted_preview}&rdquo;
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span className={msg.looks_encrypted ? "text-teal-400" : "text-red-400"}>
                    {msg.looks_encrypted ? "🔒 Encrypted" : "⚠️ Not encrypted"}
                  </span>
                  {msg.emotion && <span>Emotion: {msg.emotion}</span>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Encryption info */}
        <div className="mt-8 bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4">
          <h4 className="text-indigo-300 font-semibold text-sm mb-2 flex items-center gap-2">
            <Lock size={14} /> End-to-End Encryption Details
          </h4>
          <ul className="text-xs text-slate-400 space-y-1.5">
            <li>• <strong className="text-slate-300">AES-256-GCM</strong> — military-grade encryption, same as HTTPS and banking</li>
            <li>• <strong className="text-slate-300">HKDF-SHA256</strong> — your unique key is derived from your user ID + server secret</li>
            <li>• <strong className="text-slate-300">Random nonce</strong> — same message encrypted twice looks completely different</li>
            <li>• <strong className="text-slate-300">GCM auth tag</strong> — detects any tampering with stored data</li>
            <li>• <strong className="text-slate-300">Zero knowledge</strong> — even Supabase admins cannot read your conversations</li>
          </ul>
        </div>
      </main>
    </div>
  );
}
