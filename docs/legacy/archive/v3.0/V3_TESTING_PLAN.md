# YARNNN V3.0 Substrate - Comprehensive Testing Plan

## 🎯 Testing Philosophy

This test plan focuses on **quality-driven validation** - not just "does it work" but "does it work according to the v3.0 philosophy and deliver on the Sacred Principles?"

Each test validates:
1. **Technical correctness** (does it function?)
2. **Canon compliance** (does it follow v3.0 principles?)
3. **Service intent** (does it deliver value?)
4. **Quality metrics** (is the output high-quality?)

---

## 📋 Pre-Test Checklist

### Schema Migration Verification
```sql
-- 1. Verify context_items table is DROPPED
SELECT COUNT(*) FROM information_schema.tables
WHERE table_name = 'context_items';
-- Expected: 0

-- 2. Verify blocks table has v3.0 fields
SELECT column_name FROM information_schema.columns
WHERE table_name = 'blocks'
AND column_name IN ('anchor_role', 'anchor_status', 'anchor_confidence', 'parent_block_id', 'scope');
-- Expected: All 5 columns present

-- 3. Verify helper function exists
SELECT routine_name FROM information_schema.routines
WHERE routine_name = 'get_basket_anchor_vocabulary';
-- Expected: 1 row

-- 4. Verify substrate_type enum updated
SELECT unnest(enum_range(NULL::substrate_type));
-- Expected: 'block', 'dump', 'timeline_event' (NO 'context_item')
```

---

## 🧪 Test Suite

### Test 1: P0→P1 - Capture & Substrate Extraction

**Goal**: Verify raw memory capture flows into high-quality substrate with emergent anchors

#### Test Scenario
```
Input: User dumps strategic planning notes:
"We need to improve conversion rates from 2% to 5% by Q2.
Current blockers: slow checkout, no mobile optimization, weak CTAs.
Target customers: SMB owners in healthcare.
Key competitor: Acme Corp with 8% conversion."
```

#### Quality Checks

