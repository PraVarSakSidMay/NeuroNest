"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Heart, Flame, Moon, Brain,
  MessageCircle, BookOpen, Mic, TrendingUp, ChevronRight,
} from "lucide-react";
import Link from "next/link";
import { api, type UserDashboardData } from "@/lib/api";
import { useUser } from "@/context/UserContext";

/* ── shared card style ── */
const card: React.CSSProperties = {
  background: "#ffffff",
  borderRadius: "20px",
  border: "1px solid #ede9fe",
  boxShadow: "0 2px 16px rgba(124,58,237,0.07)",
  padding: "28px",
};

const moods = [
  { emoji: "😄", label: "Great", activeBg: "#f0fdf4", activeBorder: "#4ade80",  activeColor: "#15803d" },
  { emoji: "🙂", label: "Good",  activeBg: "#eff6ff", activeBorder: "#60a5fa",  activeColor: "#1d4ed8" },
  { emoji: "😐", label: "Okay",  activeBg: "#fffbeb", activeBorder: "#fbbf24",  activeColor: "#92400e" },
  { emoji: "😔", label: "Low",   activeBg: "#fff7ed", activeBorder: "#fb923c",  activeColor: "#9a3412" },
  { emoji: "😢", label: "Rough", activeBg: "#fef2f2", activeBorder: "#f87171",  activeColor: "#991b1b" },
];

const iconColors: Record<string, { bg: string; color: string }> = {
  violet: { bg: "#ede9fe", color: "#7c3aed" },
  orange: { bg: "#fff7ed", color: "#ea580c" },
  blue:   { bg: "#eff6ff", color: "#2563eb" },
  green:  { bg: "#f0fdf4", color: "#16a34a" },
};

