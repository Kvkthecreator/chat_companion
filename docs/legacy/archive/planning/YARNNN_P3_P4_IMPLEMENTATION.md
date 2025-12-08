# YARNNN P3/P4 Implementation Guide

**Status**: Active Development
**Version**: 1.0.0
**Last Updated**: 2025-10-13

## Purpose

This document defines the canonical implementation of P3 (Insights) and P4 (Documents) artifacts, including schema, workflows, API contracts, and governance boundaries.

## Core Principles

1. **Immutability**: P3/P4 content never edited in place - evolution via regeneration
2. **Context-Driven Freshness**: Staleness determined by substrate/graph changes, not time
3. **Direct Operations**: P3/P4 regeneration is direct (not governed proposals)
4. **Lineage Tracking**: Every artifact links to previous versions
5. **Provenance**: Every artifact records what it's derived from

---

## Canonical Basket Artifacts

Every basket maintains a guaranteed baseline set of artifacts so it always has a briefing-ready story for humans and agents:

| Layer | Artifact | Cardinality | Purpose |
|-------|----------|-------------|---------|
| P3 (Insights) | `insight_canon` | Exactly one current per basket | Authoritative "what matters now" reflection |
| P4 (Documents) | `document_canon` | Exactly one per basket | Basket Context Canon (comprehensive narrative) |
| P4 (Documents) | `starter_prompt` | At least one per basket (canonical prompt pack) | Ready-to-use context injection for ambient/agent hosts |

The client enforces these invariants (via health checks and auto-regeneration). Additional insights (`doc_insight`, `timeboxed_insight`) and documents (`artifact_other`) build on top of this core set.

---

## P3: Insights Taxonomy

### Insight Types

| Type | Scope | Cardinality | Purpose |
|------|-------|-------------|---------|
| `insight_canon` | Basket or Workspace | Exactly one current per scope | Authoritative "what matters now" |
| `doc_insight` | Document Version | One current per document version | Explains how the version supports the basket |
| `timeboxed_insight` | Temporal window | Multiple per basket | Time-scoped understanding (as_of, for_period) |
| `review_insight` | Proposal | Ephemeral (computed) | Internal governance intelligence |

`doc_insight` artifacts always reference `document_version_id`. Regenerating a document version MUST regenerate its paired doc insight so the Analyze view always reflects the latest narrative and tensions.

### Schema

```sql
-- reflections_artifact table (extended)
{
  id: uuid,
  basket_id: uuid?,  -- NULL for workspace/org/global scope
  workspace_id: uuid NOT NULL,

  -- P3 Taxonomy
  insight_type: 'insight_canon' | 'doc_insight' | 'timeboxed_insight' | 'review_insight',
  scope_level: 'basket' | 'workspace' | 'org' | 'global',
  is_current: boolean,  -- For insight_canon only (one current per scope)

  -- Content & Metadata
  reflection_text: text NOT NULL,
  substrate_hash: text NOT NULL,  -- Hash at generation time
  graph_signature: text,  -- Relationship topology snapshot
  temporal_scope: jsonb,  -- For timeboxed_insight only

  -- Lineage & Provenance
  previous_id: uuid?,  -- Points to prior version
  derived_from: jsonb,  -- Source material (block_ids, reflection_ids, doc_ids, proposal_ids)

  -- Timestamps
  computation_timestamp: timestamptz,
  created_at: timestamptz,
  updated_at: timestamptz
}
```

### Constraints

- **One current insight_canon per basket**: `uq_current_insight_canon_per_basket`
- **One current workspace insight_canon per workspace**: `uq_current_insight_canon_per_workspace`
- **Scope consistency**: Basket insights must have basket_id, workspace insights must not

---

## P4: Documents Taxonomy

### Document Types

| Type | Cardinality | Purpose |
|------|-------------|---------|
| `document_canon` | Exactly one per basket | Basket Context Canon (mandatory health invariant) |
| `starter_prompt` | ≥1 per basket (canonical + optional variants) | Reusable reasoning capsules for external hosts |
| `artifact_other` | Multiple per basket | Future extensibility (reports, briefs, etc.) |

### Schema

```sql
-- documents table (extended)
{
  id: uuid,
  basket_id: uuid,
  workspace_id: uuid NOT NULL,

  -- P4 Taxonomy
  doc_type: 'document_canon' | 'starter_prompt' | 'artifact_other',
  title: text NOT NULL,

  -- Composition (not content - content lives in document_versions)
  current_version_hash: varchar(64),  -- Points to current immutable version
  composition_instructions: jsonb,  -- How to regenerate
  substrate_filter: jsonb,  -- Which substrate to include

  -- Lineage & Provenance
  previous_id: uuid?,  -- Points to prior document (for regeneration)
  derived_from: jsonb,  -- Source material (insight_canon_id, reflection_ids, etc.)

  -- Metadata
  document_type: text,  -- Legacy compatibility
  metadata: jsonb,
  source_raw_dump_id: uuid?,

  -- Timestamps
  created_at: timestamptz,
  updated_at: timestamptz,
  created_by: uuid,
  updated_by: uuid
}
```

