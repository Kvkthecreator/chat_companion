# Monitoring

> Logs, health checks, and observability

## Health Endpoints

### Basic Health

```bash
curl https://chat-companion-api.onrender.com/health
# {"status":"healthy","service":"chat-companion-api"}
```

### Database Health

```bash
curl https://chat-companion-api.onrender.com/health/db
# {"status":"healthy","database":"connected"}
```

### Table Health

```bash
curl https://chat-companion-api.onrender.com/health/tables
# {"status":"healthy","tables":["conversations","messages",...]}
```

## Render Logs

### View Logs

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select `chat-companion-api` service
3. Click "Logs" tab

### Log Levels

| Level | When Used |
|-------|-----------|
| INFO | Normal operations |
| WARNING | Recoverable issues |
| ERROR | Failures requiring attention |

### Key Log Patterns

```
# Successful request
INFO: POST /conversation/send 200

# Database connection
INFO: Database connection established

# LLM call
INFO: LLM configured: gemini / gemini-1.5-flash

# Error
ERROR: Unhandled exception on /users/me: ...
```

## Cron Job Monitoring

### Scheduler Logs

View cron job runs in Render dashboard:
1. Select `message-scheduler` cron job
2. Click "Logs"

### Key Metrics

| Metric | How to Check |
|--------|--------------|
| Users messaged | Query scheduled_messages |
| Failures | scheduled_messages WHERE status='failed' |
| Execution time | Render cron job logs |

### Query Recent Scheduled Messages

```sql
SELECT
    u.display_name,
    sm.scheduled_for,
    sm.status,
    sm.sent_at,
    sm.failure_reason
FROM scheduled_messages sm
JOIN users u ON sm.user_id = u.id
ORDER BY sm.created_at DESC
LIMIT 20;
```

## Database Monitoring

### Connection Pool

Monitor in Supabase dashboard:
- Dashboard → Database → Connection Pooling

### Slow Queries

```sql
SELECT
    query,
    calls,
    mean_time,
    total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Table Sizes

```sql
SELECT
    relname as table,
    pg_size_pretty(pg_total_relation_size(relid)) as size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

## Alerting (TODO)

### Recommended Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| API Down | /health returns non-200 | Check Render |
| DB Disconnected | /health/db unhealthy | Check Supabase |
| High Error Rate | >5% 500 errors | Check logs |
| Scheduler Failing | 3+ consecutive failures | Check cron logs |

### Setting Up Alerts

**Render**:
- Settings → Notifications → Add webhook

**UptimeRobot** (free):
- Monitor /health endpoint
- Alert on downtime

## Performance Baselines

| Metric | Expected | Investigate If |
|--------|----------|----------------|
| /health response | <100ms | >500ms |
| /conversation/send | <3s | >5s |
| Scheduler run | <60s | >120s |
| DB query | <100ms | >500ms |

## Debugging Checklist

1. **API not responding**
   - Check Render service status
   - View Render logs
   - Try /health endpoint

2. **Database errors**
   - Check /health/db
   - Verify DATABASE_URL in Render
   - Check Supabase dashboard

3. **Messages not sending**
   - Check scheduled_messages table
   - View scheduler cron logs
   - Verify TELEGRAM_BOT_TOKEN

4. **Slow responses**
   - Check LLM provider status
   - Review Render resource usage
   - Check database connection pool
