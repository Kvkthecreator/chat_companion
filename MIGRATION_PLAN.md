# Chat Companion - Migration Plan

## From: Episode 0 (Interactive Fiction Platform)
## To: Push-Based AI Companion (Telegram/WhatsApp)

---

## Executive Summary

Pivoting from Episode 0 to a push-based AI companion that initiates daily contact via Telegram (primary) and WhatsApp (secondary). The core value proposition: **being reached out to - feeling like someone is thinking about you**.

---

## Current Architecture Assessment

### Tech Stack (Keeping)
- **Frontend**: Next.js 15.1.9 + React 18 + TypeScript
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL via Supabase
- **Payments**: LemonSqueezy (existing integration)
- **LLM**: Provider-agnostic (Google/OpenAI/Anthropic)

### Components to Reuse
| Component | Location | Adaptation Needed |
|-----------|----------|-------------------|
| Auth system | `web/src/lib/supabase/` | Minimal - add Telegram linking |
| LLM service | `api/api/src/app/services/llm.py` | None - fully reusable |
| Memory system | `api/api/src/app/services/memory.py` | Adapt types for companion context |
| Subscription | `api/api/src/app/routes/subscription.py` | Update limits for new model |
| API patterns | `api/api/src/app/` | Keep structure, replace routes |

### Components to Remove
- All series/episode content models
- Director and narrative prompting system
- Tickets/moments/sparks monetization
- Starter prompts and episode selection
- Guest mode session handling
- All isekai/story-specific content
- Character/world/roles systems
- Visual/scene generation
- Quiz/play modes

---

## Phase 1: Clean Slate

### 1.1 Purge Documentation
Delete entire `docs/` folder - all Episode 0 specific documentation.

### 1.2 Purge Database Migrations
Archive old migrations, create fresh schema for companion app.

### 1.3 Purge Backend Routes
Remove Episode 0 specific routes:
- `characters.py`, `worlds.py`, `roles.py`
- `episode_templates.py`, `series.py`
- `scenes.py`, `director.py`
- `games.py`, `avatars.py`
- `hooks.py` (old follow-up system)
- `credits.py` (sparks system)

### 1.4 Purge Frontend Pages
Remove:
- `/chat/[characterId]` - old chat interface
- `/series/[slug]` - series pages
- `/play/*` - game modes
- `/studio/*` - creator tools (keep admin)
- `/characters`, `/discover`, `/my-characters`
- `/playground`

---

## Phase 2: New Database Schema

### Core Tables

```sql
-- Users (extends Supabase auth.users)
CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email TEXT NOT NULL,
    name TEXT,
    timezone TEXT DEFAULT 'UTC',
    preferred_message_time TIME DEFAULT '09:00',
    support_style TEXT DEFAULT 'friendly_checkin', -- motivational, friendly_checkin, accountability, listener
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Telegram linking
    telegram_user_id BIGINT UNIQUE,
    telegram_username TEXT,
    telegram_linked_at TIMESTAMPTZ,

    -- WhatsApp linking (future)
    whatsapp_number TEXT UNIQUE,
    whatsapp_linked_at TIMESTAMPTZ,

    -- Subscription
    subscription_status TEXT DEFAULT 'free', -- free, trial, premium, cancelled
    subscription_expires_at TIMESTAMPTZ,
    lemonsqueezy_customer_id TEXT,
    lemonsqueezy_subscription_id TEXT,

    -- Preferences
    preferences JSONB DEFAULT '{}'
);

-- User Context (remembered facts about their life)
CREATE TABLE user_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category TEXT NOT NULL, -- fact, preference, event, goal, relationship, emotion, situation
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    importance_score FLOAT DEFAULT 0.5,
    emotional_valence INT DEFAULT 0, -- -2 to +2
    source TEXT, -- extracted, user_provided
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_referenced_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ, -- for time-bound context like "meeting tomorrow"

    UNIQUE(user_id, category, key)
);

-- Conversations (daily conversation threads)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    channel TEXT NOT NULL, -- telegram, whatsapp, web
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    message_count INT DEFAULT 0,

    -- Metadata
    initiated_by TEXT NOT NULL, -- companion, user
    mood_summary TEXT,
    topics JSONB DEFAULT '[]'
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- user, assistant
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Telegram specific
    telegram_message_id BIGINT,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Scheduled Messages (for daily check-ins)
CREATE TABLE scheduled_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,

    -- Content (generated at send time or pre-generated)
    content TEXT,
    generation_context JSONB, -- context used to generate

    -- Status
    status TEXT DEFAULT 'pending', -- pending, sent, failed, skipped
    failure_reason TEXT,

    -- Result
    conversation_id UUID REFERENCES conversations(id),

    UNIQUE(user_id, scheduled_for)
);

-- Onboarding (track progress)
CREATE TABLE onboarding (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    step TEXT DEFAULT 'name', -- name, timezone, time, style, interests, channel
    completed_at TIMESTAMPTZ,
    data JSONB DEFAULT '{}'
);

-- Usage tracking (for free tier limits)
CREATE TABLE usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    messages_sent INT DEFAULT 0,
    messages_received INT DEFAULT 0,

    UNIQUE(user_id, date)
);
```

