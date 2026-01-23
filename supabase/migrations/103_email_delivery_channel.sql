-- =============================================================================
-- Email Delivery Channel Support
-- Enables daily check-in emails for web users
-- =============================================================================

-- Add channel column to scheduled_messages for tracking delivery method
ALTER TABLE scheduled_messages ADD COLUMN IF NOT EXISTS channel TEXT DEFAULT 'push';
COMMENT ON COLUMN scheduled_messages.channel IS 'Delivery channel: push, email';

-- Add priority_level for tracking message personalization quality
ALTER TABLE scheduled_messages ADD COLUMN IF NOT EXISTS priority_level TEXT;
COMMENT ON COLUMN scheduled_messages.priority_level IS 'Message priority: FOLLOW_UP, THREAD, PATTERN, TEXTURE, GENERIC';

-- Add onboarding_path to users table to track which onboarding flow was used
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_path TEXT;
COMMENT ON COLUMN users.onboarding_path IS 'Which onboarding path was used: chat, form';

-- Create index for channel-based queries
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_channel ON scheduled_messages(channel);

-- Create index for priority level analytics
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_priority ON scheduled_messages(priority_level)
    WHERE priority_level IS NOT NULL;
