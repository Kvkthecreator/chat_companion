# YARNNN Governance Philosophy v4.0

**Unified Governance: Work Quality + Context Integrity**

**Version**: 4.0 (Major Evolution from Substrate-Only Governance)
**Date**: 2025-10-31 (Updated: 2025-11-19)
**Status**: ⚠️ DESIGN VISION (NOT YET IMPLEMENTED - SEPARATED GOVERNANCE IN PRODUCTION)
**Supersedes**: YARNNN_GOVERNANCE_CANON_V5.md

**CURRENT REALITY (2025-11-19)**: Work Supervision (work-platform) and Substrate Governance (substrate-API) are **SEPARATE** systems. This document describes a future "unified" vision that is NOT implemented.

---

## ⚠️ CURRENT IMPLEMENTATION STATUS (As of 2025-11-05)

**This document describes the v4.0 VISION, which is NOT yet implemented.**

**What IS Working** ✅:
- **Substrate Governance** (substrate-api): P0-P4 pipeline with proposals
- Blocks created via proposals only
- P1 semantic deduplication and quality validation

**What is NOT Working** ❌:
- **Work-Platform Governance**: Not yet defined or implemented
- Unified approval orchestrator: Disabled (bypassed substrate governance)
- Work→Substrate bridge: Architecture not yet designed

**Decision Pending**: How should work-platform interact with substrate governance?
- Should approved work artifacts create substrate proposals?
- Should work governance be independent from substrate governance?
- What's the right bridge architecture?

**See**: [`GOVERNANCE_SEPARATION_REFACTOR_PLAN.md`](../architecture/GOVERNANCE_SEPARATION_REFACTOR_PLAN.md)

---

## 🎯 Core Philosophy (Future Vision)

**Governance in YARNNN v4.0 will address TWO concerns**:

1. **Work Quality** - Is the agent's work good? (reasoning, completeness, accuracy)
2. **Context Integrity** - Should this update the knowledge base? (trust, relevance, correctness)

**The Key Design Question**: How should these two concerns relate?
- **Option A**: Single approval handles both (unified)
- **Option B**: Two independent approval layers (separated)
- **Current Implementation**: Only substrate governance exists (option B by default)

### The Evolution

| Version | Governance Scope | User Action |
|---------|------------------|-------------|
| v3.0 | Substrate mutations only | Approve block proposals separately |
| v3.1 | Substrate + confidence routing | Approve proposals, high-confidence auto-executes |
| **v4.0** | **Work + Substrate unified** | **Approve work once → both handled** |

---

## 🌟 The Three Governance Principles (v4.0)

### 1. **Unified Review Eliminates Redundancy**

**Old Model (v3.1)**:
```
Agent creates block proposal
  ↓
User reviews: "Should this become substrate?" ← ONLY substrate concern
  ↓
Approve/Reject
```

**Problem**: User must think about substrate layer, not work quality layer

**New Model (v4.0)**:
```
Agent completes work session with artifacts
  ↓
User reviews: "Is this good work?" ← Work quality question
  ↓
If yes: Work approved AND artifacts → substrate automatically
```

**Why Better**: Users think about work quality (natural), system handles substrate consistency (automated)

---

### 2. **Work Quality Gates Context Updates**

**Principle**: All substrate mutations flow through work session approval.

**Exception**: User-initiated direct substrate changes (manual block creation, document editing)

**Enforcement**:
```sql
-- Agents cannot directly mutate substrate
INSERT INTO blocks (...) WHERE created_by_agent = true
  → ERROR: Use work_artifacts instead

-- Only unified governance can apply artifacts to substrate
work_artifacts (status = 'approved')
  → UnifiedApprovalOrchestrator.apply_to_substrate()
  → blocks (state = 'ACCEPTED')
```

**Result**: No context pollution from ungoverned agent work

---

### 3. **Provenance is Governance**

