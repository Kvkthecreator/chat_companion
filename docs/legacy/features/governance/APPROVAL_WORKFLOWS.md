# Approval Workflows

**Complete Review Flows by Approval Strategy**

**Version**: 4.0
**Date**: 2025-10-31
**Status**: ✅ Canonical
**Layer**: 3 (Unified Governance)
**Category**: Feature Specification

---

## 🎯 Overview

This document maps complete approval workflows for each approval strategy, showing the exact sequence of checkpoints, user decisions, and state transitions.

**Key Concepts**:
- Workflows are determined by workspace approval strategy
- Each workflow has different checkpoint gates
- Auto-approval can bypass user review entirely (for eligible work)
- Iterations create feedback loops within workflows

---

## 🔄 Workflow 1: Final Only (Default)

**Strategy**: `final_only`

**Use Case**: Balanced oversight - single review point after work completion.

### Flow Diagram

```
┌─────────────────┐
│ User Creates    │
│ Task            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Work Session    │
│ Status:         │
│ initialized     │
└────────┬────────┘
         │
         │ Agent claims task
         ▼
┌─────────────────┐
│ Agent Starts    │
│ Work            │
│ Status:         │
│ in_progress     │
└────────┬────────┘
         │
         │ Agent retrieves context
         │ Agent performs work
         │ Agent creates artifacts
         ▼
┌─────────────────┐
│ Work Complete   │
│ Status:         │
│ pending_review  │
└────────┬────────┘
         │
         │ Final approval checkpoint created
         ▼
┌─────────────────────────────┐
│ User Reviews Work           │
│ - View artifacts            │
│ - View agent reasoning      │
│ - View risk assessments     │
└────────┬────────────────────┘
         │
         ├──────────────┬──────────────┬─────────────┐
         │              │              │             │
         │ Approve      │ Revision     │ Reject      │
         ▼              ▼              ▼             ▼
┌─────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐
│ Apply       │  │ Create       │  │ Reject   │  │ Cancel   │
│ Artifacts   │  │ Iteration    │  │ Work     │  │ Work     │
│ to Substrate│  │              │  │          │  │          │
└──────┬──────┘  └──────┬───────┘  └──────────┘  └──────────┘
       │                │
       │                │ Agent revises
       │                │
       │                └──────────────┐
       │                               ▼
       │                     ┌─────────────────┐
       │                     │ Agent Creates   │
       │                     │ Revised         │
       │                     │ Artifacts       │
       │                     └────────┬────────┘
       │                              │
       │                              └──► Back to pending_review
       │
       ▼
┌─────────────────┐
│ Work Complete   │
│ Status:         │
│ completed_      │
│ approved        │
└─────────────────┘
```

### Step-by-Step

**Step 1: Task Creation**
```python
# User creates task
session = await create_work_session(
    workspace_id='ws-123',
    basket_id='basket-456',
    task_intent='Research AI memory competitors',
    approval_strategy='final_only'  # Uses workspace default
)
# Status: initialized
```

**Step 2: Agent Execution**
```python
# Agent claims and executes
await update_session_status(session.id, 'in_progress')

# Agent retrieves context
context = await memory_provider.retrieve_context(...)

# Agent creates artifacts
artifact_1 = await create_artifact(
    session_id=session.id,
    artifact_type='block_proposal',
    content={...}
)
artifact_2 = await create_artifact(...)
```

**Step 3: Work Completion**
```python
# Agent marks complete
await update_session_status(session.id, 'pending_review')

# System creates final approval checkpoint
checkpoint = await create_checkpoint(
    session=session,
    checkpoint_type='final_approval',
    review_context={
        'artifacts': [artifact_1.id, artifact_2.id],
        'summary': 'Research completed: 2 competitors analyzed'
    }
)
# Checkpoint status: pending
```

