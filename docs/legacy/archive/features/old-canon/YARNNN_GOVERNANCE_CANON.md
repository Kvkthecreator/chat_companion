# YARNNN Governance Canon v4.0.0 — Unified Governance Architecture

**The Single Source of Truth for Governance Framework, Settings Policy, and Universal Work Orchestration**

This document consolidates governance architecture, workspace settings policy, and universal work orchestration into a comprehensive governance reference.

## Sacred Principles

**Governance Sacred Principle #1**: All substrate mutations flow through governed proposals
**Governance Sacred Principle #2**: Proposals target substrates only - artifacts operate independently
**Governance Sacred Principle #3**: Agent validation is mandatory for substrate proposals only

## 🚨 CRITICAL: Substrate vs Artifact Governance Boundaries

### SUBSTRATE LAYER (Governed Operations)
**Memory Layer - ALL operations require governance routing:**
- `raw_dumps` - P0 capture (direct only, no proposals per canon)
- `context_blocks` - CREATE/UPDATE/REVISE/MERGE via proposals
- `context_items` - CREATE/UPDATE/MERGE via proposals  
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
❌ **Reflection creation through proposals** - Reflections computed directly from substrate
❌ **Universal governance for all operations** - Violates substrate/artifact separation
❌ **Anchor CRUD that bypasses Decision Gateway** - Capture/revise/delete must be expressed as block/context operations. Registry metadata may be edited, but substrate mutations route through governance.

### P3/P4 ARTIFACT OPERATIONS (NOT GOVERNED)
✅ **P3 Insight Regeneration** - Direct POST endpoints, context-driven freshness checks
✅ **P4 Document Composition** - Direct POST endpoints, regenerate from P3 + substrate
✅ **Lineage Tracking** - All artifacts link previous versions (previous_id)
✅ **Provenance Recording** - All artifacts record derived_from sources
✅ **Policy Controls** - Auto-regeneration flags, workspace synthesis permissions (not governance proposals)

## 🏛️ Governance Architecture

### Workspace-Scoped Control
Governance operates at the **workspace level**, providing fine-grained control over substrate mutation policies:

```sql
-- Governance is configured per workspace
workspace_governance_settings {
  workspace_id: uuid PRIMARY KEY,
  governance_enabled: boolean DEFAULT true,
  validator_required: boolean DEFAULT false,
  direct_substrate_writes: boolean DEFAULT false,
  governance_ui_enabled: boolean DEFAULT false,
  
  -- Per-entry-point policies (substrate only)
  ep_onboarding_dump: 'direct',              -- P0 capture is always direct (no proposals)
  ep_manual_edit: 'proposal' | 'direct' | 'hybrid',
  ep_graph_action: 'proposal' | 'direct' | 'hybrid',
  ep_timeline_restore: 'proposal' | 'direct' | 'hybrid',
  -- REMOVED: ep_document_edit - documents are artifacts
  
  -- Risk-based routing
  default_blast_radius: 'Local' | 'Scoped' | 'Global',
  hybrid_risk_threshold: 'low' | 'medium' | 'high'
}
```

### Decision Gateway (Single Choke-Point)
All substrate mutations flow through the **Decision Gateway**, which routes changes based on workspace governance settings:

```typescript
// The unified entry point for all substrate changes
await routeChange(supabase: SupabaseClient, cd: ChangeDescriptor): Promise<ChangeResult>
```

**ChangeDescriptor** provides unified abstraction for all mutation intents:
```typescript
interface ChangeDescriptor {
  entry_point: 'onboarding_dump' | 'manual_edit' | 'graph_action' | 'timeline_restore',
  actor_id: string,
  workspace_id: string,
  basket_id?: string,
  document_id?: string,
  blast_radius?: 'Local' | 'Scoped' | 'Global',
  ops: Operation[],
  provenance: ProvenanceEntry[]
}
```

### PolicyDecider (Routing Logic)
Centralized logic determines whether changes go **direct** to substrate or through **proposals**:

