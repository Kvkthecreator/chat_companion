# Basket & Building Blocks Management - Codebase Audit

**Date**: 2025-10-16
**Context**: Planning substrate CRUD strategy for Building Blocks page

---

## Executive Summary

**Current State**: Building Blocks page is READ-ONLY. No substrate mutation endpoints exist for user-initiated block operations.

**Governance Architecture**: Workspace-level governance policies control routing (`proposal` vs `direct` vs `hybrid`), but currently set to `proposal` mode for `ep_manual_edit`.

**Recommendation**: Implement canon-compliant "direct-feel CRUD" by:
1. **Basket operations** → Direct REST (rename, archive/restore)
2. **Block operations** → `/api/work` with `auto` governance policy for instant approval
3. **No raw DELETE** → Use ArchiveBlock + scheduled vacuum

---

## 1. Current Implementation Status

### A. Basket-Level Operations

**Endpoint**: `GET /api/baskets/[id]`
- **Status**: ✅ Exists
- **Operations**: Read basket metadata only
- **Missing**:
  - ❌ PATCH for rename
  - ❌ POST `/archive` for soft delete
  - ❌ POST `/restore` for unarchive
  - ❌ Cascade preview before delete

**Database Schema**:
```sql
baskets (id, name, workspace_id, status, created_at)
  status: 'INIT' | 'ACTIVE' | 'ARCHIVED'
```

---

### B. Building Blocks Page

**UI**: `/app/baskets/[id]/building-blocks/BuildingBlocksClientV2.tsx`
- **Status**: ✅ Exists - Read-only substrate browser
- **Features**:
  - Filter by anchored/free/stale/unused/meaning_blocks
  - Sort by usefulness/recency/confidence/staleness
  - Search by content
  - Stats: total, anchored, stale, unused, meaning blocks
  - Quality metrics: usefulness_score, times_referenced, staleness_days

**API**: `GET /api/baskets/[id]/building-blocks`
- **Status**: ✅ Exists - Returns blocks with quality metrics
- **Missing**: No mutation endpoints (POST/PATCH/DELETE)

**Detail View**: `GET /api/baskets/[id]/building-blocks/[blockId]`
- **Status**: ✅ Exists - Single block details
- **Missing**: No PATCH/DELETE on this route

---

### C. Governance Infrastructure

**Work Orchestration**: `POST /api/work`
- **Status**: ✅ Exists
- **Supported Work Types**:
  - `P0_CAPTURE` - Raw dump (direct, no governance)
  - `P1_SUBSTRATE` - AI substrate creation (governed)
  - `P2_GRAPH` - Relationship inference (governed)
  - `MANUAL_EDIT` - User edits (governed)
  - `PROPOSAL_REVIEW` - Manual review (governed)
  - `TIMELINE_RESTORE` - Historical restore (governed)

**Operation Schema** (flat, not nested):
```typescript
{
  type: "CreateBlock" | "ReviseBlock" | "MergeBlocks" | "UpdateBlock" | "ArchiveBlock",
  data: { /* flat fields */ }
}
```

**Governance Settings** (`workspace_governance_settings`):
- `ep_manual_edit`: `'proposal'` (current default)
  - Options: `'proposal'` | `'direct'` | `'hybrid'`
- `ep_graph_action`: `'proposal'`
- `direct_substrate_writes`: `false`
- `validator_required`: `false`

---

### D. Current Gaps

**Basket Management**:
1. ❌ No PATCH `/api/baskets/[id]` for rename
2. ❌ No POST `/api/baskets/[id]/archive` for soft delete
3. ❌ No POST `/api/baskets/[id]/restore` for unarchive
4. ❌ No cascade preview endpoint

**Block Management** (all missing):
1. ❌ Create block via `/api/work` (P1_SUBSTRATE)
2. ❌ Revise block via `/api/work` (MANUAL_EDIT)
3. ❌ Merge blocks via `/api/work` (MANUAL_EDIT)
4. ❌ Update metadata/anchors via `/api/work` (MANUAL_EDIT)
5. ❌ Archive block via `/api/work` (MANUAL_EDIT)

**UI Features** (all missing):
1. ❌ Inline edit for block title/content
2. ❌ Multi-select + merge action
3. ❌ Archive button (no raw DELETE)
4. ❌ Anchor assignment UI
5. ❌ Optimistic updates with pending states

---

## 2. Canon Compliance Analysis

### Sacred Principles (from YARNNN_CANON.md)

**Principle #1**: ✅ All substrate mutations flow through governance
- **Status**: No mutations exist yet, but `/api/work` infrastructure ready
- **Compliance**: Will be compliant when operations route through `/api/work`

