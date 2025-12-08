#!/bin/bash

# API Contract Testing Script
# Runs focused tests for API endpoints to catch breaking changes

set -e

echo "🧪 Running API Contract Tests..."
echo "====================================="

# Set test environment
export NODE_ENV=test
export PLAYWRIGHT_TEST=true
export TEST_BASKET_ID=${TEST_BASKET_ID:-"da75cf04-65e5-46ac-940a-74e2ffe077a2"}

echo "📋 Test Configuration:"
echo "  - NODE_ENV: $NODE_ENV"
echo "  - TEST_BASKET_ID: $TEST_BASKET_ID"
echo "  - Target: http://localhost:3000"
echo ""

# Check if dev server is running
if ! curl -s http://localhost:3000 > /dev/null; then
  echo "❌ Dev server not running. Please start with:"
  echo "   npm run dev"
  echo "   OR"
  echo "   ./start-dev.sh"
  exit 1
fi

echo "✅ Dev server is running"
echo ""

# Run API contract tests with focused output
echo "🚀 Running critical API endpoint tests..."
echo "----------------------------------------"

# Run tests with specific pattern for critical endpoints
npx playwright test --project=api-contracts --reporter=list --grep="Baskets API Contracts|Database Schema Validation"

echo ""
echo "🔍 Running frontend API contract tests..."
echo "----------------------------------------"

npx playwright test --project=api-contracts tests/api-contracts/frontend-apis.spec.ts --reporter=list

echo ""
echo "📊 Test Summary:"
echo "=================="
echo "✅ API Contract Tests Complete"
echo ""

# Optional: Run all api-contracts if requested
if [ "$1" = "--all" ]; then
  echo "🏃 Running ALL API contract tests..."
  echo "-----------------------------------"
  npx playwright test --project=api-contracts --reporter=list
fi

echo "🎉 Testing complete!"
echo ""
echo "💡 To run specific test groups:"
echo "  - Critical baskets endpoints:  npx playwright test --project=api-contracts --grep='Baskets API'"
echo "  - Database schema validation:  npx playwright test --project=api-contracts --grep='Database Schema'" 
echo "  - Frontend API contracts:      npx playwright test --project=api-contracts frontend-apis.spec.ts"
echo "  - All contract tests:          ./scripts/test-api-contracts.sh --all"