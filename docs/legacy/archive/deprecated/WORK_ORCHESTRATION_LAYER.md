# Work Orchestration Layer (Layer 2) Implementation

**Status**: ✅ Schema Complete, Models Complete, Core Orchestrator Complete
**Date**: 2025-10-31
**Migration**: `20251031_work_orchestration_layer.sql` (Applied)

---

## Overview

The Work Orchestration Layer adds agent work management capabilities to YARNNN, transforming it from a pure "Context OS" into an integrated "AI Work Platform" where context management enables superior agent work supervision.

### Core Philosophy

**Single Approval → Dual Effect**

- User reviews **work quality** (reasoning, completeness, accuracy)
- Approved artifacts are **automatically applied to substrate**
- No redundant double-approval (work + substrate separately)

---

## Architecture

### Layer Structure

```
YARNNN Core Service
├── Layer 1: Substrate Core (blocks, documents, search) [EXISTING]
├── Layer 2: Work Orchestration [NEW]
│   ├── Work Sessions
│   ├── Work Artifacts
│   ├── Work Checkpoints
│   ├── Work Iterations
│   └── Context Mutations
└── Layer 3: Unified Governance [NEW]
    └── Single approval for work quality + substrate mutation
```

---

## Database Schema

### Tables Created

1. **`work_sessions`** - Track agent work execution
2. **`work_artifacts`** - Outputs of agent work
3. **`work_checkpoints`** - Multi-stage approval workflow
4. **`work_iterations`** - Feedback loops and revisions
5. **`work_context_mutations`** - Audit trail of substrate changes

### Key Design Decisions

#### 1. Work Session Links to Agent SDK

```sql
work_sessions (
  executed_by_agent_id text,     -- Agent SDK agent_id
  agent_session_id text           -- Agent SDK execution session (traceability)
)
```

**Purpose**: Link YARNNN work sessions to Agent SDK execution sessions for debugging and audit trails.

#### 2. Artifact Types

```sql
artifact_type IN (
  'block_proposal',        -- Will become block in substrate
  'block_update',          -- Will supersede existing block
  'document_creation',     -- Will create document
  'insight',               -- Reflection/insight
  'external_deliverable'   -- External file (no substrate impact)
)
```

**Purpose**: Not all work outputs become substrate. External deliverables (reports, spreadsheets) are tracked but don't mutate context.

#### 3. Substrate Linkage (After Approval)

```sql
work_artifacts (
  becomes_block_id uuid,        -- Populated after applied to substrate
  supersedes_block_id uuid,     -- For block updates
  creates_document_id uuid      -- For document creations
)
```

**Purpose**: Work artifacts exist before substrate application. Links are populated during unified approval.

#### 4. Multi-Checkpoint Support

```sql
work_checkpoints (
  checkpoint_sequence integer,
  checkpoint_type IN ('plan_approval', 'mid_work_review', 'artifact_review', 'final_approval')
)
```

**Purpose**: Enable iterative supervision with multiple approval points, not just final review.

---

## Python Models

### Location

```
api/src/app/work/models/
├── __init__.py
├── work_session.py           # WorkSession, WorkSessionStatus, etc.
├── work_artifact.py          # WorkArtifact, WorkArtifactType, etc.
├── work_checkpoint.py        # WorkCheckpoint, WorkCheckpointType, etc.
├── work_iteration.py         # WorkIteration, WorkIterationTrigger
└── work_context_mutation.py  # WorkContextMutation, WorkMutationType
```

### Key Models

#### WorkSession

```python
class WorkSession(BaseModel):
    id: UUID
    workspace_id: UUID
    basket_id: UUID
    initiated_by_user_id: UUID
    executed_by_agent_id: Optional[str]
    agent_session_id: Optional[str]  # Links to Agent SDK

    task_intent: str
    task_type: TaskType  # research, synthesis, analysis, composition, update
    task_document_id: Optional[UUID]  # P4 context envelope

    status: WorkSessionStatus  # initialized → in_progress → approved/rejected
    approval_strategy: WorkSessionApprovalStrategy  # checkpoint_required, final_only, auto_approve_low_risk

    artifacts_count: int
    substrate_mutations_count: int
```

#### WorkArtifact

```python
class WorkArtifact(BaseModel):
    id: UUID
    work_session_id: UUID
    artifact_type: WorkArtifactType
    content: Dict[str, Any]

    # Substrate linkage (populated after approval)
    becomes_block_id: Optional[UUID]
    supersedes_block_id: Optional[UUID]
    creates_document_id: Optional[UUID]

    agent_confidence: Optional[float]
    agent_reasoning: Optional[str]
    source_context_ids: List[UUID]  # Which blocks informed this

    status: WorkArtifactStatus  # draft → pending_review → approved → applied_to_substrate
    risk_level: Optional[RiskLevel]
```

---

## Unified Governance Orchestrator

### Location

```
api/src/app/governance/
├── __init__.py
└── unified_approval.py  # UnifiedApprovalOrchestrator
```

### Core Flow

