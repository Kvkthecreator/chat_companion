# YARNNN Auth Canon v1.4.0 — Unified Authentication & Workspace Architecture

**The Single Source of Truth for Authentication, Authorization, and Workspace Management**

This document defines the canonical authentication and workspace architecture for YARNNN, consolidating frontend token handling and backend auth workflows.

## Token requirement

All calls to the FastAPI backend must include the Supabase access token in both the `sb-access-token` and `Authorization` headers. The helper `fetchWithToken` throws an error when the token is missing. Pages should redirect the user to `/login` when this occurs.

## Utilities

- **fetchWithToken** – wraps `fetch` and ensures the token is present.
- **apiGet/apiPost/apiPut** – thin wrappers that delegate to `fetchWithToken`.

## Handling failures

If `fetchWithToken` throws, the caller should assume the user is signed out. Redirect to `/login` or surface a message prompting them to reauthenticate.

## Backend requirements

All backend services must validate tokens by:
- Checking both `sb-access-token` and `Authorization` headers
- Using `AuthMiddleware` with proper exempt paths configuration
- Verifying JWT with raw secret (no base64 decoding)
- Returning 401 on invalid/missing tokens with optional debug info via `x-yarnnn-debug-auth: 1`

## Realtime (Canon‑Aligned Default)

- Default transport is polling; enable Realtime only with feature flags after verification.
- Flags:
  - `NEXT_PUBLIC_BASKET_EVENTS` (polling | websocket)
  - `NEXT_PUBLIC_ENABLE_WORK_STATUS_REALTIME` (false by default)
- Pitfall: ensure `NEXT_PUBLIC_SUPABASE_ANON_KEY` has no trailing newline (a `%0A` in the ws URL breaks handshake).
- Subscribe narrowly (basket/workspace) and auto‑fallback on `CHANNEL_ERROR`.

## Server-side routes

Next.js API routes must:
- Use `createRouteHandlerClient` for Supabase access
- Forward user tokens to backend services (both `sb-access-token` and `Authorization` headers)
- Never use service-role keys in client-facing routes
- Try headers first, then fall back to cookies for auth token extraction

## Workspace Client Helper (Minimal)

Client workspace helpers must only project canon fields:

```
select workspace_id, workspaces (id, name)
from workspace_memberships
where user_id = auth.uid()
```

Avoid depending on non‑canonical fields (e.g., `workspaces.slug`) to prevent schema drift. Server remains the authority via `ensureWorkspaceForUser()`.

## Python Backend Auth Stack

1. **Middleware**: `AuthMiddleware` validates all non-exempt routes
2. **JWT Verifier**: `verify_jwt()` supports both raw and base64-decoded secrets
3. **Environment Variables Required**:
   - `SUPABASE_URL`: Base URL without /auth/v1
   - `SUPABASE_JWT_SECRET`: Raw JWT secret from dashboard
   - `SUPABASE_JWT_AUD`: Default "authenticated"
   - `SUPABASE_SERVICE_ROLE_KEY`: For admin operations only

## Service Role Usage

Service role keys are used ONLY for:
- Workspace bootstrap operations (`get_or_create_workspace`)
- System-level operations that bypass RLS
- Never exposed to client code or used in user-facing endpoints

## RLS Summary
- **Memory tables**: workspace-scoped SELECT; service_role-only INSERT/UPDATE/DELETE
- `reflection_cache (optional, non-authoritative)`, `timeline_events`: read by workspace members, write by service_role only
- Standard pattern: users read via workspace membership, system writes via service_role

Reflections are derived from substrate. If persisted, they live in reflection_cache as a non-authoritative cache; readers may recompute on demand.

---

## 🏛️ Canonical Authentication & Workspace Architecture

### Core Principles

#### 1. Single Workspace per User
- On first authenticated touch, the system SHALL create a workspace and membership (owner) if none exists
- Every request is evaluated against the user's single authoritative workspace_id
- Strong guarantee: Every authenticated user belongs to exactly one workspace

#### 2. Pure Supabase Architecture
- Service-role keys are used for backend agent processing operations requiring elevated permissions
- Anon keys are used for user-scoped operations with RLS enforcement
- No DATABASE_URL dependency - single Supabase connection type for cleaner architecture
- Strong Auth: All backend requests are authenticated with verified Supabase JWTs

#### 3. RLS-First Security
- Sensitive access control is enforced by Postgres RLS tied to workspace_memberships
- Data Isolation: All workspace-scoped tables enforce access exclusively via RLS policies
- Even if an API route is misconfigured, Postgres still denies cross-workspace access

