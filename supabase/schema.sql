-- ============================================================
-- NeuroNest — Varsha Feature: Wellness Dashboard
-- Supabase Schema (v4) — Users only, no doctor, no community
-- Run this entire file in Supabase → SQL Editor → New query → Run
-- ============================================================

-- ── 1. Drop everything old so we start clean ─────────────────────────────────
drop trigger  if exists on_auth_user_created on auth.users;
drop function if exists public.handle_new_user();

drop table if exists public.chat_messages     cascade;
drop table if exists public.chat_sessions     cascade;
drop table if exists public.community_likes   cascade;
drop table if exists public.community_posts   cascade;
drop table if exists public.journal_entries   cascade;
drop table if exists public.mood_logs         cascade;
drop table if exists public.user_profiles     cascade;
drop table if exists public.patient_profiles  cascade;
drop table if exists public.doctor_profiles   cascade;
drop table if exists public.profiles          cascade;

-- ── 2. profiles ──────────────────────────────────────────────────────────────
-- One row per user. Written automatically by the trigger on signup.
-- role is always 'user' — enforced by CHECK constraint.
create table public.profiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  name       text not null,
  role       text not null default 'user' check (role = 'user'),
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "profiles: select own"
  on public.profiles for select
  using (auth.uid() = id);

create policy "profiles: update own"
  on public.profiles for update
  using (auth.uid() = id);

-- ── 3. user_profiles ─────────────────────────────────────────────────────────
-- Health info collected at signup form.
-- Written by the app immediately after auth.signUp() succeeds.
create table public.user_profiles (
  id             uuid primary key references auth.users(id) on delete cascade,
  age            int,
  sleep_schedule text,                  -- 'early' | 'normal' | 'late' | 'irregular'
  avg_sleep      numeric(4,1),          -- hours per night
  last_visit     date,                  -- optional last doctor visit
  health_issues  text,                  -- free text, optional
  created_at     timestamptz default now()
);

alter table public.user_profiles enable row level security;

create policy "user_profiles: select own"
  on public.user_profiles for select
  using (auth.uid() = id);

create policy "user_profiles: insert own"
  on public.user_profiles for insert
  with check (auth.uid() = id);

create policy "user_profiles: update own"
  on public.user_profiles for update
  using (auth.uid() = id);

-- ── 4. mood_logs ─────────────────────────────────────────────────────────────
-- One row per mood check-in.
-- Powers: streak, wellness score, 7-day chart, monthly check-in count.
create table public.mood_logs (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  mood       text not null,        -- emoji  e.g. "😄"
  mood_label text not null,        -- label  e.g. "Great"
  logged_at  timestamptz default now()
);

alter table public.mood_logs enable row level security;

create policy "mood: select own"
  on public.mood_logs for select
  using (auth.uid() = user_id);

create policy "mood: insert own"
  on public.mood_logs for insert
  with check (auth.uid() = user_id);

-- ── 5. journal_entries ───────────────────────────────────────────────────────
-- Private journal entries. Only the owner can read or write.
create table public.journal_entries (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  title      text not null,
  content    text not null,
  mood       text not null,        -- emoji
  mood_label text not null,        -- text label
  tags       text[] default '{}',
  created_at timestamptz default now()
);

alter table public.journal_entries enable row level security;

create policy "journal: select own"
  on public.journal_entries for select
  using (auth.uid() = user_id);

create policy "journal: insert own"
  on public.journal_entries for insert
  with check (auth.uid() = user_id);

create policy "journal: delete own"
  on public.journal_entries for delete
  using (auth.uid() = user_id);

-- ── 6. chat_sessions ─────────────────────────────────────────────────────────
-- One row per conversation thread.
-- Title auto-updates to the first message text.
create table public.chat_sessions (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  title      text not null default 'New conversation',
  created_at timestamptz default now()
);

alter table public.chat_sessions enable row level security;

create policy "chat_sessions: select own"
  on public.chat_sessions for select
  using (auth.uid() = user_id);

create policy "chat_sessions: insert own"
  on public.chat_sessions for insert
  with check (auth.uid() = user_id);

create policy "chat_sessions: update own"
  on public.chat_sessions for update
  using (auth.uid() = user_id);

create policy "chat_sessions: delete own"
  on public.chat_sessions for delete
  using (auth.uid() = user_id);

-- ── 7. chat_messages ─────────────────────────────────────────────────────────
-- Individual messages inside a session.
-- role is 'user' (typed by person) or 'ai' (NeuroBot reply).
create table public.chat_messages (
  id         uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.chat_sessions(id) on delete cascade,
  user_id    uuid not null references auth.users(id) on delete cascade,
  role       text not null check (role in ('ai', 'user')),
  text       text not null,
  created_at timestamptz default now()
);

alter table public.chat_messages enable row level security;

create policy "chat_messages: select own"
  on public.chat_messages for select
  using (auth.uid() = user_id);

create policy "chat_messages: insert own"
  on public.chat_messages for insert
  with check (auth.uid() = user_id);

-- ── 8. Trigger: auto-create profiles row on signup ───────────────────────────
-- Runs as security definer (superuser) so it can insert into profiles
-- even though the user session does not exist yet at trigger time.
-- $$ dollar-quoting is required — single $ breaks the function body.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, name, role)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', 'User'),
    'user'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row
  execute procedure public.handle_new_user();
