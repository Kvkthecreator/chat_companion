# YARNNN_PRESENTATION_LAYERS.md
Version: 1.0
Status: Canon — Presentation (Downstream of Substrate/Graph)

## Purpose
Define how UI and agents **present** memory: documents, narrative, reflections, timelines. No substrate/graph business logic lives here.

---

## Principles
- **Documents are compositions**, not substrate.
- **Narrative is authored** (agent or user) using projection (graph + optional blocks).
- **Reflections** are computed in P3 and may be cached; UIs display them.

---

## Document Composition Model
- `documents` (with `document_type`, e.g., `narrative`)
- Attachments:
  - `document_blocks` (join)
  - `document_context_items` (join)
- No writes to `context_items`, `blocks`, or `substrate_relationships`.

---

## UI Views (examples)
- **Memory Timeline**: renders `timeline_events.preview` + deep links
- **Graph Lens**: entities/topics with edges; filter by window
- **Narrative Workspace**: side panel projection (entities/blocks), center authored text
- **Reflection Cards**: pattern/tension/question with "show inputs" affordance

---

## Event Consumption
- `doc.created|updated` are UI events only; they do not feed back into substrate.
- If atomized prose must become memory, model as `context_item.kind='cue'` in P1.

---

## Acceptance
`rg -n "Documents are compositions|Narrative is authored|Reflection Cards" docs/YARNNN_PRESENTATION_LAYERS.md`

---

## Commit
docs: add YARNNN_PRESENTATION_LAYERS clarifying narrative/docs as downstream consumers