# YARNNN Unified Governance Architecture

**Layer 3: Technical Implementation of Work + Substrate Governance**

**Version**: 4.0
**Date**: 2025-10-31
**Status**: ✅ Canonical
**Layer**: 3 (Unified Governance)
**Supersedes**: Substrate-only governance (v3.1)

---

## 🎯 Overview

This document provides the technical specification for YARNNN's **Unified Governance Layer** (Layer 3), which implements the philosophical principles defined in [YARNNN_GOVERNANCE_PHILOSOPHY_V4.md](../canon/YARNNN_GOVERNANCE_PHILOSOPHY_V4.md).

**Core Responsibility**: Orchestrate single-approval workflows that simultaneously assess work quality AND manage substrate integrity.

**Key Innovation**: Users review work quality once. The system automatically handles substrate mutations for approved artifacts.

---

## 🏗️ Architecture Overview

### Layer Position

```
┌─────────────────────────────────────────────┐
│ Layer 4: Presentation                       │
│ - Work Review UI                            │
│ - Notifications                             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Layer 3: UNIFIED GOVERNANCE ← YOU ARE HERE  │
│ - UnifiedApprovalOrchestrator               │
│ - Risk Assessment Engine                    │
│ - Checkpoint Manager                        │
│ - Auto-Approval Engine                      │
│ - Trust Calibration                         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Layer 2: Work Orchestration                 │
│ - Work Sessions, Artifacts, Checkpoints     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Layer 1: Substrate Core                     │
│ - Blocks, Documents, Timeline               │
└─────────────────────────────────────────────┘
```

### Core Components

```typescript
// Unified Governance Layer Components
export const Layer3Components = {
  orchestration: {
    UnifiedApprovalOrchestrator: "Single approval → dual effect coordinator",
    CheckpointManager: "Multi-stage approval workflow orchestrator",
    IterationCoordinator: "Feedback loop handler"
  },

  assessment: {
    RiskAssessmentEngine: "Calculate artifact risk levels",
    ConfidenceCalibrator: "Compare claimed vs. actual confidence",
    NoveltyDetector: "Identify new vs. confirming content"
  },

  automation: {
    AutoApprovalEngine: "Trusted agent bypass for low-risk work",
    TrustCalibrator: "Track agent performance and adjust thresholds",
    PolicyEvaluator: "Workspace-specific governance rules"
  },

  enforcement: {
    SubstrateMutationGuard: "Ensure only approved artifacts mutate substrate",
    GovernanceAuditor: "Log all governance decisions",
    ViolationDetector: "Catch unauthorized substrate changes"
  }
}
```

---

## 🎭 Component 1: Unified Approval Orchestrator

### Purpose

Coordinate the single-review workflow that handles both work quality assessment and substrate mutation application.

### Core Interface

```typescript
interface UnifiedApprovalOrchestrator {
  /**
   * Main entry point: User reviews work session
   *
   * @param sessionId - Work session to review
   * @param userId - Reviewing user
   * @param decision - User's approval/rejection decision with per-artifact choices
   * @returns Review result with substrate changes applied
   */
  reviewWorkSession(
    sessionId: UUID,
    userId: UUID,
    decision: WorkReviewDecision
  ): Promise<WorkReviewResult>

  /**
   * Handle checkpoint reviews (plan, mid-work, artifact)
   */
  reviewCheckpoint(
    checkpointId: UUID,
    userId: UUID,
    decision: CheckpointDecision
  ): Promise<CheckpointResult>

  /**
   * Revert previously approved work (undo substrate changes)
   */
  revertApprovedWork(
    sessionId: UUID,
    userId: UUID,
    reason: string
  ): Promise<RevertResult>
}
```

### Decision Models

```typescript
// User's review decision
interface WorkReviewDecision {
  // Overall work quality assessment
  workQuality: 'approved' | 'rejected' | 'needs_revision'

  // Optional: Per-artifact decisions (granular control)
  artifactDecisions?: Record<UUID, ArtifactDecision>

  // Feedback for rejected/revision work
  feedback?: string

  // For 'needs_revision': Structured change requests
  changeRequests?: ChangeRequest[]
}

// Per-artifact decision
type ArtifactDecision =
  | 'apply_to_substrate'      // Create/update block in substrate
  | 'approve_only'            // Good work, but no substrate impact (e.g., external deliverable)
  | 'reject'                  // Don't apply, provide feedback
  | 'defer'                   // Review later

// Structured change request for iterations
interface ChangeRequest {
  artifactId?: UUID           // Specific artifact (optional)
  requestType: 'approach' | 'focus' | 'data_quality' | 'scope'
  description: string
  priority: 'critical' | 'important' | 'nice_to_have'
}
```

### Result Models

