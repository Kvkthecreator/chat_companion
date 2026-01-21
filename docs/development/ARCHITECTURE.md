# Architecture Overview

## System Design

Chat Companion is a push-based AI companion that proactively reaches out to users daily.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web App   │     │  Telegram   │     │  WhatsApp   │
│  (Next.js)  │     │    Bot      │     │   (Future)  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │  FastAPI    │
                    │    API      │
                    └──────┬──────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
│  Supabase   │     │    LLM      │     │  Scheduler  │
│  (Postgres) │     │  (Gemini)   │     │  (Cron Job) │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Core Components

### 1. API Layer (FastAPI)

- **Location**: `/api/api/src/app/`
- **Purpose**: Handle all HTTP requests, authentication, business logic

Key services:
- `ConversationService` - Message handling and LLM interaction
- `ContextService` - User memory extraction and retrieval
- `CompanionService` - Personality and prompt building
- `SchedulerService` - Daily message scheduling
- `TelegramService` - Telegram bot integration

### 2. Web Frontend (Next.js)

- **Location**: `/web/`
- **Purpose**: User-facing web interface

Key features:
- Onboarding flow
- Chat interface
- Settings management
- Account linking (Telegram)

### 3. Database (Supabase/PostgreSQL)

- **Location**: Hosted on Supabase
- **Purpose**: Data persistence, authentication

Key tables:
- `users` - User profiles and preferences
- `conversations` - Chat sessions
- `messages` - Individual messages
- `user_context` - Companion's memory of user
- `scheduled_messages` - Daily message tracking

### 4. Scheduler (Render Cron)

- **Location**: `/api/api/src/app/jobs/scheduler.py`
- **Purpose**: Send daily check-in messages

Runs every minute, checks for users whose preferred message time matches current time.

## Data Flow

### User Sends Message (Web)

```
1. User types message in web chat
2. Frontend calls POST /conversation/send
3. API authenticates via Supabase JWT
4. ConversationService:
   a. Gets/creates today's conversation
   b. Loads user context from user_context table
   c. Builds system prompt with personality + context
   d. Calls LLM (Gemini/OpenAI/Anthropic)
   e. Saves user message + response to messages table
   f. Extracts new context from exchange (background)
5. Response returned to frontend
```

### Daily Check-in (Scheduler)

```
1. Cron job runs every minute
2. SchedulerService.get_users_for_scheduled_message():
   a. Finds users where NOW matches preferred_message_time
   b. Filters: onboarding complete, has channel, not messaged today
3. For each user:
   a. Load user context
   b. Get weather for location (optional)
   c. Generate personalized message via LLM
   d. Send via Telegram/WhatsApp
   e. Create conversation record
   f. Mark scheduled_message as sent
```

### Telegram Message

```
1. User sends message to Telegram bot
2. Telegram sends webhook to /telegram/webhook
3. API verifies webhook signature
4. Looks up user by telegram_user_id
5. Creates/continues conversation
6. Generates response via LLM
7. Sends response back via Telegram API
```

## Key Design Decisions

### Push-Based Architecture

Unlike traditional chatbots that wait for users, the companion proactively reaches out daily. This creates a more natural relationship dynamic.

### Context Extraction

The companion automatically extracts and remembers:
- Personal facts (name, job, location)
- Preferences (likes, dislikes)
- Events (upcoming meetings, birthdays)
- Goals (things they're working toward)
- Relationships (people in their life)
- Emotions (recurring feelings)
- Situations (ongoing life circumstances)

### Multi-Channel Support

Designed to work across:
- Web chat (primary)
- Telegram (implemented)
- WhatsApp (future)

Each channel connects to the same user profile and conversation history.

### Personality Customization

Users choose their companion's:
- Name (default: Aria)
- Support style (motivational, friendly, accountability, listener)
- Preferred message time
