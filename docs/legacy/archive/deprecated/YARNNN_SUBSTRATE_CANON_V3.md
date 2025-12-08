# YARNNN Substrate Canon v3.1

**The Definitive Reference for Substrate Architecture**

**Status**: Active (2025-01-15, Updated 2025-10-31 for v4.0 integration)
**Version**: v3.1 (Semantic Layer Integration)
**Supersedes**: YARNNN_SUBSTRATE_CANON.md v2.x
**Authority**: This is the single source of truth for substrate design

---

## Version History

- **v3.0** (2025-01-15): Unified substrate (context_items → blocks), emergent anchors, universal versioning
- **v3.1** (2025-01-15): Semantic intelligence layer (vector embeddings + causal relationships)
- **v4.0 Integration** (2025-10-31): Work orchestration layer links to substrate via governance

---

## 🆕 v4.0 Integration Notes

**YARNNN v4.0** introduces unified work orchestration + governance spanning both agent work quality AND substrate integrity. This document (v3.1) remains the canonical reference for **substrate architecture** (Layer 1), but now integrates with:

- **Layer 2 (Work Orchestration)**: Agent work sessions create artifacts that become substrate blocks after approval
- **Layer 3 (Unified Governance)**: Single user review handles both work quality and substrate mutation
- **Provenance**: Every block created via work orchestration includes complete lineage (work_session_id, work_artifact_id, agent_reasoning)

**Key Changes for v4.0**:
- Blocks can be created via **two paths**: Direct (human-created) or Work Orchestration (agent-created with approval)
- Agent-created blocks skip PROPOSED state (work already reviewed) → Go directly to ACCEPTED
- Block metadata includes provenance fields: `work_session_id`, `work_artifact_id`, `agent_confidence`, `approved_by_user`

**See**:
- [Work Session Lifecycle](features/work-management/WORK_SESSION_LIFECYCLE.md) - Agent work states
- [Artifact Types](features/work-management/ARTIFACT_TYPES_AND_HANDLING.md) - How artifacts → blocks
- [Audit Trails](features/governance/AUDIT_TRAILS.md) - Complete provenance tracking

---

---

## Philosophy: Emergent Memory Architecture with Semantic Intelligence

Yarnnn v3.1 implements an **emergent memory system** aligned with industry best practices:
- ChatGPT's memory model (no predefined categories)
- LangGraph's session/long-term split (scope levels)
- Mem0's temporal versioning (parent_block_id chains)
- Vector DB + knowledge graph hybrid (semantic + structural) ← **V3.1: IMPLEMENTED**

**Core insight**: Memory organization should emerge from usage, not be prescribed upfront.

**V3.1 addition**: Agents reason semantically, not just structurally. Semantic layer (embeddings + relationships) augments structural primitives (anchors, versioning, lifecycle).

---

## The Emergent Trilogy

### 1. **Versioning** (Emergent Evolution)
All blocks version identically. No special cases.

**Rule**: Version if identity persists
```sql
-- Same metric, updated value
v1: "Login completion: 60%"
v2: "Login completion: 75%" (parent_block_id → v1)

-- Same vision, clarified
v1: "Become market leader"
v2: "Become market leader in SMB CRM" (parent_block_id → v1)
```

**Rule**: New block if identity changes
```sql
-- Different goals
"Series A intent" ≠ "Series B intent" (separate blocks)

-- Different problems
"Login issues" ≠ "Checkout issues" (separate blocks)
```

### 2. **Maturation** (Emergent Lifecycle)
Blocks naturally evolve through states and scopes.

**State progression**:
```
PROPOSED → ACCEPTED → LOCKED → CONSTANT
                    ↘ SUPERSEDED (when new version created)
         ↘ REJECTED
```

**Scope elevation**:
```
NULL (basket-local)
  ↓ Important to team
WORKSPACE (cross-basket)
  ↓ Important to organization
ORG (organization-wide)
  ↓ Universal truth
GLOBAL (system-level constant)
```

**No enforced maturity stages.** Blocks accumulate, refine, and stabilize organically.

### 3. **Anchors** (Emergent Categorization)
No predefined anchor vocabulary. Anchors emerge from:
- **Agent proposals**: P1 extraction infers anchor from semantics
- **User tagging**: Building Blocks UI allows free-text anchor input
- **Autocomplete**: Shows basket's existing anchor vocabulary
- **Governance**: Accepts/rejects/modifies proposed anchors