```typescript
function decide(
  flags: WorkspaceFlags,
  cd: ChangeDescriptor, 
  riskHints?: RiskHints
): Decision {
  route: 'direct' | 'proposal',
  require_validator: boolean,
  validator_mode: 'strict' | 'lenient',
  effective_blast_radius: BlastRadius,
  reason: string
}
```

## 🔄 Dual Ingestion Model

### Sacred Capture Path (Standard Agent Flow)
```
raw_dumps (P0 direct) + existing_substrate → P1 Governed Evolution → Proposal (with Operations) → [Approval | Auto-Approval (policy)] → Substrate Evolution
```

**P1 Evolution Agent Process**:
1. **Context Analysis**: Reads new dumps + existing substrate in basket
2. **Evolution Planning**: Determines what operations are needed:
   - Novel concepts → CREATE operations
   - Refined understanding → UPDATE/REVISE operations  
   - Duplicate detection → MERGE operations
3. **Proposal Generation**: Mixed operation types based on basket maturity
4. **High confidence proposals auto-approved for immediate substrate evolution**

### Manual Curation Path (Substrate Only)
```  
Human Intent → ChangeDescriptor → PolicyDecider → proposal → Agent Validation → Substrate
```

**Key**: Both paths converge at the Decision Gateway, preserving agent intelligence while enabling human curation.

## 📝 The Proposal Model

### Proposal Anatomy
```typescript
interface Proposal {
  // Identity
  id: uuid,
  proposal_kind: 'Extraction' | 'Edit' | 'Merge' | 'Attachment' | 'ScopePromotion' | 'Deprecation',
  
  // Foundation  
  basis: 'HEAD' | snapshot_id,     // What state authored against
  origin: 'agent' | 'human',       // Source of intent
  provenance: ProvenanceEntry[],   // Raw material references
  
  // Operations (atomic changesets)
  ops: Operation[],
  blast_radius: 'Local' | 'Scoped' | 'Global',
  
  // Agent Intelligence (mandatory)
  validator_report: {
    confidence: number,
    dupes: ProposalConflict[],
    ontology_hits: string[],
    suggested_merges: uuid[],
    warnings: string[],
    impact_summary: string
  },
  
  // Governance
  status: ProposalState,
  review: ReviewDecision?,
  effects_preview: CascadePreview
}
```

### Proposal Operations Schema
**P1 Evolution Agent Operations** (substrate lifecycle management):
```typescript
// Creation operations - novel concepts not in existing substrate
{
  type: "CreateBlock",
  content: string,                    // New content from raw_dumps
  semantic_type: "insight" | "fact" | "plan" | "reflection",
  confidence: number                  // 0.0-1.0 confidence score
}

{
  type: "CreateContextItem", 
  label: string,                     // New concept identifier
  kind: "project" | "person" | "concept" | "goal",
  synonyms: string[],               // Alternative labels
  confidence: number                // 0.0-1.0 confidence score
}

// Evolution operations - refining existing substrate
{
  type: "ReviseBlock",
  block_id: string,                  // Target existing block
  content: string,                   // Updated content
  confidence: number                 // Confidence in revision
}

{
  type: "MergeContextItems",
  from_ids: string[],               // Items to merge  
  canonical_id: string,             // Surviving item
  merged_synonyms: string[]         // Combined synonyms
}

{
  type: "UpdateContextItem", 
  context_item_id: string,          // Target existing item
  label?: string,                   // Optional label update
  additional_synonyms?: string[]    // Optional new synonyms
}
```

**Other Operations** (curation and maintenance):
- `AttachBlockToDoc { block_id, document_id }`
- `MergeContextItems { from_ids[], canonical_id }`
- `ReviseBlock { block_id, content, confidence }`
- `PromoteScope { block_id, from: LOCAL, to: WORKSPACE }`

## 🔀 Policy-Based Routing

### Entry Point Policies
Each entry point can be configured with one of three policies:

- **proposal**: All changes create proposals requiring human approval
- **direct**: Only for P0 capture (raw_dumps). For P1/P2 substrate mutations, direct commits are disabled by default.
- **hybrid**: Risk-based routing for certain entry points (e.g., manual edits); high risk becomes proposals

