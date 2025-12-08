# Yarnnn Substrate Canon v3.0 Migration

**Status**: Planning
**Type**: Major Version — Breaking Changes
**Impact**: All substrate layers (P0-P4), Frontend, API

---

## Executive Summary

**What**: Unify `context_items` and `blocks` into single substrate table with emergent anchors
**Why**: Align with industry best practices (ChatGPT memory, LangGraph patterns) and future-proof for multi-platform/multi-agent memory management
**How**: Schema migration + agent refactoring + API updates

---

## Strategic Rationale

### Industry Alignment Validation ✅

**ChatGPT Memory Model (OpenAI 2024-2025)**:
- No predefined memory categories
- Emergent organization from usage
- RAG + vector DB for semantic search
- Cross-session persistence via scoping

**LangGraph/LangChain Best Practices**:
- Memory blocks as discrete units
- Session (short-term) + long-term memory split
- Temporal versioning of knowledge
- Cross-session continuity

**Mem0/Letta Agent Memory**:
- Semantic memory with priority scoring
- Temporal knowledge graphs
- Hybrid vector + graph architecture
- Emergent categorization

**Yarnnn v3.0 matches all patterns** ✅

---

## Core Principles: The Emergent Trilogy

### 1. **Versioning** (Emergent Evolution)
- All blocks version identically: `parent_block_id` chains
- No special cases for meaning vs knowledge
- Version if identity persists ("same entity, updated understanding")
- New block if identity changes ("Series A" → "Series B")

### 2. **Maturation** (Emergent Lifecycle)
- State transitions: `PROPOSED → ACCEPTED → LOCKED → CONSTANT`
- Scope elevation: `NULL (local) → WORKSPACE → ORG → GLOBAL`
- No enforced maturity stages
- Natural accumulation + refinement over time

### 3. **Anchors** (Emergent Categorization)
- No predefined anchor vocabulary
- Agents propose anchors during P1 extraction
- Users tag anchors via Building Blocks UI
- Autocomplete from basket's existing anchor usage
- Each basket develops its own anchor vocabulary organically

---

## Architecture Changes

### Before (v2.x): Dual Substrate Model

```sql
-- Two tables, unclear boundary
CREATE TABLE blocks (
  semantic_type text,  -- 'fact', 'insight', 'action', ...
  anchor_role text CHECK (anchor_role IN ('problem', 'solution', ...)),  -- Rigid
  -- Versioning support
);

CREATE TABLE context_items (
  type text,  -- 'entity', 'classification', ...
  semantic_meaning text,
  -- NO versioning support
);

-- Separate state machines
block_state: PROPOSED | ACCEPTED | LOCKED | CONSTANT | SUPERSEDED
context_item_state: PROVISIONAL | PROPOSED | UNDER_REVIEW | ACTIVE | ARCHIVED
```

**Problems**:
- Arbitrary extraction decisions (block vs context_item?)
- Inconsistent versioning (blocks yes, context_items no)
- Dual CRUD paths, dual queries
- Context_items treated as afterthought

---

### After (v3.0): Unified Substrate Model

```sql
-- Single table, semantic_type differentiates
CREATE TABLE blocks (
  id uuid PRIMARY KEY,
  basket_id uuid NOT NULL,
  workspace_id uuid NOT NULL,

  -- What kind of substrate
  semantic_type text NOT NULL,  -- 'fact', 'insight', 'intent', 'objective', 'context', etc.

  -- Content
  title text NOT NULL,
  content text NOT NULL,

  -- Emergent anchoring (optional)
  anchor_role text,  -- Free text, no constraints
  anchor_status text CHECK (anchor_status IN ('proposed', 'accepted', 'rejected')),
  anchor_confidence real CHECK (anchor_confidence BETWEEN 0 AND 1),

  -- Universal lifecycle
  state block_state CHECK (state IN (
    'PROPOSED', 'ACCEPTED', 'LOCKED', 'CONSTANT', 'SUPERSEDED', 'REJECTED'
  )),

  -- Scope elevation (optional)
  scope scope_level,  -- NULL (basket-local), 'WORKSPACE', 'ORG', 'GLOBAL'

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
  CONSTRAINT constant_must_have_scope CHECK (
    (state = 'CONSTANT' AND scope IS NOT NULL) OR
    (state != 'CONSTANT')
  ),
  CONSTRAINT blocks_content_not_empty CHECK (
    content IS NOT NULL AND content != ''
  ),
  CONSTRAINT blocks_title_not_empty CHECK (
    title IS NOT NULL AND title != ''
  )
);

-- Indexes for common queries
CREATE INDEX idx_blocks_basket ON blocks(basket_id, state, created_at DESC);
CREATE INDEX idx_blocks_workspace_scope ON blocks(workspace_id, scope) WHERE scope IS NOT NULL;
CREATE INDEX idx_blocks_anchor ON blocks(basket_id, anchor_role, anchor_status) WHERE anchor_role IS NOT NULL;
CREATE INDEX idx_blocks_semantic_type ON blocks(basket_id, semantic_type);
CREATE INDEX idx_blocks_version_chain ON blocks(parent_block_id) WHERE parent_block_id IS NOT NULL;
```

