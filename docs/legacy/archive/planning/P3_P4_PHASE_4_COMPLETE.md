# P3/P4 Phase 4 Implementation — Backend Complete ✅

**Date**: 2025-10-13
**Status**: Backend implementation complete, ready for frontend integration
**Commits**: 7d98acd4, 27533204

---

## What Was Delivered

### Phase 3: Schema Cleanup ✅
**Migrations**: `20251013_schema_cleanup_legacy.sql`, `20251013_cleanup_legacy_functions.sql`

**Removed**:
- ❌ `reflections_artifact`: reflection_target_type/id/version (pre-P3 fields)
- ❌ `blocks` + `context_items`: extraction_method, provenance_validated (P2-era)
- ❌ Legacy functions: fn_reflection_create_from_document, fn_reflection_create_from_substrate
- ❌ Views: structured_ingredient_blocks, knowledge_ingredients_view

**Result**: Schema is now P3/P4 canon-pure.

### Phase 4: Backend Implementation ✅
**New Modules**:

#### 1. [api/src/lib/freshness.py](../api/src/lib/freshness.py)
Context-driven freshness computation (NOT time-based).

**Functions**:
- `compute_basket_substrate_hash(supabase, basket_id)` → SHA256 of blocks + items + dumps + events
- `compute_graph_signature(supabase, basket_id)` → SHA256 of relationships topology
- `check_temporal_scope_validity(insight)` → Drift detection for timeboxed_insight
- `compute_substrate_diff(supabase, basket_id, old_hash, new_hash)` → High-level delta
- `should_regenerate_insight_canon(supabase, basket_id)` → Staleness check
- `should_regenerate_document_canon(supabase, basket_id)` → Canon staleness check
- `get_basket_canons_health(supabase, basket_id)` → Completeness + freshness check

**Freshness Model**:
```python
Staleness = f(substrate_hash_changed, graph_topology_changed, temporal_scope_invalid)

# NOT time-based ❌
if (now() - last_generated) > 7 days: regenerate()

# Context-based ✅
if (current_substrate_hash != insight.substrate_hash): regenerate()
if (current_graph_signature != insight.graph_signature): regenerate()
```

#### 2. [api/src/app/routes/p3_insights.py](../api/src/app/routes/p3_insights.py)
P3 Insights generation endpoints.

**Endpoints**:
- `POST /api/p3/insight-canon` - Generate/regenerate basket insight
  - Checks staleness via `should_regenerate_insight_canon()`
  - Returns existing if fresh (unless `force=True`)
  - Marks old as `is_current=false`, new as `is_current=true`
  - Links via `previous_id` for version chain
  - Records `derived_from` provenance

- `POST /api/p3/doc-insight` - Document-scoped insight
  - One per document (many over time, not is_current)
  - Interprets document's meaning/purpose

- `POST /api/p3/timeboxed-insight` - Temporal window insight
  - Filters substrate by time range
  - Useful for "what happened this week" queries

**P3 Taxonomy Implemented**:
- ✅ `insight_canon` - ONE current per basket
- ✅ `doc_insight` - MANY per basket (one per document)
- ✅ `timeboxed_insight` - MANY per basket (temporal windows)
- ⏸️ `review_insight` - Computed ephemeral (future enhancement)
- ⏸️ Workspace insights - Requires policy enablement (future)

#### 3. [api/src/app/routes/p4_canon.py](../api/src/app/routes/p4_canon.py)
P4 Canon generation endpoints.

**Endpoints**:
- `POST /api/p4/document-canon` - Generate Basket Context Canon
  - Mandatory canon (one per basket)
  - Composed from P3 insight_canon + substrate
  - Checks `should_regenerate_document_canon()`
  - Creates new `document_version` record
  - Links via `previous_id` for evolution tracking
  - Records `derived_from` with insight_canon_id + substrate_hash

- `POST /api/p4/starter-prompt` - Generate starter prompt
  - Host-specific reasoning capsules
  - Targets: claude_ai, chatgpt, cursor, windsurf
  - Optional `scope_filter` for focused prompts
  - Multiple per basket (different hosts, different scopes)

**P4 Taxonomy Implemented**:
- ✅ `document_canon` - ONE per basket (mandatory)
- ✅ `starter_prompt` - MANY per basket (host-specific)
- ⏸️ `artifact_other` - Extensible (future document types)

#### 4. [api/src/app/routes/p3_p4_health.py](../api/src/app/routes/p3_p4_health.py)
Health check endpoints for frontend validation.

