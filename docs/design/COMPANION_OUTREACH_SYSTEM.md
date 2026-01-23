# Companion Outreach System

> Designing for the illusion of independent thought

## Implementation Status

| Phase | Status | Date |
|-------|--------|------|
| Phase 1: Foundation (Daily Scheduler) | **Implemented** | Jan 2026 |
| Phase 2: Silence Detection | **Implemented** | Jan 23, 2026 |
| Phase 3: Event-Based Follow-ups | Planned | - |
| Phase 4: Earned Spontaneity | Planned | - |

### Changelog

**2026-01-23**: Phase 2 - Silence Detection
- Added `last_user_message_at`, `silence_threshold_days`, `allow_silence_checkins` to users table
- Added `messages_received_count`, `first_message_at` for user maturity tracking
- Added `trigger_type` column to `scheduled_messages`
- Created database trigger `trigger_update_user_last_message` on messages table
- Implemented `SilenceDetectionService` in `scheduler.py`
- Created `app/jobs/silence_detection.py` job entry point
- Added user settings to API (`allow_silence_checkins`, `silence_threshold_days`)
- Cron schedule: Recommended every 6 hours (`0 */6 * * *`)

**2026-01-22**: Phase 1 - Foundation
- Daily scheduler with priority-based message generation
- Push and email delivery channels
- Priority tracking (FOLLOW_UP, THREAD, PATTERN, TEXTURE, GENERIC)

---

## Philosophy

The goal is not to build a notification system that happens to be personal. The goal is to build a **companion that reaches out because it cares** - and the technology should be invisible.

A real friend doesn't message you at exactly 9:00 AM every day. They reach out:
- When something reminds them of you
- When they notice you've been quiet
- When they know something important is happening in your life
- Sometimes just randomly because they were thinking of you

This document defines how we evolve from "scheduled notifications" to "companion-initiated contact."

---

## Core Principles

### 1. Predictability Before Spontaneity

**The Trust Curve**: Users evaluate reliability before they appreciate spontaneity.

| Stage | User Mindset | System Behavior |
|-------|--------------|-----------------|
| Week 1-2 | "Is this reliable?" | Consistent daily messages at exact time |
| Week 3-4 | "This knows me" | Messages become more personalized (Priority 1-3) |
| Month 2+ | "This feels like a friend" | Earned spontaneity: silence detection, event triggers |

**Key Insight**: Randomness without context feels like chaos. A message at an unexpected time only feels meaningful when paired with content that explains *why now* ("I was thinking about your interview tomorrow").

### 2. One Daily Minimum (The Floor)

Users should always know they'll hear from their companion at least once per day at roughly their chosen time. This is the **reliability contract**.

Additional touches (silence check-ins, event follow-ups) are **additive**, not replacements. The daily message is never skipped - additional outreach is bonus presence.

### 3. The Illusion Requires Substance

| Feels Robotic | Feels Alive |
|---------------|-------------|
| Same time every day | Occasional variation in timing |
| Always asks a question | Sometimes just shares a thought |
| Only references last conversation | References something from weeks ago |
| Never acknowledges gaps | "I know I check in a lot, just want you to know I'm here" |
| Ignores external context | Mentions weather, day of week, known events |

---

## Trigger Architecture

### Current: Time-Based Only

```
┌─────────────────────────────────────────────────────┐
│  Cron (every minute)                                │
│  └─> Find users where NOW = preferred_message_time  │
│      └─> Generate message                           │
│          └─> Send via push/email                    │
└─────────────────────────────────────────────────────┘
```

### Future: Multi-Trigger System