**Principle**: Every substrate mutation must trace back to a work session or user action.

**Audit Trail**:
```
Substrate Change
  ↓ traces to
Work Context Mutation
  ↓ traces to
Work Artifact
  ↓ traces to
Work Session
  ↓ traces to
User Task Intent + Agent Reasoning
```

**Why**: If we can't trace WHY something changed, we can't trust it or debug it.

---

## 🏗️ Unified Governance Architecture

### The Single Approval Flow

```
┌─────────────────────────────────────────────────────────┐
│ USER REVIEWS WORK SESSION                                │
│                                                           │
│ Question: "Is this good work?"                           │
│                                                           │
│ Evidence:                                                 │
│ - Agent reasoning trail                                  │
│ - Source blocks used (provenance)                        │
│ - Confidence score (agent self-assessment)               │
│ - Artifacts produced (what will change)                  │
│ - Risk assessment (system-calculated)                    │
└─────────────────────────────────────────────────────────┘
                         ↓
              ┌──────────┴──────────┐
              │                     │
        [APPROVE]              [REJECT]
              │                     │
              ↓                     ↓
    ┌──────────────────┐   ┌─────────────────┐
    │ DUAL EFFECT:     │   │ NO CHANGES:     │
    │ 1. Work approved │   │ - Work rejected │
    │ 2. Artifacts →   │   │ - No substrate  │
    │    Substrate     │   │   mutations     │
    │                  │   │ - Feedback to   │
    │ Automatic:       │   │   agent         │
    │ - Blocks created │   └─────────────────┘
    │ - Docs created   │
    │ - Timeline event │
    │ - Audit trail    │
    └──────────────────┘
```

### Per-Artifact Decisions (Advanced)

Users can make **granular decisions** per artifact:

```
Work Session has 5 artifacts:
  - Artifact 1: Block about competitor X
  - Artifact 2: Block about pricing strategy
  - Artifact 3: Document summarizing research
  - Artifact 4: External spreadsheet
  - Artifact 5: Block with uncertain data

User decisions:
  - Artifact 1: ✅ Apply to substrate
  - Artifact 2: ✅ Apply to substrate
  - Artifact 3: ✅ Apply to substrate
  - Artifact 4: ✅ Approve (no substrate impact - external)
  - Artifact 5: ❌ Reject (data uncertain)

Result:
  - Work session: APPROVED (4/5 artifacts accepted)
  - Substrate: 3 blocks + 1 document added
  - Artifact 5: Rejected with feedback
```

**Why**: Nuance matters. Not all-or-nothing.

---

## 🔍 Risk Assessment Framework

### How Risk is Calculated

Every artifact gets a **risk score** (low/medium/high) based on:

#### Factor 1: Mutation Type

| Mutation | Base Risk | Reason |
|----------|-----------|--------|
| Block created (new knowledge) | Medium | Adding knowledge is safer than changing |
| Block updated (supersession) | High | Replacing existing knowledge risks contradiction |
| Block locked (finalized) | High | Permanent state change |
| Document created | Low | Documents are compositions, not substrate |
| External deliverable | Low | No substrate impact |

#### Factor 2: Agent Confidence

| Confidence | Risk Modifier | Example |
|------------|---------------|---------|
| >0.9 | -1 level | High → Medium, Medium → Low |
| 0.7-0.9 | No change | Risk stays same |
| <0.7 | +1 level | Low → Medium, Medium → High |

**Why**: Agent self-awareness correlates with accuracy

#### Factor 3: Context Impact

| Substrate Affected | Risk Modifier |
|--------------------|---------------|
| 0-2 related blocks | No change |
| 3-5 related blocks | +1 level |
| 6+ related blocks | +2 levels |

**Why**: Broad impact = higher risk of unintended consequences

#### Factor 4: Agent Track Record

| Approval Rate | Risk Modifier |
|---------------|---------------|
| >90% | -1 level |
| 70-90% | No change |
| <70% | +1 level |

