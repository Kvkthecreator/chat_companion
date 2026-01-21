-- Migration 002: Thread Tracking + Priority-Based Messages
-- Related Feature: MEMORY_SYSTEM.md (Priority Stack)
-- Date: 2025-01-21

-- ============================================================================
-- PART 1: MESSAGE PRIORITY TRACKING
-- ============================================================================

-- Add priority_level to scheduled_messages to track message generation quality
ALTER TABLE scheduled_messages ADD COLUMN IF NOT EXISTS priority_level TEXT;

-- Add comment explaining priority levels
COMMENT ON COLUMN scheduled_messages.priority_level IS
    'Message priority level used: FOLLOW_UP (1), THREAD (2), PATTERN (3), TEXTURE (4), GENERIC (5 = failure state)';

-- Create index for analyzing message quality metrics
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_priority
    ON scheduled_messages(priority_level, sent_at)
    WHERE status = 'sent';

-- ============================================================================
-- PART 2: THREAD METRICS VIEW
-- ============================================================================

-- View for analyzing message priority distribution (operational metrics)
CREATE OR REPLACE VIEW message_priority_metrics AS
SELECT
    DATE_TRUNC('day', sent_at) as day,
    priority_level,
    COUNT(*) as message_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY DATE_TRUNC('day', sent_at)) as percentage
FROM scheduled_messages
WHERE status = 'sent'
    AND sent_at IS NOT NULL
    AND priority_level IS NOT NULL
GROUP BY DATE_TRUNC('day', sent_at), priority_level
ORDER BY day DESC, priority_level;

-- ============================================================================
-- PART 3: FOLLOW-UP TRACKING INDEX
-- ============================================================================

-- Index for quickly finding pending follow-ups
CREATE INDEX IF NOT EXISTS idx_user_context_followups
    ON user_context(user_id, category, updated_at DESC)
    WHERE category = 'follow_up';

-- Index for quickly finding active threads
CREATE INDEX IF NOT EXISTS idx_user_context_threads
    ON user_context(user_id, tier, updated_at DESC)
    WHERE tier = 'thread';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Verify columns exist
    ASSERT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'scheduled_messages' AND column_name = 'priority_level'
    );

    RAISE NOTICE 'Migration 002 (thread tracking) completed successfully';
END $$;
