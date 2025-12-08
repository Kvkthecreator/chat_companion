# YARNNN Governance Canon v5.0.0 — Multi-Basket Governance Architecture

**The Single Source of Truth for Multi-Basket Governance, Change Requests, and Scope-Aware Approval Workflows**

This document establishes governance architecture for multi-basket workspaces with MCP-based basket inference.

---

## 🎯 Architectural Context

### The Multi-Basket Reality

YARNNN evolved from **single-basket philosophy** (user works within one context) to **multi-basket reality** (MCP integrations with basket inference require cross-basket coordination).

**Impact**: Governance must operate at **two distinct scopes**:
1. **Workspace-Level**: Cross-basket operations, basket assignment, workspace mutations
2. **Basket-Level**: Single-basket substrate mutations (original model)

---

## Sacred Principles

**Governance Sacred Principle #1**: All substrate mutations flow through governed change requests
**Governance Sacred Principle #2**: Change requests target substrates only - artifacts operate independently
**Governance Sacred Principle #3**: Agent validation is mandatory for substrate change requests
**Governance Sacred Principle #4**: Scope determines review location (workspace vs basket)
**Governance Sacred Principle #5**: Governance is domain-distinct from notifications (change requests generate events, but are not events themselves)

---

## 🏗️ Domain Definition: Change Requests (Governance)

### Purpose
Control substrate mutations through validation and approval workflow. Change requests are **the governance domain** - not just terminology.

### Core Workflow
```
Intent → Validation → Review → Approval/Rejection → Execution → Event Emission
```

### Distinction from Other Domains
- **Change Requests** (Governance) = Control mutation of substrate
- **Notifications** (Observability) = Communicate events to users (domain-agnostic)
- **Timeline** (History) = Show knowledge evolution narrative (basket-scoped)

**Relationship**: Change requests **generate** notifications, are **logged to** timeline, but remain a distinct domain.

---

## 🔀 Two-Scope Governance Model

### Change Request Type 1: Workspace-Level

**Purpose**: Coordinate cross-basket operations and basket assignment decisions

**Subtypes**:

#### Type 1a: Basket Assignment Requests
```typescript
// MCP capture arrives with low confidence basket inference
{
  proposal_kind: 'BASKET_ASSIGNMENT',
  scope: 'workspace',
  basket_id: null,              // Not yet assigned
  target_basket_id: uuid,       // Suggested basket
  ops: [{
    type: 'AssignDumpToBasket',
    dump_id: uuid,
    target_basket_id: uuid,
    confidence: 0.45            // Low confidence = requires review
  }],
  origin: 'agent',
  status: 'PROPOSED'
}
```

**Current Name**: "Unassigned Queue" ❌ (misleading - this IS a change request queue)
**Canon Name**: "Workspace Change Requests - Assignment Type"
**Review Location**: `/workspace/change-requests?type=assignment`
**Decision**: User approves → Dump assigned to basket → Substrate mutation executes

#### Type 1b: Cross-Basket Operations
```typescript
// Agent proposes relationship spanning baskets
{
  proposal_kind: 'CROSS_BASKET_RELATIONSHIP',
  scope: 'cross-basket',
  basket_id: null,
  affected_basket_ids: [basket_a_id, basket_b_id],
  ops: [{
    type: 'CreateRelationship',
    from_basket_id: basket_a_id,
    from_block_id: block_x_id,
    to_basket_id: basket_b_id,
    to_block_id: block_y_id,
    relationship_type: 'references'
  }],
  origin: 'agent',
  status: 'PROPOSED'
}
```

**Review Location**: `/workspace/change-requests?type=cross-basket`
**Decision**: Approve → Execute across baskets → Emit events to both baskets

#### Type 1c: Workspace Mutations
```typescript
// Agent proposes creating inferred basket from clustered captures
{
  proposal_kind: 'WORKSPACE_BASKET_CREATION',
  scope: 'workspace',
  basket_id: null,
  ops: [{
    type: 'CreateBasket',
    name: 'Inferred: Product Strategy',
    initial_dumps: [dump_1_id, dump_2_id, ...],
    confidence: 0.78
  }],
  origin: 'agent',
  status: 'PROPOSED'
}
```

