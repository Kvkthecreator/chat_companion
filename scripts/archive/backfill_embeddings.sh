#!/bin/bash
# V3.1 Embedding Backfill Script
# Generates embeddings for all existing ACCEPTED blocks in a workspace
#
# Usage:
#   ./scripts/backfill_embeddings.sh <workspace-id>
#
# Example:
#   ./scripts/backfill_embeddings.sh 550e8400-e29b-41d4-a716-446655440000

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: Workspace ID required${NC}"
    echo "Usage: $0 <workspace-id>"
    exit 1
fi

WORKSPACE_ID="$1"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}V3.1 Embedding Backfill Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Workspace ID:${NC} $WORKSPACE_ID"
echo ""

# Verify environment
echo -e "${YELLOW}→ Checking environment...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY not set${NC}"
    exit 1
fi

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo -e "${RED}Error: SUPABASE_URL and SUPABASE_SERVICE_KEY required${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment validated${NC}"
echo ""

# Confirm before proceeding
echo -e "${YELLOW}⚠️  This will generate embeddings for all ACCEPTED blocks in workspace $WORKSPACE_ID${NC}"
echo -e "${YELLOW}⚠️  This may incur OpenAI API costs (~\$0.05 per 1000 blocks)${NC}"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Aborted${NC}"
    exit 0
fi

# Run embedding generation
echo ""
echo -e "${BLUE}→ Starting embedding generation...${NC}"
echo ""

cd "$(dirname "$0")/.."  # Change to project root

python3 -m api.src.jobs.embedding_generator --workspace-id "$WORKSPACE_ID"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Embedding backfill completed successfully${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Embedding backfill failed (exit code: $EXIT_CODE)${NC}"
    echo -e "${RED}========================================${NC}"
    exit $EXIT_CODE
fi