```typescript
interface WorkReviewResult {
  status: 'approved' | 'rejected' | 'iteration_requested'

  // If approved: Substrate mutations applied
  substrateChanges?: SubstrateChangesSummary

  // If rejected: Reason captured
  rejectionReason?: string

  // If iteration requested: New iteration created
  iterationId?: UUID

  // Timeline event created
  timelineEventId: UUID

  // Notifications sent
  notificationsSent: NotificationSummary[]
}

interface SubstrateChangesSummary {
  blocksCreated: UUID[]
  blocksUpdated: UUID[]
  blocksLocked: UUID[]
  documentsCreated: UUID[]
  mutationsApplied: number
}
```

### Implementation Pattern

```python
class UnifiedApprovalOrchestrator:
    def __init__(
        self,
        db: Database,
        risk_engine: RiskAssessmentEngine,
        checkpoint_manager: CheckpointManager,
        auto_approval_engine: AutoApprovalEngine,
        timeline_service: TimelineService,
        notification_service: NotificationService
    ):
        self.db = db
        self.risk_engine = risk_engine
        self.checkpoint_manager = checkpoint_manager
        self.auto_approval = auto_approval_engine
        self.timeline = timeline_service
        self.notifications = notification_service

    async def review_work_session(
        self,
        session_id: UUID,
        user_id: UUID,
        decision: WorkReviewDecision
    ) -> WorkReviewResult:
        """
        Single user review → Dual effect (work + substrate)
        """

        # Step 1: Load work session + artifacts
        session = await self._load_work_session(session_id)
        artifacts = await self._load_artifacts(session_id)

        # Step 2: Validate user authorization
        await self._validate_reviewer(session, user_id)

        # Step 3: Handle rejection
        if decision.work_quality == 'rejected':
            return await self._handle_rejection(
                session, artifacts, decision.feedback, user_id
            )

        # Step 4: Handle iteration request
        if decision.work_quality == 'needs_revision':
            return await self._handle_iteration_request(
                session, artifacts, decision.change_requests, user_id
            )

        # Step 5: Handle approval → DUAL EFFECT
        return await self._handle_approval(
            session, artifacts, decision.artifact_decisions, user_id
        )

    async def _handle_approval(
        self,
        session: WorkSession,
        artifacts: List[WorkArtifact],
        artifact_decisions: Optional[Dict[UUID, ArtifactDecision]],
        user_id: UUID
    ) -> WorkReviewResult:
        """
        Approval logic: Work approved AND artifacts → substrate
        """

        substrate_changes = SubstrateChangesSummary(
            blocksCreated=[],
            blocksUpdated=[],
            blocksLocked=[],
            documentsCreated=[],
            mutationsApplied=0
        )

        async with self.db.transaction():
            # Process each artifact
            for artifact in artifacts:
                decision = self._get_artifact_decision(
                    artifact, artifact_decisions
                )

                if decision == 'apply_to_substrate':
                    # CORE PATTERN: Apply artifact → substrate in ACCEPTED state
                    substrate_id = await self._apply_artifact_to_substrate(
                        artifact, session, user_id
                    )

                    # Track what changed
                    if artifact.artifact_type == 'block_proposal':
                        substrate_changes.blocksCreated.append(substrate_id)
                    elif artifact.artifact_type == 'block_update_proposal':
                        substrate_changes.blocksUpdated.append(substrate_id)
                    elif artifact.artifact_type == 'document_creation':
                        substrate_changes.documentsCreated.append(substrate_id)

                    substrate_changes.mutationsApplied += 1

                    # Create work_context_mutations record
                    await self._record_substrate_mutation(
                        session, artifact, substrate_id, user_id
                    )

                elif decision == 'approve_only':
                    # Artifact approved but no substrate impact
                    await self._mark_artifact_approved(artifact, user_id)

                elif decision == 'reject':
                    # Artifact rejected, no substrate impact
                    await self._mark_artifact_rejected(artifact, user_id)

            # Update work session status
            await self._complete_work_session(
                session, approved=True, user_id=user_id
            )

            # Update agent track record
            await self._update_agent_track_record(
                session.executed_by_agent_id, approved=True
            )

            # Emit timeline event
            timeline_event_id = await self.timeline.emit_work_completion_event(
                session, artifacts, substrate_changes, user_id
            )

            # Send notifications
            notifications = await self.notifications.notify_work_approved(
                session, substrate_changes, user_id
            )

        return WorkReviewResult(
            status='approved',
            substrateChanges=substrate_changes,
            timelineEventId=timeline_event_id,
            notificationsSent=notifications
        )

    async def _apply_artifact_to_substrate(
        self,
        artifact: WorkArtifact,
        session: WorkSession,
        user_id: UUID
    ) -> UUID:
        """
        CRITICAL: Work already reviewed → Block goes to ACCEPTED state directly

        This is the key difference from v3.1:
        - v3.1: Block proposal → PROPOSED → User reviews proposal → ACCEPTED
        - v4.0: Artifact reviewed → Block created in ACCEPTED state
        """

        if artifact.artifact_type == 'block_proposal':
            # Create block in ACCEPTED state (no separate proposal governance)
            block_id = await self.db.blocks.create(
                workspace_id=session.workspace_id,
                basket_id=session.basket_id,
                content=artifact.content['block_content'],
                block_type=artifact.content.get('block_type', 'note'),
                metadata={
                    'work_session_id': str(session.id),
                    'work_artifact_id': str(artifact.id),
                    'agent_confidence': artifact.agent_confidence,
                    'created_by_agent': session.executed_by_agent_id,
                    'approved_by_user': str(user_id)
                },
                state='ACCEPTED',  # ← Direct to ACCEPTED
                created_by=user_id,
                created_at=datetime.utcnow()
            )

            # Link artifact → block
            await self.db.work_artifacts.update(
                artifact.id,
                becomes_block_id=block_id,
                status='applied_to_substrate'
            )

            return block_id

        elif artifact.artifact_type == 'block_update_proposal':
            # Supersede existing block
            old_block_id = artifact.content['supersedes_block_id']

            # Create new version in ACCEPTED state
            new_block_id = await self.db.blocks.supersede(
                old_block_id=old_block_id,
                new_content=artifact.content['new_content'],
                supersession_reason=artifact.agent_reasoning,
                created_by=user_id,
                metadata={
                    'work_session_id': str(session.id),
                    'work_artifact_id': str(artifact.id)
                }
            )

            # Link artifact → new block
            await self.db.work_artifacts.update(
                artifact.id,
                becomes_block_id=new_block_id,
                supersedes_block_id=old_block_id,
                status='applied_to_substrate'
            )

            return new_block_id

        elif artifact.artifact_type == 'document_creation':
            # Create document
            doc_id = await self.db.documents.create(
                workspace_id=session.workspace_id,
                basket_id=session.basket_id,
                title=artifact.content['title'],
                content_blocks=artifact.content['content_blocks'],
                document_type=artifact.content.get('document_type', 'composition'),
                metadata={
                    'work_session_id': str(session.id),
                    'work_artifact_id': str(artifact.id)
                },
                created_by=user_id
            )

            await self.db.work_artifacts.update(
                artifact.id,
                creates_document_id=doc_id,
                status='applied_to_substrate'
            )

            return doc_id

        else:
            raise ValueError(f"Unknown artifact type: {artifact.artifact_type}")

    async def _handle_rejection(
        self,
        session: WorkSession,
        artifacts: List[WorkArtifact],
        feedback: Optional[str],
        user_id: UUID
    ) -> WorkReviewResult:
        """
        Rejection: No substrate changes, feedback captured
        """

        async with self.db.transaction():
            # Mark session rejected
            await self.db.work_sessions.update(
                session.id,
                status='rejected',
                rejection_feedback=feedback,
                rejected_by=user_id,
                rejected_at=datetime.utcnow()
            )

            # Mark all artifacts rejected
            for artifact in artifacts:
                await self.db.work_artifacts.update(
                    artifact.id,
                    status='rejected'
                )

            # Update agent track record
            await self._update_agent_track_record(
                session.executed_by_agent_id, approved=False
            )

            # Emit timeline event
            timeline_event_id = await self.timeline.emit_work_rejection_event(
                session, feedback, user_id
            )

            # Notify agent/user
            notifications = await self.notifications.notify_work_rejected(
                session, feedback, user_id
            )

        return WorkReviewResult(
            status='rejected',
            rejectionReason=feedback,
            timelineEventId=timeline_event_id,
            notificationsSent=notifications
        )

    async def _handle_iteration_request(
        self,
        session: WorkSession,
        artifacts: List[WorkArtifact],
        change_requests: List[ChangeRequest],
        user_id: UUID
    ) -> WorkReviewResult:
        """
        Iteration: Create feedback loop for agent to revise work
        """

        # Check iteration limit
        current_iterations = await self.db.work_iterations.count(
            work_session_id=session.id
        )

        max_iterations = await self._get_workspace_max_iterations(
            session.workspace_id
        )

        if current_iterations >= max_iterations:
            # Hit iteration limit → Force rejection
            return await self._handle_rejection(
                session,
                artifacts,
                f"Exceeded max iterations ({max_iterations}). Please reframe task.",
                user_id
            )

        async with self.db.transaction():
            # Create iteration record
            iteration_id = await self.db.work_iterations.create(
                work_session_id=session.id,
                iteration_number=current_iterations + 1,
                triggered_by='user_feedback',
                user_feedback_text=self._format_change_requests(change_requests),
                changes_requested=change_requests,
                requested_by=user_id,
                created_at=datetime.utcnow()
            )

            # Update session status
            await self.db.work_sessions.update(
                session.id,
                status='iteration_requested',
                current_iteration=current_iterations + 1
            )

            # Emit timeline event
            timeline_event_id = await self.timeline.emit_iteration_requested_event(
                session, iteration_id, change_requests, user_id
            )

            # Notify agent to revise
            notifications = await self.notifications.notify_iteration_requested(
                session, change_requests, user_id
            )

        return WorkReviewResult(
            status='iteration_requested',
            iterationId=iteration_id,
            timelineEventId=timeline_event_id,
            notificationsSent=notifications
        )
```

