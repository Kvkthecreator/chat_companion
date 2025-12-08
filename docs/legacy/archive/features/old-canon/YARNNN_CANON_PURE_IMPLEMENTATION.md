# YARNNN Canon v2.3 Pure Implementation Guide

**Implementation reference for substrate/artifact separation and canon-compliant architecture**

## 🎯 Core Principle: Strict Layer Separation

The YARNNN architecture has two completely independent layers:

1. **SUBSTRATE LAYER** (Memory) - Governed operations
2. **ARTIFACT LAYER** (Expression) - Independent operations

These layers MUST NOT be mixed in implementation.

## 📊 Layer Boundaries

### SUBSTRATE LAYER (Governed via /api/work)

**Tables:**
- `raw_dumps` - Immutable user input
- `context_blocks` - Structured knowledge blocks  
- `context_items` - Semantic connective tissue
- `timeline_events` - Activity stream

**Operations:**
- ALL mutations flow through governance proposals
- Exception: P0 capture (raw_dumps) is direct by canon
- Work types: P0_CAPTURE, P1_SUBSTRATE, P2_GRAPH, MANUAL_EDIT, PROPOSAL_REVIEW, TIMELINE_RESTORE

**API Pattern:**
```typescript
// Substrate mutations MUST use governance
POST /api/work
{
  work_type: 'P1_SUBSTRATE',
  work_payload: {
    operations: [{ type: 'CreateBlock', content: '...' }],
    basket_id: uuid,
    confidence_score: 0.8
  }
}
```

### ARTIFACT LAYER (Independent REST)

**Tables:**
- `documents` - Narrative compositions
- `reflections` - Computed insights
- `substrate_references` - Document-substrate links
- `document_composition_stats` - Analytics

**Operations:**
- Direct CRUD operations
- No governance required
- Free user editing per canon
- P4 agents write directly to documents

**API Pattern:**
```typescript
// Artifact operations use direct REST
POST /api/documents
{
  title: "Document Title",
  content_raw: "Document content...",
  basket_id: uuid
}

PUT /api/documents/:id
{
  content_raw: "Updated content..."
}
```

## 🚨 Canon Violations to Eliminate

### ❌ WRONG: Documents Through Governance
```typescript
// CANON VIOLATION - Documents are artifacts
POST /api/work
{
  work_type: 'P4_COMPOSE',  // Wrong layer!
  work_payload: {
    operations: [{ type: 'create_document' }]  // Artifacts don't use operations
  }
}
```

### ✅ RIGHT: Documents Direct
```typescript
// CANON COMPLIANT - Direct artifact operation
POST /api/documents
{
  title: "New Document",
  basket_id: uuid
}
```

### ❌ WRONG: Reflections Through Proposals
```typescript
// CANON VIOLATION - Reflections are computed artifacts
POST /api/work
{
  work_type: 'P3_REFLECTION',  // REMOVED from work queue
  work_payload: {
    operations: [{ type: 'create_reflection' }]  // Wrong!
  }
}
```

### ✅ RIGHT: Reflections Direct
```typescript
// CANON COMPLIANT - Direct computation
POST /api/reflections/trigger
{
  basket_id: uuid,
  scope: 'window',
  substrate_window_hours: 168,
  force_refresh: true
}
```

## 🔄 Correct Pipeline Mapping

### P0: Capture (Substrate - Direct)
- Creates `raw_dumps` 
- NEVER creates proposals (canon exception)
- API: `/api/dumps/new` → direct insert

### P1: Evolution (Substrate - Governed)  
- Creates/updates `context_blocks`, `context_items`
- ALWAYS through proposals
- API: `/api/work` → governance → substrate tables

### P2: Connect (Substrate - Governed)
- Creates relationships between substrates
- Through governance for consistency
- API: `/api/work` → governance → relationships

### P3: Reflect (Artifact - Direct)
- Computes `reflections` from substrate
- Direct computation, no governance
- API: `/api/reflections/trigger` → direct computation

### P4: Compose (Artifact - Direct)
- Creates/updates `documents`
- Direct operations on artifact layer
- API: `/api/documents` → direct CRUD

## 📝 Implementation Checklist

### Frontend Compliance
- [ ] Document creation uses `/api/documents`, not `/api/work`
- [ ] Document editing uses direct PUT/PATCH, not governance
- [ ] Substrate mutations use `/api/work` only
- [ ] No client-side governance for artifacts

### Backend Compliance  
- [ ] P4 agents write directly to documents table
- [ ] Reflection computation bypasses governance
- [ ] Substrate operations require governance routing
- [ ] Clear separation in route handlers

### Database Compliance
- [ ] No governance triggers on artifact tables
- [ ] Substrate mutations emit timeline events
- [ ] Artifact operations are simple CRUD
- [ ] RLS policies respect layer boundaries

## 🎯 Benefits of Canon Purity

1. **Performance**: Artifacts don't suffer governance overhead
2. **User Experience**: Document editing is immediate, not queued
3. **Clarity**: Clear boundaries prevent architectural confusion
4. **Scalability**: Independent scaling of memory vs expression layers
5. **Compliance**: Maintains sacred substrate/artifact separation

## 🚧 Migration Strategy

### Phase 1: Documentation (Current)
- [x] Harden canon documentation
- [x] Define clear boundaries
- [x] Identify violations

### Phase 2: Code Audit
- [ ] Audit current P4 work routing
- [ ] Identify governance bypasses needed
- [ ] Map artifact operations to direct REST

### Phase 3: Implementation
- [ ] Move P4 operations to direct endpoints
- [ ] Update frontend to use correct APIs
- [ ] Remove artifact work types from governance
- [ ] Add canon compliance tests

### Phase 4: Cleanup
- [ ] Remove unused governance paths
- [ ] Simplify work orchestration
- [ ] Update deployment and monitoring

## 📚 References

- `YARNNN_CANON.md` - Core principles and architecture
- `YARNNN_GOVERNANCE_CANON.md` - Governance framework details
- `SCHEMA_SNAPSHOT.sql` - Database structure and boundaries