**Why**: Proven agents earn trust

#### Factor 5: Novelty Detection

| Content Novelty | Risk Modifier |
|-----------------|---------------|
| Confirms existing blocks | No change |
| Adds new topic/entity | +1 level |
| Contradicts existing blocks | +2 levels |

**Why**: New territory needs more scrutiny

### Example Calculation

```
Artifact: Block about competitor pricing
  - Mutation type: Block created → Medium
  - Agent confidence: 0.85 → No change → Medium
  - Context impact: 4 related blocks → +1 level → High
  - Agent track record: 92% approval → -1 level → Medium
  - Novelty: New competitor (not in substrate) → +1 level → High

Final Risk: HIGH
```

**UI Impact**: High-risk artifacts shown prominently in review UI

---

## 🔄 Checkpoint Strategies

### Types of Checkpoints

#### 1. Plan Approval (Before Work Starts)

**When**: Agent proposes approach before execution
**Purpose**: Validate direction before investing time
**User Question**: "Is this the right approach?"

**Example**:
```
Task: "Research AI memory competitors"

Agent Plan:
1. Query substrate for existing competitor knowledge
2. Web research for 5 top competitors (Mem0, Zep, Pinecone, Weaviate, Chroma)
3. Create block for each competitor (pricing, features, positioning)
4. Create synthesis document comparing approaches

Checkpoint: User approves plan OR redirects
```

**Configuration**: Optional (approval_strategy = 'checkpoint_required')

#### 2. Mid-Work Review (During Execution)

**When**: Agent completed partial work, requests feedback
**Purpose**: Course-correct before wasting more effort
**User Question**: "Is this on track?"

**Example**:
```
Task: "Research AI memory competitors"

Agent Progress (50% done):
- ✅ Researched Mem0 (block created)
- ✅ Researched Zep (block created)
- ⏳ Starting Pinecone...

Agent: "I noticed Mem0 focuses on personal memory while Zep targets production.
        Should I emphasize production-readiness in remaining research?"

Checkpoint: User confirms OR redirects focus
```

**Configuration**: Optional (triggered by agent or time/artifact thresholds)

#### 3. Artifact Review (Per-Artifact)

**When**: Agent requests review of individual artifact before proceeding
**Purpose**: Validate quality incrementally
**User Question**: "Is this artifact good?"

**Example**:
```
Task: "Research AI memory competitors"

Agent: "I've completed research on Mem0. Here's the block I propose adding."

Artifact Content: [detailed competitive analysis]
Agent Reasoning: "Based on their docs and pricing page..."
Confidence: 0.88
Risk: Medium

Checkpoint: User approves artifact OR requests revision
```

**Configuration**: Optional (only for high-risk artifacts or new agents)

#### 4. Final Approval (Before Substrate Application)

**When**: All work complete, ready to apply to substrate
**Purpose**: Last gate before permanent changes
**User Question**: "Apply these changes to knowledge base?"

**Example**:
```
Task: "Research AI memory competitors"

Work Complete:
- 5 competitor blocks created
- 1 synthesis document created
- 12 source blocks referenced
- Confidence: 0.91
- Overall risk: Medium

Checkpoint: User approves all → Substrate updated
```

**Configuration**: ALWAYS REQUIRED (default: 'final_only')

### Approval Strategy Matrix

| Strategy | Plan | Mid-Work | Artifact | Final | Use Case |
|----------|------|----------|----------|-------|----------|
| `checkpoint_required` | ✅ | ✅ | ❌ | ✅ | High-stakes work, new agents |
| `final_only` | ❌ | ❌ | ❌ | ✅ | Trusted agents, routine work |
| `auto_approve_low_risk` | ❌ | ❌ | ❌ | 🤖 | Proven agents, low-risk artifacts |

**Default**: `final_only` (most users start here)

---

## 🔁 Iteration Mechanics (Feedback Loops)

