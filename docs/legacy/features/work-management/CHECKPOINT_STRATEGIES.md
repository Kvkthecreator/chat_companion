# Checkpoint Strategies

**Multi-Stage Approval Workflows for Work Sessions**

**Version**: 4.0
**Date**: 2025-10-31
**Status**: ✅ Canonical
**Layer**: 3 (Unified Governance)
**Category**: Feature Specification

---

## 🎯 Overview

Checkpoints enable multi-stage approval workflows where users can review agent work at different phases: plan approval, mid-work review, artifact review, and final approval.

**Key Concepts**:
- Checkpoints are opt-in governance gates
- Different approval strategies enable different checkpoint combinations
- Final approval is always required (cannot be disabled)
- Checkpoints enable iterative feedback without full rejection

---

## 📊 Checkpoint Types

```typescript
type CheckpointType =
  | 'plan_approval'       // Before agent starts work
  | 'mid_work_review'     // During execution (progress check)
  | 'artifact_review'     // Per-artifact review (granular)
  | 'final_approval'      // Before substrate application (always required)
```

---

## 1️⃣ Plan Approval Checkpoint

### Purpose
Review agent's execution plan before work begins.

### When Created
After agent generates execution plan but before actual work.

### Review Context

```typescript
interface PlanApprovalContext {
  plan: {
    approach: string              // High-level strategy
    steps: Array<{
      step_number: number
      description: string
      estimated_duration?: string
    }>
    expected_artifacts: Array<{
      artifact_type: ArtifactType
      description: string
    }>
    context_sources: UUID[]       // Blocks agent will reference
    external_research: boolean    // Will agent search external sources?
  }
  estimated_completion_time?: string
}
```

### Example

```json
{
  "checkpoint_type": "plan_approval",
  "review_context": {
    "plan": {
      "approach": "Research each competitor individually, then synthesize findings",
      "steps": [
        {
          "step_number": 1,
          "description": "Search web for 'Mem AI memory assistant' and extract pricing/features",
          "estimated_duration": "5 minutes"
        },
        {
          "step_number": 2,
          "description": "Search web for 'Rewind AI' and extract pricing/features",
          "estimated_duration": "5 minutes"
        },
        {
          "step_number": 3,
          "description": "Synthesize findings into comparison document",
          "estimated_duration": "3 minutes"
        }
      ],
      "expected_artifacts": [
        {
          "artifact_type": "block_proposal",
          "description": "Mem competitor profile"
        },
        {
          "artifact_type": "block_proposal",
          "description": "Rewind competitor profile"
        },
        {
          "artifact_type": "document_creation",
          "description": "Competitive comparison document"
        }
      ],
      "context_sources": ["block-uuid-existing-research"],
      "external_research": true
    },
    "estimated_completion_time": "15 minutes"
  }
}
```

### User Decision Options

```typescript
type PlanApprovalDecision =
  | 'approve'                     // Proceed with plan
  | 'request_changes'             // Modify plan before proceeding
  | 'reject'                      // Don't execute this plan

interface PlanApprovalFeedback {
  decision: PlanApprovalDecision
  feedback?: string
  requested_changes?: Array<{
    change_type: 'approach' | 'scope' | 'sources' | 'steps'
    description: string
  }>
}
```

### Processing

```python
async def review_plan_checkpoint(
    checkpoint_id: UUID,
    user_id: UUID,
    decision: PlanApprovalFeedback
) -> CheckpointResult:
    """
    Handle plan approval checkpoint review
    """

    checkpoint = await db.work_checkpoints.get(checkpoint_id)
    session = await db.work_sessions.get(checkpoint.work_session_id)

    if decision.decision == 'approve':
        # Plan approved → Agent can start work
        await db.work_checkpoints.update(
            checkpoint_id,
            status='approved',
            reviewed_by=user_id,
            reviewed_at=datetime.utcnow()
        )

        await db.work_sessions.update(
            session.id,
            status='in_progress'
        )

        await notification_service.notify_plan_approved(session)

        return CheckpointResult(status='approved')

    elif decision.decision == 'request_changes':
        # Plan needs revision → Create iteration
        iteration_id = await db.work_iterations.create(
            work_session_id=session.id,
            iteration_number=1,
            triggered_by='plan_feedback',
            user_feedback_text=decision.feedback,
            changes_requested=decision.requested_changes,
            requested_by=user_id
        )

        await db.work_checkpoints.update(
            checkpoint_id,
            status='iteration_requested'
        )

        await db.work_sessions.update(
            session.id,
            status='iteration_requested'
        )

        await notification_service.notify_plan_revision_requested(
            session, decision.requested_changes
        )

        return CheckpointResult(
            status='iteration_requested',
            iteration_id=iteration_id
        )

    elif decision.decision == 'reject':
        # Plan rejected → Session rejected
        await db.work_checkpoints.update(
            checkpoint_id,
            status='rejected'
        )

        await db.work_sessions.update(
            session.id,
            status='rejected',
            rejection_feedback=decision.feedback
        )

        return CheckpointResult(status='rejected')
```