### Risk-Based Hybrid Routing
When `hybrid` policy is active, the PolicyDecider evaluates:

**Low Risk** (direct commit):
- Single `CreateBlock` operations
- `Local` blast radius changes
- High confidence validator reports

**High Risk** (proposal required):
- `PromoteScope` to `GLOBAL`
- `MergeContextItems` operations
- `Global` blast radius changes
- Low confidence or validation warnings

## 🔄 Proposal Lifecycle

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

**DRAFT** (Human-originated only):
- User crafts intent in UI
- Not yet validated
- Can be edited freely

**PROPOSED** (Entry point for agent-originated):
- Agent validation complete
- **Auto-approval criteria**:
  - Agent origin + confidence > 0.7 → Auto-approved
  - Low confidence or warnings → Requires manual review
- Agent proposals skip DRAFT state

**UNDER_REVIEW**:
- Human reviewer assigned
- Impact analysis displayed
- Can be approved, rejected, or split

**APPROVED**:
- Operations committed to substrate atomically
- Cascade events emitted
- Effects propagated to intelligence layer

## 🤖 Agent Integration

### Mandatory Agent Validation
**All proposals require agent validation** before governance review:

1. **P1 Validator Agent** (mandatory):
   - Normalizes fields and labels
   - Flags duplicates and suggests merges  
   - Computes impact reports
   - Maps to existing ontologies
   - Sets confidence scores

2. **Impact Monitor Agent** (post-commit):
   - Emits cascade events after approval
   - Provides recompute hints for intelligence layer
   - Performs drift analysis for documents

### Agent Intelligence Preservation
Even manual proposals maintain agent intelligence through:
- Mandatory validation phase
- Confidence scoring for human-created content
- Automated duplicate detection
- Impact analysis and warnings

## 🌊 Cascade Policy

### On Proposal Approval
**Immediate Effects**:
1. Operations committed to substrate tables atomically
2. Timeline events emitted with full provenance
3. Substrate relationships updated
4. Context_items state transitions executed

**Intelligence Layer Reactions**:
- **Graph**: Recomputes HEAD immediately
- **Timeline**: Appends governance events (never rewrites)
- **Reflections**: Marked stale when basis changes, offers recompute
- **Documents**: Snapshot-bound docs show drift warnings

### Event Types
**Governance Timeline Events**:
- `proposal.submitted`
- `proposal.approved`  
- `proposal.rejected`
- `substrate.committed`
- `cascade.completed`

## 🔧 Implementation Components

### Database Schema
```sql
-- Core governance table
CREATE TABLE proposals (
  id uuid PRIMARY KEY,
  basket_id uuid,
  workspace_id uuid NOT NULL,
  proposal_kind proposal_kind NOT NULL,
  basis_snapshot_id uuid,
  origin text CHECK (origin IN ('agent', 'human')),
  provenance jsonb DEFAULT '[]',
  ops jsonb NOT NULL,
  blast_radius blast_radius DEFAULT 'Local',
  validator_report jsonb DEFAULT '{}',
  status proposal_state DEFAULT 'PROPOSED',
  created_by uuid,
  created_at timestamptz DEFAULT now(),
  reviewed_by uuid,
  reviewed_at timestamptz,
  review_notes text
);

-- Execution tracking
CREATE TABLE proposal_executions (
  id uuid PRIMARY KEY,
  proposal_id uuid REFERENCES proposals(id),
  executed_at timestamptz DEFAULT now(),
  operations_count int NOT NULL,
  operations_summary jsonb DEFAULT '{}',
  substrate_ids jsonb DEFAULT '[]'
);

-- Workspace governance settings
CREATE TABLE workspace_governance_settings (
  workspace_id uuid PRIMARY KEY REFERENCES workspaces(id),
  governance_enabled boolean DEFAULT false,
  validator_required boolean DEFAULT false,
  direct_substrate_writes boolean DEFAULT true,
  governance_ui_enabled boolean DEFAULT false,
  ep_onboarding_dump text DEFAULT 'proposal',
  ep_manual_edit text DEFAULT 'proposal',
  ep_graph_action text DEFAULT 'proposal',
  ep_timeline_restore text DEFAULT 'proposal',
  -- REMOVED: ep_document_edit - documents are artifacts, not substrates
  default_blast_radius blast_radius DEFAULT 'Local',
  hybrid_risk_threshold text DEFAULT 'medium'
);
```

