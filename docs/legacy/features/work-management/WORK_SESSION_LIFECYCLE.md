# Work Session Lifecycle

**Complete State Machine for Agent Work Execution**

**Version**: 5.0
**Date**: 2025-11-17
**Status**: ✅ Canonical - Updated for Current Implementation
**Layer**: 2 (Work Orchestration)
**Category**: Feature Specification

---

## ⚠️ Implementation Update (2025-11-17)

**Current Implementation**:
- work_sessions table in **work-platform DB** (tracks execution)
- work_outputs table in **substrate-API DB** (stores agent deliverables)
- BFF pattern: work-platform orchestrates, substrate-API owns data
- Session status: pending → running → completed/completed_with_errors/failed
- Supervision: Separate from session status (outputs have supervision_status)

**Simplified States** (actual implementation):
- `pending` - Created, not started
- `running` - Agent executing
- `completed` - Finished successfully
- `completed_with_errors` - Finished but some outputs failed
- `failed` - Execution error

---

## 🎯 Overview

This document specifies the complete lifecycle of a **work session** - from task creation through agent execution, user review, and substrate application. Work sessions are the primary unit of agent work in YARNNN v4.0.

**Key Concepts**:
- Work sessions track agent execution from start to finish
- Sessions live in work-platform DB, outputs live in substrate-API DB
- BFF pattern enforces clean separation of concerns
- Session status != supervision status (outputs reviewed independently)
- Sessions create outputs that await user supervision

---

## 📊 State Machine

### Current Implementation (Simplified)

```typescript
// Actual states in work_sessions table (work-platform DB)
type WorkSessionStatus =
  | 'pending'                   // Created, not yet started
  | 'running'                   // Agent actively working
  | 'completed'                 // Finished successfully, outputs written
  | 'completed_with_errors'     // Finished but some outputs failed to write
  | 'failed'                    // Agent execution error
```

> **Note**: User review/approval is handled via **supervision_status** on individual work_outputs (substrate-API), not session status.

### Future States (Not Yet Implemented)

```typescript
// Planned for more sophisticated workflows
type FutureWorkSessionStatus =
  | 'initialized'           // Created, not yet started
  | 'in_progress'           // Agent actively working
  | 'pending_review'        // Work complete, awaiting user review
  | 'iteration_requested'   // User requested changes
  | 'completed_approved'    // Approved, artifacts applied to substrate
  | 'rejected'              // Rejected, no substrate changes
  | 'cancelled'             // User cancelled before completion
  | 'failed'                // Agent error, technical failure
```

### Current Implementation Flow

```
┌─────────┐
│ pending │ (Session created before agent execution)
└────┬────┘
     │ _create_work_session()
     ▼
┌─────────┐
│ running │ (Agent executing via yarnnn_agents)
└────┬────┘
     │ agent.deep_dive() → emit_work_output tool calls
     ▼
┌───────────┐
│ completed │ (Outputs written to substrate-API)
└───────────┘
     │
     └─────────────────────────────────────────┐
                                               ▼
                                    ┌────────────────────┐
                                    │   work_outputs     │
                                    │ (substrate-API DB) │
                                    └─────────┬──────────┘
                                              │
                                              │ supervision_status
                                              ▼
                                    ┌─────────────────────┐
                                    │   pending_review    │
                                    │   approved          │
                                    │   rejected          │
                                    │   revision_requested│
                                    └─────────────────────┘
```

**Key Insight**: Session status and output supervision are decoupled. Session tracks execution, outputs track user review.

### Future State Diagram (Sophisticated Workflow)

```
┌─────────────┐
│ initialized │ (Creation)
└──────┬──────┘
       │ Agent starts work
       ▼
┌─────────────┐
│ in_progress │ (Agent execution)
└──────┬──────┘
       │ Agent completes work
       ▼
┌──────────────┐
│pending_review│ (Awaiting user decision)
└──────┬───────┘
       │
       ├──────────────────┬──────────────────┬─────────────────┐
       │                  │                  │                 │
       │ Approved         │ Needs revision   │ Rejected        │ Cancelled
       ▼                  ▼                  ▼                 ▼
┌──────────────┐   ┌─────────────────┐   ┌──────────┐   ┌──────────┐
│completed_    │   │iteration_       │   │ rejected │   │cancelled │
│approved      │   │requested        │   └──────────┘   └──────────┘
└──────────────┘   └────────┬────────┘
                            │ Agent revises
                            │
                            └────────────────┐
                                             ▼
                                    ┌─────────────┐
                                    │ in_progress │
                                    └─────────────┘
                                             │
                                             └──► (back to pending_review)
```

