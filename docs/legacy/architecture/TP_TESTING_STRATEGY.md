# TP Architecture Testing Strategy

## Overview

This document outlines the systematic approach to testing the TP (Thinking Partner) architecture independently of production logs. We validate each workflow separately to ensure the staging pattern and work bundle architecture function correctly.

---

## Architecture Recap

### Work Bundle Pattern (Implemented Nov 21, 2025)

**Three-Phase Architecture**:
1. **Chat Phase**: TP collects requirements via natural conversation (NO substrate queries)
2. **Staging Phase**: Context loaded ONCE at work_orchestration boundary (3 queries)
3. **Delegation Phase**: Specialists receive pre-loaded WorkBundle (NO queries during execution)

**Key Components**:
- `ThinkingPartnerAgentSDK`: Orchestrator and staging gateway
- `WorkBundle`: In-memory structure with pre-loaded context
- Hierarchical sessions: TP parent → specialist children
- Staging methods: `_load_substrate_blocks()`, `_load_reference_assets()`, `_load_agent_config()`

---

## Workflow 1: Regular TP Chat (No Work Orchestration)

### Purpose
Validate that TP can handle regular conversation without triggering substrate queries or work orchestration.

### Test Scope
**Database Layer** ✅ VALIDATED (Nov 21, 2025)
- TP session creation with `agent_type='thinking_partner'`
- Session persistence to database
- No constraint violations

**Result**:
```
✅ Created: 5885a5f9-d265-4e5f-8153-f4530c043a87
   - agent_type: thinking_partner
   - parent_session_id: None
```

**Chat Layer** ⏸️ NOT YET TESTED
- Requires ANTHROPIC_API_KEY (Claude SDK)
- User message → TP processes → Response returned
- NO work_orchestration tool usage
- NO substrate queries

### Expected Behavior

1. **User sends**: "Hello! What can you help with?"
2. **TP initializes**:
   - Creates agent_session (agent_type='thinking_partner')
   - Initializes Claude SDK client
3. **TP processes**:
   - NO substrate queries (chat phase only)
   - NO work_orchestration tool called
   - Claude SDK session maintains conversation context
4. **TP responds**: Describes capabilities
5. **Database state**:
   - 1 agent_session (TP)
   - 0 specialist sessions
   - 0 work_requests
   - 0 work_tickets

### Testing Commands

**Database-only test** (no Claude API):
```bash
cd work-platform/api
PYTHONPATH=src \
SUPABASE_URL=https://galytxxkrbksilekmhcw.supabase.co \
SUPABASE_SERVICE_ROLE_KEY=... \
python3 -c "
import asyncio
from yarnnn_agents.session import AgentSession

async def test():
    session = await AgentSession.get_or_create(
        basket_id='5004b9e1-67f5-4955-b028-389d45b1f5a4',
        workspace_id='99e6bf7d-513c-45ff-9b96-9362bd914d12',
        agent_type='thinking_partner',
        user_id='aa94fbd9-13cc-4dbc-a9fb-2114ad0928f2'
    )
    print(f'✅ TP session: {session.id}')

asyncio.run(test())
"
```

**Full chat test** (with Claude API):
```bash
# TODO: Requires ANTHROPIC_API_KEY
cd work-platform/api
PYTHONPATH=src \
SUPABASE_URL=... \
SUPABASE_SERVICE_ROLE_KEY=... \
ANTHROPIC_API_KEY=... \
python3 tests/integration/test_tp_workflows.py
```

---

## Workflow 2: Work Orchestration (Staging + Delegation)

### Purpose
Validate the complete staging pattern: TP decides to delegate → loads context at boundary → creates WorkBundle → specialist executes.

### Test Scope

**Staging Phase** ⏸️ NOT YET TESTED
- work_orchestration tool triggered by Claude
- `_load_substrate_blocks()` called
- `_load_reference_assets()` called
- `_load_agent_config()` called
- WorkBundle created with pre-loaded context

**Delegation Phase** ⏸️ NOT YET TESTED
- Specialist session created (child of TP)
- Specialist agent receives WorkBundle
- Specialist executes with pre-loaded context (NO queries)
- work_outputs emitted

**Database Tracking** ⏸️ NOT YET TESTED
- work_request created (links to TP session)
- work_ticket created (execution tracking)
- work_outputs table populated (via substrate-API)

### Expected Behavior

1. **User sends**: "Research the latest developments in AI agent frameworks"
2. **TP decides**: Triggers work_orchestration tool
3. **STAGING PHASE**:
   ```
   STAGING PHASE: Loading context for research work request
   Query 1: substrate blocks (long-term knowledge)
   Query 2: reference assets (task resources)
   Query 3: agent config (settings)
   STAGING COMPLETE: 12 blocks, 3 assets, config=True
   ```
4. **WorkBundle created**:
   ```python
   bundle = WorkBundle(
       work_request_id=...,
       work_ticket_id=...,
       basket_id=...,
       task="Research AI agent frameworks",
       agent_type="research",
       substrate_blocks=[12 blocks],
       reference_assets=[3 assets],
       agent_config={...}
   )
   ```
5. **Specialist session** created/retrieved:
   - agent_type='research'
   - parent_session_id → TP session
   - Cached in `_specialist_sessions['research']`
6. **DELEGATION PHASE**:
   ```python
   agent = ResearchAgentSDK(
       basket_id=...,
       workspace_id=...,
       work_ticket_id=...,
       session=specialist_session,
       bundle=bundle  # Pre-loaded context!
   )
   result = await agent.deep_dive(topic="AI agent frameworks")
   ```