**Step 4: User Review**
```python
# User reviews work
review_data = await get_session_review_data(session.id)
# Returns: session, artifacts, risk assessments, agent metrics

# User decides
decision = WorkReviewDecision(
    workQuality='approved',
    artifactDecisions={
        artifact_1.id: 'apply_to_substrate',
        artifact_2.id: 'apply_to_substrate'
    }
)
```

**Step 5: Approval Processing**
```python
# Unified orchestrator processes
result = await review_work_session(session.id, user_id, decision)

# Result:
# - 2 blocks created in substrate
# - Session status → completed_approved
# - Timeline event created
# - Notifications sent
```

**Checkpoints**: 1 (final approval only)

**Average Duration**: Task creation → Substrate update: 5-30 minutes

---

## 🔐 Workflow 2: Checkpoint Required

**Strategy**: `checkpoint_required`

**Use Case**: Maximum oversight - review at multiple stages.

### Flow Diagram

```
┌─────────────────┐
│ User Creates    │
│ Task            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent Generates │
│ Plan            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CHECKPOINT 1:   │
│ Plan Approval   │
└────────┬────────┘
         │
         ├─── Approved ───┐
         │                │
         └─── Rejected ───┼──► Session Rejected
                          │
                          ▼
                    ┌─────────────────┐
                    │ Agent Starts    │
                    │ Work            │
                    └────────┬────────┘
                             │
                             │ (Executes 50% of plan)
                             ▼
                    ┌─────────────────┐
                    │ CHECKPOINT 2:   │
                    │ Mid-Work Review │
                    └────────┬────────┘
                             │
                             ├─── Continue ───┐
                             │                │
                             └─── Adjust ─────┤
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │ Agent Completes │
                                    │ Work            │
                                    └────────┬────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │ CHECKPOINT 3:   │
                                    │ Artifact Review │
                                    └────────┬────────┘
                                             │
                                             ├─── All Approved ───┐
                                             │                    │
                                             └─── Some Rejected ──┤
                                                                  │
                                                                  ▼
                                                         ┌─────────────────┐
                                                         │ CHECKPOINT 4:   │
                                                         │ Final Approval  │
                                                         └────────┬────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────────┐
                                                         │ Apply to        │
                                                         │ Substrate       │
                                                         └─────────────────┘
```

### Step-by-Step

**Step 1: Plan Approval**
```python
# Agent generates plan
plan = await generate_execution_plan(task_intent)

# Checkpoint 1 created
checkpoint_1 = await create_checkpoint(
    session=session,
    checkpoint_type='plan_approval',
    review_context={'plan': plan}
)

# User reviews plan
await review_checkpoint(
    checkpoint_1.id,
    user_id,
    PlanApprovalDecision(decision='approve')
)
# Agent can now start work
```

**Step 2: Mid-Work Review**
```python
# After 50% progress
checkpoint_2 = await create_checkpoint(
    session=session,
    checkpoint_type='mid_work_review',
    review_context={
        'progress': {
            'steps_completed': 3,
            'total_steps': 6,
            'completion_percentage': 50
        },
        'artifacts_created_so_far': [artifact_1.id]
    }
)

# User reviews progress
await review_checkpoint(
    checkpoint_2.id,
    user_id,
    MidWorkDecision(decision='continue')
)
# Agent continues
```

**Step 3: Artifact Review**
```python
# After each artifact batch
checkpoint_3 = await create_checkpoint(
    session=session,
    checkpoint_type='artifact_review',
    review_context={
        'artifacts': [artifact_1.id, artifact_2.id]
    }
)

# User reviews each artifact
await review_checkpoint(
    checkpoint_3.id,
    user_id,
    ArtifactReviewDecision(
        artifactDecisions={
            artifact_1.id: 'approve',
            artifact_2.id: 'approve'
        }
    )
)
```

**Step 4: Final Approval**
```python
# Same as final_only workflow
checkpoint_4 = await create_checkpoint(
    session=session,
    checkpoint_type='final_approval',
    review_context={...}
)

await review_work_session(session.id, user_id, decision)
```

