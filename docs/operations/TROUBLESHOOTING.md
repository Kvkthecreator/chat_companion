# Troubleshooting Guide

## Database Connection Issues

### "Tenant or user not found"

**Cause**: Wrong credentials or project reference in DATABASE_URL

**Solutions**:
1. Verify project reference matches your Supabase dashboard URL
2. Check the pooler region (`aws-0` vs `aws-1`) - copy exact URL from Supabase
3. Reset database password in Supabase and update DATABASE_URL
4. Ensure password is URL-encoded if it contains special characters

### "Network is unreachable"

**Cause**: Direct connection blocked by firewall

**Solution**: Use the pooler connection (port 6543) instead of direct connection

### Connection Timeout

**Cause**: SSL issues or wrong port

**Solutions**:
1. Try session pooler (port 5432) instead of transaction pooler (6543)
2. Add `?pgbouncer=true` to connection string for transaction pooler
3. Verify SSL is enabled in your database client

## API Errors

### 401 Unauthorized

**Cause**: Invalid or missing JWT token

**Solutions**:
1. Check `SUPABASE_JWT_SECRET` matches your Supabase project
2. Verify token hasn't expired
3. Ensure `Authorization: Bearer <token>` header is set correctly

### 500 Internal Server Error

**Cause**: Unhandled exception in API

**Solutions**:
1. Check Render logs for stack trace
2. Common issues:
   - Missing environment variable
   - Database query error
   - LLM API failure

### CORS Errors

**Cause**: Frontend origin not in allowed list

**Solution**: Add your frontend URL to `CORS_ORIGINS` environment variable

```bash
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app
```

## LLM Issues

### "No API key found"

**Cause**: Missing LLM provider API key

**Solution**: Set at least one of:
- `GOOGLE_API_KEY` (for Gemini)
- `OPENAI_API_KEY` (for GPT)
- `ANTHROPIC_API_KEY` (for Claude)

### Rate Limit Exceeded

**Cause**: Too many requests to LLM provider

**Solutions**:
1. Implement request queuing
2. Add delay between requests
3. Upgrade to higher tier API plan

### Slow Responses

**Cause**: LLM latency or network issues

**Solutions**:
1. Use streaming responses (`/conversation/send/stream`)
2. Consider faster model (Gemini Flash, GPT-4o-mini)
3. Reduce context window size

## Telegram Issues

### Bot Not Responding

**Causes**:
1. Webhook not set
2. Wrong webhook URL
3. Invalid bot token

**Solutions**:

Check webhook status:
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

Set webhook:
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-api.onrender.com/telegram/webhook" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

### "User not found" on Message

**Cause**: Telegram user hasn't linked their account

**Solution**: User needs to:
1. Get deep link from web app
2. Click link to open Telegram
3. Press "Start" in bot chat

## Scheduler Issues

### Messages Not Sending

**Causes**:
1. Cron job not running
2. No users match criteria
3. Telegram/WhatsApp not configured

**Debug steps**:

1. Check cron job logs in Render

2. Manually query eligible users:
```sql
SELECT id, display_name, preferred_message_time, timezone, telegram_user_id
FROM users
WHERE onboarding_completed_at IS NOT NULL
  AND telegram_user_id IS NOT NULL;
```

3. Check scheduled_messages table:
```sql
SELECT * FROM scheduled_messages
ORDER BY created_at DESC
LIMIT 10;
```

### Duplicate Messages

**Cause**: Scheduler running multiple times in same window

**Solution**: The scheduler checks for existing sent messages today. If still happening, check cron schedule isn't too frequent.

## Performance Issues

### Slow API Responses

**Causes**:
1. Cold start (Render free tier)
2. Database query performance
3. LLM latency

**Solutions**:
1. Upgrade to paid Render plan (no sleep)
2. Add database indexes
3. Use connection pooling
4. Implement caching for user context

### High Memory Usage

**Cause**: Memory leaks or large payloads

**Solutions**:
1. Check for unclosed connections
2. Limit message history length
3. Stream large responses

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing import | Check requirements.txt |
| `asyncpg.exceptions.InternalServerError` | DB auth failed | Check DATABASE_URL |
| `httpx.ConnectError` | Network issue | Check service URLs |
| `ValidationError` | Invalid request data | Check request body format |
| `JWTDecodeError` | Invalid token | Check JWT secret |

## Getting Help

1. Check Render logs: Dashboard > Service > Logs
2. Check Supabase logs: Dashboard > Logs
3. Test endpoints with curl to isolate issues
4. Check environment variables are set correctly
