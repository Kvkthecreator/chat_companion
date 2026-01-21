# Database Setup Guide

## Supabase Project Details

**Project Reference**: `gncuzrstnmwhghzoyllo`
**Region**: `ap-northeast-1` (Tokyo)

## Quick Access (Copy-Paste Ready)

### psql Command Line (Recommended)

```bash
# Working connection string with URL-encoded password
psql "postgresql://postgres.gncuzrstnmwhghzoyllo:companion%21%21%40%40%23%23%24%24@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
```

**Important**: The password must be URL-encoded in the connection string. Don't use PGPASSWORD env var with special characters.

### Password Reference

- **Raw password**: `companion!!@@##$$`
- **URL-encoded**: `companion%21%21%40%40%23%23%24%24`

## Connection String Formats

### Transaction Pooler (Port 6543) - For Serverless/API
```
postgresql://postgres.gncuzrstnmwhghzoyllo:companion%21%21%40%40%23%23%24%24@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true
```

### Session Pooler (Port 5432) - For Long-Lived Connections
```
postgresql://postgres.gncuzrstnmwhghzoyllo:companion%21%21%40%40%23%23%24%24@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres
```

## Environment Variables

For Render API deployment:
```bash
DATABASE_URL=postgresql://postgres.gncuzrstnmwhghzoyllo:companion%21%21%40%40%23%23%24%24@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true
SUPABASE_URL=https://gncuzrstnmwhghzoyllo.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<from Supabase Dashboard > Settings > API>
SUPABASE_JWT_SECRET=<from Supabase Dashboard > Settings > API > JWT Secret>
```

## Running Migrations via psql

### Example: Run SQL File
```bash
psql "postgresql://postgres.gncuzrstnmwhghzoyllo:companion%21%21%40%40%23%23%24%24@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require" -f migration.sql
```

### Example: Run Inline SQL
```bash
psql "postgresql://postgres.gncuzrstnmwhghzoyllo:companion%21%21%40%40%23%23%24%24@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require" -c "SELECT * FROM users LIMIT 5;"
```

### Example: Run Multi-Statement SQL via Heredoc
```bash
psql "postgresql://postgres.gncuzrstnmwhghzoyllo:companion%21%21%40%40%23%23%24%24@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require" << 'EOF'
CREATE TABLE IF NOT EXISTS my_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT
);
SELECT 'Done' as status;
EOF
```

### Verify Tables
```bash
psql "postgresql://postgres.gncuzrstnmwhghzoyllo:companion%21%21%40%40%23%23%24%24@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require" -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
```

## Password Encoding Reference

| Character | Encoded |
|-----------|---------|
| `!` | `%21` |
| `@` | `%40` |
| `#` | `%23` |
| `$` | `%24` |
| `%` | `%25` |
| `&` | `%26` |

Example: `companion!!@@##$$` → `companion%21%21%40%40%23%23%24%24`

## Other Access Methods

### Supabase Dashboard (SQL Editor)

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Select project `gncuzrstnmwhghzoyllo`
3. Navigate to **SQL Editor** in the left sidebar
4. Write and execute SQL queries directly

### GUI Tools (TablePlus, DBeaver, pgAdmin)

- **Host**: `aws-1-ap-northeast-1.pooler.supabase.com`
- **Port**: `6543` (transaction pooler) or `5432` (session pooler)
- **Database**: `postgres`
- **User**: `postgres.gncuzrstnmwhghzoyllo`
- **Password**: `companion!!@@##$$`
- **SSL**: Required

## Troubleshooting

### "password authentication failed"
- PGPASSWORD env var doesn't work well with special characters
- Use the URL-encoded password directly in the connection string instead

### "Tenant or user not found"
- Verify the region is correct (`aws-1` for CLI access from local machine)
- For Render deployment, try `aws-0` if `aws-1` doesn't work

### "Network is unreachable"
- Use pooler connection, not direct connection
- Direct connections may be blocked by firewall

### Connection Timeout
- Add `?sslmode=require` to connection string
- Try session pooler (port 5432) instead of transaction pooler (6543)