**Example vocabularies** (emerged organically):
- Product basket: `problem`, `solution`, `metric`, `feature`
- Research basket: `hypothesis`, `evidence`, `conclusion`, `limitation`
- Legal basket: `obligation`, `risk`, `precedent`, `compliance`

---

## Architecture: Unified Substrate Table

### Single Source of Truth

**Before v3.0** (dual model):
```sql
blocks          -- Knowledge (versioned)
context_items   -- Metadata (not versioned)
→ Arbitrary boundary, dual CRUD paths
```

**After v3.0** (unified):
```sql
blocks          -- ALL substrate (universally versioned)
→ Single CRUD path, emergent organization
```

### Blocks Table Schema

```sql
CREATE TABLE blocks (
  -- Identity
  id uuid PRIMARY KEY,
  basket_id uuid NOT NULL,
  workspace_id uuid NOT NULL,

  -- Semantic differentiation
  semantic_type text NOT NULL,

  -- Content
  title text NOT NULL CHECK (title != ''),
  content text NOT NULL CHECK (content != ''),

  -- Emergent anchoring (optional)
  anchor_role text,  -- Free text, no constraints
  anchor_status text CHECK (anchor_status IN ('proposed', 'accepted', 'rejected')),
  anchor_confidence real CHECK (anchor_confidence BETWEEN 0 AND 1),

  -- Universal lifecycle
  state block_state CHECK (state IN (
    'PROPOSED', 'ACCEPTED', 'LOCKED', 'CONSTANT', 'SUPERSEDED', 'REJECTED'
  )),

  -- Scope elevation (optional, for cross-basket memory)
  scope scope_level CHECK (scope IN ('WORKSPACE', 'ORG', 'GLOBAL')),

  -- Universal versioning
  parent_block_id uuid REFERENCES blocks(id),
  version integer DEFAULT 1 NOT NULL,

  -- Governance
  proposal_id uuid REFERENCES proposals(id),
  raw_dump_id uuid REFERENCES raw_dumps(id),

  -- Quality
  confidence_score double precision DEFAULT 0.5,
  last_validated_at timestamp with time zone DEFAULT now(),
  metadata jsonb DEFAULT '{}'::jsonb,

  created_at timestamp with time zone DEFAULT now() NOT NULL,
  updated_at timestamp with time zone DEFAULT now() NOT NULL,

  -- Constraints
  CONSTRAINT constant_requires_scope CHECK (
    (state = 'CONSTANT' AND scope IS NOT NULL) OR
    (state != 'CONSTANT')
  )
);
```

---

## Semantic Types

### Knowledge Types (What We Know)

Observable, verifiable, measurable substrate:

- **`fact`** — Verifiable statement ("Revenue was $2.7M in Q3")
- **`metric`** — Measurable quantity ("Login completion: 75%")
- **`event`** — Point-in-time occurrence ("Launched beta on Oct 15")
- **`insight`** — Derived understanding ("Users prefer mobile over desktop")
- **`action`** — Recommendation or completed action ("Prioritize mobile UX")
- **`finding`** — Discovery or observation ("40% of users abandon at login")
- **`quote`** — Direct citation ("CEO said: 'Move fast'")
- **`summary`** — Condensed overview ("Q3 performance exceeded targets")

### Meaning Types (Why/How We Know)

Interpretive, intentional, framing substrate:

- **`intent`** — Purpose or goal ("Prepare for Series A fundraising")
- **`objective`** — Measurable target ("Raise $5M by Q1 2025")
- **`rationale`** — Reasoning behind decision ("Chose React for faster iteration")
- **`principle`** — Guiding rule or belief ("Users first, always")
- **`assumption`** — Presumed truth ("Market will grow 20% annually")
- **`context`** — Framing information ("Operating in regulated healthcare market")
- **`constraint`** — Boundary or limitation ("Budget limited to $200K through Q1")

### Structural Types (Organization)

Organizational, relational substrate:

- **`entity`** — Person, company, product reference ("Google (competitor)")
- **`classification`** — Categorical tag ("Content Type: Financial Report")
- **`reference`** — External link or citation ("Based on McKinsey study")

---

## Anchor Roles (Emergent, Not Fixed)

