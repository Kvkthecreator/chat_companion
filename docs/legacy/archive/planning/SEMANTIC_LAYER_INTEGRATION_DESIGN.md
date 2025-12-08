# YARNNN v3.1: Semantic Layer Integration Architecture

**Version:** 3.1.0
**Date:** 2025-01-15
**Status:** Design Document - Pre-Implementation

---

## Executive Summary

This document defines how semantic search and relationship inference integrate into YARNNN's core P0-P4 pipeline architecture. This is **not a feature addition**—it is an **architectural upgrade** that fundamentally enhances agent intelligence for context management.

### Core Thesis

**YARNNN is a context management system powered by AI agents.** Semantic search and relationship inference are not "nice-to-have features"—they are **architectural primitives** that enable agents to:

1. **Detect semantic duplicates** (P1 substrate evolution)
2. **Infer causal relationships** (P2 graph intelligence)
3. **Retrieve relevant context** (P3 insight generation)
4. **Compose coherent narratives** (P4 document composition)

Without semantic layer: Agents rely on **exact keyword matching** and **anchor tags**.
With semantic layer: Agents perform **semantic reasoning** and **causal analysis**.

---

## Design Principles

### 1. Embed Substrate, Not Raw Input
- **Only embed ACCEPTED+ blocks** (vetted, governed substrate)
- Raw dumps remain unembedded (transient input, not persistent memory)
- Documents remain unembedded (derived artifacts, not source knowledge)

**Rationale:** We manage refined context, not store everything. Quality over quantity.

### 2. Agent-First, Not User-First
- Primary value: Agent intelligence (merge detection, relationship inference)
- Secondary value: User features (find similar, graph visualization)
- UI follows agent capabilities, not vice versa

**Rationale:** Agents are the differentiator. Users benefit from smarter agents, not search boxes.

### 3. Structure + Semantics, Not RAG
- Governance, versioning, anchors remain primary structure
- Semantic search **augments** structured queries, doesn't replace them
- Relationships capture **causal semantics** that structure alone can't express

**Rationale:** We're not building RAG. Structure is our moat, semantics enhance it.

### 4. Deliberate Integration, Not Bolt-On
- Each pillar (P0-P4) explicitly defines semantic layer usage
- Shared primitives with clear contracts
- Integration points documented in canon

**Rationale:** Architectural upgrades require deliberate design, not ad-hoc features.

---

## Semantic Layer Components

### Component 1: Vector Embeddings

**Purpose:** Enable semantic similarity search for substrate blocks

**Scope:**
- **What gets embedded:** blocks table, ACCEPTED+ state only
- **When embedded:** After governance approval (state transition to ACCEPTED/LOCKED/CONSTANT)
- **How embedded:** OpenAI text-embedding-3-small (title + content)
- **Where stored:** blocks.embedding column (vector(1536))

**Key Functions:**
```sql
-- Hybrid search: structured filters + semantic similarity
search_blocks_semantic(
  basket_id,
  query_embedding,
  semantic_types[],
  anchor_roles[],
  limit
) → blocks with similarity_score

-- Cross-basket search: scope elevation detection
search_blocks_semantic_cross_basket(
  workspace_id,
  query_embedding,
  semantic_types[],
  scopes[],
  limit
) → blocks from other baskets
```

---

### Component 2: Relationship Graph

**Purpose:** Capture causal semantics between substrate blocks

**Scope:**
- **What gets relationships:** blocks (ACCEPTED+ state)
- **Relationship types:** 4 core types (addresses, supports, contradicts, depends_on)
- **When inferred:** After P1 substrate creation, by P2 graph agent
- **How verified:** LLM verification (gpt-4o-mini) for quality
- **Where stored:** substrate_relationships table

**Key Functions:**
```sql
-- Get relationships for block (both directions)
get_block_relationships(
  block_id,
  relationship_types[],
  direction,
  min_state
) → relationships

-- Graph traversal (recursive)
traverse_graph(
  start_block_id,
  relationship_type,
  direction,
  max_depth
) → related blocks with depth
```