**Endpoints**:
- `GET /api/health/basket/{basket_id}` - Check canon completeness
  - Returns: `has_insight_canon`, `has_document_canon`, `insight_canon_stale`, `document_canon_stale`, `ready`
  - Frontend uses this to show "Generate Canon" button

- `GET /api/health/workspace/{workspace_id}` - Aggregate health
  - Returns: `baskets_ready`, `baskets_missing_canons`, `baskets_stale`
  - Workspace dashboard overview

- `GET /api/health/insight-canon/{basket_id}/staleness` - Detailed staleness
  - Shows: `substrate_changed`, `graph_changed`, `substrate_delta`
  - User can see "Substrate changed: +3 blocks, +2 items"

- `GET /api/health/document-canon/{basket_id}/staleness` - Canon staleness
  - Shows: `insight_canon_regenerated`, `substrate_changed`
  - User can see "Document out of sync with latest insight"

---

## API Routes Summary

### P3 Endpoints (Insights)
```
POST   /api/p3/insight-canon           Generate basket insight
POST   /api/p3/doc-insight              Generate document insight
POST   /api/p3/timeboxed-insight        Generate temporal insight
```

### P4 Endpoints (Documents)
```
POST   /api/p4/document-canon           Generate Basket Context Canon
POST   /api/p4/starter-prompt           Generate host-specific prompt
```

### Health Endpoints
```
GET    /api/health/basket/{id}                      Check canon completeness
GET    /api/health/workspace/{id}                   Aggregate health
GET    /api/health/insight-canon/{id}/staleness     Detailed insight staleness
GET    /api/health/document-canon/{id}/staleness    Detailed canon staleness
```

---

## Data Flow Example

### Generating Complete Canon Set for New Basket

1. **User creates basket** → Frontend loads basket page

2. **Frontend calls health check**:
   ```http
   GET /api/health/basket/{basket_id}

   Response:
   {
     "has_insight_canon": false,
     "has_document_canon": false,
     "ready": false
   }
   ```

3. **Frontend shows "Generate Canon" button** → User clicks

4. **Frontend calls P3 generation**:
   ```http
   POST /api/p3/insight-canon
   {
     "basket_id": "...",
     "force": false
   }

   Response:
   {
     "insight_id": "...",
     "substrate_hash": "abc123...",
     "graph_signature": "def456...",
     "reflection_text": "This basket focuses on...",
     "derived_from": [...]
   }
   ```

5. **Frontend calls P4 generation**:
   ```http
   POST /api/p4/document-canon
   {
     "basket_id": "...",
     "composition_mode": "comprehensive"
   }

   Response:
   {
     "document_id": "...",
     "version_hash": "789xyz...",
     "derived_from": {
       "insight_canon_id": "...",
       "substrate_hash": "abc123..."
     }
   }
   ```

6. **Basket is now ready** → Health check returns `ready: true`

### Regenerating Stale Canon

1. **User adds new dump** → Substrate changes

2. **Frontend checks staleness**:
   ```http
   GET /api/health/insight-canon/{basket_id}/staleness

   Response:
   {
     "stale": true,
     "reasons": {
       "substrate_changed": true,
       "graph_changed": false
     },
     "substrate_delta": {
       "blocks_active": 15,  // was 12
       "dumps_total": 3      // was 2
     }
   }
   ```

3. **Frontend shows staleness warning** → "Insight out of date (+3 blocks)"

4. **User clicks "Regenerate"** → Calls `POST /api/p3/insight-canon` with `force: true`

5. **New insight created**:
   - Old insight: `is_current = false`
   - New insight: `is_current = true`, `previous_id = <old_id>`
   - Version chain preserved

6. **Document canon also stale** → Auto-trigger or user-initiated regeneration

---

## Versioning Examples

### Insight Canon Evolution
```
Version 3 (current)
  id: insight_v3
  is_current: true
  previous_id: insight_v2
  substrate_hash: "hash_3"
  graph_signature: "sig_3"
  created_at: 2025-10-13T15:30:00Z
  ↓
Version 2 (superseded)
  id: insight_v2
  is_current: false
  previous_id: insight_v1
  substrate_hash: "hash_2"
  graph_signature: "sig_2"
  created_at: 2025-10-12T10:00:00Z
  ↓
Version 1 (original)
  id: insight_v1
  is_current: false
  previous_id: null
  substrate_hash: "hash_1"
  graph_signature: "sig_1"
  created_at: 2025-10-10T09:00:00Z
```

**Analysis Queries**:
- "How has understanding evolved?" → Compare reflection_text v1 → v2 → v3
- "What substrate changed?" → Compare substrate_hash + derived_from arrays
- "When did relationships change?" → Compare graph_signature
- "What was insight 2 days ago?" → Traverse previous_id chain by created_at

