# YARNNN Canon v3.1 — The Authoritative Reference

**⚠️ STATUS (2025-10-31)**: This document describes YARNNN v3.1 architecture. For current v4.0 documentation, see [docs/canon/YARNNN_PLATFORM_CANON_V4.md](canon/YARNNN_PLATFORM_CANON_V4.md)

**The Single Source of Truth for Yarnnn Service Philosophy and Implementation**

**🚨 MAJOR UPDATE (2025-01-15)**: Architecture upgraded to v3.1 - Semantic Layer Integration
- **v3.0**: Substrate unified (context_items → blocks), emergent anchors, universal versioning
- **v3.1**: Semantic intelligence layer (vector embeddings + causal relationships)
- **See**: [YARNNN_SUBSTRATE_CANON_V3.md](./YARNNN_SUBSTRATE_CANON_V3.md) for substrate reference
- **See**: [archive/planning/SEMANTIC_LAYER_INTEGRATION_DESIGN.md](archive/planning/SEMANTIC_LAYER_INTEGRATION_DESIGN.md) for historical semantic architecture (archived)

## 🌊 Core Philosophy: Memory-First, Substrate-Equal

Yarnnn is a **memory-first cognitive system** that captures human thought as immutable substrate, allows it to evolve through agent interpretation, and presents it back through deliberate narrative composition.

### The Five Sacred Principles

1. **Capture is Sacred** - All user input becomes an immutable `raw_dump`
2. **All Substrates are Peers** - No substrate type is privileged over another
3. **Narrative is Deliberate** - Documents are composed views of substrate, not editable artifacts
4. **Agent Intelligence is Mandatory** - Substrate cannot exist without agent interpretation
5. **Substrate Management Replaces Document Editing** - Users curate substrate and direct composition instead of editing prose

### The Three Governance Principles (v2.2) ✅ IMPLEMENTED

1. **Substrate-Only Governance** - ALL substrate mutations flow through governance framework
2. **User-Controlled Execution Mode** - Users control execution policy via governance flags
3. **Confidence-Informed Routing** - Confidence scores inform routing within governance modes

**📋 Governance Status (As of 2025-11-05)**:
- ✅ Substrate governance (P1 proposals) - WORKING
- ⚠️ Work-platform governance - NOT YET DEFINED (see v4.0 docs)
- ✅ Governance purity enforced - All blocks via proposals

**See**: [`GOVERNANCE_SEPARATION_REFACTOR_PLAN.md`](architecture/GOVERNANCE_SEPARATION_REFACTOR_PLAN.md) for current state.

### 🚨 CRITICAL: Governance Scope Boundaries

**GOVERNED (Substrate Layer - Memory):**
- `raw_dumps` creation (P0 - direct only, no proposals)
- `blocks` mutations (P1 - via proposals, all semantic_types) ✅ ENFORCED
- `timeline_events` (system controlled)

**INDEPENDENT (Artifact Layer - Expression):**
- **P3 Insights** - Direct regeneration from substrate state (insight_canon, doc_insight, timeboxed_insight)
- **P4 Documents** - Direct composition from P3 + substrate (document_canon, starter_prompt)
- `substrate_references` - Document-substrate metadata linking
- All artifact analytics and composition stats
- **Review insights** - Computed ephemeral (cached in proposals table for audit)

**P3/P4 Governance Boundary**:
- Regeneration is **DIRECT** (not governed proposals) - artifacts derived from substrate, don't mutate it
- Policy controls: Auto-regeneration flags, workspace synthesis permissions, throttling
- Freshness computed from context (substrate_hash, graph_signature), not time thresholds

**Canon v3.0 Revolution**: Documents are no longer editable. They are composed views of substrate state that regenerate when substrate changes or composition instructions are refined. Users manage substrate, not prose.

## 🎯 Conceptual Model

```
User Thought → Raw Capture → Agent Processing → Substrate Evolution → Reflection Derivation → Narrative Composition
     ↓             ↓              ↓                    ↓                      ↓                    ↓
  Memory       Immutable      Intelligence        Structured            Read-Model           Deliberate
  Stream        Dumps          Required           Substrates            Patterns             Documents
```

## 📚 Substrate vs Artifact Distinction

### Three Substrate Types (Memory Layer) — v3.0

1. **raw_dumps** - Immutable user input (text, files, captures) - Sacred capture
2. **blocks** - ALL structured substrate (knowledge, meaning, structural) - Unified memory
   - `semantic_type` differentiates: `fact`, `intent`, `entity`, `metric`, etc.
   - Emergent `anchor_role` for strategic categorization
   - Universal versioning via `parent_block_id` chains
   - Scope elevation for cross-basket memory (`WORKSPACE`, `ORG`, `GLOBAL`)
3. **timeline_events** - Append-only activity stream - System memory

**Critical v3.0 change**: `context_items` merged into `blocks` table for unified substrate architecture.

**See**: [YARNNN_SUBSTRATE_CANON_V3.md](./YARNNN_SUBSTRATE_CANON_V3.md) for complete details on:
- Semantic types (knowledge vs meaning vs structural)
- Emergent anchor system (no predefined roles)
- Universal versioning (all blocks version identically)
- Scope levels (basket → workspace → org → global memory)

### Two Artifact Types (Expression Layer)

