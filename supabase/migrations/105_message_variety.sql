-- =============================================================================
-- Message Variety Improvements
-- Prevents repetitive daily messages by tracking topics and enabling variety
-- =============================================================================
-- See: docs/design/COMPANION_PRESENCE_SYSTEM.md

-- Add topic_key to track what specific topic was used in a message
-- This allows us to filter out recently-used topics
ALTER TABLE scheduled_messages ADD COLUMN IF NOT EXISTS topic_key TEXT;
COMMENT ON COLUMN scheduled_messages.topic_key IS
'Identifier for the topic used (e.g., thread_id, followup hash). Used to prevent repetition.';

-- Add message_type to distinguish different kinds of outreach
-- Separate from priority_level which tracks data availability
ALTER TABLE scheduled_messages ADD COLUMN IF NOT EXISTS message_type TEXT;
COMMENT ON COLUMN scheduled_messages.message_type IS
'Type of message: FOLLOWUP, THREAD, PRESENCE, VIBE. Different from priority which tracks data source.';

-- Index for querying recent topics per user (for deduplication)
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_topic
ON scheduled_messages(user_id, topic_key, sent_at DESC)
WHERE topic_key IS NOT NULL AND status = 'sent';

-- Index for message type analytics
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_type
ON scheduled_messages(message_type, sent_at DESC)
WHERE message_type IS NOT NULL;