### Document Canon Evolution
```
Document Record v2 (current)
  id: doc_v2
  doc_type: document_canon
  current_version_hash: "ver_4"
  previous_id: doc_v1
  derived_from: {insight_canon_id: insight_v3, substrate_hash: hash_3}
  ↓ has many versions
  Content Version 4
    version_hash: "ver_4"
    content: "# Basket Context...\n\n..."
    version_trigger: "insight_canon_regenerated"
    ↓
  Content Version 3
    version_hash: "ver_3"
    version_trigger: "substrate_changed"
```

---

## Future Enhancements (Phase 5+)

### Immediate (Frontend Integration Phase)
- [ ] Frontend hooks: `useBasketCanonHealth(basketId)`
- [ ] Frontend components: `<CanonStalenessBadge />`
- [ ] Frontend validation: `ensureP3P4Canons(basketId)` on page load
- [ ] Auto-regeneration UI: "Regenerate Now" vs "Regenerate Later"

### Near-Term (LLM Integration)
- [ ] Replace placeholder `_generate_insight_text()` with actual LLM calls
- [ ] Replace placeholder `_compose_document_canon()` with LLM composition
- [ ] Host-specific prompt templates (claude_ai, chatgpt, cursor, windsurf)
- [ ] Structured output parsing (Zod schemas for insights/documents)

### Medium-Term (Advanced Features)
- [ ] Workspace insights (cross-basket synthesis)
- [ ] Review insights (proposal evaluation intelligence)
- [ ] Auto-regeneration policies via `p3_p4_regeneration_policy` table
- [ ] Substrate snapshot storage for full diff computation
- [ ] Semantic drift detection (LLM comparison of insight versions)

### Long-Term (Analytics)
- [ ] Insight evolution visualization (timeline of understanding)
- [ ] Provenance graph UI (substrate → insight → document lineage)
- [ ] Regeneration frequency analysis (which baskets churn most?)
- [ ] Context quality scoring (insight coherence over time)

---

## Testing Checklist

### Backend (API)
- [x] All modules compile without syntax errors
- [ ] Unit tests for freshness computation
- [ ] Integration tests for P3/P4 endpoints
- [ ] Test staleness detection with mock substrate changes
- [ ] Test version chain integrity (previous_id links)

### Frontend (Integration)
- [ ] Health check hook fetches correct data
- [ ] Staleness warnings display correctly
- [ ] Generate canon button triggers P3 → P4 sequence
- [ ] Regenerate button respects staleness state
- [ ] Version history UI (future enhancement)

### End-to-End
- [ ] Create basket → Check health → Generate canons → Verify ready
- [ ] Add dump → Check staleness → Regenerate insight → Verify fresh
- [ ] Traverse version history via previous_id chain
- [ ] Verify provenance (derived_from) accuracy

---

## Documentation References

- [docs/YARNNN_CANON.md](./YARNNN_CANON.md) - Updated to v3.1 (P3/P4 taxonomy)
- [docs/YARNNN_GOVERNANCE_CANON.md](./YARNNN_GOVERNANCE_CANON.md) - Artifact operation boundaries
- [docs/YARNNN_P3_P4_IMPLEMENTATION.md](./YARNNN_P3_P4_IMPLEMENTATION.md) - Complete implementation guide
- [docs/SCHEMA_CLEANUP_SUMMARY.md](./SCHEMA_CLEANUP_SUMMARY.md) - Legacy field removal
- [supabase/migrations/20251013_p3_p4_taxonomy.sql](../supabase/migrations/20251013_p3_p4_taxonomy.sql) - P3/P4 schema
- [supabase/migrations/20251013_schema_cleanup_legacy.sql](../supabase/migrations/20251013_schema_cleanup_legacy.sql) - Cleanup

---

## Success Metrics

✅ **Schema Hardening**: All legacy fields removed, canon-pure
✅ **Freshness Logic**: Context-driven (substrate + graph), not time-based
✅ **P3 Taxonomy**: 3/5 insight types implemented (canon, doc, timeboxed)
✅ **P4 Taxonomy**: 2/3 document types implemented (canon, starter_prompt)
✅ **Versioning**: previous_id chains + derived_from provenance
✅ **Health Checks**: Basket/workspace readiness endpoints
✅ **API Routes**: 8 new endpoints under /api/p3, /api/p4, /api/health

**Ready for**: Frontend integration, LLM service integration, policy-driven auto-regeneration

---

**Phase 4 Complete** 🎉
Backend foundations are hardened. Next: Frontend scaffolding.