**P3: Insights** - Immutable interpretations of substrate (understanding what matters)
- `insight_canon` - Basket-level "what matters now" (one current per basket)
- `doc_insight` - Document-scoped interpretations (one per document)
- `timeboxed_insight` - Temporal window understanding (many per basket)
- `review_insight` - Proposal evaluation intelligence (ephemeral, computed)
- Cross-basket insights - Workspace-level synthesis (one current per workspace)

**P4: Documents** - Immutable governed views of substrate (activation surfaces)
- `document_canon` - Basket Context Canon (mandatory: one per basket)
- `starter_prompt` - Reasoning capsules for external hosts (many per basket)
- `artifact_other` - Future document types (extensible)

**Critical**: Artifacts are derived FROM substrates, never the reverse. No artifact recursion.

**P3/P4 Revolution**:
- **Insights (P3)** = Interpretive intelligence layer - "what matters now"
- **Documents (P4)** = Composition definitions generating versioned snapshots
- **Immutability**: Content never edited in place - evolution via regeneration only
- **Lineage**: Every artifact tracks previous versions via `previous_id`
- **Provenance**: Every artifact records `derived_from` (blocks, reflections, proposals)
- **Context-Driven Freshness**: Staleness computed from substrate_hash + graph_signature changes, not time

## 🔄 The Four Pipelines (Substrate → Artifacts)

| Pipeline | Layer | Purpose | Sacred Rule | V3.1 Semantic Layer |
|----------|-------|---------|-------------|---------------------|
| **P0: Capture** | Substrate | Ingest raw memory | Only writes raw_dumps, never interprets (always direct, no proposals) | **NO CHANGE** - Raw dumps not embedded |
| **P1: Governed Evolution** | Substrate | Intelligent substrate evolution with duplicate detection | **All Create/Revise/Merge via governance proposals** | **UPGRADED** - Uses semantic search for duplicate/merge detection |
| **P3: Insights** | Artifact | Generate interpretive intelligence | Creates P3 insights, never modifies substrate | **ENHANCED** - Semantic retrieval for deeper insights |
| **P4: Documents** | Artifact | Theme-based narrative composition | Creates P4 documents, consumes substrate + P3 insights | **ENHANCED** - Semantic theme search for narrative coherence |

**Note:** P2 Graph Intelligence has been **permanently removed** (Canon v3.1). It was replaced by **Neural Map** - a zero-cost client-side visualization that clusters substrate by semantic type into brain regions. See rationale below.

### Why P2 Relationships Were Removed (Canon v3.1)

**Decision:** P2 Graph Agent and `substrate_relationships` table removed entirely from codebase.

**Rationale:**
1. **Semantic Type Mismatch**: P1 extraction produced semantic types (`fact`, `finding`, `insight`, `metric`) that were incompatible with P2's relationship ontology (`problem`, `constraint`, `solution`). Even relationship-rich data produced 0 relationships due to vocabulary misalignment.

2. **Minimal Integration**: P3 used relationships only for a single pattern check (≥3 relationships). P4 included them in prompts but degraded gracefully. Neither pipeline depended on relationships for core value.

3. **Canon Contradiction**: YARNNN_CANON.md line 112 explicitly stated P2 was replaced by Neural Map, yet full P2 implementation remained in codebase, creating architectural confusion.

4. **Semantic Search Superiority**: Embeddings provide more powerful substrate discovery than explicit relationships. P3/P4 use semantic similarity for context retrieval and composition.

5. **Simplicity**: Removing dual approaches (explicit relationships AND semantic search) reduces complexity and maintenance burden.

**What Replaced It:**
- **Neural Map** (client-side): Visual clustering of substrate by semantic type
- **Semantic Search** (server-side): Vector similarity for P1 duplicate detection, P3 context, P4 composition

**Impact:** Zero degradation. P3/P4 workflows unchanged. Simplified architecture aligns with Canon.

### V3.1 Semantic Layer: Core Upgrade

**What Changed:**
- **P1**: Semantic duplicate detection (merge vs create decisions based on vector similarity)
- **P3**: Semantic context retrieval (find relevant blocks without keyword matching)
- **P4**: Theme-based composition (semantic search for narrative coherence)
- **Visualization**: Neural Map replaces P2 graph inference (zero-cost brain-based clustering)

**What Didn't Change:**
- **P0**: Raw dumps remain unembedded (transient input, not persistent memory)
- **Governance**: All substrate mutations still flow through proposals
- **Structure**: Anchors, versioning, lifecycle still primary organizing principles

**Key Insight**: Semantic layer **augments** structured substrate, doesn't replace it. We're not building RAG—we're building structured memory with semantic intelligence.

### Pipeline Detail: P0→P1 Substrate Scaffolding

**P0: Capture Phase**
```
User Input → Collection of raw_dumps (unstructured)
- Text, PDFs, images become immutable raw_dumps
- Multiple inputs in one session linked by batch/provenance
- No interpretation, pure capture
```

**P1: Governed Evolution Phase (Propose → Commit) - V3.1 UPGRADED**
```
New raw_dumps + Existing substrate → Agent Analysis → Semantic Duplicate Detection → Governance Proposal → Approval → Substrate Evolution

1. Agent reads new raw_dumps collectively
2. Agent extracts facts/insights from dumps
3. V3.1: For each extracted fact, semantic search for similar existing blocks
   - similarity > 0.85 → Propose MERGE (high confidence duplicate)
   - similarity 0.70-0.85 → Propose UPDATE/ENRICH (related content)
   - similarity < 0.70 → Propose CREATE (novel content)
4. Agent determines evolution operations based on semantic analysis
5. Proposal approval → Operations executed atomically → Substrate evolved
6. V3.1: After block creation, generate embedding (for future searches)
```