```
┌─────────────────────────────────────────────────────────────────────┐
│  TRIGGER EVALUATOR (runs every minute)                              │
│                                                                     │
│  For each user, evaluate triggers in priority order:                │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. DAILY_CHECKIN (required)                                  │   │
│  │    - Time matches preferred_message_time (±2 min)            │   │
│  │    - Not already sent today                                  │   │
│  │    → Always fires once per day                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 2. SILENCE_DETECTION (caring)                                │   │
│  │    - User hasn't messaged in N days (default: 3)             │   │
│  │    - Silence check-in not sent in last 24h                   │   │
│  │    → "Hey, haven't heard from you - just checking in"        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 3. EVENT_FOLLOWUP (contextual) [FUTURE]                      │   │
│  │    - Thread has follow_up_date = TODAY                       │   │
│  │    - Event hasn't been followed up on                        │   │
│  │    → "How did your interview go?"                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 4. ENGAGEMENT_ADAPTIVE [FUTURE]                              │   │
│  │    - User responding quickly → maybe more contact welcome    │   │
│  │    - User not responding → reduce to minimum                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (Current)

**Status**: Implemented

- Daily scheduler runs every minute
- Finds users whose `preferred_message_time` matches current time (±2 min)
- Generates personalized message using Priority Stack
- Sends via push (mobile) or email (web)
- Records in `scheduled_messages` with priority level

**Behavior**: Predictable, reliable daily contact.

### Phase 2: Silence Detection

**Status**: Implemented (Jan 23, 2026)

**Cron Setup** (Render):
```bash
# Name: silence-detection
# Schedule: 0 */6 * * * (every 6 hours)
# Start Command: cd src && python -m app.jobs.silence_detection
```

**Trigger Condition**:
```sql
-- Users who:
-- 1. Have completed onboarding
-- 2. Haven't sent a message in N days
-- 3. Haven't received a silence check-in in last 24h
-- 4. Have a delivery channel

SELECT u.id, u.email, u.companion_name
FROM users u
WHERE u.onboarding_completed_at IS NOT NULL
  AND u.last_user_message_at < NOW() - INTERVAL '3 days'
  AND NOT EXISTS (
    SELECT 1 FROM scheduled_messages sm
    WHERE sm.user_id = u.id
      AND sm.trigger_type = 'silence_detection'
      AND sm.sent_at > NOW() - INTERVAL '24 hours'
  )
  AND (
    EXISTS (SELECT 1 FROM user_devices WHERE user_id = u.id AND push_token IS NOT NULL)
    OR u.email IS NOT NULL
  )
```

**Message Generation**:
- Tone: Gentle, not guilt-inducing
- Examples:
  - "Hey, just thinking of you. No pressure to respond - I'm here when you're ready."
  - "Haven't heard from you in a bit. Hope everything's okay."
  - "Just a gentle hello. I'm around if you want to chat."

**Database Changes**:
```sql
-- Add to users table
ALTER TABLE users ADD COLUMN last_user_message_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN silence_threshold_days INTEGER DEFAULT 3;

-- Add trigger type to scheduled_messages
ALTER TABLE scheduled_messages ADD COLUMN trigger_type TEXT DEFAULT 'daily_checkin';
-- Values: 'daily_checkin', 'silence_detection', 'event_followup', 'spontaneous'
```

**User Control**:
- Setting: "Check in if I've been quiet" (on/off)
- Setting: "After how many days?" (2, 3, 5, 7)

### Phase 3: Event-Based Follow-ups

**Status**: Future

When a thread has a `follow_up_date` that matches today, and the daily check-in hasn't already addressed it, send a targeted follow-up.

**Trigger Condition**:
- Thread.follow_up_date = TODAY
- Thread.status != 'resolved'
- No message sent today that references this thread

**Message Generation**:
- Uses thread context directly
- "How did [specific thing] go?"
- Can be same-day as daily check-in (multi-touch)

### Phase 4: Earned Spontaneity

**Status**: Future (requires user maturity tracking)

After a user has been active for 30+ days with consistent engagement, unlock:
- Timing jitter (±15-30 min on daily messages)
- Occasional "thinking of you" messages that aren't questions
- Pattern-based outreach ("Noticed you've been down lately - want to talk?")

**Gate**: `user.messages_received_count >= 30 AND user.days_since_signup >= 30`

---

## Message Types

| Type | Trigger | Frequency | Tone | Example |
|------|---------|-----------|------|---------|
| Daily Check-in | Time match | 1x/day (guaranteed) | Warm, personal | "Good morning! How's the job search going?" |
| Silence Check-in | No user message in N days | Max 1x/24h | Gentle, no pressure | "Just thinking of you. Here when you're ready." |
| Event Follow-up | Thread follow_up_date | 1x per event | Curious, caring | "How did your interview go yesterday?" |
| Thinking of You | Spontaneous (mature users) | Rare | Light, no ask | "Just wanted to say hi." |

---

## Database Schema Additions

```sql
-- Track user activity for silence detection
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_user_message_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS silence_threshold_days INTEGER DEFAULT 3;
ALTER TABLE users ADD COLUMN IF NOT EXISTS allow_silence_checkins BOOLEAN DEFAULT TRUE;

