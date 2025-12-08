# Phase 6: Basket-First Work Request Scaffolding

**Date**: 2025-01-16
**Status**: Planning
**Scope**: work-platform ↔ substrate-api relational layer ONLY

---

## Problem Statement

**Current Flow** (Agent-First):
```
User → POST /api/agents/run
       ↓
       requires basket_id (user must create basket manually)
       ↓
       agent_work_request created
       ↓
       agent executes with existing basket
```

**Issues**:
- User must manually create basket before calling agent
- No automatic scaffolding of substrate infrastructure
- Basket ↔ Agent relationship unclear
- raw_dump not created automatically
- Agent can't infer "which basket?" for new requests

**Desired Flow** (Basket-First):
```
User → POST /api/work-requests/new
       ↓
       Step 1: Create basket (substrate-api)
       Step 2: Create raw_dump (substrate-api)
       Step 3: [FUTURE] Agent scaffolding decision point
       Step 4: Create agent_work_request (work-platform)
       ↓
       Return work_request_id + basket_id to user
```

---

## Core Principle

**Baskets are shared context, agents are workers.**

- Basket = persistent knowledge container (owned by substrate-api)
- Agent = ephemeral worker that operates ON a basket (owned by work-platform)
- raw_dump = input artifacts that seed basket knowledge (owned by substrate-api)
- agent_work_request = trial/subscription-gated execution record (owned by work-platform)

---

## Architecture Constraints

### Phase 3 BFF Compliance (MUST MAINTAIN)
```
work-platform (BFF Layer)
  ├── Direct DB: agent_work_requests, user_agent_subscriptions, agent_catalog
  ├── HTTP to substrate-api: baskets, raw_dumps, blocks, documents, relationships
  └── Never direct DB access to substrate tables
```

### Current Table Ownership
| Table | Owner | Access Pattern |
|-------|-------|----------------|
| `baskets` | substrate-api | HTTP via substrate_client |
| `raw_dumps` | substrate-api | HTTP via substrate_client |
| `blocks` | substrate-api | HTTP via substrate_client |
| `documents` | substrate-api | HTTP via substrate_client |
| `agent_work_requests` | work-platform | Direct DB (supabase_client) |
| `user_agent_subscriptions` | work-platform | Direct DB (supabase_client) |
| `agent_catalog` | work-platform | Direct DB (supabase_client) |

---

## Phase 6 Scope: Bounded Refactoring

### IN SCOPE (Relational Scaffolding)

1. **New Endpoint**: `POST /api/work-requests/new`
   - Location: `work-platform/api/src/app/routes/work_requests.py` (new file)
   - Orchestrates basket creation, raw_dump creation, work_request creation
   - Returns: `{work_request_id, basket_id, basket_name, status}`

2. **substrate_client Extensions** (3 new methods)
   - `create_basket(workspace_id, name, metadata)` → calls `POST /api/baskets`
   - `create_raw_dump(basket_id, content, metadata)` → calls `POST /api/dumps/new`
   - `get_basket_info(basket_id)` → calls `GET /api/baskets/{basket_id}`

3. **Request Flow Orchestration**
   ```python
   # work-platform/api/src/services/work_request_scaffolder.py (new file)

   async def scaffold_new_work_request(
       user_id: str,
       workspace_id: str,
       agent_type: str,
       initial_context: str,  # raw text input
       basket_name: Optional[str] = None,
       metadata: Optional[dict] = None
   ) -> dict:
       """
       Orchestrate basket-first work request creation.

       Steps:
       1. Check permissions (Phase 5 trial/subscription)
       2. Create basket via substrate_client (substrate-api)
       3. Create raw_dump via substrate_client (substrate-api)
       4. Create agent_work_request (work-platform DB)
       5. Return orchestration result
       """
   ```

4. **Database Schema Changes** (NONE - use existing tables)
   - No new tables
   - No new columns
   - Just orchestration of existing infrastructure

