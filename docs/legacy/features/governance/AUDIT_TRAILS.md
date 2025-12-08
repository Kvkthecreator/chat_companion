# Audit Trails

**Complete Provenance Tracking from Task to Substrate**

**Version**: 4.0
**Date**: 2025-10-31
**Status**: ✅ Canonical
**Layer**: 1 (Substrate Core) + 2 (Work Orchestration) + 3 (Governance)
**Category**: Feature Specification

---

## 🎯 Overview

YARNNN provides complete provenance tracking for every substrate entity. Users can trace any block back to the work session, artifacts, agent reasoning, and governance decisions that created it.

**Key Concepts**:
- Every substrate change has an audit trail
- Provenance is first-class (not an afterthought)
- Timeline events provide append-only activity stream
- Work context mutations link work → substrate changes

---

## 🔗 Provenance Chain

### Complete Lineage

```
User Task
  ↓
Work Session
  ↓
Agent Reasoning Trail
  ↓
Work Artifacts
  ↓
Governance Review
  ↓
Substrate Entities (Blocks/Documents)
```

### Example Trace

```typescript
// Starting from a block
const block = await getBlock('block-uuid-123')

// Trace back to work artifact
const artifact = await getWorkArtifact(block.metadata.work_artifact_id)

// Trace back to work session
const session = await getWorkSession(artifact.work_session_id)

// Trace back to user
const user = await getUser(session.initiated_by_user_id)

// Complete lineage
console.log(`
Block: ${block.id}
  ← Created from artifact: ${artifact.id}
  ← In work session: ${session.id}
  ← Task: "${session.task_intent}"
  ← Initiated by: ${user.name}
  ← Executed by agent: ${session.executed_by_agent_id}
  ← Agent reasoning: ${artifact.agent_reasoning}
  ← User approved: ${session.approved_by} at ${session.approved_at}
`)
```

---

## 📊 Audit Trail Tables

### 1. Work Sessions

**Purpose**: Track agent execution lifecycle.

```sql
CREATE TABLE work_sessions (
    id UUID PRIMARY KEY,
    workspace_id UUID NOT NULL,
    basket_id UUID NOT NULL,

    -- Task definition
    task_intent TEXT NOT NULL,
    task_type TEXT,
    task_document_id UUID,

    -- Execution
    initiated_by_user_id UUID NOT NULL,
    executed_by_agent_id TEXT,
    agent_session_id TEXT,              -- Links to Agent SDK

    -- Lifecycle
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Governance
    approval_strategy TEXT,
    approved_at TIMESTAMPTZ,
    approved_by UUID,
    rejected_at TIMESTAMPTZ,
    rejected_by UUID,
    rejection_feedback TEXT,

    -- Reasoning
    reasoning_trail JSONB[],            -- Agent's thought process

    -- Metrics
    artifacts_count INTEGER DEFAULT 0,
    substrate_mutations_count INTEGER DEFAULT 0
);
```

**Audit Value**: Complete record of who requested what work, which agent executed, and outcome.

---

### 2. Work Artifacts

**Purpose**: Track agent outputs before substrate application.

```sql
CREATE TABLE work_artifacts (
    id UUID PRIMARY KEY,
    work_session_id UUID NOT NULL REFERENCES work_sessions(id),

    -- Content
    artifact_type TEXT NOT NULL,
    content JSONB NOT NULL,

    -- Agent metadata
    agent_confidence NUMERIC,
    agent_reasoning TEXT,
    source_context_ids UUID[],          -- Blocks used for reasoning

    -- Governance
    status TEXT NOT NULL,
    risk_level TEXT,

    -- Substrate linkage (after approval)
    becomes_block_id UUID,              -- Created block
    supersedes_block_id UUID,           -- Superseded block
    creates_document_id UUID,           -- Created document

    created_at TIMESTAMPTZ NOT NULL
);
```

**Audit Value**: Shows what agent proposed before approval. Enables "what was the agent thinking?" queries.

---

### 3. Work Context Mutations

**Purpose**: Audit trail linking work artifacts → substrate changes.

```sql
CREATE TABLE work_context_mutations (
    id UUID PRIMARY KEY,
    work_session_id UUID NOT NULL REFERENCES work_sessions(id),
    work_artifact_id UUID NOT NULL REFERENCES work_artifacts(id),

    -- Mutation details
    mutation_type TEXT NOT NULL,        -- block_created | block_updated | document_created | etc.
    target_block_id UUID,
    target_document_id UUID,

    -- Governance
    applied_by UUID NOT NULL,           -- User who approved
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Optional: Revert tracking
    reverted BOOLEAN DEFAULT FALSE,
    reverted_at TIMESTAMPTZ,
    reverted_by UUID,
    revert_reason TEXT
);
```

**Audit Value**: Complete record of which work artifacts caused which substrate changes.

---