---

### Component 3: Shared Primitives (API Layer)

**Purpose:** Provide consistent semantic layer access across all agents

**Location:** `api/src/services/semantic_primitives.py` (NEW)

```python
# Core primitives used by P1-P4 agents

async def semantic_search(
    basket_id: str,
    query_text: str,
    filters: SemanticSearchFilters
) -> List[BlockWithSimilarity]:
    """
    Semantic search within basket.
    Used by: P1 (duplicate detection), P3 (context retrieval), P4 (theme search)
    """

async def semantic_search_cross_basket(
    workspace_id: str,
    query_text: str,
    scopes: List[str]
) -> List[BlockWithSimilarity]:
    """
    Cross-basket semantic search.
    Used by: P1 (scope elevation detection), P3 (pattern discovery)
    """

async def infer_relationships(
    block_id: str,
    basket_id: str
) -> List[RelationshipProposal]:
    """
    Infer causal relationships for block.
    Used by: P2 (graph construction)
    """

async def traverse_relationships(
    start_block_id: str,
    relationship_type: str,
    direction: str,
    max_depth: int
) -> List[BlockWithDepth]:
    """
    Traverse relationship graph.
    Used by: P3 (causal analysis), P4 (narrative coherence)
    """

async def get_semantic_context(
    focal_block_id: str,
    context_window: int = 10
) -> SemanticContext:
    """
    Get semantic context around a block (similar + related).
    Used by: P3 (insight generation), P4 (composition)
    """
```

---

## Pillar Integration: P0-P4 Detailed Design

### P0: Capture (NO CHANGES)

**Role:** Immutable input capture
**Semantic Layer Usage:** NONE

```
User Input → raw_dumps table (unembedded)
```

**Why no changes:**
- Raw dumps are transient input, not persistent memory
- Value extracted by P1, then dumps archived
- No semantic search needed on raw input

**Unchanged:**
- No embedding generation
- No relationship inference
- Pure capture remains pure

---

### P1: Substrate Evolution (CORE UPGRADE)

**Old Role:** Extract facts, propose CREATE operations
**New Role:** Intelligent substrate evolution with semantic duplicate detection

#### Integration Points

**1. Semantic Duplicate Detection (Primary)**

```python
# P1 Substrate Agent: _process_extractions()

for fact in extracted_facts:
    # V3.1: Semantic search for existing substrate
    similar_blocks = await semantic_search(
        basket_id=basket_id,
        query_text=fact.text,
        filters=SemanticSearchFilters(
            semantic_types=[fact.type],
            min_similarity=0.70
        )
    )

    if similar_blocks and similar_blocks[0].similarity_score > 0.85:
        # High similarity = MERGE
        propose_operation({
            'type': 'MergeBlocks',
            'target_id': similar_blocks[0].id,
            'source_content': fact.text,
            'rationale': f'Semantic duplicate (similarity: {similar_blocks[0].similarity_score:.2f})'
        })

    elif similar_blocks and similar_blocks[0].similarity_score > 0.70:
        # Medium similarity = UPDATE/ENRICH
        propose_operation({
            'type': 'UpdateBlock',
            'target_id': similar_blocks[0].id,
            'new_content': fact.text,
            'rationale': f'Semantic enrichment (similarity: {similar_blocks[0].similarity_score:.2f})'
        })

    else:
        # Low similarity = CREATE
        propose_operation({
            'type': 'CreateBlock',
            'content': fact.text,
            'semantic_type': fact.type
        })
```

**2. Scope Elevation Detection (Secondary)**

```python
# P1 Substrate Agent: After creating blocks

if block.semantic_type in ['principle', 'constraint', 'assumption']:
    # Check if this pattern exists in other baskets (elevated scope)
    cross_basket_matches = await semantic_search_cross_basket(
        workspace_id=workspace_id,
        query_text=block.content,
        scopes=['WORKSPACE', 'GLOBAL']
    )

    if len(cross_basket_matches) >= 3:
        # Recurring pattern across baskets = elevate scope
        propose_operation({
            'type': 'ElevateScope',
            'block_id': block.id,
            'new_scope': 'WORKSPACE',
            'rationale': f'Pattern detected in {len(cross_basket_matches)} baskets'
        })
```

