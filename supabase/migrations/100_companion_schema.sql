-- =============================================================================
-- Chat Companion - Database Schema Migration
-- Push-based AI Companion - Daily check-ins via Telegram/WhatsApp/Web
-- =============================================================================

-- Drop old Episode 0 tables (if they exist and you want a clean slate)
-- WARNING: This will delete all existing data. Comment out if migrating data.
-- DROP TABLE IF EXISTS memory_events CASCADE;
-- DROP TABLE IF EXISTS hooks CASCADE;
-- DROP TABLE IF EXISTS messages CASCADE;
-- DROP TABLE IF EXISTS episodes CASCADE;
-- DROP TABLE IF EXISTS engagements CASCADE;
-- DROP TABLE IF EXISTS roles CASCADE;
-- DROP TABLE IF EXISTS episode_templates CASCADE;
-- DROP TABLE IF EXISTS series CASCADE;
-- DROP TABLE IF EXISTS characters CASCADE;
-- DROP TABLE IF EXISTS worlds CASCADE;

-- =============================================================================
-- Users Table (extends Supabase auth.users)
-- =============================================================================
-- Note: This modifies the existing users table to add companion-specific fields
-- If starting fresh, uncomment the CREATE TABLE below instead

ALTER TABLE users ADD COLUMN IF NOT EXISTS companion_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_message_time TIME DEFAULT '09:00';
ALTER TABLE users ADD COLUMN IF NOT EXISTS support_style TEXT DEFAULT 'friendly_checkin';
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_user_id BIGINT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_username TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_linked_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_number TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_linked_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS location TEXT; -- For weather context (city/country)

-- Ensure timezone column exists (may already exist)
ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'America/New_York';

-- Create index for Telegram user lookup
CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_user_id) WHERE telegram_user_id IS NOT NULL;

-- Create index for scheduling (find users by preferred time)
CREATE INDEX IF NOT EXISTS idx_users_preferred_time ON users(preferred_message_time);

-- =============================================================================
-- User Context Table (remembered facts about user's life)
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Context categorization
    category TEXT NOT NULL, -- fact, preference, event, goal, relationship, emotion, situation, routine, struggle
    key TEXT NOT NULL,      -- e.g., "job", "pet_name", "meeting_tomorrow"
    value TEXT NOT NULL,    -- The actual information

    -- Metadata
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
    emotional_valence INT DEFAULT 0 CHECK (emotional_valence >= -2 AND emotional_valence <= 2),
    source TEXT DEFAULT 'extracted', -- extracted, user_provided

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_referenced_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ, -- For time-bound context like "meeting tomorrow"

    UNIQUE(user_id, category, key)
);

CREATE INDEX IF NOT EXISTS idx_user_context_user ON user_context(user_id, category);
CREATE INDEX IF NOT EXISTS idx_user_context_expiry ON user_context(expires_at) WHERE expires_at IS NOT NULL;

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_user_context_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_user_context_updated_at ON user_context;
CREATE TRIGGER trigger_user_context_updated_at
    BEFORE UPDATE ON user_context
    FOR EACH ROW
    EXECUTE FUNCTION update_user_context_updated_at();

-- =============================================================================
-- Conversations Table (daily conversation threads)
-- =============================================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Channel info
    channel TEXT NOT NULL DEFAULT 'web', -- telegram, whatsapp, web

    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,

    -- Stats
    message_count INT DEFAULT 0,

    -- Metadata
    initiated_by TEXT NOT NULL DEFAULT 'user', -- companion, user
    mood_summary TEXT,
    topics JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_channel ON conversations(channel);

-- =============================================================================
-- Messages Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS companion_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Message content
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,

    -- Channel-specific IDs
    telegram_message_id BIGINT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_companion_messages_conversation ON companion_messages(conversation_id, created_at);

-- Trigger to update conversation message_count
CREATE OR REPLACE FUNCTION update_conversation_message_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE conversations SET message_count = message_count + 1 WHERE id = NEW.conversation_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE conversations SET message_count = message_count - 1 WHERE id = OLD.conversation_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_conversation_message_count ON companion_messages;
CREATE TRIGGER trigger_conversation_message_count
    AFTER INSERT OR DELETE ON companion_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_message_count();

-- =============================================================================
-- Scheduled Messages Table (for daily check-ins)
-- =============================================================================
CREATE TABLE IF NOT EXISTS scheduled_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Scheduling
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,

    -- Content (may be pre-generated or generated at send time)
    content TEXT,
    generation_context JSONB, -- Context used to generate the message

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'skipped')),
    failure_reason TEXT,

    -- Link to resulting conversation
    conversation_id UUID REFERENCES conversations(id),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Only one scheduled message per user per time slot
    UNIQUE(user_id, scheduled_for)
);

CREATE INDEX IF NOT EXISTS idx_scheduled_messages_pending ON scheduled_messages(scheduled_for)
    WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_user ON scheduled_messages(user_id, scheduled_for DESC);