---

## 🎲 Component 2: Risk Assessment Engine

### Purpose

Calculate risk levels for work artifacts based on multiple factors to inform user review prioritization and auto-approval eligibility.

### Risk Levels

```typescript
type RiskLevel = 'low' | 'medium' | 'high'

// Risk calculation factors
interface RiskFactors {
  mutationType: MutationType
  agentConfidence: number
  contextImpact: number
  agentTrackRecord: AgentPerformanceMetrics
  noveltyScore: number
}

interface RiskCalculation {
  finalRisk: RiskLevel
  baseRisk: RiskLevel
  modifiers: RiskModifier[]
  reasoning: string
}
```

### Risk Algorithm

```python
class RiskAssessmentEngine:
    """
    Calculate artifact risk using multi-factor assessment
    """

    async def assess_artifact_risk(
        self,
        artifact: WorkArtifact,
        session: WorkSession
    ) -> RiskCalculation:
        """
        Main entry point: Calculate risk for work artifact
        """

        # Factor 1: Base risk from mutation type
        base_risk = self._get_mutation_type_risk(artifact.artifact_type)

        # Factor 2: Agent confidence modifier
        confidence_modifier = self._calculate_confidence_modifier(
            artifact.agent_confidence
        )

        # Factor 3: Context impact modifier
        context_modifier = await self._calculate_context_impact_modifier(
            artifact, session
        )

        # Factor 4: Agent track record modifier
        track_record_modifier = await self._calculate_track_record_modifier(
            session.executed_by_agent_id
        )

        # Factor 5: Novelty modifier
        novelty_modifier = await self._calculate_novelty_modifier(
            artifact, session
        )

        # Apply all modifiers to base risk
        final_risk = self._apply_risk_modifiers(
            base_risk,
            [
                confidence_modifier,
                context_modifier,
                track_record_modifier,
                novelty_modifier
            ]
        )

        return RiskCalculation(
            finalRisk=final_risk,
            baseRisk=base_risk,
            modifiers=[
                confidence_modifier,
                context_modifier,
                track_record_modifier,
                novelty_modifier
            ],
            reasoning=self._generate_risk_reasoning(
                base_risk, final_risk, modifiers
            )
        )

    def _get_mutation_type_risk(self, artifact_type: str) -> RiskLevel:
        """
        Factor 1: Base risk from mutation type
        """
        risk_map = {
            'block_proposal': 'medium',          # Adding knowledge
            'block_update_proposal': 'high',     # Replacing knowledge
            'block_lock_proposal': 'high',       # Finalizing knowledge
            'document_creation': 'low',          # Composition only
            'insight': 'low',                    # No substrate impact
            'external_deliverable': 'low'        # No substrate impact
        }
        return risk_map.get(artifact_type, 'medium')

    def _calculate_confidence_modifier(
        self,
        confidence: Optional[float]
    ) -> RiskModifier:
        """
        Factor 2: Agent confidence modifier

        High confidence → Lower risk
        Low confidence → Higher risk
        """
        if confidence is None:
            return RiskModifier(
                factor='confidence',
                direction='none',
                magnitude=0,
                reason='No confidence score provided'
            )

        if confidence > 0.9:
            return RiskModifier(
                factor='confidence',
                direction='decrease',
                magnitude=1,
                reason=f'High confidence ({confidence:.2f})'
            )
        elif confidence < 0.7:
            return RiskModifier(
                factor='confidence',
                direction='increase',
                magnitude=1,
                reason=f'Low confidence ({confidence:.2f})'
            )
        else:
            return RiskModifier(
                factor='confidence',
                direction='none',
                magnitude=0,
                reason=f'Medium confidence ({confidence:.2f})'
            )

    async def _calculate_context_impact_modifier(
        self,
        artifact: WorkArtifact,
        session: WorkSession
    ) -> RiskModifier:
        """
        Factor 3: Context impact modifier

        More related blocks affected → Higher risk
        """
        # Count related blocks that would be affected
        related_blocks = await self._find_related_blocks(
            artifact, session.workspace_id, session.basket_id
        )

        count = len(related_blocks)

        if count <= 2:
            return RiskModifier(
                factor='context_impact',
                direction='none',
                magnitude=0,
                reason=f'Low context impact ({count} related blocks)'
            )
        elif count <= 5:
            return RiskModifier(
                factor='context_impact',
                direction='increase',
                magnitude=1,
                reason=f'Medium context impact ({count} related blocks)'
            )
        else:
            return RiskModifier(
                factor='context_impact',
                direction='increase',
                magnitude=2,
                reason=f'High context impact ({count} related blocks)'
            )

    async def _calculate_track_record_modifier(
        self,
        agent_id: Optional[str]
    ) -> RiskModifier:
        """
        Factor 4: Agent track record modifier

        High approval rate → Lower risk (trust earned)
        Low approval rate → Higher risk (needs scrutiny)
        """
        if not agent_id:
            return RiskModifier(
                factor='track_record',
                direction='none',
                magnitude=0,
                reason='No agent tracking'
            )

        # Fetch agent performance metrics
        metrics = await self._get_agent_performance(agent_id)

        if metrics.approval_rate > 0.9:
            return RiskModifier(
                factor='track_record',
                direction='decrease',
                magnitude=1,
                reason=f'Excellent track record ({metrics.approval_rate:.0%} approval)'
            )
        elif metrics.approval_rate < 0.7:
            return RiskModifier(
                factor='track_record',
                direction='increase',
                magnitude=1,
                reason=f'Poor track record ({metrics.approval_rate:.0%} approval)'
            )
        else:
            return RiskModifier(
                factor='track_record',
                direction='none',
                magnitude=0,
                reason=f'Average track record ({metrics.approval_rate:.0%} approval)'
            )

    async def _calculate_novelty_modifier(
        self,
        artifact: WorkArtifact,
        session: WorkSession
    ) -> RiskModifier:
        """
        Factor 5: Novelty detection modifier

        Confirms existing knowledge → Lower risk
        Introduces new entities/topics → Higher risk
        Contradicts existing knowledge → Much higher risk
        """
        # Semantic similarity check against existing blocks
        existing_blocks = await self._semantic_search_substrate(
            artifact.content,
            session.workspace_id,
            session.basket_id
        )

        if not existing_blocks:
            # Completely new topic
            return RiskModifier(
                factor='novelty',
                direction='increase',
                magnitude=1,
                reason='Introduces new topic (no related blocks found)'
            )

        # Check for confirmation vs. contradiction
        similarity_scores = [b.similarity for b in existing_blocks]
        max_similarity = max(similarity_scores)

        if max_similarity > 0.9:
            # Highly similar → Confirms existing knowledge
            return RiskModifier(
                factor='novelty',
                direction='none',
                magnitude=0,
                reason='Confirms existing knowledge (high similarity)'
            )
        elif max_similarity > 0.7:
            # Moderate similarity → Related but novel
            return RiskModifier(
                factor='novelty',
                direction='increase',
                magnitude=1,
                reason='Extends existing knowledge (moderate similarity)'
            )
        else:
            # Low similarity → Potentially contradictory or novel angle
            contradiction_detected = await self._detect_contradiction(
                artifact.content, existing_blocks
            )

            if contradiction_detected:
                return RiskModifier(
                    factor='novelty',
                    direction='increase',
                    magnitude=2,
                    reason='Potentially contradicts existing knowledge'
                )
            else:
                return RiskModifier(
                    factor='novelty',
                    direction='increase',
                    magnitude=1,
                    reason='Novel perspective on existing topic'
                )

    def _apply_risk_modifiers(
        self,
        base_risk: RiskLevel,
        modifiers: List[RiskModifier]
    ) -> RiskLevel:
        """
        Apply all modifiers to base risk
        """
        # Convert to numeric scale
        risk_value = {'low': 1, 'medium': 2, 'high': 3}[base_risk]

        # Apply each modifier
        for modifier in modifiers:
            if modifier.direction == 'increase':
                risk_value += modifier.magnitude
            elif modifier.direction == 'decrease':
                risk_value -= modifier.magnitude

        # Clamp to valid range [1, 3]
        risk_value = max(1, min(3, risk_value))

        # Convert back to risk level
        return {1: 'low', 2: 'medium', 3: 'high'}[risk_value]
```

