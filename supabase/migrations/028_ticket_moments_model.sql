-- =============================================================================
-- Migration 028: Ticket + Moments Monetization Model
-- =============================================================================
-- This migration implements the "Ticket + Moments" monetization model:
--
-- KEY CHANGES:
-- 1. Episodes are content units - users pay to ENTER, not per-action
-- 2. visual_mode replaces auto_scene_mode (cinematic/minimal/none)
-- 3. generation_budget caps auto-gens per episode (included in entry cost)
-- 4. episode_cost is the spark cost to start an episode
-- 5. entry_paid tracks if user has paid for this episode
-- 6. generations_used tracks auto-gens used in this session
-- 7. manual_generations tracks user-triggered "Capture Moment" gens
--
-- RATIONALE:
-- - Clear value exchange: "I'm buying this story" vs "random spark deductions"
-- - Predictable costs for user AND platform
-- - No mid-experience friction ("should I spend a Spark on this?")
-- - Images feel like rewards, not purchases
--
-- Reference: docs/monetization/MONETIZATION_v2.0_needsupdate.md
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Add new columns to episode_templates
-- -----------------------------------------------------------------------------

-- visual_mode: Defines how visuals are handled for this episode
-- - cinematic: 3-4 auto-gens at narrative beats (Director decides when)
-- - minimal: 1 auto-gen at climax only
-- - none: no auto-gen (manual still available)
ALTER TABLE episode_templates
ADD COLUMN IF NOT EXISTS visual_mode TEXT DEFAULT 'none';

ALTER TABLE episode_templates ADD CONSTRAINT episode_templates_visual_mode_check
    CHECK (visual_mode IN ('cinematic', 'minimal', 'none'));

-- generation_budget: Maximum auto-generated scenes for this episode
-- - cinematic default: 3
-- - minimal default: 1
-- - none default: 0
ALTER TABLE episode_templates
ADD COLUMN IF NOT EXISTS generation_budget INTEGER DEFAULT 0;

-- episode_cost: Sparks required to start this episode
-- - Default: 3 for most episodes
-- - 0 for Episode 0 (entry points) and Play Mode
ALTER TABLE episode_templates
ADD COLUMN IF NOT EXISTS episode_cost INTEGER DEFAULT 3;

-- -----------------------------------------------------------------------------
-- 2. Add new columns to sessions for tracking
-- -----------------------------------------------------------------------------

-- entry_paid: Has the user paid the episode_cost to access this episode?
-- Prevents double-charging when user returns to an episode
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS entry_paid BOOLEAN DEFAULT FALSE;

-- generations_used: Number of auto-generated scenes so far in this session
-- Compared against generation_budget to enforce cap
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS generations_used INTEGER DEFAULT 0;

-- manual_generations: Number of user-triggered "Capture Moment" generations
-- These cost 1 Spark each, regardless of visual_mode
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS manual_generations INTEGER DEFAULT 0;

-- -----------------------------------------------------------------------------
-- 3. Migrate existing data from auto_scene_mode to visual_mode
-- -----------------------------------------------------------------------------

-- Map existing auto_scene_mode values to new visual_mode
-- peaks -> cinematic (narrative beat triggers)
-- rhythmic -> cinematic (we'll handle interval in Director)
-- off -> none
UPDATE episode_templates
SET visual_mode = CASE
    WHEN auto_scene_mode = 'peaks' THEN 'cinematic'
    WHEN auto_scene_mode = 'rhythmic' THEN 'cinematic'
    ELSE 'none'
END
WHERE visual_mode = 'none' OR visual_mode IS NULL;

-- Set generation_budget based on visual_mode
UPDATE episode_templates
SET generation_budget = CASE
    WHEN visual_mode = 'cinematic' THEN 3
    WHEN visual_mode = 'minimal' THEN 1
    ELSE 0
END
WHERE generation_budget = 0 OR generation_budget IS NULL;

-- Set episode_cost: Episode 0 (entry type) is free, others cost 3
UPDATE episode_templates
SET episode_cost = CASE
    WHEN episode_type = 'entry' THEN 0
    WHEN episode_number = 0 THEN 0
    ELSE 3
END
WHERE episode_cost IS NULL;

-- -----------------------------------------------------------------------------
-- 4. Update Play Mode episodes to be free with cinematic visuals
-- -----------------------------------------------------------------------------

-- Play Mode episodes should be free (cost 0) but have visuals (cinematic)
UPDATE episode_templates et
SET
    episode_cost = 0,
    visual_mode = 'cinematic',
    generation_budget = 3
FROM series s
WHERE et.series_id = s.id
AND s.series_type = 'play';

-- -----------------------------------------------------------------------------
-- 5. Mark existing active sessions as entry_paid (grandfather in)
-- -----------------------------------------------------------------------------

-- Users who have already started sessions shouldn't be charged again
UPDATE sessions
SET entry_paid = TRUE
WHERE turn_count > 0;

-- -----------------------------------------------------------------------------
-- 6. Add feature cost for manual generation if not exists
-- -----------------------------------------------------------------------------

-- "Capture Moment" costs 1 Spark
INSERT INTO credit_costs (feature_key, display_name, spark_cost, description, is_active)
VALUES ('capture_moment', 'Capture This Moment', 1, 'Manually generate a scene image at any time', true)
ON CONFLICT (feature_key) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    spark_cost = EXCLUDED.spark_cost,
    description = EXCLUDED.description;

-- Episode access feature cost (looked up dynamically from episode_templates.episode_cost)
INSERT INTO credit_costs (feature_key, display_name, spark_cost, description, is_active)
VALUES ('episode_access', 'Episode Access', 3, 'Default cost to start an episode (actual cost from episode_templates)', true)
ON CONFLICT (feature_key) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- -----------------------------------------------------------------------------
-- 7. Add comments for documentation
-- -----------------------------------------------------------------------------

COMMENT ON COLUMN episode_templates.visual_mode IS
'Visual generation mode: cinematic (3-4 auto-gens at narrative beats), minimal (1 at climax), none (manual only)';

COMMENT ON COLUMN episode_templates.generation_budget IS
'Maximum number of auto-generated scenes included in episode cost. Director respects this cap.';

COMMENT ON COLUMN episode_templates.episode_cost IS
'Sparks required to start this episode. 0 for Episode 0, Play Mode, and premium users.';

COMMENT ON COLUMN sessions.entry_paid IS
'Whether user has paid the episode_cost for this episode. Prevents double-charging on resume.';

COMMENT ON COLUMN sessions.generations_used IS
'Count of auto-generated scenes in this session. Compared against generation_budget.';

COMMENT ON COLUMN sessions.manual_generations IS
'Count of user-triggered "Capture Moment" generations. Each costs 1 Spark.';

-- -----------------------------------------------------------------------------
-- 8. Create index for efficient episode access checks
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_sessions_entry_paid ON sessions(user_id, episode_template_id, entry_paid);

-- -----------------------------------------------------------------------------
-- 9. Verify the migration
-- -----------------------------------------------------------------------------

SELECT
    title,
    visual_mode,
    generation_budget,
    episode_cost,
    episode_type
FROM episode_templates
WHERE status = 'active'
ORDER BY episode_cost, visual_mode
LIMIT 20;
