# Option B Implementation Plan: Semantic Search + Relationship Inference (2 Weeks)

**Goal:** Add semantic layer to substrate for agent intelligence, not user features
**Focus:** Agent-driven substrate mutations and relationship inference
**Timeline:** 10 working days

---

## Overview: What We're Building

### Week 1: Semantic Search for Agent Intelligence (5 days)
**Purpose:** Enable P1 agent to detect semantic duplicates, make smarter merge/update decisions
**Success Metric:** Fewer duplicate blocks, better merge detection

### Week 2: Relationship Inference (5 days)
**Purpose:** Enable P2 agent to infer causal/support/contradiction relationships
**Success Metric:** Automatic graph structure from substrate evolution

---

## Week 1: Semantic Search (Days 1-5)

### Day 1: Schema & Infrastructure Setup

#### Database Migration

**File:** `supabase/migrations/20250116_add_embedding_support.sql`

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to blocks (nullable, only for ACCEPTED+ blocks)
ALTER TABLE blocks ADD COLUMN embedding vector(1536);

-- Index for vector similarity search (IVFFlat for performance)
-- Note: Need ~1000 rows before building index, use after backfill
-- For now, use brute force (acceptable for <10k blocks)
CREATE INDEX idx_blocks_embedding ON blocks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Hybrid semantic search function
-- Combines structured filters (basket_id, semantic_type, state) with vector similarity
CREATE OR REPLACE FUNCTION search_blocks_semantic(
  p_basket_id uuid,
  p_query_embedding vector(1536),
  p_semantic_types text[] DEFAULT NULL,
  p_anchor_roles text[] DEFAULT NULL,
  p_min_state text DEFAULT 'ACCEPTED',
  p_limit int DEFAULT 20
)
RETURNS TABLE (
  id uuid,
  title text,
  content text,
  semantic_type text,
  anchor_role text,
  state text,
  confidence_score real,
  metadata jsonb,
  created_at timestamptz,
  similarity_score real
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    b.id,
    b.title,
    b.content,
    b.semantic_type,
    b.anchor_role,
    b.state,
    b.confidence_score,
    b.metadata,
    b.created_at,
    (1 - (b.embedding <=> p_query_embedding)) AS similarity_score
  FROM blocks b
  WHERE
    b.basket_id = p_basket_id
    AND b.embedding IS NOT NULL
    AND b.state IN ('ACCEPTED', 'LOCKED', 'CONSTANT')  -- Only vetted substrate
    AND (p_semantic_types IS NULL OR b.semantic_type = ANY(p_semantic_types))
    AND (p_anchor_roles IS NULL OR b.anchor_role = ANY(p_anchor_roles))
  ORDER BY b.embedding <=> p_query_embedding
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Cross-basket semantic search (for scope elevation detection)
CREATE OR REPLACE FUNCTION search_blocks_semantic_cross_basket(
  p_workspace_id uuid,
  p_query_embedding vector(1536),
  p_semantic_types text[] DEFAULT NULL,
  p_scopes text[] DEFAULT ARRAY['WORKSPACE', 'GLOBAL'],
  p_limit int DEFAULT 10
)
RETURNS TABLE (
  id uuid,
  basket_id uuid,
  title text,
  content text,
  semantic_type text,
  scope text,
  similarity_score real
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    b.id,
    b.basket_id,
    b.title,
    b.content,
    b.semantic_type,
    b.scope,
    (1 - (b.embedding <=> p_query_embedding)) AS similarity_score
  FROM blocks b
  WHERE
    b.workspace_id = p_workspace_id
    AND b.embedding IS NOT NULL
    AND b.state IN ('LOCKED', 'CONSTANT')  -- Only elevated substrate
    AND b.scope = ANY(p_scopes)
    AND (p_semantic_types IS NULL OR b.semantic_type = ANY(p_semantic_types))
  ORDER BY b.embedding <=> p_query_embedding
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to check if block needs embedding
CREATE OR REPLACE FUNCTION block_needs_embedding(block_id uuid)
RETURNS boolean AS $$
  SELECT embedding IS NULL
    AND state IN ('ACCEPTED', 'LOCKED', 'CONSTANT')
    AND (title IS NOT NULL OR content IS NOT NULL)
  FROM blocks
  WHERE id = block_id;
$$ LANGUAGE sql STABLE;
```

**Apply migration:**
```bash
# Via Supabase CLI
supabase migration new add_embedding_support
# Copy SQL above into migration file
supabase db push

# OR via Supabase dashboard
# SQL Editor → Paste SQL → Run
```

**Deliverable:** Database ready for embeddings

---

### Day 2: Embedding Generation Service

#### Backend Service

**File:** `api/src/services/embedding_service.py` (NEW)

```python
"""
Embedding generation service for semantic search.
Only embeds ACCEPTED+ substrate blocks.
"""

import openai
from typing import Optional, List
from supabase import Client
import asyncio
import os

# Use text-embedding-3-small (cheap, fast, good quality)
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

openai.api_key = os.getenv("OPENAI_API_KEY")


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using OpenAI API.

    Args:
        text: Content to embed (title + content)

    Returns:
        List of floats (1536 dimensions)
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")

    # Truncate to 8000 tokens (model limit, ~32k chars)
    text = text[:32000]

    try:
        response = await openai.embeddings.acreate(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding generation error: {e}")
        raise


async def embed_block(supabase: Client, block_id: str) -> bool:
    """
    Generate and store embedding for a block.

    Args:
        supabase: Supabase client
        block_id: Block UUID

    Returns:
        True if successful, False if skipped/failed
    """
    # Fetch block
    result = supabase.table('blocks').select('id, title, content, state, embedding').eq('id', block_id).single().execute()

    if not result.data:
        print(f"Block {block_id} not found")
        return False

    block = result.data

    # Skip if already embedded
    if block.get('embedding') is not None:
        print(f"Block {block_id} already has embedding")
        return False

    # Skip if not vetted substrate
    if block.get('state') not in ['ACCEPTED', 'LOCKED', 'CONSTANT']:
        print(f"Block {block_id} state={block.get('state')}, skipping embedding")
        return False

    # Combine title + content for semantic richness
    title = block.get('title') or ''
    content = block.get('content') or ''
    text = f"{title}\n{content}".strip()

    if not text:
        print(f"Block {block_id} has no content, skipping")
        return False

    try:
        # Generate embedding
        embedding = await generate_embedding(text)

        # Store in database
        supabase.table('blocks').update({
            'embedding': embedding
        }).eq('id', block_id).execute()

        print(f"Block {block_id} embedded successfully")
        return True

    except Exception as e:
        print(f"Failed to embed block {block_id}: {e}")
        return False


async def backfill_embeddings(supabase: Client, workspace_id: str, batch_size: int = 50):
    """
    Backfill embeddings for all ACCEPTED+ blocks without embeddings.

    Args:
        supabase: Supabase client
        workspace_id: Workspace to backfill
        batch_size: Number of blocks to process per batch
    """
    # Get all blocks needing embeddings
    result = supabase.table('blocks').select('id').eq('workspace_id', workspace_id).is_('embedding', 'null').in_('state', ['ACCEPTED', 'LOCKED', 'CONSTANT']).execute()

    block_ids = [row['id'] for row in (result.data or [])]

    if not block_ids:
        print(f"No blocks need embedding in workspace {workspace_id}")
        return

    print(f"Backfilling {len(block_ids)} blocks...")

    # Process in batches to avoid rate limits
    for i in range(0, len(block_ids), batch_size):
        batch = block_ids[i:i + batch_size]
        tasks = [embed_block(supabase, block_id) for block_id in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        print(f"Batch {i//batch_size + 1}: {success_count}/{len(batch)} succeeded")

        # Rate limit: 3000 RPM for text-embedding-3-small
        # Sleep between batches if needed
        if i + batch_size < len(block_ids):
            await asyncio.sleep(1)  # Conservative rate limiting

    print(f"Backfill complete: {len(block_ids)} blocks processed")


async def search_semantic(
    supabase: Client,
    basket_id: str,
    query_text: str,
    semantic_types: Optional[List[str]] = None,
    anchor_roles: Optional[List[str]] = None,
    limit: int = 20
) -> List[dict]:
    """
    Semantic search for blocks within a basket.

    Args:
        supabase: Supabase client
        basket_id: Basket UUID
        query_text: Search query (natural language)
        semantic_types: Filter by semantic types (optional)
        anchor_roles: Filter by anchor roles (optional)
        limit: Max results to return

    Returns:
        List of blocks with similarity_score field
    """
    # Generate query embedding
    query_embedding = await generate_embedding(query_text)

    # Call hybrid search function
    result = supabase.rpc('search_blocks_semantic', {
        'p_basket_id': basket_id,
        'p_query_embedding': query_embedding,
        'p_semantic_types': semantic_types,
        'p_anchor_roles': anchor_roles,
        'p_limit': limit
    }).execute()

    return result.data or []


async def search_semantic_cross_basket(
    supabase: Client,
    workspace_id: str,
    query_text: str,
    semantic_types: Optional[List[str]] = None,
    scopes: Optional[List[str]] = None,
    limit: int = 10
) -> List[dict]:
    """
    Cross-basket semantic search for scope elevation detection.

    Args:
        supabase: Supabase client
        workspace_id: Workspace UUID
        query_text: Search query
        semantic_types: Filter by semantic types
        scopes: Filter by scopes (default: ['WORKSPACE', 'GLOBAL'])
        limit: Max results

    Returns:
        List of blocks from other baskets
    """
    query_embedding = await generate_embedding(query_text)

    result = supabase.rpc('search_blocks_semantic_cross_basket', {
        'p_workspace_id': workspace_id,
        'p_query_embedding': query_embedding,
        'p_semantic_types': semantic_types,
        'p_scopes': scopes or ['WORKSPACE', 'GLOBAL'],
        'p_limit': limit
    }).execute()

    return result.data or []
```

**Add to requirements:**

**File:** `api/requirements.txt`
```
openai>=1.0.0  # Add if not already present
```

**Environment variable:**

**File:** `api/.env`
```bash
OPENAI_API_KEY=sk-...  # Your OpenAI API key
```

**Deliverable:** Embedding service ready to use

---

### Day 3: Integrate Embedding into Governance Flow

#### Update Governance Processor

**File:** `api/src/app/agents/pipeline/governance_processor.py`

Add embedding generation AFTER block creation:

```python
# Add import at top
from services.embedding_service import embed_block

# Find the block creation section (around line 672)
# After successful block creation, generate embedding

async def _execute_create_block_operation(self, op: dict, ...):
    """Execute CreateBlock operation."""

    # ... existing block creation code ...

    # After block is created and state is ACCEPTED
    if block_data and block_data.get('id'):
        block_id = block_data['id']

        # V3.1: Generate embedding for semantic search
        try:
            await embed_block(self.supabase, block_id)
            logger.info(f"Generated embedding for block {block_id}")
        except Exception as e:
            # Non-critical: Log but don't fail the operation
            logger.warning(f"Failed to generate embedding for block {block_id}: {e}")

    return OperationResult(created_id=block_id, type='block')
```

**Deliverable:** New blocks automatically get embeddings

---

### Day 4: Integrate Semantic Search into P1 Agent

#### Update Substrate Agent

**File:** `api/src/app/agents/pipeline/improved_substrate_agent.py`

Add semantic duplicate detection:

```python
# Add import at top
from services.embedding_service import search_semantic

# Update _process_extractions method (around line 200)

async def _process_extractions(
    self,
    facts: List[ExtractedFact],
    basket_id: str,
    workspace_id: str
) -> tuple[List[dict], dict]:
    """
    Process extracted facts into substrate ingredients.
    V3.1: Uses semantic search for duplicate detection.
    """

    substrate_ingredients = []

    for fact in facts:
        # V3.1: Semantic duplicate detection
        similar_blocks = await search_semantic(
            supabase=self.supabase,
            basket_id=basket_id,
            query_text=fact.text,
            semantic_types=[fact.type] if fact.type else None,
            limit=3
        )

        # Check similarity threshold
        if similar_blocks and similar_blocks[0]['similarity_score'] > 0.85:
            # High similarity = likely duplicate, propose MERGE
            existing_block = similar_blocks[0]
            logger.info(
                f"Semantic duplicate detected: "
                f"fact='{fact.text[:50]}...' "
                f"similar_to='{existing_block['title']}' "
                f"similarity={existing_block['similarity_score']:.2f}"
            )

            # Add merge metadata for governance
            substrate_ingredients.append({
                'title': fact.text[:100],
                'content': fact.text,
                'semantic_type': fact.type or 'fact',
                'confidence': fact.confidence,
                'anchor_role': self._infer_anchor_from_fact(fact)[0],
                'anchor_confidence': self._infer_anchor_from_fact(fact)[1],
                'metadata': {
                    'extraction_source': 'P1_substrate_agent',
                    'semantic_duplicate_of': existing_block['id'],
                    'similarity_score': existing_block['similarity_score'],
                    'merge_recommended': True
                }
            })

        elif similar_blocks and similar_blocks[0]['similarity_score'] > 0.70:
            # Medium similarity = related but distinct, propose UPDATE/ENRICH
            existing_block = similar_blocks[0]
            logger.info(
                f"Semantic relation detected: "
                f"fact='{fact.text[:50]}...' "
                f"related_to='{existing_block['title']}' "
                f"similarity={existing_block['similarity_score']:.2f}"
            )

            substrate_ingredients.append({
                'title': fact.text[:100],
                'content': fact.text,
                'semantic_type': fact.type or 'fact',
                'confidence': fact.confidence,
                'anchor_role': self._infer_anchor_from_fact(fact)[0],
                'anchor_confidence': self._infer_anchor_from_fact(fact)[1],
                'metadata': {
                    'extraction_source': 'P1_substrate_agent',
                    'semantically_related_to': existing_block['id'],
                    'similarity_score': existing_block['similarity_score'],
                    'update_recommended': True
                }
            })

        else:
            # Low similarity = novel content, propose CREATE
            substrate_ingredients.append({
                'title': fact.text[:100],
                'content': fact.text,
                'semantic_type': fact.type or 'fact',
                'confidence': fact.confidence,
                'anchor_role': self._infer_anchor_from_fact(fact)[0],
                'anchor_confidence': self._infer_anchor_from_fact(fact)[1],
                'metadata': {
                    'extraction_source': 'P1_substrate_agent'
                }
            })

    return substrate_ingredients, {}
```

**Deliverable:** P1 agent uses semantic search for merge detection

---

### Day 5: Test & Validate Semantic Search

#### Test Script

**File:** `api/tests/test_semantic_search.py` (NEW)

```python
"""
Test semantic search for P1 agent duplicate detection.
"""

import asyncio
from services.embedding_service import search_semantic, embed_block, backfill_embeddings
from lib.supabase_client import get_supabase_client

async def test_duplicate_detection():
    """
    Test: Create two semantically similar blocks, verify P1 detects them.
    """
    supabase = get_supabase_client()

    # Create test basket
    basket = supabase.table('baskets').insert({
        'name': 'Semantic Search Test',
        'workspace_id': 'test-workspace-id',
        'user_id': 'test-user-id'
    }).execute()

    basket_id = basket.data[0]['id']

    # Create first block
    block1 = supabase.table('blocks').insert({
        'basket_id': basket_id,
        'workspace_id': 'test-workspace-id',
        'title': 'User authentication problem',
        'content': 'Users are experiencing login failures with OAuth providers',
        'semantic_type': 'problem',
        'state': 'ACCEPTED'
    }).execute()

    block1_id = block1.data[0]['id']

    # Generate embedding
    await embed_block(supabase, block1_id)

    # Test semantic search with similar query
    query = "OAuth login issues affecting users"

    results = await search_semantic(
        supabase=supabase,
        basket_id=basket_id,
        query_text=query,
        limit=5
    )

    print(f"\nQuery: '{query}'")
    print(f"Results: {len(results)}")

    for result in results:
        print(f"  - {result['title']} (similarity: {result['similarity_score']:.2f})")

    # Verify high similarity
    assert len(results) > 0
    assert results[0]['similarity_score'] > 0.75
    print("\n✅ Test passed: Semantic duplicate detection works")

async def test_cross_basket_search():
    """
    Test: Search across baskets for scope elevation detection.
    """
    supabase = get_supabase_client()
    workspace_id = 'test-workspace-id'

    # Create elevated block in basket 1
    basket1 = supabase.table('baskets').insert({
        'name': 'Basket 1',
        'workspace_id': workspace_id,
        'user_id': 'test-user-id'
    }).execute()

    block1 = supabase.table('blocks').insert({
        'basket_id': basket1.data[0]['id'],
        'workspace_id': workspace_id,
        'title': 'Authentication strategy',
        'content': 'We use OAuth 2.0 with JWT tokens for authentication',
        'semantic_type': 'principle',
        'state': 'CONSTANT',
        'scope': 'WORKSPACE'  # Elevated scope
    }).execute()

    await embed_block(supabase, block1.data[0]['id'])

    # Search from basket 2
    query = "How do we handle authentication?"

    results = await search_semantic_cross_basket(
        supabase=supabase,
        workspace_id=workspace_id,
        query_text=query,
        scopes=['WORKSPACE', 'GLOBAL'],
        limit=5
    )

    print(f"\nCross-basket search: '{query}'")
    print(f"Results: {len(results)}")

    for result in results:
        print(f"  - {result['title']} (scope: {result['scope']}, similarity: {result['similarity_score']:.2f})")

    assert len(results) > 0
    print("\n✅ Test passed: Cross-basket semantic search works")

if __name__ == "__main__":
    asyncio.run(test_duplicate_detection())
    asyncio.run(test_cross_basket_search())
```

**Run tests:**
```bash
cd api
python tests/test_semantic_search.py
```

#### Success Metrics (Week 1)

Measure before/after semantic search integration:

1. **Duplicate block rate:** % of blocks that are semantic duplicates (similarity > 0.85)
   - Target: <5% after semantic search

2. **Merge proposal rate:** % of P1 proposals that are MERGE vs CREATE
   - Target: >20% increase in merge proposals

3. **Semantic discovery:** Can agents find relevant blocks without keyword match?
   - Test: Query "login issues" → Should find "OAuth authentication failures"

**Deliverable:** Week 1 complete, semantic search integrated into P1 agent

---

## Week 2: Relationship Inference (Days 6-10)

### Day 6: Relationship Schema & Ontology

#### Database Migration

**File:** `supabase/migrations/20250117_add_relationship_model.sql`

```sql
-- Relationship type enum (start with 4 core types)
CREATE TYPE relationship_type AS ENUM (
  'addresses',      -- Solution/action addresses problem/constraint
  'contradicts',    -- Conflicts with assumption/fact
  'supports',       -- Evidence/finding supports objective/insight
  'depends_on'      -- Prerequisite dependency
);

-- Relationship source enum
CREATE TYPE relationship_source AS ENUM (
  'agent_inferred',   -- P2 graph agent inferred
  'user_created',     -- User manually linked
  'system_derived'    -- System (e.g., versioning via parent_block_id)
);

-- Relationship state enum (governance)
CREATE TYPE relationship_state AS ENUM (
  'PROPOSED',   -- Awaiting approval
  'ACCEPTED',   -- Approved and active
  'REJECTED'    -- Rejected, hidden from graph
);

-- Expand substrate_relationships table
ALTER TABLE substrate_relationships
  ADD COLUMN IF NOT EXISTS relationship_type relationship_type,
  ADD COLUMN IF NOT EXISTS relationship_strength real CHECK (relationship_strength >= 0 AND relationship_strength <= 1),
  ADD COLUMN IF NOT EXISTS source relationship_source DEFAULT 'user_created',
  ADD COLUMN IF NOT EXISTS state relationship_state DEFAULT 'PROPOSED',
  ADD COLUMN IF NOT EXISTS confidence_score real,
  ADD COLUMN IF NOT EXISTS rationale text,
  ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb;

-- Indexes for graph traversal
CREATE INDEX IF NOT EXISTS idx_relationships_from_type ON substrate_relationships(from_block_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_relationships_to_type ON substrate_relationships(to_block_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_relationships_state ON substrate_relationships(state);

-- Function: Get relationships for a block
CREATE OR REPLACE FUNCTION get_block_relationships(
  p_block_id uuid,
  p_relationship_types relationship_type[] DEFAULT NULL,
  p_direction text DEFAULT 'both',  -- 'from', 'to', 'both'
  p_min_state relationship_state DEFAULT 'ACCEPTED'
)
RETURNS TABLE (
  id uuid,
  from_block_id uuid,
  to_block_id uuid,
  relationship_type relationship_type,
  relationship_strength real,
  source relationship_source,
  state relationship_state,
  rationale text,
  created_at timestamptz
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    r.id,
    r.from_block_id,
    r.to_block_id,
    r.relationship_type,
    r.relationship_strength,
    r.source,
    r.state,
    r.rationale,
    r.created_at
  FROM substrate_relationships r
  WHERE
    (p_direction IN ('from', 'both') AND r.from_block_id = p_block_id
     OR p_direction IN ('to', 'both') AND r.to_block_id = p_block_id)
    AND r.state IN ('ACCEPTED', 'PROPOSED')
    AND (p_relationship_types IS NULL OR r.relationship_type = ANY(p_relationship_types))
  ORDER BY r.relationship_strength DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Graph traversal (recursive)
-- Example: "What problems does this solution address?" (follow 'addresses' backward)
CREATE OR REPLACE FUNCTION traverse_graph(
  p_start_block_id uuid,
  p_relationship_type relationship_type,
  p_direction text DEFAULT 'forward',  -- 'forward' (from→to), 'backward' (to→from)
  p_max_depth int DEFAULT 3
)
RETURNS TABLE (
  block_id uuid,
  depth int,
  relationship_chain uuid[]
) AS $$
WITH RECURSIVE graph_traversal AS (
  -- Base case: start block
  SELECT
    p_start_block_id AS block_id,
    0 AS depth,
    ARRAY[p_start_block_id] AS relationship_chain

  UNION ALL

  -- Recursive case: follow relationships
  SELECT
    CASE
      WHEN p_direction = 'forward' THEN r.to_block_id
      ELSE r.from_block_id
    END AS block_id,
    gt.depth + 1,
    gt.relationship_chain || CASE
      WHEN p_direction = 'forward' THEN r.to_block_id
      ELSE r.from_block_id
    END
  FROM graph_traversal gt
  JOIN substrate_relationships r ON (
    (p_direction = 'forward' AND r.from_block_id = gt.block_id)
    OR (p_direction = 'backward' AND r.to_block_id = gt.block_id)
  )
  WHERE
    gt.depth < p_max_depth
    AND r.relationship_type = p_relationship_type
    AND r.state = 'ACCEPTED'
    AND NOT (
      CASE
        WHEN p_direction = 'forward' THEN r.to_block_id
        ELSE r.from_block_id
      END = ANY(gt.relationship_chain)  -- Prevent cycles
    )
)
SELECT * FROM graph_traversal WHERE depth > 0;
$$ LANGUAGE sql STABLE;
```

**Apply migration:**
```bash
supabase migration new add_relationship_model
supabase db push
```

**Deliverable:** Relationship schema ready

---

### Day 7: Relationship Inference Service

#### Backend Service

**File:** `api/src/services/relationship_inference.py` (NEW)

```python
"""
Relationship inference service for P2 graph agent.
Automatically detects semantic relationships between blocks.
"""

from typing import List, Dict, Optional
from supabase import Client
from services.embedding_service import search_semantic
import openai
import json

# Relationship ontology
RELATIONSHIP_TYPES = {
    'addresses': {
        'from_types': ['action', 'insight', 'objective', 'solution'],
        'to_types': ['problem', 'constraint', 'issue'],
        'description': 'Solution/action addresses problem/constraint'
    },
    'supports': {
        'from_types': ['fact', 'finding', 'metric', 'evidence'],
        'to_types': ['objective', 'insight', 'hypothesis'],
        'description': 'Evidence supports objective/insight'
    },
    'contradicts': {
        'from_types': ['fact', 'finding', 'insight'],
        'to_types': ['assumption', 'fact', 'insight'],
        'description': 'Conflicts with assumption/fact'
    },
    'depends_on': {
        'from_types': ['action', 'objective', 'task'],
        'to_types': ['action', 'objective', 'constraint'],
        'description': 'Prerequisite dependency'
    }
}


async def infer_relationships_for_block(
    supabase: Client,
    block_id: str,
    basket_id: str
) -> List[Dict]:
    """
    Infer relationships for a newly created block.

    Args:
        supabase: Supabase client
        block_id: New block UUID
        basket_id: Basket UUID

    Returns:
        List of inferred relationships (dicts with from_block_id, to_block_id, type, etc.)
    """
    # Fetch the new block
    result = supabase.table('blocks').select('*').eq('id', block_id).single().execute()

    if not result.data:
        return []

    new_block = result.data
    semantic_type = new_block.get('semantic_type')

    if not semantic_type:
        return []

    relationships = []

    # For each relationship type, check if new block could be source or target
    for rel_type, config in RELATIONSHIP_TYPES.items():
        # Check if new block can be source (from)
        if semantic_type in config['from_types']:
            target_candidates = await _find_relationship_targets(
                supabase, basket_id, new_block, config['to_types'], rel_type
            )

            for candidate in target_candidates:
                # Verify with LLM
                verified = await _verify_relationship_with_llm(
                    from_block=new_block,
                    to_block=candidate,
                    relationship_type=rel_type,
                    description=config['description']
                )

                if verified['is_valid']:
                    relationships.append({
                        'from_block_id': new_block['id'],
                        'to_block_id': candidate['id'],
                        'relationship_type': rel_type,
                        'relationship_strength': verified['strength'],
                        'rationale': verified['rationale'],
                        'source': 'agent_inferred',
                        'state': 'PROPOSED',  # Needs governance approval
                        'confidence_score': verified['confidence']
                    })

        # Check if new block can be target (to)
        if semantic_type in config['to_types']:
            source_candidates = await _find_relationship_sources(
                supabase, basket_id, new_block, config['from_types'], rel_type
            )

            for candidate in source_candidates:
                verified = await _verify_relationship_with_llm(
                    from_block=candidate,
                    to_block=new_block,
                    relationship_type=rel_type,
                    description=config['description']
                )

                if verified['is_valid']:
                    relationships.append({
                        'from_block_id': candidate['id'],
                        'to_block_id': new_block['id'],
                        'relationship_type': rel_type,
                        'relationship_strength': verified['strength'],
                        'rationale': verified['rationale'],
                        'source': 'agent_inferred',
                        'state': 'PROPOSED',
                        'confidence_score': verified['confidence']
                    })

    return relationships


async def _find_relationship_targets(
    supabase: Client,
    basket_id: str,
    source_block: dict,
    target_types: List[str],
    rel_type: str
) -> List[dict]:
    """
    Find candidate target blocks for relationship using semantic search.
    """
    # Use semantic search to find related blocks of target types
    query_text = f"{source_block.get('title', '')} {source_block.get('content', '')}"

    candidates = await search_semantic(
        supabase=supabase,
        basket_id=basket_id,
        query_text=query_text,
        semantic_types=target_types,
        limit=5
    )

    # Filter by similarity threshold
    return [c for c in candidates if c['similarity_score'] > 0.70]


async def _find_relationship_sources(
    supabase: Client,
    basket_id: str,
    target_block: dict,
    source_types: List[str],
    rel_type: str
) -> List[dict]:
    """
    Find candidate source blocks for relationship using semantic search.
    """
    query_text = f"{target_block.get('title', '')} {target_block.get('content', '')}"

    candidates = await search_semantic(
        supabase=supabase,
        basket_id=basket_id,
        query_text=query_text,
        semantic_types=source_types,
        limit=5
    )

    return [c for c in candidates if c['similarity_score'] > 0.70]


async def _verify_relationship_with_llm(
    from_block: dict,
    to_block: dict,
    relationship_type: str,
    description: str
) -> dict:
    """
    Use LLM to verify if relationship exists and assess strength.

    Returns:
        {
            'is_valid': bool,
            'strength': float (0-1),
            'confidence': float (0-1),
            'rationale': str
        }
    """
    prompt = f"""Analyze if a relationship exists between two knowledge blocks.

Relationship Type: {relationship_type}
Description: {description}

Block A (Source):
Title: {from_block.get('title')}
Content: {from_block.get('content')}
Type: {from_block.get('semantic_type')}

Block B (Target):
Title: {to_block.get('title')}
Content: {to_block.get('content')}
Type: {to_block.get('semantic_type')}

Question: Does Block A {relationship_type} Block B?

Respond in JSON format:
{{
  "is_valid": true/false,
  "strength": 0.0-1.0 (how strong is the relationship),
  "confidence": 0.0-1.0 (how confident are you),
  "rationale": "Brief explanation why this relationship exists or doesn't"
}}
"""

    try:
        response = await openai.chat.completions.acreate(
            model="gpt-4o-mini",  # Fast and cheap for verification
            messages=[
                {"role": "system", "content": "You are a knowledge graph analyst. Evaluate relationships between knowledge blocks."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"LLM verification error: {e}")
        return {
            'is_valid': False,
            'strength': 0.0,
            'confidence': 0.0,
            'rationale': f'Verification failed: {e}'
        }
```

**Deliverable:** Relationship inference service ready

---

### Day 8: Integrate Relationship Inference into P2 Agent

#### Update Graph Agent

**File:** `api/src/app/agents/pipeline/graph_agent.py`

Add relationship inference after substrate creation:

```python
# Add import at top
from services.relationship_inference import infer_relationships_for_block

# Add new method to GraphAgent class

async def infer_relationships(self, basket_id: str, new_block_ids: List[str]):
    """
    Infer relationships for newly created blocks.
    Called after P1 substrate creation completes.
    """
    logger.info(f"P2 relationship inference: basket={basket_id}, blocks={len(new_block_ids)}")

    all_relationships = []

    for block_id in new_block_ids:
        try:
            relationships = await infer_relationships_for_block(
                supabase=self.supabase,
                block_id=block_id,
                basket_id=basket_id
            )

            all_relationships.extend(relationships)

            logger.info(f"Block {block_id}: Inferred {len(relationships)} relationships")

        except Exception as e:
            logger.error(f"Relationship inference failed for block {block_id}: {e}")

    # Store inferred relationships (PROPOSED state)
    if all_relationships:
        result = self.supabase.table('substrate_relationships').insert(all_relationships).execute()

        logger.info(f"Stored {len(all_relationships)} proposed relationships")

        # TODO: Create governance proposal for relationship approval
        # For MVP: Auto-accept high-confidence relationships
        auto_accept_threshold = 0.85

        for rel in all_relationships:
            if rel.get('confidence_score', 0) > auto_accept_threshold:
                self.supabase.table('substrate_relationships').update({
                    'state': 'ACCEPTED'
                }).eq('id', rel['id']).execute()

                logger.info(f"Auto-accepted relationship {rel['id']} (confidence={rel['confidence_score']:.2f})")

    return all_relationships

# Update process() method to call relationship inference after substrate ops
async def process(self, basket_id: str, workspace_id: str) -> dict:
    """
    P2 Graph processing with relationship inference.
    """
    # ... existing graph processing code ...

    # V3.1: Infer relationships for new blocks
    # Get blocks created in last hour (recent substrate evolution)
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    recent_blocks = self.supabase.table('blocks').select('id').eq('basket_id', basket_id).gte('created_at', one_hour_ago).execute()

    if recent_blocks.data:
        new_block_ids = [b['id'] for b in recent_blocks.data]
        await self.infer_relationships(basket_id, new_block_ids)

    # ... rest of existing code ...
```

**Deliverable:** P2 agent infers relationships automatically

---

### Day 9: Relationship Governance Integration

#### Add Relationship Proposals to Governance

**File:** `api/src/services/relationship_governance.py` (NEW)

```python
"""
Governance integration for relationship proposals.
"""

from supabase import Client
from typing import List, Dict

async def create_relationship_proposal(
    supabase: Client,
    basket_id: str,
    workspace_id: str,
    user_id: str,
    relationships: List[Dict]
) -> str:
    """
    Create governance proposal for relationship(s).

    Args:
        supabase: Supabase client
        basket_id: Basket UUID
        workspace_id: Workspace UUID
        user_id: User UUID
        relationships: List of relationship dicts

    Returns:
        Proposal ID
    """
    # Build proposal operations
    operations = []

    for rel in relationships:
        operations.append({
            'type': 'CreateRelationship',
            'data': {
                'from_block_id': rel['from_block_id'],
                'to_block_id': rel['to_block_id'],
                'relationship_type': rel['relationship_type'],
                'relationship_strength': rel.get('relationship_strength', 0.8),
                'rationale': rel.get('rationale', ''),
                'source': rel.get('source', 'user_created')
            }
        })

    # Create proposal
    proposal = supabase.table('proposals').insert({
        'basket_id': basket_id,
        'workspace_id': workspace_id,
        'requested_by': user_id,
        'operations': operations,
        'status': 'pending',
        'blast_radius': 'Local',
        'provenance': ['user_manual_link'],
        'metadata': {
            'proposal_type': 'relationship_creation',
            'relationship_count': len(relationships)
        }
    }).execute()

    return proposal.data[0]['id']


async def approve_relationship_proposal(
    supabase: Client,
    proposal_id: str
) -> List[str]:
    """
    Approve relationship proposal and create relationships.

    Returns:
        List of created relationship IDs
    """
    # Fetch proposal
    proposal = supabase.table('proposals').select('*').eq('id', proposal_id).single().execute()

    if not proposal.data:
        raise ValueError(f"Proposal {proposal_id} not found")

    operations = proposal.data['operations']
    created_ids = []

    for op in operations:
        if op['type'] == 'CreateRelationship':
            data = op['data']

            # Create relationship
            result = supabase.table('substrate_relationships').insert({
                'from_block_id': data['from_block_id'],
                'to_block_id': data['to_block_id'],
                'relationship_type': data['relationship_type'],
                'relationship_strength': data.get('relationship_strength', 0.8),
                'rationale': data.get('rationale', ''),
                'source': data.get('source', 'user_created'),
                'state': 'ACCEPTED',
                'confidence_score': data.get('confidence_score', 0.8)
            }).execute()

            created_ids.append(result.data[0]['id'])

    # Update proposal status
    supabase.table('proposals').update({
        'status': 'approved'
    }).eq('id', proposal_id).execute()

    return created_ids
```

**Deliverable:** Relationship proposals integrated with governance

---

### Day 10: Test & Validate Relationship Inference

#### Test Script

**File:** `api/tests/test_relationship_inference.py` (NEW)

```python
"""
Test relationship inference for P2 graph agent.
"""

import asyncio
from services.relationship_inference import infer_relationships_for_block
from services.embedding_service import embed_block
from lib.supabase_client import get_supabase_client

async def test_addresses_relationship():
    """
    Test: Create problem + solution blocks, verify 'addresses' relationship inferred.
    """
    supabase = get_supabase_client()

    # Create test basket
    basket = supabase.table('baskets').insert({
        'name': 'Relationship Test',
        'workspace_id': 'test-workspace-id',
        'user_id': 'test-user-id'
    }).execute()

    basket_id = basket.data[0]['id']

    # Create problem block
    problem = supabase.table('blocks').insert({
        'basket_id': basket_id,
        'workspace_id': 'test-workspace-id',
        'title': 'Users complain about slow dashboard load times',
        'content': 'Dashboard takes 5+ seconds to load, causing user frustration',
        'semantic_type': 'problem',
        'state': 'ACCEPTED'
    }).execute()

    problem_id = problem.data[0]['id']
    await embed_block(supabase, problem_id)

    # Create solution block
    solution = supabase.table('blocks').insert({
        'basket_id': basket_id,
        'workspace_id': 'test-workspace-id',
        'title': 'Implement dashboard caching',
        'content': 'Add Redis caching layer to reduce database queries and improve load time',
        'semantic_type': 'action',
        'state': 'ACCEPTED'
    }).execute()

    solution_id = solution.data[0]['id']
    await embed_block(supabase, solution_id)

    # Infer relationships
    relationships = await infer_relationships_for_block(
        supabase=supabase,
        block_id=solution_id,
        basket_id=basket_id
    )

    print(f"\nInferred {len(relationships)} relationships")

    for rel in relationships:
        print(f"  - {rel['relationship_type']}: {rel['from_block_id'][:8]}... → {rel['to_block_id'][:8]}...")
        print(f"    Strength: {rel['relationship_strength']:.2f}")
        print(f"    Rationale: {rel['rationale']}")

    # Verify 'addresses' relationship detected
    addresses_rels = [r for r in relationships if r['relationship_type'] == 'addresses']
    assert len(addresses_rels) > 0
    assert addresses_rels[0]['to_block_id'] == problem_id

    print("\n✅ Test passed: 'addresses' relationship inferred correctly")


async def test_supports_relationship():
    """
    Test: Create objective + evidence blocks, verify 'supports' relationship.
    """
    supabase = get_supabase_client()

    basket = supabase.table('baskets').insert({
        'name': 'Supports Test',
        'workspace_id': 'test-workspace-id',
        'user_id': 'test-user-id'
    }).execute()

    basket_id = basket.data[0]['id']

    # Create objective
    objective = supabase.table('blocks').insert({
        'basket_id': basket_id,
        'workspace_id': 'test-workspace-id',
        'title': 'Increase user retention by 20%',
        'content': 'Goal: Improve retention rate from 40% to 60% by Q2',
        'semantic_type': 'objective',
        'state': 'ACCEPTED'
    }).execute()

    objective_id = objective.data[0]['id']
    await embed_block(supabase, objective_id)

    # Create supporting evidence
    evidence = supabase.table('blocks').insert({
        'basket_id': basket_id,
        'workspace_id': 'test-workspace-id',
        'title': 'User surveys show engagement is key to retention',
        'content': 'Survey data: 85% of retained users engage daily vs 20% of churned users',
        'semantic_type': 'finding',
        'state': 'ACCEPTED'
    }).execute()

    evidence_id = evidence.data[0]['id']
    await embed_block(supabase, evidence_id)

    # Infer relationships
    relationships = await infer_relationships_for_block(
        supabase=supabase,
        block_id=evidence_id,
        basket_id=basket_id
    )

    print(f"\nInferred {len(relationships)} relationships for evidence block")

    supports_rels = [r for r in relationships if r['relationship_type'] == 'supports']

    if supports_rels:
        print(f"  - 'supports' relationship found: strength={supports_rels[0]['relationship_strength']:.2f}")
        print(f"    Rationale: {supports_rels[0]['rationale']}")
        print("\n✅ Test passed: 'supports' relationship inferred")
    else:
        print("\n⚠️  No 'supports' relationship found (might need LLM adjustment)")


if __name__ == "__main__":
    asyncio.run(test_addresses_relationship())
    asyncio.run(test_supports_relationship())
```

**Run tests:**
```bash
cd api
python tests/test_relationship_inference.py
```

#### Success Metrics (Week 2)

Measure relationship inference quality:

1. **Precision:** % of agent-inferred relationships that are semantically correct
   - Target: >80% precision (4 out of 5 inferred relationships are valid)

2. **Coverage:** % of blocks that have at least 1 relationship
   - Target: >60% coverage (most blocks are connected)

3. **Type distribution:** Are all 4 relationship types being inferred?
   - addresses, supports, contradicts, depends_on

4. **Manual override rate:** How often do users reject agent-inferred relationships?
   - Target: <20% rejection rate

**Deliverable:** Week 2 complete, relationship inference working

---

## Post-Implementation: Minimal UI Updates (Optional - Day 11)

If you want basic UI to visualize relationships:

### Frontend: Relationship Sidebar

**File:** `web/components/substrate/BlockRelationships.tsx` (NEW)

```typescript
"use client";

import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ArrowRight, Link as LinkIcon } from 'lucide-react';
import { fetchWithToken } from '@/lib/fetchWithToken';

interface Relationship {
  id: string;
  from_block_id: string;
  to_block_id: string;
  relationship_type: 'addresses' | 'supports' | 'contradicts' | 'depends_on';
  relationship_strength: number;
  rationale: string;
  state: string;
}

interface Block {
  id: string;
  title: string;
  semantic_type: string;
}

export function BlockRelationships({ blockId }: { blockId: string }) {
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [relatedBlocks, setRelatedBlocks] = useState<Record<string, Block>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRelationships();
  }, [blockId]);

  async function loadRelationships() {
    try {
      const response = await fetchWithToken(`/api/blocks/${blockId}/relationships`);
      const data = await response.json();

      setRelationships(data.relationships || []);
      setRelatedBlocks(data.blocks || {});
    } catch (error) {
      console.error('Failed to load relationships:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>Loading relationships...</div>;
  if (relationships.length === 0) return null;

  const relationshipTypeLabels = {
    addresses: { label: 'Addresses', color: 'bg-green-100 text-green-800' },
    supports: { label: 'Supports', color: 'bg-blue-100 text-blue-800' },
    contradicts: { label: 'Contradicts', color: 'bg-red-100 text-red-800' },
    depends_on: { label: 'Depends On', color: 'bg-amber-100 text-amber-800' }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <LinkIcon className="h-4 w-4" />
          Relationships ({relationships.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {relationships.map((rel) => {
          const isOutgoing = rel.from_block_id === blockId;
          const relatedBlockId = isOutgoing ? rel.to_block_id : rel.from_block_id;
          const relatedBlock = relatedBlocks[relatedBlockId];
          const typeConfig = relationshipTypeLabels[rel.relationship_type];

          return (
            <div key={rel.id} className="border rounded-lg p-3 space-y-2">
              <div className="flex items-center gap-2">
                <Badge className={typeConfig.color}>
                  {typeConfig.label}
                </Badge>
                {rel.state === 'PROPOSED' && (
                  <Badge variant="outline" className="text-xs">
                    Proposed
                  </Badge>
                )}
                <span className="text-xs text-slate-500">
                  {Math.round(rel.relationship_strength * 100)}% confidence
                </span>
              </div>

              <div className="flex items-center gap-2 text-sm">
                {!isOutgoing && <ArrowRight className="h-3 w-3 text-slate-400" />}
                <span className="font-medium">
                  {relatedBlock?.title || 'Unknown block'}
                </span>
                {isOutgoing && <ArrowRight className="h-3 w-3 text-slate-400" />}
              </div>

              {rel.rationale && (
                <p className="text-xs text-slate-600 italic">
                  {rel.rationale}
                </p>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
```

**API Endpoint:** `web/app/api/blocks/[id]/relationships/route.ts` (NEW)

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: blockId } = await params;
  const supabase = createServerSupabaseClient();

  // Get relationships
  const { data: relationships } = await supabase
    .rpc('get_block_relationships', {
      p_block_id: blockId,
      p_direction: 'both'
    })
    .execute();

  // Get related blocks
  const relatedBlockIds = new Set<string>();
  relationships?.forEach((rel: any) => {
    relatedBlockIds.add(rel.from_block_id);
    relatedBlockIds.add(rel.to_block_id);
  });

  const { data: blocks } = await supabase
    .table('blocks')
    .select('id, title, semantic_type')
    .in('id', Array.from(relatedBlockIds))
    .execute();

  const blocksMap = Object.fromEntries(
    (blocks || []).map(b => [b.id, b])
  );

  return NextResponse.json({
    relationships: relationships || [],
    blocks: blocksMap
  });
}
```

**Usage:** Add to SubstrateDetailModal or block detail pages

---

## Success Criteria & Validation

### Week 1 Success (Semantic Search)

**Quantitative:**
- Duplicate block rate decreases by >30%
- Merge proposal rate increases by >20%
- Semantic search recall >80% (finds relevant blocks)

**Qualitative:**
- P1 agent finds duplicates that keyword matching misses
- Cross-basket search discovers elevated substrate
- Agents retrieve relevant context without loading entire basket

### Week 2 Success (Relationship Inference)

**Quantitative:**
- Relationship inference precision >80%
- Block coverage (% with relationships) >60%
- Auto-accept rate <20% rejection

**Qualitative:**
- Relationships make semantic sense
- Graph enables "why" questions
- Users engage with relationship proposals

---

## Cost Estimate

### OpenAI API Costs

**Embedding generation:**
- Model: text-embedding-3-small
- Cost: $0.02 per 1M tokens
- Block size: ~200 tokens avg
- 1000 blocks = 200k tokens = $0.004

**Relationship verification:**
- Model: gpt-4o-mini
- Cost: $0.15 per 1M input tokens
- Verification prompt: ~300 tokens
- 1000 relationships = 300k tokens = $0.045

**Total for 1000 blocks + relationships: ~$0.05**

At scale (10k users, 100 blocks each):
- 1M blocks = $40/month (embeddings + relationships)

**Negligible cost, high value.**

---

## Rollout Plan

### Phase 1: Enable Features (Day 1-10)
- Deploy schema migrations
- Deploy backend services
- Backfill embeddings for existing blocks
- Test with internal baskets

### Phase 2: Validate (Day 11-12)
- Monitor P1 merge detection quality
- Monitor P2 relationship inference precision
- Collect feedback from test users

### Phase 3: Iterate (Week 3+)
- Tune similarity thresholds
- Expand relationship ontology if needed
- Add UI features based on validation

---

## Questions to Answer Post-Implementation

1. **Do users engage with proposed relationships?**
   - If yes → Expand to more relationship types
   - If no → Simplify, auto-accept more

2. **Does semantic search improve agent quality?**
   - Measure: Duplicate block rate, merge success rate
   - If yes → Integrate into P3, P4 agents
   - If no → Tune embedding model or thresholds

3. **Should we visualize graph structure?**
   - If relationships are used → Build graph visualization
   - If not → Keep minimal UI

---

## Next Steps After Week 2

If validation is positive:

1. **Expand relationship ontology** (adds, derives_from, conflicts_with, etc.)
2. **Graph visualization UI** (D3.js or React Flow)
3. **Integrate into P3/P4** (use relationships for insight generation, document composition)
4. **Cross-basket relationship inference** (detect patterns across workspaces)
5. **User-facing "Find Similar"** (if demand exists)

If validation is negative:

1. **Defer relationship inference** (keep schema, disable agent auto-inference)
2. **Keep semantic search only** (proven value for merge detection)
3. **Focus on core product** (governance, UI, user adoption)

---

## You're Ready to Start

**Deliverables by end of Week 2:**
- ✅ Semantic search integrated into P1 agent
- ✅ Relationship inference integrated into P2 agent
- ✅ Governance integration for relationships
- ✅ Tests validating both features
- ✅ Metrics to assess value

**Proceed with Day 1: Schema & Infrastructure Setup**
