# Workspace Governance Policies

**Per-Workspace Configuration for Unified Governance**

**Version**: 4.0
**Date**: 2025-10-31
**Status**: ✅ Canonical
**Layer**: 3 (Unified Governance)
**Category**: Feature Specification

---

## 🎯 Overview

Workspace governance policies control how agent work is reviewed and approved. Each workspace can configure its own policies, enabling different oversight levels for different use cases.

**Key Concepts**:
- Policies are per-workspace (isolated by RLS)
- Policies control checkpoint enablement, auto-approval rules, iteration limits
- Policy changes affect future work sessions, not in-flight ones
- Admins can update policies, regular members use configured policies

---

## 📋 Policy Schema

```typescript
interface WorkspaceApprovalPolicy {
  workspace_id: UUID

  // Default approval strategy
  defaultStrategy: ApprovalStrategy

  // Checkpoint configuration
  enablePlanApproval: boolean
  enableMidWorkReview: boolean
  enableArtifactReview: boolean
  finalApprovalRequired: boolean  // Always true (cannot disable)

  // Auto-approval rules
  autoApproveEnabled: boolean
  autoApproveConfidenceMin: number        // 0-1, default: 0.9
  autoApproveAgentApprovalRateMin: number // 0-1, default: 0.85
  autoApproveRiskLevels: RiskLevel[]      // Default: ['low']

  // Iteration limits
  maxIterationsPerSession: number  // Default: 3

  // Metadata
  updated_at: ISO8601
  updated_by: UUID
}

type ApprovalStrategy =
  | 'checkpoint_required'         // All checkpoints enabled
  | 'final_only'                  // Only final approval (default)
  | 'auto_approve_low_risk'       // Auto-approve for trusted agents

type RiskLevel = 'low' | 'medium' | 'high'
```

---

## 🎛️ Policy Presets

### 1. Maximum Oversight (Paranoid Mode)

```typescript
const maximumOversight: WorkspaceApprovalPolicy = {
  defaultStrategy: 'checkpoint_required',

  // All checkpoints enabled
  enablePlanApproval: true,
  enableMidWorkReview: true,
  enableArtifactReview: true,
  finalApprovalRequired: true,

  // No auto-approval
  autoApproveEnabled: false,

  // Conservative iteration limit
  maxIterationsPerSession: 2
}
```

**Use Cases**:
- Mission-critical knowledge bases
- Legal/compliance documentation
- Financial data
- New agents being tested

**Trade-offs**:
- ✅ Maximum control and visibility
- ✅ Catch issues early (plan approval)
- ❌ High user burden (many reviews)
- ❌ Slow execution (multiple approval gates)

---

### 2. Balanced (Default)

```typescript
const balanced: WorkspaceApprovalPolicy = {
  defaultStrategy: 'final_only',

  // Only final approval
  enablePlanApproval: false,
  enableMidWorkReview: false,
  enableArtifactReview: false,
  finalApprovalRequired: true,

  // No auto-approval (yet)
  autoApproveEnabled: false,

  // Standard iteration limit
  maxIterationsPerSession: 3
}
```

**Use Cases**:
- General-purpose workspaces
- Mixed teams (trusted + new agents)
- Moderate-stakes content

**Trade-offs**:
- ✅ Single review point (user-friendly)
- ✅ Still maintains control (final approval)
- ✅ Flexible iterations (up to 3)
- ❌ No early feedback (plan not reviewed)

---

### 3. High Velocity (Trusted Agents)

```typescript
const highVelocity: WorkspaceApprovalPolicy = {
  defaultStrategy: 'auto_approve_low_risk',

  // Skip intermediate checkpoints
  enablePlanApproval: false,
  enableMidWorkReview: false,
  enableArtifactReview: false,
  finalApprovalRequired: true,  // Still required, but may auto-pass

  // Aggressive auto-approval
  autoApproveEnabled: true,
  autoApproveConfidenceMin: 0.85,          // Lower threshold
  autoApproveAgentApprovalRateMin: 0.80,   // Lower threshold
  autoApproveRiskLevels: ['low', 'medium'], // Include medium risk

  // Generous iteration limit
  maxIterationsPerSession: 5
}
```