**1. P0 Capture Quality**
- ✅ Raw dump created with immutable content
- ✅ Workspace_id and basket_id correctly set
- ✅ Timeline event emitted: `dump_created`
- ✅ No interpretation at P0 (Sacred Principle #1)

**2. P1 Substrate Extraction Quality**

**Expected Output Structure:**
```typescript
{
  substrate_ingredients: [
    {
      semantic_type: "metric",
      title: "Current conversion rate baseline",
      content: "Current conversion rate is 2%",
      anchor_role: "metric",          // Emergent anchor inferred
      anchor_status: "proposed",
      anchor_confidence: 0.85,
      confidence_score: 0.9
    },
    {
      semantic_type: "objective",     // Meaning type
      title: "Conversion rate target",
      content: "Improve conversion rates from 2% to 5% by Q2",
      anchor_role: "goal",            // Emergent anchor
      anchor_status: "proposed",
      anchor_confidence: 0.80,
      confidence_score: 0.85
    },
    {
      semantic_type: "finding",       // Knowledge type
      title: "Checkout speed blocker",
      content: "Slow checkout is a current blocker",
      anchor_role: "problem",         // Emergent anchor
      anchor_status: "proposed",
      anchor_confidence: 0.75,
      confidence_score: 0.80
    },
    {
      semantic_type: "entity",        // Structural type
      title: "SMB healthcare owners",
      content: "Target customer segment: SMB owners in healthcare",
      anchor_role: null,              // Entities typically don't need anchors
      anchor_status: null,
      confidence_score: 0.85
    },
    {
      semantic_type: "entity",
      title: "Acme Corp",
      content: "Key competitor with 8% conversion rate",
      anchor_role: "competitor",      // Optional emergent anchor
      anchor_status: "proposed",
      anchor_confidence: 0.70,
      confidence_score: 0.80
    }
  ],
  extraction_summary: {
    total_blocks: 5,
    knowledge_blocks: 2,  // metric + finding
    meaning_blocks: 1,    // objective
    structural_blocks: 2, // entities
    anchors_proposed: 4
  }
}
```

**Quality Validation:**
- ✅ **Semantic Diversity**: Mix of knowledge, meaning, structural types
- ✅ **Anchor Emergence**: Anchors inferred from content semantics (goal, problem, metric, competitor)
- ✅ **No Fixed Categories**: anchor_role is free-text, not from predefined enum
- ✅ **Confidence Scores**: All blocks have confidence_score ≥ 0.70
- ✅ **Anchor Confidence**: Proposed anchors have anchor_confidence scores
- ✅ **Title Quality**: Concise, descriptive titles (not just content snippets)
- ✅ **No Duplication**: Each distinct concept gets one block

**3. Governance Proposal Quality**
- ✅ Proposal created with operation_type: "CreateBlock" (not CreateContextItem)
- ✅ All blocks include v3.0 anchor fields
- ✅ Proposal status: "PROPOSED" (awaiting approval)
- ✅ Provenance: Links to raw_dump_id

---

### Test 2: Emergent Anchor Vocabulary

**Goal**: Verify anchors emerge naturally and vocabulary can be queried

#### Test Scenario
After Test 1, add more dumps to same basket:
- "Need to hire 2 engineers by March. Budget: $200k."
- "Competitor analysis: Acme has better UX, slower support."

#### Quality Checks

**Expected Anchor Evolution:**
```sql
SELECT * FROM get_basket_anchor_vocabulary('basket-uuid');

-- Expected output:
anchor_role | usage_count | accepted_count | avg_confidence | semantic_types
------------|-------------|----------------|----------------|----------------
metric      | 3           | 2              | 0.83           | {metric,fact}
problem     | 2           | 2              | 0.78           | {finding}
goal        | 2           | 1              | 0.82           | {objective,intent}
competitor  | 2           | 2              | 0.72           | {entity}
resource    | 1           | 0              | 0.75           | {fact}
```

**Quality Validation:**
- ✅ **Vocabulary Emergence**: New anchors appear naturally ("resource" added)
- ✅ **Frequency Tracking**: usage_count reflects actual usage
- ✅ **Acceptance Tracking**: accepted_count shows governance outcomes
- ✅ **Quality Metrics**: avg_confidence computed per anchor_role
- ✅ **Semantic Associations**: semantic_types array shows what types use each anchor

---

### Test 3: Universal Versioning

**Goal**: Verify all blocks version identically via parent_block_id chains

#### Test Scenario
1. Create metric block: "Conversion rate: 2%"
2. Update same metric: "Conversion rate: 2.3%" (refined measurement)
3. Update again: "Conversion rate: 2.8%" (continued tracking)

#### Quality Checks

**Expected Block Chain:**
```sql
-- Block v1 (original)
id: block-uuid-v1
title: "Conversion rate baseline"
content: "Conversion rate: 2%"
parent_block_id: NULL
state: SUPERSEDED

-- Block v2 (first update)
id: block-uuid-v2
title: "Conversion rate baseline"
content: "Conversion rate: 2.3%"
parent_block_id: block-uuid-v1
state: SUPERSEDED

-- Block v3 (latest)
id: block-uuid-v3
title: "Conversion rate baseline"
content: "Conversion rate: 2.8%"
parent_block_id: block-uuid-v2
state: ACCEPTED
```

**Quality Validation:**
- ✅ **Chain Integrity**: Each version links to previous via parent_block_id
- ✅ **Identity Preservation**: Same title across versions (identity persists)
- ✅ **State Management**: Old versions marked SUPERSEDED, current is ACCEPTED
- ✅ **No Special Cases**: Versioning works identically for ALL semantic_types
- ✅ **Emergent Rule**: Version if identity persists, new block if identity changes

---

### Test 4: P1→P2 - Graph Relationships

**Goal**: Verify P2 creates semantic connections from unified blocks

#### Test Scenario
Given substrate from Test 1, P2 should detect relationships:
- Metric → Goal (supports)
- Problem → Goal (blocks)
- Entity (customer) → Goal (benefits_from)
- Entity (competitor) → Metric (benchmarks_against)

#### Quality Checks

**Expected Relationships:**
```typescript
[
  {
    from_type: "block",  // V3.0: Always block
    from_id: "metric-block-uuid",
    to_type: "block",    // V3.0: Always block
    to_id: "goal-block-uuid",
    relationship_type: "related_content",
    strength: 0.75,
    description: "Current metric provides baseline for goal"
  },
  {
    from_type: "block",
    from_id: "problem-block-uuid",
    to_type: "block",
    to_id: "goal-block-uuid",
    relationship_type: "impact_relationship",
    strength: 0.80,
    description: "Blocker impacts achievement of goal"
  },
  {
    from_type: "block",
    from_id: "goal-block-uuid",
    to_type: "block",  // Entity block
    to_id: "customer-entity-uuid",
    relationship_type: "entity_reference",  // V3.0: renamed from context_reference
    strength: 0.75,
    description: "Goal mentions target customer entity"
  }
]
```

**Quality Validation:**
- ✅ **Unified Types**: All from_type and to_type are "block" (no "context_item")
- ✅ **Entity References**: Detects references from knowledge blocks to entity blocks
- ✅ **Semantic Relationships**: Uses appropriate relationship_type (not just generic "related")
- ✅ **Strength Scoring**: Relationships have meaningful strength scores
- ✅ **Sacred Rule**: P2 creates relationships only, never modifies substrate

---

### Test 5: P2→P3 - Insight Generation

**Goal**: Verify P3 generates interpretive intelligence from substrate + graph

#### Test Scenario
From substrate and relationships above, P3 should generate insight_canon

#### Quality Checks

**Expected Insight Structure:**
```typescript
{
  insight_type: "insight_canon",
  basket_id: "basket-uuid",
  is_current: true,
  content: {
    what_matters_now: "Conversion optimization is the primary focus with a clear 2→5% target by Q2",
    key_themes: ["metrics_tracking", "customer_targeting", "competitive_positioning"],
    critical_path: [
      "Address checkout speed blocker (highest priority)",
      "Mobile optimization for healthcare SMB segment",
      "Benchmark against Acme Corp's 8% conversion"
    ],
    emergent_patterns: [
      "Strong metric-driven approach with baseline established",
      "Customer segment clarity (healthcare SMBs)",
      "Competitive awareness influencing strategy"
    ],
    substrate_summary: {
      total_blocks: 5,
      knowledge_blocks: 2,
      meaning_blocks: 1,
      structural_blocks: 2,
      key_anchors: ["metric", "goal", "problem", "competitor"]
    }
  },
  substrate_hash: "...",
  graph_signature: "...",
  previous_id: null
}
```

**Quality Validation:**
- ✅ **Interpretive Quality**: Goes beyond substrate to provide "what matters" interpretation
- ✅ **Theme Emergence**: Identifies patterns across blocks (not just listing them)
- ✅ **Actionability**: Critical path provides clear next steps
- ✅ **Anchor Integration**: References emergent anchors in analysis
- ✅ **Semantic Awareness**: Distinguishes knowledge vs meaning vs structural substrate
- ✅ **Immutability**: Creates new version, doesn't edit in place
- ✅ **Context Tracking**: substrate_hash and graph_signature for freshness

---

### Test 6: P3→P4 - Document Composition

**Goal**: Verify P4 composes coherent narrative from insights + substrate

#### Test Scenario
Request document_canon composition with intent: "Strategic planning summary"

#### Quality Checks

**Expected Document Structure:**
```typescript
{
  document_type: "document_canon",
  basket_id: "basket-uuid",
  title: "Conversion Optimization Strategy - Q2 Focus",
  content_raw: `
# Conversion Optimization Strategy

## Current State
Our conversion rate baseline is 2%, as measured against the target of 5% by Q2.
This represents a 2.5x improvement goal with clear milestones.

## Target Market
We're focused on healthcare SMB owners, a segment with specific needs around...

## Key Blockers
1. **Checkout Speed** - Current bottleneck affecting conversion
2. **Mobile Experience** - Not optimized for on-the-go healthcare professionals
3. **CTA Weakness** - Calls to action lack compelling messaging

## Competitive Landscape
Acme Corp maintains 8% conversion, providing a benchmark 3x higher than our current state...

## Strategic Priorities
[Composed narrative incorporating all substrate with emergent structure]
  `,
  substrate_references: [
    { block_id: "metric-uuid", relevance_score: 0.95, section: "Current State" },
    { block_id: "goal-uuid", relevance_score: 0.90, section: "Current State" },
    { block_id: "entity-customer-uuid", relevance_score: 0.85, section: "Target Market" },
    { block_id: "problem-uuid", relevance_score: 0.80, section: "Key Blockers" },
    { block_id: "competitor-uuid", relevance_score: 0.75, section: "Competitive Landscape" }
  ],
  metadata: {
    substrate_count: 5,
    knowledge_blocks: 2,
    meaning_blocks: 1,
    entity_blocks: 2,
    primary_anchors: ["metric", "goal", "problem"],
    composition_strategy: "thematic",
    insight_canon_id: "insight-uuid"
  }
}
```

**Quality Validation:**
- ✅ **Narrative Coherence**: Flows naturally, not just block concatenation
- ✅ **Semantic Organization**: Sections align with semantic types (metrics → context → blockers)
- ✅ **Anchor-Driven Structure**: Emergent anchors inform document sections
- ✅ **Substrate Provenance**: All assertions link back to substrate via references
- ✅ **Entity Integration**: Entity blocks naturally incorporated (not listed separately)
- ✅ **Insight Integration**: P3 insights inform narrative structure and emphasis
- ✅ **Immutability**: Content stored in document_versions (not editable)
- ✅ **Service Intent**: Document is an "activation surface" for strategic planning

---

### Test 7: Scope Elevation (Cross-Basket Memory)

**Goal**: Verify WORKSPACE/ORG/GLOBAL scope enables cross-basket memory

#### Test Scenario
1. Create block in Basket A with NULL scope (basket-local)
2. Create block in Basket A with WORKSPACE scope
3. Query from Basket B - should see WORKSPACE block, not NULL scope block

#### Quality Checks

**Expected Behavior:**
```sql
-- From Basket A
INSERT INTO blocks (semantic_type, scope, ...)
VALUES ('principle', NULL, ...),      -- Basket-local
       ('principle', 'WORKSPACE', ...); -- Workspace-wide

-- Query from Basket B
SELECT * FROM blocks WHERE workspace_id = 'workspace-uuid';
-- Should return WORKSPACE scoped block only
```

**Quality Validation:**
- ✅ **Isolation**: NULL scope blocks stay basket-local
- ✅ **Elevation**: WORKSPACE scope visible across baskets
- ✅ **CONSTANT Constraint**: CONSTANT state blocks MUST have scope (enforced)
- ✅ **Use Case**: Principles, standards, reusable entities span baskets

---

### Test 8: Anchor Refinement (User Override)

**Goal**: Verify users can refine emergent anchors via Building Blocks UI

#### Test Scenario
1. Agent proposes anchor_role = "problem"
2. User reviews and changes to "blocker" (more specific)
3. Verify anchor_status updates to "accepted"

#### Quality Checks

**Expected State Transition:**
```sql
-- Before (agent-proposed)
anchor_role: "problem"
anchor_status: "proposed"
anchor_confidence: 0.75

-- After (user-accepted)
anchor_role: "blocker"  -- User refined
anchor_status: "accepted"
anchor_confidence: NULL  -- Only for proposed
```

**Quality Validation:**
- ✅ **User Agency**: Users can refine emergent vocabulary
- ✅ **Status Tracking**: anchor_status reflects governance outcome
- ✅ **Vocabulary Evolution**: Basket vocabulary becomes more precise over time
- ✅ **No Constraints**: anchor_role accepts any string (no CHECK constraint)

---

## 📊 Quality Metrics Dashboard

### Substrate Quality Metrics
```sql
-- Average confidence by semantic_type
SELECT semantic_type, AVG(confidence_score), COUNT(*)
FROM blocks
WHERE basket_id = ?
GROUP BY semantic_type;

-- Anchor acceptance rate
SELECT
  COUNT(*) FILTER (WHERE anchor_status = 'accepted') * 100.0 / COUNT(*) as acceptance_rate
FROM blocks
WHERE anchor_role IS NOT NULL;

-- Versioning activity
SELECT
  COUNT(DISTINCT parent_block_id) as versioned_concepts,
  COUNT(*) as total_versions
FROM blocks
WHERE parent_block_id IS NOT NULL;
```

### Graph Quality Metrics
```sql
-- Relationship diversity
SELECT relationship_type, COUNT(*), AVG(strength)
FROM substrate_relationships
WHERE basket_id = ?
GROUP BY relationship_type;

-- Entity reference coverage
SELECT
  COUNT(DISTINCT b.id) as entities,
  COUNT(DISTINCT sr.from_id) as referenced_entities
FROM blocks b
LEFT JOIN substrate_relationships sr
  ON sr.to_id = b.id AND sr.relationship_type = 'entity_reference'
WHERE b.semantic_type = 'entity';
```

### Insight Quality Metrics
```sql
-- Freshness tracking
SELECT
  insight_type,
  substrate_hash,
  is_current,
  created_at
FROM reflections_artifact
WHERE basket_id = ?
ORDER BY created_at DESC;

-- Regeneration patterns
SELECT
  insight_type,
  COUNT(*) as version_count,
  MAX(created_at) as latest_version
FROM reflections_artifact
WHERE basket_id = ?
GROUP BY insight_type;
```

---

## ✅ Success Criteria

### Technical Success
- ✅ All pipeline agents execute without errors
- ✅ Database schema matches v3.0 specification
- ✅ No references to context_items in active code paths
- ✅ Helper functions return correct results

### Canon Compliance
- ✅ Emergent anchors work (no fixed constraints)
- ✅ Universal versioning applies to all blocks
- ✅ Semantic types correctly differentiate knowledge/meaning/structural
- ✅ Scope elevation enables cross-basket memory

### Service Intent
- ✅ Substrate extraction provides high-quality, diverse blocks
- ✅ Graph relationships are semantically meaningful
- ✅ Insights provide interpretive intelligence (not just summaries)
- ✅ Documents are coherent narratives (not block lists)

### Quality Standards
- ✅ Average confidence scores ≥ 0.75
- ✅ Anchor acceptance rate ≥ 60%
- ✅ Relationship strength scores ≥ 0.70
- ✅ Insight regeneration triggers on substrate changes
- ✅ Document substrate_references coverage ≥ 80%

---

## 🚀 Next Steps After Testing

1. **If tests pass**: Proceed with frontend v3.0 updates
2. **If quality issues**: Refine agent prompts and heuristics
3. **If technical issues**: Debug pipeline flows and fix errors
4. **Document learnings**: Update canon with real-world patterns

---

**Status**: Testing plan ready for execution
**Priority**: Focus on quality, not just functionality
**Philosophy**: V3.0 is about emergent intelligence, not rigid categorization
