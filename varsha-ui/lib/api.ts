/**
 * NeuroNest API client
 *
 * Auth + user data → real Supabase calls
 * Chat             → mock (AI backend not ready)
 */

import { supabase } from "@/lib/supabase";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    name: string;
    email: string;
    role: "user";
  };
}

export interface MeResponse {
  id: string;
  name: string;
  email: string;
  role: "user";
}

export interface UserDashboardData {
  wellnessScore: number | null;
  streak: number;
  sleepAvg: number | null;
  moodCheckins: number;
  moodData: { day: string; score: number }[];
}

export interface JournalEntry {
  id: string;
  title: string;
  content: string;
  mood: string;
  moodLabel: string;
  tags: string[];
  date: string;
  time: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
}

export interface ChatMessage {
  id: string | number;
  role: "ai" | "user";
  text: string;
  time: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function requireUserId(): Promise<string> {
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) throw new Error("Not authenticated");
  return user.id;
}

function formatDate(ts: string): string {
  return new Date(ts).toLocaleDateString("en-US", {
    month: "long", day: "numeric", year: "numeric",
  });
}

function formatTime(ts: string): string {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function moodLabelToScore(label: string): number {
  const map: Record<string, number> = {
    Great: 90, Good: 75, Okay: 55, Low: 35, Rough: 20,
  };
  return map[label] ?? 50;
}

// ── API ───────────────────────────────────────────────────────────────────────

export const api = {

  // ── Auth ──────────────────────────────────────────────────────────────────

  /** Sign in — no role needed, everyone is a user */
  async login(email: string, password: string): Promise<AuthResponse> {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw new Error(error.message);

    const session = data.session!;
    const userId  = data.user!.id;

    const { data: profile, error: profileErr } = await supabase
      .from("profiles")
      .select("name, role")
      .eq("id", userId)
      .single();

    if (profileErr) throw new Error("Could not load user profile.");

    return {
      access_token: session.access_token,
      token_type:   "bearer",
      user: {
        id:    userId,
        name:  profile.name,
        email: data.user!.email!,
        role:  "user",
      },
    };
  },

  /** Restore session on app mount */
  async me(): Promise<MeResponse> {
    const { data: { user }, error } = await supabase.auth.getUser();
    if (error || !user) throw new Error("Not authenticated");

    const { data: profile, error: profileErr } = await supabase
      .from("profiles")
      .select("name, role")
      .eq("id", user.id)
      .single();

    if (profileErr) throw new Error("Could not load user profile.");

    return {
      id:    user.id,
      name:  profile.name,
      email: user.email!,
      role:  "user",
    };
  },

  signup: {
    /**
     * Register a new user.
     * Saves name + role in Supabase auth metadata (trigger writes profiles row).
     * Saves health info in user_profiles table.
     */
    async user(data: {
      firstName: string;
      lastName: string;
      age: string;
      email: string;
      password: string;
      sleepSchedule: string;
      avgSleep: string;
      lastVisit: string;
      healthIssues: string;
    }): Promise<AuthResponse> {
      const name = `${data.firstName} ${data.lastName}`.trim();

      // 1. Create Supabase auth user
      const { data: authData, error } = await supabase.auth.signUp({
        email:    data.email,
        password: data.password,
        options:  { data: { name, role: "user" } },
      });
      if (error) throw new Error(error.message);

      const session = authData.session;
      if (!session) {
        throw new Error(
          "Account created but no session returned. " +
          "Go to Supabase → Authentication → Providers → Email → turn off 'Confirm email'."
        );
      }

      const userId = authData.user!.id;

      // 2. Save health profile data
      const { error: profileErr } = await supabase
        .from("user_profiles")
        .insert({
          id:             userId,
          age:            data.age ? parseInt(data.age, 10) : null,
          sleep_schedule: data.sleepSchedule || null,
          avg_sleep:      data.avgSleep ? parseFloat(data.avgSleep) : null,
          last_visit:     data.lastVisit || null,
          health_issues:  data.healthIssues || null,
        });

      if (profileErr) console.warn("user_profiles insert failed:", profileErr.message);

      return {
        access_token: session.access_token,
        token_type:   "bearer",
        user: { id: userId, name, email: data.email, role: "user" },
      };
    },
  },

  // ── User dashboard ────────────────────────────────────────────────────────

  user: {
    async dashboard(): Promise<UserDashboardData> {
      const userId = await requireUserId();

      // Sleep average from user_profiles
      const { data: userProfile } = await supabase
        .from("user_profiles")
        .select("avg_sleep")
        .eq("id", userId)
        .single();

      // Mood logs this month
      const startOfMonth = new Date();
      startOfMonth.setDate(1);
      startOfMonth.setHours(0, 0, 0, 0);

      const { data: monthLogs } = await supabase
        .from("mood_logs")
        .select("mood_label, logged_at")
        .eq("user_id", userId)
        .gte("logged_at", startOfMonth.toISOString())
        .order("logged_at", { ascending: true });

      const moodCheckins = monthLogs?.length ?? 0;

      // Last 7 days for chart
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 6);
      sevenDaysAgo.setHours(0, 0, 0, 0);

      const { data: recentLogs } = await supabase
        .from("mood_logs")
        .select("mood_label, logged_at")
        .eq("user_id", userId)
        .gte("logged_at", sevenDaysAgo.toISOString())
        .order("logged_at", { ascending: true });

      const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
      const dayMap: Record<string, number> = {};

      (recentLogs ?? []).forEach(log => {
        const key = dayNames[new Date(log.logged_at).getDay()];
        dayMap[key] = moodLabelToScore(log.mood_label);
      });

      const moodData: { day: string; score: number }[] = [];
      for (let i = 6; i >= 0; i--) {
        const d   = new Date();
        d.setDate(d.getDate() - i);
        const key = dayNames[d.getDay()];
        moodData.push({ day: key, score: dayMap[key] ?? 0 });
      }

      // Streak
      let streak = 0;
      for (let i = 0; i < 365; i++) {
        const day      = new Date();
        day.setDate(day.getDate() - i);
        const dayStart = new Date(day); dayStart.setHours(0, 0, 0, 0);
        const dayEnd   = new Date(day); dayEnd.setHours(23, 59, 59, 999);

        const { count } = await supabase
          .from("mood_logs")
          .select("id", { count: "exact", head: true })
          .eq("user_id", userId)
          .gte("logged_at", dayStart.toISOString())
          .lte("logged_at", dayEnd.toISOString());

        if ((count ?? 0) > 0) streak++;
        else break;
      }

      // Wellness score
      const scoredDays    = moodData.filter(d => d.score > 0);
      const wellnessScore = scoredDays.length > 0
        ? Math.round(scoredDays.reduce((s, d) => s + d.score, 0) / scoredDays.length)
        : null;

      return {
        wellnessScore,
        streak,
        sleepAvg:    userProfile?.avg_sleep ?? null,
        moodCheckins,
        moodData,
      };
    },

    async logMood(mood: string, moodLabel: string): Promise<void> {
      const userId = await requireUserId();
      const { error } = await supabase
        .from("mood_logs")
        .insert({ user_id: userId, mood, mood_label: moodLabel });
      if (error) throw new Error(error.message);
    },

    async getJournals(): Promise<JournalEntry[]> {
      const userId = await requireUserId();
      const { data, error } = await supabase
        .from("journal_entries")
        .select("id, title, content, mood, mood_label, tags, created_at")
        .eq("user_id", userId)
        .order("created_at", { ascending: false });

      if (error) throw new Error(error.message);

      return (data ?? []).map(row => ({
        id:        row.id,
        title:     row.title,
        content:   row.content,
        mood:      row.mood,
        moodLabel: row.mood_label,
        tags:      row.tags ?? [],
        date:      formatDate(row.created_at),
        time:      formatTime(row.created_at),
      }));
    },

    async createJournal(data: {
      title: string;
      content: string;
      mood: string;
      moodLabel: string;
      tags: string[];
    }): Promise<JournalEntry> {
      const userId = await requireUserId();
      const { data: row, error } = await supabase
        .from("journal_entries")
        .insert({
          user_id:    userId,
          title:      data.title,
          content:    data.content,
          mood:       data.mood,
          mood_label: data.moodLabel,
          tags:       data.tags,
        })
        .select("id, title, content, mood, mood_label, tags, created_at")
        .single();

      if (error) throw new Error(error.message);

      return {
        id:        row.id,
        title:     row.title,
        content:   row.content,
        mood:      row.mood,
        moodLabel: row.mood_label,
        tags:      row.tags ?? [],
        date:      formatDate(row.created_at),
        time:      formatTime(row.created_at),
      };
    },
  },

  // ── Chat — stored in Supabase ─────────────────────────────────────────────

  chat: {
    /** Get all chat sessions for the current user, newest first. */
    async getSessions(): Promise<ChatSession[]> {
      const userId = await requireUserId();
      const { data, error } = await supabase
        .from("chat_sessions")
        .select("id, title, created_at")
        .eq("user_id", userId)
        .order("created_at", { ascending: false });

      if (error) throw new Error(error.message);
      return (data ?? []).map(s => ({
        id:        s.id,
        title:     s.title,
        createdAt: s.created_at,
      }));
    },

    /** Get all messages for a session, oldest first. */
    async getMessages(sessionId: string): Promise<ChatMessage[]> {
      const { data, error } = await supabase
        .from("chat_messages")
        .select("id, role, text, created_at")
        .eq("session_id", sessionId)
        .order("created_at", { ascending: true });

      if (error) throw new Error(error.message);
      return (data ?? []).map(m => ({
        id:   m.id,
        role: m.role as "ai" | "user",
        text: m.text,
        time: formatTime(m.created_at),
      }));
    },

    /** Create a new chat session and return its id. */
    async createSession(title = "New conversation"): Promise<string> {
      const userId = await requireUserId();
      const { data, error } = await supabase
        .from("chat_sessions")
        .insert({ user_id: userId, title })
        .select("id")
        .single();

      if (error) throw new Error(error.message);
      return data.id;
    },

    /** Update the title of a session (e.g. after first message). */
    async updateSessionTitle(sessionId: string, title: string): Promise<void> {
      const { error } = await supabase
        .from("chat_sessions")
        .update({ title })
        .eq("id", sessionId);
      if (error) throw new Error(error.message);
    },

    /**
     * Save a message to Supabase and return it as a ChatMessage.
     * Use role "user" for user messages, "ai" for bot replies.
     */
    async saveMessage(sessionId: string, text: string, role: "ai" | "user"): Promise<ChatMessage> {
      const userId = await requireUserId();
      const { data, error } = await supabase
        .from("chat_messages")
        .insert({ session_id: sessionId, user_id: userId, role, text })
        .select("id, role, text, created_at")
        .single();

      if (error) throw new Error(error.message);
      return {
        id:   data.id,
        role: data.role as "ai" | "user",
        text: data.text,
        time: formatTime(data.created_at),
      };
    },

    /**
     * Send a user message, save it, generate an AI reply, save that too.
     * Returns the AI reply message.
     * Replace the reply logic here when the FastAPI AI backend is ready.
     */
    async send(sessionId: string, userText: string): Promise<ChatMessage> {
      // Save user message
      await api.chat.saveMessage(sessionId, userText, "user");

      // Generate AI reply (mock — replace with real AI call later)
      const replies = [
        "That's really insightful. How long have you been feeling this way?",
        "I understand. It takes courage to acknowledge these feelings. 💜",
        "Let's explore that together. What do you think triggered this?",
        "You're doing great by talking about this. Remember, healing isn't linear.",
        "Have you tried any grounding techniques when you feel overwhelmed?",
        "That sounds really challenging. You're not alone in this journey.",
      ];
      await new Promise(r => setTimeout(r, 1400));
      const replyText = replies[Math.floor(Math.random() * replies.length)];

      // Save AI reply
      const aiMsg = await api.chat.saveMessage(sessionId, replyText, "ai");
      return aiMsg;
    },
  },
};
