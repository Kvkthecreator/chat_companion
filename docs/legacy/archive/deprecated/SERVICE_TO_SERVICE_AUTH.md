# Service-to-Service Authentication Guide

## Overview

This document describes the authentication patterns used for service-to-service (S2S) communication in the BFF (Backend-for-Frontend) architecture.

**Last Updated**: 2025-11-07
**Architecture**: Phase 6 - Project-First Onboarding

## Architecture Context

The platform uses a BFF pattern with clear domain separation:

- **work-platform**: Orchestration layer, user-facing APIs, project management
- **substrate-api**: Core domain service, handles baskets, blocks, documents, dumps

### Database Boundaries

**CRITICAL**: Services maintain separate databases and NEVER perform cross-database joins:
- `work-platform` DB: projects, work_sessions, workspace_memberships
- `substrate` DB: baskets, blocks, documents, raw_dumps

## Authentication Patterns

### Pattern 1: User-Initiated Requests (Frontend → BFF)

**Flow**: Browser → Next.js API Route → Substrate API

```typescript
// Next.js API Route: /app/api/baskets/[id]/route.ts
export async function GET(request: NextRequest, { params }) {
  const supabase = createRouteHandlerClient({ cookies });

  // 1. Authenticate user via Supabase session
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) {
    return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
  }

  // 2. Verify workspace access
  const workspace = await ensureWorkspaceServer(supabase);
  if (!workspace) {
    return NextResponse.json({ error: 'Workspace access required' }, { status: 403 });
  }

  // 3. Call substrate-api with service credentials
  const response = await fetch(`${SUBSTRATE_API_URL}/api/baskets/${basketId}`, {
    headers: {
      'Authorization': `Bearer ${SUBSTRATE_SERVICE_SECRET}`,
      'X-Service-Name': 'work-platform',
    },
  });

  // 4. Verify data belongs to user's workspace
  const data = await response.json();
  if (data.workspace_id !== workspace.id) {
    return NextResponse.json({ error: 'Access denied' }, { status: 403 });
  }

  return NextResponse.json(data);
}
```

**Key Points**:
- User auth happens at BFF layer using Supabase session
- Service auth happens at substrate-api call using service secret
- BFF enforces workspace isolation
- NO user credentials passed to substrate-api

### Pattern 2: Service-Initiated Requests (BFF → Substrate API)

**Flow**: work-platform API → Substrate API

```python
# work-platform/api/src/clients/substrate_client.py
class SubstrateClient:
    def __init__(self):
        self.base_url = settings.SUBSTRATE_API_URL
        self.service_secret = settings.SUBSTRATE_SERVICE_SECRET

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        headers = {
            "Authorization": f"Bearer {self.service_secret}",
            "X-Service-Name": "work-platform",
            "Content-Type": "application/json",
        }

        response = requests.request(
            method,
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    def create_basket(self, workspace_id: str, name: str, metadata: dict, user_id: str) -> dict:
        return self._request("POST", "/api/baskets", json={
            "workspace_id": workspace_id,
            "name": name,
            "metadata": metadata,
            "user_id": user_id,
        })
```

**Key Points**:
- Service secret used for all substrate-api calls
- No JWT verification at substrate-api level for service calls
- `X-Service-Name` header for audit trails
- Workspace context passed as parameters

### Pattern 3: Middleware Exemptions

Some substrate-api endpoints are exempt from JWT middleware but still require service auth:

```python
# substrate-api/api/src/app/middleware.py
JWT_EXEMPT_PATHS = [
    "/api/dumps/new",          # Service-to-service only
    "/api/baskets",            # Service-to-service creation
    # ... other exemptions
]
```

**IMPORTANT**: Middleware exemption ≠ No authentication
- Exempt endpoints bypass JWT middleware
- Still require service secret via `Authorization` header
- Use `Depends()` is bypassed, but auth still checked in endpoint logic

## Supabase Client Selection

### When to Use Admin Client

Use `supabase_admin_client` (service role key) for:
- ✅ Service-to-service operations
- ✅ Bypassing RLS policies
- ✅ Cross-workspace admin operations
- ✅ Background jobs and migrations

```python
from app.utils.supabase_client import supabase_admin_client

# Example: Creating dump from service
sb = supabase_admin_client()
basket = sb.table("baskets").select("*").eq("id", basket_id).single().execute()
```

### When to Use Regular Client

Use `supabase_client` (anon key) for:
- ✅ User-scoped queries with RLS
- ✅ Operations requiring user permissions
- ✅ Frontend API routes with user context

```python
from app.utils.supabase_client import supabase_client

# Example: User fetching their own data
sb = supabase_client()
projects = sb.table("projects").select("*").eq("user_id", user_id).execute()
```

## Common Issues and Solutions

### Issue 1: Permission Denied Errors

**Symptom**: `postgrest.exceptions.APIError: {'code': '42501'}`

