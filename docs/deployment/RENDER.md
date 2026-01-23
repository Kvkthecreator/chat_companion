# Render Deployment (API)

> Backend API and Scheduler deployment

## Overview

Render hosts:
- **chat-companion-api** (FastAPI Web Service)
- **message-scheduler** (Cron Job - every minute, sends daily messages)
- **pattern-computation** (Cron Job - daily at 2am UTC, analyzes behavior patterns)

## API Deployment

### 1. Create Web Service

1. Go to [render.com](https://render.com) and connect your GitHub repo
2. Create a new **Web Service**
3. Configure:
   - **Name**: `companion-api`
   - **Root Directory**: `api/api`
   - **Runtime**: Python 3
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `cd src && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 2. Environment Variables

Set these in Render Dashboard > Environment:

```bash
# Database
DATABASE_URL=postgresql://postgres.[ref]:[pass]@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true

# Supabase
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret

# LLM (at least one required)
GOOGLE_API_KEY=your-google-api-key
# or
OPENAI_API_KEY=your-openai-api-key
# or
ANTHROPIC_API_KEY=your-anthropic-api-key

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_SECRET=your-webhook-secret

# Email (Resend - for web user daily check-ins)
RESEND_API_KEY=your-resend-api-key
RESEND_FROM_EMAIL=companion@yourdomain.com
WEB_APP_URL=https://your-app.vercel.app

# CORS
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app

# Payments (optional)
LEMONSQUEEZY_API_KEY=your-api-key
LEMONSQUEEZY_STORE_ID=your-store-id
LEMONSQUEEZY_VARIANT_ID=your-variant-id
LEMONSQUEEZY_WEBHOOK_SECRET=your-webhook-secret
```

### 3. Create Cron Jobs

#### message-scheduler (Daily Messages)

1. Create a new **Cron Job** in Render
2. Configure:
   - **Name**: `message-scheduler`
   - **Root Directory**: `api/api`
   - **Schedule**: `* * * * *` (every minute)
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `cd src && python -m app.jobs.scheduler`
3. Add environment variables: `DATABASE_URL`, `SUPABASE_URL`, `GOOGLE_API_KEY`, `OPENWEATHER_API_KEY`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `WEB_APP_URL`

#### pattern-computation (Behavior Analysis)

1. Create a new **Cron Job** in Render
2. Configure:
   - **Name**: `pattern-computation`
   - **Root Directory**: `api/api`
   - **Schedule**: `0 2 * * *` (daily at 2am UTC)
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `cd src && python -m app.jobs.patterns`
3. Add environment variables: `DATABASE_URL`, `SUPABASE_URL`, `GOOGLE_API_KEY`

#### silence-detection (Check on Quiet Users)

1. Create a new **Cron Job** in Render
2. Configure:
   - **Name**: `silence-detection`
   - **Root Directory**: `api/api`
   - **Schedule**: `0 */6 * * *` (every 6 hours)
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `cd src && python -m app.jobs.silence_detection`
3. Add environment variables: `DATABASE_URL`, `SUPABASE_URL`, `GOOGLE_API_KEY`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `WEB_APP_URL`

## Post-Deployment Checklist

### 1. Run Database Migrations

Copy the SQL from `/docs/setup/SCHEMA.md` and run in Supabase SQL Editor.

### 2. Verify API Health

```bash
curl https://companion-api.onrender.com/health
```

Expected response:
```json
{"status": "healthy", "database": "connected"}
```

### 3. Test Authentication

The API uses Supabase JWT tokens. Test with:

```bash
curl https://companion-api.onrender.com/users/me \
  -H "Authorization: Bearer YOUR_SUPABASE_TOKEN"
```

### 4. Set Up Telegram Webhook (if using)

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://companion-api.onrender.com/telegram/webhook" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

### 5. Verify CORS

Test from browser console on your web app domain:

```javascript
fetch('https://companion-api.onrender.com/health')
  .then(r => r.json())
  .then(console.log)
```

## Monitoring

See [operations/MONITORING.md](../operations/MONITORING.md) for full monitoring guide.

### Quick Checks

- View logs: Render Dashboard → Service → Logs
- Health check: `curl https://chat-companion-api.onrender.com/health`

## See Also

- [Vercel Deployment](VERCEL.md) - Frontend deployment
- [Troubleshooting](../operations/TROUBLESHOOTING.md) - Common issues