**Review Location**: `/workspace/change-requests?type=workspace`
**Decision**: Approve → Create basket + assign dumps → Execute substrate mutations

---

### Change Request Type 2: Basket-Level

**Purpose**: Direct substrate mutations within single basket context

**Examples**:
```typescript
// Standard P1 evolution - agent proposes blocks from dumps
{
  proposal_kind: 'BLOCK_PROPOSAL',
  scope: 'basket',
  basket_id: uuid,              // Scoped to single basket
  affected_basket_ids: [uuid],  // Only this basket
  ops: [
    { type: 'CreateBlock', content: '...', confidence: 0.85 },
    { type: 'ReviseBlock', block_id: '...', content: '...', confidence: 0.72 }
  ],
  origin: 'agent',
  status: 'PROPOSED'
}

// Human manual edit
{
  proposal_kind: 'CONTEXT_ITEM_PROPOSAL',
  scope: 'basket',
  basket_id: uuid,
  ops: [
    { type: 'CreateContextItem', label: 'Project X', kind: 'project' }
  ],
  origin: 'human',
  status: 'PROPOSED'
}
```

**Review Location**: `/baskets/[id]/change-requests`
**Decision**: Approve → Substrate mutates within basket → Timeline event logged

---

## 📊 Unified Workspace Change Request UX

### Route Structure
**Single Page**: `/workspace/change-requests`

**Filter Tabs**:
```typescript
- All (24 pending)
- Assignments (12)     // Type 1a - basket assignment decisions
- Cross-Basket (3)      // Type 1b - multi-basket operations
- Workspace (2)         // Type 1c - workspace mutations
- Approved (156)
- Rejected (18)
```

### UI Layout
```
Workspace Change Requests

──────────────────────────────────────────
📋 Pending Assignments (12)

[MCP Capture] "API design discussion notes"
  Tool: claude.memory
  Suggested: "Project X" (confidence: 0.72)
  [Assign to Basket ▼] [Dismiss]

[MCP Capture] "Meeting notes - Product roadmap"
  Tool: chatgpt.remember
  Suggested: "Work Journal" (confidence: 0.45)
  [Assign to Basket ▼] [Dismiss]

──────────────────────────────────────────
🔗 Cross-Basket Operations (3)

[Relationship] Link "Research Notes" → "Project Implementation"
  Proposed by: Ambient Agent
  Confidence: 0.81 | Impact: 2 baskets
  [Review Details] [Approve] [Reject]

──────────────────────────────────────────
🌐 Workspace Operations (2)

[New Basket] Create "Inferred: Q1 Planning"
  From: 8 clustered captures
  Confidence: 0.76
  [Review Details] [Approve] [Reject]
```

---

## 🗄️ Database Schema (Enhanced for Multi-Basket)

### Proposals Table Enhancement

```sql
-- BEFORE (Single-basket only)
CREATE TABLE proposals (
  id uuid PRIMARY KEY,
  basket_id uuid NOT NULL REFERENCES baskets(id),  -- ❌ Prevents workspace-scoped!
  workspace_id uuid NOT NULL,
  -- ...
);

-- AFTER (Multi-basket enabled)
ALTER TABLE proposals
  ALTER COLUMN basket_id DROP NOT NULL;  -- ✅ Allow workspace-scoped

ALTER TABLE proposals
  ADD COLUMN scope text
    CHECK (scope IN ('basket', 'workspace', 'cross-basket'))
    DEFAULT 'basket',

  ADD COLUMN target_basket_id uuid REFERENCES baskets(id),
    -- For Type 1a: Which basket to assign to

  ADD COLUMN affected_basket_ids uuid[] DEFAULT '{}';
    -- For Type 1b: All baskets touched by this change

-- Backfill existing data
UPDATE proposals SET
  scope = 'basket',
  affected_basket_ids = ARRAY[basket_id]
WHERE basket_id IS NOT NULL;

-- Indexes for workspace queries
CREATE INDEX idx_proposals_workspace_scope
  ON proposals(workspace_id, scope, status, created_at DESC)
  WHERE basket_id IS NULL OR scope IN ('workspace', 'cross-basket');

CREATE INDEX idx_proposals_basket_scope
  ON proposals(basket_id, status, created_at DESC)
  WHERE scope = 'basket';
```

### New Proposal Kinds

