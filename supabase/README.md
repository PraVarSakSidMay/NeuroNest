# Supabase Setup — NeuroNest Reflective Journal

This directory contains the SQL migration files for the NeuroNest Reflective Journal feature.

---

## Prerequisites

- A Supabase project (cloud or local via the Supabase CLI)
- The [Supabase CLI](https://supabase.com/docs/guides/cli) installed (`npm install -g supabase`)

---

## Applying the Migration

### Option 1 — Supabase CLI (recommended for local development)

1. Link your project (first time only):
   ```bash
   supabase link --project-ref <your-project-ref>
   ```

2. Push all pending migrations to your linked project:
   ```bash
   supabase db push
   ```

   Or, to apply migrations against a local Supabase instance started with `supabase start`:
   ```bash
   supabase db reset
   ```

### Option 2 — Supabase Dashboard SQL Editor

1. Open your project in the [Supabase Dashboard](https://app.supabase.com).
2. Navigate to **SQL Editor**.
3. Copy the contents of `migrations/001_journal_schema.sql`.
4. Paste into the editor and click **Run**.

### Option 3 — psql (direct connection)

```bash
psql "$DATABASE_URL" -f supabase/migrations/001_journal_schema.sql
```

Replace `$DATABASE_URL` with your Supabase PostgreSQL connection string (found in **Project Settings → Database**).

---

## Migration Files

| File | Description |
|------|-------------|
| `migrations/001_journal_schema.sql` | Creates `journal_entries` and `emotional_summaries` tables, enables RLS, creates access policies, and adds a composite index on `journal_entries(user_id, created_at)`. |

---

## Schema Overview

### `journal_entries`

Stores encrypted journal entries. Sensitive fields (`title`, `content`, `mood`) are written as AES-256-GCM ciphertext by the FastAPI backend before insertion — the database never sees plaintext.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key, auto-generated |
| `user_id` | UUID | FK → `auth.users(id)`, cascade delete |
| `title` | TEXT | Nullable; AES-256-GCM ciphertext |
| `content` | TEXT NOT NULL | AES-256-GCM ciphertext |
| `mood` | TEXT | Nullable; AES-256-GCM ciphertext |
| `created_at` | TIMESTAMPTZ | Server-set default; client cannot override |

**RLS policy**: `"Users own their entries"` — `auth.uid() = user_id`

**Index**: `idx_journal_entries_user_created` on `(user_id, created_at)` for efficient date-range queries.

### `emotional_summaries`

Stores AI-generated emotional reflection summaries. All sensitive text fields are AES-256-GCM ciphertext. Array fields are JSON-serialized before encryption. `selected_range` is stored as plaintext JSONB (non-sensitive date metadata).

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key, auto-generated |
| `user_id` | UUID | FK → `auth.users(id)`, cascade delete |
| `selected_range` | JSONB NOT NULL | Plaintext `{ preset, startDate, endDate }` |
| `generated_summary` | TEXT NOT NULL | AES-256-GCM ciphertext |
| `emotional_patterns` | TEXT NOT NULL | AES-256-GCM ciphertext of JSON array |
| `positive_observations` | TEXT NOT NULL | AES-256-GCM ciphertext of JSON array |
| `gentle_insights` | TEXT NOT NULL | AES-256-GCM ciphertext of JSON array |
| `created_at` | TIMESTAMPTZ | Server-set default |

**RLS policy**: `"Users own their summaries"` — `auth.uid() = user_id`

---

## Security Notes

- **Row Level Security (RLS)** is enabled on both tables. Every query is automatically scoped to the authenticated user via `auth.uid()`.
- **No plaintext sensitive data** is ever written to the database. Encryption and decryption happen exclusively in the FastAPI backend.
- **Content length and mood enum validation** are enforced at the application layer before encryption — not via database `CHECK` constraints, since stored values are ciphertext.
- The `selected_range` JSONB field is the only non-encrypted field in `emotional_summaries`; it contains only date metadata and no personal content.