-- =============================================================================
-- Onboarding Table (track onboarding progress)
-- =============================================================================
CREATE TABLE IF NOT EXISTS onboarding (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,

    -- Progress tracking
    current_step TEXT DEFAULT 'welcome', -- welcome, name, companion_name, timezone, time, style, interests, channel, complete
    completed_at TIMESTAMPTZ,

    -- Collected data (stored here during onboarding, then copied to users table)
    data JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_onboarding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_onboarding_updated_at ON onboarding;
CREATE TRIGGER trigger_onboarding_updated_at
    BEFORE UPDATE ON onboarding
    FOR EACH ROW
    EXECUTE FUNCTION update_onboarding_updated_at();

-- =============================================================================
-- Usage Table (for free tier limits)
-- =============================================================================
CREATE TABLE IF NOT EXISTS daily_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Date (in user's timezone, stored as date)
    usage_date DATE NOT NULL,

    -- Counts
    messages_sent INT DEFAULT 0,
    messages_received INT DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_usage_user ON daily_usage(user_id, usage_date DESC);

-- =============================================================================
-- Row Level Security (RLS)
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE user_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE companion_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_usage ENABLE ROW LEVEL SECURITY;

-- User Context policies
CREATE POLICY "Users can view own context" ON user_context
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own context" ON user_context
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own context" ON user_context
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own context" ON user_context
    FOR DELETE USING (auth.uid() = user_id);

-- Conversations policies
CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own conversations" ON conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Messages policies (via conversation ownership)
CREATE POLICY "Users can view own messages" ON companion_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = companion_messages.conversation_id
            AND c.user_id = auth.uid()
        )
    );
CREATE POLICY "Users can insert own messages" ON companion_messages
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = companion_messages.conversation_id
            AND c.user_id = auth.uid()
        )
    );

-- Scheduled messages policies
CREATE POLICY "Users can view own scheduled messages" ON scheduled_messages
    FOR SELECT USING (auth.uid() = user_id);

-- Onboarding policies
CREATE POLICY "Users can view own onboarding" ON onboarding
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own onboarding" ON onboarding
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own onboarding" ON onboarding
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Daily usage policies
CREATE POLICY "Users can view own usage" ON daily_usage
    FOR SELECT USING (auth.uid() = user_id);

-- =============================================================================
-- Service Role Bypass (for backend operations)
-- =============================================================================
-- The service role key bypasses RLS, so backend can:
-- - Schedule messages for any user
-- - Update context from conversation analysis
-- - Manage conversations across channels

-- =============================================================================
-- Helper Functions
-- =============================================================================

-- Function to get users who should receive messages at the current time
CREATE OR REPLACE FUNCTION get_users_for_scheduled_message(
    check_time TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
    user_id UUID,
    display_name TEXT,
    companion_name TEXT,
    support_style TEXT,
    timezone TEXT,
    telegram_user_id BIGINT,
    location TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id as user_id,
        u.display_name,
        u.companion_name,
        u.support_style,
        u.timezone,
        u.telegram_user_id,
        u.location
    FROM users u
    WHERE
        -- User has completed onboarding
        u.onboarding_completed_at IS NOT NULL
        -- User has a connected channel
        AND (u.telegram_user_id IS NOT NULL OR u.whatsapp_number IS NOT NULL)
        -- Current time matches their preferred time (within 1 minute window)
        AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
            BETWEEN u.preferred_message_time
            AND (u.preferred_message_time + interval '1 minute')
        -- No message sent today
        AND NOT EXISTS (
            SELECT 1 FROM scheduled_messages sm
            WHERE sm.user_id = u.id
            AND sm.status = 'sent'
            AND sm.sent_at::date = (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date
        );
END;
$$ LANGUAGE plpgsql;

-- Function to get recent context for a user (for message generation)
CREATE OR REPLACE FUNCTION get_user_context_summary(
    p_user_id UUID,
    p_limit INT DEFAULT 20
)
RETURNS TABLE (
    category TEXT,
    key TEXT,
    value TEXT,
    importance_score FLOAT,
    last_referenced_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        uc.category,
        uc.key,
        uc.value,
        uc.importance_score,
        uc.last_referenced_at
    FROM user_context uc
    WHERE uc.user_id = p_user_id
        AND (uc.expires_at IS NULL OR uc.expires_at > NOW())
    ORDER BY
        uc.importance_score DESC,
        uc.last_referenced_at DESC NULLS LAST,
        uc.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Seed Support Styles (reference data)
-- =============================================================================
COMMENT ON COLUMN users.support_style IS 'Support styles: motivational, friendly_checkin, accountability, listener';

-- Support style descriptions (for reference):
-- motivational: Encouraging and energizing, focuses on goals and positive momentum
-- friendly_checkin: Warm and casual like a close friend, focuses on how they''re feeling
-- accountability: Supportive but direct, focuses on progress and commitments
-- listener: Gentle and present, creates space to share and validates feelings
