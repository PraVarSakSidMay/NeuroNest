-- ============================================================
-- DEMO SETUP - Run this in Supabase SQL Editor
-- ============================================================
-- This script will:
-- 1. Drop existing tables (if any)
-- 2. Create new tables WITHOUT foreign key constraints
-- 3. Disable RLS for demo mode
-- ============================================================

-- Step 1: Drop existing tables
DROP TABLE IF EXISTS emotional_summaries CASCADE;
DROP TABLE IF EXISTS journal_entries CASCADE;

-- Step 2: Create journal_entries table (DEMO VERSION - No foreign keys)
CREATE TABLE journal_entries (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL,
  title       TEXT,
  content     TEXT        NOT NULL,
  mood        TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Disable RLS for demo mode
ALTER TABLE journal_entries DISABLE ROW LEVEL SECURITY;

-- Create index for efficient queries
CREATE INDEX idx_journal_entries_user_created
  ON journal_entries (user_id, created_at);

-- Step 3: Create emotional_summaries table (DEMO VERSION - No foreign keys)
CREATE TABLE emotional_summaries (
  id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID        NOT NULL,
  selected_range        JSONB       NOT NULL,
  generated_summary     TEXT        NOT NULL,
  emotional_patterns    TEXT        NOT NULL DEFAULT '',
  positive_observations TEXT        NOT NULL DEFAULT '',
  gentle_insights       TEXT        NOT NULL DEFAULT '',
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Disable RLS for demo mode
ALTER TABLE emotional_summaries DISABLE ROW LEVEL SECURITY;

-- Done! Tables are ready for demo mode.