7. **Specialist executes**:
   - NO substrate queries (uses bundle)
   - web_search tool for current info
   - emit_work_output tool for deliverables
8. **Database state**:
   - 2 agent_sessions (TP + research specialist)
   - 1 work_request (links to TP session)
   - 1 work_ticket (execution tracking)
   - N work_outputs (deliverables in substrate-API)

### Testing Commands

**Manual trigger** (requires Claude API + substrate access):
```bash
cd work-platform/api
PYTHONPATH=src \
SUPABASE_URL=... \
SUPABASE_SERVICE_ROLE_KEY=... \
ANTHROPIC_API_KEY=... \
SUBSTRATE_API_URL=https://yarnnn-substrate-api.onrender.com \
python3 tests/integration/test_tp_workflows.py
```

**Production testing** (via frontend):
1. Go to https://www.yarnnn.com
2. Open existing project
3. Send message: "I need you to research AI agent frameworks"
4. Monitor backend logs for:
   - "STAGING PHASE: Loading context"
   - "STAGING COMPLETE: X blocks, Y assets"
   - "DELEGATION PHASE: Executing research"

---

## Key Validation Points

### ✅ Database Architecture (VALIDATED)
- [x] `thinking_partner` allowed in agent_type constraint
- [x] TP session creation works
- [x] Session persistence to database
- [x] Hierarchical session pattern (parent-child linking via save())

### ⏸️ Chat Phase (NOT YET TESTED)
- [ ] TP processes simple messages without work_orchestration
- [ ] Claude SDK session management working
- [ ] NO substrate queries during chat phase
- [ ] Conversation continuity across messages

### ⏸️ Staging Phase (NOT YET TESTED)
- [ ] work_orchestration tool triggered correctly
- [ ] `_load_substrate_blocks()` executes (3 retries, circuit breaker)
- [ ] `_load_reference_assets()` executes
- [ ] `_load_agent_config()` executes
- [ ] WorkBundle created with correct structure
- [ ] Errors handled gracefully (401 → empty arrays)

### ⏸️ Delegation Phase (NOT YET TESTED)
- [ ] Specialist session created/retrieved as child of TP
- [ ] Specialist agent receives WorkBundle
- [ ] Specialist NO substrate queries (uses bundle only)
- [ ] work_outputs emitted correctly
- [ ] TP synthesizes specialist results

### ⏸️ Database Tracking (NOT YET TESTED)
- [ ] work_request created with TP session link
- [ ] work_ticket created with specialist session link
- [ ] work_outputs table populated (via substrate-API)
- [ ] Provenance chain complete (request → ticket → outputs → sessions)

---

##
 Current Status (Nov 21, 2025)

### What Works ✅
1. **Database migration applied**: `thinking_partner` constraint fixed
2. **TP session creation**: Database layer validated
3. **TP chat returning 200 OK**: Production logs show successful responses
4. **Code architecture**: Staging pattern implemented correctly

### What's Untested ⏸️
1. **Chat phase behavior**: Requires Claude API testing
2. **Staging phase execution**: Need to trigger work_orchestration
3. **WorkBundle creation**: Need to verify staging queries succeed
4. **Delegation phase**: Need to verify specialist execution with bundle
5. **Substrate API auth**: 401 errors from old deployment (pre-staging pattern)

### Next Steps

1. **Test Chat Phase** (Workflow 1):
   - Add ANTHROPIC_API_KEY to local/test environment
   - Run `tests/integration/test_tp_workflows.py`
   - Verify simple chat works without work_orchestration

2. **Test Staging Phase** (Workflow 2):
   - Trigger work_orchestration with clear work request
   - Monitor logs for "STAGING PHASE" messages
   - Verify 3 queries execute (blocks, assets, config)
   - Check if substrate API 401 errors persist

3. **Test Delegation Phase** (Workflow 2 continued):
   - Verify specialist session created as child
   - Check WorkBundle passed to specialist
   - Verify specialist executes without queries
   - Check work_outputs emitted

4. **Production Validation**:
   - Test via frontend (www.yarnnn.com)
   - Monitor Render logs for complete flow
   - Verify database records created correctly

---

## Troubleshooting

### Issue: TP Session Creation Fails
**Symptom**: Database constraint violation
**Cause**: Migration not applied
**Fix**: Apply `supabase/migrations/20251121_fix_thinking_partner_agent_type.sql`

### Issue: Staging Queries Fail with 401
**Symptom**: "Substrate API error: HTTP 401"
**Possible Causes**:
1. `user_token` not being passed correctly
2. JWT format doesn't match substrate-API expectations
3. substrate-API auth middleware rejecting token
**Diagnosis**: Check logs for `has_token=True/False` in staging debug messages

### Issue: Work Orchestration Not Triggered
**Symptom**: No "STAGING PHASE" logs, no work_outputs
**Possible Causes**:
1. Claude didn't decide to use work_orchestration tool
2. User message not clear enough
3. Tool not properly registered in ClaudeAgentOptions
**Fix**: Use more explicit work request language

### Issue: Specialist Session Creation Fails
**Symptom**: Error creating child session
**Possible Causes**:
1. TP session not initialized
2. Foreign key constraints
**Diagnosis**: Check TP session exists and has valid ID

---

## Test Files

- `tests/integration/test_tp_workflows.py` - Complete workflow tests (Chat + Work Orchestration)
- `tests/integration/test_tp_chat_basic.py` - Database-only validation (no Claude API)
- `work-platform/api/test_tp_quick.py` - Quick validation script (inline)

---

**Last Updated**: Nov 21, 2025
**Status**: Database layer validated, Chat/Staging/Delegation phases awaiting testing
