# Deployment Guide

## Overview

The Chat Companion app consists of:
- **API** (FastAPI) - Deployed on Render
- **Web** (Next.js) - Deployed on Vercel
- **Database** (PostgreSQL) - Supabase
- **Scheduler** (Cron job) - Render Cron

## API Deployment (Render)

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

# CORS
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app

# Payments (optional)
LEMONSQUEEZY_API_KEY=your-api-key
LEMONSQUEEZY_STORE_ID=your-store-id
LEMONSQUEEZY_VARIANT_ID=your-variant-id
LEMONSQUEEZY_WEBHOOK_SECRET=your-webhook-secret
```

### 3. Create Cron Job (Scheduler)

1. Create a new **Cron Job** in Render
2. Configure:
   - **Name**: `message-scheduler`
   - **Root Directory**: `api/api`
   - **Schedule**: `* * * * *` (every minute)
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `cd src && python -m app.jobs.scheduler`
3. Add the same environment variables as the web service

## Web Deployment (Vercel)

### 1. Connect Repository

1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `web`

### 2. Environment Variables

Set in Vercel Dashboard > Settings > Environment Variables:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://[project-ref].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=https://companion-api.onrender.com
```

### 3. Deploy

Vercel auto-deploys on push to main branch.

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

### Render Logs

View logs in Render Dashboard > Your Service > Logs

### Supabase Logs

View in Supabase Dashboard > Logs > API or Postgres

### Common Issues

1. **502 Bad Gateway** - Check Render logs for Python errors
2. **CORS errors** - Verify `CORS_ORIGINS` includes your frontend URL
3. **Auth errors** - Check `SUPABASE_JWT_SECRET` matches your project
4. **Database connection** - Verify `DATABASE_URL` format and credentials