**v3.0 change**: Anchors are **free text**, not enum-constrained.

**What anchors represent**: Strategic or semantic significance of a block.

**Common anchor roles** (emerged from usage, not prescribed):

| Anchor Role | Meaning | Example Block |
|-------------|---------|---------------|
| `problem` | Issues to solve | "Users struggle with OAuth flow" |
| `vision` | Long-term ambition | "Become market leader in SMB CRM" |
| `customer` | Who we serve | "Enterprise clients in healthcare" |
| `solution` | How we address problems | "Implement passwordless login" |
| `feature` | Product capabilities | "Real-time collaboration editing" |
| `constraint` | Boundary conditions | "Must comply with GDPR" |
| `metric` | Measurable goals | "Target: 100K MAU by EOY" |
| `insight` | Key understanding | "Mobile users convert 2x desktop" |

**Basket-specific anchors emerge**:
- Research basket: `hypothesis`, `evidence`, `conclusion`
- Legal basket: `obligation`, `risk`, `precedent`
- Creative basket: `inspiration`, `theme`, `mood`

**Discovery query**:
```sql
SELECT * FROM get_basket_anchor_vocabulary(:basket_id);
-- Returns: anchor_role, usage_count, accepted_count, avg_confidence
```

---

## State Machine (Universal)

All blocks follow the same lifecycle:

```
┌─────────────┐
│  PROPOSED   │ ← Newly created (via proposal)
└──────┬──────┘
       │ Governance approval
       ↓
┌─────────────┐
│  ACCEPTED   │ ← Active, current understanding
└──┬────┬─────┘
   │    │
   │    └─────────────→ New version created
   │                    ┌──────────────┐
   │                    │  SUPERSEDED  │ ← Replaced by newer version
   │                    └──────────────┘
   │
   ↓ User marks as important milestone
┌─────────────┐
│   LOCKED    │ ← Frozen, no edits (e.g., active fundraise)
└──────┬──────┘
       │ Elevate to workspace scope
       ↓
┌─────────────┐
│  CONSTANT   │ ← Universal truth, cross-basket memory
└─────────────┘  (Must have scope: WORKSPACE/ORG/GLOBAL)

Alternative path:
PROPOSED → REJECTED (governance rejection)
```

**Examples**:

```javascript
// Fact evolution
{state: 'PROPOSED'} → {state: 'ACCEPTED'} → {state: 'SUPERSEDED'}
// New version replaces

// Intent maturation
{state: 'PROPOSED'} → {state: 'ACCEPTED'} → {state: 'LOCKED'} → {state: 'CONSTANT', scope: 'WORKSPACE'}
// Commitment → Active execution → Completed goal (org memory)
```

---

## Scope Levels (Cross-Basket Memory)

**Purpose**: Enable multi-session, cross-basket LLM memory.

| Scope | Visibility | Use Case | Example |
|-------|------------|----------|---------|
| `NULL` (default) | Basket-local | Session-specific knowledge | "Q3 metrics for this product" |
| `WORKSPACE` | All baskets in workspace | Team-wide context | "We're preparing for Series A" |
| `ORG` | All workspaces in org | Organization-wide principles | "Company values: transparency, speed" |
| `GLOBAL` | System-wide | Universal constants | "HTTP 200 means success" |

**Elevation pattern**:
```sql
-- Start local
INSERT INTO blocks (basket_id, scope, ...) VALUES (:id, NULL, ...);

-- Team realizes this is important across baskets
UPDATE blocks SET scope = 'WORKSPACE', state = 'CONSTANT' WHERE id = :block_id;

-- Later, becomes org principle
UPDATE blocks SET scope = 'ORG' WHERE id = :block_id;
```

**LLM memory queries**:
```sql
-- Short-term memory (session): Recent basket blocks
SELECT * FROM blocks
WHERE basket_id = :id
ORDER BY last_validated_at DESC
LIMIT 50;

-- Long-term memory (persistent): Workspace constants
SELECT * FROM get_workspace_constants(:workspace_id);
-- Returns blocks with scope IN ('WORKSPACE', 'ORG', 'GLOBAL')
```

---

## Versioning (Universal)

All blocks can be versioned. No special cases.

### Version Chain Structure