-- Track user maturity for earned features
ALTER TABLE users ADD COLUMN IF NOT EXISTS messages_received_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_message_at TIMESTAMPTZ;

-- Track trigger types for analytics
ALTER TABLE scheduled_messages ADD COLUMN IF NOT EXISTS trigger_type TEXT DEFAULT 'daily_checkin';
-- Constraint: CHECK (trigger_type IN ('daily_checkin', 'silence_detection', 'event_followup', 'spontaneous'))

-- Index for silence detection query
CREATE INDEX IF NOT EXISTS idx_users_last_message ON users(last_user_message_at)
  WHERE onboarding_completed_at IS NOT NULL;
```

---

## Monitoring & Health Metrics

### Key Metrics

| Metric | Target | Alert If |
|--------|--------|----------|
| Daily message send rate | 100% of eligible users | < 95% |
| Silence check-in response rate | > 30% respond within 24h | < 20% |
| Priority 5 (generic) rate | < 40% | > 50% |
| Unsubscribe rate after silence check-in | < 5% | > 10% |

### Queries

```sql
-- Trigger type distribution (last 7 days)
SELECT trigger_type, COUNT(*),
       ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 1) as pct
FROM scheduled_messages
WHERE sent_at > NOW() - INTERVAL '7 days'
GROUP BY trigger_type;

-- Silence check-in effectiveness
SELECT
  COUNT(*) as silence_checkins_sent,
  COUNT(*) FILTER (WHERE EXISTS (
    SELECT 1 FROM messages m
    WHERE m.conversation_id = sm.conversation_id
      AND m.role = 'user'
      AND m.created_at > sm.sent_at
      AND m.created_at < sm.sent_at + INTERVAL '24 hours'
  )) as got_response_within_24h
FROM scheduled_messages sm
WHERE trigger_type = 'silence_detection'
  AND sent_at > NOW() - INTERVAL '30 days';
```

---

## User Settings

### Current Settings
- `preferred_message_time` - When to send daily check-in
- `timezone` - For time calculation
- `message_time_flexibility` - exact, around, window

### Phase 2 Settings
- `allow_silence_checkins` - Enable "checking in when quiet" (default: true)
- `silence_threshold_days` - Days before silence check-in (default: 3)

### Future Settings
- `message_frequency` - daily, few_times_week, adaptive
- `allow_spontaneous_messages` - Enable "thinking of you" messages
- `quiet_mode_until` - Temporarily pause all outreach

---

## Anti-Patterns to Avoid

### 1. Over-Messaging
Never send more than 2 messages per day (1 daily + 1 event/silence). Users should never feel spammed.

### 2. Guilt-Inducing Language
Bad: "I noticed you haven't responded..."
Good: "Just thinking of you. No pressure."

### 3. Fake Spontaneity
Don't add jitter just to seem random. Timing variation should be earned and paired with content that justifies unexpected timing.

### 4. Ignoring Signals
If a user consistently doesn't respond to silence check-ins, reduce or disable them. Adapt to behavior.

### 5. Breaking the Contract
The daily message at preferred time is a promise. Never skip it to "seem more spontaneous." Additional touches are additive.

---

## See Also

- [SCHEDULER.md](../features/SCHEDULER.md) - Current implementation details
- [MEMORY_SYSTEM.md](../features/MEMORY_SYSTEM.md) - Context for personalization
- [PATTERN_DETECTION_AND_MEMORY_TRANSPARENCY.md](PATTERN_DETECTION_AND_MEMORY_TRANSPARENCY.md) - Behavioral patterns
- [ADR-001-memory-architecture.md](../adr/ADR-001-memory-architecture.md) - Memory design decisions
