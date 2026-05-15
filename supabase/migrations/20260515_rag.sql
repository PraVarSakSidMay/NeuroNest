-- ============================================================
-- NeuroNest RAG Migration — pgvector Memory Layer
-- ============================================================

-- 1. Enable pgvector extension (available on all Supabase projects)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Add embedding column to interactions table
--    text-embedding-3-small produces 1536-dimensional vectors
ALTER TABLE interactions
    ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- 3. Create IVFFlat index for fast approximate cosine similarity search
--    (only effective once there are enough rows; safe to create now)
CREATE INDEX IF NOT EXISTS interactions_embedding_idx
    ON interactions
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 4. match_interactions RPC
--    Called by the RAG service to retrieve top-k semantically similar past turns
--    for a specific user, excluding the current interaction (if provided).
CREATE OR REPLACE FUNCTION match_interactions(
    query_embedding   vector(1536),
    match_user_id     UUID,
    match_count       INT DEFAULT 5,
    exclude_session   UUID DEFAULT NULL
)
RETURNS TABLE (
    id                UUID,
    transcript        TEXT,
    emotion           TEXT,
    stress_level      INTEGER,
    tone              TEXT,
    hidden_emotion    TEXT,
    response_text     TEXT,
    created_at        TIMESTAMPTZ,
    similarity        FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.transcript,
        i.emotion,
        i.stress_level,
        i.tone,
        i.hidden_emotion,
        i.response_text,
        i.created_at,
        1 - (i.embedding <=> query_embedding) AS similarity
    FROM interactions i
    WHERE
        i.user_id = match_user_id
        AND i.embedding IS NOT NULL
        AND (exclude_session IS NULL OR i.session_id != exclude_session)
    ORDER BY i.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 5. get_last_session_emotion — returns the final emotion from the most recent
--    *completed* session (i.e., any session other than the current one)
CREATE OR REPLACE FUNCTION get_last_session_emotion(
    lookup_user_id UUID,
    current_session UUID DEFAULT NULL
)
RETURNS TABLE (
    emotion       TEXT,
    stress_level  INTEGER,
    created_at    TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.emotion,
        i.stress_level,
        i.created_at
    FROM interactions i
    WHERE
        i.user_id = lookup_user_id
        AND i.emotion IS NOT NULL
        AND (current_session IS NULL OR i.session_id != current_session)
    ORDER BY i.created_at DESC
    LIMIT 1;
END;
$$;