### Data Model (Authoritative Schema)

**workspaces**
- Columns: id (uuid PK), owner_id (uuid), name (text), is_demo (bool default false), timestamps

**workspace_memberships** 
- Columns: workspace_id (uuid), user_id (uuid), role (enum: owner|member), timestamps
- Constraint: (workspace_id, user_id) is UNIQUE

**Workspace-scoped tables**: baskets, raw_dumps, context_blocks, documents, context_items
- Each SHALL include workspace_id (uuid NOT NULL) and be protected by RLS referencing workspace_memberships

**Baskets timestamp semantics**
- `baskets` does NOT have `updated_at`
- "Last activity" MUST be derived from `timeline_events.max(ts)`; fallback to `baskets.created_at`

### Authentication & Token Handling

**Frontend Requirements**
- SHALL use `supabase.auth.getUser()` in the client for UI state only
- Server actions/route handlers SHALL obtain verified user via helper (e.g., `getAuthenticatedUser()`)
- All data mutations go through server actions or API routes with proper auth

**Backend Requirements**
- SHALL verify Supabase JWTs by validating signature, issuer, audience, and exp using Supabase JWKS
- user_id is taken from the token's sub claim after verification
- Transport: Authorization: Bearer <jwt> (preferred) or sb-access-token header

### Workspace Resolution Contract

**Single authoritative function SHALL exist server-side:**

```python
# Python implementation in api/src/app/utils/workspace.py
def get_or_create_workspace(user_id: str) -> str:
    """Returns workspace_id, creating if necessary using admin client"""
```

**Rules:**
- Uses `supabase_admin()` client (service role) to bypass RLS for bootstrap operations
- If workspace exists with owner_id=user_id → return its id
- If none exists → create workspace row (owner = user), name = "{user_id[:6]}'s workspace" → return id
- Returns only the single authoritative workspace_id
- This function is the only place allowed to create default workspaces
- MUST validate user_id is a valid UUID before proceeding

### RBAC (Role-Based Access Control)

**Roles:** owner, member

**Privileges:**
- Owner: all member actions plus elevated actions (delete workspace, transfer ownership)
- Member: standard operations excluding destructive global actions

**Enforcement:**
- API layer: route-level guards call shared requireRole(workspaceId, userId, roleOrHigher) utility
- DB layer: RLS policies consider membership and role for reads/writes where applicable

### RLS (Row-Level Security) Policy Canon

**Read Policy:** 
```sql
EXISTS (SELECT 1 FROM workspace_memberships m 
        WHERE m.user_id = auth.uid() AND m.workspace_id = row.workspace_id)
```

**Write/Update/Delete Policy:**
- Same membership predicate
- Additional role predicates where applicable (destructive ops require role = 'owner')
- All workspace-scoped tables SHALL implement these predicates

### Backend (FastAPI) Workflow

1. **JWT Verification**
   - `AuthMiddleware` extracts token from headers (Authorization or sb-access-token)
   - `verify_jwt()` validates with raw JWT secret from env
   - Derives user_id from token's sub claim

2. **Workspace Resolution**
   - Call `get_or_create_workspace(user_id)` → workspace_id
   - Uses admin client for bootstrap operations only

3. **Database Operations**
   - Workspace bootstrap: Use `supabase_admin()` (service role)
   - User data operations: Use `supabase_admin()` for now (until user-scoped client implemented)
   - All inserts MUST include workspace_id
   - Generate UUIDs client-side when needed (e.g., basket_id)

4. **Error Handling**
   - Return debug info when `x-yarnnn-debug-auth: 1` header present
   - Wrap exceptions in try/catch with proper logging
   - Use HTTPException for standard error responses

### Next.js (App Router) Implementation

**Server Components**
- SHALL use `createServerComponentClient({ cookies })` for database operations
- SHALL call server helper: `getAuthenticatedUser()` → verified `userId`
- SHALL resolve active workspace via RLS or `ensureWorkspaceForUser(userId)`

**API Route Handlers**
```typescript
import { createRouteHandlerClient } from '@/lib/supabase/clients'
import { cookies } from 'next/headers'

export async function POST(req: Request) {
  const supabase = createRouteHandlerClient({ cookies })
  
  // Auth check
  const { data, error } = await supabase.auth.getUser()
  if (error || !data?.user) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }
  
  // Workspace resolution  
  const { id: workspaceId } = await ensureWorkspaceForUser(data.user.id, supabase)
  // ... rest of implementation
}
```

**Middleware**
- SHALL NOT perform authentication or RBAC decisions
- MAY normalize host names and canonicalize `/baskets/:id/*` paths