5. **Documentation**
   - API docs for new endpoint
   - Sequence diagrams for basket-first flow
   - Update PHASE4_IMPLEMENTATION_SUMMARY.md with Phase 6 addendum

### OUT OF SCOPE (Deferred to Future Phases)

1. **Agent Execution Logic**
   - Agent chat/conversation interface
   - Agent lifecycle management
   - Agent governance workflow
   - These remain in existing `POST /api/agents/run` endpoint

2. **Agent Scaffolding Decision**
   - "Should this basket get auto-scaffolded with agent context?"
   - Manual vs automatic agent initialization
   - Agent template selection
   - Deferred until we understand usage patterns

3. **Basket Inference for Existing Work Requests**
   - "User already has 3 baskets, which one should agent use?"
   - Smart basket routing/selection
   - Multi-basket scenarios
   - Deferred - for now user explicitly creates new work-request → new basket

4. **3rd Party Integration Basket Mapping**
   - MCP/OpenAI Apps auto-basket-assignment
   - Webhook-triggered basket creation
   - Similar to substrate-api's existing unassigned_queue logic
   - Deferred - different problem domain

---

## Detailed Implementation Plan

### Step 1: Extend substrate_client.py (Phase 3 BFF)

**File**: `work-platform/api/src/clients/substrate_client.py`

Add 3 new methods to `SubstrateClient` class:

```python
def create_basket(
    self,
    workspace_id: UUID | str,
    name: str,
    metadata: Optional[dict] = None,
    user_id: Optional[UUID | str] = None
) -> dict:
    """
    Create new basket in substrate-api.

    Args:
        workspace_id: Workspace UUID
        name: Basket name
        metadata: Optional metadata (tags, origin_template, etc.)
        user_id: Optional user ID for ownership

    Returns:
        {"basket_id": "...", "name": "...", "workspace_id": "...", ...}
    """
    request_body = {
        "workspace_id": str(workspace_id),
        "name": name,
        "metadata": metadata or {}
    }
    if user_id:
        request_body["user_id"] = str(user_id)

    return self._request("POST", "/api/baskets", json=request_body)


def get_basket_info(self, basket_id: UUID | str) -> dict:
    """
    Get basket information.

    Args:
        basket_id: Basket UUID

    Returns:
        Basket details
    """
    return self._request("GET", f"/api/baskets/{basket_id}")
```

**Note**: `create_dump()` already exists (line 451-473), so no changes needed.

---

### Step 2: Create Work Request Scaffolder Service

**File**: `work-platform/api/src/services/work_request_scaffolder.py` (NEW)

