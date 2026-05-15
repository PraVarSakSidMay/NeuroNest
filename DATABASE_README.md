# NeuroNest — Database & Encryption Documentation

## Overview

NeuroNest uses **Supabase (PostgreSQL)** as the database. All conversation content is **AES-256-GCM encrypted before being sent to Supabase** — the database never stores plaintext. Even Supabase admins cannot read user conversations.

---

## Encryption Algorithm — AES-256-GCM

### What is AES-256-GCM?

| Property | Value |
|----------|-------|
| Algorithm | AES (Advanced Encryption Standard) |
| Key size | 256 bits (32 bytes) |
| Mode | GCM (Galois/Counter Mode) |
| Nonce size | 12 bytes (96 bits) |
| Auth tag | 16 bytes (128 bits) |
| Security level | Military-grade, same as HTTPS/TLS |

**AES-256** is the encryption standard used by:
- HTTPS (every website you visit)
- Banking and financial systems
- Military communications
- WhatsApp end-to-end encryption

**GCM mode** adds two important properties:
1. **Authenticated encryption** — the 16-byte auth tag detects any tampering with stored data
2. **Parallelizable** — fast encryption/decryption

---

## Key Derivation — HKDF-SHA256

### Why key derivation?

Instead of using one master key for all users, we derive a **unique 256-bit key per user** using HKDF (HMAC-based Key Derivation Function).

```
Master Key (SECRET_KEY from .env)
         +
User ID (e.g. "user-123")
         │
         ▼
HKDF-SHA256
         │
         ▼
Unique 256-bit key for "user-123"
```

**Benefits**:
- Compromising one user's key doesn't affect other users
- The master key never leaves the server
- Same user always gets the same derived key (deterministic)
- Different users get completely different keys

### HKDF Parameters

```python
HKDF(
    algorithm = SHA-256,
    length    = 32 bytes (256 bits),
    salt      = None,
    info      = b"neuronest-chat-{user_id}"
)
```

---

## Encryption Process — Step by Step

### Encrypting a message

```
Input: "I am feeling very stressed about my exams"
User ID: "user-123"

Step 1: Derive key
  HKDF(SECRET_KEY + "user-123") → 32-byte key

Step 2: Generate nonce
  os.urandom(12) → 12 random bytes (unique per message)
  e.g. [0x4d, 0x4e, 0x69, 0x50, 0x64, 0x74, 0x33, 0x46, 0x49, 0x46, 0x59, 0x4b]

Step 3: Encrypt with AES-256-GCM
  AES-256-GCM(key, nonce, plaintext) → ciphertext + 16-byte auth tag

Step 4: Combine and encode
  base64(nonce + ciphertext + auth_tag)
  → "lOtlkzRthSdphIFB8VKFg1PQRhjdpJ4xG634X5RDJpKRHHuvCu..."

Step 5: Store in Supabase
  content_encrypted = "lOtlkzRthSdphIFB8VKFg1PQRhjdpJ4xG634X5RDJpKRHHuvCu..."
```

### Decrypting a message

```
Input: "lOtlkzRthSdphIFB8VKFg1PQRhjdpJ4xG634X5RDJpKRHHuvCu..."
User ID: "user-123"

Step 1: Derive same key
  HKDF(SECRET_KEY + "user-123") → same 32-byte key

Step 2: Decode and split
  base64_decode → bytes
  bytes[0:12]  → nonce
  bytes[12:]   → ciphertext + auth_tag

Step 3: Decrypt and verify
  AES-256-GCM.decrypt(key, nonce, ciphertext+auth_tag)
  → "I am feeling very stressed about my exams"
  (GCM automatically verifies auth tag — fails if tampered)
```

### Security properties

| Property | Explanation |
|----------|-------------|
| **Confidentiality** | Only someone with SECRET_KEY + correct user_id can decrypt |
| **Integrity** | GCM auth tag detects any modification to stored data |
| **Uniqueness** | Same message encrypted twice → different ciphertext (unique nonces) |
| **User isolation** | Different user_id → different derived key → different ciphertext |
| **Forward secrecy** | Each message has its own nonce — compromising one doesn't help others |