**V3.0 Foundation**: All substrate unified into blocks table (semantic_type differentiates)
**V3.1 Upgrade**: Semantic duplicate detection via vector embeddings (text-embedding-3-small)

**Critical Insight**: P1 evolved from "extraction agent" → "intelligent substrate evolution agent". Semantic search enables detecting duplicates that keyword matching misses (e.g., "login failure" matches "authentication bug").

### Pipeline Detail: P3→P4 Artifact Generation

**P3: Insights Phase (Interpretive Intelligence)**
```
Substrate State + Reflections → Agent Analysis → P3 Insight Generation → Lineage Tracking

Insight Types:
1. insight_canon (basket-level): "What matters now in this basket?"
   - Cardinality: ONE current per basket (health invariant)
   - Regeneration: Creates new version, marks previous non-current
   - Freshness: Computed from substrate_hash + graph_signature changes

2. doc_insight (document-level): "What does this document mean?"
   - Cardinality: ONE per document (many documents = many insights)
   - Scope: Attached to specific document_id
   - Freshness: Recomputed when document's substrate_references change

3. timeboxed_insight (temporal): "What mattered in Q3 2025?"
   - Cardinality: MANY per basket (different time windows)
   - Scope: Explicit temporal_scope metadata
   - Freshness: Immutable for historical windows, active for current period

4. review_insight (governance): "Should this proposal be approved?"
   - Cardinality: ONE per proposal (ephemeral, computed on-demand)
   - Storage: Cached in proposals.review_insight (not in reflections_artifact)
   - Purpose: Internal governance intelligence only

5. Cross-basket insights (workspace-level): "What matters across all my contexts?"
   - Cardinality: ONE current per workspace
   - Scope: Synthesizes across all basket insight_canons
   - Policy-gated: Requires workspace_insight_enabled flag
```

**P4: Documents Phase (Composition & Activation)**
```
P3 Insights + Substrate → Agent Composition → P4 Document Generation → Versioning

Document Types:
1. document_canon (Basket Context Canon):
   - Cardinality: ONE per basket (mandatory health invariant)
   - Purpose: Authoritative narrative of basket state
   - Regeneration: Creates new version when substrate/insights change
   - Content: Lives in document_versions (immutable)

2. starter_prompt (Reasoning Capsules):
   - Cardinality: MANY per basket (multiple intents: strategy, marketing, technical)
   - Purpose: Reusable activation surfaces for external hosts (Claude, ChatGPT)
   - Composition: Canon + Insights + reasoning metadata (purpose, constraints, continuity)
   - Portability: Designed for cross-host reuse

3. artifact_other (Extensible):
   - Cardinality: MANY per basket
   - Purpose: Future document types without schema changes
```

**P3/P4 Freshness Model (Context-Driven, Not Time-Driven)**
```
Staleness = f(substrate_hash_changed, graph_topology_changed, temporal_scope_invalid)

# NOT time-based
❌ WRONG: if (now() - last_generated) > 7 days: regenerate()

# Context-based
✅ RIGHT: if (current_substrate_hash != insight.substrate_hash): regenerate()
✅ RIGHT: if (current_graph_signature != insight.graph_signature): regenerate()
```

## 🏛️ Architectural Pillars

### 1. Memory-First Architecture
- User thoughts emerge from captured substrate, not imposed structure
- **Substrate Layer**: Immutable memory (raw_dumps, blocks, timeline_events) — V3.0 unified
- **Artifact Layer**: Derived expressions (documents, reflections) that never become substrate
- Unidirectional flow: Substrate → Artifacts

### 2. Governance-Mediated Evolution 🔥
- **Sacred Principle**: ALL substrate mutations flow through governance framework
- **Workspace Control**: Users configure execution policies (auto/proposal/confidence routing)
- **Agent Intelligence Preservation**: Mandatory validation for all substrate changes
- **Confidence-Informed Routing**: High-confidence operations auto-execute within governance bounds
- **Cross-cutting Impact**: Governance affects every pipeline, workflow, and user interaction

### 3. Workspace-Scoped Security
- Single workspace per user (strong guarantee)
- All access via RLS policies on workspace_memberships
- Governance settings isolated per workspace
- No client-side data synthesis allowed

### 4. Event-Driven Consistency
- Every mutation emits timeline events
- Events flow: `timeline_events` → `events` → client subscriptions
- Governance decisions audited in timeline
- Single source of truth: the substrate tables

### 5. Substrate Work Orchestration (v2.3)
- **Substrate Endpoint**: `POST /api/work` - Substrate mutations flow through governance
- **Substrate Work Types**: P0_CAPTURE, P1_SUBSTRATE, P2_GRAPH, P3_REFLECTION, MANUAL_EDIT, PROPOSAL_REVIEW, TIMELINE_RESTORE
- **Artifact Work Types**: P4_COMPOSE_NEW, P4_RECOMPOSE (document operations)
- **Governance Integration**: Substrate work evaluated against workspace governance policies
- **Direct Artifact Operations** - Documents, reflections operate independently via dedicated endpoints
- **Status Visibility**: Complete traceability for substrate mutations, simple REST for artifacts

### Governance Architecture Detail

**Sacred Principle**: All substrate mutations flow through governed proposals

