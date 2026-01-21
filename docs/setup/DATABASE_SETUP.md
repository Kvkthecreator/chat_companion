# Database Setup Guide

## Supabase Project Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your project reference (e.g., `gncuzrstnmwhghzoyllo`)
3. Set a database password (avoid special characters for simplicity)

### 2. Connection Strings

Supabase provides several connection options:

#### Transaction Pooler (Recommended for serverless)
```
postgresql://postgres.[project-ref]:[password]@aws-[region].pooler.supabase.com:6543/postgres?pgbouncer=true
```

#### Session Pooler (For long-lived connections)
```
postgresql://postgres.[project-ref]:[password]@aws-[region].pooler.supabase.com:5432/postgres
```

#### Direct Connection (For migrations only)
```
postgresql://postgres.[project-ref]:[password]@aws-[region].pooler.supabase.com:5432/postgres
```

### 3. Environment Variables

Set these in your deployment platform (Render, Vercel, etc.):

```bash
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # From Supabase Dashboard > Settings > API
SUPABASE_JWT_SECRET=...           # From Supabase Dashboard > Settings > API > JWT Secret
```

### 4. Password Encoding

If your password contains special characters, URL-encode them:

| Character | Encoded |
|-----------|---------|
| `!` | `%21` |
| `@` | `%40` |
| `#` | `%23` |
| `$` | `%24` |
| `%` | `%25` |
| `&` | `%26` |

Example: `pass!word` → `pass%21word`

## Accessing Supabase Database Directly

### Option 1: Supabase Dashboard (SQL Editor)

1. Go to your Supabase Dashboard
2. Navigate to **SQL Editor** in the left sidebar
3. Write and execute SQL queries directly

### Option 2: psql Command Line

```bash
# Using the pooler connection
psql "postgresql://postgres.[project-ref]:[password]@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"

# Example
psql "postgresql://postgres.gncuzrstnmwhghzoyllo:YourPassword@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
```

### Option 3: GUI Tools (TablePlus, DBeaver, pgAdmin)

Use the connection string components:
- **Host**: `aws-1-ap-northeast-1.pooler.supabase.com`
- **Port**: `6543` (pooler) or `5432` (direct)
- **Database**: `postgres`
- **User**: `postgres.[project-ref]`
- **Password**: Your database password
- **SSL**: Required

### Option 4: Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Link to your project
supabase link --project-ref [project-ref]

# Access database
supabase db remote commit
```

## Running Migrations

### Initial Schema Setup

Run the companion app schema in Supabase SQL Editor:

```sql
-- See /docs/setup/SCHEMA.md for full schema
```

### Checking Tables Exist

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
```

## Troubleshooting

### "Tenant or user not found"
- Check the project reference is correct
- Verify password is correct (try resetting it)
- Use the correct pooler host (check `aws-0` vs `aws-1` in your region)

### "Network is unreachable"
- Direct connections may be blocked; use the pooler instead
- Check your deployment platform allows outbound connections

### Connection Timeout
- Ensure SSL is enabled
- Try the session pooler (port 5432) instead of transaction pooler (6543)
