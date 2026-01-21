# Telegram Integration

> Primary messaging channel

## Overview

Telegram is the primary channel for push-based messaging. Users link their Telegram account to receive daily check-ins and have conversations.

## Setup

### 1. Create Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Follow prompts to name your bot
4. Copy the bot token

### 2. Configure Webhook

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://chat-companion-api.onrender.com/telegram/webhook" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

### 3. Environment Variables

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_WEBHOOK_SECRET=random-secret-string
```

## Account Linking

### Flow

```
1. User clicks "Connect Telegram" in web app
   ↓
2. API generates link token
   POST /telegram/link/{user_id}
   Returns: { deep_link_url: "https://t.me/YourBot?start=abc123" }
   ↓
3. User clicks deep link → opens Telegram
   ↓
4. User presses "Start" in bot
   ↓
5. Bot receives /start command with token
   ↓
6. API validates token, links accounts
   ↓
7. User's telegram_user_id saved to users table
```

### Database

```sql
-- Link tokens (temporary)
telegram_link_tokens (
    id UUID,
    user_id UUID,
    token TEXT UNIQUE,
    expires_at TIMESTAMPTZ,
    used_at TIMESTAMPTZ,
    created_at
)

-- User's Telegram info (permanent)
users (
    telegram_user_id BIGINT UNIQUE,
    telegram_username TEXT,
    telegram_linked_at TIMESTAMPTZ
)
```

## Webhook Handler

### Endpoint

`POST /telegram/webhook`

### Verification

```python
# Verify webhook authenticity
secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
if secret_token != os.getenv("TELEGRAM_WEBHOOK_SECRET"):
    raise HTTPException(401)
```

### Message Handling

```python
@router.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        # Find user by telegram_user_id
        user = await find_user_by_telegram(chat_id)

        if text.startswith("/start"):
            # Handle account linking
            await handle_start_command(chat_id, text)
        else:
            # Regular message - generate response
            response = await conversation_service.send_message(
                user_id=user.id,
                content=text,
                channel="telegram"
            )

            # Send response back
            await send_telegram_message(chat_id, response.content)
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Link account (with token) |
| `/start` | New user greeting (without token) |
| `/help` | Show available commands |
| `/settings` | Link to web settings |

## Sending Messages

```python
async def send_telegram_message(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"  # Optional: enable formatting
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)
```

## Troubleshooting

### Bot not responding

1. Check webhook is set:
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

2. Verify webhook URL is correct and accessible

3. Check Render logs for errors

### "User not found" on message

User hasn't linked their account. They need to:
1. Get link from web app
2. Click to open Telegram
3. Press "Start"

### Messages not delivering

- Check `telegram_user_id` is set in users table
- Verify bot wasn't blocked by user
- Check Telegram API rate limits

## Rate Limits

Telegram limits:
- 30 messages/second to different users
- 1 message/second to same user

The scheduler respects these limits with built-in delays.

## See Also

- [Scheduler](SCHEDULER.md) - Daily message sending
- [API Endpoints](../api/ENDPOINTS.md#telegram) - Telegram API routes