---

## ⏸️ Component 3: Checkpoint Manager

### Purpose

Orchestrate multi-stage approval workflows (plan, mid-work, artifact, final) based on workspace policies.

### Checkpoint Types

```typescript
type CheckpointType =
  | 'plan_approval'       // Before work starts
  | 'mid_work_review'     // During execution (progress check)
  | 'artifact_review'     // Per-artifact (granular)
  | 'final_approval'      // Before substrate application (always required)

interface Checkpoint {
  id: UUID
  workSessionId: UUID
  checkpointType: CheckpointType
  checkpointNumber: number

  // What's being reviewed
  reviewContext: {
    artifacts?: UUID[]
    progress?: WorkProgress
    plan?: AgentPlan
  }

  status: 'pending' | 'approved' | 'rejected' | 'iteration_requested'

  // User decision
  decision?: CheckpointDecision
  reviewedBy?: UUID
  reviewedAt?: timestamp
}

interface CheckpointDecision {
  outcome: 'approve' | 'reject' | 'request_iteration'
  feedback?: string
  changeRequests?: ChangeRequest[]
}
```

### Approval Strategies

```typescript
type ApprovalStrategy =
  | 'checkpoint_required'      // All checkpoints enabled
  | 'final_only'               // Only final approval (default)
  | 'auto_approve_low_risk'    // Auto-approve for trusted agents

interface WorkspaceApprovalPolicy {
  defaultStrategy: ApprovalStrategy

  // Checkpoint configuration
  enablePlanApproval: boolean
  enableMidWorkReview: boolean
  enableArtifactReview: boolean
  finalApprovalRequired: boolean  // Always true

  // Auto-approval rules
  autoApproveEnabled: boolean
  autoApproveConfidenceMin: number
  autoApproveAgentApprovalRateMin: number
  autoApproveRiskLevels: RiskLevel[]  // e.g., ['low']
}
```