---

## 2️⃣ Mid-Work Review Checkpoint

### Purpose
Check progress during execution without stopping work entirely.

### When Created
At configurable intervals (e.g., after 50% of estimated time, or after N artifacts).

### Review Context

```typescript
interface MidWorkReviewContext {
  progress: {
    steps_completed: number
    total_steps: number
    completion_percentage: number
  }
  artifacts_created_so_far: UUID[]
  current_step: string
  estimated_time_remaining?: string
  issues_encountered?: Array<{
    issue_type: string
    description: string
    resolution: string
  }>
}
```

### User Decision Options

```typescript
type MidWorkDecision =
  | 'continue'                    // Keep going as planned
  | 'adjust_approach'             // Provide feedback, agent adjusts
  | 'cancel'                      // Stop work immediately

interface MidWorkFeedback {
  decision: MidWorkDecision
  feedback?: string
  adjustments?: string[]
}
```

### Processing

```python
async def review_mid_work_checkpoint(
    checkpoint_id: UUID,
    user_id: UUID,
    decision: MidWorkFeedback
) -> CheckpointResult:
    """
    Handle mid-work review checkpoint
    """

    checkpoint = await db.work_checkpoints.get(checkpoint_id)
    session = await db.work_sessions.get(checkpoint.work_session_id)

    if decision.decision == 'continue':
        # User satisfied, agent continues
        await db.work_checkpoints.update(
            checkpoint_id,
            status='approved'
        )

        return CheckpointResult(status='approved')

    elif decision.decision == 'adjust_approach':
        # User provides mid-work guidance
        await db.work_sessions.append_reasoning(
            session.id,
            reasoning_entry={
                "timestamp": datetime.utcnow(),
                "reasoning": f"Mid-work feedback: {decision.feedback}. Adjustments: {decision.adjustments}"
            }
        )

        await db.work_checkpoints.update(
            checkpoint_id,
            status='approved',
            decision=decision
        )

        await notification_service.notify_mid_work_adjustment(
            session, decision.adjustments
        )

        return CheckpointResult(status='adjusted')

    elif decision.decision == 'cancel':
        # User cancels work mid-execution
        await db.work_checkpoints.update(
            checkpoint_id,
            status='rejected'
        )

        await db.work_sessions.update(
            session.id,
            status='cancelled',
            cancelled_by=user_id,
            cancellation_reason=decision.feedback
        )

        return CheckpointResult(status='cancelled')
```

---

## 3️⃣ Artifact Review Checkpoint

### Purpose
Granular per-artifact review before final approval.

### When Created
After each artifact is created (or after batch of artifacts).

### Review Context

```typescript
interface ArtifactReviewContext {
  artifacts: UUID[]               // Artifacts to review in this checkpoint
  total_artifacts_in_session: number
  artifacts_reviewed_so_far: number
}
```

### User Decision Options

```typescript
interface ArtifactReviewDecision {
  artifactDecisions: Record<UUID, ArtifactCheckpointDecision>
}

type ArtifactCheckpointDecision =
  | 'approve'                     // Looks good
  | 'request_revision'            // Needs changes
  | 'reject'                      // Don't include this artifact

interface ArtifactFeedback {
  artifact_id: UUID
  decision: ArtifactCheckpointDecision
  feedback?: string
}
```

### Processing

```python
async def review_artifact_checkpoint(
    checkpoint_id: UUID,
    user_id: UUID,
    decision: ArtifactReviewDecision
) -> CheckpointResult:
    """
    Handle per-artifact review checkpoint
    """

    checkpoint = await db.work_checkpoints.get(checkpoint_id)
    session = await db.work_sessions.get(checkpoint.work_session_id)

    approved_count = 0
    rejected_count = 0
    revision_requested = []

    for artifact_id, artifact_decision in decision.artifactDecisions.items():
        if artifact_decision == 'approve':
            await db.work_artifacts.update(
                artifact_id,
                checkpoint_approved=True
            )
            approved_count += 1

        elif artifact_decision == 'reject':
            await db.work_artifacts.update(
                artifact_id,
                status='rejected',
                checkpoint_rejected=True
            )
            rejected_count += 1

        elif artifact_decision == 'request_revision':
            revision_requested.append(artifact_id)

    await db.work_checkpoints.update(
        checkpoint_id,
        status='approved',
        reviewed_by=user_id,
        decision=decision
    )

    # If revisions requested, create iteration
    if revision_requested:
        iteration_id = await db.work_iterations.create(
            work_session_id=session.id,
            iteration_number=session.current_iteration + 1,
            triggered_by='artifact_feedback',
            artifacts_to_revise=revision_requested,
            requested_by=user_id
        )

        await db.work_sessions.update(
            session.id,
            status='iteration_requested'
        )

        return CheckpointResult(
            status='iteration_requested',
            iteration_id=iteration_id,
            approved_count=approved_count,
            rejected_count=rejected_count
        )

    # All artifacts reviewed
    return CheckpointResult(
        status='approved',
        approved_count=approved_count,
        rejected_count=rejected_count
    )
```