**Principle #2**: ✅ User-controlled execution mode
- **Status**: Workspace governance settings exist
- **Current**: `ep_manual_edit = 'proposal'` (requires review)
- **Recommended**: Change to `'direct'` or implement `auto` confidence routing

**Principle #3**: ⚠️ Confidence-informed routing
- **Status**: Infrastructure exists but not utilized
- **Issue**: No confidence thresholds configured in governance settings
- **Recommendation**: Add `confidence_threshold` field or use `user_override: 'allow_auto'`

**Principle #4**: ✅ Agent intelligence mandatory
- **Status**: Not applicable - user-initiated operations don't require agent processing
- **Note**: P1_SUBSTRATE operations from agents still go through governance

---

### V3.0/V3.1 Substrate Architecture

**V3.0 Changes** ✅:
- context_items merged into blocks ✅
- Unified semantic_type taxonomy ✅
- Emergent anchor_role (not fixed categories) ✅
- Universal versioning (parent_block_id chains) ✅

**V3.1 Semantic Layer** ✅:
- Vector embeddings on ACCEPTED+ blocks ✅
- P2 relationship inference (addresses, supports, contradicts, depends_on) ✅
- Embeddings generate AFTER governance approval ✅
- P2 queues after new ACCEPTED blocks ✅

**Implication**: User CRUD must go through governance so embeddings/P2 fire correctly.

---

## 3. Recommended Implementation Strategy

### Philosophy: "Direct-Feel CRUD via Governed Auto-Approval"

**User Perception**: Instant feedback (like direct CRUD)
**Reality**: Every action routes through governance, emits events, triggers embeddings/P2

**Mechanism**:
1. Set `ep_manual_edit = 'direct'` OR use `user_override: 'allow_auto'` in payload
2. Operations submit via `/api/work` with `confidence=1.0` (human-initiated)
3. Governance routes to auto-approve instantly
4. Timeline events + embeddings + P2 all fire normally
5. UI shows optimistic updates with "Pending" → "Accepted" states

---

### A. Basket Operations (Direct REST - Not Governed)

These are **container-level**, not substrate mutations.

#### 1. Rename Basket

**Endpoint**: `PATCH /api/baskets/[id]`

**Request**:
```json
{
  "name": "Updated Basket Name"
}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "Updated Basket Name",
  "updated_at": "2025-10-16T..."
}
```

**Backend**:
- Update `baskets.name`
- Emit `timeline_events`: `BASKET_RENAMED`
- **NOT governed** (container metadata, not substrate)

---

#### 2. Archive Basket

**Endpoint**: `POST /api/baskets/[id]/archive`

**Request**:
```json
{
  "reason": "Project completed"
}
```

**Response**:
```json
{
  "id": "uuid",
  "status": "ARCHIVED",
  "cascade_preview": {
    "blocks_affected": 45,
    "documents_affected": 3,
    "insights_affected": 1
  }
}
```

**Backend**:
- Set `baskets.status = 'ARCHIVED'`
- Blocks/docs remain immutable (just hidden from default views)
- Emit `timeline_events`: `BASKET_ARCHIVED`
- **NOT governed**

---

#### 3. Restore Basket

**Endpoint**: `POST /api/baskets/[id]/restore`

**Response**:
```json
{
  "id": "uuid",
  "status": "ACTIVE"
}
```

**Backend**:
- Set `baskets.status = 'ACTIVE'`
- Emit `timeline_events`: `BASKET_RESTORED`

---

#### 4. Schedule Hard Delete (Ops-Only)

**Endpoint**: `POST /api/baskets/[id]/schedule-delete`

**Request**:
```json
{
  "execute_at": "2025-12-01T00:00:00Z"
}
```

**Guardrails**:
- Only allowed if `status = 'ARCHIVED'`
- 7-day cooling-off period
- Ops vacuum scheduled
- NOT exposed to regular users (admin-only future feature)

---

### B. Block Operations (Governed via `/api/work`)

All substrate mutations route through `/api/work` with `work_type: 'MANUAL_EDIT'`.

#### Universal Request Envelope

**Endpoint**: `POST /api/work`

**Request**:
```json
{
  "work_type": "MANUAL_EDIT",
  "work_payload": {
    "basket_id": "uuid",
    "operations": [
      { /* operation object */ }
    ],
    "user_override": "allow_auto",  // For instant approval
    "confidence_score": 1.0,         // Human-initiated = high confidence
    "provenance": []                 // Optional: source raw_dump_ids
  },
  "priority": "normal"
}
```

---

#### Operation 1: CreateBlock

**Operation Object**:
```json
{
  "type": "CreateBlock",
  "title": "API Performance SLO",
  "content": "p95 latency <= 300ms by Q4",
  "semantic_type": "objective",
  "anchor_role": "performance",
  "confidence": 1.0
}
```