### State Transitions

| From | To | Trigger | Actor | Database Changes |
|------|-----|---------|-------|------------------|
| `initialized` | `in_progress` | Agent starts work | Agent | `started_at = NOW()` |
| `in_progress` | `pending_review` | Agent completes work | Agent | `completed_at = NOW()`, `artifacts_count` set |
| `in_progress` | `failed` | Agent error | System | `failed_at = NOW()`, `failure_reason` set |
| `pending_review` | `completed_approved` | User approves | User | `approved_at = NOW()`, `approved_by` set, substrate mutations applied |
| `pending_review` | `rejected` | User rejects | User | `rejected_at = NOW()`, `rejected_by` set, `rejection_feedback` set |
| `pending_review` | `iteration_requested` | User requests changes | User | `current_iteration` incremented, iteration record created |
| `pending_review` | `cancelled` | User cancels | User | `cancelled_at = NOW()`, `cancelled_by` set |
| `iteration_requested` | `in_progress` | Agent starts revision | Agent | `current_iteration` maintained |
| `initialized` | `cancelled` | User cancels before start | User | `cancelled_at = NOW()` |
| `in_progress` | `cancelled` | User cancels mid-work | User | `cancelled_at = NOW()` |

---

## 🔄 Current Implementation (2025-11-17)

### Actual Execution Flow

```python
# work-platform/api/src/app/routes/agent_orchestration.py

async def execute_agent_work(request: AgentWorkRequest, user_id: str):
    # 1. Create work session BEFORE agent execution
    work_session_id = await _create_work_session(
        basket_id=request.basket_id,
        workspace_id=request.workspace_id,
        user_id=user_id,
        agent_type=request.agent_type,
        task_intent=request.task_intent,
        project_id=request.project_id,
    )
    # Status: pending → running

    # 2. Execute agent (yarnnn_agents)
    result = await _run_research_agent(request, user_id, work_session_id)
    # Agent emits outputs via emit_work_output tool

    # 3. Write outputs to substrate-API
    work_outputs = result.get("work_outputs", [])
    output_write_result = write_agent_outputs(
        basket_id=request.basket_id,
        work_session_id=work_session_id,
        agent_type=request.agent_type,
        outputs=work_outputs,
    )

    # 4. Update session status based on results
    if output_write_result.get("all_successful"):
        # Status: running → completed
        await update_session_status(work_session_id, "completed")
    else:
        # Status: running → completed_with_errors
        await update_session_status(work_session_id, "completed_with_errors")
```

### Supervision Flow (Separate from Session)

```python
# substrate-api/api/src/app/work_outputs/routes.py

@router.get("/baskets/{basket_id}/outputs")
async def list_outputs(basket_id: str, supervision_status: str = "pending_review"):
    # Returns outputs pending user review
    pass

@router.put("/baskets/{basket_id}/outputs/{output_id}/status")
async def update_output_status(output_id: str, status: str, notes: str):
    # User approves/rejects individual output
    # supervision_status: pending_review → approved/rejected/revision_requested
    pass
```

**Key Insight**: Session execution and output supervision are independent workflows.

---

## 🔄 Lifecycle Phases (Reference Architecture)

### Phase 1: Initialization

**Trigger**: User creates task, agent receives assignment, or system schedules work.

**Actions**:
```python
# Create work session
session = await db.work_sessions.create(
    workspace_id=workspace_id,
    basket_id=basket_id,
    initiated_by_user_id=user_id,
    task_intent="Research competitors in AI memory space",
    task_type="research",
    status="initialized",
    approval_strategy="final_only",
    created_at=datetime.utcnow()
)

# Emit timeline event
await timeline_service.emit_work_session_created(session)

# Notify agent (if automated execution)
await notification_service.notify_agent_task_ready(session)
```

**Database Records**:
- 1 `work_sessions` row (status: `initialized`)
- 1 `timeline_events` row (type: `work_session_created`)

**Frontend State**:
- Task appears in "Pending Work" queue
- User can view task details, cancel if needed