```
Raw Input → P0 Capture → P1 Proposal → Approval → Substrate Creation
```

**Proposal Structure** (Unapplied Changeset):
```typescript
interface Proposal {
  ops: Operation[]  // The substrate changes to apply
  status: 'PROPOSED' | 'APPROVED' | 'EXECUTED'
  origin: 'agent' | 'human'
  provenance: uuid[]  // Source raw_dump IDs
}
```

**Operation Schema** (P1 Evolution Agent Output) — V3.0:
```typescript
// Creation operations - novel concepts
{
  type: "CreateBlock",
  title: "Project Strategy",
  content: "New insight from dumps...",
  semantic_type: "insight" | "fact" | "entity" | "intent" | "metric",
  anchor_role: "strategy",  // V3.0: Emergent anchor (optional)
  anchor_status: "proposed",
  anchor_confidence: 0.85,
  confidence: 0.8
}

// Evolution operations - refining existing substrate
{
  type: "ReviseBlock",
  block_id: "existing-uuid",
  title: "Updated Project Strategy",
  content: "Updated content with new information...",
  parent_block_id: "existing-uuid",  // V3.0: Versioning chain
  confidence: 0.85
}

{
  type: "MergeBlocks",  // V3.0: Unified merge
  from_ids: ["uuid1", "uuid2"],
  canonical_id: "uuid1",
  merged_content: "Combined understanding..."
}

{
  type: "UpdateBlock",
  block_id: "existing-uuid",
  title: "Refined Title",
  anchor_role: "updated-anchor",  // V3.0: Emergent anchors evolve
  confidence: 0.9
}
```

**V3.0 Changes**:
- No more `CreateContextItem` / `UpdateContextItem` / `MergeContextItems`
- All operations now target unified `blocks` table
- Emergent `anchor_role` replaces fixed categories
- Versioning via `parent_block_id` chains

**Approval Criteria**:
- Agent-generated proposals: Auto-approve if confidence > 0.7
- Human-generated proposals: Manual review required
- Operations executed atomically on approval

### 6. Pure Supabase Async Intelligence Model
- Raw dumps automatically trigger agent queue processing via database triggers
- Pure Supabase architecture: no DATABASE_URL dependency, single connection type
- Service role authentication for backend operations, anon role for user operations
- User experience is immediate, intelligence processing happens asynchronously
- Agent processing is mandatory for substrate creation per Sacred Principle #4
- Queue-based processing ensures YARNNN canon compliance at scale
- Frontend shows processing state but never synthesizes substrate

## 🎬 Operational Flow

### Basket Lifecycle
```
INIT → ACTIVE → ARCHIVED
```
- Empty INIT baskets > 48h are eligible for cleanup
- Baskets are workspace-level containers for cognitive work

### Block State Machine
```
PROPOSED → ACCEPTED → LOCKED → CONSTANT
         ↘         ↗
          REJECTED → SUPERSEDED
```

### Substrate Evolution Flow
- **Multi-Input Capture**: Text, files, images become collection of raw_dumps
- **Context-Aware Processing**: P1 Agent analyzes new dumps + existing substrate
- **Evolution Decisions**: Agent determines Create/Update/Merge operations needed
- **Governance Proposal**: Single proposal with mixed operation types based on basket maturity
- **Auto-Approval**: High confidence evolution proposals execute immediately
- **Substrate Evolution**: Operations evolve the basket's knowledge representation

**Operation Mix Over Basket Lifecycle**:
- **Early Stage (1-10 dumps)**: 90% Create, 10% Update - exploring new conceptual space
- **Growing Stage (10-50 dumps)**: 60% Create, 40% Update - filling out knowledge gaps  
- **Mature Stage (50+ dumps)**: 30% Create, 70% Update - refining existing knowledge

**Deletion & Retention**: User operations are Archive/Redact (governance‑first) with cascade preview and audit tombstones; physical deletion is policy‑driven via scheduled vacuum (developer‑level). See `docs/YARNNN_DELETION_RETENTION_CANON_v1.0.md`.

### Document Composition (Artifact Layer)
- Documents = independent artifacts composed from substrate ingredients + authored prose
- Git-inspired versioning: Documents create snapshots for stable references
- Substrate ingredients remain immutable; documents evolve independently
- P4 agent creates initial composition, users freely edit afterward

## 📝 Sacred Principle #5: Substrate Management Replaces Document Editing (v3.0)

### Philosophy

**Documents are read-only composed views of substrate state. Users do not edit documents—they manage substrate and direct composition.**

This is YARNNN's revolutionary stance: fundamentally different from Notion, Google Docs, and traditional note-taking apps.

### What Users Do Instead of Editing

**1. Curate Substrate** (replaces: "editing content")
- Approve/reject/merge blocks via governance
- Add/remove substrate references from documents
- Update blocks through proposals (V3.0: unified substrate)

**2. Direct Composition** (replaces: "formatting and structure")
- Define composition instructions ("make section 2 more technical")
- Select which substrate to include/exclude
- Request regeneration with updated parameters

**3. Govern Substrate Mutations** (replaces: "revising drafts")
- Review proposals for block updates
- Approve substrate merges and refinements
- Validate agent-extracted substrate

**4. Manage Versions** (replaces: "save and track changes")
- Freeze versions as final snapshots
- Compare versions to see substrate evolution
- Accept/reject regenerated compositions

### The Fundamental Shift

**Traditional (Notion/Docs):**
```
User types prose → saves → document updated
```