**Client Components**
- Access session via supabase.auth.getUser() for UI state only
- All data mutations go through server actions or API routes

### API Contract Examples

**Create Basket**
```
POST /api/baskets/new
Authorization: Bearer <jwt>
Body: { "idempotency_key": "<uuid>", "intent": "optional", "raw_dump": "optional", "notes": "optional" }
```

**Resolve Basket (single-basket world)**
```
GET /api/baskets/resolve
Authorization: Bearer <jwt>
Returns: { "id": "<uuid>" }
```

**Create Raw Dump**
```
POST /api/dumps/new
Authorization: Bearer <jwt>
Body: { "dump_request_id": "<uuid>", "text_dump": "...", "file_url": "..." }
```

### Error Semantics

- **401**: Missing/invalid JWT
- **403**: Authenticated but not authorized (membership/role)
- **409**: Idempotency/workspace uniqueness conflicts
- **422**: Schema/validation failures

Error format: `{ "error": { "code": "FORBIDDEN", "message": "Owner role required." } }`

### Capture Policy (P0) — Canon Defaults

P0 capture (raw dumps) is always direct insert. Governance applies to substrate evolution (P1+), not to raw dump creation.

- Default route for `entry_point=onboarding_dump`: `direct`
- Side-effects: database triggers enqueue work for P1/P2/P3, but API success is not gated by downstream processing
- Rationale: users need immediate acknowledgement of capture; intelligence arrives asynchronously

### Threat Model

- **Token forgery**: mitigated by JWKS signature verification
- **Cross-tenant data leakage**: mitigated by RLS + workspace_id checks  
- **Privilege escalation**: mitigated by RBAC checks at API + RLS role predicates

### Compliance Checklist (MUST pass)

- [ ] JWT signature verified on every protected route
- [ ] Single authoritative workspace resolver in server code
- [ ] User-scoped DB client used for all user CRUD
- [ ] RLS enabled on all workspace tables
- [ ] RBAC enforced at API layer for elevated actions
- [ ] All rows carry correct workspace_id
- [ ] Logs include user_id + workspace_id
- [ ] Middleware does not perform authentication decisions
- [ ] No code selects or orders by `baskets.updated_at`

---

## MCP OAuth Integration

### Overview
MCP servers (Claude.ai remote connectors) use OAuth 2.1 with Dynamic Client Registration to access YARNNN workspaces.

### Authentication Flow
1. **Discovery**: Claude fetches OAuth metadata from `/.well-known/oauth-authorization-server`
2. **Dynamic Registration**: Claude registers via `POST /oauth/register` (RFC 7591)
3. **Authorization**: User redirected to `/mcp/authorize` → YARNNN login → consent page
4. **Token Exchange**: Claude exchanges authorization code for 90-day access token
5. **MCP Connection**: Claude uses Bearer token for all MCP requests

### Key Components

**MCP Server** (`mcp-server/adapters/anthropic/src/oauth.ts`):
- Issues 90-day access tokens (auto-renew within 7 days of expiry)
- Stores token mappings in `mcp_oauth_sessions` table
- Validates tokens against backend `/api/mcp/auth/sessions/validate`

**Web App** (`web/app/mcp/authorize/page.tsx`):
- Ensures user authenticated via Supabase (uses centralized `createBrowserClient()`)
- Shows consent UI with workspace context
- Redirects to MCP server callback with Supabase token

**Backend** (`api/src/app/routes/mcp_auth.py`):
- Stores MCP token → Supabase token + workspace mappings
- Auto-renews tokens within 7 days of expiry (rolling 90-day window)
- Validates tokens on every MCP request

### Critical Implementation Details

1. **Session Cookies**: MCP authorize page MUST use `createBrowserClient()` from `@/lib/supabase/clients` (not direct `@supabase/ssr`) to properly read session cookies after OAuth redirect

2. **Return URL Handling**: Login page stores `returnUrl` query param in `localStorage` before OAuth, auth callback reads it to redirect back to MCP authorize page

3. **Token Longevity**: 90-day expiration with auto-renewal for active connections; inactive tokens expire after 90 days

4. **Workspace Scoping**: All MCP tokens are scoped to user's canonical workspace via `mcp_oauth_sessions.workspace_id`

### Security Model
- MCP tokens are workspace-scoped via RLS on `mcp_oauth_sessions`
- Underlying Supabase tokens enforce RLS on all data access
- Token validation updates `last_used_at` for audit trail
- Tokens can be revoked via `DELETE /api/mcp/auth/sessions/{token}`
