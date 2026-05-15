# NeuroNest — varsha-ui

AI-powered mental wellness platform built with Next.js 16, React 19, TypeScript, Supabase, and Tailwind CSS.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Framework | Next.js (App Router) | 16.2.6 |
| Language | TypeScript | 5 |
| UI Library | React | 19.2.4 |
| Styling | Tailwind CSS + inline styles | 4 |
| Icons | lucide-react | 1.14.0 |
| Database + Auth | Supabase (PostgreSQL) | 2.105.4 |
| Class utilities | clsx + tailwind-merge | latest |
| Font | Inter (Google Fonts) | — |

---

## Running Locally

```bash
cd varsha-ui
npm install
npm run dev
```

App runs at **http://localhost:3000** and redirects to `/login`.

---

## Environment Variables

Create `varsha-ui/.env.local` with:

```env
# FastAPI AI backend (not wired yet — reserved for future integration)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase — get from Supabase Dashboard → Project Settings → API
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
```

---

## Project Structure

```
varsha-ui/
│
├── app/                              ← Next.js App Router (URL routes)
│   ├── layout.tsx                    ← Root layout — loads Inter font, wraps in UserProvider
│   ├── page.tsx                      ← / → redirects to /login
│   ├── globals.css                   ← Design tokens, keyframes, reusable CSS classes
│   │
│   ├── (auth)/                       ← Route group — no URL prefix
│   │   ├── layout.tsx                ← Split-screen: left hero panel + right form panel
│   │   ├── login/page.tsx            ← /login
│   │   └── signup/page.tsx           ← /signup
│   │
│   └── (patient)/                    ← Route group — no URL prefix
│       ├── layout.tsx                ← Wraps all user pages in AppLayout (sidebar + content)
│       ├── dashboard/page.tsx        ← /dashboard
│       ├── chat/page.tsx             ← /chat
│       ├── journal/page.tsx          ← /journal
│       └── voice/page.tsx            ← /voice
│
├── components/
│   ├── auth/
│   │   ├── LoginPage.tsx             ← Email + password login form
│   │   └── SignupPage.tsx            ← Full registration form with health info
│   │
│   ├── patient/
│   │   ├── PatientDashboard.tsx      ← Main dashboard (stats, mood logger, chart, quick access)
│   │   ├── ChatPage.tsx              ← AI chat with session history
│   │   ├── JournalPage.tsx           ← Private journal (create + list entries)
│   │   └── VoicePage.tsx             ← Voice assistant UI (mock — no real recording yet)
│   │
│   ├── layout/
│   │   ├── AppLayout.tsx             ← Sidebar + main content shell
│   │   ├── Sidebar.tsx               ← Collapsible left nav (4 links)
│   │   └── Navbar.tsx                ← Top bar component (available, not used in main pages)
│   │
│   └── ui/
│       ├── Button.tsx                ← Reusable button (primary / outline / ghost variants)
│       ├── Card.tsx                  ← White card wrapper
│       └── InputField.tsx            ← Labeled input with error display
│
├── context/
│   ├── UserContext.tsx               ← Global user state: name, role, avatar, logout()
│   └── SidebarContext.tsx            ← Sidebar collapsed/expanded state
│
├── lib/
│   ├── api.ts                        ← All Supabase API calls (auth, user, chat)
│   ├── supabase.ts                   ← Supabase client singleton
│   ├── mockData.ts                   ← Fallback mock data (kept for reference)
│   └── utils.ts                      ← cn() helper (clsx + tailwind-merge)
│
├── supabase_schema.sql               ← Full DB schema — run this in Supabase SQL Editor
├── .env.local                        ← Credentials (never commit to git)
├── next.config.ts                    ← Next.js config (dev indicator disabled)
├── tsconfig.json                     ← TypeScript config (strict, @/* path alias)
└── package.json                      ← Dependencies and scripts
```

---

## Pages and What They Do

### `/login`
Email + password form. No role toggle — everyone is a user. Calls `api.login()`, stores the Supabase access token in `localStorage["nn_token"]`, sets user in context, redirects to `/dashboard`.

### `/signup`
Full registration form with two sections:

**Account info (required):** First name, Last name, Age, Email, Password

**Health info (optional):** Sleep schedule, Average sleep hours, Last visit date, Existing health issues

On submit calls `api.signup.user()` which creates the Supabase auth user and saves health data to `user_profiles`.

### `/dashboard`
The main hub. Shows:
- Time-based greeting with user's first name
- Welcome banner — shows onboarding message for new users, streak message for returning users
- 4 stat cards: Wellness Score, Weekly Streak, Sleep Average, Mood Check-ins
- Mood logger — 5 emoji buttons (😄 Great, 🙂 Good, 😐 Okay, 😔 Low, 😢 Rough) + Log Mood button
- 7-day mood trend bar chart
- Quick access cards linking to Chat, Journal, Voice
- Recent activity section (only visible after first mood log)

