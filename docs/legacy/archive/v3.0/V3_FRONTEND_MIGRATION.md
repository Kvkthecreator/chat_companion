# V3.0 Frontend Migration Guide

**Status:** 🔴 CRITICAL - Frontend currently BROKEN with v3.0 backend

## Executive Summary

The v3.0 backend refactoring merged `context_items` into unified `blocks` table. Frontend still expects dual substrate model and will fail if deployed against v3.0 backend.

## Breaking Changes Identified

### 1. Context Items API Routes (HIGH PRIORITY)

**File:** `web/app/api/baskets/[id]/context-items/route.ts`
- **Issue:** Queries dropped `context_items` table
- **Impact:** 500 errors on GET /api/baskets/{id}/context-items
- **Fix Required:** Remove route entirely OR migrate to query blocks with `semantic_type IN ('entity', 'intent', 'objective', ...)`

**File:** `web/lib/contextItems.ts`
- **Issue:** Client calls `/api/context_items` endpoint
- **Impact:** All createContextItem(), updateContextItem(), deleteContextItem() calls fail
- **Fix Required:** Remove file, migrate callers to blocks API

**File:** `web/lib/server/contextItems.ts`
- **Issue:** Server-side context_items helpers
- **Impact:** SSR pages using these helpers will fail
- **Fix Required:** Remove file, migrate to blocks helpers

---

### 2. Building Blocks Page (HIGH PRIORITY)

**File:** `web/app/api/baskets/[id]/building-blocks/route.ts`
- **Line 114-120:** Queries `context_items` table
- **Line 161-168:** Returns `context_items` array in response
- **Impact:** Building Blocks page (/baskets/[id]/building-blocks) shows incomplete data
- **Fix Required:**
  ```typescript
  // REMOVE context_items query entirely
  // FILTER blocks to show meaning types separately if needed:
  const meaningBlocks = blocks.filter(b =>
    ['intent', 'objective', 'rationale', 'principle', 'assumption', 'context', 'constraint'].includes(b.semantic_type)
  );
  ```

**File:** `web/app/baskets/[id]/building-blocks/BuildingBlocksClientV2.tsx`
- **Line 57-64:** TypeScript interface expects `context_items`
- **Line 68:** `BuildingBlocksResponse` type includes `context_items` and `total_context_items`
- **Impact:** Component rendering broken
- **Fix Required:**
  ```typescript
  // REMOVE ContextItemWithMetrics interface
  // UPDATE BuildingBlocksResponse to remove context_items field
  // UPDATE stats to remove total_context_items
  // FILTER blocks by semantic_type categories instead
  ```

---

### 3. Governance Operations (CRITICAL)

**File:** `web/lib/governance/canonicalSubstrateOps.ts`
- **Line 70-100:** `createContextItemCanonical()` inserts into `context_items` table
- **Impact:** All governance proposals with CreateContextItem operations fail during approval
- **Fix Required:**
  ```typescript
  // MIGRATE createContextItemCanonical to create blocks with semantic_type
  export async function createContextItemCanonical(
    supabase: AnySupabase,
    op: any,
    basketId: string,
    workspaceId: string
  ): Promise<OperationResult> {
    // Map context item "kind" to semantic_type
    const semanticTypeMap: Record<string, string> = {
      'concept': 'entity',
      'entity': 'entity',
      'intent': 'intent',
      'objective': 'objective',
      'rationale': 'rationale',
      'principle': 'principle',
      'constraint': 'constraint',
    };

    const semanticType = semanticTypeMap[op.kind] || 'entity';

    // Create block with v3.0 fields
    const { data, error } = await supabase.rpc('fn_block_create', {
      p_basket_id: basketId,
      p_workspace_id: workspaceId,
      p_title: op.label || op.title,
      p_body_md: op.content || '',
    });

    // Update with v3.0 semantic fields
    await supabase.from('blocks').update({
      semantic_type: semanticType,
      anchor_role: op.anchor_role || null,
      anchor_status: op.anchor_status || 'proposed',
      anchor_confidence: op.anchor_confidence || op.confidence || 0.7,
      metadata: op.metadata,
      state: 'ACCEPTED',
    }).eq('id', blockId);

    return { created_id: blockId, type: 'block' };
  }
  ```

**File:** `web/lib/governance/changeDescriptor.ts`
- **Impact:** Operation type detection for CreateContextItem
- **Fix Required:** Update to recognize semantic_type-based block creation

**File:** `web/lib/anchors/mutationHelpers.ts`
- **Impact:** Anchor tagging creates context_items
- **Fix Required:** Update to create blocks with anchor_role field

---

### 4. Database Type Definitions (MEDIUM PRIORITY)