**Benefits**:
- One substrate entity = one table
- Consistent versioning for ALL substrate
- Single CRUD path, single governance flow
- Emergent anchor vocabulary per basket
- Natural scope elevation for cross-basket memory

---

## Semantic Type Expansion

### Current Block semantic_types
`'summary', 'fact', 'insight', 'action', 'metric', 'event', 'status', 'quote', 'finding'`

### New semantic_types (from context_items migration)
`'intent', 'objective', 'rationale', 'principle', 'context', 'entity', 'classification', 'reference'`

### Combined v3.0 semantic_types

**Knowledge Types** (what we know):
- `fact` — Observable, verifiable statement
- `metric` — Measurable quantity
- `event` — Point-in-time occurrence
- `insight` — Derived understanding
- `action` — Recommended or completed action
- `quote` — Direct citation
- `finding` — Discovery or observation
- `summary` — Condensed overview

**Meaning Types** (why/how we know):
- `intent` — Purpose or goal
- `objective` — Measurable target
- `rationale` — Reasoning behind decision
- `principle` — Guiding rule or belief
- `assumption` — Presumed truth
- `context` — Framing information
- `constraint` — Boundary or limitation

**Structural Types** (organization):
- `entity` — Person, company, product reference
- `classification` — Categorical tag
- `reference` — External link or citation

---

## Migration Strategy

### Phase 1: Schema Migration (Database)

**Step 1.1: Backup**
```sql
-- Create safety net
CREATE TABLE context_items_backup_v2 AS
SELECT * FROM context_items;

CREATE TABLE blocks_backup_v2 AS
SELECT * FROM blocks;
```

**Step 1.2: Extend blocks table**
```sql
-- Remove anchor_role CHECK constraint
ALTER TABLE blocks DROP CONSTRAINT IF EXISTS blocks_anchor_role_check;

-- Allow NULL scope (was required for CONSTANT)
ALTER TABLE blocks ALTER COLUMN scope DROP NOT NULL;

-- Ensure scope can be NULL for local blocks
ALTER TABLE blocks DROP CONSTRAINT IF EXISTS blocks_check;
ALTER TABLE blocks ADD CONSTRAINT constant_must_have_scope CHECK (
  (state = 'CONSTANT' AND scope IS NOT NULL) OR
  (state != 'CONSTANT')
);
```