### Constraints

- **One document_canon per basket**: `uq_document_canon_per_basket`
- **Immutability**: Content lives in `document_versions` only (not in documents table)

---

## Freshness: Context-Driven, Not Time-Driven

### Philosophy

**WRONG**: Freshness = (current_time - last_generated_time) > threshold

**RIGHT**: Freshness = substrate_hash_changed OR graph_topology_changed OR temporal_scope_invalid

### Implementation

```python
def should_regenerate_insight_canon(basket_id: str) -> dict:
    """
    Context-driven staleness check
    """
    current_canon = get_current_insight_canon(basket_id)
    if not current_canon:
        return {"stale": True, "reason": "missing"}

    # Check 1: Substrate changed?
    current_substrate_hash = compute_basket_substrate_hash(basket_id)
    substrate_changed = current_substrate_hash != current_canon.substrate_hash

    # Check 2: Relationship graph changed?
    current_graph_signature = compute_graph_signature(basket_id)
    graph_changed = current_graph_signature != current_canon.graph_signature

    # Check 3: Temporal drift (for timeboxed_insight only)
    temporal_drift = False
    if current_canon.insight_type == 'timeboxed_insight':
        temporal_drift = check_temporal_scope_validity(current_canon)

    return {
        "stale": substrate_changed or graph_changed or temporal_drift,
        "reasons": {
            "substrate_changed": substrate_changed,
            "graph_changed": graph_changed,
            "temporal_drift": temporal_drift
        },
        "substrate_delta": compute_substrate_diff(current_canon.substrate_hash, current_substrate_hash) if substrate_changed else None
    }
```

### Substrate Hash Computation

```python
def compute_basket_substrate_hash(basket_id: str) -> str:
    """
    Deterministic hash of basket's substrate state
    Includes: ACCEPTED/LOCKED/CONSTANT blocks and raw_dumps (immutable IDs + content hashes)
    """
    blocks = [
        {
            "id": b.id,
            "semantic_type": b.semantic_type,
            "anchor_role": b.anchor_role,
            "content_hash": hash(b.content),
        }
        for b in get_basket_blocks(basket_id, states=("ACCEPTED", "LOCKED", "CONSTANT"))
    ]

    substrate = {
        "blocks": blocks,
        "raw_dumps": [{"id": r.id} for r in get_basket_raw_dumps(basket_id)]  # Immutable capture
    }

    return hashlib.sha256(json.dumps(substrate, sort_keys=True).encode()).hexdigest()
```

### Graph Signature Computation

```python
def compute_graph_signature(basket_id: str) -> str:
    """
    Deterministic hash of relationship topology
    Captures: which substrates are connected, not content
    """
    relationships = get_basket_relationships(basket_id)

    # Sort for determinism
    edges = sorted([
        (r.source_id, r.target_id, r.relationship_type)
        for r in relationships
    ])

    return hashlib.sha256(json.dumps(edges).encode()).hexdigest()
```

---

## API Contracts

### P3 Insights Endpoints

#### `POST /api/baskets/:id/insights/canon/regenerate`
Regenerate basket-level insight (one current per basket)

**Request**: None (uses current basket state)

**Response**:
```json
{
  "insight_id": "uuid",
  "is_current": true,
  "previous_id": "uuid or null",
  "substrate_hash": "sha256...",
  "graph_signature": "sha256...",
  "lineage_chain": ["uuid1", "uuid2", "uuid3"],
  "provenance": {
    "reflection_ids": ["uuid1", "uuid2"],
    "block_ids": ["uuid3"],
    "derived_at": "2025-10-13T12:00:00Z"
  }
}
```

**Freshness Guard**: Returns error if substrate/graph unchanged since last generation

---

#### `GET /api/baskets/:id/insights/canon`
Get current basket insight

**Response**:
```json
{
  "id": "uuid",
  "reflection_text": "Current focus is...",
  "substrate_hash": "sha256...",
  "graph_signature": "sha256...",
  "is_current": true,
  "created_at": "2025-10-13T12:00:00Z",
  "stale": false,
  "stale_reasons": null
}
```

---

#### `GET /api/baskets/:id/insights/lineage`
Get insight evolution history

**Response**:
```json
{
  "current_id": "uuid3",
  "lineage": [
    {"id": "uuid3", "created_at": "2025-10-13T12:00:00Z", "is_current": true},
    {"id": "uuid2", "created_at": "2025-10-12T10:00:00Z", "is_current": false},
    {"id": "uuid1", "created_at": "2025-10-11T08:00:00Z", "is_current": false}
  ]
}
```

