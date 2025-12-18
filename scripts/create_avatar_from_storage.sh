#!/bin/bash
# Create avatar kit from existing storage image
#
# Usage: ./scripts/create_avatar_from_storage.sh <character_id> <source_bucket> <source_path> [character_name]
#
# Example:
#   ./scripts/create_avatar_from_storage.sh e60042ca-83c2-4861-b9f9-d24d73d4aa4d scenes series/weekend-regular/cover.png "Minji"
#
# This script:
# 1. Downloads image from source bucket
# 2. Uploads to avatars bucket
# 3. Creates avatar_kit and avatar_asset records
# 4. Links kit to character

set -e

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: $0 <character_id> <source_bucket> <source_path> [character_name]"
    echo ""
    echo "Example:"
    echo "  $0 e60042ca-83c2-4861-b9f9-d24d73d4aa4d scenes series/weekend-regular/cover.png Minji"
    exit 1
fi

CHARACTER_ID="$1"
SOURCE_BUCKET="$2"
SOURCE_PATH="$3"
CHARACTER_NAME="${4:-Character}"

# Configuration
SUPABASE_URL="https://lfwhdzwbikyzalpbwfnd.supabase.co"
DB_HOST="aws-1-ap-northeast-1.pooler.supabase.com"
DB_PASSWORD="42PJb25YJhJHJdkl"
DB_USER="postgres.lfwhdzwbikyzalpbwfnd"

# Get service role key from env or prompt
if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "SUPABASE_SERVICE_ROLE_KEY not set."
    echo "Get it from: https://supabase.com/dashboard/project/lfwhdzwbikyzalpbwfnd/settings/api"
    read -p "Enter service role key: " SUPABASE_SERVICE_ROLE_KEY
fi

# Generate UUIDs
KIT_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
ASSET_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
KIT_NAME="$CHARACTER_NAME Default"

echo "Creating avatar kit from storage..."
echo "  Character: $CHARACTER_NAME ($CHARACTER_ID)"
echo "  Source: $SOURCE_BUCKET/$SOURCE_PATH"
echo "  Kit ID: $KIT_ID"
echo "  Asset ID: $ASSET_ID"

# Create temp file
TEMP_FILE=$(mktemp /tmp/avatar_XXXXXX.png)
trap "rm -f $TEMP_FILE" EXIT

# Download from source bucket
echo ""
echo "Downloading from $SOURCE_BUCKET/$SOURCE_PATH..."
curl -s "$SUPABASE_URL/storage/v1/object/$SOURCE_BUCKET/$SOURCE_PATH" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -o "$TEMP_FILE"

# Check if download succeeded
if [ ! -s "$TEMP_FILE" ]; then
    echo "Error: Failed to download image from $SOURCE_BUCKET/$SOURCE_PATH"
    exit 1
fi

FILE_SIZE=$(wc -c < "$TEMP_FILE" | tr -d ' ')
echo "Downloaded: $FILE_SIZE bytes"

# Upload to avatars bucket
STORAGE_PATH="$KIT_ID/anchors/$ASSET_ID.png"
echo ""
echo "Uploading to avatars/$STORAGE_PATH..."
UPLOAD_RESULT=$(curl -s -X POST "$SUPABASE_URL/storage/v1/object/avatars/$STORAGE_PATH" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: image/png" \
  -H "x-upsert: true" \
  --data-binary "@$TEMP_FILE")

echo "Upload result: $UPLOAD_RESULT"

# Create avatar kit in database
echo ""
echo "Creating database records..."

PGPASSWORD="$DB_PASSWORD" psql "postgresql://$DB_USER@$DB_HOST:5432/postgres" <<EOF
-- Create avatar kit (9 columns = 9 values)
INSERT INTO avatar_kits (
    id,
    character_id,
    name,
    description,
    appearance_prompt,
    style_prompt,
    negative_prompt,
    status,
    is_default
) VALUES (
    '$KIT_ID'::uuid,
    '$CHARACTER_ID'::uuid,
    '$KIT_NAME',
    'Created from storage image',
    'Anime-style character portrait, consistent with series visual identity',
    'High-quality anime illustration, soft lighting, warm color palette',
    'Low quality, blurry, deformed, multiple people, text, watermark',
    'active',
    false
);

-- Create avatar asset (asset_type must be: portrait, fullbody, or scene)
INSERT INTO avatar_assets (
    id,
    avatar_kit_id,
    asset_type,
    storage_bucket,
    storage_path,
    source_type,
    is_canonical,
    mime_type
) VALUES (
    '$ASSET_ID'::uuid,
    '$KIT_ID'::uuid,
    'portrait',
    'avatars',
    '$STORAGE_PATH',
    'imported',
    true,
    'image/png'
);

-- Set as primary anchor
UPDATE avatar_kits
SET primary_anchor_id = '$ASSET_ID'::uuid
WHERE id = '$KIT_ID'::uuid;

-- Link to character
UPDATE characters
SET active_avatar_kit_id = '$KIT_ID'::uuid
WHERE id = '$CHARACTER_ID'::uuid;

-- Verify
SELECT 'Avatar Kit Created:' as status, ak.id as kit_id, ak.name, ak.status,
       c.name as character_name
FROM avatar_kits ak
JOIN characters c ON c.id = ak.character_id
WHERE ak.id = '$KIT_ID'::uuid;
EOF

echo ""
echo "============================================"
echo "SUCCESS!"
echo "============================================"
echo "Kit ID: $KIT_ID"
echo "Asset ID: $ASSET_ID"
echo "Storage: avatars/$STORAGE_PATH"
echo ""
echo "Verify at: GET /characters to see avatar_url"
echo "============================================"