```sql
-- Original block
{
  id: 'block-1',
  parent_block_id: NULL,
  version: 1,
  content: 'Login completion: 60%',
  state: 'SUPERSEDED'
}

-- Revised block
{
  id: 'block-2',
  parent_block_id: 'block-1',
  version: 2,
  content: 'Login completion: 75%',
  state: 'ACCEPTED'
}

-- Further revision
{
  id: 'block-3',
  parent_block_id: 'block-2',
  version: 3,
  content: 'Login completion: 85% (target achieved)',
  state: 'ACCEPTED'
}
```

### Traversing Version History

```sql
SELECT * FROM get_block_version_history(:block_id);
-- Recursively walks parent_block_id chain
-- Returns all versions ordered by version DESC
```

### When to Version vs New Block

**Version** (same entity, updated understanding):
- Correcting facts: "Revenue: $2.5M" → "Revenue: $2.7M (revised)"
- Refining meaning: "Improve UX" → "Improve mobile UX specifically"
- Updating metrics: "Target: 100K users" → "Target: 150K users"

**New block** (different entity):
- Sequential goals: "Series A intent" vs "Series B intent"
- Different problems: "Login bugs" vs "Checkout bugs"
- Time-based: "Q3 objectives" vs "Q4 objectives"

---

## Governance Integration

All substrate mutations flow through proposals.

### Creating Blocks

```python
# P1 agent proposes substrate creation
proposal = {
  "proposal_kind": "Extraction",
  "ops": [{
    "op": "CreateBlock",
    "semantic_type": "fact",
    "title": "Q3 Revenue",
    "content": "Revenue reached $2.7M in Q3",
    "anchor_role": "metric",  # Agent-proposed
    "anchor_status": "proposed",
    "anchor_confidence": 0.9
  }]
}

# Governance approves → block created with state='ACCEPTED'
```

### Editing Blocks (Versioning)

```python
# User/agent proposes edit
proposal = {
  "proposal_kind": "Edit",
  "ops": [{
    "op": "EditBlock",
    "block_id": "existing-block-id",
    "changes": {
      "content": "Revenue reached $2.9M in Q3 (corrected)"
    }
  }]
}

# On approval:
# 1. Old block: state='SUPERSEDED'
# 2. New block: parent_block_id=old_id, version=old.version+1
```

### Tagging Anchors

```python
# User tags block with anchor
proposal = {
  "proposal_kind": "Edit",
  "ops": [{
    "op": "UpdateBlockAnchor",
    "block_id": "block-id",
    "anchor_role": "problem",  # User-specified
    "anchor_status": "proposed"
  }]
}

# Governance approves → anchor accepted
```

---

## P0 → P4 Pipeline Integration

### P0: Capture (Immutable Ingestion)

```
User input → raw_dumps table
- Sacred, immutable capture
- No substrate creation yet
```

### P1: Substrate Extraction

```python
# Agent extracts from raw_dump
def create_substrate(dump_id):
    # Extract all semantic types
    substrate = [
        {"semantic_type": "fact", "anchor_role": "metric", ...},      # Knowledge
        {"semantic_type": "intent", "anchor_role": "vision", ...},    # Meaning
        {"semantic_type": "entity", "anchor_role": None, ...}         # Structural
    ]

    # Single proposal with all blocks
    return create_proposal("Extraction", substrate)
```

**Key**: P1 creates **all semantic_types** in one unified flow.

### P2: Graph Fabric

```python
# Build relationships from unified substrate
def build_graph(basket_id):
    all_blocks = get_blocks(basket_id, state='ACCEPTED')

    for block in all_blocks:
        if block.semantic_type in KNOWLEDGE_TYPES:
            add_knowledge_node(block)
        elif block.semantic_type in MEANING_TYPES:
            add_meaning_node(block)
        elif block.semantic_type == 'entity':
            add_entity_node(block)

    # Discover relationships between nodes
    discover_relationships(all_blocks)
```

### P3: Insights (Reflection)

```python
# Reflect on unified substrate
def generate_insight_canon(basket_id):
    # Get all substrate
    substrate = get_blocks(basket_id, state='ACCEPTED')

    # Categorize for analysis
    knowledge = [b for b in substrate if b.semantic_type in KNOWLEDGE_TYPES]
    meaning = [b for b in substrate if b.semantic_type in MEANING_TYPES]
    anchored = [b for b in substrate if b.anchor_role]

    # Generate insight from combined substrate
    return llm_reflect(knowledge, meaning, anchored)
```