export default function UserDashboard() {
  const { user } = useUser();

  const [stats, setStats]               = useState<UserDashboardData | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);

  const [selectedMood, setSelectedMood] = useState<number | null>(null);
  const [moodLogged, setMoodLogged]     = useState(false);
  const [loggingMood, setLoggingMood]   = useState(false);

  const hour      = new Date().getHours();
  const greeting  = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const firstName = user.name.split(" ")[0];

  const loadStats = useCallback(async () => {
    setLoadingStats(true);
    try {
      const data = await api.user.dashboard();
      setStats(data);
    } catch (e) {
      console.error("Failed to load dashboard stats:", e);
    } finally {
      setLoadingStats(false);
    }
  }, []);

  useEffect(() => { loadStats(); }, [loadStats]);

  async function handleLogMood() {
    if (selectedMood === null) return;
    setLoggingMood(true);
    try {
      await api.user.logMood(moods[selectedMood].emoji, moods[selectedMood].label);
      setMoodLogged(true);
      // Reload stats so streak + chart update immediately
      await loadStats();
    } catch (e) {
      console.error("Failed to log mood:", e);
    } finally {
      setLoggingMood(false);
    }
  }

  const moodData      = stats?.moodData ?? [];
  const maxScore      = moodData.length > 0 ? Math.max(...moodData.map(d => d.score), 1) : 1;
  const hasAnyMood    = moodData.some(d => d.score > 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>

      {/* ── Top bar ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: 700, color: "#111827", lineHeight: 1.2 }}>
            {greeting}, {firstName} 👋
          </h1>
          <p style={{ fontSize: "15px", color: "#6b7280", marginTop: "6px" }}>
            Here&apos;s your wellness overview for today
          </p>
        </div>
        <div style={{
          width: "48px", height: "48px", borderRadius: "50%",
          background: "linear-gradient(135deg, #7c3aed, #3b82f6)",
          display: "flex", alignItems: "center", justifyContent: "center",
          color: "#fff", fontWeight: 700, fontSize: "16px",
          boxShadow: "0 4px 12px rgba(124,58,237,0.3)", flexShrink: 0,
        }}>
          {user.avatar}
        </div>
      </div>

      {/* ── Welcome banner ── */}
      <div style={{
        borderRadius: "20px",
        background: "linear-gradient(135deg, #7c3aed 0%, #4f46e5 50%, #3b82f6 100%)",
        padding: "36px 40px", color: "#fff", position: "relative", overflow: "hidden",
      }}>
        <div style={{ position: "absolute", right: "-40px", top: "-40px", width: "220px", height: "220px", borderRadius: "50%", background: "rgba(255,255,255,0.08)", pointerEvents: "none" }} />
        <div style={{ position: "absolute", right: "60px", bottom: "-60px", width: "160px", height: "160px", borderRadius: "50%", background: "rgba(255,255,255,0.05)", pointerEvents: "none" }} />

        <p style={{ fontSize: "13px", fontWeight: 600, color: "rgba(255,255,255,0.75)", marginBottom: "10px", letterSpacing: "0.04em" }}>
          🌸 Daily Insight
        </p>

        {/* Banner text changes based on whether user has any data */}
        {!loadingStats && stats && stats.moodCheckins === 0 ? (
          <>
            <h2 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "12px", lineHeight: 1.3 }}>
              Welcome to NeuroNest, {firstName}! 🎉
            </h2>
            <p style={{ fontSize: "15px", color: "rgba(255,255,255,0.75)", lineHeight: 1.7, maxWidth: "520px" }}>
              Start your wellness journey by logging your first mood below. Your streak, score, and chart will update as you check in daily.
            </p>
          </>
        ) : (
          <>
            <h2 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "12px", lineHeight: 1.3 }}>
              {(stats?.streak ?? 0) > 1
                ? `You're on a ${stats?.streak}-day streak! 🔥`
                : "Keep going — every check-in counts!"}
            </h2>
            <p style={{ fontSize: "15px", color: "rgba(255,255,255,0.75)", lineHeight: 1.7, maxWidth: "520px" }}>
              Keep logging your mood daily to build your streak and track your wellness over time.
            </p>
          </>
        )}

        <div style={{ display: "flex", gap: "12px", marginTop: "20px", flexWrap: "wrap" }}>
          <span style={{ background: "rgba(255,255,255,0.2)", color: "#fff", fontSize: "13px", fontWeight: 600, padding: "6px 16px", borderRadius: "20px" }}>
            🔥 {loadingStats ? "—" : stats?.streak ?? 0}-day streak
          </span>
          <span style={{ background: "rgba(255,255,255,0.2)", color: "#fff", fontSize: "13px", fontWeight: 600, padding: "6px 16px", borderRadius: "20px" }}>
            Score: {loadingStats ? "—" : stats?.wellnessScore != null ? `${stats.wellnessScore}/100` : "No data yet"}
          </span>
        </div>
      </div>

      {/* ── Stat cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "20px" }}>
        <StatCard
          title="Wellness Score"
          value={loadingStats ? "—" : stats?.wellnessScore != null ? String(stats.wellnessScore) : "—"}
          unit="/100"
          iconKey="violet"
          icon={<Heart size={20} />}
          subtext={loadingStats ? "Loading..." : stats?.wellnessScore != null ? "Based on your mood logs" : "Log a mood to start"}
          hasData={!loadingStats && stats?.wellnessScore != null}
        />
        <StatCard
          title="Weekly Streak"
          value={loadingStats ? "—" : String(stats?.streak ?? 0)}
          unit="days"
          iconKey="orange"
          icon={<Flame size={20} />}
          subtext={loadingStats ? "Loading..." : (stats?.streak ?? 0) > 0 ? "Keep it up!" : "Log today to start"}
          hasData={!loadingStats && (stats?.streak ?? 0) > 0}
        />
        <StatCard
          title="Sleep Average"
          value={loadingStats ? "—" : stats?.sleepAvg != null ? String(stats.sleepAvg) : "—"}
          unit="hrs"
          iconKey="blue"
          icon={<Moon size={20} />}
          subtext={loadingStats ? "Loading..." : stats?.sleepAvg != null ? "From your profile" : "Set in your profile"}
          hasData={!loadingStats && stats?.sleepAvg != null}
        />
        <StatCard
          title="Mood Check-ins"
          value={loadingStats ? "—" : String(stats?.moodCheckins ?? 0)}
          unit="/month"
          iconKey="green"
          icon={<Brain size={20} />}
          subtext={loadingStats ? "Loading..." : (stats?.moodCheckins ?? 0) > 0 ? "This month" : "None yet this month"}
          hasData={!loadingStats && (stats?.moodCheckins ?? 0) > 0}
        />
      </div>

      {/* ── Mood + Graph ── */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 3fr", gap: "20px" }}>

        {/* Mood card */}
        <div style={card}>
          <h3 style={{ fontSize: "17px", fontWeight: 600, color: "#111827", marginBottom: "6px" }}>
            Today&apos;s Mood
          </h3>
          <p style={{ fontSize: "14px", color: "#6b7280", marginBottom: "20px" }}>
            How are you feeling right now?
          </p>

          <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
            {moods.map((m, i) => (
              <button
                key={i}
                onClick={() => { setSelectedMood(i); setMoodLogged(false); }}
                style={{
                  flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "6px",
                  padding: "12px 4px", borderRadius: "14px",
                  border: selectedMood === i ? `2px solid ${m.activeBorder}` : "2px solid transparent",
                  background: selectedMood === i ? m.activeBg : "#f9f8ff",
                  cursor: "pointer", transition: "all 0.15s ease",
                  transform: selectedMood === i ? "scale(1.05)" : "scale(1)",
                }}
              >
                <span style={{ fontSize: "24px" }}>{m.emoji}</span>
                <span style={{ fontSize: "11px", fontWeight: 500, color: selectedMood === i ? m.activeColor : "#9ca3af" }}>
                  {m.label}
                </span>
              </button>
            ))}
          </div>

          {moodLogged && selectedMood !== null && (
            <div style={{
              background: "#f0fdf4", borderRadius: "12px", padding: "10px",
              textAlign: "center", fontSize: "14px", color: "#16a34a",
              fontWeight: 600, marginBottom: "16px",
            }}>
              ✓ Logged: {moods[selectedMood].label} {moods[selectedMood].emoji}
            </div>
          )}

          <button
            disabled={selectedMood === null || loggingMood}
            onClick={handleLogMood}
            style={{
              width: "100%", height: "48px", borderRadius: "14px", border: "none",
              background: selectedMood === null
                ? "#e5e7eb"
                : "linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)",
              color: selectedMood === null ? "#9ca3af" : "#fff",
              fontSize: "15px", fontWeight: 600,
              cursor: selectedMood === null || loggingMood ? "not-allowed" : "pointer",
              opacity: loggingMood ? 0.7 : 1,
              transition: "all 0.2s ease",
            }}
          >
            {loggingMood ? "Saving..." : moodLogged ? "Mood Logged ✓" : "Log Mood"}
          </button>
        </div>

        {/* Graph card */}
        <div style={card}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
            <h3 style={{ fontSize: "17px", fontWeight: 600, color: "#111827" }}>Mood Trend</h3>
            <span style={{
              fontSize: "12px", background: "#ede9fe", color: "#7c3aed",
              fontWeight: 600, padding: "5px 12px", borderRadius: "20px",
              display: "flex", alignItems: "center", gap: "5px",
            }}>
              <TrendingUp size={11} /> This Week
            </span>
          </div>
          <p style={{ fontSize: "14px", color: "#6b7280", marginBottom: "24px" }}>
            This week&apos;s mood scores
          </p>

          {loadingStats ? (
            <div style={{ height: "140px", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <p style={{ fontSize: "14px", color: "#9ca3af" }}>Loading...</p>
            </div>
          ) : !hasAnyMood ? (
            /* Empty state for new users */
            <div style={{
              height: "140px", display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center", gap: "8px",
            }}>
              <span style={{ fontSize: "32px" }}>📊</span>
              <p style={{ fontSize: "14px", color: "#9ca3af", textAlign: "center" }}>
                No mood data yet.<br />Log your first mood to see the chart.
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "flex-end", gap: "12px", height: "140px", paddingTop: "20px" }}>
              {moodData.map(({ day, score }) => (
                <div key={day} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", height: "100%" }}>
                  <div style={{ flex: 1, width: "100%", display: "flex", alignItems: "flex-end" }}>
                    <div
                      title={score > 0 ? `${day}: ${score}` : `${day}: no data`}
                      style={{
                        width: "100%",
                        height: score > 0 ? `${(score / maxScore) * 100}%` : "8px",
                        minHeight: "8px",
                        background: score > 0
                          ? "linear-gradient(180deg, #a78bfa, #7c3aed)"
                          : "#e5e7eb",
                        borderRadius: "8px 8px 4px 4px",
                        transition: "opacity 0.2s ease",
                        cursor: "pointer",
                      }}
                      onMouseEnter={e => (e.currentTarget.style.opacity = "0.75")}
                      onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
                    />
                  </div>
                  <span style={{ fontSize: "12px", color: "#9ca3af", fontWeight: 500 }}>{day}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Quick Access ── */}
      <div>
        <h3 style={{ fontSize: "18px", fontWeight: 600, color: "#111827", marginBottom: "16px" }}>
          Quick Access
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
          {[
            { href: "/chat",    icon: MessageCircle, label: "AI Chat", sub: "Talk to NeuroBot",    bg: "#ede9fe", ic: "#7c3aed" },
            { href: "/journal", icon: BookOpen,      label: "Journal", sub: "Write your thoughts", bg: "#eff6ff", ic: "#2563eb" },
            { href: "/voice",   icon: Mic,           label: "Voice",   sub: "Speak your mind",     bg: "#f0fdf4", ic: "#16a34a" },
          ].map(({ href, icon: Icon, label, sub, bg, ic }) => (
            <Link
              key={href}
              href={href}
              style={{
                display: "flex", flexDirection: "column", gap: "16px",
                background: "#ffffff", borderRadius: "20px",
                border: "1px solid #ede9fe",
                boxShadow: "0 2px 16px rgba(124,58,237,0.07)",
                padding: "24px", textDecoration: "none",
                transition: "box-shadow 0.2s ease, transform 0.2s ease",
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.boxShadow = "0 8px 32px rgba(124,58,237,0.15)";
                (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)";
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 16px rgba(124,58,237,0.07)";
                (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
              }}
            >
              <div style={{ width: "44px", height: "44px", borderRadius: "14px", background: bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Icon size={22} color={ic} />
              </div>
              <div>
                <p style={{ fontSize: "15px", fontWeight: 600, color: "#111827" }}>{label}</p>
                <p style={{ fontSize: "13px", color: "#6b7280", marginTop: "3px" }}>{sub}</p>
              </div>
              <ChevronRight size={16} color="#d1d5db" style={{ alignSelf: "flex-end" }} />
            </Link>
          ))}
        </div>
      </div>

      {/* ── Recent Activity — only shown if user has data ── */}
      {!loadingStats && (stats?.moodCheckins ?? 0) > 0 && (
        <div>
          <h3 style={{ fontSize: "18px", fontWeight: 600, color: "#111827", marginBottom: "16px" }}>
            Recent Activity
          </h3>
          <div style={{
            background: "#ffffff", borderRadius: "20px",
            border: "1px solid #ede9fe",
            boxShadow: "0 2px 16px rgba(124,58,237,0.07)",
            overflow: "hidden",
          }}>
            {[
              { icon: Brain,         bg: "#f0fdf4", ic: "#16a34a", title: "Mood Logged",     desc: "You logged your mood today. Keep the streak going!",  time: "Today" },
              { icon: BookOpen,      bg: "#ede9fe", ic: "#7c3aed", title: "Journal",         desc: "Write about your day in the journal.",                 time: "" },
              { icon: MessageCircle, bg: "#eff6ff", ic: "#2563eb", title: "AI Chat",         desc: "Talk to NeuroBot about how you're feeling.",           time: "" },
            ].map(({ icon: Icon, bg, ic, title, desc, time }, i, arr) => (
              <div
                key={i}
                style={{
                  display: "flex", alignItems: "center", gap: "16px",
                  padding: "20px 28px",
                  borderBottom: i < arr.length - 1 ? "1px solid #f9f8ff" : "none",
                }}
              >
                <div style={{ width: "40px", height: "40px", borderRadius: "12px", background: bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <Icon size={18} color={ic} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: "15px", fontWeight: 600, color: "#111827" }}>{title}</p>
                  <p style={{ fontSize: "13px", color: "#6b7280", marginTop: "2px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{desc}</p>
                </div>
                {time && <span style={{ fontSize: "12px", color: "#9ca3af", flexShrink: 0 }}>{time}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}

/* ── Stat card ── */
function StatCard({ title, value, unit, iconKey, icon, subtext, hasData }: {
  title: string; value: string; unit: string;
  iconKey: string; icon: React.ReactNode;
  subtext: string; hasData: boolean;
}) {
  const { bg, color } = iconColors[iconKey] ?? iconColors.violet;
  return (
    <div style={{
      background: "#ffffff", borderRadius: "20px",
      border: "1px solid #ede9fe",
      boxShadow: "0 2px 16px rgba(124,58,237,0.07)",
      padding: "24px", display: "flex", flexDirection: "column", gap: "16px",
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <p style={{ fontSize: "11px", fontWeight: 700, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          {title}
        </p>
        <div style={{ width: "38px", height: "38px", borderRadius: "12px", background: bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ color }}>{icon}</span>
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: "6px" }}>
        <span style={{ fontSize: "36px", fontWeight: 700, color: hasData ? "#111827" : "#d1d5db", lineHeight: 1 }}>
          {value}
        </span>
        <span style={{ fontSize: "14px", color: "#9ca3af", marginBottom: "4px" }}>{unit}</span>
      </div>
      <p style={{ fontSize: "13px", fontWeight: 500, color: hasData ? "#6b7280" : "#9ca3af" }}>
        {subtext}
      </p>
    </div>
  );
}