---

#### `POST /api/workspaces/:id/insights/synthesize`
Generate workspace-level cross-basket insight (policy-gated)

**Request**:
```json
{
  "force": false  // Override throttle
}
```

**Response**:
```json
{
  "workspace_insight_id": "uuid",
  "basket_canons_used": ["uuid1", "uuid2", "uuid3"],
  "synthesis_summary": "Across your 3 active projects..."
}
```

**Policy Gates**:
- `workspace_insight_enabled` must be true
- Minimum N baskets (default: 3)
- Throttled to once per 24 hours

---

### P4 Documents Endpoints

#### `POST /api/baskets/:id/documents/canon/generate`
Generate/regenerate Basket Context Canon (mandatory)

**Request**: None (uses current substrate + insight_canon)

**Response**:
```json
{
  "canon_id": "uuid",
  "version_hash": "sha256...",
  "composition_signature": "sha256...",
  "derived_from": {
    "insight_canon_id": "uuid",
    "reflection_ids": ["uuid1", "uuid2"],
    "substrate_summary": {"blocks": 12, "context_items": 5}
  }
}
```

---

#### `POST /api/baskets/:id/documents/starter/generate`
Generate Starter Prompt (on-demand, multiple intents supported)

**Request**:
```json
{
  "intent": "strategy",  // or "marketing", "technical", etc.
  "constraints": {
    "max_length": 500,
    "tone": "concise"
  },
  "temporal_scope": {
    "as_of": "2025-10-13",
    "for_period": "Q4 2025"
  }
}
```

**Response**:
```json
{
  "starter_id": "uuid",
  "version_hash": "sha256...",
  "title": "Starter: Strategy",
  "continuity_links": {
    "canon_id": "uuid",
    "insight_id": "uuid"
  }
}
```

---

#### `GET /api/baskets/:id/documents/canon`
Get current Canon

**Response**:
```json
{
  "id": "uuid",
  "title": "Basket Context Canon",
  "current_version_hash": "sha256...",
  "stale": false,
  "version": {
    "version_hash": "sha256...",
    "content": "# Context\n\nThis basket is focused on...",
    "created_at": "2025-10-13T12:00:00Z"
  }
}
```

---

#### `GET /api/baskets/:id/p3p4/health`
Health check for required P3/P4 artifacts

**Response**:
```json
{
  "healthy": true,
  "missing": [],  // ["insight_canon", "document_canon"]
  "stale": ["document_canon"],
  "details": {
    "insight_canon": {
      "exists": true,
      "is_current": true,
      "stale": false
    },
    "document_canon": {
      "exists": true,
      "stale": true,
      "stale_reasons": {
        "substrate_changed": true,
        "graph_changed": false
      }
    }
  }
}
```

---

## Seeding Strategy: Validate-and-Seed Pattern

### Frontend Guard (On Basket Load)

```typescript
// web/lib/baskets/ensureP3P4Canons.ts

export async function ensureBasketCanons(basketId: string) {
  // Check health
  const health = await fetch(`/api/baskets/${basketId}/p3p4/health`).then(r => r.json());

  if (!health.healthy) {
    // Auto-seed missing artifacts
    const promises = [];

    if (health.missing.includes('insight_canon')) {
      promises.push(
        fetch(`/api/baskets/${basketId}/insights/canon/generate`, { method: 'POST' })
      );
    }

    if (health.missing.includes('document_canon')) {
      promises.push(
        fetch(`/api/baskets/${basketId}/documents/canon/generate`, { method: 'POST' })
      );
    }

    await Promise.all(promises);
    return { seeded: true, artifacts: health.missing };
  }

  return { seeded: false, healthy: true };
}
```

### Backend Health Endpoint

```python
# api/src/app/routes/p3_p4_health.py

@router.get("/api/baskets/{basket_id}/p3p4/health")
async def check_p3_p4_health(basket_id: str):
    """
    Health check: Do required P3/P4 artifacts exist?
    Returns what's missing and whether artifacts are stale
    """

    insight_canon = get_current_insight_canon(basket_id)
    document_canon = get_document_canon(basket_id)

    health = {
        "healthy": bool(insight_canon and document_canon),
        "missing": [],
        "stale": [],
        "details": {}
    }

    # Check insight_canon
    if not insight_canon:
        health["missing"].append("insight_canon")
        health["details"]["insight_canon"] = {"exists": False}
    else:
        stale_check = should_regenerate_insight_canon(basket_id)
        health["details"]["insight_canon"] = {
            "exists": True,
            "is_current": True,
            "stale": stale_check["stale"],
            "stale_reasons": stale_check["reasons"] if stale_check["stale"] else None
        }
        if stale_check["stale"]:
            health["stale"].append("insight_canon")

    # Check document_canon
    if not document_canon:
        health["missing"].append("document_canon")
        health["details"]["document_canon"] = {"exists": False}
    else:
        # Document Canon staleness checked via substrate references drift
        drift = check_document_canon_drift(document_canon)
        health["details"]["document_canon"] = {
            "exists": True,
            "stale": drift["stale"],
            "stale_reasons": drift["reasons"] if drift["stale"] else None
        }
        if drift["stale"]:
            health["stale"].append("document_canon")

    return health
```