### 4. Timeline Events

**Purpose**: Append-only activity stream capturing all system events.

```sql
CREATE TABLE timeline_events (
    id UUID PRIMARY KEY,
    workspace_id UUID NOT NULL,
    basket_id UUID,

    -- Event details
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL,

    -- Actor
    actor_type TEXT NOT NULL,           -- user | agent | system
    actor_id UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_timeline_workspace_time
ON timeline_events(workspace_id, created_at DESC);

CREATE INDEX idx_timeline_event_type
ON timeline_events(event_type);
```

**Event Types**:
- `work_session_created`
- `work_session_started`
- `work_session_completed`
- `work_session_approved`
- `work_session_rejected`
- `iteration_requested`
- `checkpoint_created`
- `checkpoint_reviewed`
- `block_created`
- `block_updated`
- `block_locked`
- `document_created`
- `policy_changed`
- `workspace_member_added`

**Audit Value**: Complete chronological history of all workspace activity.

---

### 5. Blocks (with provenance metadata)

**Purpose**: Substrate entities with embedded provenance.

```sql
CREATE TABLE blocks (
    id UUID PRIMARY KEY,
    workspace_id UUID NOT NULL,
    basket_id UUID NOT NULL,

    -- Content
    content JSONB NOT NULL,
    block_type TEXT,
    state TEXT NOT NULL,                -- ACCEPTED | PROPOSED | REJECTED | SUPERSEDED

    -- Provenance (embedded in metadata)
    metadata JSONB,
    -- metadata.work_session_id
    -- metadata.work_artifact_id
    -- metadata.agent_confidence
    -- metadata.created_by_agent
    -- metadata.approved_by_user

    -- Versioning
    supersedes UUID REFERENCES blocks(id),
    superseded_by UUID REFERENCES blocks(id),
    superseded_at TIMESTAMPTZ,

    -- Timestamps
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ
);
```

**Audit Value**: Every block carries provenance in metadata. Can trace to work session without JOIN.

---

## 🔍 Provenance Queries

### Query 1: Block → Work Session

```sql
-- Given a block, find the work session that created it
SELECT
    ws.*,
    u.name AS initiated_by_name,
    approver.name AS approved_by_name
FROM blocks b
INNER JOIN work_artifacts wa ON wa.becomes_block_id = b.id
INNER JOIN work_sessions ws ON ws.id = wa.work_session_id
LEFT JOIN users u ON u.id = ws.initiated_by_user_id
LEFT JOIN users approver ON approver.id = ws.approved_by
WHERE b.id = $1;
```

### Query 2: Work Session → All Substrate Changes

```sql
-- Given a work session, find all substrate changes
SELECT
    wcm.mutation_type,
    wcm.target_block_id,
    b.content,
    b.created_at,
    wcm.applied_by,
    u.name AS applied_by_name
FROM work_context_mutations wcm
LEFT JOIN blocks b ON b.id = wcm.target_block_id
LEFT JOIN users u ON u.id = wcm.applied_by
WHERE wcm.work_session_id = $1
ORDER BY wcm.applied_at ASC;
```

### Query 3: User → All Approved Work

```sql
-- Find all work approved by a specific user
SELECT
    ws.id,
    ws.task_intent,
    ws.approved_at,
    ws.artifacts_count,
    ws.substrate_mutations_count,
    COUNT(wcm.id) AS mutations_applied
FROM work_sessions ws
LEFT JOIN work_context_mutations wcm ON wcm.work_session_id = ws.id
WHERE ws.approved_by = $1
  AND ws.status = 'completed_approved'
GROUP BY ws.id
ORDER BY ws.approved_at DESC;
```

### Query 4: Agent → Track Record

```sql
-- Calculate agent performance metrics
SELECT
    ws.executed_by_agent_id,
    COUNT(*) AS total_sessions,
    COUNT(*) FILTER (WHERE ws.status = 'completed_approved') AS approved,
    COUNT(*) FILTER (WHERE ws.status = 'rejected') AS rejected,
    AVG(wa.agent_confidence) AS avg_confidence,
    COUNT(wcm.id) AS total_mutations
FROM work_sessions ws
LEFT JOIN work_artifacts wa ON wa.work_session_id = ws.id
LEFT JOIN work_context_mutations wcm ON wcm.work_session_id = ws.id
WHERE ws.executed_by_agent_id = $1
GROUP BY ws.executed_by_agent_id;
```

### Query 5: Workspace → Timeline

```sql
-- Complete activity timeline for workspace
SELECT
    te.event_type,
    te.event_data,
    te.actor_type,
    u.name AS actor_name,
    te.created_at
FROM timeline_events te
LEFT JOIN users u ON u.id = te.actor_id
WHERE te.workspace_id = $1
ORDER BY te.created_at DESC
LIMIT 50;
```

---

## 📋 Provenance API Endpoints