**YARNNN (Revolutionary):**
```
User curates substrate → requests composition → document regenerated
```

### Expected Time Allocation

- **80%** substrate curation (governance, building-blocks management)
- **20%** composition refinement (document regeneration, instruction tuning)

**Substrate management IS the primary user activity.** Documents are downstream artifacts of well-managed substrate.

### Three-Layer Mental Model

**Layer 1: RAW_DUMPS** (Immutable Capture)
- Purpose: Preserve original input exactly as received
- User interaction: View original (read-only reference)
- Location: `/baskets/[id]/timeline` (Uploads tab)

**Layer 2: SUBSTRATE** (Governed Knowledge)
- Purpose: Structured, validated knowledge atoms
- User interaction: Curate, approve, merge (governance)
- Location: `/baskets/[id]/building-blocks`

**Layer 3: DOCUMENTS** (Composed Artifacts)
- Purpose: Narrative compositions from substrate
- User interaction: Manage substrate, refine composition
- Location: `/baskets/[id]/documents/[doc-id]`

### Upload Wizard Transformation

When users upload existing documents (e.g., `product-spec.docx`):

1. **P0:** Create raw_dump with original text (preserved exactly)
2. **P1:** Extract substrate → Create proposals
3. **User:** Review and approve substrate (governance)
4. **P4:** Compose NEW document from extracted substrate
5. **Show:** Side-by-side diff (original vs YARNNN version)
6. **User:** Accept transformation or cancel upload

**Key Insight:** We don't "migrate" documents. We **transform** them into substrate-backed knowledge.

**Trust Model:** Transparency through side-by-side comparison builds confidence in substrate extraction quality.

## 💡 Key Insights from Canon

1. **Substrate Equality** - The three substrate types (dumps, blocks, events) are peers — V3.0 unified
2. **Substrate vs Artifacts** - Clear separation between memory (substrate) and expressions (artifacts)
3. **Read-Only Documents** - Documents are composed views, never directly edited (v3.0)
4. **Pipeline Discipline** - P0-P1 create substrate via governance, P3-P4 create artifacts
5. **Memory Permanence** - Substrate is immutable; documents regenerate from substrate changes
6. **Document Versioning** - Git-inspired immutable snapshots for stable artifact references
7. **Workspace Isolation** - Complete data isolation between workspaces
8. **Agent Necessity** - Substrate cannot exist without agent processing
9. **Async Intelligence** - User feedback is instant, intelligence processing happens asynchronously
10. **Governance-Mediated Creation** - All substrate mutations flow through proposals, enabling review and atomic execution
11. **Supervisory Work Model** - Users direct and govern; agents research and compose (v3.0)
12. **Semantic Intelligence** - Agents reason semantically, not just keyword matching (v3.1)
13. **Causal Graph** - Relationships capture "why" and "what depends on", not just "relates to" (v3.1)
14. **Structure + Semantics** - Semantic layer augments structure, doesn't replace it (v3.1)

## 🚀 Implementation Guidelines

1. **Frontend Must**:
   - Mirror durable server state only
   - Never synthesize data client-side
   - Respect substrate equality in UI

2. **Backend Must**:
   - Enforce pipeline write boundaries
   - Emit timeline events for every mutation
   - Maintain workspace isolation via RLS

3. **Agents Must**:
   - **P1 Evolution Agents (V3.1 UPGRADED)**:
     - Read new raw_dumps AND existing substrate in basket
     - V3.1: Use semantic search to detect duplicates (similarity > 0.85 = MERGE, 0.70-0.85 = UPDATE, <0.70 = CREATE)
     - Make intelligent Create/Update/Merge decisions based on semantic overlap, not just keyword matching
     - Use proper operation schema (flat structure, not nested objects)
     - Process actual dump content, never hardcoded templates
     - Achieve confidence > 0.7 for auto-approval eligibility
     - Handle basket lifecycle: heavy Create (early) → heavy Update (mature)

   - **P3 Insight Agents (V3.1 ENHANCED)**:
     - Use semantic search to retrieve relevant context (not full basket scan)
     - Generate insights with evidence from substrate

   - **P4 Composition Agents (V3.1 ENHANCED)**:
     - Use semantic search for theme-based retrieval (not just anchor_role filtering)
     - Create coherent narrative from substrate + P3 insights
     - Integrate workspace-level context via cross-basket semantic search

---

## 🧠 V3.1 Semantic Layer Architecture

**Purpose:** Enable agents to reason semantically about substrate, not just keyword matching

**See**: [SEMANTIC_LAYER_INTEGRATION_DESIGN.md](./SEMANTIC_LAYER_INTEGRATION_DESIGN.md) for complete technical architecture

### Core Components

#### 1. Vector Embeddings (Semantic Search)

**What Gets Embedded:**
- `blocks` table ONLY (ACCEPTED+ state)
- NOT raw_dumps (transient input)
- NOT documents (derived artifacts)

**When Embedded:**
- After governance approval (state → ACCEPTED/LOCKED/CONSTANT)
- Async generation via OpenAI text-embedding-3-small (1536 dimensions)
- Stored in `blocks.embedding` column

**Purpose:**
- Semantic duplicate detection (P1)
- Theme-based retrieval (P3, P4)
- Cross-basket pattern discovery (P1, P3)

**Key Principle:** Embed substrate (refined knowledge), not raw input

---

#### 2. Relationship Graph (Causal Semantics)

