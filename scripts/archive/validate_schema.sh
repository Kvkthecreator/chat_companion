#!/bin/bash
# Schema Validation Script
# Validates that production database schema matches expected schema definitions
# Usage: ./scripts/validate_schema.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Source dump_schema.sh for PG_DUMP_URL
source "$(dirname "$0")/dump_schema.sh"

echo "🔍 Validating database schema..."

# Function to check if table exists
check_table_exists() {
    local table_name=$1
    local result=$(psql "$PG_DUMP_URL" -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '$table_name');")
    echo "$result" | tr -d '[:space:]'
}

# Function to check if column exists
check_column_exists() {
    local table_name=$1
    local column_name=$2
    local result=$(psql "$PG_DUMP_URL" -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '$table_name' AND column_name = '$column_name');")
    echo "$result" | tr -d '[:space:]'
}

# Function to get column count
get_column_count() {
    local table_name=$1
    psql "$PG_DUMP_URL" -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = '$table_name';" | tr -d '[:space:]'
}

# Validation results
ERRORS=0
WARNINGS=0

echo ""
echo "📋 Validating projects table..."

# Check table exists
if [ "$(check_table_exists 'projects')" = "t" ]; then
    echo -e "${GREEN}✓${NC} projects table exists"

    # Expected columns for projects table
    declare -a expected_columns=(
        "id"
        "workspace_id"
        "basket_id"
        "name"
        "description"
        "user_id"
        "created_at"
        "updated_at"
        "status"
        "project_type"
        "origin_template"
        "onboarded_at"
        "archived_at"
        "metadata"
    )

    # Check each expected column
    for col in "${expected_columns[@]}"; do
        if [ "$(check_column_exists 'projects' "$col")" = "t" ]; then
            echo -e "  ${GREEN}✓${NC} Column: $col"
        else
            echo -e "  ${RED}✗${NC} Missing column: $col"
            ((ERRORS++))
        fi
    done

    # Check column count
    col_count=$(get_column_count 'projects')
    expected_count=${#expected_columns[@]}
    if [ "$col_count" -eq "$expected_count" ]; then
        echo -e "${GREEN}✓${NC} Column count matches: $col_count/$expected_count"
    else
        echo -e "${YELLOW}⚠${NC}  Column count mismatch: $col_count found, $expected_count expected"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗${NC} projects table does not exist!"
    ((ERRORS++))
fi

echo ""
echo "📋 Validating baskets table..."

# Check baskets table columns
if [ "$(check_table_exists 'baskets')" = "t" ]; then
    echo -e "${GREEN}✓${NC} baskets table exists"

    # Key columns for baskets (not exhaustive)
    declare -a basket_columns=(
        "id"
        "workspace_id"
        "user_id"
        "name"
        "status"
        "origin_template"
    )

    for col in "${basket_columns[@]}"; do
        if [ "$(check_column_exists 'baskets' "$col")" = "t" ]; then
            echo -e "  ${GREEN}✓${NC} Column: $col"
        else
            echo -e "  ${RED}✗${NC} Missing column: $col"
            ((ERRORS++))
        fi
    done
else
    echo -e "${RED}✗${NC} baskets table does not exist!"
    ((ERRORS++))
fi

# Summary
echo ""
echo "═══════════════════════════════════════════"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠  Validation completed with $WARNINGS warning(s)${NC}"
    exit 0
else
    echo -e "${RED}✗ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Check if migrations have been run: ls supabase/migrations/"
    echo "2. Run missing migrations on production database"
    echo "3. Consider running: psql \"\$PG_DUMP_URL\" -f supabase/migrations/<migration_file>.sql"
    exit 1
fi
