"use client";

/**
 * RLDashboard
 * ───────────
 * Live policy comparison panel.  Shows all three bandits side-by-side,
 * per-dimension arm rankings, and a refresh button.
 *
 * Data sources:
 *   GET /rl/stats    → RLPolicyReport
 *   GET /rl/rankings → RLRankings
 *   GET /rl/policy   → active policy + win rates
 */

import { useState, useEffect, useCallback, type FC } from "react";
import type { LucideProps } from "lucide-react";
import {
  BrainCircuit,
  RefreshCw,
  Trophy,
  TrendingUp,
  BarChart3,
  Zap,
  Target,
  MessageSquare,
  Sparkles,
  Heart,
  AlignLeft,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { getRLStats, getRLRankings } from "../lib/api-client";
import type { RLPolicyReport, RLRankings, PolicyName, RLArmStats, RLPolicyStats } from "../types";

// ─── helpers ────────────────────────────────────────────────────────────────

function pct(v: number) {
  return `${(v * 100).toFixed(1)}%`;
}
function fmt(v: number, decimals = 3) {
  return v.toFixed(decimals);
}

const POLICY_META: Record<
  PolicyName,
  { label: string; desc: string; colour: string; badge: string }
> = {
  thompson_sampling: {
    label: "Thompson Sampling",
    desc:  "Beta posterior — balances explore/exploit via probability matching",
    colour: "from-violet-500 to-purple-600",
    badge:  "bg-violet-100 text-violet-700 border-violet-200",
  },
  epsilon_greedy: {
    label: "ε-Greedy",
    desc:  "Decaying epsilon — explores randomly, exploits best known arm",
    colour: "from-amber-400 to-orange-500",
    badge:  "bg-amber-100 text-amber-700 border-amber-200",
  },
  ucb1: {
    label: "UCB1",
    desc:  "Upper Confidence Bound — optimistic exploration bonus",
    colour: "from-cyan-400 to-teal-500",
    badge:  "bg-cyan-100 text-cyan-700 border-cyan-200",
  },
};

const DIM_META: Record<
  string,
  { label: string; icon: FC<LucideProps> }
> = {
  persona:           { label: "Persona",           icon: BrainCircuit  },
  response_length:   { label: "Response Length",   icon: AlignLeft     },
  questioning_style: { label: "Questioning Style", icon: MessageSquare },
  motivation_style:  { label: "Motivation Style",  icon: Heart         },
  detail_level:      { label: "Detail Level",      icon: Target        },
};

// ─── sub-components ──────────────────────────────────────────────────────────

function RewardBar({ value }: { value: number }) {
  // value in [-1, +1] → map to [0, 100] for width
  const pctWidth = ((value + 1) / 2) * 100;
  const colour =
    value > 0.1
      ? "bg-emerald-400"
      : value < -0.1
      ? "bg-rose-400"
      : "bg-slate-300";
  return (
    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-700 ${colour}`}
        style={{ width: `${pctWidth}%` }}
      />
    </div>
  );
}

function PolicyCard({
  policyName,
  stats,
  isActive,
}: {
  policyName: PolicyName;
  stats: RLPolicyReport["policies"][PolicyName];
  isActive: boolean;
}) {
  const meta   = POLICY_META[policyName];
  const [open, setOpen] = useState(false);

  return (
    <div
      className={`rounded-2xl border p-4 transition-all duration-300 ${
        isActive
          ? "border-indigo-300 bg-indigo-50/60 shadow-md"
          : "border-slate-200 bg-white"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <span
              className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${meta.badge}`}
            >
              {meta.label}
            </span>
            {isActive && (
              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                <Trophy size={9} /> Active
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">{meta.desc}</p>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="text-center">
          <p className="text-[10px] text-slate-400 uppercase tracking-wider">Pulls</p>
          <p className="text-sm font-bold text-slate-700">{stats.total_pulls}</p>
        </div>
        <div className="text-center">
          <p className="text-[10px] text-slate-400 uppercase tracking-wider">Win Rate</p>
          <p className="text-sm font-bold text-indigo-600">{pct(stats.win_rate)}</p>
        </div>
        <div className="text-center">
          <p className="text-[10px] text-slate-400 uppercase tracking-wider">Σ Reward</p>
          <p
            className={`text-sm font-bold ${
              stats.cumulative_reward >= 0 ? "text-emerald-600" : "text-rose-500"
            }`}
          >
            {stats.cumulative_reward >= 0 ? "+" : ""}
            {fmt(stats.cumulative_reward, 2)}
          </p>
        </div>
      </div>

      {/* Win-rate bar */}
      <RewardBar value={stats.win_rate * 2 - 1} />

      {/* Epsilon badge (only ε-greedy) */}
      {stats.epsilon != null && (
        <p className="text-[10px] text-slate-400 mt-1.5">
          ε = {fmt(stats.epsilon, 4)} (decaying)
        </p>
      )}

      {/* Arm details toggle */}
      <button
        onClick={() => setOpen((p) => !p)}
        className="mt-3 text-[11px] text-indigo-500 flex items-center gap-1 hover:underline"
      >
        {open ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
        {open ? "Hide" : "Show"} arm stats
      </button>

      {open && (
        <div className="mt-2 space-y-3">
          {Object.entries(stats.arms as Record<string, RLArmStats[]>).map(([dim, arms]) => {
            const dimMeta = DIM_META[dim] ?? { label: dim, icon: BarChart3 };
            const Icon    = dimMeta.icon;
            return (
              <div key={dim}>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1 mb-1">
                  <Icon size={9} /> {dimMeta.label}
                </p>
                <div className="space-y-1">
                  {arms.map((arm) => (
                    <div key={arm.arm} className="flex items-center gap-2">
                      <span className="text-[10px] text-slate-600 w-28 truncate capitalize">
                        {arm.arm.replace(/_/g, " ")}
                      </span>
                      <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            arm.mean > 0 ? "bg-indigo-400" : "bg-slate-300"
                          }`}
                          style={{
                            width: `${Math.max(2, ((arm.mean + 1) / 2) * 100)}%`,
                          }}
                        />
                      </div>
                      <span className="text-[10px] text-slate-500 w-12 text-right">
                        {fmt(arm.mean)} ({arm.pulls})
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function RankingsPanel({ rankings }: { rankings: RLRankings }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {Object.entries(rankings).map(([dim, arms]) => {
        const dimMeta = DIM_META[dim] ?? { label: dim, icon: BarChart3 };
        const Icon    = dimMeta.icon;
        const best    = arms[0];
        return (
          <div
            key={dim}
            className="bg-white rounded-2xl border border-slate-200 p-4"
          >
            <div className="flex items-center gap-1.5 mb-3">
              <Icon size={12} className="text-indigo-500" />
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                {dimMeta.label}
              </span>
              {best && (
                <span className="ml-auto text-[10px] text-emerald-600 font-bold bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                  <Trophy size={9} /> {best.arm.replace(/_/g, " ")}
                </span>
              )}
            </div>
            <div className="space-y-1.5">
              {arms.map((arm, idx) => {
                const barW = Math.max(
                  4,
                  arms[0]?.avg_mean !== 0
                    ? Math.abs(arm.avg_mean / Math.max(...arms.map((a) => Math.abs(a.avg_mean)), 0.001)) * 100
                    : 10,
                );
                return (
                  <div key={arm.arm} className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-400 w-4 font-mono">
                      {idx + 1}.
                    </span>
                    <span className="text-[11px] text-slate-600 w-24 truncate capitalize">
                      {arm.arm.replace(/_/g, " ")}
                    </span>
                    <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          arm.avg_mean > 0 ? "bg-gradient-to-r from-indigo-400 to-purple-400" : "bg-slate-300"
                        }`}
                        style={{ width: `${barW}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-slate-400 w-12 text-right">
                      {fmt(arm.avg_mean)} ({arm.total_pulls})
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function RLDashboard() {
  const [report,   setReport]   = useState<RLPolicyReport | null>(null);
  const [rankings, setRankings] = useState<RLRankings | null>(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);
  const [lastSync, setLastSync] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [r, k] = await Promise.all([getRLStats(), getRLRankings()]);
      setReport(r);
      setRankings(k);
      setLastSync(new Date());
    } catch (e) {
      setError("Could not reach the backend. Is it running?");
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-refresh every 30 s
  useEffect(() => {
    fetchData();
    const t = setInterval(fetchData, 30_000);
    return () => clearInterval(t);
  }, [fetchData]);

  const totalPulls = report
    ? Math.max(
        ...Object.values(report.policies).map((p) => (p as RLPolicyStats).total_pulls),
      )
    : 0;

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-50 rounded-xl border border-indigo-100">
            <BrainCircuit size={18} className="text-indigo-600" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-800">
              RL Policy Engine
            </h2>
            <p className="text-[11px] text-slate-400">
              Multi-Armed Bandit · Live comparison ·{" "}
              {totalPulls} total pulls
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {lastSync && (
            <span className="text-[10px] text-slate-400">
              synced {lastSync.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchData}
            disabled={loading}
            className="p-2 rounded-xl border border-slate-200 bg-white text-slate-500
                       hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-200
                       disabled:opacity-40 transition-all"
            aria-label="Refresh"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 text-sm text-rose-600">
          {error}
        </div>
      )}

      {/* ── Active Policy Banner ────────────────────────────────────── */}
      {report && (
        <div
          className={`rounded-2xl p-4 bg-gradient-to-r ${
            POLICY_META[report.active_policy].colour
          } text-white shadow-md`}
        >
          <div className="flex items-center gap-2 mb-1">
            <Trophy size={14} />
            <span className="text-xs font-bold uppercase tracking-wider opacity-90">
              Active Policy
            </span>
          </div>
          <p className="text-xl font-extrabold">
            {POLICY_META[report.active_policy].label}
          </p>
          <p className="text-xs opacity-75 mt-0.5">
            {POLICY_META[report.active_policy].desc}
          </p>
          <div className="flex gap-4 mt-3">
            {Object.entries(report.policies).map(([pn, ps]) => {
              const pStats = ps as RLPolicyStats;
              return (
                <div key={pn} className="text-center">
                  <p className="text-[10px] uppercase tracking-wider opacity-70">
                    {POLICY_META[pn as PolicyName].label}
                  </p>
                  <p className="text-sm font-bold">{pct(pStats.win_rate)}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Policy Cards (3-column) ─────────────────────────────────── */}
      {report ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {(Object.keys(report.policies) as PolicyName[]).map((pn) => (
            <PolicyCard
              key={pn}
              policyName={pn}
              stats={report.policies[pn] as RLPolicyStats}
              isActive={pn === report.active_policy}
            />
          ))}
        </div>
      ) : loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="rounded-2xl border border-slate-200 bg-white p-4 h-32 animate-pulse"
            />
          ))}
        </div>
      ) : null}

      {/* ── Action Space Rankings ───────────────────────────────────── */}
      {rankings && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={14} className="text-indigo-500" />
            <h3 className="text-sm font-bold text-slate-700">
              Action Space Rankings
            </h3>
            <span className="text-[10px] text-slate-400">
              — averaged across all 3 policies
            </span>
          </div>
          <RankingsPanel rankings={rankings} />
        </div>
      )}

      {/* ── Reward Signal Weights ───────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles size={13} className="text-indigo-500" />
          <h3 className="text-sm font-bold text-slate-700">
            Reward Signal Composition
          </h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "User Feedback",    weight: 40, colour: "bg-violet-400" },
            { label: "Sentiment Delta",  weight: 30, colour: "bg-indigo-400" },
            { label: "Session Duration", weight: 20, colour: "bg-cyan-400"   },
            { label: "Turn Engagement",  weight: 10, colour: "bg-emerald-400"},
          ].map(({ label, weight, colour }) => (
            <div key={label} className="text-center">
              <div className="relative w-12 h-12 mx-auto mb-1">
                <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke="#f1f5f9" strokeWidth="3" />
                  <circle
                    cx="18" cy="18" r="15.9" fill="none"
                    strokeWidth="3"
                    stroke={colour.replace("bg-", "").includes("violet")
                      ? "#8b5cf6"
                      : colour.includes("indigo") ? "#6366f1"
                      : colour.includes("cyan")   ? "#22d3ee"
                      : "#34d399"}
                    strokeDasharray={`${weight} ${100 - weight}`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-slate-700">
                  {weight}%
                </span>
              </div>
              <p className="text-[10px] text-slate-500 leading-tight">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Action Space Dimensions ─────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Zap size={13} className="text-indigo-500" />
          <h3 className="text-sm font-bold text-slate-700">
            Action Space  — 5 independent dimensions
          </h3>
        </div>
        <div className="space-y-2 text-xs text-slate-600">
          {[
            { dim: "Persona",           arms: ["Empathetic Friend", "Humorous", "Direct", "Philosophical", "Cheerleader"] },
            { dim: "Response Length",   arms: ["Brief (1-2s)", "Moderate (2-3s)", "Detailed (3-5s)"] },
            { dim: "Questioning Style", arms: ["None", "Open-ended", "Reflective", "Socratic"] },
            { dim: "Motivation Style",  arms: ["None", "Encouragement", "Challenge", "Reframe"] },
            { dim: "Detail Level",      arms: ["Concise", "Balanced", "Thorough"] },
          ].map(({ dim, arms }) => (
            <div key={dim} className="flex flex-wrap gap-1.5 items-center">
              <span className="font-bold text-slate-700 w-32">{dim}</span>
              {arms.map((a) => (
                <span
                  key={a}
                  className="bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-full text-[10px] text-slate-500"
                >
                  {a}
                </span>
              ))}
            </div>
          ))}
        </div>
        <p className="mt-3 text-[10px] text-slate-400">
          Total joint arms = 5 × 3 × 4 × 4 × 3 = <b>720</b> — factorised into 5
          independent bandits to keep the problem tractable.
        </p>
      </div>
    </div>
  );
}