All stats are real — loaded from Supabase on mount. New users see `—` and "Log a mood to start" until they have data.

### `/chat`
AI chat interface with persistent session history.
- Left panel: list of past conversations, + button to start new one
- Right panel: message thread with NeuroBot
- Sessions auto-open the most recent one on load
- Session title updates to the first message text
- Messages are saved to Supabase (both user and AI replies)
- AI replies are currently mocked (random responses, 1.4s delay) — will be replaced with real AI backend

### `/journal`
Private journal. Entries are stored in Supabase and only visible to the logged-in user.
- New entry form: title (required), mood selector, content (required), tags (optional)
- Tags can be added by typing and pressing Enter or clicking Add
- Entries list shows mood emoji, title, content preview, date, time, mood label, tags
- Empty state shown for new users

### `/voice`
Voice assistant UI — currently a visual demo only.
- Animated waveform
- Large mic button with pulse animation when "recording"
- Quick prompt buttons
- Shows a mock transcript after 3 seconds
- No real voice recording or transcription yet

---

## Sidebar Navigation

4 links — no community, no doctor:

| Icon | Label | Route |
|---|---|---|
| LayoutDashboard | Dashboard | `/dashboard` |
| MessageCircle | AI Chat | `/chat` |
| BookOpen | Journal | `/journal` |
| Mic | Voice | `/voice` |

The sidebar is collapsible. Collapsed width: 68px (icons only). Expanded width: 220px (icons + labels). State is shared via `SidebarContext` so the main content margin adjusts in sync.

---

## Supabase Database Schema

6 tables. No doctor tables. No community tables. Run `supabase_schema.sql` in Supabase SQL Editor to create them.

### `profiles`
Auto-created by trigger when a user signs up. Never written by the app directly.

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key, FK to auth.users |
| name | text | Full name from signup |
| role | text | Always `'user'` — enforced by CHECK constraint |
| created_at | timestamptz | Auto |

### `user_profiles`
Health info collected at signup. Written by the app after `auth.signUp()` succeeds.

| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key, FK to auth.users |
| age | int | Optional |
| sleep_schedule | text | `early` / `normal` / `late` / `irregular` |
| avg_sleep | numeric(4,1) | Hours per night |
| last_visit | date | Last doctor visit (optional) |
| health_issues | text | Free text (optional) |
| created_at | timestamptz | Auto |

### `mood_logs`
One row per mood check-in. Powers the streak, wellness score, chart, and monthly count.

| Column | Type | Notes |
|---|---|---|
| id | uuid | Auto-generated |
| user_id | uuid | FK to auth.users |
| mood | text | Emoji e.g. `"😄"` |
| mood_label | text | Text e.g. `"Great"` |
| logged_at | timestamptz | Auto |

**Mood → score mapping used for wellness calculations:**
- Great → 90, Good → 75, Okay → 55, Low → 35, Rough → 20

### `journal_entries`
Private journal entries. Only the owner can read or write.

| Column | Type | Notes |
|---|---|---|
| id | uuid | Auto-generated |
| user_id | uuid | FK to auth.users |
| title | text | Required |
| content | text | Required |
| mood | text | Emoji |
| mood_label | text | Text label |
| tags | text[] | Array of tag strings, default `{}` |
| created_at | timestamptz | Auto |

### `chat_sessions`
One row per conversation thread.

| Column | Type | Notes |
|---|---|---|
| id | uuid | Auto-generated |
| user_id | uuid | FK to auth.users |
| title | text | Defaults to `'New conversation'`, updates to first message text |
| created_at | timestamptz | Auto |

### `chat_messages`
Individual messages inside a session.

| Column | Type | Notes |
|---|---|---|
| id | uuid | Auto-generated |
| session_id | uuid | FK to chat_sessions |
| user_id | uuid | FK to auth.users |
| role | text | `'user'` or `'ai'` — enforced by CHECK constraint |
| text | text | Message content |
| created_at | timestamptz | Auto |

### Trigger: `handle_new_user`
Fires after every insert into `auth.users`. Creates the `profiles` row automatically using `security definer` (runs as superuser, bypasses RLS). Uses `$$` dollar-quoting — required for PostgreSQL function bodies.

### Row Level Security
Every table has RLS enabled. Users can only read and write their own rows. No public tables.

---

## API Client (`lib/api.ts`)

All Supabase calls go through `lib/api.ts`. Components never import `supabase` directly.

