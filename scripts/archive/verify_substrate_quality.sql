-- Verification script for substrate quality improvements
-- Run with: psql "$PG_DUMP_URL" -f scripts/verify_substrate_quality.sql

\echo '================================================'
\echo 'SUBSTRATE QUALITY IMPROVEMENTS - VERIFICATION'
\echo '================================================'

\echo ''
\echo '1. Checking block_usage table exists...'
SELECT COUNT(*) as block_usage_table_exists
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name = 'block_usage';

\echo ''
\echo '2. Checking extraction_quality_metrics table exists...'
SELECT COUNT(*) as metrics_table_exists
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name = 'extraction_quality_metrics';

\echo ''
\echo '3. Checking last_validated_at column on blocks...'
SELECT COUNT(*) as staleness_column_exists
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'blocks'
  AND column_name = 'last_validated_at';

\echo ''
\echo '4. Checking basket_substrate_context view exists...'
SELECT COUNT(*) as context_view_exists
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name = 'basket_substrate_context';

\echo ''
\echo '5. Checking increment_block_usage function exists...'
SELECT COUNT(*) as increment_function_exists
FROM pg_proc
WHERE proname = 'increment_block_usage';

\echo ''
\echo '6. Checking log_extraction_metrics function exists...'
SELECT COUNT(*) as log_metrics_function_exists
FROM pg_proc
WHERE proname = 'log_extraction_metrics';

\echo ''
\echo '7. Checking mark_related_blocks_stale trigger exists...'
SELECT COUNT(*) as staleness_trigger_exists
FROM pg_trigger
WHERE tgname = 'trigger_mark_blocks_stale_on_new_dump';

\echo ''
\echo '8. Checking auto_increment_usage trigger exists...'
SELECT COUNT(*) as usage_trigger_exists
FROM pg_trigger
WHERE tgname = 'trigger_auto_increment_usage_on_substrate_reference';

\echo ''
\echo '================================================'
\echo 'TEST: Insert test block and track usage'
\echo '================================================'

-- Create test block
INSERT INTO blocks (basket_id, workspace_id, semantic_type, title, content, status)
VALUES (
  gen_random_uuid(),
  gen_random_uuid(),
  'test',
  'Verification test block',
  'This block tests the usage tracking system',
  'proposed'
)
RETURNING id AS test_block_id \gset

\echo 'Created test block:' :test_block_id

-- Increment usage 3 times
SELECT increment_block_usage(:'test_block_id');
SELECT increment_block_usage(:'test_block_id');
SELECT increment_block_usage(:'test_block_id');

\echo ''
\echo 'Usage tracking after 3 increments:'
SELECT
  block_id,
  times_referenced,
  usefulness_score,
  last_used_at
FROM block_usage
WHERE block_id = :'test_block_id';

-- Cleanup
DELETE FROM blocks WHERE id = :'test_block_id';

\echo ''
\echo '================================================'
\echo 'TEST: Log extraction metrics'
\echo '================================================'

SELECT log_extraction_metrics(
  gen_random_uuid(), -- dump_id
  gen_random_uuid(), -- basket_id
  gen_random_uuid(), -- workspace_id
  'verification_test_v1', -- agent_version
  'context_aware_extraction', -- extraction_method
  8, -- blocks_created
  5, -- context_items_created
  0.87, -- avg_confidence
  1800 -- processing_time_ms
) AS test_metric_id \gset

\echo 'Logged test metric:' :test_metric_id

\echo ''
\echo 'Latest extraction metrics:'
SELECT
  agent_version,
  extraction_method,
  blocks_created,
  context_items_created,
  avg_confidence,
  processing_time_ms,
  created_at
FROM extraction_quality_metrics
ORDER BY created_at DESC
LIMIT 3;

\echo ''
\echo '================================================'
\echo 'VERIFICATION COMPLETE ✅'
\echo '================================================'
