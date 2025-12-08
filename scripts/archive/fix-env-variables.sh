#!/bin/bash

# Script to add missing NEXT_PUBLIC environment variables to .env file

echo "Adding missing NEXT_PUBLIC environment variables..."

# Check if NEXT_PUBLIC_SUPABASE_URL exists
if ! grep -q "NEXT_PUBLIC_SUPABASE_URL" .env; then
    echo "" >> .env
    echo "# Next.js public environment variables (required for browser client)" >> .env
    echo "NEXT_PUBLIC_SUPABASE_URL=https://galytxxkrbksilekmhcw.supabase.co" >> .env
    echo "✅ Added NEXT_PUBLIC_SUPABASE_URL"
else
    echo "⏭️  NEXT_PUBLIC_SUPABASE_URL already exists"
fi

# Check if NEXT_PUBLIC_SUPABASE_ANON_KEY exists
if ! grep -q "NEXT_PUBLIC_SUPABASE_ANON_KEY" .env; then
    # Extract project ref from the service role key
    # The anon key needs to be retrieved from Supabase dashboard
    echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdhbHl0eHhrcmJrc2lsZWttaGN3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NTU3NjMsImV4cCI6MjA2MjMzMTc2M30.fmELHf-Ge9K-rI0MQDa9vE8QBOJdTKCHNSZ4Xj5AvBw" >> .env
    echo "✅ Added NEXT_PUBLIC_SUPABASE_ANON_KEY (placeholder - update with actual anon key)"
else
    echo "⏭️  NEXT_PUBLIC_SUPABASE_ANON_KEY already exists"
fi

# Also add other useful env vars
if ! grep -q "NEXT_PUBLIC_APP_ENV" .env; then
    echo "NEXT_PUBLIC_APP_ENV=development" >> .env
    echo "✅ Added NEXT_PUBLIC_APP_ENV"
fi

if ! grep -q "API_MODE" .env; then
    echo "API_MODE=remote" >> .env
    echo "✅ Added API_MODE=remote"
fi

echo ""
echo "🔍 Current environment variables:"
echo "-----------------------------------"
grep -E "NEXT_PUBLIC_|SUPABASE_|API_MODE" .env | sed 's/=.*$/=.../'

echo ""
echo "⚠️  IMPORTANT: The NEXT_PUBLIC_SUPABASE_ANON_KEY is a placeholder!"
echo "Please get the actual anon key from your Supabase dashboard:"
echo "1. Go to https://app.supabase.com/project/galytxxkrbksilekmhcw/settings/api"
echo "2. Copy the 'anon public' key"
echo "3. Replace the placeholder in .env"