**Step 1.3: Migrate context_items → blocks**
```sql
-- Map context_items to blocks with semantic_type
INSERT INTO blocks (
  id,
  basket_id,
  workspace_id,
  semantic_type,
  title,
  content,
  anchor_role,
  anchor_status,
  anchor_confidence,
  state,
  scope,
  parent_block_id,
  version,
  proposal_id,
  raw_dump_id,
  confidence_score,
  last_validated_at,
  metadata,
  created_at,
  updated_at
)
SELECT
  ci.id,
  ci.basket_id,
  b.workspace_id,  -- Get workspace_id from basket

  -- Map type → semantic_type
  CASE
    WHEN ci.type = 'entity' THEN 'entity'
    WHEN ci.type = 'classification' THEN 'classification'
    WHEN ci.type LIKE '%intent%' THEN 'intent'
    WHEN ci.type LIKE '%objective%' THEN 'objective'
    WHEN ci.type LIKE '%context%' THEN 'context'
    ELSE 'reference'
  END AS semantic_type,

  ci.title,
  COALESCE(ci.content, ci.semantic_meaning, ci.description, ci.title) AS content,
  ci.anchor_role,
  ci.anchor_status,
  ci.anchor_confidence,

  -- Map context_item_state → block_state
  CASE ci.state
    WHEN 'ACTIVE' THEN 'ACCEPTED'::block_state
    WHEN 'PROPOSED' THEN 'PROPOSED'::block_state
    WHEN 'UNDER_REVIEW' THEN 'PROPOSED'::block_state
    WHEN 'PROVISIONAL' THEN 'PROPOSED'::block_state
    WHEN 'ARCHIVED' THEN 'SUPERSEDED'::block_state
    ELSE 'PROPOSED'::block_state
  END AS state,

  NULL AS scope,  -- Context items start as local (NULL scope)
  NULL AS parent_block_id,  -- No versioning history for migrated items
  1 AS version,
  ci.proposal_id,
  ci.raw_dump_id,
  ci.confidence_score,
  ci.updated_at AS last_validated_at,
  ci.metadata,
  ci.created_at,
  ci.updated_at
FROM context_items ci
JOIN baskets b ON ci.basket_id = b.id;

-- Verify migration
SELECT
  'blocks' as table_name, COUNT(*) as count
FROM blocks
UNION ALL
SELECT
  'context_items_migrated', COUNT(*)
FROM blocks
WHERE semantic_type IN ('entity', 'classification', 'context', 'intent', 'objective');
```

**Step 1.4: Update substrate_relationships**
```sql
-- Update relationships pointing to context_items
UPDATE substrate_relationships
SET from_type = 'block'
WHERE from_type = 'context_item';

UPDATE substrate_relationships
SET to_type = 'block'
WHERE to_type = 'context_item';

-- Update substrate_type enum
ALTER TYPE substrate_type RENAME TO substrate_type_old;
CREATE TYPE substrate_type AS ENUM ('block', 'dump', 'event', 'document');
ALTER TABLE substrate_relationships
  ALTER COLUMN from_type TYPE substrate_type USING from_type::text::substrate_type;
ALTER TABLE substrate_relationships
  ALTER COLUMN to_type TYPE substrate_type USING to_type::text::substrate_type;
DROP TYPE substrate_type_old;
```

**Step 1.5: Drop context_items table**
```sql
-- Drop views first
DROP VIEW IF EXISTS anchored_substrate;

-- Drop context_items
DROP TABLE context_items CASCADE;

-- Recreate anchored_substrate view with blocks only
CREATE VIEW anchored_substrate AS
SELECT
  'block'::text AS substrate_type,
  id AS substrate_id,
  basket_id,
  anchor_role,
  anchor_status,
  anchor_confidence,
  title,
  content,
  semantic_type,
  state::text AS state,
  created_at,
  updated_at,
  last_validated_at,
  metadata
FROM blocks
WHERE anchor_role IS NOT NULL;
```

---

### Phase 2: Backend Agent Updates (Python)

**Files to update**: ~40 Python files

**Key changes**:

**2.1: P1 Substrate Agent (improved_substrate_agent.py)**

