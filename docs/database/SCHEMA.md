# Database Schema

> **Status**: Current as of 2026-01-26
> **Migration Prefix**: 100+ (companion schema)
> **Legacy**: Migrations 001-066 are from Episode-0/fantazy product (retained for reference)

---

## Schema Overview

The companion app uses Supabase (PostgreSQL) with the following tables:

| Table | Purpose | Migration |
|-------|---------|-----------|
| `users` | User profiles and preferences | 100_companion_schema.sql |
| `user_context` | Memory facts (extracted from conversations) | 100_companion_schema.sql |
| `conversations` | Daily conversation threads | 100_companion_schema.sql |
| `companion_messages` | Individual messages (note: NOT `messages`) | 100_companion_schema.sql |
| `scheduled_messages` | Daily check-in scheduler | 100_companion_schema.sql |
| `onboarding` | Onboarding progress tracking | 100_companion_schema.sql |
| `daily_usage` | Free tier usage limits | 100_companion_schema.sql |
| `telegram_link_tokens` | Telegram account linking | 100_companion_schema.sql |
| `user_devices` | Mobile push notification devices | 102_mobile_devices.sql |
| `push_notifications` | Push notification history | 102_mobile_devices.sql |
| `extraction_logs` | Memory/thread extraction observability | 104_extraction_logs.sql |

---

## Core Tables

### users

User profiles extending Supabase auth.users.

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS companion_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_message_time TIME DEFAULT '09:00';
ALTER TABLE users ADD COLUMN IF NOT EXISTS support_style TEXT DEFAULT 'friendly_checkin';
ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'America/New_York';
ALTER TABLE users ADD COLUMN IF NOT EXISTS location TEXT;

-- Telegram integration
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_user_id BIGINT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_username TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_linked_at TIMESTAMPTZ;

-- WhatsApp integration (future)
ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_number TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_linked_at TIMESTAMPTZ;

-- Onboarding
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMPTZ;
```

### user_context

Companion's memory of facts, preferences, goals, and situations.

**Categories**: fact, preference, event, goal, relationship, emotion, situation, routine, struggle, thread, follow_up, pattern

```sql
CREATE TABLE IF NOT EXISTS user_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    importance_score FLOAT DEFAULT 0.5,
    emotional_valence INT DEFAULT 0,  -- -2 to +2
    source TEXT DEFAULT 'extracted',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_referenced_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,

    UNIQUE(user_id, category, key)
);
```

**Note**: Threads and follow-ups are stored in `user_context` with special categories:
- `category = 'thread'`: Ongoing life situations (value is JSON)
- `category = 'follow_up'`: Scheduled follow-up questions
- `category = 'pattern'`: Detected behavioral patterns

### conversations

Daily conversation threads.

```sql
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel TEXT NOT NULL DEFAULT 'web',  -- telegram, whatsapp, web
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    message_count INT DEFAULT 0,
    initiated_by TEXT NOT NULL DEFAULT 'user',  -- companion, user
    mood_summary TEXT,
    topics JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### companion_messages

Individual messages within conversations.

**IMPORTANT**: The actual table is `companion_messages`, NOT `messages`.

```sql
CREATE TABLE IF NOT EXISTS companion_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    telegram_message_id BIGINT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### scheduled_messages

Daily check-in scheduler with priority tracking.

```sql
CREATE TABLE IF NOT EXISTS scheduled_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    content TEXT,
    generation_context JSONB,
    status TEXT DEFAULT 'pending',  -- pending, sent, failed, skipped
    priority_level TEXT,  -- FOLLOW_UP, THREAD, PATTERN, TEXTURE, GENERIC
    failure_reason TEXT,
    conversation_id UUID REFERENCES conversations(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, scheduled_for)
);
```

### user_devices

Mobile device registration for push notifications.

```sql
CREATE TABLE IF NOT EXISTS user_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL,  -- Expo device ID
    platform TEXT NOT NULL,  -- ios, android
    push_token TEXT,  -- Expo push token
    push_token_updated_at TIMESTAMPTZ,
    app_version TEXT,
    os_version TEXT,
    device_model TEXT,
    is_active BOOLEAN DEFAULT true,
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, device_id)
);
```

### extraction_logs

Observability for background memory/thread extraction.

```sql
CREATE TABLE IF NOT EXISTS extraction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL,
    extraction_type TEXT NOT NULL,  -- context, thread
    status TEXT NOT NULL,  -- success, failed
    error_message TEXT,
    items_extracted INTEGER DEFAULT 0,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Legacy Tables (Episode-0)

The following tables exist from the previous Episode-0/fantazy product. They are NOT used by the companion app but migrations are retained for reference:

- `worlds`, `characters`, `series`, `episodes` - Story content
- `sessions`, `engagements`, `messages` - User interactions (note: companion uses `companion_messages`)
- `memory_events`, `hooks` - Memory system (companion uses `user_context`)
- Various seed data tables

**Note**: The `messages` table from Episode-0 is different from `companion_messages`. If you see references to `messages` in code, verify which table is intended.

---

## Database Connection

See [ACCESS.md](./ACCESS.md) for connection details.

```bash
# Quick connect
psql "postgresql://postgres.[project-ref]:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
```

---

## Verify Installation

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'companion%'
   OR table_name IN ('users', 'user_context', 'conversations', 'scheduled_messages',
                     'onboarding', 'daily_usage', 'user_devices', 'extraction_logs')
ORDER BY table_name;
```

Expected companion tables:
- companion_messages
- conversations
- daily_usage
- extraction_logs
- onboarding
- scheduled_messages
- user_context
- user_devices
- users