```ts
// ── Auth ──────────────────────────────────────────────────────────────────
api.login(email, password)
// → signInWithPassword + fetch profiles row → returns AuthResponse

api.me()
// → getUser() + fetch profiles row → restores session on app mount

api.signup.user({
  firstName, lastName, age, email, password,
  sleepSchedule, avgSleep, lastVisit, healthIssues
})
// → signUp() + insert user_profiles row → returns AuthResponse

// ── Dashboard ─────────────────────────────────────────────────────────────
api.user.dashboard()
// → reads user_profiles (sleep avg) + mood_logs (streak, chart, score, count)
// → returns UserDashboardData

api.user.logMood(mood, moodLabel)
// → inserts into mood_logs

// ── Journal ───────────────────────────────────────────────────────────────
api.user.getJournals()
// → selects from journal_entries ordered by created_at desc

api.user.createJournal({ title, content, mood, moodLabel, tags })
// → inserts into journal_entries, returns the new row

// ── Chat ──────────────────────────────────────────────────────────────────
api.chat.getSessions()
// → selects from chat_sessions ordered by created_at desc

api.chat.getMessages(sessionId)
// → selects from chat_messages for session, ordered oldest first

api.chat.createSession(title?)
// → inserts into chat_sessions, returns new id

api.chat.updateSessionTitle(sessionId, title)
// → updates chat_sessions.title

api.chat.saveMessage(sessionId, text, role)
// → inserts into chat_messages, returns the saved message

api.chat.send(sessionId, userText)
// → saves user message → generates mock AI reply (1.4s delay) → saves AI reply
// → replace reply logic with real AI call when backend is ready
```

---

## State Management

### `UserContext`
Stores the logged-in user globally. Available everywhere via `useUser()`.

```ts
const { user, setUser, logout } = useUser();

// user shape:
{ name: string; role: "user"; avatar: string }
```

On app mount: checks `localStorage["nn_token"]`, calls `api.me()` to restore session from Supabase. Falls back to `localStorage["nn_user"]` if the API call fails (e.g. expired token).

`logout()` calls `supabase.auth.signOut()`, clears both localStorage keys, resets user to default.

### `SidebarContext`
Stores sidebar collapsed state. Available via `useSidebar()`.

```ts
const { collapsed, toggle } = useSidebar();
```

Used by `Sidebar.tsx` (to show/hide labels) and `AppLayout.tsx` (to set `marginLeft` on main content).

---

## Styling System

**Tailwind CSS 4** for utility classes. **Inline styles** for components where CSS purging could cause issues (auth forms, dashboard cards).

**Design tokens** defined in `globals.css` as CSS custom properties:

```css
--primary:       #7c3aed   /* violet */
--accent:        #3b82f6   /* blue */
--bg:            #f5f3ff   /* light purple background */
--surface:       #ffffff
--text:          #1e1b4b
--muted:         #6b7280
```

**Keyframe animations** defined in `globals.css`:
- `fadeUp` — elements slide up on appear
- `fadeIn` — opacity fade
- `pulse-ring` — expanding ring (voice page mic button)
- `wave` — waveform bars (voice page)
- `typing` — bouncing dots (chat typing indicator)
- `spin` — loading spinner

**Gradient pattern** used throughout: `linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)`

---

## Supabase Setup (Manual Steps)

1. Go to **Supabase → SQL Editor → New query**
2. Paste the full contents of `supabase_schema.sql` and click **Run**
3. Go to **Authentication → Providers → Email**
4. Toggle **"Confirm email"** to **OFF** → Save

If you see "Database error saving new user" on signup, the trigger is broken. Re-run the schema SQL — it drops and recreates everything cleanly.

---

## What's Real vs What's Mock

| Feature | Status | Details |
|---|---|---|
| Sign up | ✅ Real | Supabase auth + user_profiles insert |
| Login | ✅ Real | Supabase auth + profiles fetch |
| Session restore on refresh | ✅ Real | Supabase getUser() + profiles fetch |
| Logout | ✅ Real | Supabase signOut() + localStorage clear |
| Dashboard stats | ✅ Real | Calculated from mood_logs + user_profiles |
| Mood logging | ✅ Real | Inserts into mood_logs |
| Journal read | ✅ Real | Fetches from journal_entries |
| Journal create | ✅ Real | Inserts into journal_entries |
| Chat sessions | ✅ Real | Stored in chat_sessions |
| Chat messages | ✅ Real | Stored in chat_messages |
| AI chat replies | ⚠️ Mock | Random strings, 1.4s delay — replace with FastAPI |
| Voice recording | ⚠️ Mock | UI only, 3s fake recording — no real audio |

---


---

## For Future Development

**Wire up real AI chat:**
In `lib/api.ts`, find `api.chat.send()`. Replace the mock reply block with a real call to `NEXT_PUBLIC_API_URL/chat/send`. The session and message saving logic stays the same.

**Wire up voice:**
`VoicePage.tsx` has the full UI ready. Add Web Speech API (`SpeechRecognition`) or connect to a backend transcription service. The transcript display is already built.

**Add more features:**
The database schema is clean and extensible. New tables follow the same RLS pattern — enable RLS, add `select own` and `insert own` policies using `auth.uid()`.

**Deploy:**
```bash
npm run build
npm run start
```

Set the same `.env.local` variables in your deployment environment (Vercel, etc.).
