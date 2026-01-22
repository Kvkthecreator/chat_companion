-- =============================================================================
-- Timing Flexibility Migration
-- Adds user-controlled timing preferences for daily messages
-- =============================================================================

-- Add timing flexibility column
-- Options: 'exact', 'around', 'window'
-- 'exact' = message at preferred_message_time (current behavior)
-- 'around' = ±15-30 minutes of preferred_message_time
-- 'window' = within a time block (morning, midday, evening, night)
ALTER TABLE users ADD COLUMN IF NOT EXISTS message_time_flexibility TEXT
    DEFAULT 'exact'
    CHECK (message_time_flexibility IN ('exact', 'around', 'window'));

-- Add time window column for window-based timing
-- Options: 'morning', 'midday', 'evening', 'night'
ALTER TABLE users ADD COLUMN IF NOT EXISTS message_time_window TEXT
    CHECK (message_time_window IN ('morning', 'midday', 'evening', 'night'));

-- Comment for documentation
COMMENT ON COLUMN users.message_time_flexibility IS 'How flexible the daily message timing should be: exact (at preferred_message_time), around (±15-30 min), or window (time block)';
COMMENT ON COLUMN users.message_time_window IS 'Time window for messages when flexibility=window: morning (6-10am), midday (11am-2pm), evening (5-8pm), night (8-11pm)';

-- Update the helper function to handle flexibility
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
    location TEXT,
    message_time_flexibility TEXT,
    message_time_window TEXT
) AS $$
DECLARE
    window_start TIME;
    window_end TIME;
BEGIN
    RETURN QUERY
    SELECT
        u.id as user_id,
        u.display_name,
        u.companion_name,
        u.support_style,
        u.timezone,
        u.telegram_user_id,
        u.location,
        u.message_time_flexibility,
        u.message_time_window
    FROM users u
    WHERE
        -- User has completed onboarding
        u.onboarding_completed_at IS NOT NULL
        -- User has a connected channel
        AND (u.telegram_user_id IS NOT NULL OR u.whatsapp_number IS NOT NULL)
        -- Daily messages not paused
        AND COALESCE((u.preferences->>'daily_messages_paused')::boolean, false) = false
        -- No message sent today
        AND NOT EXISTS (
            SELECT 1 FROM scheduled_messages sm
            WHERE sm.user_id = u.id
            AND sm.status = 'sent'
            AND (sm.sent_at AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date
                = (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date
        )
        -- Time matching based on flexibility setting
        AND (
            -- Exact: within 2 minute window of preferred time
            (COALESCE(u.message_time_flexibility, 'exact') = 'exact'
             AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                 BETWEEN u.preferred_message_time
                 AND (u.preferred_message_time + interval '2 minutes'))
            OR
            -- Around: within 30 minute window centered on preferred time
            (u.message_time_flexibility = 'around'
             AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                 BETWEEN (u.preferred_message_time - interval '15 minutes')
                 AND (u.preferred_message_time + interval '15 minutes'))
            OR
            -- Window: within the specified time block
            (u.message_time_flexibility = 'window'
             AND (
                 (u.message_time_window = 'morning'
                  AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                      BETWEEN '06:00'::time AND '10:00'::time)
                 OR
                 (u.message_time_window = 'midday'
                  AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                      BETWEEN '11:00'::time AND '14:00'::time)
                 OR
                 (u.message_time_window = 'evening'
                  AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                      BETWEEN '17:00'::time AND '20:00'::time)
                 OR
                 (u.message_time_window = 'night'
                  AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                      BETWEEN '20:00'::time AND '23:00'::time)
             ))
        );
END;
$$ LANGUAGE plpgsql;