```python
# Before: Dual return
return {
  "block_ingredients": blocks,
  "context_item_ingredients": context_items
}

# After: Single unified substrate
return {
  "substrate_ingredients": blocks,  # Contains all semantic_types
  "extraction_summary": {
    "knowledge_blocks": len([b for b in blocks if b['semantic_type'] in KNOWLEDGE_TYPES]),
    "meaning_blocks": len([b for b in blocks if b['semantic_type'] in MEANING_TYPES]),
    "structural_blocks": len([b for b in blocks if b['semantic_type'] in STRUCTURAL_TYPES])
  }
}

# Emergent anchor proposal
def _transform_to_substrate(extraction, dump_id):
    blocks = []

    for fact in extraction.facts:
        blocks.append({
            "semantic_type": "fact",
            "title": f"Fact: {fact.text[:50]}",
            "content": fact.text,
            "anchor_role": _infer_anchor_role(fact),  # ← Emergent
            "anchor_status": "proposed",
            "anchor_confidence": fact.confidence
        })

    for ctx in extraction.context:
        blocks.append({
            "semantic_type": "entity",  # ← Was context_item, now block
            "title": ctx.entity,
            "content": _generate_semantic_meaning(ctx),
            "anchor_role": None,  # ← Entities may not need anchors
            "anchor_status": None
        })

    return blocks  # Single list

def _infer_anchor_role(fact) -> str | None:
    """Emergent anchor inference from content"""
    content_lower = fact.text.lower()

    # Agent proposes anchor based on semantic analysis
    if "problem" in content_lower or "issue" in content_lower:
        return "problem"
    elif "goal" in content_lower or "objective" in content_lower:
        return "objective"
    elif "metric" in content_lower or "measure" in content_lower:
        return "metric"
    # ... more heuristics

    return None  # No anchor if unclear
```

**2.2: Governance Processor (governance_processor.py)**

```python
# Before: Separate block and context_item operations
async def _execute_create_block(op, basket_id):
    await supabase.table('blocks').insert(...)

async def _execute_create_context_item(op, basket_id):
    await supabase.table('context_items').insert(...)

# After: Unified
async def _execute_create_block(op, basket_id):
    """Creates any substrate block (knowledge, meaning, or structural)"""
    block_data = {
        "basket_id": basket_id,
        "semantic_type": op.get("semantic_type", "fact"),
        "title": op["title"],
        "content": op["content"],
        "anchor_role": op.get("anchor_role"),  # May be None
        "anchor_status": op.get("anchor_status", "proposed"),
        "state": "ACCEPTED",  # Governance approved
        "version": 1
    }
    await supabase.table('blocks').insert(block_data)

# Operation types simplified
OPERATION_TYPES = {
    "CreateBlock",  # Creates any semantic_type
    "EditBlock",    # Creates new version
    "MergeBlocks",  # Creates merged block
    # No more CreateContextItem
}
```

**2.3: P2 Graph Agent (graph_agent.py)**

```python
# Before: Query blocks + context_items separately
blocks = await supabase.table('blocks').select('*').eq('basket_id', basket_id)
context_items = await supabase.table('context_items').select('*').eq('basket_id', basket_id)
all_substrate = blocks + context_items

# After: Single query
all_substrate = await supabase.table('blocks')\
    .select('*')\
    .eq('basket_id', basket_id)\
    .eq('state', 'ACCEPTED')\
    .execute()

# Build graph from unified substrate
for block in all_substrate:
    if block['semantic_type'] in KNOWLEDGE_TYPES:
        # Knowledge nodes (facts, insights)
        add_knowledge_node(block)
    elif block['semantic_type'] in MEANING_TYPES:
        # Meaning nodes (intent, objectives)
        add_meaning_node(block)
    elif block['semantic_type'] == 'entity':
        # Entity nodes
        add_entity_node(block)
```

**2.4: P3 Reflection Agent (reflection_agent_canon_v2.py)**

```python
# Before: Separate queries
async def get_basket_substrate(basket_id):
    blocks = await supabase.from('blocks').select('*').eq('basket_id', basket_id)
    context_items = await supabase.from('context_items').select('*').eq('basket_id', basket_id)
    return {"blocks": blocks, "context_items": context_items}

# After: Single query with semantic filtering
async def get_basket_substrate(basket_id):
    # Get all substrate
    all_blocks = await supabase.from('blocks')\
        .select('*')\
        .eq('basket_id', basket_id)\
        .eq('state', 'ACCEPTED')\
        .execute()

    # Categorize by semantic_type for analysis
    knowledge = [b for b in all_blocks if b['semantic_type'] in KNOWLEDGE_TYPES]
    meaning = [b for b in all_blocks if b['semantic_type'] in MEANING_TYPES]
    anchored = [b for b in all_blocks if b['anchor_role'] is not None]

    return {
        "all_substrate": all_blocks,
        "knowledge": knowledge,
        "meaning": meaning,
        "anchored": anchored
    }
```

---

### Phase 3: Frontend API Updates (TypeScript)

**Files to update**: ~105 TypeScript files