```python
"""
Work Request Scaffolder - Phase 6: Basket-First Orchestration

Orchestrates creation of:
1. Basket (substrate-api via substrate_client)
2. Raw dump (substrate-api via substrate_client)
3. Agent work request (work-platform via supabase_client)

Maintains Phase 3 BFF architecture compliance.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from app.utils.supabase_client import supabase_client
from clients.substrate_client import get_substrate_client
from utils.permissions import (
    check_agent_work_request_allowed,
    record_work_request,
    PermissionDeniedError,
)
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class ScaffoldingError(Exception):
    """Raised when scaffolding fails."""

    def __init__(
        self,
        message: str,
        step: str,
        details: Optional[dict] = None,
        basket_id: Optional[str] = None,
        dump_id: Optional[str] = None
    ):
        self.message = message
        self.step = step  # "create_basket", "create_dump", "create_work_request"
        self.details = details or {}
        self.basket_id = basket_id
        self.dump_id = dump_id
        super().__init__(message)


async def scaffold_new_work_request(
    user_id: str,
    workspace_id: str,
    agent_type: str,
    initial_context: str,
    work_mode: str = "general",
    basket_name: Optional[str] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Scaffold new work request with basket-first approach.

    Phase 6: Creates basket + raw_dump (substrate-api) + work_request (work-platform).

    Args:
        user_id: User ID from JWT
        workspace_id: Workspace ID for context
        agent_type: Agent type ('research', 'content', 'reporting')
        initial_context: Raw text input to seed basket
        work_mode: Work mode (default: "general")
        basket_name: Optional basket name (auto-generated if not provided)
        metadata: Optional metadata for basket

    Returns:
        {
            "work_request_id": "...",
            "basket_id": "...",
            "basket_name": "...",
            "dump_id": "...",
            "status": "scaffolded",
            "is_trial_request": true/false,
            "remaining_trials": 7
        }

    Raises:
        PermissionDeniedError: If trial exhausted and not subscribed
        ScaffoldingError: If scaffolding fails at any step
        HTTPException: If validation fails
    """
    logger.info(
        f"Scaffolding work request: user={user_id}, agent={agent_type}, "
        f"workspace={workspace_id}"
    )

    basket_id = None
    dump_id = None
    work_request_id = None

    try:
        # ================================================================
        # Step 1: Check Permissions (Phase 5 trial/subscription logic)
        # ================================================================
        try:
            permission_info = await check_agent_work_request_allowed(
                user_id=user_id,
                workspace_id=workspace_id,
                agent_type=agent_type
            )
        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            raise

        # ================================================================
        # Step 2: Create Basket (substrate-api via HTTP)
        # ================================================================
        substrate_client = get_substrate_client()

        # Auto-generate basket name if not provided
        if not basket_name:
            basket_name = f"{agent_type.capitalize()} Work - {user_id[:8]}"

        basket_metadata = metadata or {}
        basket_metadata["agent_type"] = agent_type
        basket_metadata["created_via"] = "work_request_scaffolder"

        try:
            basket_response = substrate_client.create_basket(
                workspace_id=workspace_id,
                name=basket_name,
                metadata=basket_metadata,
                user_id=user_id
            )
            basket_id = basket_response["basket_id"]
            logger.info(f"Created basket {basket_id} via substrate-api")

        except Exception as e:
            logger.error(f"Failed to create basket: {e}")
            raise ScaffoldingError(
                message=f"Failed to create basket: {str(e)}",
                step="create_basket",
                details={"error": str(e)}
            )

        # ================================================================
        # Step 3: Create Raw Dump (substrate-api via HTTP)
        # ================================================================
        dump_metadata = {
            "source": "work_request_scaffolder",
            "agent_type": agent_type,
            "work_mode": work_mode
        }

        try:
            dump_response = substrate_client.create_dump(
                basket_id=basket_id,
                content=initial_context,
                metadata=dump_metadata
            )
            dump_id = dump_response.get("dump_id") or dump_response.get("id")
            logger.info(f"Created raw_dump {dump_id} for basket {basket_id}")

        except Exception as e:
            logger.error(f"Failed to create raw_dump: {e}")
            raise ScaffoldingError(
                message=f"Failed to create raw_dump: {str(e)}",
                step="create_dump",
                details={"error": str(e)},
                basket_id=basket_id
            )

        # ================================================================
        # Step 4: Create Agent Work Request (work-platform DB)
        # ================================================================
        request_payload = {
            "initial_context": initial_context,
            "basket_name": basket_name,
            "scaffolding_timestamp": "now()",
            "dump_id": dump_id
        }

        try:
            work_request_id = await record_work_request(
                user_id=user_id,
                workspace_id=workspace_id,
                basket_id=basket_id,
                agent_type=agent_type,
                work_mode=work_mode,
                request_payload=request_payload,
                permission_info=permission_info
            )
            logger.info(
                f"Created work_request {work_request_id} "
                f"(trial={not permission_info.get('is_subscribed')})"
            )

        except Exception as e:
            logger.error(f"Failed to create work_request: {e}")
            raise ScaffoldingError(
                message=f"Failed to create work_request: {str(e)}",
                step="create_work_request",
                details={"error": str(e)},
                basket_id=basket_id,
                dump_id=dump_id
            )

        # ================================================================
        # Step 5: Return Orchestration Result
        # ================================================================
        logger.info(
            f"Successfully scaffolded work_request {work_request_id}: "
            f"basket={basket_id}, dump={dump_id}"
        )

        return {
            "work_request_id": work_request_id,
            "basket_id": basket_id,
            "basket_name": basket_name,
            "dump_id": dump_id,
            "status": "scaffolded",
            "is_trial_request": not permission_info.get("is_subscribed", False),
            "remaining_trials": permission_info.get("remaining_trial_requests")
        }

    except PermissionDeniedError:
        # Re-raise permission errors as-is
        raise

    except ScaffoldingError:
        # Re-raise scaffolding errors as-is
        raise

    except Exception as e:
        logger.exception(f"Unexpected error during scaffolding: {e}")
        raise ScaffoldingError(
            message=f"Unexpected scaffolding error: {str(e)}",
            step="unknown",
            details={"error": str(e), "type": type(e).__name__},
            basket_id=basket_id,
            dump_id=dump_id
        )
```