**Use Cases**:
- Proven agents with track records
- Internal team knowledge bases
- Rapid prototyping/experimentation
- Low-stakes content

**Trade-offs**:
- ✅ Minimal user burden (auto-approval common)
- ✅ Fast execution (no waiting)
- ✅ Generous iterations (5 attempts)
- ❌ Less oversight (trust required)
- ❌ Potential substrate pollution (if agent misbehaves)

---

## 🔧 Policy Configuration

### Database Schema

```sql
CREATE TABLE workspace_approval_policies (
    workspace_id UUID PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,

    -- Default strategy
    default_strategy TEXT NOT NULL DEFAULT 'final_only',

    -- Checkpoint configuration
    enable_plan_approval BOOLEAN NOT NULL DEFAULT FALSE,
    enable_mid_work_review BOOLEAN NOT NULL DEFAULT FALSE,
    enable_artifact_review BOOLEAN NOT NULL DEFAULT FALSE,
    final_approval_required BOOLEAN NOT NULL DEFAULT TRUE,

    -- Auto-approval rules
    auto_approve_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    auto_approve_confidence_min NUMERIC NOT NULL DEFAULT 0.9,
    auto_approve_agent_approval_rate_min NUMERIC NOT NULL DEFAULT 0.85,
    auto_approve_risk_levels TEXT[] NOT NULL DEFAULT ARRAY['low'],

    -- Iteration limits
    max_iterations_per_session INTEGER NOT NULL DEFAULT 3,

    -- Metadata
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

-- RLS policies
ALTER TABLE workspace_approval_policies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view policies for their workspaces"
ON workspace_approval_policies
FOR SELECT
TO authenticated
USING (
    workspace_id IN (
        SELECT workspace_id
        FROM workspace_members
        WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Admins can update policies for their workspaces"
ON workspace_approval_policies
FOR UPDATE
TO authenticated
USING (
    workspace_id IN (
        SELECT workspace_id
        FROM workspace_members
        WHERE user_id = auth.uid()
          AND role IN ('admin', 'owner')
    )
);
```

---

## 📡 API Endpoints

### Get Workspace Policy

**GET** `/api/governance/workspaces/{workspace_id}/policy`

**Response**:
```json
{
  "policy": {
    "workspace_id": "ws-123",
    "defaultStrategy": "final_only",
    "enablePlanApproval": false,
    "enableMidWorkReview": false,
    "enableArtifactReview": false,
    "finalApprovalRequired": true,
    "autoApproveEnabled": false,
    "autoApproveConfidenceMin": 0.9,
    "autoApproveAgentApprovalRateMin": 0.85,
    "autoApproveRiskLevels": ["low"],
    "maxIterationsPerSession": 3,
    "updated_at": "2025-01-15T10:30:00Z",
    "updated_by": "user-456"
  }
}
```

---

### Update Workspace Policy

**PUT** `/api/governance/workspaces/{workspace_id}/policy`

**Request Body**:
```json
{
  "policy": {
    "defaultStrategy": "auto_approve_low_risk",
    "autoApproveEnabled": true,
    "autoApproveConfidenceMin": 0.85,
    "autoApproveRiskLevels": ["low", "medium"]
  }
}
```

**Response**:
```json
{
  "policy": {
    "workspace_id": "ws-123",
    "defaultStrategy": "auto_approve_low_risk",
    "autoApproveEnabled": true,
    "autoApproveConfidenceMin": 0.85,
    "autoApproveRiskLevels": ["low", "medium"],
    ...
  }
}
```

---

### Apply Preset

**POST** `/api/governance/workspaces/{workspace_id}/policy/apply-preset`

**Request Body**:
```json
{
  "preset": "maximum_oversight"
}
```

**Presets Available**:
- `maximum_oversight`
- `balanced`
- `high_velocity`

---

## 🔄 Policy Application

### When Policies Are Applied

Policies are **evaluated at checkpoint creation time**, not at work session creation:

```python
async def create_checkpoint(
    session: WorkSession,
    checkpoint_type: CheckpointType
) -> Optional[Checkpoint]:
    """
    Checkpoints respect policy at creation time
    """

    # Fetch current policy
    policy = await db.workspace_approval_policies.get(session.workspace_id)

    # Check if checkpoint type is enabled
    if not _is_checkpoint_enabled(checkpoint_type, policy):
        return None  # Skip checkpoint

    # Create checkpoint
    checkpoint = await db.work_checkpoints.create(
        work_session_id=session.id,
        checkpoint_type=checkpoint_type,
        status='pending',
        policy_snapshot=policy  # Store policy at creation time
    )

    return checkpoint
```

**Why snapshot policy?**
- Prevents mid-flight policy changes from affecting in-progress work
- Audit trail shows which policy was active at checkpoint creation
- Users can change policy without breaking active sessions

---

### Policy Evolution Strategy

**Recommended Progression**:

```
New Workspace → Balanced (final_only)
    ↓ (After 10+ approved sessions)
High Velocity (auto_approve_low_risk, low only)
    ↓ (After 50+ approved sessions, 90%+ approval rate)
High Velocity (auto_approve_low_risk, low + medium)
```

**Rollback Strategy**:
- If approval rate drops below 80%, revert to Balanced
- If critical error (substrate corruption), revert to Maximum Oversight temporarily

---

## 📊 Policy Metrics

### Workspace Policy Performance

```typescript
interface WorkspacePolicyMetrics {
  workspace_id: UUID
  current_policy: WorkspaceApprovalPolicy

  // Session outcomes
  sessionApprovalRate: number          // Approved / Total
  artifactApprovalRate: number         // Applied to substrate / Total artifacts
  avgIterationsPerSession: number

  // Auto-approval effectiveness
  autoApprovalRate: number             // Auto-approved / Total
  autoApprovalPrecision: number        // Auto-approved sessions that weren't later reverted

  // User burden
  avgReviewTimeSeconds: number
  checkpointsPerSession: number

  // Substrate quality
  postApprovalRevertRate: number       // Approved work later reverted / Total
}
```

### Calculating Metrics

```python
async def calculate_policy_metrics(
    workspace_id: UUID,
    time_range: str = "30d"
) -> WorkspacePolicyMetrics:
    """
    Calculate policy performance metrics
    """

    start_date = datetime.utcnow() - timedelta(days=30)

    # Fetch all sessions in time range
    sessions = await db.work_sessions.list(
        workspace_id=workspace_id,
        created_after=start_date
    )

    # Calculate metrics
    total_sessions = len(sessions)
    approved_sessions = len([s for s in sessions if s.status == 'completed_approved'])
    auto_approved = len([s for s in sessions if s.auto_approved])

    metrics = WorkspacePolicyMetrics(
        workspace_id=workspace_id,
        current_policy=await db.workspace_approval_policies.get(workspace_id),
        sessionApprovalRate=approved_sessions / total_sessions if total_sessions > 0 else 0,
        autoApprovalRate=auto_approved / total_sessions if total_sessions > 0 else 0,
        avgReviewTimeSeconds=_calc_avg_review_time(sessions),
        checkpointsPerSession=_calc_avg_checkpoints(sessions),
        postApprovalRevertRate=await _calc_revert_rate(workspace_id, start_date)
    )

    return metrics
```

---

## 🎯 Policy Recommendations

### Recommendation Engine