**3.1: Type definitions**

```typescript
// Before: Separate types
interface Block {
  semantic_type: string;
  anchor_role?: 'problem' | 'solution' | ...;  // Enum
}

interface ContextItem {
  type: string;
  semantic_meaning?: string;
}

// After: Unified
interface Block {
  id: string;
  basket_id: string;
  workspace_id: string;

  semantic_type:
    | 'fact' | 'insight' | 'action' | 'metric'  // Knowledge
    | 'intent' | 'objective' | 'rationale'      // Meaning
    | 'entity' | 'classification';               // Structural

  title: string;
  content: string;

  anchor_role?: string;  // Free text, no enum
  anchor_status?: 'proposed' | 'accepted' | 'rejected';
  anchor_confidence?: number;

  state: 'PROPOSED' | 'ACCEPTED' | 'LOCKED' | 'CONSTANT' | 'SUPERSEDED' | 'REJECTED';
  scope?: 'WORKSPACE' | 'ORG' | 'GLOBAL';

  parent_block_id?: string;
  version: number;

  confidence_score?: number;
  last_validated_at?: string;
  metadata?: Record<string, any>;

  created_at: string;
  updated_at: string;
}

// Helper types
type KnowledgeBlock = Block & {
  semantic_type: 'fact' | 'insight' | 'action' | 'metric' | 'event' | 'finding' | 'quote' | 'summary'
};

type MeaningBlock = Block & {
  semantic_type: 'intent' | 'objective' | 'rationale' | 'principle' | 'assumption' | 'context' | 'constraint'
};

type StructuralBlock = Block & {
  semantic_type: 'entity' | 'classification' | 'reference'
};
```

**3.2: API routes**

```typescript
// Before: Separate endpoints
GET /api/baskets/[id]/building-blocks  // Returns blocks
GET /api/baskets/[id]/context-items    // Returns context_items

// After: Unified with filtering
GET /api/baskets/[id]/substrate?type=knowledge  // semantic_type filter
GET /api/baskets/[id]/substrate?type=meaning
GET /api/baskets/[id]/substrate?type=structural
GET /api/baskets/[id]/substrate  // All substrate

// Building Blocks page
async function getKnowledgeBlocks(basketId: string) {
  const { data } = await supabase
    .from('blocks')
    .select('*')
    .eq('basket_id', basketId)
    .in('semantic_type', ['fact', 'insight', 'action', 'metric', 'event', 'finding'])
    .eq('state', 'ACCEPTED')
    .order('last_validated_at', { ascending: false });

  return data as KnowledgeBlock[];
}

// Context/Memory page
async function getStructuralBlocks(basketId: string) {
  const { data } = await supabase
    .from('blocks')
    .select('*')
    .eq('basket_id', basketId)
    .in('semantic_type', ['entity', 'classification', 'reference'])
    .order('created_at', { ascending: false });

  return data as StructuralBlock[];
}

// Anchor vocabulary discovery
GET /api/baskets/[id]/anchors/vocabulary

async function getAnchorVocabulary(basketId: string) {
  const { data } = await supabase
    .rpc('get_basket_anchor_vocabulary', { p_basket_id: basketId });

  return data as Array<{
    anchor_role: string;
    usage_count: number;
    accepted_count: number;
    avg_confidence: number;
  }>;
}
```

**3.3: Building Blocks page updates**

```typescript
// Before: Queried blocks only
const { data: blocks } = await supabase.from('blocks')...;
const { data: contextItems } = await supabase.from('context_items')...;

// After: Query with semantic_type filter
const { data: knowledgeBlocks } = await supabase
  .from('blocks')
  .select('*')
  .eq('basket_id', basketId)
  .in('semantic_type', KNOWLEDGE_TYPES)
  .eq('state', 'ACCEPTED');

// Emergent anchor autocomplete
function AnchorTagInput({ basketId, blockId }: Props) {
  const { data: anchorVocabulary } = useSWR(
    `/api/baskets/${basketId}/anchors/vocabulary`,
    fetcher
  );

  return (
    <Autocomplete
      suggestions={anchorVocabulary.map(a => ({
        value: a.anchor_role,
        label: `${a.anchor_role} (used ${a.usage_count} times)`,
        confidence: a.avg_confidence
      }))}
      onSelect={(anchor) => proposeAnchorTag(blockId, anchor)}
      allowCustom={true}
      placeholder="Add anchor tag..."
    />
  );
}

// Proposal for anchor tagging
async function proposeAnchorTag(blockId: string, anchorRole: string) {
  await fetchWithToken('/api/proposals', {
    method: 'POST',
    body: JSON.stringify({
      proposal_kind: 'Edit',
      ops: [{
        op: 'UpdateBlockAnchor',
        block_id: blockId,
        anchor_role: anchorRole,
        anchor_status: 'proposed'
      }]
    })
  });
}
```

