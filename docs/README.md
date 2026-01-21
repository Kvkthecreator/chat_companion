# Chat Companion Documentation

Push-based AI companion that reaches out daily via Telegram, WhatsApp, or Web.

## Quick Links

### Setup
- [Database Setup](setup/DATABASE_SETUP.md) - Supabase configuration and direct access
- [Schema](setup/SCHEMA.md) - Database tables and migrations
- [Deployment](setup/DEPLOYMENT.md) - Render and Vercel deployment

### Architecture
- [Overview](architecture/OVERVIEW.md) - System design and data flow

### Operations
- [Troubleshooting](operations/TROUBLESHOOTING.md) - Common issues and solutions

### API
- [Endpoints](api/ENDPOINTS.md) - API reference

## Getting Started

1. **Set up Supabase**
   - Create project at [supabase.com](https://supabase.com)
   - Run schema from [SCHEMA.md](setup/SCHEMA.md)
   - Get connection strings from [DATABASE_SETUP.md](setup/DATABASE_SETUP.md)

2. **Deploy API**
   - Follow [DEPLOYMENT.md](setup/DEPLOYMENT.md)
   - Set environment variables in Render

3. **Deploy Web**
   - Deploy `/web` to Vercel
   - Configure Supabase keys

4. **Test**
   - Check `/health` endpoint
   - Create account and complete onboarding
   - Send first message

## Project Structure

```
chat_companion/
├── api/api/           # FastAPI backend
│   └── src/app/
│       ├── routes/    # API endpoints
│       ├── services/  # Business logic
│       ├── models/    # Data models
│       └── jobs/      # Scheduler
├── web/               # Next.js frontend
│   └── src/
│       ├── app/       # Pages
│       ├── components/
│       └── lib/       # Utilities
├── docs/              # Documentation (you are here)
└── render.yaml        # Render deployment config
```