```sql
-- Add workspace-level proposal kinds
ALTER TYPE proposal_kind ADD VALUE IF NOT EXISTS 'BASKET_ASSIGNMENT';
ALTER TYPE proposal_kind ADD VALUE IF NOT EXISTS 'CROSS_BASKET_RELATIONSHIP';
ALTER TYPE proposal_kind ADD VALUE IF NOT EXISTS 'WORKSPACE_BASKET_CREATION';
```

---

## 🚨 CRITICAL: Substrate vs Artifact Governance Boundaries

### SUBSTRATE LAYER (Governed Operations)
**Memory Layer - ALL operations require governance routing:**
- `raw_dumps` - P0 capture (direct only, no change requests per canon)
- `context_blocks` - CREATE/UPDATE/REVISE/MERGE via change requests
- `context_items` - CREATE/UPDATE/MERGE via change requests
- `basket anchors` - Metadata registry only. Anchor content is always mediated through block/context operations above; registry updates may not bypass governance.
- `timeline_events` - System events (append-only, controlled)

### ARTIFACT LAYER (Independent Operations)
**Expression Layer - NO governance required:**
- `documents` - Direct CRUD operations, free user editing
- `reflections` - Direct generation from substrate, computed insights
- `substrate_references` - Document-substrate linking (metadata only)
- `document_composition_stats` - Analytics and metrics

### CANON-BREAKING PATTERNS TO ELIMINATE
❌ **P3/P4 regeneration through governance** - Insights/Documents are artifacts, regenerated directly
❌ **Document editing** - Documents are immutable, evolution via regeneration only
❌ **Reflection creation through change requests** - Reflections computed directly from substrate
❌ **Universal governance for all operations** - Violates substrate/artifact separation
❌ **Anchor CRUD that bypasses Decision Gateway** - Capture/revise/delete must be expressed as block/context operations. Registry metadata may be edited, but substrate mutations route through governance.

---

## 🔄 Change Request Lifecycle

### States
```
DRAFT → PROPOSED → UNDER_REVIEW → [APPROVED | REJECTED]
                                     ↓
                                 COMMITTED
```

**Additional Terminal States**:
- `SUPERSEDED` - Replaced by newer proposal
- `MERGED` - Combined with other proposals

### State Transitions

**PROPOSED** (Entry point for agent-originated):
- Agent validation complete
- **Auto-approval criteria**:
  - Agent origin + confidence > 0.7 → Auto-approved
  - Type 1a (Assignment) + confidence > 0.85 → Auto-approved
  - Low confidence or warnings → Requires manual review
- Agent proposals skip DRAFT state

**APPROVED**:
- Operations committed to substrate atomically
- If Type 1a: Dump assigned to basket, then substrate mutations execute
- If Type 1b: Cross-basket relationships created
- If Type 2: Basket substrate updated
- Timeline events emitted to affected baskets
- Notifications generated (domain-agnostic event emission)

---

## 🎯 Routing & UX Clarity

### Workspace-Level Review
**Route**: `/workspace/change-requests`

**What Appears Here**:
- All Type 1 proposals (scope = 'workspace' OR 'cross-basket')
- Optionally: Can show basket-level proposals grouped by basket for overview

**Actions**:
- Approve/reject workspace operations
- Assign captures to baskets (Type 1a)
- Review cross-basket impacts (Type 1b)

### Basket-Level Review
**Route**: `/baskets/[id]/change-requests`

**What Appears Here**:
- Type 2 proposals where `basket_id = X`
- Type 1b proposals where `X IN affected_basket_ids` (cross-basket view)

**Actions**:
- Approve/reject basket substrate mutations
- See cross-basket proposals affecting this basket

---

## 📡 Event Emission (Domain Boundary)

### Change Requests Generate Events

When change request lifecycle transitions occur, **notifications are emitted** (separate domain):

```typescript
// Example: When Type 1a proposal created
await notificationService.emit({
  type: 'governance.workspace_proposal',
  category: 'governance',
  severity: 'info',
  title: 'Workspace change request pending',
  message: `Basket assignment for "${capture.summary}" awaiting review`,
  governance_context: {
    requires_approval: true,
    auto_approvable: proposal.confidence > 0.85
  },
  related_entities: {
    workspace_id,
    proposal_id: proposal.id
  },
  actions: [{
    label: 'Review',
    href: `/workspace/change-requests#${proposal.id}`
  }]
});