### P4: Documents (Composition)

```python
# Compose documents from unified substrate
def compose_document_canon(basket_id):
    # Query substrate with semantic filters
    facts = get_blocks(basket_id, semantic_type='fact')
    intents = get_blocks(basket_id, semantic_type='intent')
    anchored_priorities = get_blocks(basket_id, anchor_status='accepted')

    # Compose narrative
    return llm_compose(facts, intents, anchored_priorities)
```

---

## Query Patterns for LLM Memory

### Pattern 1: Short-Term Memory (Session Context)

```sql
-- Recent validated blocks in basket
SELECT * FROM blocks
WHERE basket_id = :basket_id
  AND state = 'ACCEPTED'
ORDER BY last_validated_at DESC
LIMIT 50;
```

### Pattern 2: Long-Term Memory (Persistent Context)

```sql
-- Workspace constants (cross-basket memory)
SELECT * FROM get_workspace_constants(:workspace_id);

-- Returns blocks with:
-- - state = 'CONSTANT'
-- - scope IN ('WORKSPACE', 'ORG', 'GLOBAL')
```

### Pattern 3: Meaning Context (Framing)

```sql
-- Basket's intent, objectives, principles
SELECT * FROM blocks
WHERE basket_id = :basket_id
  AND semantic_type IN ('intent', 'objective', 'principle', 'rationale')
  AND state = 'ACCEPTED'
ORDER BY anchor_confidence DESC NULLS LAST;
```

### Pattern 4: Anchored Priorities

```sql
-- High-confidence anchored blocks
SELECT * FROM blocks
WHERE basket_id = :basket_id
  AND anchor_status = 'accepted'
  AND state = 'ACCEPTED'
ORDER BY anchor_confidence DESC
LIMIT 20;
```

### Pattern 5: Version History

```sql
-- Evolution of understanding
SELECT * FROM get_block_version_history(:block_id);

-- Returns all versions of a block, ordered by version DESC
```

### Pattern 6: Categorized Substrate

```sql
-- Get substrate categorized by type
SELECT * FROM get_basket_substrate_categorized(:basket_id);

-- Returns:
-- category    | block_count | semantic_types
-- knowledge   | 45          | {"fact": 20, "insight": 15, ...}
-- meaning     | 12          | {"intent": 5, "objective": 7}
-- structural  | 8           | {"entity": 6, "classification": 2}
```

---

## Helper Functions (Database)

### get_basket_anchor_vocabulary

```sql
SELECT * FROM get_basket_anchor_vocabulary(:basket_id);
```

Returns emergent anchor vocabulary for basket:
- `anchor_role` — Free-text anchor name
- `usage_count` — How many blocks use this anchor
- `accepted_count` — How many are accepted
- `avg_confidence` — Average confidence score
- `semantic_types` — Which semantic_types use this anchor

**Use case**: Autocomplete for anchor tagging UI

---

### get_workspace_constants

```sql
SELECT * FROM get_workspace_constants(:workspace_id);
```

Returns cross-basket memory (workspace-scoped constants):
- Blocks with `state='CONSTANT'` and `scope IN ('WORKSPACE', 'ORG', 'GLOBAL')`
- Ordered by scope (GLOBAL → ORG → WORKSPACE) and creation date

**Use case**: LLM long-term memory initialization

---

### get_block_version_history

```sql
SELECT * FROM get_block_version_history(:block_id);
```

Recursively walks `parent_block_id` chain to return complete version history:
- All versions ordered by `version DESC`
- Includes state transitions

**Use case**: Show evolution of understanding in UI

---

### get_basket_substrate_categorized

```sql
SELECT * FROM get_basket_substrate_categorized(:basket_id);
```

Groups substrate by category:
- `knowledge` — semantic_types: fact, insight, action, metric, etc.
- `meaning` — semantic_types: intent, objective, rationale, etc.
- `structural` — semantic_types: entity, classification, reference

Returns count and breakdown per category.

**Use case**: Dashboard analytics, substrate health metrics

---

## Migration from v2.x

**Breaking change**: `context_items` table dropped entirely.

**For pre-launch systems**: No migration needed, schema purge acceptable.

