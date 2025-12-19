# Studio (Internal-Only)

## Access control
- Gated by Supabase auth **and** email allowlist.
- Allowlist env: `STUDIO_ALLOWED_EMAILS` (comma-separated). Default/fallback currently includes `kvkthecreator@gmail.com` to keep prod access for the requester.
- Middleware + `/studio` layout both enforce the allowlist; non-allowed users are redirected.

## Adding an internal user
1) Add their email to `STUDIO_ALLOWED_EMAILS` in your env (no spaces, comma-separated).
2) Deploy/restart so middleware and server components pick up the env change.

## Run/test locally
```bash
cd web
npm install
npm run dev
```
- Sign in via Supabase auth with an allowlisted email.
- Visit `/studio` (landing) → `/studio/create` (wizard v0).
- Submit button currently logs the draft JSON to the browser console (no persistence yet).

---

## Operational Model

There are two parallel paths for content operations:

### 1. Studio UI (User-Facing)
- **Path:** Web UI → API endpoints → Database
- **Auth:** JWT via Supabase
- **Use case:** Creating/editing content through the Studio interface
- **Endpoints:** `/studio/*`, `/series/*`, `/characters/*`

### 2. CLI Scripts (Dev/Ops)
- **Path:** Shell scripts → Direct DB + Storage access
- **Auth:** Supabase service role key + DB password
- **Use case:** Bulk operations, migrations, debugging, initial setup
- **Scripts:** `scripts/*.sh`

Both paths should achieve the same result and validate each other.

---

## Avatar Kit Scripts

### Create avatar kit from local image
```bash
# Upload a local image and create avatar kit
./scripts/setup_test_avatar.sh /path/to/image.png
```

### Create avatar kit from existing storage
```bash
# Copy image from one bucket to avatars and create kit
export SUPABASE_SERVICE_ROLE_KEY="..."
./scripts/create_avatar_from_storage.sh <character_id> <source_bucket> <source_path> [character_name]

# Example:
./scripts/create_avatar_from_storage.sh e60042ca-83c2-4861-b9f9-d24d73d4aa4d scenes series/weekend-regular/cover.png "Minji"
```

### Required environment
Scripts need:
- `SUPABASE_SERVICE_ROLE_KEY` - Get from Supabase dashboard → Settings → API
- Database credentials are hardcoded in scripts (pooler connection)

---

## Data Model Reference

### Avatar Kit Architecture
```
characters.active_avatar_kit_id  →  avatar_kits.id
avatar_kits.primary_anchor_id    →  avatar_assets.id
avatar_assets.storage_path       →  Supabase Storage (avatars bucket)
```

### Avatar Asset Types
- `portrait` - Primary anchor (shoulders up)
- `fullbody` - Full body reference
- `scene` - Scene-specific variant

### Series-Character Linking
- Series have `featured_characters: UUID[]` array
- Characters can belong to multiple series
- Series displayed on character detail pages