**Relationship Types (4 Core):**

| Type | From Types | To Types | Description |
|------|-----------|----------|-------------|
| `addresses` | action, insight, objective, solution | problem, constraint, issue | Solution addresses problem |
| `supports` | fact, finding, metric, evidence | objective, insight, hypothesis | Evidence supports claim |
| `contradicts` | fact, finding, insight | assumption, fact, insight | Conflicts with statement |
| `depends_on` | action, objective, task | action, objective, constraint | Prerequisite dependency |

**Inference Process:**
1. P2 agent analyzes new blocks after P1 substrate creation
2. Semantic search finds relationship candidates (similarity > 0.70)
3. LLM verification (gpt-4o-mini) confirms causal relationship
4. Propose via governance (auto-accept if confidence > 0.90)

**Purpose:**
- Causal reasoning (P3 insights)
- Narrative coherence (P4 documents)
- Decision tracing ("why did we decide X?")

**Key Principle:** Relationships capture causality, not just association

---

#### 3. Shared Primitives (API Layer)

All agents use standardized semantic layer API:

```python
# Semantic search within basket
semantic_search(basket_id, query_text, filters, limit)
→ List[BlockWithSimilarity]

# Cross-basket search (elevated scope)
semantic_search_cross_basket(workspace_id, query_text, scopes, limit)
→ List[BlockWithSimilarity]

# Infer relationships for block
infer_relationships(block_id, basket_id)
→ List[RelationshipProposal]

# Traverse relationship graph
traverse_relationships(start_block_id, relationship_type, direction, max_depth)
→ List[BlockWithDepth]

# Get rich semantic context
get_semantic_context(focal_block_id, context_window)
→ {similar_blocks, relationships}
```

**Location:** `api/src/services/semantic_primitives.py`

---

### Integration Points by Pillar

#### P0: Capture - NO CHANGES
- Raw dumps not embedded (transient input, not persistent memory)
- Pure capture remains pure

#### P1: Substrate Evolution - UPGRADED
**Before:** Extract facts → propose CREATE operations
**After:** Extract facts → semantic search for duplicates → propose CREATE/MERGE/UPDATE

**Thresholds:**
- similarity > 0.85 → MERGE (high confidence duplicate)
- similarity 0.70-0.85 → UPDATE/ENRICH (related content)
- similarity < 0.70 → CREATE (novel content)

**Impact:** 30-40% reduction in duplicate blocks

#### P3: Insights - ENHANCED
**Before:** Analyze all blocks in basket
**After:** Semantic retrieval → analyze patterns → generate insights

**Features:**
- Context retrieval without keyword matching
- Pattern recognition across substrate types
- Evidence-based insight generation

**Impact:** Richer insights with semantic pattern recognition

#### P4: Documents - ENHANCED
**Before:** Retrieve blocks by anchor_role
**After:** Semantic theme search → compose coherent narrative

**Features:**
- Theme-based retrieval (not just anchor tags)
- Narrative flow from substrate patterns
- Workspace context integration (elevated scope)

**Impact:** More coherent documents with semantic structure

---

### Design Principles (Reaffirmed)

1. **Embed Substrate, Not Raw Input**
   - Quality over quantity
   - ACCEPTED+ blocks only (vetted knowledge)

2. **Agent-First, Not User-First**
   - Primary value: Agent intelligence
   - Secondary value: User features (find similar, graph viz)

3. **Structure + Semantics, Not RAG**
   - Governance, versioning, anchors remain primary
   - Semantic layer augments, doesn't replace

4. **Deliberate Integration**
   - Each pillar explicitly defines semantic usage
   - Shared primitives with clear contracts
   - Integration points documented

---

### Success Metrics

**P1 (Substrate Evolution):**
- Duplicate block rate: <5% (down from ~15%)
- Merge proposal rate: >25% (up from ~5%)

**P3 (Insights):**
- Context relevance: >85% (% retrieved blocks relevant)
- Pattern recognition: Insights identify emergent themes

**P4 (Documents):**
- Narrative coherence: Sections follow semantic structure
- Theme relevance: >90% blocks match document outline

**Neural Map (Visualization):**
- Zero infrastructure cost (no LLM/vector search)
- Instant render (<1s vs 150s+ for P2 graph)
- Intuitive brain-based metaphor (neurons, synapses, brain regions)

---

### Cost Model

**Embedding Generation:**
- Model: text-embedding-3-small ($0.02 per 1M tokens)
- Avg block size: 200 tokens
- 1000 blocks = 200k tokens = **$0.004**

**Relationship Verification:**
- Model: gpt-4o-mini ($0.15 per 1M input tokens)
- Verification prompt: ~300 tokens
- 1000 relationships = 300k tokens = **$0.045**

**Total: ~$0.05 per 1000 blocks (negligible at scale)**

---

## Canonical Files

- **SCHEMA_SNAPSHOT.sql**  
  Frozen Postgres/Supabase schema — structural source of truth.  

- **YARNNN_AUTH_WORKFLOW.md**  
  Authentication and workspace membership flow, JWT verification, and access rules.  

- **YARNNN_FRONTEND_AUTH.md**  
  Frontend session handling and integration with Supabase authentication.  

- **YARNNN_INGESTION_FLOW.md**  
  Contracts and flow for atomic basket + dump ingestion.  

- **YARNNN_INTERFACE_SPEC_v0.1.0.md**
  API and DTO contracts for baskets, dumps, and ingestion flows.  

