-- Migration 001: Memory Tiers + Personalization Schema
-- Related ADRs: ADR-001, ADR-002, ADR-003
-- Date: 2025-01-21

-- ============================================================================
-- PART 1: MEMORY SYSTEM EXTENSIONS (ADR-001)
-- ============================================================================

-- Add tier column to user_context
-- 'core' = permanent facts, 'thread' = active situations
ALTER TABLE user_context ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'core';

-- Add thread tracking
ALTER TABLE user_context ADD COLUMN IF NOT EXISTS thread_id UUID;

-- Add extraction confidence (0.0-1.0)
ALTER TABLE user_context ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 1.0;

-- Link to source message
ALTER TABLE user_context ADD COLUMN IF NOT EXISTS extracted_from UUID;

-- Indexes for new columns
CREATE INDEX IF NOT EXISTS idx_user_context_tier ON user_context(tier);
CREATE INDEX IF NOT EXISTS idx_user_context_thread ON user_context(thread_id);
CREATE INDEX IF NOT EXISTS idx_user_context_expires ON user_context(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- PART 2: PERSONALIZATION EXTENSIONS (ADR-002)
-- ============================================================================

-- Ensure preferences column exists with proper default
-- (Already exists, but ensure it has the right default)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'preferences'
    ) THEN
        ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}';
    END IF;
END $$;

-- ============================================================================
-- PART 3: ONBOARDING EXTENSIONS (ADR-003)
-- ============================================================================

-- Add personality type from quiz
ALTER TABLE users ADD COLUMN IF NOT EXISTS personality_type TEXT;

-- Store quiz answers for analysis
ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_answers JSONB DEFAULT '{}';

-- Track which onboarding path user took
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_path TEXT;

-- ============================================================================
-- PART 4: DEFAULT PREFERENCES STRUCTURE
-- ============================================================================

-- Update existing users with default preferences structure if empty
UPDATE users
SET preferences = jsonb_build_object(
    'communication', jsonb_build_object(
        'emoji_level', 'moderate',
        'formality', 'casual',
        'message_length', 'moderate'
    ),
    'support', jsonb_build_object(
        'style', support_style,  -- migrate from existing column
        'feedback_type', 'balanced',
        'questions', 'moderate'
    ),
    'boundaries', jsonb_build_object(
        'avoid_topics', '[]'::jsonb,
        'sensitive_topics', '[]'::jsonb
    )
)
WHERE preferences = '{}'::jsonb OR preferences IS NULL;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify columns exist
DO $$
BEGIN
    -- user_context columns
    ASSERT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_context' AND column_name = 'tier');
    ASSERT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_context' AND column_name = 'thread_id');
    ASSERT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_context' AND column_name = 'confidence');

    -- users columns
    ASSERT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'personality_type');
    ASSERT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'quiz_answers');
    ASSERT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'onboarding_path');

    RAISE NOTICE 'Migration 001 completed successfully';
END $$;