### Indexes
```sql
CREATE INDEX idx_users_telegram ON users(telegram_user_id) WHERE telegram_user_id IS NOT NULL;
CREATE INDEX idx_users_preferred_time ON users(preferred_message_time);
CREATE INDEX idx_scheduled_messages_pending ON scheduled_messages(scheduled_for) WHERE status = 'pending';
CREATE INDEX idx_conversations_user ON conversations(user_id, started_at DESC);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_user_context_user ON user_context(user_id, category);
```

---

## Phase 3: Backend Architecture

### New Route Structure
```
api/api/src/app/routes/
├── health.py          # Keep - health checks
├── auth.py            # NEW - auth endpoints
├── users.py           # NEW - user profile CRUD
├── onboarding.py      # NEW - onboarding flow
├── telegram.py        # NEW - Telegram webhook + commands
├── whatsapp.py        # NEW - WhatsApp webhook (future)
├── conversations.py   # ADAPT - simplified from old
├── messages.py        # ADAPT - simplified
├── scheduler.py       # NEW - scheduling endpoints
├── subscription.py    # ADAPT - update limits
└── webhooks.py        # ADAPT - keep structure
```

### New Services
```
api/api/src/app/services/
├── llm.py             # Keep - AI generation
├── memory.py          # ADAPT - context extraction
├── companion.py       # NEW - companion personality/prompting
├── scheduler.py       # NEW - message scheduling logic
├── telegram.py        # NEW - Telegram bot service
├── whatsapp.py        # NEW - WhatsApp service (future)
└── context.py         # NEW - context retrieval for messages
```

### Companion Prompting System
```python
# services/companion.py

SUPPORT_STYLES = {
    "motivational": {
        "tone": "encouraging and energizing",
        "focus": "goals, growth, and positive momentum",
        "morning_energy": "high"
    },
    "friendly_checkin": {
        "tone": "warm and casual, like a close friend",
        "focus": "how they're feeling, what's going on",
        "morning_energy": "medium"
    },
    "accountability": {
        "tone": "supportive but direct",
        "focus": "progress on goals, habits, commitments",
        "morning_energy": "medium-high"
    },
    "listener": {
        "tone": "gentle and present",
        "focus": "creating space to share, validating feelings",
        "morning_energy": "low-medium"
    }
}

COMPANION_SYSTEM_PROMPT = """
You are a caring AI companion. Your role is to reach out to {name} daily and be someone who genuinely cares about their wellbeing.

## Your Personality
- Warm and supportive, like a caring friend
- Not overly bubbly or fake-positive
- Remembers previous conversations naturally
- Asks thoughtful follow-up questions
- Adapts tone to their current mood and preferences

## Support Style: {support_style}
{style_description}

## What You Know About {name}
{user_context}

## Recent Conversation Summary
{recent_summary}

## Today's Context
- Day: {day_of_week}
- Their local time: {local_time}
- Weather: {weather_info}

## Guidelines
- Keep messages concise but personal
- Reference specific things they've shared
- If they mentioned something upcoming, ask about it
- Match their energy - don't be hyper if they're tired
- End with something that invites response without pressure
"""
```

---

## Phase 4: Telegram Bot Integration

### Setup
1. Create bot via BotFather
2. Set webhook URL to `https://api.yourapp.com/telegram/webhook`
3. Configure commands: `/start`, `/settings`, `/pause`, `/resume`

### Bot Service
```python
# services/telegram.py

from telegram import Bot, Update
from telegram.ext import Application

class TelegramService:
    def __init__(self, token: str):
        self.bot = Bot(token)

    async def send_message(self, telegram_user_id: int, text: str) -> int:
        """Send message, return message_id"""
        message = await self.bot.send_message(
            chat_id=telegram_user_id,
            text=text,
            parse_mode='Markdown'
        )
        return message.message_id

    async def handle_webhook(self, update: Update):
        """Process incoming message"""
        # Extract user info
        # Find or create conversation
        # Generate response
        # Send reply
        pass
```

### Deep Linking
- Onboarding generates link: `https://t.me/YourBotName?start={user_id_hash}`
- Bot `/start` command links Telegram to web account

---

## Phase 5: Message Scheduler

