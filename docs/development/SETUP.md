# Local Development Setup

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL client (`psql`) for database access
- Supabase account
- Telegram Bot Token (via BotFather)
- LLM API key (OpenAI, Google Gemini, or Anthropic)

## Environment Setup

### 1. Clone and Configure

```bash
git clone https://github.com/Kvkthecreator/chat_companion.git
cd chat_companion
cp .env.example .env
```

### 2. Configure `.env`

Required variables:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Database
DATABASE_URL=postgresql://postgres.xxx:password@aws-1-region.pooler.supabase.com:6543/postgres

# LLM (at least one required)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...

# Telegram (optional for local dev)
TELEGRAM_BOT_TOKEN=...
```

## Running the Backend

```bash
cd api/api
pip install -r requirements.txt
cd src
uvicorn app.main:app --reload --port 10000
```

API available at: http://localhost:10000

### Health Check

```bash
curl http://localhost:10000/health
# {"status":"healthy","service":"chat-companion-api"}
```

## Running the Frontend

```bash
cd web
npm install
npm run dev
```

Web app available at: http://localhost:3000

## Database Access

See [database/ACCESS.md](../database/ACCESS.md) for connection strings and psql commands.

## Testing

```bash
# Backend tests
cd api/api
pytest

# Frontend tests
cd web
npm test
```

## Common Issues

### Port already in use
```bash
lsof -i :10000  # Find process
kill -9 <PID>   # Kill it
```

### Database connection failed
- Check DATABASE_URL is correctly set
- Verify password is URL-encoded if it contains special characters
- See [database/ACCESS.md](../database/ACCESS.md) troubleshooting

### LLM API errors
- Verify at least one API key is set (OPENAI_API_KEY, GOOGLE_API_KEY, or ANTHROPIC_API_KEY)
- Check API key has valid billing/credits
