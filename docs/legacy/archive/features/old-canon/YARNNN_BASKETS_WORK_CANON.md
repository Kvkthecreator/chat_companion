# Canon v2.0 — Substrate/Artifact Model
Reflections are artifacts stored in reflections_artifact table. Pure substrate memory layer.

# Yarnnn — Basket Work Canon (Display-Only, Phase 1)

**Purpose**
Define the read-only surfaces and payloads for `/baskets/:id/dashboard` and subpages, covering documents, blocks (**context_blocks**), and context_items. Mutation (Dump, Proposals, Review) is explicitly out of scope for Phase 1.

## Core Principle
Users return to see:
1) **State of the basket right now** (continuity & trust)  
2) **The most important next move** (bounded, reviewable suggestion)

## Authority
- Memory reflections: server computes → `reflections_artifact` → `timeline_events` → `events`
- Frontend mirrors durable state; no client-side synthesis

Reflections are artifacts targeting substrate state or document versions. Stored durably in reflections_artifact with flexible targeting.

## Pages & Panels

### A. Dashboard (default)
**Route:** `/baskets/[id]/dashboard`  
**Panels:**
- **Middle (primary)**
  1. **State Snapshot** — name, counts, last_updated, current_focus  
     **GET** `/api/baskets/:id/state`
  2. **Canonical Docs (top 3)** — id, title, updated_at, preview  
     **GET** `/api/baskets/:id/documents?limit=3`
  3. **Governance Queue** — active proposals awaiting review  
     **GET** `/api/baskets/:id/proposals` (real governance queue)

- **Right (Guide)**  
  Tabs: **Ask** (compute-only, no writes) | **Review** (governance queue management)  
  *Review tab enables proposal approval/rejection workflow.*

- **Left (Basket Nav)**  
  Links: **Dashboard**, **Documents**, **Blocks**, **Timeline**.

- **Top Bar**  
  Back button → `/baskets`, basket title, show/hide left panel.

### B. Documents
**Route:** `/baskets/[id]/documents` (list)  
**GET** `/api/baskets/:id/documents`  
Detail: `/baskets/[id]/documents/[docId]`  
**GET** `/api/documents/:docId`  
*Read-only. No inline edits in Phase 1.*

### C. Blocks (Governance-Enabled)
**Route:** `/baskets/[id]/blocks`  
**GET** `/api/baskets/:id/blocks`  
*Power-user governance interface. Includes proposal review for blocks and context_items.*

### D. Timeline (Evolution)
**Route:** `/baskets/[id]/timeline`  
**GET** `/api/baskets/:id/timeline`  
Union view of `basket_deltas` (applied/rejected), `revisions`, notable `events`. Read-only.

## Payload Contracts (minimal)

### 1) `GET /api/baskets/:id/state`
```json
{
  "basket_id": "uuid",
  "name": "string",
  "counts": {"documents": 3, "blocks": 4, "context_items": 1},
  "last_updated": "2025-08-14T10:10:00Z",
  "current_focus": "Prototype + marketing plan"
}
```
2) GET /api/baskets/:id/documents?limit=3
{
  "items": [
    {"id":"uuid","title":"Marketing Plan","updated_at":"...","preview":"..."},
    {"id":"uuid","title":"Design Brief","updated_at":"...","preview":"..."}
  ]
}
3) GET /api/baskets/:id/proposals
{
  "items": [
    {
      "id":"uuid",
      "proposal_kind":"Extraction",
      "origin":"agent",
      "status":"PROPOSED",
      "ops_summary":"Create block 'Q4 Strategy', context_item 'Revenue Target'",
      "confidence":0.85,
      "impact_summary":"affects 2 docs, 4 relationships",
      "created_at":"...",
      "validator_report": {"dupes":[],"warnings":[],"suggested_merges":[]}
    }
  ]
}
4) GET /api/baskets/:id/blocks
{"items":[{"id":"uuid","title":"Target Audience","state":"accepted","updated_at":"..."}]}
5) GET /api/baskets/:id/timeline
{
  "items": [
    {"ts":"...","type":"delta","summary":"Accepted update to Marketing Plan"},
    {"ts":"...","type":"event","summary":"Dump added from Figma notes"}
  ]
}
6) GET /api/documents/:docId
{"id":"uuid","title":"Marketing Plan","updated_at":"...","content_rendered":"<html or md preview>"}
Golden Rules (Phase 1)
No writes. UI must not fire POST/PATCH/DELETE.
“Ask | Suggest” in Guide = UI placeholders only.
All basket reads scoped by workspace_id under RLS.
Previews/snippets are computed server-side.
End of doc.
