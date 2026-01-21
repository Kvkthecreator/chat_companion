# Data Model

> Design decisions and relationships

## Entity Relationship

```
┌─────────────┐
│   users     │
│─────────────│
│ id (PK)     │◄─────────────────────────────────────────┐
│ email       │                                          │
│ display_name│                                          │
│ companion_* │                                          │
│ telegram_*  │                                          │
│ subscription│                                          │
└─────────────┘                                          │
       │                                                 │
       │ 1:N                                             │
       ▼                                                 │
┌─────────────┐         ┌─────────────┐                  │
│conversations│         │ user_context│                  │
│─────────────│         │─────────────│                  │
│ id (PK)     │         │ id (PK)     │                  │
│ user_id (FK)│         │ user_id (FK)│◄─────────────────┤
│ channel     │         │ category    │                  │
│ initiated_by│         │ key         │                  │
│ started_at  │         │ value       │                  │
└─────────────┘         └─────────────┘                  │
       │                                                 │
       │ 1:N                                             │
       ▼                                                 │
┌─────────────┐         ┌─────────────────┐              │
│  messages   │         │scheduled_messages│             │
│─────────────│         │─────────────────│              │
│ id (PK)     │         │ id (PK)         │              │
│ conv_id (FK)│         │ user_id (FK)    │◄─────────────┤
│ role        │         │ scheduled_for   │              │
│ content     │         │ status          │              │
└─────────────┘         └─────────────────┘              │
                                                         │
┌─────────────┐         ┌─────────────────────┐          │
│ onboarding  │         │telegram_link_tokens │          │
│─────────────│         │─────────────────────│          │
│ id (PK)     │         │ id (PK)             │          │
│ user_id (FK)│◄────────│ user_id (FK)        │◄─────────┘
│ current_step│         │ token               │
│ data (JSONB)│         │ expires_at          │
└─────────────┘         └─────────────────────┘
```

## Table Design Decisions

### users

**Why extend auth.users?**
- Supabase auth.users is managed by Supabase Auth
- We need additional fields (companion settings, Telegram, subscription)
- FK to auth.users ensures consistency

**Why JSONB preferences?**
- Flexible for future settings without schema changes
- Easy to add new preferences without migrations

### conversations

**Why separate conversations from messages?**
- Track metadata per "day" or "session"
- Enable mood/topic summaries per conversation
- Support multiple channels (web, telegram, whatsapp)

**Why `initiated_by`?**
- Distinguish push (companion-initiated) vs pull (user-initiated)
- Analytics: how often do users initiate vs respond?

### messages

**Why not store in conversations JSONB?**
- Messages can be large (many per conversation)
- Need indexing for search/retrieval
- Separate table scales better

**Why `telegram_message_id`?**
- Link to original Telegram message for edits/replies
- Enable message threading in Telegram

### user_context

**Why separate from users?**
- Many context items per user
- Different lifecycles (some expire, some permanent)
- Need category-based queries

**Why composite unique constraint (user_id, category, key)?**
- Prevent duplicate facts
- Enable upsert pattern for updates
- Key acts as "what" (e.g., "job"), value is "detail" (e.g., "software engineer")

### scheduled_messages

**Why track each scheduled message?**
- Audit trail for debugging
- Track delivery status
- Prevent duplicate sends (check if sent today)

### onboarding

**Why separate from users?**
- Temporary state during onboarding
- Complex data (step progress, partial inputs)
- Clean separation of concerns

### telegram_link_tokens

**Why expiring tokens?**
- Security: tokens should be short-lived
- One-time use (marked `used_at` after linking)
- Clean up old unused tokens

## Indexing Strategy

| Table | Index | Purpose |
|-------|-------|---------|
| conversations | user_id | Find user's conversations |
| conversations | started_at DESC | Recent conversations first |
| messages | conversation_id | Messages in conversation |
| messages | created_at DESC | Recent messages first |
| user_context | user_id | User's memories |
| user_context | category | Filter by type |
| scheduled_messages | user_id | User's scheduled messages |
| scheduled_messages | status | Find pending messages |

## RLS Policies

All tables use Row-Level Security. Users can only access their own data:

```sql
-- Direct ownership
users: auth.uid() = id
onboarding: auth.uid() = user_id
user_context: auth.uid() = user_id

-- Indirect ownership
messages: conversation_id IN (SELECT id FROM conversations WHERE user_id = auth.uid())
```

## See Also

- [SCHEMA.md](SCHEMA.md) - Full SQL definitions
- [ACCESS.md](ACCESS.md) - Database connection