---

## Database Schema

### Table: `chat_sessions`

Stores one record per conversation session.

```sql
CREATE TABLE chat_sessions (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     TEXT        NOT NULL,
    session_id  TEXT        NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at  TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'UTC')
);
```

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Auto-generated primary key |
| `user_id` | TEXT | The user who owns this session |
| `session_id` | TEXT | Unique session identifier (from frontend) |
| `created_at` | TIMESTAMPTZ | Session start time (UTC) |
| `updated_at` | TIMESTAMPTZ | Last activity time (UTC) |

---

### Table: `chat_messages`

Stores every individual message — both user messages and AI responses.

```sql
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
```

| Column | Type | Encrypted? | Description |
|--------|------|-----------|-------------|
| `id` | UUID | No | Auto-generated primary key |
| `session_id` | TEXT | No | Links to `chat_sessions.session_id` |
| `user_id` | TEXT | No | The user who owns this message |
| `role` | TEXT | No | `'user'` or `'assistant'` |
| `content_encrypted` | TEXT | **YES** | AES-256-GCM ciphertext of the message |
| `emotion` | TEXT | No | Detected emotion (e.g. `stressed`) — not sensitive |
| `mood_level` | TEXT | No | Detected mood (e.g. `bad`) — not sensitive |
| `response_mode` | TEXT | No | `support`, `celebrate`, or `reflect` (assistant only) |
| `created_at` | TIMESTAMPTZ | No | Message timestamp (UTC) |

**Why emotion and mood_level are NOT encrypted**: These are used for analytics and are not personally sensitive. Knowing someone felt "stressed" without knowing what they said is not a privacy risk.

**Why response_mode is NULL for user messages**: `response_mode` only applies to assistant responses. User messages don't have a response mode.

---

## Relationships

```
chat_sessions (1)
      │
      │  One session has many messages
      │  (CASCADE DELETE — deleting a session deletes all its messages)
      │
      └──── chat_messages (many)
             session_id → chat_sessions.session_id
```

**One-to-many relationship**: One `chat_sessions` row → many `chat_messages` rows.

Every message belongs to exactly one session. If a session is deleted, all its messages are automatically deleted (CASCADE).

---

## Indexes

```sql
-- Fast lookup of all messages in a session
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);

-- Fast lookup of all messages by a user
CREATE INDEX idx_chat_messages_user ON chat_messages(user_id);

-- Fast lookup of all sessions by a user
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
```

These indexes make queries like "get all messages for session X" and "get all sessions for user Y" fast even with millions of rows.

---

## Row Level Security (RLS)

RLS is a PostgreSQL feature that enforces access control at the database level — even if someone gets a valid JWT token, they can only see their own rows.

```sql
-- Service role (backend) has full access — bypasses RLS
CREATE POLICY "Service role full access to sessions"
    ON chat_sessions FOR ALL TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access to messages"
    ON chat_messages FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- Authenticated users can only see their own data
CREATE POLICY "Users see own sessions"
    ON chat_sessions FOR ALL TO authenticated
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users see own messages"
    ON chat_messages FOR ALL TO authenticated
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);
```

**Two-tier access**:
1. **Service role key** (used by backend) — bypasses RLS, full access
2. **Authenticated users** (via Supabase Auth JWT) — can only see rows where `user_id = auth.uid()`

---

## What Supabase Stores vs What Users See

### In the Supabase Table Editor

```
id          | role      | content_encrypted                              | emotion  | mood_level
------------|-----------|------------------------------------------------|----------|----------
uuid-1      | user      | lOtlkzRthSdphIFB8VKFg1PQRhjdpJ4xG634X5RDJpKR | stressed | bad
uuid-2      | assistant | XkR9mPqL2vNwYtBcZs7dFhJqKmNpRtWxYzAbCdEfGhIj | stressed | bad
```