---

### Step 3: Create Work Requests Route

**File**: `work-platform/api/src/app/routes/work_requests.py` (NEW)

```python
"""
Work Requests API - Phase 6: Basket-First Scaffolding

Endpoints:
- POST /api/work-requests/new - Create new work request (basket-first)
- GET /api/work-requests/{work_request_id} - Get work request status
- GET /api/work-requests - List user's work requests
"""

from __future__ import annotations

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.utils.jwt import verify_jwt
from app.utils.supabase_client import supabase_client
from services.work_request_scaffolder import (
    scaffold_new_work_request,
    ScaffoldingError
)
from utils.permissions import PermissionDeniedError

router = APIRouter(prefix="/api/work-requests", tags=["work-requests"])
logger = logging.getLogger(__name__)


# ========================================================================
# Request/Response Models
# ========================================================================

class NewWorkRequestRequest(BaseModel):
    """Request to create new work request with basket scaffolding."""
    agent_type: str = Field(..., description="Agent type (research, content, reporting)")
    initial_context: str = Field(..., description="Initial context/input for basket")
    work_mode: str = Field(default="general", description="Work mode")
    basket_name: Optional[str] = Field(None, description="Optional basket name")
    metadata: Optional[dict] = Field(None, description="Optional basket metadata")


class WorkRequestResponse(BaseModel):
    """Response from work request creation."""
    work_request_id: str
    basket_id: str
    basket_name: str
    dump_id: str
    status: str
    is_trial_request: bool
    remaining_trials: Optional[int]
    message: str


class WorkRequestStatus(BaseModel):
    """Work request status details."""
    work_request_id: str
    basket_id: Optional[str]
    agent_type: str
    work_mode: str
    status: str
    is_trial_request: bool
    result_summary: Optional[str]
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]


# ========================================================================
# Endpoints
# ========================================================================

@router.post("/new", response_model=WorkRequestResponse)
async def create_new_work_request(
    request: NewWorkRequestRequest,
    user: dict = Depends(verify_jwt)
):
    """
    Create new work request with basket-first scaffolding.

    Phase 6: Orchestrates:
    1. Permission check (trial/subscription)
    2. Basket creation (substrate-api)
    3. Raw dump creation (substrate-api)
    4. Work request record (work-platform)

    Args:
        request: Work request parameters
        user: Authenticated user from JWT

    Returns:
        Work request creation result

    Example Request:
        {
            "agent_type": "research",
            "initial_context": "Research latest AI developments in healthcare",
            "basket_name": "Healthcare AI Research",
            "work_mode": "general"
        }

    Example Response:
        {
            "work_request_id": "550e8400-e29b-41d4-a716-446655440000",
            "basket_id": "660e8400-e29b-41d4-a716-446655440001",
            "basket_name": "Healthcare AI Research",
            "dump_id": "770e8400-e29b-41d4-a716-446655440002",
            "status": "scaffolded",
            "is_trial_request": true,
            "remaining_trials": 7,
            "message": "Work request scaffolded successfully"
        }
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")

    # Get workspace_id for user (existing helper from agent_orchestration.py)
    from app.routes.agent_orchestration import _get_workspace_id_for_user
    workspace_id = await _get_workspace_id_for_user(user_id)

    logger.info(
        f"Creating work request: user={user_id}, agent={request.agent_type}, "
        f"workspace={workspace_id}"
    )

    try:
        result = await scaffold_new_work_request(
            user_id=user_id,
            workspace_id=workspace_id,
            agent_type=request.agent_type,
            initial_context=request.initial_context,
            work_mode=request.work_mode,
            basket_name=request.basket_name,
            metadata=request.metadata
        )

        return WorkRequestResponse(
            **result,
            message="Work request scaffolded successfully"
        )

    except PermissionDeniedError as e:
        logger.warning(f"Permission denied: {e}")
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )

    except ScaffoldingError as e:
        logger.error(f"Scaffolding failed at step '{e.step}': {e.message}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": e.message,
                "step": e.step,
                "basket_id": e.basket_id,
                "dump_id": e.dump_id,
                "details": e.details
            }
        )

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create work request: {str(e)}"
        )


@router.get("/{work_request_id}", response_model=WorkRequestStatus)
async def get_work_request_status(
    work_request_id: str,
    user: dict = Depends(verify_jwt)
):
    """
    Get work request status.

    Args:
        work_request_id: Work request ID
        user: Authenticated user from JWT

    Returns:
        Work request status details
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")

    try:
        supabase = supabase_client

        response = supabase.table("agent_work_requests").select(
            "*"
        ).eq("id", work_request_id).eq("user_id", user_id).single().execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Work request not found")

        work_request = response.data

        return WorkRequestStatus(
            work_request_id=work_request["id"],
            basket_id=work_request.get("basket_id"),
            agent_type=work_request["agent_type"],
            work_mode=work_request.get("work_mode", "general"),
            status=work_request["status"],
            is_trial_request=work_request["is_trial_request"],
            result_summary=work_request.get("result_summary"),
            error_message=work_request.get("error_message"),
            created_at=work_request["created_at"],
            completed_at=work_request.get("completed_at")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching work request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch work request: {str(e)}"
        )


@router.get("", response_model=List[WorkRequestStatus])
async def list_work_requests(
    user: dict = Depends(verify_jwt),
    limit: int = 20,
    offset: int = 0
):
    """
    List user's work requests.

    Args:
        user: Authenticated user from JWT
        limit: Maximum results to return
        offset: Results offset for pagination

    Returns:
        List of work requests
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")

    try:
        supabase = supabase_client

        response = supabase.table("agent_work_requests").select(
            "*"
        ).eq("user_id", user_id).order(
            "created_at", desc=True
        ).limit(limit).offset(offset).execute()

        work_requests = []
        for wr in response.data:
            work_requests.append(WorkRequestStatus(
                work_request_id=wr["id"],
                basket_id=wr.get("basket_id"),
                agent_type=wr["agent_type"],
                work_mode=wr.get("work_mode", "general"),
                status=wr["status"],
                is_trial_request=wr["is_trial_request"],
                result_summary=wr.get("result_summary"),
                error_message=wr.get("error_message"),
                created_at=wr["created_at"],
                completed_at=wr.get("completed_at")
            ))

        return work_requests

    except Exception as e:
        logger.error(f"Error listing work requests: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list work requests: {str(e)}"
        )
```

