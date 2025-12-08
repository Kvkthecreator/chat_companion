# Agent Execution Integration Test

**Date**: 2025-11-16
**Status**: Phase 5 Complete
**Purpose**: Document end-to-end agent execution flow

---

## Test Scenario

User wants to run a research agent on their project and review the outputs.

### Flow Overview

```
1. User → POST /projects/{id}/work-sessions (create session)
2. User → POST /projects/{id}/work-sessions/{id}/execute (trigger agent)
3. Agent → Reads substrate context via SubstrateMemoryAdapter
4. Agent → Returns ResearchResult with findings
5. Executor → Parses findings into work_outputs table
6. User → GET /api/supervision/sessions/{id}/outputs (review outputs)
7. User → POST /api/supervision/outputs/{id}/approve (approve good outputs)
8. User → POST /api/supervision/sessions/{id}/finalize (finalize session)
```

---

## Step-by-Step Walkthrough

### Step 1: Create Work Session

**Request:**
```http
POST /projects/proj-123/work-sessions
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "agent_id": "agent-456",
  "task_description": "Research AI agent market trends for Q4 2024",
  "priority": 5,
  "approval_strategy": {
    "strategy": "auto_approve_high_confidence"
  }
}
```

**Response:**
```json
{
  "session_id": "sess-789",
  "project_id": "proj-123",
  "agent_id": "agent-456",
  "agent_type": "research",
  "task_description": "Research AI agent market trends for Q4 2024",
  "status": "initialized",
  "work_request_id": "req-012",
  "created_at": "2025-11-16T10:00:00Z",
  "is_trial_request": false,
  "remaining_trials": null,
  "message": "Work session created with context envelope. Agent ready to execute."
}
```

### Step 2: Execute Agent

**Request:**
```http
POST /projects/proj-123/work-sessions/sess-789/execute
Authorization: Bearer <jwt>
```

**Internal Flow:**
1. WorkSessionExecutor.execute_work_session(sess-789)
2. Updates session status: initialized → in_progress
3. Creates agent via factory (with DB-first config)
4. SubstrateMemoryAdapter.query() fetches context blocks
5. SubstrateMemoryAdapter injects reference_assets + agent_config
6. Agent.execute() returns ResearchResult
7. Executor parses findings → work_outputs rows
8. Checkpoint detection checks confidence thresholds
9. Updates session status: in_progress → completed (or checkpoint_required)

**Response:**
```json
{
  "session_id": "sess-789",
  "status": "completed",
  "artifacts_count": 2
}
```

### Step 3: List Outputs for Review

**Request:**
```http
GET /api/supervision/sessions/sess-789/outputs
Authorization: Bearer <jwt>
```

**Response:**
```json
{
  "session_id": "sess-789",
  "session_status": "completed",
  "outputs": [
    {
      "id": "out-001",
      "output_type": "research_finding",
      "content": "AI agent market growing 40% YoY according to Gartner",
      "agent_confidence": 0.92,
      "agent_reasoning": "High confidence due to authoritative source",
      "status": "pending",
      "created_at": "2025-11-16T10:01:00Z"
    },
    {
      "id": "out-002",
      "output_type": "research_finding",
      "content": "New competitor AgentForce launched with $50M funding",
      "agent_confidence": 0.85,
      "agent_reasoning": "Medium-high confidence, single source",
      "status": "pending",
      "created_at": "2025-11-16T10:01:01Z"
    }
  ],
  "total_count": 2,
  "pending_count": 2,
  "approved_count": 0,
  "rejected_count": 0
}
```

### Step 4: Approve Outputs

**Request:**
```http
POST /api/supervision/outputs/out-001/approve
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "feedback": "Good finding, add to substrate"
}
```

**Response:**
```json
{
  "output_id": "out-001",
  "status": "approved",
  "reviewed_at": "2025-11-16T10:05:00Z",
  "reviewed_by_user_id": "user-abc",
  "message": "Output approved successfully"
}
```