---

## 4️⃣ Final Approval Checkpoint

### Purpose
Review all work before applying to substrate. **Always required.**

### When Created
After agent completes all work (status: `pending_review`).

### Review Context

```typescript
interface FinalApprovalContext {
  artifacts: UUID[]               // All artifacts
  summary: string                 // Agent's summary of work
  reasoning_trail: Array<{
    timestamp: ISO8601
    reasoning: string
  }>
  substrate_impact_summary?: {
    blocks_to_create: number
    blocks_to_update: number
    documents_to_create: number
  }
}
```

### User Decision Options

```typescript
interface FinalApprovalDecision {
  workQuality: 'approved' | 'rejected' | 'needs_revision'
  artifactDecisions?: Record<UUID, ArtifactDecision>
  feedback?: string
  changeRequests?: ChangeRequest[]
}
```

### Processing

This is handled by the **Unified Approval Orchestrator** (see [YARNNN_UNIFIED_GOVERNANCE.md](../../architecture/YARNNN_UNIFIED_GOVERNANCE.md)).

---

## 🎛️ Approval Strategies

Approval strategies determine which checkpoints are enabled.

```typescript
type ApprovalStrategy =
  | 'checkpoint_required'         // All checkpoints enabled
  | 'final_only'                  // Only final approval (default)
  | 'auto_approve_low_risk'       // Auto-approve for trusted agents + low risk
```

### Strategy Configurations

#### 1. Checkpoint Required (Maximum Oversight)

```typescript
const checkpointRequired: WorkspaceApprovalPolicy = {
  defaultStrategy: 'checkpoint_required',

  enablePlanApproval: true,
  enableMidWorkReview: true,
  enableArtifactReview: true,
  finalApprovalRequired: true,

  autoApproveEnabled: false
}
```

**Use Case**: High-stakes work, new agents, sensitive domains.

**Flow**:
```
Task Created → Plan Approval → Work Starts → Mid-Work Review →
Artifacts Created → Artifact Review → Final Approval → Substrate
```

---

#### 2. Final Only (Standard Oversight)

```typescript
const finalOnly: WorkspaceApprovalPolicy = {
  defaultStrategy: 'final_only',

  enablePlanApproval: false,
  enableMidWorkReview: false,
  enableArtifactReview: false,
  finalApprovalRequired: true,

  autoApproveEnabled: false
}
```

**Use Case**: General purpose, balanced oversight.

**Flow**:
```
Task Created → Work Starts → Artifacts Created → Final Approval → Substrate
```

---

#### 3. Auto-Approve Low Risk (Minimal Oversight)

```typescript
const autoApproveLowRisk: WorkspaceApprovalPolicy = {
  defaultStrategy: 'auto_approve_low_risk',

  enablePlanApproval: false,
  enableMidWorkReview: false,
  enableArtifactReview: false,
  finalApprovalRequired: true,  // Still created, but may auto-pass

  autoApproveEnabled: true,
  autoApproveConfidenceMin: 0.9,
  autoApproveAgentApprovalRateMin: 0.85,
  autoApproveRiskLevels: ['low']
}
```

**Use Case**: Trusted agents, routine tasks, high velocity.

**Flow**:
```
Task Created → Work Starts → Artifacts Created →
Auto-Approval Check → [Pass: Substrate] or [Fail: User Review]
```

---

## 📋 Checkpoint Lifecycle

### States

```typescript
type CheckpointStatus =
  | 'pending'                     // Awaiting user review
  | 'approved'                    // User approved
  | 'rejected'                    // User rejected
  | 'iteration_requested'         // User requested changes
  | 'skipped'                     // Checkpoint disabled or auto-passed
```

### State Transitions

```
Created (pending)
   ↓
   ├─→ approved (user approves)
   ├─→ rejected (user rejects)
   ├─→ iteration_requested (user requests changes)
   └─→ skipped (auto-approval or checkpoint disabled)
```

---

## 🔄 Checkpoint Orchestration

### Creating Checkpoints