The `content_encrypted` column contains **unreadable base64-encoded ciphertext**. No one can read the actual messages from the database.

### After decryption (what the user sees)

```
role      | content
----------|----------------------------------------------------------
user      | "I am feeling very stressed about my exams"
assistant | "That sounds really exhausting — carrying all of that..."
```

---

## Timestamp Handling

All timestamps are stored in **UTC** using `TIMESTAMPTZ` (timestamp with timezone).

- Supabase Table Editor shows: `2026-05-14 07:51:19.211006+00`
- The `+00` means UTC
- For India (IST = UTC+5:30): add 5 hours 30 minutes
- `07:51 UTC` = `13:21 IST`

**To view in IST in Supabase SQL Editor**:
```sql
SELECT
    id,
    role,
    emotion,
    created_at AT TIME ZONE 'Asia/Kolkata' AS created_at_IST
FROM chat_messages
ORDER BY created_at DESC
LIMIT 20;
```

**Why timestamps are correct**: The backend does NOT send `created_at` — Supabase uses `DEFAULT NOW() AT TIME ZONE 'UTC'` which is always accurate server time.

---

## Verification Queries

Run these in Supabase SQL Editor to verify everything is working:

### Check data is stored
```sql
SELECT COUNT(*) FROM chat_messages;
SELECT COUNT(*) FROM chat_sessions;
```

### Confirm data is encrypted (content_encrypted should be unreadable)
```sql
SELECT
    id,
    role,
    emotion,
    LEFT(content_encrypted, 60) || '...' AS stored_value,
    LENGTH(content_encrypted) AS encrypted_length,
    created_at
FROM chat_messages
ORDER BY created_at DESC
LIMIT 10;
```

### Check a specific session
```sql
SELECT
    m.role,
    m.emotion,
    m.mood_level,
    m.response_mode,
    LEFT(m.content_encrypted, 40) || '...' AS ciphertext,
    m.created_at AT TIME ZONE 'Asia/Kolkata' AS time_IST
FROM chat_messages m
WHERE m.session_id = 'your-session-id'
ORDER BY m.created_at ASC;
```

### Check RLS is enabled
```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('chat_sessions', 'chat_messages');
```

---

## FastAPI Verification Endpoints

Use these to prove encryption is working without writing SQL:

| Endpoint | What it proves |
|----------|---------------|
| `POST /api/db/test-encryption` | Encryption/decryption round-trip works |
| `GET /api/db/raw/{session_id}` | Supabase stores only ciphertext |
| `GET /api/db/verify/{session_id}` | Ciphertext vs plaintext side-by-side |
| `GET /api/db/history/{session_id}` | Correct user can decrypt their data |
| `GET /api/db/health` | Supabase connection is working |

---

## Setup Instructions

### Step 1 — Create Supabase project
1. Go to [supabase.com](https://supabase.com) → New Project
2. Name: `neuronest`, choose region closest to you

### Step 2 — Get API keys
1. Settings → API → Legacy anon, service_role API keys tab
2. Copy: Project URL, anon key, service_role key

### Step 3 — Run SQL setup
1. SQL Editor → New Query
2. Paste contents of `backend/supabase_setup.sql`
3. Click Run → "Success. No rows returned"

### Step 4 — Add to .env
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
SECRET_KEY=your-32-char-minimum-secret-key
```

### Step 5 — Verify
```
GET http://localhost:8000/api/db/health
```
Should return `"supabase_configured": true`

---

## Security Summary

| Threat | Protection |
|--------|-----------|
| Database breach | AES-256-GCM encryption — ciphertext is useless without key |
| Key theft | HKDF per-user keys — one key doesn't expose others |
| Data tampering | GCM auth tag — any modification causes decryption failure |
| Unauthorized access | RLS policies — users can only see their own rows |
| Replay attacks | Unique nonce per message — same plaintext → different ciphertext |
| Admin snooping | Zero-knowledge — even Supabase admins see only ciphertext |