---

## Governance Boundaries

### P3/P4 Artifacts Are Direct (Not Governed)

**Rationale** (from Governance Canon v4.0):
- P3/P4 are **artifacts**, not substrate
- Regeneration is **deterministic** from substrate state
- No substrate mutations occur during P3/P4 operations
- User controls **when** to regenerate, not **what** content is valid

**What this means:**
- ✅ `POST /api/baskets/:id/insights/canon/regenerate` → Direct operation
- ✅ `POST /api/baskets/:id/documents/canon/generate` → Direct operation
- ❌ No proposals table involvement for P3/P4
- ❌ No governance settings affect P3/P4 regeneration

**Policy table controls:**
- Whether to auto-regenerate on substrate change
- Throttling for workspace-level synthesis
- Feature flags for cross-basket insights

---

## Review Insights: Computed Ephemeral

### Design Decision

**Review insights are NOT stored in `reflections_artifact` table.**

**Rationale:**
- Primary purpose: Help governance decide on proposals
- Computed on-demand (fresh evaluation each time)
- Cached in `proposals.review_insight` column for audit trail
- Does NOT satisfy "one insight per basket" health invariant

### Implementation

```python
@router.get("/api/proposals/{proposal_id}/review-insight")
async def get_proposal_review_insight(proposal_id: str):
    """
    Compute review insight for governance decision
    NOT persisted in reflections_artifact - computed fresh
    Cached in proposals.review_insight for audit trail
    """
    proposal = get_proposal(proposal_id)

    # Check cache first
    if proposal.review_insight:
        return proposal.review_insight

    # Compute fresh
    review = await agent_evaluate_proposal(
        proposal=proposal,
        existing_substrate=get_basket_substrate(proposal.basket_id),
        ontology=get_workspace_ontology(proposal.workspace_id)
    )

    review_insight = {
        "confidence": review.confidence,
        "dupes": review.duplicates,
        "ontology_hits": review.ontology_matches,
        "suggested_merges": review.merge_suggestions,
        "warnings": review.warnings,
        "impact_summary": review.impact_narrative
    }

    # Cache in proposals table
    update_proposal(proposal_id, review_insight=review_insight)

    return review_insight
```

---

## Implementation Phases

### Phase 1: Schema (✅ Complete)
- Migration `20251013_p3_p4_taxonomy.sql` created
- P3 insights taxonomy added
- P4 documents taxonomy added
- Regeneration policy table created
- Constraints and indexes added

### Phase 2: Remove Document Editing (Next)
- Audit backend routes for PATCH/PUT document editing
- Remove direct prose modification endpoints
- Keep only regeneration/composition endpoints
- Update tests to enforce immutability

### Phase 3: P3 Workflows (Next)
- Implement `regenerate_basket_insight_canon()` endpoint
- Implement context-driven freshness checks
- Implement lineage tracking
- Implement workspace synthesis endpoint (policy-gated)

### Phase 4: P4 Workflows (Next)
- Implement `generate_basket_document_canon()` endpoint
- Implement `generate_starter_prompt()` endpoint
- Implement composition signature hashing
- Seed Canon on basket creation

### Phase 5: Health & Seeding (Next)
- Implement `/p3p4/health` endpoint
- Implement frontend `ensureBasketCanons()` guard
- Add health checks to basket loading flows

---

## Open Questions / Future Work

1. **Starter Prompt Intents**: What default intent types? (strategy, marketing, technical, product)
2. **Workspace Synthesis Triggers**: What events should auto-trigger workspace insight synthesis?
3. **Document Canon Auto-Regen**: Should Canon auto-regenerate on substrate change, or only on-demand?
4. **Cross-Basket Graph**: Do we need a unified graph view across all workspace baskets for synthesis?
5. **Temporal Scope Format**: What's the schema for `timeboxed_insight.temporal_scope`?

---

## Version History

- **v1.0.0** (2025-10-13): Initial implementation guide
  - P3/P4 taxonomy defined
  - Context-driven freshness model
  - Validate-and-seed pattern
  - Review insights as computed ephemeral
  - Cross-basket insights schema included (policy-gated)