**Checkpoints**: 4 (plan, mid-work, artifact, final)

**Average Duration**: Task creation → Substrate update: 1-4 hours (due to multiple reviews)

---

## ⚡ Workflow 3: Auto-Approve Low Risk

**Strategy**: `auto_approve_low_risk`

**Use Case**: High velocity - bypass review for trusted agents.

### Flow Diagram

```
┌─────────────────┐
│ User Creates    │
│ Task            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent Executes  │
│ Work            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Work Complete   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Auto-Approval Eligibility Check │
└────────┬────────────────────────┘
         │
         ├──────────────┬─────────────┐
         │              │             │
         │ Eligible     │ Not Eligible│
         ▼              ▼             │
┌─────────────┐  ┌──────────────┐   │
│ Auto-Approve│  │ User Review  │   │
│ + Apply to  │  │ Required     │───┘
│ Substrate   │  └──────────────┘
└─────────────┘         │
         │              │
         └──────┬───────┘
                ▼
       ┌─────────────────┐
       │ Work Complete   │
       │ Status:         │
       │ completed_      │
       │ approved        │
       └─────────────────┘
```

### Auto-Approval Eligibility Rules

```python
async def evaluate_auto_approval_eligibility(
    session: WorkSession,
    artifacts: List[WorkArtifact],
    policy: WorkspaceApprovalPolicy
) -> AutoApprovalEvaluation:
    """
    Check if work session qualifies for auto-approval
    """

    if not policy.autoApproveEnabled:
        return AutoApprovalEvaluation(
            eligible=False,
            reason='Auto-approval disabled for workspace'
        )

    # Rule 1: All artifacts must be within allowed risk levels
    all_allowed_risk = all(
        a.risk_level in policy.autoApproveRiskLevels
        for a in artifacts
    )

    if not all_allowed_risk:
        high_risk_artifacts = [
            a for a in artifacts
            if a.risk_level not in policy.autoApproveRiskLevels
        ]
        return AutoApprovalEvaluation(
            eligible=False,
            reason=f'{len(high_risk_artifacts)} artifacts exceed allowed risk levels'
        )

    # Rule 2: Agent confidence must exceed threshold
    min_confidence = min(
        a.agent_confidence for a in artifacts if a.agent_confidence
    )

    if min_confidence < policy.autoApproveConfidenceMin:
        return AutoApprovalEvaluation(
            eligible=False,
            reason=f'Min confidence {min_confidence:.2f} below threshold {policy.autoApproveConfidenceMin:.2f}'
        )

    # Rule 3: Agent track record must exceed threshold
    agent_metrics = await get_agent_performance(
        session.executed_by_agent_id
    )

    if agent_metrics.approval_rate < policy.autoApproveAgentApprovalRateMin:
        return AutoApprovalEvaluation(
            eligible=False,
            reason=f'Agent approval rate {agent_metrics.approval_rate:.0%} below threshold'
        )

    # All rules passed
    return AutoApprovalEvaluation(
        eligible=True,
        reason='All auto-approval criteria met'
    )
```

### Step-by-Step

**Step 1-2: Same as final_only**
```python
# Task created, agent executes, work completed
# Status: pending_review
```

**Step 3: Auto-Approval Check**
```python
# System evaluates eligibility
evaluation = await evaluate_auto_approval_eligibility(
    session, artifacts, policy
)

if evaluation.eligible:
    # Auto-approve
    result = await auto_approve_work_session(session, artifacts)

    # Notify user of auto-approval
    await notify_work_auto_approved(session, result.substrateChanges)

    # Status: completed_approved (user never saw it)
else:
    # Fall back to user review
    checkpoint = await create_checkpoint(
        session=session,
        checkpoint_type='final_approval',
        review_context={...}
    )
    # User must review
```

**Checkpoints**: 0-1 (final approval only if auto-approval fails)

**Average Duration**: Task creation → Substrate update: 2-10 minutes (no user wait)

