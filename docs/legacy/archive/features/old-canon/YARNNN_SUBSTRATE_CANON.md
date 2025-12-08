# YARNNN Substrate Canon v2.0 — Unified Substrate Architecture

**The Single Source of Truth for Substrate vs Artifact Model, Pipeline Operations, and Runtime Behavior**

This document consolidates substrate architecture, pipeline clarification, runtime operations, and artifact separation into a comprehensive canonical reference.

## 🧠 Core Substrate vs Artifact Distinction

YARNNN distinguishes between **Substrates** (the memory itself) and **Artifacts** (expressions derived from memory).

```
SUBSTRATE LAYER          ARTIFACT LAYER
(The Memory)            (The Expressions)
     │                        │
     ├── raw_dumps           ├── documents
     ├── context_blocks      └── reflections
     ├── context_items            
     └── timeline_events          
```

### Substrates (Memory Layer)

**Substrates** are the foundational memory units that capture and structure human thought:

1. **raw_dumps** - Sacred, immutable capture of user input (text, files)
2. **context_blocks** - Structured knowledge ingredients extracted from raw_dumps (goals, constraints, metrics, entities)
3. **context_items** - Semantic connective tissue that links and tags other substrates
4. **timeline_events** - Immutable activity log of all system events

### Artifacts (Expression Layer)

**Artifacts** are computed or composed expressions derived FROM substrates:

1. **documents** - Deliberate narrative compositions that reference substrate + authored prose
2. **reflections** - Computed insights and observations about substrate patterns

## 🏛️ Key Substrate Principles

### 1. Unidirectional Flow
```
Substrate → Artifacts (never the reverse)
```
- Artifacts NEVER become substrate for other artifacts
- Reflections analyze substrate, not other reflections
- Documents compose from substrate, not from other documents

### 2. Substrate Equality
- **No substrate hierarchy** - all substrate types are equal peers
- All substrates have equal status in composition
- No preferential treatment in UI or operations

### 3. Substrate Characteristics
- **Immutable**: Once created, substrate is never modified (only evolved through new versions)
- **Workspace-scoped**: All substrates belong to exactly one workspace
- **Agent-processed**: All substrate creation flows through agent intelligence
- **Event-tracked**: All substrate mutations emit timeline events

### 4. Sacred Write Path
- **P0 Capture**: POST /api/dumps/new (one dump per call)
- **P1 Substrate**: All substrate creation flows through governance proposals
- **No direct substrate writes**: All operations must flow through pipeline discipline

## 🔄 Pipeline Architecture & Runtime

### Core Pipeline Flow (P0 → P1 → P2 → P3 → P4)

| Pipeline | Purpose | Allowed Writes | Disallowed | Emits |
|---|---|---|---|---|
| **P0 Capture** | Immutable ingestion of raw memory | `raw_dumps` | artifacts, relationships | `dump.created` |
| **P1 Substrate CRUD** | Create/update substrate atoms | `context_items`, `context_blocks`, proposals | artifacts, relationships | `block.proposed\|accepted`, `context.tagged` |
| **P2 Graph Fabric** | Materialize substrate relationships | `substrate_relationships` | artifacts | `rel.bulk_upserted` |
| **P3 Artifact Gen** | Generate artifacts from substrate | `reflections_artifact`, `document_versions` | substrate writes | `reflection.computed`, `document.versioned` |
| **P4 Presentation** | Document composition and editing | `documents`, substrate_references | substrate writes | `doc.created\|updated` |

### P0: Capture Phase
**Purpose**: Capture all user inputs as immutable raw_dumps without interpretation

```
User Input Types:
- Text → raw_dump (body_md)
- PDF → raw_dump (file_url + extracted text in body_md)  
- Image → raw_dump (file_url + OCR/description in body_md)
- Multiple inputs in one session → Multiple raw_dumps (linked by batch_id)

Result: Collection of unstructured raw_dumps
```

### P1: Extract & Structure Phase  
**Purpose**: Agent digests raw_dumps and proposes substrate creation

```
Input: Collection of raw_dumps (may be batched)
↓
Agent Processing:
1. Read all related raw_dumps collectively
2. Extract semantic meaning from the whole
3. Create proposal with operations
↓
Output: Proposal containing operations to create substrate
```

### Proposal Structure

A proposal is an **unapplied changeset** (like an uncommitted git commit) containing:

```typescript
interface Proposal {
  id: uuid
  ops: Operation[]  // The substrate changes to apply
  status: 'PROPOSED' | 'APPROVED' | 'REJECTED' | 'EXECUTED'
  origin: 'agent' | 'human'
  provenance: uuid[]  // Source raw_dump IDs
}
```

### Allowed RPCs Matrix

| Pipeline | Allowed RPCs |
|---|---|
| P0 | `fn_ingest_dumps` |
| P1 | context_items direct inserts (service role), `fn_block_create`, `fn_block_revision_create`, `fn_proposal_create`, `fn_proposal_approve`, `fn_proposal_reject` |
| P2 | `fn_relationship_upsert_bulk` |
| P3 | *(none)* `fn_reflection_cache_upsert` *(optional)* |
| P4 | `fn_document_create`, `fn_document_attach_block`, `fn_document_attach_context_item` |

### Memory Plane ↔ REST

| Storage (DB)       | API                                                      |
|--------------------|----------------------------------------------------------|
| timeline_events (append-only) | `GET /api/baskets/{id}/timeline` |
| reflection_cache (optional)   | `GET /api/baskets/{id}/reflections/latest` (may compute on read) |

### ✅ Implementation Achievements

**Canon v2.0 implementation is complete across all layers:**

1. **Contract Layer**: Generic `substrate_references.ts` with peer equality support
2. **Database Layer**: `substrate_references` table with all substrate types
3. **API Layer**: Universal substrate attachment/detachment endpoints
4. **UI Layer**: Multi-substrate composition with type-specific displays
5. **Testing Layer**: Comprehensive coverage of substrate canon compliance

## Substrate Reference Patterns

### Blocks (context_blocks)
- Role: "primary", "supporting", "example"
- Weight: Relevance score
- Snippets: Quoted sections

### Dumps (raw_dumps)
- Role: "source", "reference", "inspiration"
- Weight: Coverage percentage
- Snippets: Relevant excerpts

### Context Items
- Role: "theme", "audience", "goal", "constraint"
- Weight: Importance score
- Metadata: Context type, validation status

### Reflections
- Role: "insight", "pattern", "tension", "question"
- Weight: Confidence score
- Metadata: Computation timestamp, window

### Timeline Events
- Role: "milestone", "reference", "annotation"
- Weight: Relevance to document
- Metadata: Event kind, actor, timestamp

## Implementation Priority ✅ COMPLETED

1. **Contract alignment** ✅ - Foundation for all changes
2. **Database schema** ✅ - Enable substrate storage
3. **API routes** ✅ - Wire up functionality
4. **UI updates** ✅ - User-facing changes
5. **Migration** ✅ - Preserve existing data
6. **Testing** ✅ - Comprehensive test coverage
7. **Sub-page scaffolds** ✅ - Blocks and Graph views

## Notes

- Backend Python already supports rich composition
- Frontend TypeScript diverged to block-only
- Database has partial support (blocks + context_items)
- Need to unify around generic substrate reference model
- Maintain backward compatibility during migration