---

### Phase 2: Agent Execution

**Trigger**: Agent starts working on task (manual or automatic).

**State Transition**: `initialized` → `in_progress`

**Actions**:
```python
# Agent updates status
await db.work_sessions.update(
    session_id,
    status="in_progress",
    started_at=datetime.utcnow(),
    executed_by_agent_id="claude-opus-20250115",
    agent_session_id="agent-sdk-session-uuid"  # Link to Agent SDK
)

# Agent retrieves context from substrate
context = await memory_provider.retrieve_context(
    query="AI memory competitors",
    session_metadata={
        "workspace_id": workspace_id,
        "basket_id": basket_id
    }
)

# Agent performs work (research, synthesis, etc.)
# ...

# Agent creates artifacts
artifact_1 = await db.work_artifacts.create(
    work_session_id=session_id,
    artifact_type="block_proposal",
    content={
        "block_content": {
            "text": "Mem (YC W22) - Personal memory assistant...",
            "entities": ["Mem", "YC"]
        }
    },
    agent_confidence=0.95,
    agent_reasoning="Verified from official sources",
    status="draft"
)

# Risk assessment calculated automatically
risk = await risk_engine.assess_artifact_risk(artifact_1, session)
await db.work_artifacts.update(artifact_1.id, risk_level=risk.finalRisk)

# Agent logs reasoning trail
await db.work_sessions.append_reasoning(
    session_id,
    reasoning_entry={
        "timestamp": datetime.utcnow(),
        "reasoning": "Found 3 major competitors, focusing on pricing and features"
    }
)
```

**Database Records**:
- `work_sessions` row updated (status: `in_progress`, `started_at` set)
- N `work_artifacts` rows created (status: `draft`)
- `reasoning_trail` array appended

**Frontend State**:
- Task shows "In Progress" status
- User can view live progress (if agent streams updates)
- User can cancel if needed

---

### Phase 3: Work Completion

**Trigger**: Agent finishes all work, ready for review.

**State Transition**: `in_progress` → `pending_review`

**Actions**:
```python
# Agent marks work complete
await db.work_sessions.update(
    session_id,
    status="pending_review",
    completed_at=datetime.utcnow(),
    artifacts_count=len(artifacts)
)

# Update all artifacts to pending_review
await db.work_artifacts.update_many(
    work_session_id=session_id,
    status="pending_review"
)

# Create checkpoint (if approval strategy requires)
checkpoint = await checkpoint_manager.create_checkpoint(
    session,
    checkpoint_type="final_approval",
    review_context={
        "artifacts": [a.id for a in artifacts],
        "summary": "Research completed: 3 competitors identified"
    }
)

# Emit timeline event
await timeline_service.emit_work_completed(session)

# Notify user for review
await notification_service.notify_work_ready_for_review(
    session, artifacts_count=len(artifacts)
)
```

**Database Records**:
- `work_sessions` row updated (status: `pending_review`, `completed_at` set)
- All `work_artifacts` rows updated (status: `pending_review`)
- 1 `work_checkpoints` row created (status: `pending`)
- 1 `timeline_events` row (type: `work_completed`)
- 1 `notifications` row (user notification)

**Frontend State**:
- Task appears in "Review Queue"
- User can open work review UI
- Shows artifacts with risk indicators

---

### Phase 4A: User Approval

**Trigger**: User reviews work and approves.

**State Transition**: `pending_review` → `completed_approved`

**Actions**:
```python
# User submits approval decision
decision = WorkReviewDecision(
    workQuality="approved",
    artifactDecisions={
        artifact_1.id: "apply_to_substrate",
        artifact_2.id: "apply_to_substrate",
        artifact_3.id: "approve_only"  # No substrate impact
    }
)

# Unified orchestrator processes approval
result = await unified_orchestrator.review_work_session(
    session_id, user_id, decision
)

# Result:
# - Artifacts 1, 2 → Blocks created in substrate (ACCEPTED state)
# - Artifact 3 → Marked approved but no substrate mutation
# - Session status → completed_approved
# - Timeline event created
# - Notifications sent
# - Agent track record updated
```

