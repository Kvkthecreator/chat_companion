# Substrate API Authentication Fix - FINAL Solution - November 21, 2025

## Problem Summary

**Error**: Work-platform → substrate-API calls failing with 401 Unauthorized
```
DEBUG: Substrate API GET https://yarnnn-substrate-api.onrender.com/baskets/.../blocks: 401
ERROR: Substrate API error: HTTP 401 error
ERROR: Circuit breaker: Opening circuit after 5 failures
```

## Root Cause Discovery

**Key Insight from /context Page** (working correctly):
- Frontend Next.js API route `/api/projects/[id]/context/route.ts` calls substrate-API successfully
- Uses **user JWT token** from Supabase session: `session.access_token`
- substrate-API accepts JWT tokens for user authentication
- Lines 242-244 (POST) and 259 (POST JSON):
  ```typescript
  headers: {
    'Authorization': `Bearer ${token}`,  // USER JWT!
  }
  ```

**The Bug in TP Backend**:
- [substrate_client.py:189](../../work-platform/api/src/clients/substrate_client.py#L189) sends:
  ```python
  "Authorization": f"Bearer {self.service_secret}",  # ❌ WRONG
  ```
- `SUBSTRATE_SERVICE_SECRET` is an arbitrary env var, NOT a valid auth mechanism
- substrate-API auth middleware tries to verify as:
  1. Supabase JWT → fails (not a JWT)
  2. Integration token → fails (hash doesn't exist in database)
- Result: 401 Unauthorized

## Solution Architecture

### Pattern: User JWT Pass-Through

```
Frontend (Supabase session)
  ↓ access_token (JWT)
work-platform-API (/api/tp/chat endpoint)
  ↓ verify_jwt() extracts user info
  ↓ passes JWT to ThinkingPartnerAgentSDK
  ↓ passes JWT to SubstrateMemoryAdapter
  ↓ passes JWT to SubstrateClient
  ↓ Authorization: Bearer <JWT>
substrate-API (AuthMiddleware)
  ✅ verifies JWT successfully
```

### Why This Works

1. **Frontend has user JWT** - from Supabase authentication
2. **work-platform receives JWT** - via Authorization header
3. **JWT is valid for substrate-API** - both use same Supabase instance
4. **No new tokens needed** - reuse existing user authentication

## Implementation

### Step 1: Update SubstrateClient to Accept User Token

**File**: [substrate_client.py](../../work-platform/api/src/clients/substrate_client.py)

**Changes**:
```python
class SubstrateClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        service_secret: Optional[str] = None,  # DEPRECATED
        user_token: Optional[str] = None,  # NEW: User JWT token
        timeout: float = 30.0,
    ):
        self.base_url = base_url or os.getenv(
            "SUBSTRATE_API_URL", "http://localhost:10000"
        )
        # Prefer user_token over service_secret
        self.auth_token = user_token or service_secret or os.getenv("SUBSTRATE_SERVICE_SECRET")
        self.timeout = timeout

        if not self.auth_token:
            logger.warning(
                "No auth token provided - substrate auth will fail"
            )

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.auth_token}",  # ✅ Can be JWT or integration token
            "X-Service-Name": "platform-api",
            "Content-Type": "application/json",
        }
```

**Backward Compatibility**:
- `service_secret` parameter still exists but deprecated
- Falls back to env var if neither token provided
- No breaking changes for existing code

### Step 2: Update SubstrateMemoryAdapter to Accept User Token

**File**: [memory_adapter.py](../../work-platform/api/src/adapters/memory_adapter.py)

**Changes**:
```python
class SubstrateMemoryAdapter(MemoryProvider):
    def __init__(
        self,
        basket_id: str | UUID,
        workspace_id: str,
        user_token: Optional[str] = None,  # NEW: User JWT token
        agent_type: Optional[str] = None,
        project_id: Optional[str] = None,
        work_ticket_id: Optional[str] = None
    ):
        self.basket_id = str(basket_id)
        self.workspace_id = workspace_id
        self.user_token = user_token
        self.agent_type = agent_type
        self.project_id = project_id
        self.work_ticket_id = work_ticket_id

        # Create client with user token
        from clients.substrate_client import SubstrateClient
        self.client = SubstrateClient(user_token=user_token) if user_token else get_substrate_client()
```

### Step 3: Update ThinkingPartnerAgentSDK to Pass User Token

**File**: [thinking_partner_sdk.py](../../work-platform/api/src/agents_sdk/thinking_partner_sdk.py)

**Changes**:
```python
class ThinkingPartnerAgentSDK:
    def __init__(
        self,
        basket_id: str,
        workspace_id: str,
        user_id: str,
        user_token: Optional[str] = None,  # NEW: User JWT token
        ...
    ):
        self.basket_id = basket_id
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.user_token = user_token

        # Initialize memory with user token
        self.memory = SubstrateMemoryAdapter(
            basket_id=basket_id,
            workspace_id=workspace_id,
            user_token=user_token,  # ✅ Pass through
            agent_type="thinking_partner",
        )
```

### Step 4: Update TP Route to Extract and Pass JWT

**File**: [thinking_partner.py](../../work-platform/api/src/app/routes/thinking_partner.py)

**Changes**:
```python
@router.post("/chat", response_model=TPChatResponse)
async def tp_chat(
    request: TPChatRequest,
    user: dict = Depends(verify_jwt)
):
    user_id = user.get("sub") or user.get("user_id")

    # NEW: Extract JWT from request context
    # The verify_jwt dependency should store the raw token
    user_token = user.get("token")  # Assuming verify_jwt adds this

    # Alternative: Get from request headers directly
    # from fastapi import Request
    # auth_header = request.headers.get("authorization", "")
    # user_token = auth_header.split(" ", 1)[1] if auth_header.lower().startswith("bearer ") else None

    # Create TP with user token
    tp = create_thinking_partner_sdk(
        basket_id=request.basket_id,
        workspace_id=workspace_id,
        user_id=user_id,
        user_token=user_token  # ✅ Pass JWT
    )
```

### Step 5: Update verify_jwt to Include Raw Token

**File**: [app/utils/jwt.py](../../work-platform/api/src/app/utils/jwt.py)

**Changes**:
```python
def verify_jwt(request: Request) -> dict[str, str]:
    """Return the caller's user ID, set by AuthMiddleware."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Extract raw token from header
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split(" ", 1)[1] if auth_header.lower().startswith("bearer ") else None

    return {
        "user_id": str(user_id),
        "token": token  # NEW: Include raw JWT for pass-through
    }
```

## Benefits

1. ✅ **No New Tokens Required** - reuses existing user JWT
2. ✅ **Proper Authentication** - substrate-API verifies JWT successfully
3. ✅ **User Context Preserved** - JWT contains user_id for RLS
4. ✅ **Minimal Code Changes** - just thread token through existing chain
5. ✅ **Backward Compatible** - service_secret fallback still works
6. ✅ **No Env Var Changes** - works immediately after code deployment

## Testing Checklist

After deployment:

- [ ] TP chat completes without hanging
- [ ] Render logs show 200 OK for substrate-API calls
- [ ] No 401 errors in logs
- [ ] Circuit breaker stays closed
- [ ] Memory context loads successfully
- [ ] Backend stability improves

## Rollback Plan

If issues occur:
1. Revert code changes
2. System falls back to `SUBSTRATE_SERVICE_SECRET` (fails gracefully)
3. Circuit breaker protects from cascading failures

## Comparison with Previous Approach

**Previous Attempt**: Create integration token
- ❌ Requires manual token creation
- ❌ Requires updating Render env vars
- ❌ Additional admin overhead
- ✅ Would work (integration tokens are valid)

**Current Approach**: Pass user JWT through
- ✅ No manual steps required
- ✅ No env var changes needed
- ✅ Uses existing authentication
- ✅ Simpler architecture
- ✅ **Matches what /context page does** (proven working pattern)

## Related Files

- [substrate_client.py:186-192](../../work-platform/api/src/clients/substrate_client.py#L186-L192) - Auth header logic
- [memory_adapter.py:55-78](../../work-platform/api/src/adapters/memory_adapter.py#L55-L78) - Client initialization
- [thinking_partner_sdk.py](../../work-platform/api/src/agents_sdk/thinking_partner_sdk.py) - TP initialization
- [thinking_partner.py:134-224](../../work-platform/api/src/app/routes/thinking_partner.py#L134-L224) - TP endpoint
- [/context/route.ts:242-244](../../work-platform/web/app/api/projects/[id]/context/route.ts#L242-L244) - Working reference

---

**Status**: READY TO IMPLEMENT

**Estimated Time**: 30 minutes (5 file changes + testing)

**Risk**: Low (backward compatible, proven pattern from /context page)