---

### Phase 4: Canon Documentation Updates

**Files to create/update**:
- `docs/YARNNN_SUBSTRATE_CANON_V3.md` (new)
- `docs/YARNNN_CANON.md` (update to v3.0)
- `docs/YARNNN_ARCHITECTURE_CANON.md` (update substrate section)

**Key documentation changes**:

```markdown
# YARNNN Substrate Canon v3.0

## Core Principle: Unified Substrate with Emergent Organization

**One substrate type**: All memory stored in `blocks` table
**Semantic differentiation**: `semantic_type` field distinguishes knowledge/meaning/structural
**Emergent anchors**: Anchor vocabulary develops organically per basket
**Universal versioning**: All blocks version identically via `parent_block_id`
**Scope elevation**: Blocks can elevate from basket → workspace → org → global

## Substrate Types

### Knowledge Blocks (What We Know)
- `fact`, `metric`, `event`, `insight`, `action`, `finding`, `quote`, `summary`
- Verifiable, observable, measurable
- Version when understanding changes

### Meaning Blocks (Why/How We Know)
- `intent`, `objective`, `rationale`, `principle`, `assumption`, `context`, `constraint`
- Interpretive, intentional, framing
- Version when interpretation evolves

### Structural Blocks (Organization)
- `entity`, `classification`, `reference`
- Organizational, relational
- May or may not version

## Emergent Anchors

Anchors emerge from usage, not predefined lists:

1. **Agent proposes**: P1 extraction infers anchor from content semantics
2. **User tags**: Building Blocks UI allows anchor tagging
3. **Autocomplete**: Shows basket's existing anchor vocabulary
4. **Governance**: Accepts/rejects/modifies proposed anchors

Example anchor vocabularies:
- Product basket: `problem`, `solution`, `metric`, `feature`
- Research basket: `hypothesis`, `evidence`, `conclusion`, `limitation`
- Legal basket: `obligation`, `risk`, `precedent`, `compliance`

## State Machine (Universal)

All blocks follow same lifecycle:
```
PROPOSED → ACCEPTED → LOCKED → CONSTANT
                    ↘ SUPERSEDED (when versioned)
         ↘ REJECTED
```

## Scope Elevation (Cross-Basket Memory)

```
NULL (basket-local)
  ↓ (important to workspace)
WORKSPACE (cross-basket)
  ↓ (important to organization)
ORG (organization-wide)
  ↓ (universal truth)
GLOBAL (system-level constant)
```

## Versioning Rules

**Version if identity persists:**
- Same entity, updated understanding
- Same metric, new value
- Same vision, clarified scope

**New block if identity changes:**
- Different goals (Series A → Series B)
- Different problems
- Different time periods

## Memory Patterns for LLM Agents

### Short-term memory (session)
```sql
SELECT * FROM blocks
WHERE basket_id = ?
ORDER BY last_validated_at DESC
LIMIT 50;
```

### Long-term memory (persistent)
```sql
SELECT * FROM blocks
WHERE workspace_id = ?
  AND state = 'CONSTANT'
  AND scope IN ('WORKSPACE', 'ORG');
```

### Meaning context (framing)
```sql
SELECT * FROM blocks
WHERE basket_id = ?
  AND semantic_type IN ('intent', 'objective', 'principle')
  AND state = 'ACCEPTED';
```

### Anchored priorities
```sql
SELECT * FROM blocks
WHERE basket_id = ?
  AND anchor_status = 'accepted'
ORDER BY anchor_confidence DESC;
```
```

