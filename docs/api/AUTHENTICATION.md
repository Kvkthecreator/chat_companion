# Authentication

> JWT-based authentication with Supabase

## Overview

Chat Companion uses Supabase Auth for authentication. All API endpoints (except health and webhooks) require a valid JWT token.

## Auth Flow

```
1. User signs in via Supabase Auth (web app)
   ↓
2. Supabase returns access_token (JWT)
   ↓
3. Frontend includes token in API requests:
   Authorization: Bearer <access_token>
   ↓
4. API validates JWT using SUPABASE_JWT_SECRET
   ↓
5. API extracts user_id from token claims
```

## Request Format

```bash
curl https://chat-companion-api.onrender.com/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## JWT Structure

```json
{
  "sub": "user-uuid",           // user_id
  "email": "user@example.com",
  "aud": "authenticated",
  "role": "authenticated",
  "exp": 1234567890,            // expiration
  "iat": 1234567800             // issued at
}
```

## Exempt Endpoints

These endpoints don't require authentication:

| Endpoint | Reason |
|----------|--------|
| `GET /health` | Health checks |
| `GET /health/db` | Health checks |
| `POST /telegram/webhook` | Telegram calls this |
| `POST /webhooks/lemonsqueezy` | Payment webhooks |

## Row-Level Security (RLS)

Supabase RLS ensures users can only access their own data:

```sql
-- Example: users can only read their own profile
CREATE POLICY users_own_data ON public.users
    FOR ALL USING (auth.uid() = id);
```

All tables have RLS policies. See [database/SCHEMA.md](../database/SCHEMA.md).

## Service Role Access

For backend operations that need to access all data (e.g., scheduler):

```python
# Use service role key (bypasses RLS)
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
}
```

**Never expose service role key to frontend.**

## Token Refresh

Supabase handles token refresh automatically. Access tokens expire after 1 hour.

Frontend should use `supabase.auth.getSession()` which auto-refreshes.

## Troubleshooting

### 401 Unauthorized

- Token expired → refresh or re-login
- Token malformed → check header format
- Wrong secret → verify `SUPABASE_JWT_SECRET`

### 403 Forbidden

- RLS policy blocking access
- User trying to access another user's data

## Environment Variables

```bash
SUPABASE_JWT_SECRET=your-jwt-secret    # From Supabase dashboard
SUPABASE_SERVICE_ROLE_KEY=your-key     # For backend service access
```
