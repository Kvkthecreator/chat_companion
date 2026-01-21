# Chat Companion

**Push-based AI Companion - Daily check-ins via Telegram/WhatsApp/Web**

An AI companion that reaches out to you daily. Instead of you coming to the app when lonely, the companion initiates contact - a personalized morning message that makes you feel like someone is thinking about you.

## Core Concept

> The value is in being reached out to - feeling like someone genuinely cares about your day.

## Features

- **Daily Check-ins**: Personalized morning messages at your preferred time
- **Multi-channel**: Telegram (primary), WhatsApp (future), Web chat
- **Persistent Memory**: Remembers your life, preferences, and ongoing situations
- **Adaptive Companion**: Adjusts tone and style based on your preferences
- **Named Companion**: Give your companion a name during onboarding

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account
- Telegram Bot Token (via BotFather)
- LLM API key (OpenAI/Google/Anthropic)

### Development

**Backend:**
```bash
cd api/api
pip install -r requirements.txt
cd src && uvicorn app.main:app --reload --port 10000
```

**Frontend:**
```bash
cd web
npm install
npm run dev
```

### Deployment

See [docs/deployment/](docs/deployment/) for Render and Vercel setup.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│                         /web → Vercel                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)                        │
│                    /api → Render                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Telegram │ │ Companion│ │ Memory   │ │  Scheduler   │   │
│  │   Bot    │ │ Service  │ │ Context  │ │  (Cron)      │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database (Supabase)                        │
│  users, conversations, messages, user_context,              │
│  scheduled_messages, onboarding                             │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
chat_companion/
├── api/api/              # FastAPI backend
│   └── src/app/
│       ├── routes/       # API endpoints
│       ├── services/     # Business logic
│       └── jobs/         # Scheduler
├── web/                  # Next.js frontend
│   └── src/
│       ├── app/          # Pages
│       ├── components/
│       └── lib/          # Utilities
├── docs/                 # Documentation
└── render.yaml           # Render deployment config
```

## Documentation

Full documentation: [docs/](docs/)

- [Development Setup](docs/development/SETUP.md)
- [API Reference](docs/api/ENDPOINTS.md)
- [Database Schema](docs/database/SCHEMA.md)
- [Architecture Decisions](docs/adr/)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL (Supabase) |
| Auth | Supabase Auth |
| AI | Provider-agnostic (Gemini, OpenAI, Anthropic) |
| Messaging | Telegram Bot API |
| Payments | LemonSqueezy |

## Live URLs

| Service | URL |
|---------|-----|
| API | https://chat-companion-api.onrender.com |
| Web | https://chat-companion.vercel.app |

## License

MIT License
