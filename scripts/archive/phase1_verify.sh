#!/bin/bash

# Phase 1 Verification Script
# Verifies all Phase 1 migrations completed successfully

set -e

PG_DUMP_URL="${PG_DUMP_URL:-postgresql://postgres.galytxxkrbksilekmhcw:4ogIUdwWzVyPH0nU@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require}"

echo "======================================================================"
echo "Phase 1 Migration Verification"
echo "======================================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Helper function
check_result() {
  if [ $1 -eq 0 ]; then
    echo -e "${GREEN}✅${NC} $2"
  else
    echo -e "${RED}❌${NC} $2"
    FAILURES=$((FAILURES + 1))
  fi
}

# 1. Check tables exist
echo "1. Checking required tables..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
  'agent_catalog',
  'project_agents',
  'work_sessions',
  'asset_type_catalog',
  'reference_assets',
  'blocks',
  'agent_config_history'
);
" | tr -d ' ')

[ "$RESULT" = "7" ]
check_result $? "All 7 required tables exist"

# 2. Check agent_catalog columns
echo ""
echo "2. Checking agent_catalog schema..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name = 'agent_catalog'
AND column_name IN ('icon', 'config_schema', 'is_beta', 'schema_version', 'deprecated_at', 'notes');
" | tr -d ' ')

[ "$RESULT" = "6" ]
check_result $? "agent_catalog has all 6 new columns"

# 3. Check project_agents config columns
echo ""
echo "3. Checking project_agents config columns..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name = 'project_agents'
AND column_name IN ('config', 'config_version', 'config_updated_at', 'config_updated_by');
" | tr -d ' ')

[ "$RESULT" = "4" ]
check_result $? "project_agents has all 4 config columns"

# 4. Check executed_by_agent_id removed
echo ""
echo "4. Checking work_sessions cleanup..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name = 'work_sessions' AND column_name = 'executed_by_agent_id';
" | tr -d ' ')

[ "$RESULT" = "0" ]
check_result $? "executed_by_agent_id removed from work_sessions"

# 5. Check asset_type_catalog seeded
echo ""
echo "5. Checking asset_type_catalog seed data..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM asset_type_catalog WHERE is_active = true;
" | tr -d ' ')

[ "$RESULT" -ge "7" ]
check_result $? "asset_type_catalog has 7+ asset types"

# 6. Check reference_assets table
echo ""
echo "6. Checking reference_assets table..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM information_schema.tables
WHERE table_name = 'reference_assets';
" | tr -d ' ')

[ "$RESULT" = "1" ]
check_result $? "reference_assets table exists"

# 7. Check blocks.derived_from_asset_id
echo ""
echo "7. Checking blocks provenance column..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name = 'blocks' AND column_name = 'derived_from_asset_id';
" | tr -d ' ')

[ "$RESULT" = "1" ]
check_result $? "blocks.derived_from_asset_id exists"

# 8. Check storage bucket
echo ""
echo "8. Checking storage bucket..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM storage.buckets WHERE id = 'yarnnn-assets';
" | tr -d ' ')

[ "$RESULT" = "1" ]
check_result $? "yarnnn-assets bucket exists"

RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT public FROM storage.buckets WHERE id = 'yarnnn-assets';
" | tr -d ' ')

[ "$RESULT" = "f" ]
check_result $? "yarnnn-assets bucket is private"

# 9. Check RLS policies
echo ""
echo "9. Checking RLS policies..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('agent_catalog', 'project_agents', 'reference_assets', 'asset_type_catalog', 'agent_config_history');
" | tr -d ' ')

[ "$RESULT" -ge "15" ]
check_result $? "At least 15 RLS policies configured"

# 10. Check storage RLS policies
echo ""
echo "10. Checking storage RLS policies..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM pg_policies
WHERE schemaname = 'storage'
AND tablename = 'objects'
AND (policyname LIKE '%yarnnn-assets%' OR policyname LIKE '%workspace baskets%');
" | tr -d ' ')

[ "$RESULT" -ge "5" ]
check_result $? "At least 5 storage RLS policies configured"

# 11. Check key indexes
echo ""
echo "11. Checking indexes..."
RESULT=$(psql "$PG_DUMP_URL" -t -c "
SELECT COUNT(*) FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('reference_assets', 'project_agents', 'agent_config_history')
AND indexname LIKE 'idx_%';
" | tr -d ' ')

[ "$RESULT" -ge "15" ]
check_result $? "At least 15 indexes created"

# Summary
echo ""
echo "======================================================================"
if [ $FAILURES -eq 0 ]; then
  echo -e "${GREEN}✅ All Phase 1 verifications passed!${NC}"
  echo "======================================================================"
  echo ""
  echo "Next Steps:"
  echo "  1. Deploy substrate-API file upload endpoints"
  echo "  2. Deploy work-platform BFF proxy routes"
  echo "  3. Build UI components (Assets tab, Config forms)"
  echo "  4. Test end-to-end asset upload/download flow"
  exit 0
else
  echo -e "${RED}❌ $FAILURES verification(s) failed${NC}"
  echo "======================================================================"
  echo ""
  echo "Review the failures above and:"
  echo "  1. Check migration logs for errors"
  echo "  2. Re-run failed migrations if needed"
  echo "  3. Use rollback script if necessary:"
  echo "     psql \$PG_DUMP_URL -f supabase/migrations/20251113_phase1_rollback.sql"
  exit 1
fi