**Cause**: Using `supabase_client` (anon key) for service operations

**Solution**: Switch to `supabase_admin_client` for service-to-service calls

```python
# ❌ WRONG - will fail with permission denied
from app.utils.supabase_client import supabase_client
sb = supabase_client()

# ✅ CORRECT - uses service role
from app.utils.supabase_client import supabase_admin_client
sb = supabase_admin_client()
```

### Issue 2: Middleware Blocking Service Calls

**Symptom**: 401 Unauthorized despite valid service secret

**Cause**: JWT middleware running before endpoint can check service auth

**Solution**: Add endpoint to `JWT_EXEMPT_PATHS` in middleware

```python
# substrate-api/api/src/app/middleware.py
JWT_EXEMPT_PATHS = [
    "/api/dumps/new",
    "/api/baskets",  # Add your endpoint
]
```

### Issue 3: Cross-Database Queries

**Symptom**: "Could not find column 'X' in schema cache" or cross-DB JOIN attempts

**Cause**: Attempting to join tables across work-platform DB and substrate DB

**Solution**: Use BFF pattern with HTTP calls

```python
# ❌ WRONG - cross-DB join
projects = supabase.table("projects").select("""
    *,
    baskets (name, status)  # baskets is in different DB!
""").execute()

# ✅ CORRECT - fetch separately via substrate client
projects = supabase.table("projects").select("*").execute()
for project in projects:
    basket = substrate_client.get_basket(project.basket_id)
```

### Issue 4: PostgREST Schema Cache Staleness

**Symptom**: Column exists in DB but PostgREST returns "not in schema cache"

**Cause**: PostgREST schema cache not reloaded after migration

**Solution**:
1. Reload schema cache: Supabase Dashboard → Settings → API → Reload schema cache
2. Verify with `scripts/validate_schema.sh`
3. Wait 30 seconds for cache propagation

## Environment Variables

### work-platform

```bash
# Service-to-service auth
SUBSTRATE_API_URL=http://localhost:8001
SUBSTRATE_SERVICE_SECRET=your-secret-here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### substrate-api

```bash
# Service auth
SUBSTRATE_SERVICE_SECRET=your-secret-here  # Must match work-platform

# Supabase (substrate DB)
SUPABASE_URL=https://your-substrate-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Testing Service-to-Service Calls

### Manual Testing with cURL

```bash
# Test substrate-api endpoint with service auth
curl -X POST http://localhost:8001/api/baskets \
  -H "Authorization: Bearer $SUBSTRATE_SERVICE_SECRET" \
  -H "X-Service-Name: work-platform" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "...",
    "name": "Test Basket",
    "user_id": "..."
  }'

# Test BFF endpoint with user session
curl -X GET http://localhost:3000/api/baskets/basket-id \
  -H "Cookie: sb-access-token=..." \
  -H "Cookie: sb-refresh-token=..."
```

### Automated Testing

```python
# pytest example for service-to-service
def test_create_basket_service_auth():
    headers = {
        "Authorization": f"Bearer {SUBSTRATE_SERVICE_SECRET}",
        "X-Service-Name": "work-platform",
    }
    response = client.post("/api/baskets", headers=headers, json={
        "workspace_id": str(workspace_id),
        "name": "Test Basket",
    })
    assert response.status_code == 201
```

## Security Best Practices

1. **Never expose service secrets to frontend**
   - Service secrets only in backend `.env` files
   - Use Supabase session for user auth

2. **Always verify workspace isolation**
   - Check `workspace_id` matches user's workspace
   - Enforce in BFF layer before calling substrate

3. **Use service role judiciously**
   - Only for legitimate service operations
   - Never for user-initiated queries that should respect RLS

4. **Audit service calls**
   - Log all service-to-service calls with `X-Service-Name`
   - Include `user_id` in service payloads for audit trails

5. **Validate all inputs**
   - UUIDs must be valid format
   - Use Pydantic/Zod for schema validation
   - Never trust service parameters blindly

## Debugging Checklist

When debugging service-to-service issues:

- [ ] Check service secret is set and matches between services
- [ ] Verify middleware exemptions for endpoint
- [ ] Confirm using `supabase_admin_client` not `supabase_client`
- [ ] Check endpoint is not attempting cross-DB queries
- [ ] Verify PostgREST schema cache is up to date
- [ ] Review logs for workspace mismatch errors
- [ ] Validate UUID formats in requests
- [ ] Ensure headers include `Authorization` and `X-Service-Name`

## References

- [Platform Canon v4.0](../docs/PLATFORM_CANON_V4.md)
- [Phase 6 Project Onboarding](../docs/PHASE_6_PROJECT_ONBOARDING.md)
- [BFF Architecture](../docs/BFF_ARCHITECTURE.md)
- [Database Schema Validation](../scripts/validate_schema.sh)

---

**Maintained by**: Platform Team
**Questions**: See #engineering-platform