**For production systems** (future reference):
1. Map `context_items.type` → `blocks.semantic_type`
2. Set `parent_block_id = NULL` (no version history for migrated items)
3. Set `version = 1`
4. Map `context_item_state` → `block_state`
5. Update `substrate_relationships` (context_item → block)

---

## Best Practices

### 1. Semantic Type Selection

**Use knowledge types** for:
- Observable facts: "User clicked login button"
- Measurements: "Page load time: 2.3s"
- Events: "Deployed v2.0 on Oct 15"

**Use meaning types** for:
- Purposes: "This basket tracks Series A prep"
- Goals: "Achieve 100K MAU by EOY"
- Reasoning: "Chose PostgreSQL for ACID compliance"

**Use structural types** for:
- References: "Google (competitor in search)"
- Categories: "Content Type: Technical Documentation"

### 2. Anchor Usage

**Do**:
- Let agents propose anchors during extraction
- Show autocomplete from basket's vocabulary
- Accept ambiguity — anchors emerge organically

**Don't**:
- Force every block to have an anchor
- Prescribe anchor vocabulary upfront
- Over-anchor (only mark strategically important blocks)

### 3. Versioning

**Version when**:
- Correcting errors ("Revenue: $2.5M" → "$2.7M")
- Refining understanding ("Improve UX" → "Improve mobile UX")
- Updating metrics (same metric, new value)

**New block when**:
- Different entity (Series A ≠ Series B)
- Different problem (Login ≠ Checkout)
- Time-based split (Q3 ≠ Q4)

### 4. Scope Elevation

**Elevate to WORKSPACE when**:
- Block is relevant across multiple baskets
- Team needs shared context
- Becoming org-level knowledge

**Mark as CONSTANT when**:
- Understanding is finalized
- Represents completed milestone
- Serves as historical reference

### 5. State Transitions

**PROPOSED → ACCEPTED**: Routine governance approval

**ACCEPTED → LOCKED**: User marks block as "don't change" (e.g., active fundraise, regulatory submission)

**LOCKED → CONSTANT**: Completed milestone elevated to org memory

**ACCEPTED → SUPERSEDED**: New version created

---

## Future Enhancements (Enabled by v3.0)

### Vector Embeddings

```sql
ALTER TABLE blocks ADD COLUMN embedding vector(1536);
```

Enables semantic search:
```sql
SELECT * FROM blocks
WHERE basket_id = :id
ORDER BY embedding <=> :query_embedding
LIMIT 10;
```

### Multi-Platform Memory

Same substrate accessible from:
- Web UI
- Mobile app
- Slack bot
- API clients
- MCP servers

All platforms query unified `blocks` table with different filters.

### Agent Memory Profiles

Different agents query different semantic_types:
```python
# Sales agent
sales_memory = get_blocks(
    workspace_id=id,
    scope='WORKSPACE',
    anchor_role='customer'
)

# Product agent
product_memory = get_blocks(
    basket_id=id,
    semantic_type=['feature', 'metric', 'insight']
)
```

### Temporal Queries

```sql
-- What were our intents in Q3 2024?
SELECT * FROM blocks
WHERE basket_id = :id
  AND semantic_type = 'intent'
  AND created_at BETWEEN '2024-07-01' AND '2024-09-30';
```

### Memory Export

```sql
-- Export complete memory graph
SELECT
  b.*,
  ARRAY_AGG(v.* ORDER BY v.version DESC) as version_history,
  ARRAY_AGG(r.* WHERE r.from_id = b.id) as outgoing_relationships
FROM blocks b
LEFT JOIN get_block_version_history(b.id) v ON true
LEFT JOIN substrate_relationships r ON r.from_id = b.id
WHERE b.workspace_id = :id
GROUP BY b.id;
```

---

## Comparison with Industry Standards

### ChatGPT Memory (OpenAI)

| Feature | ChatGPT | Yarnnn v3.0 |
|---------|---------|-------------|
| Saved memories | User-explicit facts | CONSTANT blocks with WORKSPACE scope |
| Chat history | All conversations | All ACCEPTED blocks |
| Memory categories | Emergent (no predefined) | Emergent (semantic_types + anchors) |
| Cross-session | Redis vector cache | Scope elevation (WORKSPACE/ORG) |
| Versioning | Not exposed | Explicit parent_block_id chains |