```python
class CheckpointManager:
    async def create_checkpoint(
        self,
        session: WorkSession,
        checkpoint_type: CheckpointType,
        review_context: dict
    ) -> Optional[Checkpoint]:
        """
        Create checkpoint if enabled by workspace policy
        """

        # Get workspace policy
        policy = await self._get_workspace_policy(session.workspace_id)

        # Check if this checkpoint type is enabled
        if not self._is_checkpoint_enabled(checkpoint_type, policy):
            return None  # Skip checkpoint

        # Create checkpoint record
        checkpoint = await self.db.work_checkpoints.create(
            work_session_id=session.id,
            checkpoint_type=checkpoint_type,
            checkpoint_number=await self._get_next_checkpoint_number(session.id),
            review_context=review_context,
            status='pending',
            created_at=datetime.utcnow()
        )

        # Notify user
        await self.notifications.notify_checkpoint_ready(checkpoint, session)

        return checkpoint

    def _is_checkpoint_enabled(
        self,
        checkpoint_type: CheckpointType,
        policy: WorkspaceApprovalPolicy
    ) -> bool:
        """
        Check if checkpoint type is enabled per policy
        """

        enabled_map = {
            'plan_approval': policy.enablePlanApproval,
            'mid_work_review': policy.enableMidWorkReview,
            'artifact_review': policy.enableArtifactReview,
            'final_approval': True  # Always enabled
        }

        return enabled_map[checkpoint_type]
```

### Checkpoint Waiting

If checkpoint is pending, work session is blocked:

```python
async def can_proceed_to_next_phase(
    session: WorkSession
) -> Tuple[bool, Optional[UUID]]:
    """
    Check if session can proceed (no pending checkpoints)
    """

    pending_checkpoints = await db.work_checkpoints.list(
        work_session_id=session.id,
        status='pending'
    )

    if pending_checkpoints:
        return False, pending_checkpoints[0].id
    else:
        return True, None
```

---

## 📊 Checkpoint Metrics

### Workspace Checkpoint Metrics

```typescript
interface WorkspaceCheckpointMetrics {
  workspace_id: UUID

  // Checkpoint usage
  checkpointsByType: Record<CheckpointType, number>
  avgCheckpointsPerSession: number

  // Outcomes
  approvalRateByCheckpoint: Record<CheckpointType, number>
  iterationRateByCheckpoint: Record<CheckpointType, number>

  // Timing
  avgReviewTimeByCheckpoint: Record<CheckpointType, number>  // Seconds
}
```

### Calculating Metrics

```python
async def calculate_checkpoint_metrics(
    workspace_id: UUID,
    time_range: str = "30d"
) -> WorkspaceCheckpointMetrics:
    start_date = datetime.utcnow() - timedelta(days=30)

    checkpoints = await db.work_checkpoints.list(
        workspace_id=workspace_id,
        created_after=start_date
    )

    metrics = WorkspaceCheckpointMetrics(
        workspace_id=workspace_id,
        checkpointsByType={
            checkpoint_type: len([c for c in checkpoints if c.checkpoint_type == checkpoint_type])
            for checkpoint_type in CheckpointType.__members__
        },
        avgCheckpointsPerSession=_calc_avg_checkpoints_per_session(checkpoints),
        approvalRateByCheckpoint=_calc_approval_rate_by_checkpoint(checkpoints),
        iterationRateByCheckpoint=_calc_iteration_rate_by_checkpoint(checkpoints),
        avgReviewTimeByCheckpoint=_calc_avg_review_time_by_checkpoint(checkpoints)
    )

    return metrics
```

---

## 🎯 Best Practices

### When to Use Each Checkpoint

| Checkpoint | Use When... | Skip When... |
|------------|-------------|--------------|
| **Plan Approval** | Complex tasks, high cost, unfamiliar agent | Routine tasks, trusted agent, clear instructions |
| **Mid-Work Review** | Long-running tasks (>1 hour), external research | Quick tasks, internal context only |
| **Artifact Review** | Critical content, learning new agent behavior | Trusted agent, low-risk artifacts |
| **Final Approval** | Always (cannot be disabled) | Never |

### Checkpoint Fatigue Mitigation

Too many checkpoints → User fatigue → Checkbox approval without real review.

**Strategies**:
1. **Start with fewer checkpoints** (final only), add more only if issues arise
2. **Use auto-approval** for proven agents + low-risk work
3. **Batch artifact reviews** instead of interrupting per artifact
4. **Time-based checkpoints** (mid-work only for tasks >30 min)

---

## 📎 See Also

- [WORK_SESSION_LIFECYCLE.md](./WORK_SESSION_LIFECYCLE.md) - Session states
- [WORKSPACE_POLICIES.md](../governance/WORKSPACE_POLICIES.md) - Policy configuration
- [APPROVAL_WORKFLOWS.md](../governance/APPROVAL_WORKFLOWS.md) - Complete review flows
- [YARNNN_UNIFIED_GOVERNANCE.md](../../architecture/YARNNN_UNIFIED_GOVERNANCE.md) - Governance layer

---

**4 checkpoint types. 3 approval strategies. Configurable oversight without checkpoint fatigue.**
