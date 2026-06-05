"use client";

/**
 * FeedbackWidget
 * ──────────────
 * Thumbs-up / thumbs-down widget rendered after every AI response.
 * On click it:
 *   1. Calls POST /feedback with the interaction_id + score (+1/-1)
 *   2. Passes session_duration so the backend can weight the reward
 *   3. Shows the computed RL reward returned by the server
 *   4. Locks after first submission to prevent double-counting
 */

import { useState, useRef } from "react";
import { ThumbsUp, ThumbsDown, Loader2, Sparkles } from "lucide-react";
import { submitFeedback } from "../lib/api-client";
import type { RLAction, PolicyName } from "../types";

interface FeedbackWidgetProps {
  interactionId: string;
  sessionStartTime: number;         // Date.now() when session started
  appliedAction?: RLAction | null;
  appliedPolicy?: PolicyName | null;
}

export default function FeedbackWidget({
  interactionId,
  sessionStartTime,
  appliedAction,
  appliedPolicy,
}: FeedbackWidgetProps) {
  const [submitted, setSubmitted] = useState<1 | -1 | null>(null);
  const [reward, setReward] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lockRef = useRef(false);

  const handleFeedback = async (score: 1 | -1) => {
    if (lockRef.current || !interactionId) return;
    lockRef.current = true;
    setLoading(true);
    setError(null);

    const sessionDuration = (Date.now() - sessionStartTime) / 1000;

    try {
      const res = await submitFeedback({
        interaction_id: interactionId,
        score,
        session_duration: sessionDuration,
      });
      setSubmitted(score);
      if (res.reward != null) setReward(res.reward);
    } catch (e) {
      setError("Feedback failed");
      lockRef.current = false;
    } finally {
      setLoading(false);
    }
  };

  // ── Policy badge colour ──────────────────────────────────────────
  const policyColour: Record<string, string> = {
    thompson_sampling: "bg-violet-100 text-violet-700 border-violet-200",
    epsilon_greedy:    "bg-amber-100  text-amber-700  border-amber-200",
    ucb1:              "bg-cyan-100   text-cyan-700   border-cyan-200",
  };
  const policyLabel: Record<string, string> = {
    thompson_sampling: "Thompson",
    epsilon_greedy:    "ε-Greedy",
    ucb1:              "UCB1",
  };

  return (
    <div className="mt-3 flex flex-col gap-2">

      {/* Action tags */}
      {appliedAction && (
        <div className="flex flex-wrap gap-1.5 items-center">
          {appliedPolicy && (
            <span
              className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${policyColour[appliedPolicy] ?? "bg-slate-100 text-slate-500"}`}
            >
              {policyLabel[appliedPolicy] ?? appliedPolicy}
            </span>
          )}
          {Object.entries(appliedAction).map(([k, v]) => (
            <span
              key={k}
              className="text-[10px] bg-indigo-50 text-indigo-500 border border-indigo-100 px-2 py-0.5 rounded-full"
            >
              {k.replace(/_/g, " ")}: <b>{String(v)}</b>
            </span>
          ))}
        </div>
      )}

      {/* Feedback buttons */}
      {!submitted && !loading && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">
            Was this helpful?
          </span>
          <button
            onClick={() => handleFeedback(1)}
            aria-label="Thumbs up"
            className="p-1.5 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-600
                       hover:bg-emerald-100 hover:scale-110 active:scale-95 transition-all"
          >
            <ThumbsUp size={14} />
          </button>
          <button
            onClick={() => handleFeedback(-1)}
            aria-label="Thumbs down"
            className="p-1.5 rounded-xl border border-rose-200 bg-rose-50 text-rose-500
                       hover:bg-rose-100 hover:scale-110 active:scale-95 transition-all"
          >
            <ThumbsDown size={14} />
          </button>
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-1.5 text-xs text-indigo-400">
          <Loader2 size={12} className="animate-spin" />
          <span>Recording feedback…</span>
        </div>
      )}

      {submitted && !loading && (
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-semibold flex items-center gap-1 ${
              submitted === 1 ? "text-emerald-600" : "text-rose-500"
            }`}
          >
            {submitted === 1 ? (
              <ThumbsUp size={12} />
            ) : (
              <ThumbsDown size={12} />
            )}
            {submitted === 1 ? "Thanks — great response!" : "Got it — will improve."}
          </span>
          {reward != null && (
            <span className="text-[10px] text-slate-400 flex items-center gap-0.5">
              <Sparkles size={10} className="text-indigo-400" />
              RL reward: {reward > 0 ? "+" : ""}{reward.toFixed(3)}
            </span>
          )}
        </div>
      )}

      {error && (
        <p className="text-xs text-rose-500">{error}</p>
      )}
    </div>
  );
}