**Database Records** (Transaction):
- `work_sessions` row updated (status: `completed_approved`, `approved_at` set)
- N `blocks` rows created (from artifacts, state: `ACCEPTED`)
- N `work_artifacts` rows updated (status: `applied_to_substrate`, `becomes_block_id` set)
- N `work_context_mutations` rows created (audit trail)
- 1 `timeline_events` row (type: `work_approved`)
- 1 `agent_track_record` row updated (approval_rate recalculated)
- N `notifications` rows (workspace members notified)

**Frontend State**:
- Task moves to "Completed" list
- Shows substrate changes summary (e.g., "3 blocks created")
- New blocks appear in substrate view
- Timeline shows work approval event

---

### Phase 4B: User Rejection

**Trigger**: User reviews work and rejects.

**State Transition**: `pending_review` → `rejected`

**Actions**:
```python
# User submits rejection decision
decision = WorkReviewDecision(
    workQuality="rejected",
    feedback="Research too surface-level, need deeper analysis on pricing"
)

# Unified orchestrator processes rejection
result = await unified_orchestrator.review_work_session(
    session_id, user_id, decision
)

# Result:
# - No substrate changes
# - All artifacts marked rejected
# - Feedback captured
# - Agent track record updated (rejection logged)
```

**Database Records**:
- `work_sessions` row updated (status: `rejected`, `rejected_at` set, `rejection_feedback` set)
- N `work_artifacts` rows updated (status: `rejected`)
- 1 `timeline_events` row (type: `work_rejected`)
- 1 `agent_track_record` row updated (rejection counted)

**Frontend State**:
- Task moves to "Rejected" list
- Shows rejection reason
- User can create new task if needed

---

### Phase 4C: Iteration Request

**Trigger**: User reviews work and requests changes.

**State Transition**: `pending_review` → `iteration_requested` → `in_progress`

**Actions**:
```python
# User submits iteration request
decision = WorkReviewDecision(
    workQuality="needs_revision",
    changeRequests=[
        ChangeRequest(
            requestType="data_quality",
            description="Need deeper analysis on pricing for each competitor",
            priority="critical"
        ),
        ChangeRequest(
            requestType="scope",
            description="Include open-source alternatives like Obsidian",
            priority="important"
        )
    ]
)

# Unified orchestrator creates iteration
result = await unified_orchestrator.review_work_session(
    session_id, user_id, decision
)

# Result:
# - Iteration record created (iteration_number = 1)
# - Session status → iteration_requested
# - Agent notified to revise

# Agent starts revision
await db.work_sessions.update(
    session_id,
    status="in_progress"  # Back to in_progress for iteration
)

# Agent creates NEW artifacts (iteration 2)
# ... (same as Phase 2) ...

# Eventually returns to pending_review
await db.work_sessions.update(
    session_id,
    status="pending_review"
)
```

**Database Records** (Iteration):
- 1 `work_iterations` row created (iteration_number, changes_requested)
- `work_sessions` row updated (status: `iteration_requested` → `in_progress` → `pending_review`)
- N new `work_artifacts` rows created (revised versions)
- 1 `timeline_events` row (type: `iteration_requested`)

**Iteration Limits**:
- Max iterations: 3 (configurable per workspace)
- After 3 iterations, forced rejection:
  ```python
  if current_iterations >= max_iterations:
      # Force rejection
      await unified_orchestrator._handle_rejection(
          session, artifacts,
          f"Exceeded max iterations ({max_iterations}). Please reframe task.",
          user_id
      )
  ```

**Frontend State**:
- Task shows "Revising" status
- Displays iteration history (feedback → revision → feedback)
- User can view progress of revision

---

### Phase 5: Cancellation (Optional)

**Trigger**: User cancels task before/during execution.

**State Transition**: `initialized` | `in_progress` | `pending_review` → `cancelled`

**Actions**:
```python
# User cancels work session
await db.work_sessions.update(
    session_id,
    status="cancelled",
    cancelled_at=datetime.utcnow(),
    cancelled_by=user_id,
    cancellation_reason="Task no longer needed"
)

# Mark artifacts as cancelled
await db.work_artifacts.update_many(
    work_session_id=session_id,
    status="cancelled"
)

# Emit timeline event
await timeline_service.emit_work_cancelled(session, user_id)
```

**Database Records**:
- `work_sessions` row updated (status: `cancelled`)
- N `work_artifacts` rows updated (status: `cancelled`)
- 1 `timeline_events` row (type: `work_cancelled`)