- **YARNNN_MEMORY_MODEL.md**  
  Canonical substrate contracts, mutability guarantees, and composition rules.  

- **YARNNN_MONOREPO_ARCHITECTURE.md**  
  Deployment and substrate-level architecture of the monorepo.  

- **YARNNN_RELATIONAL_MODEL.md**
  Semantic roles and flows across substrates (raw_dump, block, document, event). V3.0: unified blocks.  

- **YARNNN_CREATE_CANON.md**  
  The one sacred write path for capture.

- **YARNNN_REFLECTION_READMODEL.md**  
  How authoritative reflections are computed (text + graph) and reconciled with optimistic UI.

---

## Governance Evolution (v2.0 Preview)

**See**: `YARNNN_GOVERNANCE_CANON.md` for substrate governance model evolution

**Key Evolution**: Governance as first-class workflow
- All substrate mutations flow through governed proposals
- Agent validation mandatory for all proposals (agent + human origin)
- V3.0: All blocks have governance states: `PROPOSED → ACCEPTED → LOCKED → CONSTANT`
- Unified governance preserves sacred capture path while enabling manual substrate curation

**V3.0 Changes**: Unified blocks table with emergent anchors replaces context_items

---

---

## ⚙️ Universal Work Orchestration (v2.2)

**The Governance Revolution**: ALL substrate mutations flow through a single orchestrated pipeline.

### Core Concept: Work-Type Based Governance

```typescript
interface WorkRequest {
  work_type: 'P0_CAPTURE' | 'P1_SUBSTRATE' | 'P2_GRAPH' | 'P3_REFLECTION' | 
            'P4_COMPOSE' | 'MANUAL_EDIT' | 'PROPOSAL_REVIEW' | 'TIMELINE_RESTORE'
  work_payload: {
    operations: Operation[]     // What substrate changes to make
    basket_id: string          // Workspace context
    confidence_score?: number  // AI confidence level
    user_override?: 'require_review' | 'allow_auto'
    provenance?: string[]      // Source raw_dumps or context
  }
}
```

### Governance Policy Framework

Each workspace has governance policies that determine execution mode:

```typescript
interface WorkTypePolicy {
  mode: 'auto' | 'proposal' | 'confidence'
  confidence_threshold: number  // Used in confidence mode
  require_validation: boolean   // Manual validator required
}
```

**Mode Behaviors:**
- `auto`: Execute immediately (like git auto-merge)
- `proposal`: Always create proposal for review (like git pull request)
- `confidence`: Route based on AI confidence score within governance framework

### Universal Routing Algorithm

```
1. Work Request → Universal Work API (/api/work)
2. Fetch workspace governance policy for work_type
3. Apply routing logic:
   - user_override takes precedence
   - otherwise use policy.mode
   - confidence mode uses confidence_threshold
4. Route to execution path:
   - auto_execute → immediate substrate modification
   - create_proposal → create review proposal
5. Emit timeline events for visibility
6. Return work_id and routing decision
```

### Sacred Principles Enforcement

1. **Substrate-Only Governance**: No direct substrate endpoints exist - substrate mutations flow through `/api/work`
2. **Artifact Independence**: Documents and reflections use direct REST endpoints (`/api/documents`, `/api/reflections`)
3. **User Control**: Governance policies are user-configurable per workspace for substrate operations only
4. **Confidence Integration**: AI confidence informs substrate routing but doesn't override governance

### Canon-Pure Patterns (v2.3)

**SUBSTRATE OPERATIONS (Governed):**
- Substrate mutations: `/api/work` → governance → substrate tables
- Work types: P0_CAPTURE, P1_SUBSTRATE, P2_GRAPH, P3_REFLECTION, MANUAL_EDIT

**ARTIFACT OPERATIONS (Independent):**
- Document CRUD: `/api/documents` → direct → documents table
- Document composition: P4 agents → direct → document updates
- Reflection generation: `/api/reflections` → direct → reflections table
- Analytics: Direct queries to composition_stats, substrate_references

**ELIMINATED Canon Violations:**
- Document creation through governance ❌ → Direct REST endpoints ✅
- Reflection proposals ❌ → Direct computation ✅  
- Universal governance for artifacts ❌ → Substrate-only governance ✅

---

## Version Lock

- Canon version: **v3.1**
- Frozen as of: **2025-10-13**
- Update policy: Do not edit in place. Amendments require a new canon version.

### v3.1.0 Changes (P3/P4 Taxonomy & Immutability Hardening)
- **P3 Insights Taxonomy Formalized**: insight_canon, doc_insight, timeboxed_insight, review_insight, cross-basket insights
- **P4 Documents Taxonomy Formalized**: document_canon (mandatory), starter_prompt (many), artifact_other (extensible)
- **Context-Driven Freshness**: Staleness computed from substrate_hash + graph_signature changes, NOT time-based
- **Lineage Tracking**: All P3/P4 artifacts link to previous versions via previous_id
- **Provenance Recording**: All artifacts record derived_from (substrate sources)
- **Cardinality Clarity**: ONE insight_canon per basket/workspace, MANY doc_insights per basket, MANY starter_prompts
- **Review Insights Scoped**: Computed ephemeral, cached in proposals table (not in reflections_artifact)
- **Cross-Basket Synthesis**: Workspace-level insights schema included (policy-gated for future enablement)
- **Governance Boundary Hardened**: P3/P4 regeneration is DIRECT (not governed), policy-controlled only
- **Basket Modes Eliminated**: Removed legacy preset/template patterns in favor of emergent P3/P4 intelligence