// Example: When Type 2 proposal approved
await notificationService.emit({
  type: 'governance.basket_proposal_approved',
  category: 'governance',
  severity: 'success',
  title: 'Change request approved',
  message: `Substrate updated: ${proposal.ops_summary}`,
  related_entities: {
    basket_id: proposal.basket_id,
    proposal_id: proposal.id
  }
});

// Timeline event also logged (separate concern)
await timelineService.log({
  basket_id: proposal.basket_id,
  kind: 'proposal.approved',
  ref_id: proposal.id,
  payload: { ops_summary, origin }
});
```

**Key Insight**: Change requests **participate** in governance, notifications **observe** governance. Clean domain separation.

---

## 🛡️ Security & Isolation

### Workspace Isolation
- All governance settings scoped by `workspace_id`
- RLS policies enforce workspace membership
- No cross-workspace governance leakage

### Access Control
- **Proposal creation**: Any workspace member
- **Proposal approval**:
  - Workspace-level proposals: Owner/admin role required
  - Basket-level proposals: Basket collaborator with edit permission
- **Governance settings**: Owner role required
- **Validator configuration**: System admin only

---

## 🔧 API Endpoints

### Workspace-Level
- **GET /api/workspace/change-requests** - Query workspace + cross-basket proposals
- **POST /api/workspace/change-requests** - Create workspace-scoped proposals
- **POST /api/workspace/change-requests/[id]/approve** - Approve workspace proposal
- **POST /api/workspace/change-requests/[id]/reject** - Reject with reason

### Basket-Level
- **GET /api/baskets/[id]/change-requests** - Query basket-scoped proposals
- **POST /api/baskets/[id]/change-requests** - Create basket proposals
- **POST /api/baskets/[id]/change-requests/[proposalId]/approve** - Approve basket proposal
- **POST /api/baskets/[id]/change-requests/[proposalId]/reject** - Reject with reason

### Universal Change Endpoint
- **POST /api/changes** - Decision Gateway for all mutations (determines scope and routing)

---

## 📋 Implementation Checklist

### Phase 1: Schema Migration
- [ ] Make `proposals.basket_id` nullable
- [ ] Add `scope`, `target_basket_id`, `affected_basket_ids` columns
- [ ] Add new proposal kinds for workspace operations
- [ ] Create indexes for workspace-scoped queries
- [ ] Backfill existing proposals with scope='basket'

### Phase 2: Workspace Change Request UI
- [ ] Create `/workspace/change-requests` page
- [ ] Build WorkspaceChangeRequestsClient component
- [ ] Implement filter tabs (All, Assignments, Cross-Basket, Workspace)
- [ ] Add approve/reject actions
- [ ] Wire up to workspace proposals API

### Phase 3: Route Cleanup
- [ ] Rename `/memory/unassigned` → `/workspace/change-requests?view=assignments`
- [ ] Update dashboard link to workspace change requests
- [ ] Update sidebar navigation
- [ ] Rename `/baskets/[id]/governance` → `/baskets/[id]/change-requests`

### Phase 4: Event Integration
- [ ] Wire notification emission on proposal lifecycle events
- [ ] Ensure timeline events logged for approved proposals
- [ ] Add deep links from notifications to change request pages

---

## 🎓 Mental Model Summary

### For Users

**"Where do I review change requests?"**
- **Workspace-level**: Things affecting multiple baskets or needing basket assignment → `/workspace/change-requests`
- **Basket-level**: Things within a single basket's knowledge → `/baskets/[id]/change-requests`

**"What's the difference?"**
- **Workspace** = Coordination (assign captures, cross-basket ops, create baskets)
- **Basket** = Focused curation (evolve substrate within this context)

### For Developers

**Change Requests** = Governance domain (substrate mutation control)
**Notifications** = Observability domain (event communication)
**Timeline** = Historical domain (knowledge evolution narrative)

Clean separation, clear boundaries, canonical purity.

---

*This canon ensures governance scales elegantly from single-basket simplicity to multi-basket coordination, preserving substrate quality while adapting to MCP-driven ambient intelligence workflows.*
