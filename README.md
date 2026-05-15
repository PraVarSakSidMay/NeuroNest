# NeuroNest — Varsha's Feature: Wellness Dashboard UI

> **Branch:** `varsha-wellness-ui`
> **Contributor:** Varsha
> **Feature:** Full wellness dashboard frontend with Supabase auth, mood tracking, journaling, and AI chat

---

## What This Feature Does

A complete mental wellness frontend built with Next.js 16 + React 19 + TypeScript + Supabase. Users can sign up, log their mood daily, write private journal entries, and chat with NeuroBot (AI chat). All data is stored in Supabase and is private to each user.

---

## Folder Structure

```
varsha-wellness-ui/          ← this branch root
├── frontend/                ← Next.js app (all UI code)
│   ├── app/                 ← Next.js App Router (pages + layouts)
│   ├── components/          ← React components
│   ├── context/             ← React Context (user state, sidebar state)
│   ├── lib/                 ← API client, Supabase client, utilities
│   ├── public/              ← Static assets
│   ├── .env.example         ← Copy to .env.local and fill in credentials
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                 ← Backend placeholder (AI integration coming soon)
│
├── supabase/
│   └── schema.sql           ← Full database schema — run in Supabase SQL Editor
│
└── README.md                ← This file
```

---

## Architecture

```
Browser (Next.js 16)
    │
    ├── /login  ──────────────────────────────────────────────────────────────┐
    ├── /signup ──────────────────────────────────────────────────────────────┤
    │                                                                          │
    │   Auth via Supabase Auth (email + password)                             │
    │   Token stored in localStorage["nn_token"]                              │
    │                                                                          ▼
    ├── /dashboard ──── api.user.dashboard() ──── Supabase: mood_logs
    │                                                        user_profiles
    │
    ├── /chat ────────── api.chat.*() ──────────── Supabase: chat_sessions
    │                                                         chat_messages
    │
    ├── /journal ───────api.user.getJournals()  ── Supabase: journal_entries
    │                   api.user.createJournal()
    │
    └── /voice ─────────── UI only (no backend yet)


State Management:
    UserContext     → logged-in user (name, role, avatar)
    SidebarContext  → sidebar collapsed/expanded

All Supabase calls go through lib/api.ts — components never call supabase directly.
```

---

## Database Schema

6 tables in Supabase (PostgreSQL). Full SQL is in `supabase/schema.sql`.

| Table | Purpose |
|---|---|
| `profiles` | One row per user. Auto-created by trigger on signup. Stores name + role (`'user'`). |
| `user_profiles` | Health info from signup: age, sleep schedule, avg sleep, last visit, health issues. |
| `mood_logs` | Every mood check-in. Emoji + label + timestamp. Powers streak, chart, wellness score. |
| `journal_entries` | Private journal entries with title, content, mood, tags. |
| `chat_sessions` | One row per conversation. Title = first message text. |
| `chat_messages` | Individual messages per session. Role = `'user'` or `'ai'`. |

### Mood → Score Mapping (used for wellness score calculation)

| Mood | Label | Score |
|---|---|---|
| 😄 | Great | 90 |
| 🙂 | Good | 75 |
| 😐 | Okay | 55 |
| 😔 | Low | 35 |
| 😢 | Rough | 20 |

**Wellness Score** = average of last 7 mood scores. `null` for new users with no data.
**Streak** = consecutive days ending today that have at least one mood log.

### Row Level Security
All tables have RLS enabled. Users can only read and write their own rows. No public tables.

---

## Pages

| Route | Component | Description |
|---|---|---|
| `/` | — | Redirects to `/login` |
| `/login` | `LoginPage.tsx` | Email + password sign in |
| `/signup` | `SignupPage.tsx` | Registration with health info |
| `/dashboard` | `PatientDashboard.tsx` | Stats, mood logger, chart, quick access |
| `/chat` | `ChatPage.tsx` | AI chat with session history |
| `/journal` | `JournalPage.tsx` | Private journal entries |
| `/voice` | `VoicePage.tsx` | Voice assistant UI (mock) |

---

## How to Run This Feature Locally

### Step 1 — Clone the repo and switch to this branch

```bash
git clone https://github.com/PraVarSakSidMay/NeuroNest.git
cd NeuroNest
git checkout varsha-wellness-ui
```

### Step 2 — Set up Supabase

1. Go to [supabase.com](https://supabase.com) and create a free project
2. Go to **SQL Editor → New query**
3. Paste the contents of `supabase/schema.sql` and click **Run**
4. Go to **Authentication → Providers → Email**
5. Toggle **"Confirm email"** to **OFF** → Save

### Step 3 — Configure environment variables

```bash
cd frontend
cp .env.example .env.local
```

Open `.env.local` and fill in your Supabase values:
- `NEXT_PUBLIC_SUPABASE_URL` — from Supabase Dashboard → Project Settings → API → Project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` — from the same page, under "anon / public" key

### Step 4 — Install dependencies and run

```bash
npm install
npm run dev
```

App runs at **http://localhost:3000**

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Framework | Next.js (App Router) | 16.2.6 |
| Language | TypeScript | 5 |
| UI Library | React | 19.2.4 |
| Styling | Tailwind CSS 4 + inline styles | 4 |
| Icons | lucide-react | 1.14.0 |
| Database + Auth | Supabase | 2.105.4 |
| Utilities | clsx + tailwind-merge | latest |

---

## Integration with Other Team Members' Features

This frontend is designed to integrate with the team's shared Supabase project and FastAPI backend.

- **Supabase URL/Key** — use the shared team Supabase project credentials in `.env.local`
- **FastAPI backend** — `NEXT_PUBLIC_API_URL` in `.env.local` points to the backend. Currently unused — AI chat replies are mocked. When the backend is ready, update `api.chat.send()` in `frontend/lib/api.ts` to call the real endpoint.
- **No conflicts** — this feature only creates tables prefixed with user data (`profiles`, `user_profiles`, `mood_logs`, `journal_entries`, `chat_sessions`, `chat_messages`). No overlap with other features' tables.

---

## What's Not Done Yet

- **Real AI chat** — replies are random strings with 1.4s delay. Replace `api.chat.send()` with a real FastAPI call.
- **Voice recording** — UI is built, no actual audio capture or transcription.
- **Mobile responsiveness** — optimized for desktop, some pages need mobile polish.
