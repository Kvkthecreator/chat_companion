# Chat Companion

**Push-based AI Companion - Daily check-ins via Telegram/WhatsApp/Web**

An AI companion that reaches out to you daily via Telegram (primary), WhatsApp (secondary), or web chat. Instead of you coming to the app when lonely, the companion initiates contact - a personalized morning message that makes you feel like someone is thinking about you.

## Core Concept

> The value is in being reached out to - feeling like someone genuinely cares about your day.

## Features

- **Daily Check-ins**: Personalized morning messages at your preferred time
- **Multi-channel**: Telegram (primary), WhatsApp (secondary), Web chat
- **Persistent Memory**: Remembers your life, preferences, and ongoing situations
- **Adaptive Companion**: Adjusts tone and style based on your preferences
- **Named Companion**: Give your companion a name during onboarding
- **Weather Context**: Messages can reference local weather (optional)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                     │
│                         /web                                 │
│                       Vercel                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │ Onboarding │ │  Settings  │ │  Web Chat  │               │
│  └────────────┘ └────────────┘ └────────────┘               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)                        │
│                       /api                                   │
│                       Render                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Telegram │ │ Companion│ │ Memory   │ │  Scheduler   │   │
│  │   Bot    │ │ Prompting│ │ Context  │ │  (Cron)      │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Database (PostgreSQL)                        │
│                      Supabase                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ users, user_context, conversations, messages,         │  │
│  │ scheduled_messages, onboarding, usage, subscriptions  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Model

| Entity | Description |
|--------|-------------|
| `users` | Profile, timezone, preferred time, Telegram link, subscription |
| `user_context` | Remembered facts, preferences, goals, situations |
| `conversations` | Daily conversation threads |
| `messages` | Individual messages in conversations |
| `scheduled_messages` | Queue for daily check-ins |
| `onboarding` | Onboarding progress tracking |
| `usage` | Message counting for free tier limits |

## Technology Stack

- **Frontend**: Next.js 15 + Tailwind CSS + shadcn/ui (Vercel)
- **Backend**: FastAPI + Python (Render)
- **Database**: PostgreSQL (Supabase)
- **Auth**: Supabase Auth with Google OAuth
- **AI**: Provider-agnostic (Google Gemini, OpenAI, Anthropic)
- **Messaging**: Telegram Bot API, WhatsApp Business API (future)
- **Payments**: LemonSqueezy
- **Weather**: OpenWeather API

## Repository Structure

```
chat-companion/
├── web/                      # Next.js frontend (Vercel)
│   └── src/
│       ├── app/              # App router pages
│       │   ├── (auth)/       # Login
│       │   ├── (onboarding)/ # Onboarding wizard
│       │   ├── (dashboard)/  # Dashboard, settings
│       │   └── chat/         # Web chat interface
│       ├── components/       # React components
│       └── lib/              # Supabase client, API client
├── api/
│   └── api/                  # FastAPI backend (Render)
│       └── src/
│           ├── app/
│           │   ├── routes/   # API endpoints
│           │   ├── services/ # Business logic
│           │   └── jobs/     # Scheduler jobs
│           └── middleware/   # Auth middleware
├── supabase/
│   └── migrations/           # Database migrations
└── MIGRATION_PLAN.md         # Detailed implementation plan
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account
- Telegram Bot Token (via BotFather)
- OpenAI/Google/Anthropic API key

### Environment Setup

1. Copy environment template:
```bash
cp .env.example .env
```

2. Configure credentials in `.env`

### Start Development

**Frontend:**
```bash
cd web
npm install
npm run dev
```

**Backend:**
```bash
cd api/api
pip install -r requirements.txt
cd src && uvicorn app.main:app --reload --port 10000
```

## API Endpoints

### Health
- `GET /health` - API health check
- `GET /health/db` - Database connectivity

### Users
- `GET /users/me` - Current user profile
- `PATCH /users/me` - Update profile

### Conversations
- `POST /conversations` - Start conversation
- `GET /conversations` - List conversations
- `POST /conversations/{id}/messages` - Send message

### Telegram
- `POST /telegram/webhook` - Telegram webhook handler

### Subscription
- `POST /subscription/checkout` - Create checkout session
- `GET /subscription/status` - Get subscription status

## Subscription Tiers

| Tier | Features |
|------|----------|
| Free | Daily messages, 5 replies/day, 7-day trial |
| Premium ($9.99/mo) | Unlimited replies, custom timing, deeper personalization |

## Deployments

| Service | Platform | URL |
|---------|----------|-----|
| Frontend | Vercel | TBD |
| Backend | Render | TBD |
| Database | Supabase | (managed) |

## License

MIT License