### Get Block Provenance

**GET** `/api/substrate/blocks/{block_id}/provenance`

**Response**:
```json
{
  "block": {
    "id": "block-uuid-123",
    "content": {...},
    "created_at": "2025-01-15T10:30:00Z"
  },
  "provenance": {
    "work_session_id": "session-uuid-456",
    "work_artifact_id": "artifact-uuid-789",
    "task_intent": "Research AI memory competitors",
    "executed_by_agent_id": "claude-opus-20250115",
    "agent_confidence": 0.95,
    "agent_reasoning": "Verified from official sources",
    "initiated_by_user_id": "user-uuid-abc",
    "initiated_by_user_name": "Alice",
    "approved_by_user_id": "user-uuid-def",
    "approved_by_user_name": "Bob",
    "approved_at": "2025-01-15T10:45:00Z",
    "source_context_ids": ["block-uuid-100", "block-uuid-101"]
  }
}
```

---

### Get Work Session Audit Trail

**GET** `/api/work/sessions/{session_id}/audit-trail`

**Response**:
```json
{
  "session": {
    "id": "session-uuid-456",
    "task_intent": "Research AI memory competitors",
    "status": "completed_approved"
  },
  "timeline": [
    {
      "timestamp": "2025-01-15T10:00:00Z",
      "event": "session_created",
      "actor": "user-uuid-abc",
      "details": "Task created by Alice"
    },
    {
      "timestamp": "2025-01-15T10:05:00Z",
      "event": "session_started",
      "actor": "claude-opus-20250115",
      "details": "Agent started work"
    },
    {
      "timestamp": "2025-01-15T10:10:00Z",
      "event": "artifact_created",
      "actor": "claude-opus-20250115",
      "details": "Artifact 1: block_proposal (confidence: 0.95)"
    },
    {
      "timestamp": "2025-01-15T10:15:00Z",
      "event": "artifact_created",
      "actor": "claude-opus-20250115",
      "details": "Artifact 2: block_proposal (confidence: 0.92)"
    },
    {
      "timestamp": "2025-01-15T10:20:00Z",
      "event": "session_completed",
      "actor": "claude-opus-20250115",
      "details": "Work completed, 2 artifacts created"
    },
    {
      "timestamp": "2025-01-15T10:45:00Z",
      "event": "session_approved",
      "actor": "user-uuid-def",
      "details": "Approved by Bob, 2 blocks created"
    }
  ],
  "artifacts": [
    {
      "id": "artifact-uuid-789",
      "type": "block_proposal",
      "risk_level": "low",
      "becomes_block_id": "block-uuid-123",
      "status": "applied_to_substrate"
    },
    {
      "id": "artifact-uuid-790",
      "type": "block_proposal",
      "risk_level": "medium",
      "becomes_block_id": "block-uuid-124",
      "status": "applied_to_substrate"
    }
  ],
  "substrate_changes": [
    {
      "mutation_type": "block_created",
      "target_block_id": "block-uuid-123",
      "applied_by": "user-uuid-def",
      "applied_at": "2025-01-15T10:45:00Z"
    },
    {
      "mutation_type": "block_created",
      "target_block_id": "block-uuid-124",
      "applied_by": "user-uuid-def",
      "applied_at": "2025-01-15T10:45:00Z"
    }
  ]
}
```

---

### Get User Approval History

**GET** `/api/governance/users/{user_id}/approval-history`

**Response**:
```json
{
  "user": {
    "id": "user-uuid-def",
    "name": "Bob"
  },
  "metrics": {
    "totalApprovals": 42,
    "totalRejections": 8,
    "approvalRate": 0.84,
    "avgReviewTimeSeconds": 180,
    "substrateChangesApproved": 120
  },
  "recent_approvals": [
    {
      "session_id": "session-uuid-456",
      "task_intent": "Research AI memory competitors",
      "approved_at": "2025-01-15T10:45:00Z",
      "artifacts_approved": 2,
      "blocks_created": 2
    },
    ...
  ]
}
```

---

## 🔄 Revert Support

### Recording Reverts

```sql
-- When user reverts approved work
UPDATE work_context_mutations
SET
    reverted = TRUE,
    reverted_at = NOW(),
    reverted_by = $1,
    revert_reason = $2
WHERE work_session_id = $3;

-- Mark reverted blocks as SUPERSEDED
UPDATE blocks
SET
    state = 'SUPERSEDED',
    superseded_at = NOW()
WHERE id IN (
    SELECT target_block_id
    FROM work_context_mutations
    WHERE work_session_id = $3
);

-- Emit timeline event
INSERT INTO timeline_events (
    workspace_id,
    event_type,
    event_data,
    actor_type,
    actor_id
) VALUES (
    $workspace_id,
    'work_reverted',
    jsonb_build_object(
        'session_id', $session_id,
        'reason', $revert_reason
    ),
    'user',
    $user_id
);
```