### Implementation

```python
class CheckpointManager:
    """
    Orchestrate multi-stage approval workflow
    """

    async def create_checkpoint(
        self,
        session: WorkSession,
        checkpoint_type: CheckpointType,
        review_context: dict
    ) -> Checkpoint:
        """
        Create checkpoint based on workspace policy
        """

        # Get workspace approval policy
        policy = await self._get_workspace_policy(session.workspace_id)

        # Check if this checkpoint type is enabled
        if not self._is_checkpoint_enabled(checkpoint_type, policy):
            # Skip this checkpoint
            return None

        # Create checkpoint record
        checkpoint = await self.db.work_checkpoints.create(
            work_session_id=session.id,
            checkpoint_type=checkpoint_type,
            checkpoint_number=await self._get_next_checkpoint_number(session.id),
            review_context=review_context,
            status='pending',
            created_at=datetime.utcnow()
        )

        # Notify reviewers
        await self.notifications.notify_checkpoint_ready(
            checkpoint, session
        )

        return checkpoint

    async def review_checkpoint(
        self,
        checkpoint_id: UUID,
        user_id: UUID,
        decision: CheckpointDecision
    ) -> CheckpointResult:
        """
        Handle checkpoint review
        """

        checkpoint = await self.db.work_checkpoints.get(checkpoint_id)
        session = await self.db.work_sessions.get(checkpoint.work_session_id)

        # Validate reviewer authorization
        await self._validate_reviewer(session, user_id)

        async with self.db.transaction():
            # Update checkpoint
            await self.db.work_checkpoints.update(
                checkpoint_id,
                status=decision.outcome,
                decision=decision,
                reviewed_by=user_id,
                reviewed_at=datetime.utcnow()
            )

            # Handle different outcomes
            if decision.outcome == 'approve':
                # Checkpoint passed, agent continues
                await self._notify_checkpoint_approved(checkpoint, session)

                if checkpoint.checkpoint_type == 'final_approval':
                    # This is the final checkpoint → Trigger unified approval
                    return await self.unified_orchestrator.review_work_session(
                        session.id,
                        user_id,
                        WorkReviewDecision(workQuality='approved')
                    )

            elif decision.outcome == 'reject':
                # Checkpoint failed → Session rejected
                return await self.unified_orchestrator.review_work_session(
                    session.id,
                    user_id,
                    WorkReviewDecision(
                        workQuality='rejected',
                        feedback=decision.feedback
                    )
                )

            elif decision.outcome == 'request_iteration':
                # Feedback provided → Create iteration
                return await self.unified_orchestrator.review_work_session(
                    session.id,
                    user_id,
                    WorkReviewDecision(
                        workQuality='needs_revision',
                        changeRequests=decision.change_requests
                    )
                )

        return CheckpointResult(status='approved')

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
            'final_approval': True  # Always required
        }
        return enabled_map[checkpoint_type]
```