```python
async def review_work_session(
    work_session_id: UUID,
    user_id: UUID,
    decision: WorkReviewDecision,
) -> WorkReviewResult:
    """
    Single approval with dual effect:
    1. Work quality assessment
    2. Substrate application
    """

    # Step 1: Check work quality
    if decision.work_quality != "approved":
        reject_entire_session()
        return WorkReviewResult(status="rejected")

    # Step 2: Per-artifact decisions
    for artifact in artifacts:
        if decision.artifacts[artifact.id] == "apply_to_substrate":
            # THIS IS WHERE SUBSTRATE GOVERNANCE HAPPENS
            if artifact.type == "block_proposal":
                block = create_block(state="ACCEPTED")  # Direct acceptance
                log_context_mutation()

            elif artifact.type == "block_update":
                new_block = supersede_block(state="ACCEPTED")
                log_context_mutation()

            elif artifact.type == "document_creation":
                doc = create_document(state="PUBLISHED")
                log_context_mutation()

        elif decision.artifacts[artifact.id] == "save_as_draft":
            mark_approved_but_dont_apply()

        elif decision.artifacts[artifact.id] == "reject":
            reject_artifact()

    # Step 3: Update session status
    complete_work_session(status="approved")

    # Step 4: Emit timeline event
    emit_work_completion_event()

    return WorkReviewResult(artifacts_applied=X, substrate_mutations=[...])
```

### Key Insight: Direct Substrate Application

**Work was already reviewed** → Blocks go straight to `ACCEPTED` state

No separate block proposal governance needed. The work review IS the substrate governance.

---

## RLS & Security

### Workspace-Scoped Access

All work orchestration tables enforce workspace membership:

```sql
CREATE POLICY "Users can view work sessions in their workspaces"
  ON work_sessions FOR SELECT
  USING (
    workspace_id IN (
      SELECT workspace_id FROM workspace_memberships WHERE user_id = auth.uid()
    )
  );
```

### Grants

- `service_role`: Full access (for API backend)
- `authenticated`: SELECT, INSERT, UPDATE (via RLS)
- `anon`: No access (must be authenticated)

---

## Triggers & Auto-Counters

### 1. Updated Timestamp

```sql
CREATE TRIGGER trigger_update_work_session_timestamp
  BEFORE UPDATE ON work_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_work_session_timestamp();
```

### 2. Artifact Counter

```sql
CREATE TRIGGER trigger_increment_artifacts_count
  AFTER INSERT ON work_artifacts
  FOR EACH ROW
  EXECUTE FUNCTION increment_work_session_artifacts_count();
```

Updates `work_sessions.artifacts_count` automatically.

### 3. Mutation Counter

```sql
CREATE TRIGGER trigger_increment_mutations_count
  AFTER INSERT ON work_context_mutations
  FOR EACH ROW
  EXECUTE FUNCTION increment_work_session_mutations_count();
```

Updates `work_sessions.substrate_mutations_count` automatically.

---

## Agent SDK Integration

### Session Linking

**Agent SDK → YARNNN**:
```python
# Agent SDK starts work
agent_session = AgentSession(
    id="session_abc123",
    task_id="work_session_xyz"  # YARNNN work session ID
)
```

**YARNNN → Agent SDK**:
```sql
-- YARNNN tracks which agent session executed the work
work_sessions (
  agent_session_id = "session_abc123"
)
```

**Bidirectional link** enables traceability.

### YarnnnGovernance Provider

```python
class YarnnnGovernance(GovernanceProvider):
    async def propose(self, changes, confidence, reasoning):
        # Creates work artifact (not direct block proposal)
        response = await self.client.post(
            f"/api/work/sessions/{self.work_session_id}/artifacts",
            json={
                'artifact_type': 'block_proposal',
                'content': changes,
                'agent_confidence': confidence,
                'agent_reasoning': reasoning,
                'metadata': {
                    'agent_session_id': self.agent_session_id
                }
            }
        )
        return Proposal(id=response['artifact_id'], status='pending_work_review')
```

**Key**: Agent SDK doesn't directly create blocks. It creates artifacts that await work review.

---

## Next Steps

### Immediate (Required for MVP)

1. **API Endpoints** (`/api/work/sessions`, `/api/work/artifacts`, etc.)
2. **Work Session Manager** (orchestrate session lifecycle)
3. **Risk Assessment** (calculate artifact risk levels)
4. **Timeline Integration** (emit events on work completion)

### Future Enhancements

1. **Checkpoint Strategies** (configurable per-user or per-agent)
2. **Agent Track Record** (trust calibration based on approval history)
3. **Context Mutation Limits** (safety thresholds)
4. **Work Management UI** (frontend for reviewing work sessions)

---

## Migration Applied

**File**: `supabase/migrations/20251031_work_orchestration_layer.sql`

**Status**: ✅ Applied to database

**Tables Created**:
- `work_sessions`
- `work_artifacts`
- `work_checkpoints`
- `work_iterations`
- `work_context_mutations`

**Verify**:
```sql
\dt work_*
```

**Output**:
```
 public | work_artifacts         | table
 public | work_checkpoints       | table
 public | work_context_mutations | table
 public | work_iterations        | table
 public | work_sessions          | table
```

---

## Summary

✅ **Layer 2 (Work Orchestration) Complete**
- 5 tables created with RLS, triggers, indexes
- Python models for all entities
- Unified governance orchestrator implemented

🔄 **Next Phase**:
- API routes for work session management
- Integration with existing substrate governance
- Frontend work review UI

**This implementation transforms YARNNN from "Context OS" to "AI Work Platform" while maintaining clean architectural boundaries.**