**Frontend State**:
- Task moves to "Cancelled" list
- Shows cancellation reason

---

### Phase 6: Failure Handling (Error Cases)

**Trigger**: Agent encounters error during execution.

**State Transition**: `in_progress` → `failed`

**Actions**:
```python
# Agent reports failure
await db.work_sessions.update(
    session_id,
    status="failed",
    failed_at=datetime.utcnow(),
    failure_reason="API rate limit exceeded",
    failure_details={
        "error_type": "RateLimitError",
        "error_message": "429 Too Many Requests",
        "retry_after": 60
    }
)

# Emit timeline event
await timeline_service.emit_work_failed(session)

# Notify user
await notification_service.notify_work_failed(session)
```

**Database Records**:
- `work_sessions` row updated (status: `failed`, `failure_reason` set)
- 1 `timeline_events` row (type: `work_failed`)
- 1 `notifications` row (user notification)

**Frontend State**:
- Task shows "Failed" status
- Displays error message
- User can retry or cancel

**Retry Logic**:
```python
# User retries failed work
new_session = await db.work_sessions.create(
    workspace_id=original_session.workspace_id,
    basket_id=original_session.basket_id,
    task_intent=original_session.task_intent,
    task_type=original_session.task_type,
    parent_session_id=original_session.id,  # Link to failed session
    status="initialized"
)
```

---

## 📋 Session Metadata

### Core Fields

```typescript
interface WorkSession {
  // Identity
  id: UUID
  workspace_id: UUID
  basket_id: UUID

  // Initiation
  initiated_by_user_id: UUID
  created_at: ISO8601

  // Task definition
  task_intent: string               // Natural language description
  task_type: string                 // research | synthesis | analysis | etc.
  task_document_id?: UUID           // P4 document providing context

  // Agent execution
  executed_by_agent_id?: string     // Agent identifier
  agent_session_id?: string         // Links to Agent SDK session
  started_at?: ISO8601
  completed_at?: ISO8601

  // Lifecycle state
  status: WorkSessionStatus
  current_iteration: number         // Default: 0

  // Governance
  approval_strategy: string         // checkpoint_required | final_only | auto_approve_low_risk
  approved_at?: ISO8601
  approved_by?: UUID
  rejected_at?: ISO8601
  rejected_by?: UUID
  rejection_feedback?: string
  cancelled_at?: ISO8601
  cancelled_by?: UUID
  cancellation_reason?: string
  failed_at?: ISO8601
  failure_reason?: string
  failure_details?: Record<string, any>

  // Work summary
  artifacts_count: number
  substrate_mutations_count: number

  // Agent reasoning
  reasoning_trail?: Array<{
    timestamp: ISO8601
    reasoning: string
  }>
}
```

---

## 🔍 Querying Sessions

### By Status

```sql
-- Get all pending review sessions
SELECT * FROM work_sessions
WHERE workspace_id = $1
  AND status = 'pending_review'
ORDER BY completed_at DESC;
```

### By Agent

```sql
-- Get agent's recent sessions
SELECT * FROM work_sessions
WHERE executed_by_agent_id = $1
ORDER BY created_at DESC
LIMIT 10;
```

### By Time Range

```sql
-- Get sessions created in last 7 days
SELECT * FROM work_sessions
WHERE workspace_id = $1
  AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

### With Artifacts

```sql
-- Get session with all artifacts
SELECT
  ws.*,
  json_agg(wa.*) AS artifacts
FROM work_sessions ws
LEFT JOIN work_artifacts wa ON wa.work_session_id = ws.id
WHERE ws.id = $1
GROUP BY ws.id;
```

---

## 📊 Metrics

### Session Metrics

```typescript
interface WorkSessionMetrics {
  // Volume
  totalSessions: number
  sessionsByStatus: Record<WorkSessionStatus, number>

  // Timing
  avgExecutionTimeSeconds: number
  avgReviewTimeSeconds: number
  avgIterations: number