### Step 5: Get Session Summary

**Request:**
```http
GET /api/supervision/sessions/sess-789/summary
Authorization: Bearer <jwt>
```

**Response:**
```json
{
  "session_id": "sess-789",
  "session_status": "completed",
  "task_intent": "Research AI agent market trends for Q4 2024",
  "total_outputs": 2,
  "approved_outputs": 2,
  "rejected_outputs": 0,
  "pending_outputs": 0,
  "can_finalize": true,
  "created_at": "2025-11-16T10:00:00Z",
  "ended_at": null
}
```

### Step 6: Finalize Session

**Request:**
```http
POST /api/supervision/sessions/sess-789/finalize
Authorization: Bearer <jwt>
```

**Response:**
```json
{
  "session_id": "sess-789",
  "final_status": "approved",
  "finalized_at": "2025-11-16T10:10:00Z",
  "approved_outputs": 2,
  "rejected_outputs": 0,
  "message": "Session finalized with status: approved"
}
```

---

## Architecture Layers Involved

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                     │
│  project_work_sessions.py, work_supervision.py               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Work Session Executor                        │
│  work_session_executor.py, agent_sdk_client.py              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Agent Factory                             │
│  factory.py (DB-first config with YAML fallback)            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Substrate Memory Adapter                     │
│  memory_adapter.py (BFF pattern: HTTP to substrate-api)     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                     SDK Agents (Mock)                        │
│  claude_agent_sdk/archetypes.py (contract definition)       │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Tables Involved

1. **work_sessions** - Execution tracking
2. **work_outputs** (renamed from work_artifacts) - Agent deliverables
3. **work_checkpoints** - Mid-execution review points
4. **project_agents** - Agent configuration (DB-first)
5. **agent_work_requests** - Billing/trial tracking

---

## Key Insights

### What Works

1. **Terminology Hardening** ✅
   - work_outputs (not work_artifacts)
   - output_type (not artifact_type)
   - Prevents confusion with reflections_artifact

2. **Config Consolidation** ✅
   - DB-first (project_agents.config)
   - YAML fallback for defaults
   - Single source of truth

3. **Mock SDK Contract** ✅
   - ResearchResult with findings list
   - ContentResult with variations list
   - ReportResult with report data
   - Checkpoint detection via confidence thresholds

4. **Supervision Endpoints** ✅
   - Separate from Substrate Governance
   - Human oversight of agent deliverables
   - Approve/reject individual outputs

### What's Missing (Deferred)

1. **Direct agent_orchestration wiring**
   - Current: Creates agent, returns raw result
   - Needed: Create session, store outputs automatically
   - Status: WorkSessionExecutor exists but not wired

2. **Checkpoint resumption**
   - WorkSessionExecutor.resume_from_checkpoint() is NotImplemented
   - Need to restore agent state and continue execution

3. **Substrate governance bridge**
   - Approved outputs → substrate block proposals
   - Not implemented (intentionally separate domain)

4. **Scheduled execution (execution modes)**
   - Cron-based agent runs
   - Not mission critical for MVP

5. **Real SDK integration**
   - Mock SDK defines contract
   - Real SDK when available

---

## Test Assertions

```python
# Session lifecycle
assert session["status"] in ["initialized", "in_progress", "completed", "failed", "approved"]

# Output review
assert output["status"] in ["pending", "approved", "rejected"]

# Config loading
assert factory uses project_agents.config first
assert factory falls back to YAML if no DB config

# Terminology
assert "work_outputs" in database_tables
assert "work_artifacts" not in database_tables
```

---

## Next Steps

1. **Wire agent_orchestration.py** to use WorkSessionExecutor
2. **Implement checkpoint resumption** for iterative refinement
3. **Build substrate governance bridge** (approved outputs → block proposals)
4. **Add scheduled execution** when needed
5. **Replace mock SDK** with real implementation

---

**End of Integration Test**