**Alignment**: ✅ Both use emergent organization, no rigid schemas

### LangGraph Memory (LangChain)

| Feature | LangGraph | Yarnnn v3.0 |
|---------|-----------|-------------|
| Short-term memory | Session context | Recent validated blocks (LIMIT 50) |
| Long-term memory | Persistent store | CONSTANT blocks with scope |
| Memory blocks | Discrete functional units | Blocks with semantic_type |
| State management | Checkpointing | State machine + versioning |
| Multi-session | Thread persistence | Workspace scope sharing |

**Alignment**: ✅ Both separate session vs persistent memory

### Mem0 Agent Memory

| Feature | Mem0 | Yarnnn v3.0 |
|---------|------|-------------|
| Semantic memory | Vector embeddings | Blocks (embeddings ready) |
| Temporal versioning | History tracking | parent_block_id chains |
| Priority scoring | Importance weights | anchor_confidence |
| Cross-session | User/org memory | Scope elevation |
| Emergent org | No fixed schemas | No anchor constraints |

**Alignment**: ✅ Both use temporal versioning + priority scoring

---

## Summary

**Yarnnn Substrate Canon v3.1** implements an emergent memory architecture that:

1. **Unifies substrate** — One table, semantic_type differentiates
2. **Enables versioning** — Universal parent_block_id chains
3. **Supports maturation** — State + scope progression
4. **Allows emergent anchors** — No predefined vocabulary
5. **Facilitates LLM memory** — Session + persistent patterns
6. **Aligns with industry** — ChatGPT, LangGraph, Mem0 patterns
7. **V3.1: Semantic intelligence** — Vector embeddings + causal relationships for agent reasoning

**Key principle**: Organization emerges from usage, not prescription.

**Result**: Best-in-class foundation for multi-platform, multi-agent memory management with semantic reasoning.

---

## V3.1: Semantic Layer Extension

**Purpose:** Enable agents to reason semantically, not just structurally

**Complete technical design:** See [SEMANTIC_LAYER_INTEGRATION_DESIGN.md](./SEMANTIC_LAYER_INTEGRATION_DESIGN.md)

### Architecture Summary

#### 1. Vector Embeddings

- **Scope:** `blocks` table only (ACCEPTED+ state)
- **Model:** OpenAI text-embedding-3-small (1536 dimensions)
- **Storage:** `blocks.embedding` column
- **Generation:** After governance approval (async)

**Purpose:** Semantic duplicate detection (P1), theme-based retrieval (P3, P4), cross-basket pattern discovery

#### 2. Causal Relationships

**Schema:** `substrate_relationships` table

**Types:** 4 core relationships
- `addresses`: Solution addresses problem
- `supports`: Evidence supports claim
- `contradicts`: Conflicts with statement
- `depends_on`: Prerequisite dependency

**Inference:** P2 agent (semantic search + LLM verification)
**Governance:** Proposed → Accepted (auto-accept high confidence)

**Purpose:** Causal reasoning (P3), narrative coherence (P4), decision tracing

#### 3. Integration Points

| Pillar | Integration | Impact |
|--------|-------------|--------|
| P0 | None | Raw dumps not embedded (transient) |
| P1 | Semantic duplicate detection | 30-40% fewer duplicate blocks |
| P2 | Causal relationship inference | 60%+ blocks have relationships |
| P3 | Semantic retrieval + graph traversal | Richer causal insights |
| P4 | Theme-based composition | More coherent narratives |

### Design Principles

1. **Embed substrate, not raw input** (quality over quantity)
2. **Agent-first, not user-first** (intelligence over features)
3. **Structure + semantics** (augment, don't replace)
4. **Deliberate integration** (each pillar explicitly uses semantic layer)

### Success Metrics

- Duplicate rate: <5% (down from ~15%)
- Relationship precision: >80%
- Block coverage: >60% have relationships
- Context relevance: >85%

### Cost Model

- ~$0.05 per 1000 blocks (embeddings + relationship verification)
- Negligible at scale

---

**Document version**: 3.1.0
**Last updated**: 2025-01-15
**Changelog**:
- v3.1.0 (2025-01-15): Semantic layer integration (embeddings + relationships)
- v3.0.0 (2025-01-15): Initial v3 canon — emergent trilogy, unified substrate
- v2.x (2024): Dual substrate model (blocks + context_items)