  // Outcomes
  approvalRate: number              // approved / (approved + rejected)
  autoApprovalRate: number          // auto-approved / total
  iterationRate: number             // sessions with iterations / total
  failureRate: number               // failed / total
}
```

### Calculating Metrics

```python
async def calculate_session_metrics(
    workspace_id: UUID,
    time_range: str = "30d"
) -> WorkSessionMetrics:
    start_date = datetime.utcnow() - timedelta(days=30)

    sessions = await db.work_sessions.list(
        workspace_id=workspace_id,
        created_after=start_date
    )

    total = len(sessions)

    metrics = WorkSessionMetrics(
        totalSessions=total,
        sessionsByStatus={
            status: len([s for s in sessions if s.status == status])
            for status in WorkSessionStatus.__members__
        },
        avgExecutionTimeSeconds=_calc_avg_execution_time(sessions),
        avgReviewTimeSeconds=_calc_avg_review_time(sessions),
        avgIterations=_calc_avg_iterations(sessions),
        approvalRate=_calc_approval_rate(sessions),
        autoApprovalRate=_calc_auto_approval_rate(sessions),
        iterationRate=_calc_iteration_rate(sessions),
        failureRate=_calc_failure_rate(sessions)
    )

    return metrics
```

---

## 🚨 Edge Cases & Error Handling

### 1. Session Stuck in `in_progress`

**Scenario**: Agent crashes mid-execution, session never completes.

**Detection**:
```python
# Cron job runs hourly
stuck_sessions = await db.work_sessions.list(
    status="in_progress",
    started_before=datetime.utcnow() - timedelta(hours=4)  # Timeout after 4 hours
)

for session in stuck_sessions:
    await db.work_sessions.update(
        session.id,
        status="failed",
        failure_reason="Execution timeout (4 hours)",
        failed_at=datetime.utcnow()
    )
```

### 2. Orphaned Artifacts

**Scenario**: Artifacts created but session deleted.

**Prevention**: Foreign key constraint with `ON DELETE CASCADE`
```sql
ALTER TABLE work_artifacts
ADD CONSTRAINT fk_work_session
FOREIGN KEY (work_session_id)
REFERENCES work_sessions(id)
ON DELETE CASCADE;
```

### 3. Concurrent Review Attempts

**Scenario**: Two users try to review same session simultaneously.

**Prevention**: Optimistic locking
```python
async def review_work_session(session_id, user_id, decision):
    async with db.transaction():
        # Lock session row
        session = await db.work_sessions.select_for_update(session_id)

        if session.status != "pending_review":
            raise ConflictError(
                f"Session {session_id} is not pending review (status: {session.status})"
            )

        # Proceed with review
        # ...
```

### 4. Exceeding Iteration Limit

**Scenario**: Session hits max iterations.

**Handling**: Force rejection with clear message
```python
if current_iterations >= max_iterations:
    await _handle_rejection(
        session, artifacts,
        f"Exceeded max iterations ({max_iterations}). Task may need reframing or additional context.",
        user_id
    )
```

---

## ✅ Best Practices

### For Frontend

1. **Poll for Status Updates**: Long-running sessions require periodic status checks
2. **Show Progress Indicators**: Display agent reasoning trail in real-time
3. **Enable Cancellation**: Always allow users to cancel active work
4. **Iteration History**: Show complete feedback → revision chain

### For Backend

1. **Atomic State Transitions**: Use database transactions for state changes
2. **Emit Timeline Events**: Every state transition → timeline event
3. **Validate Transitions**: Enforce state machine rules
4. **Timeout Detection**: Background job to detect stuck sessions

### For Agents

1. **Frequent Status Updates**: Update reasoning trail during execution
2. **Graceful Failure**: Report errors clearly with retry guidance
3. **Respect Cancellation**: Check for cancellation requests periodically
4. **Iteration Awareness**: Know which iteration you're on, respect feedback

---

## 📎 See Also

- [ARTIFACT_TYPES_AND_HANDLING.md](./ARTIFACT_TYPES_AND_HANDLING.md) - Artifact specifications
- [CHECKPOINT_STRATEGIES.md](./CHECKPOINT_STRATEGIES.md) - Multi-stage approval workflows
- [YARNNN_UNIFIED_GOVERNANCE.md](../../architecture/YARNNN_UNIFIED_GOVERNANCE.md) - Governance layer
- [YARNNN_DATA_FLOW_V4.md](../../architecture/YARNNN_DATA_FLOW_V4.md) - Complete request flows

---

**Work sessions: From task to substrate in 6 phases. Deterministic, auditable, recoverable.**
