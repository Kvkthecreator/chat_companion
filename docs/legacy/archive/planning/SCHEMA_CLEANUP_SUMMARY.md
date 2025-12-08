# Schema Cleanup Summary — P3/P4 Canon Hardening

**Date**: 2025-10-13
**Status**: Complete
**Migrations**: `20251013_schema_cleanup_legacy.sql`, `20251013_cleanup_legacy_functions.sql`

## Purpose

Remove all legacy P2-era extraction patterns and pre-P3 reflection fields to achieve schema purity for P3/P4 implementation.

## Fields Removed

### reflections_artifact
- ❌ `reflection_target_type` - Replaced by `insight_type` (P3 taxonomy)
- ❌ `reflection_target_id` - Replaced by `derived_from` (provenance)
- ❌ `reflection_target_version` - Replaced by `derived_from` (provenance)
- ❌ Constraint `valid_reflection_target`

**Rationale**: P3 insights now use explicit taxonomy (`insight_canon`, `doc_insight`, etc.) and structured provenance via `derived_from` JSONB field.

### blocks
- ❌ `extraction_method` - Replaced by governance proposals + metadata
- ❌ `provenance_validated` - Replaced by proposal validation workflow
- ❌ `ingredient_version` - Replaced by proposal metadata
- ❌ View `structured_ingredient_blocks` (dependent on extraction_method)
- ❌ View `knowledge_ingredients_view` (dependent on extraction_method)
- ❌ Index `idx_blocks_extraction_method`
- ❌ Index `idx_blocks_provenance_validated`

**Rationale**: Substrate creation now flows through governance pipeline (P0 Capture → P1 Proposals → P2 Acceptance). Extraction metadata lives in proposal payloads.

### context_items
- ❌ `extraction_method`
- ❌ `provenance_validated`
- ❌ `ingredient_version`

**Rationale**: Same as blocks - governed substrate creation.

### extraction_quality_metrics
- ❌ `extraction_method` column

**Rationale**: Metrics can still track quality without coupling to extraction method enum.

## Functions Removed

### Pre-P3 Reflection Functions
- ❌ `fn_reflection_create_from_document(uuid, uuid, text)`
- ❌ `fn_reflection_create_from_substrate(uuid, text)`
- ❌ `fn_persist_reflection(uuid, text, text, text)`
- ❌ `fn_reflection_cache_upsert(uuid, text, text, text, text)`

**Rationale**: These functions used old `reflection_target_type` fields. P3 implementation will introduce new insight generation functions using `insight_type` + `derived_from`.

### Updated Functions
- ✅ `log_extraction_metrics` - Removed `p_extraction_method` parameter (old signature dropped)

## Acceptable Remaining References

### validate_structured_ingredient_metadata
- `metadata_json -> 'provenance_validated'` (JSON path check)
- `metadata_json ? 'extraction_method'` (JSON key existence check)

**Why acceptable**: This function validates JSONB metadata content, not schema columns. It's defensive validation for legacy data that may still exist in metadata blobs. Does not enforce schema-level coupling.

## Verification

```bash
# Check for any schema-level column references (should return empty)
grep -E "^\s+(extraction_method|provenance_validated|reflection_target_type)" docs/SCHEMA_SNAPSHOT.sql

# Result: No matches (only metadata validation logic remains)
```

## Next Steps

Schema is now canon-pure and ready for:

1. ✅ **P3 Backend Implementation**: New insight generation functions using P3 taxonomy
2. ✅ **P4 Backend Implementation**: Document composition using `doc_type` taxonomy
3. ✅ **Freshness Computation**: Context-driven staleness checks (substrate_hash + graph_signature)
4. ✅ **Health Checks**: Endpoint to verify required canons exist per basket

## Rollback Plan

If needed, restore legacy fields:
```sql
-- Rollback: Re-add reflection_target fields
ALTER TABLE reflections_artifact
  ADD COLUMN reflection_target_type varchar(20) DEFAULT 'legacy',
  ADD COLUMN reflection_target_id uuid,
  ADD COLUMN reflection_target_version varchar(64);

-- Rollback: Re-add extraction fields to blocks
ALTER TABLE blocks
  ADD COLUMN extraction_method text DEFAULT 'legacy_governance',
  ADD COLUMN provenance_validated boolean DEFAULT false,
  ADD COLUMN ingredient_version text DEFAULT '1.0';
```

(Not recommended - forward-only canon evolution is preferred)

## Related Documentation

- [docs/YARNNN_CANON.md](./YARNNN_CANON.md) - Updated to v3.1 (P3/P4 taxonomy)
- [docs/YARNNN_GOVERNANCE_CANON.md](./YARNNN_GOVERNANCE_CANON.md) - Artifact operations boundaries
- [docs/YARNNN_P3_P4_IMPLEMENTATION.md](./YARNNN_P3_P4_IMPLEMENTATION.md) - Complete implementation guide
- [supabase/migrations/20251013_p3_p4_taxonomy.sql](../supabase/migrations/20251013_p3_p4_taxonomy.sql) - P3/P4 schema additions

---

**Status**: Schema cleanup complete. Codebase is streamlined and canon-pure for P3/P4 implementation.