---

## 🤖 Component 4: Auto-Approval Engine

### Purpose

Enable trusted agents to bypass human review for low-risk work, improving efficiency while maintaining safety.

### Auto-Approval Rules

```python
class AutoApprovalEngine:
    """
    Determine if work session qualifies for auto-approval
    """

    async def evaluate_auto_approval_eligibility(
        self,
        session: WorkSession,
        artifacts: List[WorkArtifact]
    ) -> AutoApprovalEvaluation:
        """
        Check if session qualifies for auto-approval
        """

        # Get workspace policy
        policy = await self._get_workspace_policy(session.workspace_id)

        if not policy.autoApproveEnabled:
            return AutoApprovalEvaluation(
                eligible=False,
                reason='Auto-approval disabled for workspace'
            )

        # Rule 1: All artifacts must be low risk
        all_low_risk = all(
            a.risk_level in policy.autoApproveRiskLevels
            for a in artifacts
        )

        if not all_low_risk:
            return AutoApprovalEvaluation(
                eligible=False,
                reason='Contains non-low-risk artifacts'
            )

        # Rule 2: Agent confidence must exceed threshold
        min_confidence = min(
            a.agent_confidence for a in artifacts if a.agent_confidence
        )

        if min_confidence < policy.autoApproveConfidenceMin:
            return AutoApprovalEvaluation(
                eligible=False,
                reason=f'Confidence {min_confidence:.2f} below threshold {policy.autoApproveConfidenceMin:.2f}'
            )

        # Rule 3: Agent track record must exceed threshold
        agent_metrics = await self._get_agent_performance(
            session.executed_by_agent_id
        )

        if agent_metrics.approval_rate < policy.autoApproveAgentApprovalRateMin:
            return AutoApprovalEvaluation(
                eligible=False,
                reason=f'Agent approval rate {agent_metrics.approval_rate:.0%} below threshold {policy.autoApproveAgentApprovalRateMin:.0%}'
            )

        # All rules passed → Eligible for auto-approval
        return AutoApprovalEvaluation(
            eligible=True,
            reason='All auto-approval criteria met'
        )

    async def auto_approve_work_session(
        self,
        session: WorkSession,
        artifacts: List[WorkArtifact]
    ) -> WorkReviewResult:
        """
        Auto-approve work session (bypass human review)
        """

        # Create synthetic user decision
        decision = WorkReviewDecision(
            workQuality='approved',
            artifactDecisions={
                a.id: 'apply_to_substrate'
                for a in artifacts
                if a.artifact_type in [
                    'block_proposal',
                    'block_update_proposal',
                    'document_creation'
                ]
            }
        )

        # Use unified orchestrator (same code path)
        result = await self.unified_orchestrator.review_work_session(
            session.id,
            user_id=None,  # System auto-approval
            decision=decision
        )

        # Notify user of auto-approval
        await self.notifications.notify_work_auto_approved(
            session, result.substrateChanges
        )

        return result
```