### The Problem with Binary Approval

```
Agent does 2 hours of work
  ↓
User: "This is 80% right but approach was wrong"
  ↓
Options:
  - Approve → Pollute context with flawed work
  - Reject → Waste 2 hours of effort
  ↓
Result: Frustration, low agent utility
```

### YARNNN Solution: Iterations

```
Agent proposes plan
  ↓
Checkpoint: User provides feedback "Focus on X, not Y"
  ↓
Iteration 1: Agent revises approach
  ↓
Agent continues work with new direction
  ↓
Checkpoint: User reviews progress
  ↓
Iteration 2: User says "Good, keep going"
  ↓
Agent completes work
  ↓
Final approval: User approves refined work
  ↓
Result: High-quality output, no wasted effort
```

### Iteration Tracking

```sql
work_iterations (
  iteration_number INT,           -- 1, 2, 3...
  triggered_by TEXT,              -- 'checkpoint_rejection', 'user_feedback'
  user_feedback_text TEXT,        -- "Focus on SMB segment"
  changes_requested JSONB,        -- Structured feedback
  agent_interpretation TEXT,      -- How agent understood feedback
  revised_approach TEXT,          -- What agent will do differently
  artifacts_revised UUID[]        -- Which artifacts changed
)
```

**Bounded Iterations**: Max 3 iterations per session (configurable)
**Why**: Prevent infinite loops, encourage clear task scoping

---

## 🛡️ Auto-Approval (Trust Calibration)

### When Auto-Approval Triggers

```
IF (
  artifact.risk_level = 'low'
  AND artifact.agent_confidence > workspace.confidence_threshold
  AND agent.approval_rate > 0.85
  AND workspace.approval_strategy = 'auto_approve_low_risk'
) THEN
  auto_approve_artifact()
  notify_user("Auto-approved low-risk work from trusted agent")
ELSE
  require_user_review()
END
```

### Trust Calibration Over Time

```
Agent Track Record:
  Sessions: 50
  Approved: 47 (94%)
  Rejected: 2 (4%)
  Partial: 1 (2%)
  Avg Confidence: 0.89
  Confidence Calibration: Good (claimed 0.9, actual 0.94 approval)

Result: Agent earns auto-approve for low-risk work
```

**Why**: High-performing agents shouldn't require review for routine work

**Safety**: Auto-approved work still captured in timeline with "revert" option

---

## 📊 Governance Metrics (Observability)

### Session-Level Metrics

- **Approval Rate**: % of sessions approved on first review
- **Iteration Rate**: Avg iterations per session
- **Rejection Rate**: % of sessions rejected
- **Partial Approval Rate**: % of sessions with some artifacts rejected

**Target**: >70% approval rate, <1.5 avg iterations

### Artifact-Level Metrics

- **Artifact Approval Rate**: % of artifacts applied to substrate
- **Risk Distribution**: % low/medium/high risk artifacts
- **Auto-Approval Rate**: % of artifacts auto-approved

**Target**: >80% artifact approval, <20% high-risk

### Agent-Level Metrics

- **Agent Approval Rate**: % of agent's sessions approved
- **Confidence Calibration**: Claimed confidence vs. actual approval rate
- **Revision Rate**: % of artifacts revised after feedback

**Target**: >85% agent approval rate, <0.1 confidence calibration error

### User-Level Metrics

- **Review Time**: Avg time to review work session
- **Engagement Rate**: % of pending sessions reviewed within 24hr
- **Trust Level**: % of work auto-approved (for trusted agents)

**Target**: <5 min review time, >80% engagement rate

---

## 🎯 Governance by Workspace (Policy Configuration)

### Workspace Governance Settings

