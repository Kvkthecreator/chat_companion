# YARNNN Document Modes — Canon v2.0 (Spec)

Version: 1.0.0
Status: Authoritative
Last Updated: 2025-09-09

## Purpose
Define the canonical document modes, UX contracts, and guardrails so P4 Presentation remains pure and consistent across FE/BE. This spec narrows scope to Read, Compose (instructions), Compare (v1), and Analyze Lite (v1). Full Analyze can follow in v2.

## Modes

- Read: Finalized presentation. Renders composed prose + resolved substrate context. No substrate writes.
- Compose (Instructions): Capture or refine composition intent and pinned substrate. Regeneration always creates a new version; there is no inline prose editing.
- Compare: Version diff for prose and reference set. Uses immutable `document_versions`.
- Analyze Lite: Reference panel, composition_stats, coverage %, stale badge if referenced substrate changed. Links to proposals affecting this doc.

## Acceptance Criteria

### Read
- Renders current document with resolved substrate references (peers: block, dump, context_item, timeline_event).
- Shows references panel with role/weight and deep links to substrate.
- Emits no substrate writes; only consumes `documents`, `substrate_references`, and read-only substrate queries.

### Compose (Instructions)
- Collect intent, target audience, tone, and optional template selection.
- Allow pinning specific substrate (blocks, dumps) to guarantee inclusion.
- Submit instructions directly to P4 composer; regeneration creates a new immutable `document_version`.
- Optional action: Extract to Memory → snapshot current prose to `raw_dump` (P0) with provenance; P1 proposals run async; user can later attach resulting substrate.
- No inline prose editing; users adjust instructions and regenerate.

### Compare
- Version list with timestamps and author.
- Prose diff and references diff (added/removed/changed role/weight).
- Clear version semantics; compare current working copy vs any version.

### Analyze Lite
- Show composition stats: counts per substrate type, total references, provenance coverage %, freshness score.
- Surface the current `doc_insight` (themes, tensions, opportunities, recommended actions) for the active version.
- Flag stale substrate references and link to impacted proposals.
- Provide actions to regenerate doc insight or export insight summary.

## Guardrails (Canon)
- P4-only writes: `documents`, `document_versions`, `substrate_references`.
- No P1/P2 RPCs from document routes; governance is separate.
- Reflections target `document_versions` (optional read), never used as substrate.
- No artifact recursion: documents do not compose documents; reflections do not reflect on reflections.

## RPC Allow-List (by mode)
- Read: read-only selects on `document_heads`, `document_versions`, `substrate_references`, `blocks`, `raw_dumps`, `timeline_events`.
- Compose: `fn_document_create`, `fn_document_set_instructions`, `fn_document_version_create`, `fn_document_reference_sync`.
- Compare: read-only on `document_versions`, references-by-version view.
- Analyze Lite: read-only on projections: `document_composition_stats`, `document_insights_by_version`, last-modified metadata for referenced substrate.

## Events
- doc.created, doc.updated (edit), doc.versioned (compare/lock).
- Optional: doc.composition_stats.computed, doc.stale_detected (analyze-lite).

## Endpoints (v1)
- GET /api/documents/:id
- GET /api/documents/:id/composition
- GET /api/documents/:id/versions
- POST /api/baskets/:id/documents (create instructions + enqueue composition)
- POST /api/documents/:id/recompose (update instructions + enqueue new version)
- POST /api/p4/document-canon (regenerate canonical document)
- POST /api/p4/starter-prompt (regenerate canonical prompt pack)
- Optional: POST /api/documents/:id/extract-to-memory (snapshot → raw_dump)

## UX Notes
- Display substrate types as peers (no hierarchy), with type-specific affordances.
- Show clear messaging: “This text is not memory until you Extract to Memory.”
- On stale: surface impact gently; do not auto‑change prose.

## Document Creation Flow
- Present a single entry point with two paths: **Quick Intent** (free-form instructions) and **Template** (predefined schema such as Strategy Brief, Prompt Starter, 7-day Plan).
- Always collect intent, target audience, and optional tone; template selection preloads structured prompts.
- After submission, navigate to the document detail page showing the Compose banner while the version is generated.
- The frontend calls `/api/baskets/:id/documents` which stores instructions and enqueues composition; no prose is edited client-side.

## Definition of Done (v1)
- Read/Compose/Compare live behind P4 guardrails.
- `substrate_references` remains the single attach/detach surface; no block-only endpoints.
- Composer generates structured output (summary, themes, tensions, recommendations) and stores narrative in `document_versions`.
- Analyze Lite surfaces doc insight + metrics sourced from read-only projections.