**Governance Flow**:
1. Proposal created with `origin='human'`, `confidence=1.0`
2. Policy checks `ep_manual_edit` (if `'direct'`) → auto-approve
3. Block created with `state='ACCEPTED'`
4. Embedding generated (V3.1)
5. P2 queued to infer relationships
6. Timeline event emitted

---

#### Operation 2: ReviseBlock

**Operation Object**:
```json
{
  "type": "ReviseBlock",
  "block_id": "existing-uuid",
  "title": "API Performance SLO (revised)",
  "content": "p95 latency <= 250ms by Q4",
  "confidence": 1.0
}
```

**Backend Behavior**:
- Creates new block with `parent_block_id = existing-uuid` (versioning)
- Old block remains in chain
- New embedding generated
- P2 re-infers relationships

---

#### Operation 3: MergeBlocks

**Operation Object**:
```json
{
  "type": "MergeBlocks",
  "from_ids": ["dup-1", "dup-2"],
  "canonical_id": "keeper-id",
  "merged_content": "Consolidated definition...",
  "confidence": 1.0
}
```

**Backend Behavior**:
- Duplicates archived
- Canonical block content updated
- Embedding regenerated
- P2 relationship graph updated

---

#### Operation 4: UpdateBlock

**Use Case**: Retag anchors, update metadata (no content change)

**Operation Object**:
```json
{
  "type": "UpdateBlock",
  "block_id": "uuid",
  "anchor_role": "reliability",
  "metadata": { "priority": "high" },
  "confidence": 1.0
}
```

**Backend Behavior**:
- In-place update (no versioning for metadata-only changes)
- No embedding regeneration
- Timeline event only

---

#### Operation 5: ArchiveBlock

**Operation Object**:
```json
{
  "type": "ArchiveBlock",
  "block_id": "uuid",
  "reason": "superseded",
  "confidence": 1.0
}
```

**Backend Behavior**:
- Set `status = 'archived'`
- Embedding marked stale (not deleted)
- P2 relationships preserved (for audit trail)
- Timeline event emitted
- **NOT a DELETE** - data remains for restoration

**Canon Compliance**: No raw DELETE allowed. Physical deletion is scheduled ops vacuum.

---

## 4. Governance Policy Configuration

### Current Settings (from DB)

```sql
ep_manual_edit = 'proposal'          -- Requires review
direct_substrate_writes = false      -- Disallows direct table writes
validator_required = false           -- No mandatory human review
governance_enabled = false           -- (?)
```

### Recommended Change for "Direct-Feel CRUD"

**Option A**: Change workspace policy
```sql
UPDATE workspace_governance_settings
SET ep_manual_edit = 'direct'
WHERE workspace_id = 'user-workspace-uuid';
```

**Option B**: Use `user_override` in request payload (per-request)
```json
{
  "work_payload": {
    "user_override": "allow_auto",  // Bypasses policy, routes to auto
    ...
  }
}
```

**Recommendation**: Use **Option B** for flexibility. Allows per-operation control without changing workspace-wide policy.

---

## 5. UI/UX Implementation Pattern

### Optimistic Update Flow

**User Action** → **Optimistic UI** → **API Call** → **Confirm/Rollback**

```typescript
// User clicks "Archive Block"
const handleArchive = async (blockId: string) => {
  // 1. Optimistic update
  setBlocks(prev => prev.map(b =>
    b.id === blockId ? { ...b, status: 'pending_archive' } : b
  ));

  // 2. Submit to /api/work
  const response = await fetch('/api/work', {
    method: 'POST',
    body: JSON.stringify({
      work_type: 'MANUAL_EDIT',
      work_payload: {
        basket_id: basketId,
        operations: [{
          type: 'ArchiveBlock',
          block_id: blockId,
          reason: 'user_archived',
          confidence: 1.0
        }],
        user_override: 'allow_auto'
      }
    })
  });

  // 3. Handle response
  if (response.ok) {
    const { routing_decision } = await response.json();

    if (routing_decision === 'EXECUTED') {
      // Auto-approved - finalize UI
      setBlocks(prev => prev.filter(b => b.id !== blockId));
      toast.success('Block archived');
    } else {
      // Routed to proposal - show pending state
      setBlocks(prev => prev.map(b =>
        b.id === blockId ? { ...b, status: 'awaiting_approval' } : b
      ));
      toast.info('Archive request submitted for review');
    }
  } else {
    // Rollback optimistic update
    setBlocks(prev => prev.map(b =>
      b.id === blockId ? { ...b, status: 'active' } : b
    ));
    toast.error('Failed to archive block');
  }
};
```

---

### Block Row Actions