---

## 🔁 Iteration Workflows

Iterations create feedback loops within any workflow.

### Iteration Flow

```
┌─────────────────┐
│ User Reviews    │
│ Work            │
└────────┬────────┘
         │
         │ Decision: needs_revision
         ▼
┌─────────────────────────────┐
│ Create Iteration Record     │
│ - iteration_number          │
│ - changes_requested         │
│ - user_feedback_text        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│ Session Status: │
│ iteration_      │
│ requested       │
└────────┬────────┘
         │
         │ Agent notified
         ▼
┌─────────────────┐
│ Agent Fetches   │
│ Feedback        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent Revises   │
│ Work            │
│ (creates new    │
│ artifacts)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Session Status: │
│ pending_review  │
│ (again)         │
└────────┬────────┘
         │
         └──► Back to user review
```

### Iteration Limits

```python
# Check iteration limit before creating iteration
if session.current_iteration >= policy.maxIterationsPerSession:
    # Force rejection
    await handle_rejection(
        session, artifacts,
        f"Exceeded max iterations ({policy.maxIterationsPerSession}). "
        "Task may need reframing.",
        user_id
    )
else:
    # Create iteration
    iteration = await create_iteration(...)
```

---

## 📊 Workflow Metrics

### Workflow Performance

```typescript
interface WorkflowMetrics {
  strategy: ApprovalStrategy

  // Sessions
  totalSessions: number
  avgSessionDuration: number        // Minutes

  // Checkpoints
  avgCheckpointsPerSession: number
  checkpointApprovalRate: Record<CheckpointType, number>

  // Outcomes
  finalApprovalRate: number
  iterationRate: number
  avgIterations: number

  // Auto-approval (if applicable)
  autoApprovalRate?: number
  autoApprovalPrecision?: number    // % not later reverted
}
```

### Comparative Analysis

| Metric | Final Only | Checkpoint Required | Auto-Approve Low Risk |
|--------|-----------|---------------------|----------------------|
| **Checkpoints/Session** | 1 | 4 | 0-1 |
| **Avg Duration** | 15 min | 2 hrs | 5 min |
| **User Burden** | Low | High | Very Low |
| **Oversight Level** | Medium | High | Low |
| **Iteration Rate** | 15% | 8% | 10% |
| **Approval Rate** | 85% | 92% | 95% |
| **Substrate Quality** | Good | Excellent | Good |

---

## 🎯 Workflow Selection Guide

### Decision Tree

```
Is this mission-critical content?
├─ Yes → checkpoint_required
└─ No
    │
    ├─ Do you have proven agents (>50 sessions, >85% approval)?
    │  ├─ Yes → auto_approve_low_risk
    │  └─ No → final_only
    │
    └─ Is velocity more important than oversight?
       ├─ Yes → auto_approve_low_risk (accept risk)
       └─ No → final_only
```

### Recommendations

**Use checkpoint_required when**:
- Legal/compliance documentation
- Financial data
- New untested agents
- High-stakes content
- Learning agent behavior patterns

**Use final_only when**:
- General purpose workspaces
- Mixed agent experience levels
- Moderate-stakes content
- Balanced velocity + oversight

**Use auto_approve_low_risk when**:
- Trusted agents with track records
- Internal team knowledge bases
- Rapid prototyping
- Low-stakes content
- Velocity is critical

---

## 📎 See Also

- [CHECKPOINT_STRATEGIES.md](../work-management/CHECKPOINT_STRATEGIES.md) - Checkpoint types
- [WORKSPACE_POLICIES.md](./WORKSPACE_POLICIES.md) - Policy configuration
- [RISK_ASSESSMENT.md](./RISK_ASSESSMENT.md) - Risk calculation
- [WORK_SESSION_LIFECYCLE.md](../work-management/WORK_SESSION_LIFECYCLE.md) - Session states

---

**3 workflows. From maximum oversight to high velocity. Choose based on trust + stakes.**