---

## 🔒 Component 5: Enforcement & Audit

### Substrate Mutation Guard

```python
class SubstrateMutationGuard:
    """
    Ensure only approved work artifacts can mutate substrate
    """

    async def validate_mutation_authorized(
        self,
        block_id: Optional[UUID],
        work_artifact_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Check if mutation is authorized (artifact approved)
        """

        artifact = await self.db.work_artifacts.get(work_artifact_id)

        if artifact.status != 'applied_to_substrate':
            raise GovernanceViolation(
                f"Artifact {work_artifact_id} not approved for substrate application"
            )

        # Check that artifact's session was approved
        session = await self.db.work_sessions.get(artifact.work_session_id)

        if session.status != 'completed_approved':
            raise GovernanceViolation(
                f"Work session {session.id} not approved"
            )

        return True
```

### Database RLS Enforcement

```sql
-- Agents cannot directly mutate substrate
-- Only unified orchestrator (service_role) can create blocks
CREATE POLICY "agents_cannot_create_blocks_directly"
ON blocks
FOR INSERT
TO authenticated
WITH CHECK (
  -- Blocks must be created via work_artifacts
  -- OR by humans (no agent_id in metadata)
  NOT (metadata->>'created_by_agent' IS NOT NULL AND auth.uid() != metadata->>'approved_by_user'::uuid)
);
```

### Governance Audit Trail

```python
class GovernanceAuditor:
    """
    Log all governance decisions for compliance
    """

    async def log_governance_decision(
        self,
        session_id: UUID,
        decision_type: str,  # 'approval', 'rejection', 'iteration_request'
        decision_maker: UUID,
        decision_details: dict
    ):
        """
        Append-only governance audit log
        """

        await self.db.governance_audit_log.create(
            work_session_id=session_id,
            decision_type=decision_type,
            decision_maker=decision_maker,
            decision_details=decision_details,
            timestamp=datetime.utcnow()
        )
```

---

## 🔄 Complete Governance Flow

### Scenario: Research Task with Final Approval

```
1. Agent completes research task
   ↓
   Work Session created with 5 artifacts

2. Risk Assessment Engine evaluates each artifact
   ↓
   Artifact 1: Low risk (new block, high confidence)
   Artifact 2: Medium risk (new block, moderate confidence)
   Artifact 3: Low risk (document creation)
   Artifact 4: High risk (updates existing block, low confidence)
   Artifact 5: Low risk (external deliverable)

3. Checkpoint Manager checks workspace policy
   ↓
   Policy: final_only (skip plan/mid-work checkpoints)
   ↓
   Create final_approval checkpoint

4. Auto-Approval Engine evaluates eligibility
   ↓
   Contains high-risk artifact (Artifact 4) → NOT eligible
   ↓
   Require human review

5. User reviews work session
   ↓
   Reviews overall work quality: "Good research"
   ↓
   Per-artifact decisions:
     - Artifact 1: Apply to substrate ✅
     - Artifact 2: Apply to substrate ✅
     - Artifact 3: Apply to substrate ✅
     - Artifact 4: Reject (data seems outdated) ❌
     - Artifact 5: Approve only (no substrate impact) ✅

6. Unified Approval Orchestrator processes decision
   ↓
   Transaction started:
     - Create 2 blocks (Artifacts 1, 2) in ACCEPTED state
     - Create 1 document (Artifact 3)
     - Reject Artifact 4 (no substrate mutation)
     - Mark Artifact 5 approved (no substrate mutation)
     - Record 3 work_context_mutations
     - Update session status → completed_approved
     - Update agent track record
     - Emit timeline event
     - Send notifications
   Transaction committed

7. Result
   ↓
   - User reviewed once
   - 3 substrate changes applied
   - 1 artifact rejected with feedback
   - Complete audit trail
   - Agent track record updated
```

---