### API Endpoints
- **POST /api/baskets/[id]/proposals** - Create proposals with mandatory validation
- **POST /api/baskets/[id]/proposals/[proposalId]/approve** - Execute operations atomically
- **POST /api/baskets/[id]/proposals/[proposalId]/reject** - Reject with reason
- **GET /api/governance/workspace/settings** - Get workspace governance configuration
- **POST /api/changes** - Universal change endpoint using Decision Gateway

### Core Services
- **Decision Gateway** (`/web/lib/governance/decisionGateway.ts`) - Single choke-point for all mutations
- **PolicyDecider** (`/web/lib/governance/policyDecider.ts`) - Centralized routing logic
- **Workspace Flags** (`/web/lib/governance/flagsServer.ts`) - Workspace-scoped governance evaluation
- **Change Descriptor** (`/web/lib/governance/changeDescriptor.ts`) - Unified change abstraction

## 🎯 Backward Compatibility

### Universal Change Service
The new governance system maintains backward compatibility with existing change workflows through:

- **Legacy format support** in `/api/changes` endpoint
- **Automatic descriptor creation** for existing API calls
- **Gradual migration path** via workspace governance settings
- **Feature flag controls** for safe rollout

### Migration Strategy
1. **Phase 1**: Deploy with `governance_enabled: false` (direct writes continue)
2. **Phase 2**: Enable validation (`validator_required: true`)
3. **Phase 3**: Enable governance UI (`governance_ui_enabled: true`)  
4. **Phase 4**: Switch to proposal-first (`direct_substrate_writes: false`)

## 🛡️ Security & Isolation

### Workspace Isolation
- All governance settings scoped by `workspace_id`
- RLS policies enforce workspace membership
- No cross-workspace governance leakage

### Access Control
- Proposal creation: Any workspace member
- Proposal approval: Owner role required
- Governance settings: Owner role required
- Validator configuration: System admin only

---

*Governance ensures substrate quality while preserving the sacred capture → intelligence → make flow that defines YARNNN's value proposition.*

---

## 🎛️ Workspace Settings Policy (Canon-Safe Implementation)

### Purpose
Prevent configuration drift and UX ambiguity by documenting the canon-safe subset of governance controls exposed in the product.

### Product Controls (Simplified User Interface)

**Visible Controls (Plain Language):**
- **Governance**: on/off (default: on)
- **Review Mode**: 
  - Review everything (Proposal)
  - Smart review (Hybrid) — lets YARNNN auto-approve small, safe changes
- **Always run validator**: on/off 
  - When on, proposals cannot be auto-approved
- **Change scope** (default reach): Local (basket) or Scoped (workspace)

**Fixed Controls (Canon-Enforced):**
- Capture (P0) is always immediate (Direct)
- Timeline Restore always requires review (Proposal)
- Direct substrate writes are disabled globally
- Artifact entry points (documents/reflections) are out of scope

### Server Enforcement & Coercions

**Role Requirements:**
- Role: owner/admin may update (Owners are canonical admins)

**Automatic Coercions:**
- `ep_onboarding_dump` = `direct` (P0 capture always immediate)
- `timeline_restore` = `proposal` (always requires review)
- Review Mode controls `manual_edit` + `graph_action` together: `proposal` or `hybrid`
- `direct` is not allowed for `manual_edit`/`graph_action`
- `default_blast_radius`: coerce `Global` → `Scoped`
- `direct_substrate_writes` → `false` (globally disabled)

### Default Settings
When settings are absent:
- `onboarding_dump='direct'`, `manual_edit='proposal'`, `graph_action='proposal'`, `timeline_restore='proposal'`, `default_blast_radius='Scoped'`
- Matches `public.get_workspace_governance_flags()` fallback behavior