### v3.0.0 Changes (Revolutionary - Substrate-First Documents)
- **Sacred Principle #5 Added**: Substrate Management Replaces Document Editing
- **Document Model Revolution**: Documents are read-only composed views, never directly edited
- **Upload Wizard Transformation**: Uploaded documents transformed via substrate extraction, not preserved as-is
- **Three-Layer Mental Model**: raw_dumps (capture) → substrate (knowledge) → documents (compositions)
- **Schema Evolution**: Documents table becomes composition definitions; content lives in immutable versions
- **Supervisory Work Model**: Users curate substrate 80%, refine compositions 20%
- **Fundamental Differentiation**: YARNNN is not Notion—it's substrate-first intelligence platform

### v2.3.0 Changes (Clarification & Canon Purity)
- **Substrate/Artifact Separation**: Clarified governance applies ONLY to substrate layer
- **Artifact Independence**: Documents and reflections operate via direct REST, not governance
- **Canon-Pure Boundaries**: Eliminated universal governance violation of artifact autonomy
- **P4 Reclassification**: Document composition moved from governance to direct artifact operations
- **Documentation Hardening**: Crystal clear boundaries prevent future canon violations

### v2.2.0 Changes (Revolutionary)
- **Universal Work Orchestration**: ALL substrate mutations flow through single governance pipeline
- **Work-Type Based Governance**: Replaced entry-point routing with universal work type policies
- **Eliminated Dual Approaches**: Deleted all legacy direct substrate endpoints
- **Enhanced User Control**: Workspace-level governance configuration with confidence sub-options
- **Canon Purity**: Complete elimination of governance bypass patterns

### v2.1.0 Changes (Extension)
- **Universal Work Orchestration**: Extended canonical_queue to handle all async operations
- **Real-time Status Visibility**: Canon-compliant status derivation across all workflows  
- **Cascade Framework Integration**: Unified P0→P1→P2→P3 orchestration with status tracking
- **Schema Enhancement**: Extended canonical_queue with cascade metadata and universal work support
- **Sacred Principle Preservation**: All changes maintain strict canon compliance

### v3.0.0 Changes (Breaking) — 2025-01-15
- **Unified Substrate Architecture**: `context_items` merged into `blocks` table
- **Three Pure Substrates**: raw_dumps, blocks (unified), timeline_events
- **Emergent Anchors**: Free-text `anchor_role` replaces fixed categorization
- **Universal Versioning**: All blocks version identically via `parent_block_id` chains
- **Scope Elevation**: Cross-basket memory via WORKSPACE/ORG/GLOBAL scopes
- **Semantic Types**: Knowledge (fact, metric), Meaning (intent, objective), Structural (entity)
- **See**: [YARNNN_SUBSTRATE_CANON_V3.md](./YARNNN_SUBSTRATE_CANON_V3.md) for complete details

### v2.0.0 Changes (Breaking)
- **Substrate/Artifact Separation**: Clear distinction between memory (substrate) and expressions (artifacts)
- **Two Artifact Types**: documents (versioned), reflections (computed)
- **Document Versioning**: Git-inspired versioning for stable artifact references
- **Legacy Table Removal**: Eliminated block_links, document_context_items, basket_events, revisions
- **No Artifact Recursion**: Reflections can target substrates OR document versions, never other artifacts

### v1.4.0 Changes
- Added Pure Supabase Async Intelligence Model as 5th Architectural Pillar
- Updated to reflect queue-based agent processing architecture 
- Clarified service role vs anon role authentication patterns
- Reinforced Agent Intelligence Mandatory principle (#4)
- **Memory Page Evolution**: Transformed primary operating surface into comprehensive memory interface
- **Document Library Integration**: Added document upload, library management, and breakdown proposal workflow
- **UX Simplification**: Dual-mode interface (Quick Capture ↔ Document Library) for clearer user journey  

## 📊 Canon v1.3.1 Compliance Audit Results

**Audit Date**: August 27, 2025  
**Auditor**: Claude Code  
**Overall Compliance Score: 78% (7/9 categories compliant or partial)**

The codebase shows **strong alignment** with Canon v1.3.1 principles, particularly in the core architectural areas. Recent work has successfully implemented substrate equality and generic composition patterns. Key violations involve legacy APIs that are deprecated but still present.

### Canon Compliance Achievements ✅

1. **Substrate Equality Compliance**: Generic `substrate_references.ts` contract and API implemented
2. **Pipeline Discipline**: Clear P0-P4 pipeline separation maintained  
3. **Sacred Write Path**: Primary `/api/dumps/new` path and batch ingestion working correctly
4. **Memory-First Architecture**: Reflections properly derived from substrate
5. **Workspace-Scoped Security**: RLS policies and workspace isolation implemented
6. **Event-Driven Consistency**: Timeline events properly emitted for mutations
7. **Database Schema Alignment**: Schema perfectly aligned with canon requirements

### Areas for Legacy Cleanup ⚠️

- Deprecated API routes still exist but marked DEPRECATED
- Legacy contract types (BlockLinkDTO) present but deprecated
- Frontend UI component compliance requires verification

**Key Achievement**: The core Canon v1.3.1 implementation work was successful. Major principles are implemented correctly, with only legacy cleanup remaining.

---
