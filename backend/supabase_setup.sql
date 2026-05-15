-- NeuroNest — Supabase Database Setup
-- Run this entire file in your Supabase SQL Editor
-- Dashboard → SQL Editor → New Query → paste this → Run

-- ── Set timezone to UTC (Supabase default, ensures consistent timestamps) ────
SET timezone = 'UTC';

-- ── Drop existing tables if they exist (clean slate) ─────────────────────────
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;

-- ── Tables ────────────────────────────────────────────────────────────────────

CREATE TABLE chat_sessions (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     TEXT        NOT NULL,
    session_id  TEXT        NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id                UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id        TEXT        NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    user_id           TEXT        NOT NULL,
    role              TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
    content_encrypted TEXT        NOT NULL,
    emotion           TEXT,
    mood_level        TEXT,
    response_mode     TEXT,
    created_at        TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'UTC')
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_user    ON chat_messages(user_id);
CREATE INDEX idx_chat_sessions_user    ON chat_sessions(user_id);

-- ── Row Level Security ────────────────────────────────────────────────────────

ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- ── RLS Policies ─────────────────────────────────────────────────────────────
-- IMPORTANT: These policies allow the service_role key (used by backend) to
-- bypass RLS entirely. The anon key is restricted.
-- For testing without auth, we allow all operations via service_role.

-- Allow service role full access (backend uses service_role key)
CREATE POLICY "Service role full access to sessions"
    ON chat_sessions FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access to messages"
    ON chat_messages FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow authenticated users to see only their own data
CREATE POLICY "Users see own sessions"
    ON chat_sessions FOR ALL
    TO authenticated
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users see own messages"
    ON chat_messages FOR ALL
    TO authenticated
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);

-- ── Verification: run this after sending messages to confirm encryption ───────
-- SELECT
--     id,
--     role,
--     emotion,
--     LEFT(content_encrypted, 60) || '...' AS stored_value,
--     LENGTH(content_encrypted)            AS encrypted_length,
--     created_at
-- FROM chat_messages
-- ORDER BY created_at DESC
-- LIMIT 10;
