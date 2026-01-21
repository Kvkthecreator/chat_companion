# Scheduler

> Daily push-based messaging

## Overview

The scheduler is the heart of the push-based companion experience. It sends daily check-in messages to users at their preferred time.

## How It Works

### Cron Job

Runs every minute on Render:

```bash
cd src && python -m app.jobs.scheduler
```

### Selection Logic

Each minute, the scheduler:

1. Finds users where:
   - Current time matches `preferred_message_time` (±30 min window)
   - User has completed onboarding
   - User has a messaging channel (Telegram, WhatsApp)
   - User hasn't been messaged today

2. For each eligible user:
   - Load user context (memory)
   - Optionally fetch weather for location
   - Generate personalized message via LLM
   - Send via appropriate channel
   - Record in `scheduled_messages` table

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

## Channels

### Telegram (Primary)

Uses Telegram Bot API to send messages:

```python
await bot.send_message(
    chat_id=user.telegram_user_id,
    text=message_content
)
```

### WhatsApp (Future)

Planned integration with WhatsApp Business API.

### Web (Fallback)

If no messaging channel, message appears in web chat when user logs in.

## Failure Handling

| Failure | Handling |
|---------|----------|
| User blocked bot | Mark user, stop scheduling |
| Rate limit | Retry with backoff |
| Network error | Retry up to 3 times |
| LLM error | Use fallback generic message |

## Monitoring

Check scheduled_messages for failures:

```sql
SELECT * FROM scheduled_messages
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 20;
```

## Configuration

| Env Var | Description |
|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `OPENWEATHER_API_KEY` | Weather API (optional) |

## See Also

- [Telegram Integration](TELEGRAM.md)
- [Memory System](MEMORY_SYSTEM.md) - Context for messages
