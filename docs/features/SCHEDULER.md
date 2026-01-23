# Scheduler

> Daily push-based messaging

## Overview

The scheduler is the heart of the push-based companion experience. It sends daily check-in messages to users at their preferred time.

## How It Works

### Cron Jobs

Two cron jobs run on Render:

1. **message-scheduler** - Every minute
   ```bash
   cd src && python -m app.jobs.scheduler
   ```

2. **pattern-computation** - Daily at 2am UTC
   ```bash
   cd src && python -m app.jobs.patterns
   ```

### Selection Logic

Each minute, the scheduler:

1. Finds users where:
   - Current time matches `preferred_message_time` (±2 min window)
   - User has completed onboarding
   - User has a delivery channel (push token OR email enabled)
   - User hasn't been messaged today

2. For each eligible user:
   - Load user context (memory)
   - Get priority-based message context from ThreadService
   - Optionally fetch weather for location
   - Generate personalized message via LLM (Gemini Flash)
   - Send via appropriate channel (push or email)
   - Record in `scheduled_messages` table with priority level

### Priority Stack

Messages are generated using a 5-level priority stack (most personal first):

| Priority | Name | Description |
|----------|------|-------------|
| 1 | FOLLOW_UP | Ask about something specific from recent conversation |
| 2 | THREAD | Reference ongoing life situation (job search, relationship, etc.) |
| 3 | PATTERN | Acknowledge mood/engagement trend (requires pattern-computation job) |
| 4 | TEXTURE | Personal check-in with weather/time context |
| 5 | GENERIC | Warm fallback - **FAILURE STATE** (no personal content available) |

**Goal**: <40% Priority 5 (generic), >60% Priority 1-3 (personal)

### Database Tables

**scheduled_messages**
```sql
scheduled_messages (
    id UUID,
    user_id UUID,
    conversation_id UUID,
    scheduled_for TIMESTAMPTZ,
    content TEXT,
    status TEXT,  -- pending, sent, failed
    sent_at TIMESTAMPTZ,
    failure_reason TEXT,
    priority_level TEXT,  -- FOLLOW_UP, THREAD, PATTERN, TEXTURE, GENERIC
    channel TEXT,  -- push, email
    created_at
)
```

## Message Generation

### Prompt Building

```
System: You are {companion_name}, a {support_style} companion.
        You're reaching out for a daily check-in.

Context: {user_context_summary}
         - Recent: {recent_context}
         - Ongoing: {active_situations}

Weather: {weather_if_available}

Generate a warm, personalized morning message.
Keep it brief (1-2 sentences).
Reference something relevant to them.
```

### Example Output

> "Hey Alex! Hope your interview prep is going well.
> How are you feeling about tomorrow? ☀️"

## Delivery Channels

### Push Notifications (Mobile)

For users with active push tokens (Expo Push):

```python
await push_service.send_notification(
    user_id=user_id,
    title=f"{companion_name} is here",
    body=message[:100] + "...",
    data={"type": "daily-checkin", "conversation_id": str(conv_id)}
)
```

### Email (Web Users)

For web users without push tokens (via Resend):

```python
await email_service.send_daily_checkin(
    to_email=user_email,
    companion_name=companion_name,
    message=message,
    conversation_url=f"{WEB_APP_URL}/chat/{conversation_id}"
)
```

### Channel Selection Logic

1. If user has active push token → **push**
2. Else if email_notifications_enabled (default: true) and has email → **email**
3. Else → skip user (no delivery method)

## Failure Handling

| Failure | Handling |
|---------|----------|
| User blocked bot | Mark user, stop scheduling |
| Rate limit | Retry with backoff |
| Network error | Retry up to 3 times |
| LLM error | Use fallback generic message |

## Monitoring

### Check for failures

```sql
SELECT * FROM scheduled_messages
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 20;
```

### Priority Distribution (Memory System Health)

Use the admin endpoint to track message personalization:

```bash
GET /admin/message-priority
```

Returns:
- `generic_rate` - % of Priority 5 messages (failure state)
- `personal_rate` - % of Priority 1-3 messages (goal: >60%)
- `insights` - Automated health check messages

### Check by channel

```sql
SELECT channel, COUNT(*),
       COUNT(*) FILTER (WHERE status = 'sent') as sent,
       COUNT(*) FILTER (WHERE status = 'failed') as failed
FROM scheduled_messages
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY channel;
```

## Configuration

| Env Var | Description |
|---------|-------------|
| `GOOGLE_API_KEY` | Gemini API key (LLM for message generation) |
| `OPENWEATHER_API_KEY` | Weather API (optional) |
| `RESEND_API_KEY` | Email delivery via Resend |
| `RESEND_FROM_EMAIL` | From address for emails |
| `WEB_APP_URL` | Base URL for email links |

## See Also

- [Memory System](MEMORY_SYSTEM.md) - Context for messages
- [Pattern Detection](../design/PATTERN_DETECTION_AND_MEMORY_TRANSPARENCY.md)