**File:** `web/lib/dbTypes.ts`
- **Line 6-19:** `blocks` table Row type missing v3.0 fields
- **Impact:** TypeScript errors, missing autocomplete for v3.0 fields
- **Fix Required:**
  ```typescript
  blocks: {
    Row: {
      id: string;
      basket_id: string | null;
      workspace_id: string | null;
      parent_block_id: string | null;  // V3.0: Universal versioning
      semantic_type: string;
      content: string | null;
      title: string | null;
      version: number;
      state: string;
      scope: string | null;  // V3.0: WORKSPACE | ORG | GLOBAL
      anchor_role: string | null;  // V3.0: Emergent anchor
      anchor_status: string | null;  // V3.0: proposed | accepted | locked
      anchor_confidence: number | null;  // V3.0: 0.0-1.0
      confidence_score: number | null;
      canonical_value: string | null;
      origin_ref: string | null;
      raw_dump_id: string | null;
      metadata: Json | null;
      created_at: string;
      updated_at: string | null;
      last_validated_at: string | null;
    };
  };
  ```

---

### 5. Shared Contracts (MEDIUM PRIORITY)

**File:** `web/shared/contracts/context.ts`
- **Impact:** Contract definitions for CreateContextItem operations
- **Fix Required:** Mark as deprecated, add v3.0 block creation contracts

**File:** `web/shared/contracts/blocks.ts`
- **Impact:** Block types missing v3.0 fields
- **Fix Required:** Add v3.0 fields to Block type

---

### 6. Test Files (LOW PRIORITY - Fix after core)

**Files:**
- `web/__tests__/governance/changeDescriptor.test.ts`
- `web/__tests__/governance/decisionGateway.test.ts`
- `web/__tests__/governance/policyDecider.test.ts`
- `web/tests/e2e/contract_validation.spec.ts`

**Impact:** Test failures
**Fix Required:** Update test fixtures to use blocks instead of context_items

---

## Migration Sequence (Recommended)

### Phase 1: Critical Path (Deploy Blocker)
1. ✅ **Update database types** ([web/lib/dbTypes.ts](web/lib/dbTypes.ts)) - Add v3.0 fields
2. ✅ **Migrate governance operations** ([web/lib/governance/canonicalSubstrateOps.ts](web/lib/governance/canonicalSubstrateOps.ts))
3. ✅ **Remove context_items API routes**
   - Delete [web/app/api/baskets/[id]/context-items/route.ts](web/app/api/baskets/[id]/context-items/route.ts)
   - Delete [web/lib/contextItems.ts](web/lib/contextItems.ts)
   - Delete [web/lib/server/contextItems.ts](web/lib/server/contextItems.ts)

### Phase 2: UI Updates
4. ✅ **Fix Building Blocks page**
   - Update [web/app/api/baskets/[id]/building-blocks/route.ts](web/app/api/baskets/[id]/building-blocks/route.ts)
   - Update [web/app/baskets/[id]/building-blocks/BuildingBlocksClientV2.tsx](web/app/baskets/[id]/building-blocks/BuildingBlocksClientV2.tsx)
5. ✅ **Update anchor helpers** ([web/lib/anchors/mutationHelpers.ts](web/lib/anchors/mutationHelpers.ts))

### Phase 3: Cleanup
6. ✅ **Update shared contracts**
7. ✅ **Fix test files**
8. ✅ **Remove deprecated files**

---

## Deployment Recommendation

**🔴 DO NOT DEPLOY TO PRODUCTION**

**Reason:** Frontend will fail with 500 errors on:
- Building Blocks page (/baskets/[id]/building-blocks)
- Any governance proposal approval with CreateContextItem operations
- Any anchor tagging workflows

**Timeline Estimate:**
- Phase 1 (Critical Path): 2-3 hours
- Phase 2 (UI Updates): 2-3 hours
- Phase 3 (Cleanup): 1-2 hours
- **Total: 5-8 hours**

**Safe Deployment Path:**
1. Complete Phase 1 + Phase 2 migration
2. Test locally with v3.0 backend
3. Deploy to production
4. Complete Phase 3 cleanup post-deployment

---

## Testing Checklist (Pre-Deployment)

- [ ] Building Blocks page loads without errors
- [ ] Governance proposal approval works (test CreateBlock operations)
- [ ] Anchor tagging creates blocks (not context_items)
- [ ] No 500 errors in browser console
- [ ] TypeScript compilation passes
- [ ] All semantic_types render correctly in UI

---

## Additional Notes

**V3.0 Semantic Types Reference:**
- **Knowledge:** fact, metric, event, insight, action, finding, quote, summary
- **Meaning:** intent, objective, rationale, principle, assumption, context, constraint
- **Structural:** entity, classification, reference

**Emergent Anchors:**
- No predefined vocabulary (free-text `anchor_role` field)
- Vocabulary emerges from agent inference + user tagging
- Autocomplete shows existing vocabulary via query: `SELECT DISTINCT anchor_role FROM blocks WHERE anchor_role IS NOT NULL`

**Universal Versioning:**
- All blocks can have `parent_block_id` chains
- Version if identity persists, new block if identity changes

**Scope Elevation:**
- NULL (basket-scoped) → WORKSPACE → ORG → GLOBAL
- Enables cross-basket memory for CONSTANT blocks
