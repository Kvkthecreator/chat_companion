-- =============================================================================
-- Migration: 108_fix_messages_table
-- Description: Fix messages table naming inconsistency
--
-- Problem: Schema created companion_messages, but services query 'messages'
-- Solution: Add conversation_id column to messages table for companion use
-- =============================================================================

-- Add conversation_id column to messages table (nullable at first for backward compat)
ALTER TABLE messages ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE;

-- Create index for conversation-based queries (used by chat companion)
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at)
WHERE conversation_id IS NOT NULL;

-- Update trigger to handle conversation message counts
-- Note: episode_id column doesn't exist in production schema, so we only handle conversation_id
CREATE OR REPLACE FUNCTION update_message_counts()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Update conversation count if conversation_id exists
        IF NEW.conversation_id IS NOT NULL THEN
            UPDATE conversations SET message_count = message_count + 1 WHERE id = NEW.conversation_id;
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.conversation_id IS NOT NULL THEN
            UPDATE conversations SET message_count = message_count - 1 WHERE id = OLD.conversation_id;
        END IF;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Drop old trigger if exists and create new one
DROP TRIGGER IF EXISTS messages_count_trigger ON messages;
CREATE TRIGGER messages_count_trigger
    AFTER INSERT OR DELETE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_message_counts();

-- Add RLS policy for conversation-based access
DROP POLICY IF EXISTS "Users can view conversation messages" ON messages;
CREATE POLICY "Users can view conversation messages" ON messages
    FOR SELECT
    USING (
        conversation_id IS NOT NULL AND
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = messages.conversation_id
            AND c.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can insert conversation messages" ON messages;
CREATE POLICY "Users can insert conversation messages" ON messages
    FOR INSERT
    WITH CHECK (
        conversation_id IS NOT NULL AND
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = messages.conversation_id
            AND c.user_id = auth.uid()
        )
    );

-- Note: The companion_messages table becomes redundant after this migration
-- It can be deprecated but kept for safety. New messages should use the
-- messages table with conversation_id populated.