#### Success Metrics

- **Duplicate block rate:** <5% (down from ~15% without semantic search)
- **Merge proposal rate:** >25% of operations are MERGE/UPDATE (up from ~5%)
- **False positive rate:** <10% (semantic matches that aren't actually duplicates)

#### Configuration

```python
# P1 Configuration
SEMANTIC_DUPLICATE_THRESHOLDS = {
    'high_confidence_merge': 0.85,  # Auto-propose merge
    'medium_confidence_update': 0.70,  # Propose update/enrich
    'low_confidence_create': 0.70  # Below this = create new
}

SCOPE_ELEVATION_THRESHOLDS = {
    'min_cross_basket_matches': 3,  # Need 3+ baskets with similar content
    'min_similarity': 0.80  # Cross-basket similarity threshold
}
```

---

### P2: Graph Intelligence (CORE UPGRADE)

**Old Role:** Entity co-occurrence detection
**New Role:** Causal relationship inference with semantic understanding

#### Integration Points

**1. Relationship Inference (Primary)**

```python
# P2 Graph Agent: infer_relationships()

async def infer_relationships(self, basket_id: str, new_block_ids: List[str]):
    """
    Infer causal relationships for newly created blocks.
    """

    for block_id in new_block_ids:
        block = await fetch_block(block_id)

        # For each relationship type, find candidates
        for rel_type, config in RELATIONSHIP_ONTOLOGY.items():

            # Check if block can be source (from)
            if block.semantic_type in config['from_types']:
                # Use semantic search to find potential targets
                target_candidates = await semantic_search(
                    basket_id=basket_id,
                    query_text=block.content,
                    filters=SemanticSearchFilters(
                        semantic_types=config['to_types'],
                        min_similarity=0.70
                    )
                )

                for candidate in target_candidates:
                    # Verify relationship with LLM
                    verification = await verify_relationship_with_llm(
                        from_block=block,
                        to_block=candidate,
                        relationship_type=rel_type
                    )

                    if verification.is_valid:
                        # Propose relationship (needs governance approval)
                        propose_relationship({
                            'from_block_id': block.id,
                            'to_block_id': candidate.id,
                            'relationship_type': rel_type,
                            'relationship_strength': verification.strength,
                            'rationale': verification.rationale,
                            'source': 'agent_inferred',
                            'state': 'PROPOSED'
                        })
```

**2. Relationship Ontology (Core Types)**

```python
RELATIONSHIP_ONTOLOGY = {
    'addresses': {
        'from_types': ['action', 'insight', 'objective', 'solution'],
        'to_types': ['problem', 'constraint', 'issue'],
        'description': 'Solution/action addresses problem/constraint',
        'llm_prompt': 'Does the action/solution described in Block A directly address or solve the problem/constraint in Block B?'
    },

    'supports': {
        'from_types': ['fact', 'finding', 'metric', 'evidence'],
        'to_types': ['objective', 'insight', 'hypothesis', 'principle'],
        'description': 'Evidence supports objective/insight',
        'llm_prompt': 'Does the evidence/finding in Block A provide support or validation for the objective/insight in Block B?'
    },

    'contradicts': {
        'from_types': ['fact', 'finding', 'insight'],
        'to_types': ['assumption', 'fact', 'insight', 'principle'],
        'description': 'Conflicts with assumption/fact',
        'llm_prompt': 'Does Block A contradict or conflict with the assumption/fact stated in Block B?'
    },

    'depends_on': {
        'from_types': ['action', 'objective', 'task'],
        'to_types': ['action', 'objective', 'constraint', 'principle'],
        'description': 'Prerequisite dependency',
        'llm_prompt': 'Does Block A depend on Block B being completed/satisfied first? Is Block B a prerequisite for Block A?'
    }
}
```

**3. LLM Verification (Quality Gate)**

```python
async def verify_relationship_with_llm(
    from_block: Block,
    to_block: Block,
    relationship_type: str
) -> RelationshipVerification:
    """
    Use LLM to verify if semantic similarity = actual relationship.

    Why needed: Semantic search finds candidates (70-85% similarity),
    but not all similar blocks have causal relationships.
    LLM acts as quality gate.
    """

    config = RELATIONSHIP_ONTOLOGY[relationship_type]

    prompt = f"""
Analyze if a causal relationship exists between two knowledge blocks.

Relationship Type: {relationship_type}
Description: {config['description']}

Block A (Source):
Title: {from_block.title}
Content: {from_block.content}
Type: {from_block.semantic_type}

Block B (Target):
Title: {to_block.title}
Content: {to_block.content}
Type: {to_block.semantic_type}

Question: {config['llm_prompt']}

Respond in JSON:
{{
  "is_valid": true/false,
  "strength": 0.0-1.0,
  "confidence": 0.0-1.0,
  "rationale": "2-3 sentence explanation"
}}
"""

    response = await openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a knowledge graph analyst. Evaluate causal relationships."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return RelationshipVerification(**json.loads(response.choices[0].message.content))
```

#### Success Metrics

- **Precision:** >80% of agent-inferred relationships are valid (user approval rate)
- **Recall:** >60% of obvious relationships are detected
- **Coverage:** >60% of blocks have at least 1 relationship
- **Type distribution:** All 4 relationship types used (not skewed to one type)

#### Configuration

```python
# P2 Configuration
RELATIONSHIP_INFERENCE_CONFIG = {
    'semantic_similarity_threshold': 0.70,  # Minimum for candidate consideration
    'llm_verification_threshold': 0.75,  # Minimum LLM confidence to propose
    'auto_accept_threshold': 0.90,  # Auto-accept high-confidence relationships
    'max_candidates_per_block': 5,  # Limit semantic search results
    'verify_batch_size': 10  # LLM verification batch size (rate limiting)
}
```

---

### P3: Insights & Reflection (ENHANCED UPGRADE)

**Old Role:** Analyze substrate + graph, generate reflections
**New Role:** Semantic context retrieval + causal reasoning for deeper insights

#### Integration Points

**1. Semantic Context Retrieval (Primary)**

```python
# P3 Reflection Agent: _get_graph_window()

async def _get_graph_window(self, basket_id: str, dump_window: List[RawDump]):
    """
    Get relevant context for reflection.
    V3.1: Uses semantic search, not full basket scan.
    """

    # Build query from recent dumps
    query_text = " ".join([dump.body for dump in dump_window])

    # V3.1: Semantic search for relevant blocks
    relevant_blocks = await semantic_search(
        basket_id=basket_id,
        query_text=query_text,
        filters=SemanticSearchFilters(
            semantic_types=['insight', 'objective', 'constraint', 'principle'],
            min_similarity=0.65  # Lower threshold for broader context
        ),
        limit=20
    )

    # Also get relationships for these blocks (causal context)
    for block in relevant_blocks:
        block.relationships = await get_block_relationships(
            block_id=block.id,
            relationship_types=None,  # All types
            direction='both'
        )

    return relevant_blocks
```

**2. Causal Reasoning (Secondary)**

```python
# P3 Reflection Agent: _analyze_causal_chains()

async def _analyze_causal_chains(self, focal_blocks: List[Block]):
    """
    Traverse relationship graph to understand "why" questions.
    """

    insights = []

    for block in focal_blocks:
        # If this is an action/objective, what problems does it address?
        if block.semantic_type in ['action', 'objective']:
            addressed_problems = await traverse_relationships(
                start_block_id=block.id,
                relationship_type='addresses',
                direction='forward',  # From action TO problem
                max_depth=2
            )

            if addressed_problems:
                insights.append({
                    'type': 'causal_insight',
                    'content': f"{block.title} addresses {len(addressed_problems)} identified problems",
                    'evidence': addressed_problems
                })

        # If this is an insight, what evidence supports it?
        if block.semantic_type in ['insight', 'objective']:
            supporting_evidence = await traverse_relationships(
                start_block_id=block.id,
                relationship_type='supports',
                direction='backward',  # From evidence TO insight
                max_depth=1
            )

            if supporting_evidence:
                insights.append({
                    'type': 'evidence_backed_insight',
                    'content': f"{block.title} is supported by {len(supporting_evidence)} pieces of evidence",
                    'evidence': supporting_evidence
                })

    return insights
```

**3. Pattern Discovery Across Baskets (Tertiary)**

```python
# P3 Reflection Agent: _discover_cross_basket_patterns()

async def _discover_cross_basket_patterns(self, workspace_id: str, focal_theme: str):
    """
    Use semantic search to find similar patterns in other baskets.
    """

    # Search for similar substrate in elevated scope
    similar_patterns = await semantic_search_cross_basket(
        workspace_id=workspace_id,
        query_text=focal_theme,
        scopes=['WORKSPACE', 'GLOBAL']
    )

    if len(similar_patterns) >= 3:
        return {
            'type': 'recurring_pattern',
            'content': f"This theme appears in {len(similar_patterns)} other contexts",
            'evidence': similar_patterns[:5]  # Top 5 examples
        }

    return None
```

#### Success Metrics

- **Context relevance:** >85% of retrieved blocks deemed relevant by LLM eval
- **Insight quality:** Reflections cite causal relationships (not just correlation)
- **Cross-basket discovery:** Recurring patterns identified in >30% of reflections

#### Configuration

```python
# P3 Configuration
REFLECTION_SEMANTIC_CONFIG = {
    'context_retrieval_threshold': 0.65,  # Broader than P1 (more exploratory)
    'context_window_size': 20,  # Max blocks to consider
    'causal_chain_depth': 2,  # Max relationship traversal depth
    'cross_basket_pattern_threshold': 3  # Min baskets for pattern detection
}
```

---

### P4: Narrative Composition (ENHANCED UPGRADE)

**Old Role:** Retrieve blocks by anchor_role, compose documents
**New Role:** Theme-based semantic composition with causal narrative flow

#### Integration Points

**1. Theme-Based Semantic Retrieval (Primary)**

```python
# P4 Composition Agent: _prepare_substrate_with_relationships()

async def _prepare_substrate_with_relationships(
    self,
    basket_id: str,
    document_outline: str,
    target_length: str
):
    """
    Retrieve substrate semantically relevant to document theme.
    V3.1: Not just anchor_role filtering, but semantic theme matching.
    """

    # V3.1: Semantic search for theme-relevant blocks
    theme_relevant_blocks = await semantic_search(
        basket_id=basket_id,
        query_text=document_outline,  # The narrative structure
        filters=SemanticSearchFilters(
            semantic_types=['insight', 'objective', 'principle', 'constraint'],
            min_similarity=0.60  # Broad relevance for narrative
        ),
        limit=50
    )

    # Categorize blocks by semantic type for narrative structure
    categorized = {
        'objectives': [b for b in theme_relevant_blocks if b.semantic_type == 'objective'],
        'insights': [b for b in theme_relevant_blocks if b.semantic_type == 'insight'],
        'principles': [b for b in theme_relevant_blocks if b.semantic_type == 'principle'],
        'constraints': [b for b in theme_relevant_blocks if b.semantic_type == 'constraint']
    }

    return categorized
```

**2. Causal Narrative Flow (Secondary)**

```python
# P4 Composition Agent: _build_narrative_with_causal_flow()

async def _build_narrative_with_causal_flow(self, focal_blocks: List[Block]):
    """
    Use relationship graph to create coherent narrative.
    """

    narrative_sections = []

    # Start with objectives (what we want to achieve)
    for objective in focal_blocks['objectives']:
        section = {
            'type': 'objective',
            'content': objective.content
        }

        # What problems does this objective address?
        addressed_problems = await traverse_relationships(
            start_block_id=objective.id,
            relationship_type='addresses',
            direction='forward',
            max_depth=1
        )

        if addressed_problems:
            section['context'] = f"This objective addresses: {format_problems(addressed_problems)}"

        # What evidence supports this objective?
        supporting_evidence = await traverse_relationships(
            start_block_id=objective.id,
            relationship_type='supports',
            direction='backward',
            max_depth=1
        )

        if supporting_evidence:
            section['evidence'] = format_evidence(supporting_evidence)

        narrative_sections.append(section)

    return narrative_sections
```

**3. Cross-Basket Memory Integration (Tertiary)**

```python
# P4 Composition Agent: _integrate_workspace_context()

async def _integrate_workspace_context(
    self,
    workspace_id: str,
    document_theme: str
):
    """
    Pull elevated substrate from workspace scope for context.
    """

    # Search for workspace-level principles/constraints relevant to theme
    workspace_context = await semantic_search_cross_basket(
        workspace_id=workspace_id,
        query_text=document_theme,
        scopes=['WORKSPACE', 'GLOBAL']
    )

    if workspace_context:
        return {
            'type': 'workspace_context',
            'content': 'Relevant workspace-level context:',
            'blocks': workspace_context[:3]  # Top 3 most relevant
        }

    return None
```

#### Success Metrics

- **Narrative coherence:** Documents cite causal relationships in >70% of sections
- **Theme relevance:** >90% of included blocks semantically relevant to outline
- **Cross-basket integration:** Workspace context included in >40% of documents

#### Configuration

```python
# P4 Configuration
COMPOSITION_SEMANTIC_CONFIG = {
    'theme_retrieval_threshold': 0.60,  # Broad for exploratory composition
    'max_blocks_per_document': 50,  # Budget constraint
    'narrative_chain_depth': 1,  # Keep causal chains simple for readability
    'include_workspace_context': True  # Always pull elevated substrate
}
```

---

## Shared Primitives API Contract

All agents (P1-P4) use these standardized functions for semantic layer access.

### File: `api/src/services/semantic_primitives.py`

```python
"""
Semantic layer primitives used across P0-P4 pipeline.
Standardized API for semantic search and relationship operations.
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class SemanticSearchFilters:
    """Filters for semantic search."""
    semantic_types: Optional[List[str]] = None
    anchor_roles: Optional[List[str]] = None
    min_similarity: float = 0.70
    exclude_block_ids: Optional[List[str]] = None

@dataclass
class BlockWithSimilarity:
    """Block with semantic similarity score."""
    id: str
    title: str
    content: str
    semantic_type: str
    anchor_role: Optional[str]
    state: str
    confidence_score: float
    metadata: dict
    created_at: str
    similarity_score: float  # 0.0-1.0

@dataclass
class BlockWithDepth:
    """Block with graph traversal depth."""
    id: str
    title: str
    content: str
    semantic_type: str
    depth: int  # Distance from start block
    relationship_chain: List[str]  # Path of block IDs

@dataclass
class RelationshipProposal:
    """Proposed relationship for governance."""
    from_block_id: str
    to_block_id: str
    relationship_type: str
    relationship_strength: float
    rationale: str
    source: str  # 'agent_inferred', 'user_created'
    confidence_score: float

class RelationshipType(Enum):
    """Supported relationship types."""
    ADDRESSES = "addresses"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DEPENDS_ON = "depends_on"

# ============================================================================
# Core Primitives
# ============================================================================

async def semantic_search(
    supabase: Client,
    basket_id: str,
    query_text: str,
    filters: SemanticSearchFilters,
    limit: int = 20
) -> List[BlockWithSimilarity]:
    """
    Semantic search within basket.

    Used by:
    - P1: Duplicate detection (high threshold: 0.85)
    - P3: Context retrieval (medium threshold: 0.65)
    - P4: Theme-based composition (broad threshold: 0.60)

    Args:
        supabase: Supabase client
        basket_id: Basket UUID
        query_text: Natural language query
        filters: Search filters (semantic_types, anchor_roles, min_similarity)
        limit: Max results

    Returns:
        List of blocks with similarity scores (sorted by similarity desc)
    """
    # Implementation in api/src/services/embedding_service.py
    pass

async def semantic_search_cross_basket(
    supabase: Client,
    workspace_id: str,
    query_text: str,
    scopes: List[str] = ['WORKSPACE', 'GLOBAL'],
    semantic_types: Optional[List[str]] = None,
    limit: int = 10
) -> List[BlockWithSimilarity]:
    """
    Cross-basket semantic search (elevated scope only).

    Used by:
    - P1: Scope elevation detection
    - P3: Pattern discovery across baskets
    - P4: Workspace context integration

    Args:
        supabase: Supabase client
        workspace_id: Workspace UUID
        query_text: Natural language query
        scopes: Filter by scope levels
        semantic_types: Filter by semantic types
        limit: Max results

    Returns:
        List of blocks from other baskets (elevated scope)
    """
    pass

async def infer_relationships(
    supabase: Client,
    block_id: str,
    basket_id: str
) -> List[RelationshipProposal]:
    """
    Infer causal relationships for block.

    Used by:
    - P2: Automatic relationship inference after P1 substrate creation

    Process:
    1. Determine relationship types block could participate in (based on semantic_type)
    2. Use semantic_search() to find candidates
    3. Verify each candidate with LLM
    4. Return proposed relationships (PROPOSED state, needs governance)

    Args:
        supabase: Supabase client
        block_id: New block UUID
        basket_id: Basket UUID

    Returns:
        List of proposed relationships
    """
    # Implementation in api/src/services/relationship_inference.py
    pass

async def traverse_relationships(
    supabase: Client,
    start_block_id: str,
    relationship_type: RelationshipType,
    direction: str = 'forward',  # 'forward' (from→to), 'backward' (to→from)
    max_depth: int = 2
) -> List[BlockWithDepth]:
    """
    Traverse relationship graph recursively.

    Used by:
    - P3: Causal analysis ("what does this address?", "what supports this?")
    - P4: Narrative flow ("why this objective?", "what depends on this?")

    Args:
        supabase: Supabase client
        start_block_id: Starting block UUID
        relationship_type: Type of relationship to follow
        direction: 'forward' (from→to) or 'backward' (to→from)
        max_depth: Max traversal depth

    Returns:
        List of blocks with depth and path
    """
    pass

async def get_semantic_context(
    supabase: Client,
    focal_block_id: str,
    basket_id: str,
    context_window: int = 10
) -> dict:
    """
    Get rich semantic context around a block.
    Combines semantic similarity + relationships.

    Used by:
    - P3: Insight generation (understand block in context)
    - P4: Composition (gather related material)

    Returns:
        {
            'focal_block': Block,
            'similar_blocks': List[BlockWithSimilarity],
            'relationships': {
                'addresses': List[BlockWithDepth],
                'supports': List[BlockWithDepth],
                'contradicts': List[BlockWithDepth],
                'depends_on': List[BlockWithDepth]
            }
        }
    """
    pass

# ============================================================================
# Helper Functions
# ============================================================================

async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for text.
    Model: text-embedding-3-small (1536 dimensions)
    """
    pass

async def verify_relationship_with_llm(
    from_block: Block,
    to_block: Block,
    relationship_type: RelationshipType
) -> dict:
    """
    Use LLM to verify if relationship is valid.
    Model: gpt-4o-mini

    Returns:
        {
            'is_valid': bool,
            'strength': float (0-1),
            'confidence': float (0-1),
            'rationale': str
        }
    """
    pass
```

---

## Integration Testing Strategy

### Phase 1: Unit Tests (Per Primitive)
- Test semantic_search() with known duplicates
- Test infer_relationships() precision/recall
- Test traverse_relationships() cycle detection

### Phase 2: Integration Tests (Per Pillar)
- P1: Does semantic search reduce duplicate blocks?
- P2: Does relationship inference build coherent graph?
- P3: Does semantic retrieval improve insight quality?
- P4: Does theme-based composition create coherent documents?

### Phase 3: End-to-End Tests (Full Pipeline)
- P0→P1→P2→P3→P4 flow with semantic layer
- Measure: Overall substrate quality, graph density, document coherence
- Compare: With/without semantic layer (A/B test)

---

## Implementation Sequencing

### Week 1: Infrastructure + P1
- Day 1: Schema (embeddings + relationships)
- Day 2: Shared primitives (semantic_search, generate_embedding)
- Day 3-4: P1 integration (duplicate detection)
- Day 5: Test P1 quality (duplicate rate, merge proposal rate)

### Week 2: P2
- Day 6: Relationship ontology + inference logic
- Day 7-8: P2 integration (relationship inference)
- Day 9: Governance integration (relationship proposals)
- Day 10: Test P2 quality (precision, recall, coverage)

### Week 3: P3 + P4
- Day 11-12: P3 integration (semantic retrieval + causal analysis)
- Day 13-14: P4 integration (theme-based composition)
- Day 15: End-to-end testing (full pipeline with semantic layer)

---

## Success Criteria (Overall)

### Quantitative
- **Duplicate block rate:** <5% (down from ~15%)
- **Merge proposal rate:** >25% (up from ~5%)
- **Relationship precision:** >80% (% valid relationships)
- **Block coverage:** >60% (% blocks with relationships)
- **Context relevance:** >85% (% retrieved blocks relevant)

### Qualitative
- Agents make smarter substrate mutation decisions
- Graphs reveal causal structure, not just co-occurrence
- Insights cite evidence via relationship traversal
- Documents have coherent narrative flow

### Cost
- Embedding cost: ~$0.004 per 1000 blocks
- Relationship verification: ~$0.045 per 1000 relationships
- Total: <$0.10 per 1000 blocks (negligible)

---

## Next Steps

1. **Review this design** with stakeholders
2. **Update canon documentation** (YARNNN_CANON.md, YARNNN_SUBSTRATE_CANON_V3.md)
3. **Implement shared primitives** (semantic_primitives.py)
4. **Integrate pillars sequentially** (P1 → P2 → P3 → P4)
5. **Validate with metrics** (compare before/after semantic layer)

---

## Appendix: Why This Design

### Design Decision 1: Why Embed Substrate, Not Raw Dumps?

**Alternative:** Embed everything (RAG approach)
**Chosen:** Embed substrate only (context management approach)

**Rationale:**
- YARNNN manages refined context, not stores everything
- Raw dumps are transient, substrate is persistent memory
- Embedding only vetted substrate ensures quality over quantity
- Cost efficiency: 45% reduction in embedding volume

### Design Decision 2: Why Agent-First, Not User-First?

**Alternative:** Build "Find Similar" UI for users first
**Chosen:** Build agent intelligence first, UI second

**Rationale:**
- Agents are the differentiator (everyone has search boxes)
- Users benefit from smarter agents (fewer duplicates, better insights)
- Agent quality validates semantic layer value before investing in UI

### Design Decision 3: Why 4 Relationship Types, Not More?

**Alternative:** Large ontology (10+ relationship types)
**Chosen:** 4 core types (addresses, supports, contradicts, depends_on)

**Rationale:**
- Start simple, expand if needed
- 4 types cover 80% of causal semantics
- LLM verification is easier with clear types
- Users understand simple ontology better

### Design Decision 4: Why LLM Verification for Relationships?

**Alternative:** Trust semantic similarity alone
**Chosen:** Semantic search finds candidates, LLM verifies

**Rationale:**
- Semantic similarity ≠ causal relationship
- "Login bug" and "Authentication issue" are similar but may not have causal relationship
- LLM acts as quality gate (precision over recall)
- Cost negligible (~$0.045 per 1000 relationships)

---

**End of Design Document**