---

## Migration Execution Plan

### Pre-Migration Checklist

- [ ] Full database backup
- [ ] Staging environment testing
- [ ] Migration script validated on copy of production data
- [ ] Rollback plan prepared
- [ ] Downtime window scheduled (estimate: 2-4 hours)
- [ ] Team notified

### Execution Steps

**Day 1: Schema Migration (Database)**
1. Enable maintenance mode
2. Create backups (context_items, blocks)
3. Run migration SQL (Steps 1.1-1.5)
4. Verify row counts match
5. Test queries on unified blocks table
6. Disable maintenance mode

**Day 2-3: Backend Updates (Python)**
1. Update P1 substrate agent
2. Update governance processor
3. Update P2 graph agent
4. Update P3/P4 agents
5. Deploy API changes
6. Test P0→P1→P2→P3→P4 flow

**Day 4-5: Frontend Updates (TypeScript)**
1. Update type definitions
2. Update API routes
3. Update Building Blocks page
4. Update Memory/Context page
5. Deploy frontend changes
6. Test UI flows

**Day 6: Canon Documentation**
1. Write Substrate Canon v3.0
2. Update main Canon docs
3. Update architecture docs
4. Update GitBook user-facing docs

**Day 7: Validation**
1. End-to-end testing
2. Performance benchmarks
3. User acceptance testing
4. Monitor for issues

### Rollback Plan

If critical issues discovered:

```sql
-- Restore context_items table
CREATE TABLE context_items AS
SELECT * FROM context_items_backup_v2;

-- Remove migrated blocks
DELETE FROM blocks
WHERE id IN (SELECT id FROM context_items_backup_v2);

-- Restore substrate_relationships
UPDATE substrate_relationships
SET from_type = 'context_item'
WHERE from_type = 'block'
  AND from_id IN (SELECT id FROM context_items_backup_v2);

-- Redeploy v2.x code
```

---

## Success Metrics

**Technical**:
- [ ] All context_items migrated to blocks (row count match)
- [ ] All queries return expected results
- [ ] P0→P4 pipeline functions correctly
- [ ] No performance degradation (<5% query time increase)

**Functional**:
- [ ] Users can create/edit blocks via Building Blocks UI
- [ ] Anchors can be tagged and appear in autocomplete
- [ ] Versioning creates proper parent_block_id chains
- [ ] Scope elevation works (basket → workspace)

**Strategic**:
- [ ] LLM agents can query unified substrate
- [ ] Multi-session memory retrieval works
- [ ] Cross-basket context sharing enabled
- [ ] Foundation for multi-platform support validated

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Data loss during migration | HIGH | Full backups, staging validation, row count verification |
| Performance degradation | MEDIUM | Proper indexing, query optimization, benchmark testing |
| Breaking API changes | MEDIUM | Staged rollout, version compatibility layer |
| User confusion (UI changes) | LOW | Documentation, tooltips, gradual feature rollout |
| Anchor proliferation | LOW | UI shows vocabulary, suggests consolidation |

---

## Post-Migration Opportunities

**Enabled by v3.0**:

1. **Vector embeddings**: Add `embedding` column to blocks for semantic search
2. **Multi-platform memory**: Same substrate accessible from web, mobile, Slack, API
3. **Agent memory profiles**: Different agents query different semantic_types
4. **Cross-basket insights**: P3 reflections across workspace scope
5. **Memory export**: User downloads their complete memory graph
6. **Temporal queries**: "Show me all intent blocks from Q3 2024"
7. **Anchor analytics**: "What problems have we solved over time?"

---

## Timeline

**Estimated duration**: 2 weeks (10 working days)

- **Week 1**: Schema migration + Backend updates + Testing
- **Week 2**: Frontend updates + Documentation + Validation

**Go-live target**: [TBD - coordinate with team]

---

## Approval Required

This is a **major version migration** requiring:
- [ ] Technical lead approval (architecture)
- [ ] Product lead approval (UX implications)
- [ ] Engineering team approval (implementation plan)
- [ ] Stakeholder approval (downtime window)

---

**Document version**: 1.0
**Last updated**: 2025-01-15
**Next review**: Post-migration retrospective