```typescript
interface WorkspaceGovernancePolicy {
  // Approval Strategy
  default_approval_strategy: 'checkpoint_required' | 'final_only' | 'auto_approve_low_risk'

  // Thresholds
  confidence_threshold: number  // 0.0-1.0, default 0.85
  max_iterations_per_session: number  // default 3

  // Auto-Approval
  enable_auto_approve: boolean
  auto_approve_confidence_min: number  // default 0.9
  auto_approve_agent_approval_rate_min: number  // default 0.85

  // Risk Tolerance
  require_review_for_high_risk: boolean  // default true
  allow_medium_risk_auto_approve: boolean  // default false

  // Notifications
  notify_on_auto_approve: boolean  // default true
  notify_on_checkpoint: boolean  // default true
}
```

**Default**: Conservative (checkpoint required, no auto-approve)
**Progressive**: Users can relax constraints as trust builds

---

## 🚨 Governance Violations & Enforcement

### Violations

1. **Agent Attempts Direct Substrate Mutation**
   - Action: Block at database level (RLS policy)
   - Log: Governance violation event
   - Notify: User + admin

2. **Artifact Applied Without Approval**
   - Action: Impossible (UnifiedApprovalOrchestrator is only path)
   - Defense: Code-level enforcement

3. **Work Session Exceeds Iteration Limit**
   - Action: Session marked 'failed', no substrate changes
   - Reason: Prevent infinite loops
   - Recovery: User can restart with clearer task

4. **Confidence Miscalibration**
   - Detection: Agent claims >0.9 confidence, <70% approval rate
   - Action: Flag agent, require human review
   - Recovery: Agent track record resets

### Enforcement Layers

```
Layer 1: Database RLS (agents cannot INSERT into blocks)
Layer 2: API Authorization (work APIs require workspace membership)
Layer 3: Unified Orchestrator (only approved artifacts applied)
Layer 4: Timeline Audit (all mutations logged)
Layer 5: User Visibility (transparent governance in UI)
```

---

## 📖 Governance Glossary

**Work Session**: Agent execution lifecycle requiring governance review

**Work Artifact**: Agent output awaiting approval (block, document, insight, external)

**Unified Approval**: Single review handling work quality + substrate mutation

**Checkpoint**: Approval point during work session (plan, mid-work, artifact, final)

**Iteration**: Feedback loop where user requests changes and agent revises

**Risk Assessment**: System-calculated risk level for each artifact

**Auto-Approval**: Trusted agents bypass review for low-risk work

**Context Mutation**: Substrate change resulting from approved work artifact

**Provenance**: Complete lineage from task → work → reasoning → artifact → substrate

**Track Record**: Agent's historical approval rate and confidence calibration

---

## ✅ Summary: Governance v4.0

**Core Change**: Substrate-only governance → Unified work + substrate governance

**Key Benefits**:
1. Single approval eliminates redundancy
2. Work quality gates context integrity
3. Provenance ensures accountability
4. Iterations improve outcomes
5. Trust calibration enables efficiency

**User Experience**:
- Ask ONE question: "Is this good work?"
- See FULL CONTEXT: reasoning, sources, confidence, risk
- Give NUANCED FEEDBACK: approve all, partial, iterate, reject
- Trust AUTO-APPROVE: Low-risk work from proven agents bypasses review

**Result**: Agent deployment becomes default, not feared

---

## 📎 See Also

- [YARNNN_PLATFORM_CANON_V4.md](./YARNNN_PLATFORM_CANON_V4.md) - Core platform philosophy
- [YARNNN_WORK_PLATFORM_THESIS.md](./YARNNN_WORK_PLATFORM_THESIS.md) - Why unified governance matters
- [YARNNN_UNIFIED_GOVERNANCE.md](../architecture/YARNNN_UNIFIED_GOVERNANCE.md) - Technical implementation
- [WORK_SESSION_LIFECYCLE.md](../features/work-management/WORK_SESSION_LIFECYCLE.md) - Session states and flows

---

**Unified governance: Work quality + Context integrity. One review, dual effect. This is YARNNN v4.0.**