```python
async def recommend_policy_adjustments(
    workspace_id: UUID
) -> List[PolicyRecommendation]:
    """
    Suggest policy changes based on metrics
    """

    metrics = await calculate_policy_metrics(workspace_id)
    policy = await db.workspace_approval_policies.get(workspace_id)

    recommendations = []

    # Recommendation 1: Enable auto-approval
    if (
        not policy.autoApproveEnabled
        and metrics.sessionApprovalRate > 0.90
        and metrics.avgIterationsPerSession < 1.5
    ):
        recommendations.append(PolicyRecommendation(
            type='enable_auto_approval',
            priority='medium',
            reasoning='High approval rate (>90%) and low iterations. Auto-approval could reduce review burden.',
            impact=f'Estimated {metrics.sessionApprovalRate * 0.7:.0%} of sessions could auto-approve',
            suggested_changes={
                'autoApproveEnabled': True,
                'autoApproveRiskLevels': ['low']
            }
        ))

    # Recommendation 2: Increase auto-approval threshold
    if (
        policy.autoApproveEnabled
        and policy.autoApproveRiskLevels == ['low']
        and metrics.autoApprovalPrecision > 0.95
    ):
        recommendations.append(PolicyRecommendation(
            type='expand_auto_approval',
            priority='low',
            reasoning='Excellent auto-approval precision (>95%). Medium-risk artifacts may be safe to auto-approve.',
            impact=f'Could increase auto-approval rate from {metrics.autoApprovalRate:.0%} to ~{metrics.autoApprovalRate * 1.3:.0%}',
            suggested_changes={
                'autoApproveRiskLevels': ['low', 'medium']
            }
        ))

    # Recommendation 3: Add checkpoints
    if (
        policy.defaultStrategy == 'final_only'
        and metrics.avgIterationsPerSession > 2
    ):
        recommendations.append(PolicyRecommendation(
            type='add_checkpoints',
            priority='high',
            reasoning='High iteration rate (>2 per session). Plan approval could catch issues earlier.',
            impact=f'Estimated {metrics.avgIterationsPerSession * 0.5:.1f} fewer iterations per session',
            suggested_changes={
                'enablePlanApproval': True
            }
        ))

    # Recommendation 4: Reduce checkpoints
    if (
        policy.enablePlanApproval
        and policy.enableMidWorkReview
        and policy.enableArtifactReview
        and metrics.sessionApprovalRate > 0.90
    ):
        recommendations.append(PolicyRecommendation(
            type='reduce_checkpoints',
            priority='medium',
            reasoning='High approval rate with many checkpoints. May be causing review fatigue.',
            impact=f'Reduce checkpoint burden from {metrics.checkpointsPerSession:.1f} to ~2 per session',
            suggested_changes={
                'enableMidWorkReview': False,
                'enableArtifactReview': False
            }
        ))

    return recommendations
```

---

## 🔒 Security & Authorization

### Who Can Update Policies

Only workspace admins/owners can update policies:

```python
async def validate_policy_update_authorization(
    workspace_id: UUID,
    user_id: UUID
) -> bool:
    """
    Check if user can update workspace policy
    """

    membership = await db.workspace_members.get(
        workspace_id=workspace_id,
        user_id=user_id
    )

    if not membership:
        raise Forbidden("User not member of workspace")

    if membership.role not in ['admin', 'owner']:
        raise Forbidden("Only admins/owners can update governance policies")

    return True
```

### Policy Change Audit Trail

All policy changes are logged:

```python
async def update_workspace_policy(
    workspace_id: UUID,
    user_id: UUID,
    policy_updates: dict
) -> WorkspaceApprovalPolicy:
    """
    Update policy with audit trail
    """

    # Validate authorization
    await validate_policy_update_authorization(workspace_id, user_id)

    # Get old policy
    old_policy = await db.workspace_approval_policies.get(workspace_id)

    # Update policy
    new_policy = await db.workspace_approval_policies.update(
        workspace_id,
        **policy_updates,
        updated_at=datetime.utcnow(),
        updated_by=user_id
    )

    # Log change in timeline
    await timeline_service.emit_policy_change_event(
        workspace_id=workspace_id,
        old_policy=old_policy,
        new_policy=new_policy,
        changed_by=user_id
    )

    return new_policy
```

---

## 📎 See Also

- [CHECKPOINT_STRATEGIES.md](../work-management/CHECKPOINT_STRATEGIES.md) - Checkpoint types
- [APPROVAL_WORKFLOWS.md](./APPROVAL_WORKFLOWS.md) - Complete review flows
- [RISK_ASSESSMENT.md](./RISK_ASSESSMENT.md) - Risk calculation
- [YARNNN_UNIFIED_GOVERNANCE.md](../../architecture/YARNNN_UNIFIED_GOVERNANCE.md) - Governance layer

---

**3 presets. Per-workspace configuration. Policy metrics. Recommendation engine. Workspace-level governance control.**
