-- =============================================================================
-- Mobile Device Support Migration
-- Adds device registration, push tokens, and notification tracking
-- =============================================================================

-- Device tokens for push notifications
CREATE TABLE IF NOT EXISTS user_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL,  -- Unique device identifier (from Expo)
    platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
    push_token TEXT,  -- Expo push token
    push_token_updated_at TIMESTAMPTZ,
    app_version TEXT,
    os_version TEXT,
    device_model TEXT,
    is_active BOOLEAN DEFAULT true,
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, device_id)
);

-- Index for push notification queries
CREATE INDEX idx_user_devices_push ON user_devices(user_id, is_active, push_token)
    WHERE is_active = true AND push_token IS NOT NULL;

CREATE INDEX idx_user_devices_user ON user_devices(user_id, is_active);

-- Track push notification delivery
CREATE TABLE IF NOT EXISTS push_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id UUID REFERENCES user_devices(id) ON DELETE SET NULL,
    scheduled_message_id UUID REFERENCES scheduled_messages(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'clicked')),
    expo_receipt_id TEXT,
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_push_notifications_user ON push_notifications(user_id, created_at DESC);
CREATE INDEX idx_push_notifications_status ON push_notifications(status, created_at)
    WHERE status = 'pending';
CREATE INDEX idx_push_notifications_receipt ON push_notifications(expo_receipt_id)
    WHERE expo_receipt_id IS NOT NULL;

-- Add preferred notification channel to users
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_channel TEXT
    DEFAULT 'push' CHECK (preferred_channel IN ('push', 'telegram', 'whatsapp', 'none'));

COMMENT ON COLUMN users.preferred_channel IS 'Preferred channel for daily messages: push (mobile app), telegram, whatsapp, or none (paused)';

-- Helper to get active push tokens for a user
CREATE OR REPLACE FUNCTION get_user_push_tokens(p_user_id UUID)
RETURNS TABLE (
    device_id UUID,
    push_token TEXT,
    platform TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT ud.id, ud.push_token, ud.platform
    FROM user_devices ud
    WHERE ud.user_id = p_user_id
      AND ud.is_active = true
      AND ud.push_token IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Update scheduled message function to include preferred_channel and check for push devices
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
    message_time_window TEXT,
    preferred_channel TEXT
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
        u.location,
        u.message_time_flexibility,
        u.message_time_window,
        u.preferred_channel
    FROM users u
    WHERE
        -- User has completed onboarding
        u.onboarding_completed_at IS NOT NULL
        -- User has a connected channel (telegram, whatsapp, OR mobile push)
        AND (
            u.telegram_user_id IS NOT NULL
            OR u.whatsapp_number IS NOT NULL
            OR EXISTS (
                SELECT 1 FROM user_devices ud
                WHERE ud.user_id = u.id
                AND ud.is_active = true
                AND ud.push_token IS NOT NULL
            )
        )
        -- Daily messages not paused (preferred_channel != 'none')
        AND COALESCE(u.preferred_channel, 'push') != 'none'
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
