# YARNNN Deletion & Retention Canon v1.0

Status: Adopted • Scope: Substrate lifecycle (archive/redact → retention → physical delete) • Date: 2025‑09‑15

## 1) Philosophy & Scope

- Substrate is the durable memory plane. Users never “erase” memory by default — they archive/redact.  
- Hard deletion is policy‑bound and executed by the platform (cron/vacuum), not by users.  
- Governance and audit are preserved at every step; all mutations route through `/api/work`.

In scope: blocks, context_items, raw_dumps.  
Out of scope: timeline_events (append‑only), artifacts (documents/reflections managed independently).

## 2) User‑Visible Operations (Basket‑Scoped)

These are the only destructive surfaces users see:

- Building Blocks & Graph: Per‑item Archive/Redact with cascade preview and governance.  
- Basket Settings → Danger Zone: Basket‑wide actions (governance‑first, chunked):
  - Archive + Redact All (default):
    - Blocks → `ArchiveBlock`
    - Context items → `Delete`/Deprecate (soft), or `ArchiveContextItem` when available
    - Dumps → `RedactDump` (scope: full)
  - Redact Dumps Only (privacy fast‑path)
  - Hard Purge (Admin): disabled unless retention + admin policy enabled; schedules physical delete via retention/vacuum (no immediate hard delete)

Safety: Always show cascade preview; typed confirmation (basket name). Chunk operations (50–100/batch) and show progress.

## 3) Developer‑Level Retention Policy (No End‑User UI)

Retention is configured by developers/ops; not user‑editable.

- Defaults (recommended):  
  - `block`: 30 days after archive  
  - `context_item`: 30 days after deprecate/archive  
  - `dump`: 90 days after redact  
  - `timeline_event`: never  
  - Artifacts (documents/reflections): not covered by substrate retention; users delete freely

- Tombstones (`public.substrate_tombstones`):
  - Created by Archive/Redact operations.
  - `earliest_physical_delete_at` set from workspace policy if retention is enabled; otherwise left null.
  - Contains counts for cascade impact (refs, relationships, affected documents) and audit metadata.

- Physical Deletion (Vacuum):
  - Function: `public.fn_vacuum_substrates(workspace_id uuid, limit int)`  
  - Preconditions: `earliest_physical_delete_at` passed; no remaining hard references; relationships pruned.  
  - Emission: `substrate.physically_deleted` timeline events.

## 4) Scheduling (Cron)

One of:

- Supabase Postgres scheduler (preferred) to call `fn_vacuum_substrates` nightly per workspace.  
- Vercel Cron hitting `/api/vacuum/run` with service role; enumerate workspaces; call vacuum in batches.

Cron only acts when retention is enabled and tombstones are eligible. No silent deletion outside this path.

## 5) API & Workflow (Single Path — No Dual Approaches)

- All destructive actions use `/api/work` (Universal Work).  
- Supported ops (subset): `ArchiveBlock`, `RedactDump`, `Delete` (context_item soft), `MergeContextItems`.  
- Basket‑wide purge is a composite “PurgeBasket” request expanded into chunked operations (never a direct “delete all” SQL).

Pseudocode (Danger Zone → Archive + Redact All):

```json
POST /api/work
{
  "work_type": "MANUAL_EDIT",
  "work_payload": {
    "basket_id": "...",
    "operations": [
      { "type": "ArchiveBlock", "data": { "block_id": "..." } },
      { "type": "Delete", "data": { "target_id": "...", "target_type": "context_item", "delete_reason": "purge_basket" } },
      { "type": "RedactDump", "data": { "dump_id": "...", "scope": "full", "reason": "purge_basket" } }
    ]
  },
  "priority": "normal"
}
```

Chunk in batches with progress reporting; respect governance (proposal vs auto‑execute per policy).

## 6) UI Surfaces (Canon‑Aligned)

- Building Blocks & Graph: Per‑item Archive/Redact with preview + governance.  
- Basket Settings (new subpage; last after Graph):
  - Overview: counts (active/archived/redacted) + plain English retention statement.  
  - Bulk Actions: Archive + Redact All (default), Redact Dumps Only, Hard Purge (Admin; only when retention+policy enabled).  
  - No retention editors or summaries for end‑users.

## 7) Guardrails

- Governance‑first: No destructive mutations outside `/api/work`.  
- Cascade preview mandatory; document version snapshot optional before detach.  
- Timeline events emitted for archive/redact/physical delete.

## 8) Implementation Notes (Current State)

- Blocks & Dumps: Archive/Redact RPCs + tombstones present.  
- Context Items: Deprecate/Delete path exists; mirror tombstone+retention for CI recommended (tracked as a small follow‑up).  
- Retention UI removed from user settings; policy is developer‑managed.  
- Vacuum endpoints exist; cron to be configured per environment.

## 9) Non‑Goals

- No user‑visible knobs for retention durations.  
- No direct “hard delete now” buttons — hard deletion is policy‑driven via vacuum.

## 10) Migration & Backward Compatibility

- `/api/changes` is deprecated; `/api/work` is canonical.  
- Legacy delete/retention UIs removed; single path documented here.

