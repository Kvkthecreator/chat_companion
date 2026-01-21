# Database Schema

Run this SQL in Supabase SQL Editor to create the companion app tables.

## Core Tables

```sql
-- ============================================================================
-- USERS TABLE (extends Supabase auth.users)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    companion_name TEXT DEFAULT 'Aria',
    timezone TEXT DEFAULT 'America/New_York',
    preferred_message_time TIME DEFAULT '09:00:00',
    support_style TEXT DEFAULT 'friendly_checkin',
    location TEXT,

    -- Telegram integration
    telegram_user_id BIGINT UNIQUE,
    telegram_username TEXT,
    telegram_linked_at TIMESTAMPTZ,

    -- WhatsApp integration (future)
    whatsapp_number TEXT,
    whatsapp_linked_at TIMESTAMPTZ,

    -- Onboarding
    onboarding_completed_at TIMESTAMPTZ,

    -- Subscription
    subscription_status TEXT DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    lemonsqueezy_customer_id TEXT,
    lemonsqueezy_subscription_id TEXT,

    -- Usage tracking
    flux_generations_used INT DEFAULT 0,
    flux_generations_reset_at TIMESTAMPTZ DEFAULT NOW(),
    messages_sent_count INT DEFAULT 0,
    messages_reset_at TIMESTAMPTZ DEFAULT NOW(),

    -- Preferences (JSON)
    preferences JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ONBOARDING TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.onboarding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    current_step TEXT DEFAULT 'welcome',
    completed_at TIMESTAMPTZ,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- CONVERSATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    channel TEXT NOT NULL DEFAULT 'web', -- web, telegram, whatsapp
    initiated_by TEXT DEFAULT 'user', -- user, companion
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    message_count INT DEFAULT 0,
    mood_summary TEXT,
    topics JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX idx_conversations_started_at ON public.conversations(started_at DESC);

-- ============================================================================
-- MESSAGES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- user, assistant
    content TEXT NOT NULL,
    telegram_message_id BIGINT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX idx_messages_created_at ON public.messages(created_at DESC);

-- ============================================================================
-- USER CONTEXT TABLE (Companion's memory)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    category TEXT NOT NULL, -- fact, preference, event, goal, relationship, emotion, situation, routine, struggle
    key TEXT NOT NULL, -- unique identifier within category
    value TEXT NOT NULL, -- the actual information
    importance_score FLOAT DEFAULT 0.5,
    emotional_valence INT DEFAULT 0, -- -2 to +2
    source TEXT DEFAULT 'extracted', -- extracted, manual
    expires_at TIMESTAMPTZ, -- for time-bound context
    last_referenced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, category, key)
);

CREATE INDEX idx_user_context_user_id ON public.user_context(user_id);
CREATE INDEX idx_user_context_category ON public.user_context(category);

-- ============================================================================
-- SCHEDULED MESSAGES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.scheduled_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES public.conversations(id),
    scheduled_for TIMESTAMPTZ NOT NULL,
    content TEXT,
    status TEXT DEFAULT 'pending', -- pending, sent, failed
    sent_at TIMESTAMPTZ,
    failure_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scheduled_messages_user_id ON public.scheduled_messages(user_id);
CREATE INDEX idx_scheduled_messages_status ON public.scheduled_messages(status);

-- ============================================================================
-- TELEGRAM LINK TOKENS (for account linking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.telegram_link_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_telegram_link_tokens_token ON public.telegram_link_tokens(token);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.onboarding ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scheduled_messages ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY users_own_data ON public.users
    FOR ALL USING (auth.uid() = id);

CREATE POLICY onboarding_own_data ON public.onboarding
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY conversations_own_data ON public.conversations
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY messages_own_data ON public.messages
    FOR ALL USING (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );

CREATE POLICY user_context_own_data ON public.user_context
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY scheduled_messages_own_data ON public.scheduled_messages
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON public.conversations
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER update_user_context_updated_at
    BEFORE UPDATE ON public.user_context
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at();
```

## Verify Installation

After running the schema, verify tables exist:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Expected output:
- conversations
- messages
- onboarding
- scheduled_messages
- telegram_link_tokens
- user_context
- users