**Building Blocks Table**:
- ✏️ **Edit** → Opens inline editor → `ReviseBlock`
- 🔗 **Merge** (multi-select) → Dialog → `MergeBlocks`
- 🏷️ **Retag** → Anchor dropdown → `UpdateBlock`
- 📦 **Archive** → Confirm dialog → `ArchiveBlock`
- ℹ️ **Details** → Opens detail modal (read-only)

**System Indicators**:
- 🟡 "Pending" chip (governance status)
- 🔗 Relationship count badge
- ✅ Embedding status icon
- ⚠️ Staleness warning

---

## 6. Missing Implementation Checklist

### Basket Endpoints (Direct REST)
- [ ] `PATCH /api/baskets/[id]` - Rename
- [ ] `POST /api/baskets/[id]/archive` - Soft delete
- [ ] `POST /api/baskets/[id]/restore` - Unarchive
- [ ] `GET /api/baskets/[id]/cascade-preview` - Impact analysis

### Block Operations (via `/api/work`)
- [ ] Frontend: Inline edit form → `ReviseBlock`
- [ ] Frontend: Multi-select merge → `MergeBlocks`
- [ ] Frontend: Anchor assignment → `UpdateBlock`
- [ ] Frontend: Archive button → `ArchiveBlock`
- [ ] Frontend: Create block dialog → `CreateBlock`

### Governance Policy
- [ ] Add `confidence_threshold` field to `workspace_governance_settings`
- [ ] Implement auto-approval logic in `universalWorkRouter`
- [ ] Document `user_override` behavior in canon

### UI/UX Polish
- [ ] Optimistic updates with rollback
- [ ] Loading states (pending/executing)
- [ ] Toast notifications
- [ ] Keyboard shortcuts (⌘K for create, ⌘E for edit)
- [ ] Bulk actions (select all → archive)

---

## 7. Future Considerations (Out of Scope)

### Multi-Actor Approval
- **Current**: Single approval path (auto or manual)
- **Future**: Approval chains (AI → Human → Admin)
- **Schema Extension**:
```sql
ALTER TABLE proposals ADD COLUMN approvals jsonb DEFAULT '[]'::jsonb;

-- Example approval chain
approvals: [
  { actor_type: 'agent', actor_id: 'gpt-4', decision: 'approve', at: 'ts' },
  { actor_type: 'human', actor_id: 'user-uuid', decision: 'approve', at: 'ts' }
]
```

### Scheduled Operations
- **Use Case**: "Archive this block in 30 days"
- **Implementation**: Queue scheduled work items

### Undo/Redo
- **Use Case**: "Oops, restore that archived block"
- **Implementation**: Timeline-based restoration via `TIMELINE_RESTORE` work type

---

## 8. Assessment Summary

### Strengths
✅ Strong governance infrastructure (`/api/work` + workspace policies)
✅ V3.0/V3.1 substrate architecture solid (unified blocks + semantic layer)
✅ Read-only Building Blocks page with quality metrics
✅ Canon-compliant timeline events + embedding triggers

### Gaps
❌ No mutation endpoints for user-initiated block operations
❌ No basket rename/archive endpoints
❌ Governance policy stuck in `proposal` mode (needs `auto` or `direct`)
❌ No UI for CRUD actions (edit/merge/archive)

### Recommended Next Steps

**Phase 1 (Core CRUD)**: 2-3 days
1. Implement basket PATCH/archive/restore endpoints
2. Add `user_override: 'allow_auto'` support in `/api/work`
3. Create UI components for edit/merge/archive actions
4. Add optimistic updates with pending states

**Phase 2 (Polish)**: 1-2 days
5. Cascade preview for basket delete
6. Bulk actions (multi-select)
7. Keyboard shortcuts
8. Toast notifications

**Phase 3 (Advanced)**: Future
9. Confidence-based auto-approval thresholds
10. Multi-actor approval chains
11. Scheduled operations

---

## 9. Final Recommendation

**Conclusion**: Your intuition is correct - CRUD for Yarnnn IS different because substrate management (relationships, embeddings, scope) is the core service.

**Strategy**:
- **Don't overthink it** - Use `user_override: 'allow_auto'` for instant governance approval
- **Users get direct control feel** - Instant feedback with optimistic UI
- **Canon compliance preserved** - Timeline, embeddings, P2 all fire correctly
- **Future-proof** - Can tighten policies later without UI changes

**No need to scope multi-actor approval now** - You're right to defer that complexity. Start with simple auto-approval, iterate based on user behavior.

**Your framing of "blocks as core substrate" is spot-on** - The context management/relationships/scope elevation is what differentiates Yarnnn from traditional note-taking. Embrace that complexity in the backend, hide it with simple CRUD UX in the frontend.

---

**Next Step**: Implement Phase 1 (Core CRUD endpoints + UI components). Should I proceed with coding?