### Rationale
- Keeps capture immediate to preserve P0→P1 pipeline, eliminates 'Capture' proposals
- Preserves governance for substrate evolution where it matters
- Prevents artifact/substrate conflation and dangerous bypasses

---

## 🎵 Universal Work Orchestration Integration

### Architectural Extension: Beyond Dump Processing

YARNNN users initiate async operations through multiple entry points:
- **P0→P1→P2→P3 Pipeline**: Raw dump ingestion and processing
- **Governance Operations**: Manual proposal creation and approval
- **Direct Substrate Edits**: Block/context item modifications
- **Document Composition**: P4 artifact creation from substrate
- **Graph Operations**: P2 relationship mapping
- **Timeline Restoration**: Historical state recovery

### Solution: Canonical Queue as Universal Orchestrator

The `canonical_queue` table becomes the single source of truth for ALL async work in YARNNN, integrating seamlessly with governance.

### Enhanced Canonical Queue Schema

```sql
-- Enhanced canonical_queue schema (Canon v2.1 + Governance Integration)
CREATE TABLE canonical_queue (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Work Identification
    work_type text NOT NULL, -- P1_SUBSTRATE | P2_GRAPH | P3_REFLECTION | MANUAL_EDIT | DOCUMENT_COMPOSE | PROPOSAL_REVIEW
    work_id text, -- Optional: dump_id, proposal_id, document_id, etc
    
    -- Context & Governance
    basket_id uuid,
    workspace_id uuid NOT NULL,
    user_id uuid, -- Who initiated this work
    governance_mode text, -- 'direct' | 'proposal' | 'auto_approved'
    
    -- Orchestration
    status text NOT NULL DEFAULT 'pending', -- pending | claimed | processing | cascading | completed | failed
    processing_stage text, -- Stage-specific status (validating | extracting | approving | etc)
    worker_id text,
    priority integer DEFAULT 5,
    
    -- Payload & Results
    work_payload jsonb DEFAULT '{}', -- Input data for work
    work_result jsonb DEFAULT '{}', -- Output data from completed work
    cascade_metadata jsonb DEFAULT '{}', -- Cross-pipeline coordination
    
    -- Governance Integration
    proposal_id uuid, -- Links to proposals table when applicable
    confidence_score numeric, -- AI confidence for auto-approval decisions
    
    -- Timestamps
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    claimed_at timestamptz,
    completed_at timestamptz
);
```

### Governance-Work Integration Patterns

**Direct Work (P0 Capture):**
```
User Input → canonical_queue(work_type='P0_CAPTURE', governance_mode='direct') → Immediate Processing
```

**Governed Work (P1 Substrate):**
```
Agent Analysis → canonical_queue(work_type='P1_SUBSTRATE', governance_mode='proposal') → Proposal Creation → Approval → Substrate Mutation
```

**Auto-Approved Work (High Confidence):**
```
Agent Analysis → canonical_queue(work_type='P1_SUBSTRATE', governance_mode='auto_approved') → Immediate Substrate Mutation + Audit Trail
```

### Universal Status Derivation

All YARNNN operations now provide consistent status visibility through the canonical queue:

**Frontend Status Integration:**
- Work status indicators pull from `canonical_queue.status`
- Cross-page status persistence via workspace context
- Real-time updates via Supabase subscriptions
- Governance decisions visible in work timeline

**API Endpoints for Universal Status:**
- `GET /api/work/{work_id}/status` — Canonical per-work status
- `GET /api/work/workspace/{workspace_id}/summary` — Workspace-level work summary
- Both endpoints enforce workspace isolation via RLS + server validation

### Governance-Orchestration Benefits

1. **Unified Status Model**: All async operations visible through single interface
2. **Governance Compliance**: Every work item respects workspace governance settings
3. **Audit Trail**: Complete traceability from user action through governance to completion
4. **Performance Optimization**: Single queue enables intelligent work scheduling
5. **Cross-Pipeline Coordination**: Cascade metadata enables P1→P2→P3 orchestration

This unified governance-orchestration model ensures that governance is not an afterthought but an integral part of YARNNN's operational architecture, providing users with both control and visibility into their cognitive workspace operations.