---

### Step 4: Register New Router in agent_server.py

**File**: `work-platform/api/src/app/agent_server.py`

Add import and registration:

```python
# After existing imports (around line 40)
from .routes.work_requests import router as work_requests_router

# In routers tuple (around line 173)
routers = (
    baskets_router,
    agents_router,
    work_requests_router,  # NEW: Phase 6
    agent_orchestration_router,
    # ... rest
)
```

---

### Step 5: Add Basket Creation Endpoint to substrate-api

**File**: `substrate-api/api/src/app/routes/baskets.py`

Add new endpoint (if it doesn't exist):

```python
@router.post("", response_model=dict)
async def create_basket(
    request: dict,
    user: dict = Depends(verify_jwt),
    db=Depends(get_db)
):
    """
    Create new basket.

    Phase 6: Called by work-platform BFF layer.

    Args:
        request: {
            "workspace_id": "...",
            "name": "...",
            "metadata": {...}
        }

    Returns:
        {"basket_id": "...", "name": "...", ...}
    """
    workspace_id = request.get("workspace_id")
    name = request.get("name", "Untitled Basket")
    metadata = request.get("metadata", {})
    user_id = request.get("user_id") or user.get("sub")

    if not workspace_id:
        raise HTTPException(400, "workspace_id required")

    supabase = supabase_client

    basket_data = {
        "workspace_id": workspace_id,
        "name": name,
        "status": "INIT",
        "tags": metadata.get("tags", []),
        "origin_template": metadata.get("origin_template")
    }

    if user_id:
        basket_data["user_id"] = user_id

    response = supabase.table("baskets").insert(basket_data).execute()

    if not response.data:
        raise HTTPException(500, "Failed to create basket")

    basket = response.data[0]

    return {
        "basket_id": basket["id"],
        "name": basket["name"],
        "workspace_id": basket["workspace_id"],
        "status": basket["status"],
        "created_at": basket["created_at"]
    }
```

---

## User Flow Examples

### Example 1: New User First Work Request

```bash
# Step 1: User creates work request (basket-first)
POST /api/work-requests/new
{
  "agent_type": "research",
  "initial_context": "Research latest AI developments in healthcare",
  "basket_name": "Healthcare AI Research"
}

# Response:
{
  "work_request_id": "550e8400-...",
  "basket_id": "660e8400-...",
  "basket_name": "Healthcare AI Research",
  "dump_id": "770e8400-...",
  "status": "scaffolded",
  "is_trial_request": true,
  "remaining_trials": 9,
  "message": "Work request scaffolded successfully"
}

# Step 2: [FUTURE] User executes agent work on scaffolded basket
POST /api/agents/run
{
  "agent_type": "research",
  "basket_id": "660e8400-...",  # Use scaffolded basket
  "task_type": "monitor_domain",
  "parameters": {...}
}
```

### Example 2: User Creates Multiple Baskets for Different Projects

```bash
# Request 1: Marketing project
POST /api/work-requests/new
{
  "agent_type": "content",
  "initial_context": "Blog post about product launch",
  "basket_name": "Marketing - Product Launch"
}

# Request 2: Research project
POST /api/work-requests/new
{
  "agent_type": "research",
  "initial_context": "Competitive analysis of SaaS pricing",
  "basket_name": "Research - Competitor Analysis"
}

# Each gets its own basket + raw_dump + work_request
```

---

## Benefits

### 1. Basket-First Mental Model
- Users think in terms of "projects" (baskets), not "agent executions"
- Shared context container persists across multiple agent interactions
- Clear separation: basket = context, agent = worker

### 2. Automatic Substrate Scaffolding
- No manual basket creation required
- raw_dump automatically created with initial context
- Ready for agent execution immediately

### 3. Phase 3 BFF Compliance
- work-platform never touches substrate tables directly
- All substrate operations via substrate_client HTTP calls
- Clean separation of concerns

### 4. Phase 5 Trial/Subscription Integration
- Work request scaffolding counts as trial usage
- Permission checks happen BEFORE basket creation
- Clear audit trail in agent_work_requests table

### 5. Future-Proof for Agent Scaffolding
- Decision point exists for "should we auto-scaffold agent context?"
- Can add agent initialization logic later without breaking API
- Defers complexity until usage patterns understood

---

## Out-of-Scope Future Considerations

### Future Phase: Agent Scaffolding Decision
```python
# In scaffold_new_work_request(), after Step 3 (create raw_dump)

# Step 3.5: [FUTURE] Agent scaffolding decision point
if should_scaffold_agent_context(agent_type, work_mode, metadata):
    # Auto-initialize agent with prompts, tools, memory
    await initialize_agent_context(
        basket_id=basket_id,
        agent_type=agent_type,
        scaffolding_template="default"
    )
```

### Future Phase: Basket Inference for Repeat Requests
```python
# When user creates 2nd work request for same agent_type:
# - Show list of existing baskets for that agent
# - Allow user to choose: "New basket" or "Use existing basket_id"
# - Smart recommendation: "Last used basket for this agent"
```

### Future Phase: 3rd Party Integration Basket Mapping
- Similar to substrate-api's `mcp_unassigned_captures` → basket assignment
- Webhook triggers → auto-create basket → assign to agent
- Different problem domain (inbound events vs user-initiated requests)

---

## Testing Plan

### Unit Tests
1. `test_scaffold_new_work_request()` - Happy path
2. `test_scaffold_permission_denied()` - Trial exhausted
3. `test_scaffold_basket_creation_failure()` - substrate-api down
4. `test_scaffold_dump_creation_failure()` - Rollback basket?
5. `test_scaffold_work_request_creation_failure()` - Cleanup?

### Integration Tests
1. `test_end_to_end_scaffolding()` - Full flow with real substrate-api
2. `test_substrate_client_basket_creation()` - HTTP call works
3. `test_substrate_client_dump_creation()` - HTTP call works

### Manual Testing
1. Create work request via Postman/curl
2. Verify basket created in substrate-api
3. Verify raw_dump created with content
4. Verify agent_work_request created in work-platform
5. Check trial counter decrements

---

## Migration Path

### No Breaking Changes
- Existing `POST /api/agents/run` endpoint unchanged
- Users who manually create baskets can continue doing so
- New endpoint is additive, not replacement

### Recommended User Flow
**Old** (manual):
```
1. POST /api/baskets (manual - substrate-api)
2. POST /api/dumps/new (manual - substrate-api)
3. POST /api/agents/run (basket_id required)
```

**New** (basket-first):
```
1. POST /api/work-requests/new (auto-scaffolds basket + dump)
2. POST /api/agents/run (use returned basket_id)
```

---

## Success Criteria

1. ✅ User can create work request without manually creating basket
2. ✅ Basket + raw_dump automatically scaffolded via substrate-api
3. ✅ Phase 3 BFF architecture compliance maintained
4. ✅ Phase 5 trial/subscription logic integrated
5. ✅ Clear separation: basket = context, agent = worker
6. ✅ No breaking changes to existing endpoints
7. ✅ Defers agent scaffolding/inference decisions to future phase

---

## Files to Create/Modify

### New Files (3)
1. `work-platform/api/src/services/work_request_scaffolder.py` (~200 lines)
2. `work-platform/api/src/app/routes/work_requests.py` (~250 lines)
3. `substrate-api/api/src/app/routes/baskets.py` - Add `POST /api/baskets` endpoint (~50 lines)

### Modified Files (2)
4. `work-platform/api/src/clients/substrate_client.py` - Add 2 new methods (~40 lines)
5. `work-platform/api/src/app/agent_server.py` - Register new router (~2 lines)

**Total**: ~540 lines of new code

---

## Timeline Estimate

- **Step 1** (substrate_client): 30 minutes
- **Step 2** (scaffolder service): 1.5 hours
- **Step 3** (work_requests routes): 2 hours
- **Step 4** (agent_server registration): 5 minutes
- **Step 5** (substrate-api endpoint): 30 minutes
- **Testing**: 1 hour
- **Documentation**: 30 minutes

**Total**: ~6 hours for complete implementation

---

## Next Steps After Phase 6

1. **Frontend Integration**: Build UI for `POST /api/work-requests/new`
2. **Agent Scaffolding**: Decide on auto-initialization logic
3. **Basket Inference**: Smart basket selection for repeat users
4. **Agent Lifecycle**: Chat interface, governance workflow
5. **3rd Party Integration**: Webhook-triggered basket creation

---

**Status**: Ready for implementation approval
