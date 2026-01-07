-- =============================================================================
-- Migration 056: Fix Episode 0 Costs
-- =============================================================================
-- ISSUE: Episode 0 (entry episodes) were seeded with episode_cost = 3 instead
-- of 0 after migration 028 set the default. New content inserted after 028
-- used the default value instead of explicitly setting cost = 0.
--
-- This caused users to be charged 3 Sparks for the "free trial" episode,
-- which should have been free as per the Ticket + Moments model.
--
-- FIX: Set episode_cost = 0 for all episodes where:
--   - episode_number = 0, OR
--   - episode_type = 'entry'
-- =============================================================================

-- Fix all Episode 0 and entry episodes to have cost = 0
UPDATE episode_templates
SET episode_cost = 0
WHERE episode_number = 0 OR episode_type = 'entry';

-- Also ensure Play Mode episodes remain free (already should be from migration 028)
UPDATE episode_templates et
SET episode_cost = 0
FROM series s
WHERE et.series_id = s.id
AND s.series_type = 'play';

-- Verify the fix
SELECT
  s.slug as series_slug,
  et.episode_number,
  et.episode_type,
  et.episode_cost
FROM episode_templates et
JOIN series s ON s.id = et.series_id
WHERE et.episode_number = 0 OR et.episode_type = 'entry'
ORDER BY s.slug;

-- Log summary
DO $$
DECLARE
  updated_count INT;
BEGIN
  SELECT COUNT(*) INTO updated_count
  FROM episode_templates
  WHERE (episode_number = 0 OR episode_type = 'entry')
  AND episode_cost = 0;

  RAISE NOTICE 'Fixed episode_cost to 0 for % entry/episode-0 templates', updated_count;
END $$;