## 📊 Governance Metrics

### Agent Performance Tracking

```typescript
interface AgentPerformanceMetrics {
  agentId: string

  // Session-level metrics
  totalSessions: number
  sessionsApproved: number
  sessionsRejected: number
  sessionsPartialApproval: number
  approvalRate: number  // sessionsApproved / totalSessions

  // Artifact-level metrics
  totalArtifacts: number
  artifactsAppliedToSubstrate: number
  artifactsRejected: number
  artifactApprovalRate: number

  // Confidence calibration
  avgClaimedConfidence: number
  avgActualApprovalRate: number
  confidenceCalibrationError: number  // |claimed - actual|

  // Iteration metrics
  avgIterationsPerSession: number

  // Risk distribution
  lowRiskArtifacts: number
  mediumRiskArtifacts: number
  highRiskArtifacts: number
}
```

### Workspace Governance Metrics

```typescript
interface WorkspaceGovernanceMetrics {
  workspaceId: UUID

  // Overall approval rates
  sessionApprovalRate: number
  artifactApprovalRate: number

  // Efficiency metrics
  avgReviewTimeSeconds: number
  autoApprovalRate: number

  // Quality metrics
  postApprovalRevertRate: number  // % of approved work later reverted
  iterationRate: number  // % of sessions requiring iterations
}
```

---

## 🔗 Integration Points

### Layer 2 (Work Orchestration)

```python
# Governance layer consumes work orchestration data
from app.work.models import WorkSession, WorkArtifact

# Governance layer emits work status updates
await work_service.update_session_status(
    session_id, 'completed_approved'
)
```

### Layer 1 (Substrate Core)

```python
# Governance layer creates substrate entities
from app.substrate.blocks import BlockService
from app.substrate.documents import DocumentService

# Direct to ACCEPTED state (work already reviewed)
block_id = await block_service.create(
    content=artifact.content,
    state='ACCEPTED',  # Key difference from v3.1
    metadata={'work_artifact_id': artifact.id}
)
```

### Layer 4 (Presentation)

```python
# Governance layer provides review data to UI
review_data = await governance_service.get_session_review_data(
    session_id
)
# Returns: session, artifacts, risk assessments, agent track record

# UI calls governance layer for approval
result = await governance_service.review_work_session(
    session_id, user_id, decision
)
```

---

## 🚦 API Surface

### Core Endpoints

```typescript
// Review work session
POST /api/governance/sessions/{sessionId}/review
Body: WorkReviewDecision
Returns: WorkReviewResult

// Review checkpoint
POST /api/governance/checkpoints/{checkpointId}/review
Body: CheckpointDecision
Returns: CheckpointResult

// Get review data (for UI)
GET /api/governance/sessions/{sessionId}/review-data
Returns: {
  session: WorkSession
  artifacts: WorkArtifact[]
  riskAssessments: RiskCalculation[]
  agentMetrics: AgentPerformanceMetrics
  workspacePolicy: WorkspaceApprovalPolicy
}

// Revert approved work
POST /api/governance/sessions/{sessionId}/revert
Body: { reason: string }
Returns: RevertResult

// Get agent performance
GET /api/governance/agents/{agentId}/metrics
Returns: AgentPerformanceMetrics

// Update workspace policy
PUT /api/governance/workspaces/{workspaceId}/policy
Body: WorkspaceApprovalPolicy
Returns: WorkspaceApprovalPolicy
```

---

## ✅ Summary

**Unified Governance Layer (Layer 3)** provides:

1. **Single Approval → Dual Effect**: One review handles work quality + substrate integrity
2. **Risk-Informed Review**: Multi-factor risk assessment guides user attention
3. **Multi-Stage Checkpoints**: Flexible approval workflows (plan, mid-work, artifact, final)
4. **Iterative Supervision**: Bounded feedback loops for work refinement
5. **Auto-Approval**: Trusted agents bypass review for low-risk work
6. **Enforcement**: Database-level guards prevent unauthorized substrate mutations
7. **Complete Audit**: All governance decisions logged for compliance

**Key Pattern**: Work artifacts go from `draft` → `pending_review` → `applied_to_substrate`, creating substrate entities in `ACCEPTED` state directly (no separate proposal governance).

**Result**: Users trust agent outputs because governance is transparent, traceable, and granular.

---

## 📎 See Also

- [YARNNN_GOVERNANCE_PHILOSOPHY_V4.md](../canon/YARNNN_GOVERNANCE_PHILOSOPHY_V4.md) - Governance principles
- [YARNNN_LAYERED_ARCHITECTURE_V4.md](./YARNNN_LAYERED_ARCHITECTURE_V4.md) - Overall architecture
- [WORK_SESSION_LIFECYCLE.md](../features/work-management/WORK_SESSION_LIFECYCLE.md) - Session states
- [RISK_ASSESSMENT.md](../features/governance/RISK_ASSESSMENT.md) - Risk calculation details

---

**Unified Governance: One review, dual effect. Trust through transparency.**
