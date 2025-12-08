# Reflections Schema Migration - Canon v1.4.0 Compliance

## Issue Summary

The reflections API is failing with `column reflection_cache.computation_timestamp does not exist` due to **schema migration conflicts** between legacy and canonical reflection schemas.

## Root Cause

**Two Competing Schemas:**

### Legacy Schema (Production Current)
```sql
CREATE TABLE reflection_cache (
    id uuid,
    basket_id uuid,
    pattern text,
    tension text, 
    question text,
    computed_at timestamp with time zone,  -- ← Legacy column
    meta_derived_from text,
    meta_refreshable boolean,
    workspace_id uuid
);
```

### Canonical Schema (ReflectionEngine Expected)
```sql
CREATE TABLE reflection_cache (
    id UUID PRIMARY KEY,
    basket_id UUID REFERENCES baskets(id),
    workspace_id UUID REFERENCES workspaces(id), 
    substrate_hash TEXT NOT NULL,
    reflection_text TEXT NOT NULL,
    substrate_window_start TIMESTAMPTZ,
    substrate_window_end TIMESTAMPTZ,
    computation_timestamp TIMESTAMPTZ,  -- ← Canonical column
    last_accessed_at TIMESTAMPTZ,
    meta JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

## Migration Strategy

### 1. Database Migration
- **File**: `supabase/migrations/20250901_fix_reflection_cache_schema.sql`
- **Strategy**: Detect current schema and migrate data safely
- **Data Preservation**: Combine `pattern`, `tension`, `question` into `reflection_text`
- **Timestamp Migration**: `computed_at` → `computation_timestamp`

### 2. Code Updates Required

#### High Priority
- [x] **Migration File**: Created canonical migration
- [x] **Legacy API Route**: Updated to use canonical schema with backward compatibility  
- [ ] **Legacy Contract**: Update `memory.ts` to reference canonical contract
- [ ] **Function Updates**: Fix `fn_persist_reflection` and related functions

#### Medium Priority  
- [ ] **Schema Snapshots**: Update to reflect canonical schema
- [ ] **Test Updates**: Update reflection tests to use canonical schema
- [ ] **Documentation**: Update canon docs to reflect single source of truth

## Backward Compatibility

The legacy `/api/baskets/[id]/reflections/latest` route will:
1. Query using canonical schema (`computation_timestamp`, `reflection_text`)
2. Transform response to legacy format for existing clients
3. Extract pattern/tension/question from `meta` field if available

## Testing Plan

1. **Database Migration**: Apply migration in development
2. **API Testing**: Verify both `/reflections` and `/reflections/latest` work
3. **Data Integrity**: Ensure existing reflection data is preserved
4. **Canon Compliance**: Verify ReflectionEngine operates correctly

## Files Modified

1. `supabase/migrations/20250901_fix_reflection_cache_schema.sql` - Database migration
2. `web/app/api/baskets/[id]/reflections/latest/route.ts` - Legacy API compatibility
3. Next: `shared/contracts/memory.ts` - Contract alignment

## Expected Resolution

After migration:
- ✅ ReflectionEngine will work with canonical `computation_timestamp` column
- ✅ Legacy APIs maintain backward compatibility  
- ✅ Single source of truth for reflection schema
- ✅ Canon v1.4.0 compliance achieved
- ✅ Production `/reflections` API will work without errors