### Query Reverted Work

```sql
-- Find work that was approved but later reverted
SELECT
    ws.*,
    wcm.reverted_at,
    wcm.revert_reason,
    reverter.name AS reverted_by_name
FROM work_sessions ws
INNER JOIN work_context_mutations wcm ON wcm.work_session_id = ws.id
LEFT JOIN users reverter ON reverter.id = wcm.reverted_by
WHERE wcm.reverted = TRUE
ORDER BY wcm.reverted_at DESC;
```

---

## 📊 Audit Metrics

### Governance Audit Metrics

```typescript
interface GovernanceAuditMetrics {
  workspace_id: UUID
  time_range: string

  // Decision volume
  totalApprovals: number
  totalRejections: number
  totalIterations: number
  totalReverts: number

  // Decision distribution
  approvalsByUser: Record<UUID, number>
  rejectionsByUser: Record<UUID, number>

  // Quality indicators
  revertRate: number                    // Reverts / Approvals
  iterationRate: number                 // Sessions with iterations / Total
  avgReviewTimeSeconds: number

  // Provenance coverage
  blocksWithProvenance: number
  blocksWithoutProvenance: number       // Should be 0
}
```

### Calculating Metrics

```python
async def calculate_governance_audit_metrics(
    workspace_id: UUID,
    time_range: str = "30d"
) -> GovernanceAuditMetrics:
    start_date = datetime.utcnow() - timedelta(days=30)

    # Count approvals
    approvals = await db.work_sessions.count(
        workspace_id=workspace_id,
        status='completed_approved',
        approved_at_after=start_date
    )

    # Count rejections
    rejections = await db.work_sessions.count(
        workspace_id=workspace_id,
        status='rejected',
        rejected_at_after=start_date
    )

    # Count reverts
    reverts = await db.work_context_mutations.count(
        workspace_id=workspace_id,
        reverted=True,
        reverted_at_after=start_date
    )

    # Provenance coverage
    total_blocks = await db.blocks.count(
        workspace_id=workspace_id,
        created_after=start_date
    )

    blocks_with_provenance = await db.blocks.count(
        workspace_id=workspace_id,
        created_after=start_date,
        metadata_contains={'work_session_id': None}  # Has this key
    )

    return GovernanceAuditMetrics(
        workspace_id=workspace_id,
        time_range=time_range,
        totalApprovals=approvals,
        totalRejections=rejections,
        totalReverts=reverts,
        revertRate=reverts / approvals if approvals > 0 else 0,
        blocksWithProvenance=blocks_with_provenance,
        blocksWithoutProvenance=total_blocks - blocks_with_provenance
    )
```

---

## 🔒 Audit Log Retention

### Retention Policy

```python
# Audit logs are append-only and retained indefinitely by default
# Workspace admins can configure retention

class AuditRetentionPolicy:
    # Timeline events
    timeline_retention_days: int = 365 * 5  # 5 years

    # Work sessions (completed)
    work_sessions_retention_days: int = 365 * 3  # 3 years

    # Work artifacts
    work_artifacts_retention_days: int = 365 * 2  # 2 years

    # Work context mutations (never delete - critical provenance)
    work_mutations_retention_days: int = None  # Infinite

    # Reverted work (keep longer for forensics)
    reverted_work_retention_days: int = 365 * 5  # 5 years
```

### Archival Process

```python
async def archive_old_audit_logs(workspace_id: UUID):
    """
    Move old logs to cold storage (S3, Glacier, etc.)
    """

    policy = await get_retention_policy(workspace_id)

    # Archive old timeline events
    cutoff_date = datetime.utcnow() - timedelta(
        days=policy.timeline_retention_days
    )

    old_events = await db.timeline_events.list(
        workspace_id=workspace_id,
        created_before=cutoff_date
    )

    # Move to cold storage
    await archive_to_s3(old_events, f"workspace_{workspace_id}/timeline")

    # Delete from hot database
    await db.timeline_events.delete_many(
        workspace_id=workspace_id,
        created_before=cutoff_date
    )
```

---

## 📎 See Also

- [WORK_SESSION_LIFECYCLE.md](../work-management/WORK_SESSION_LIFECYCLE.md) - Session states
- [ARTIFACT_TYPES_AND_HANDLING.md](../work-management/ARTIFACT_TYPES_AND_HANDLING.md) - Artifact types
- [YARNNN_UNIFIED_GOVERNANCE.md](../../architecture/YARNNN_UNIFIED_GOVERNANCE.md) - Governance layer
- [TIMELINE_AND_NOTIFICATIONS.md](../integrations/TIMELINE_AND_NOTIFICATIONS.md) - Event stream

---

**Complete provenance. Every block traces to task, agent, reasoning, approval. Audit-ready from day one.**
