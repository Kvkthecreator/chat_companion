#!/bin/bash
# Backend Build Check Script - Equivalent to npm run build for Python

echo "🚀 Backend Build Check"
echo "======================"

# Run the syntax and import test
python test_syntax.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Backend is ready for deployment!"
    echo "🎯 Run this script before pushing to catch issues early"
else
    echo ""
    echo "❌ Backend has issues that need to be fixed before deployment"
    echo "🔧 Please address the errors above"
    exit 1
fi