### Scheduler Service
```python
# services/scheduler.py

async def get_users_to_message_now() -> List[User]:
    """
    Find users whose preferred_message_time matches current time
    in their timezone, who haven't been messaged today.
    """
    pass

async def generate_daily_message(user: User) -> str:
    """
    Generate personalized morning message using:
    - User preferences and support style
    - Recent conversation context
    - Extracted user context (what's going on in their life)
    - Day of week
    - Any pending follow-ups
    """
    pass

async def send_scheduled_messages():
    """
    Main scheduler job - runs every minute.
    """
    users = await get_users_to_message_now()
    for user in users:
        message = await generate_daily_message(user)
        await telegram_service.send_message(user.telegram_user_id, message)
        await mark_message_sent(user.id)
```

### Render Cron Job
```yaml
# render.yaml
services:
  - type: cron
    name: message-scheduler
    schedule: "* * * * *"  # Every minute
    buildCommand: pip install -r requirements.txt
    startCommand: python -m app.jobs.scheduler
```

---

## Phase 6: Web Frontend

### New Pages
```
web/src/app/
├── (auth)/
│   └── login/                 # Keep
├── (onboarding)/
│   └── onboarding/
│       ├── page.tsx           # Main onboarding flow
│       └── steps/
│           ├── Name.tsx
│           ├── Timezone.tsx
│           ├── MessageTime.tsx
│           ├── SupportStyle.tsx
│           ├── Interests.tsx   # Optional
│           └── ConnectTelegram.tsx
├── (dashboard)/
│   ├── dashboard/             # Simple home - status, next message
│   ├── settings/              # Keep & adapt
│   └── history/               # Conversation history (optional)
├── auth/callback/             # Keep
└── page.tsx                   # Landing page
```

### Minimal UI
The web interface is intentionally minimal since most interaction happens in Telegram:
- Landing page with value prop
- Google sign-in
- Onboarding wizard
- Settings page
- Subscription management

---

## Phase 7: Memory System Adaptation

### Context Categories (Updated)
```python
CONTEXT_CATEGORIES = {
    "fact": "Personal facts (name, job, location, age)",
    "preference": "Likes, dislikes, preferences",
    "event": "Upcoming or past significant events",
    "goal": "Things they're working toward",
    "relationship": "People in their life",
    "emotion": "Significant emotional states",
    "situation": "Ongoing life situations (job search, moving, etc.)",
    "routine": "Daily habits and routines",
    "struggle": "Challenges they're facing"
}
```

### Extraction Prompt
After each conversation, extract:
- New facts learned
- Updates to existing context
- Things to follow up on
- Mood/emotional state

---

## Phase 8: Subscription Model

### Tiers
```python
SUBSCRIPTION_TIERS = {
    "free": {
        "daily_messages": True,
        "replies_per_day": 5,
        "trial_days": 7
    },
    "premium": {
        "daily_messages": True,
        "replies_per_day": "unlimited",
        "custom_time": True,
        "deeper_personalization": True,
        "price_monthly": 9.99
    }
}
```

### Flow
1. Free users hit reply limit
2. Companion sends checkout link in chat
3. LemonSqueezy webhook updates status
4. Unlocked immediately

---

## Implementation Order

### Week 1: Foundation
1. ✅ Create migration plan (this document)
2. Purge docs folder and Episode 0 content
3. Create new database schema
4. Set up Telegram bot basics

### Week 2: Core Flow
1. Web onboarding (simplified)
2. Telegram linking
3. Basic conversation handling
4. Memory/context storage

### Week 3: Daily Messages
1. Scheduler implementation
2. Morning message generation
3. Context retrieval
4. Follow-up tracking

### Week 4: Polish
1. Subscription integration
2. Settings page
3. Error handling
4. Testing & deployment

---

## Files to Delete

### Docs (entire folder)
```
docs/
```

### Backend Routes to Remove
```
~~PURGED~~ (completed)

---

## Environment Variables (New)

```env
# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=

# WhatsApp (future)
WHATSAPP_API_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=

# Weather API (optional)
OPENWEATHER_API_KEY=

# Keep existing
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
LEMONSQUEEZY_API_KEY=
GOOGLE_API_KEY=
OPENAI_API_KEY=
```

---

## Success Criteria for First Milestone

1. ✅ User signs up on web
2. ✅ Completes onboarding (name, timezone, time, style)
3. ✅ Connects Telegram via deep link
4. ✅ Receives personalized morning message at preferred time
5. ✅ Can reply and have conversation
6. ✅ Companion remembers context for next day

---

## Decisions Made

1. **Companion naming** - User names their companion during onboarding (personal touch)
2. **Web chat** - Yes, web chat is available. Telegram is one channel option, not mandatory
3. **WhatsApp** - V2, build Telegram first
4. **Weather** - Yes, include weather context in morning messages

---

*Document created: 2025-01-21*
*Status: Ready for review and implementation*
