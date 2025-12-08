# YARNNN Compose From Memory — Canon v2.0 (Spec)

Version: 1.0.0
Status: Authoritative
Last Updated: 2025-09-09

## Purpose
Define a canon-pure “Compose From Memory” path distinct from “Start Blank,” enabling users to generate documents from governed memory plus a simple intent while preserving substrate/artifact separation.

## Principles
- P4-only: Composition consumes existing substrate; no substrate writes.
- Intent-as-artifact by default: treat user intent as artifact metadata; optionally allow “Add intent to memory” via P0/P1.
- Deterministic inputs: explicit memory window and optional pinned substrates.
- Duplication control: composition_signature for idempotent re-composition.

## UX (Simple)
- Entry: “Compose From Memory”
- Inputs: intent (short text), document_type (brief/plan/summary/report), memory window (since/range/tags), optional pinned substrates.
- Option: “Add intent to memory” (off by default).
- Output: new document with initial document_version, references attached, coverage and stale indicators.

## API

POST /api/presentation/compose
- Body (extension of DocumentComposition):
```json
{
  "title": "Q4 Plan",
  "narrative_sections": [{"id":"sec1","content":"...","order":0}],
  "substrate_references": [{"id":"uuid","type":"block","order":0}],
  "composition_context": {
    "intent": "Create a Q4 marketing plan",
    "document_type": "plan",
    "window": { "since": "2025-08-01" , "tags": ["marketing"] },
    "pinned": { "blocks": ["..."], "items": ["..."] }
  },
  "composition_signature": "sha256(...)",
  "workspace_id": "...",
  "basket_id": "...",
  "author_id": "...",
  "add_intent_to_memory": false
}
```

Behavior (P4):
- Validates substrate references by type and workspace.
- Creates/updates document + initial document_version; attaches references via `substrate_references`.
- Stores `composition_context` and `composition_signature` in document metadata for reproducibility.
- Emits events: `doc.created` (first time), `doc.versioned` (on new version).

Optional Side-effect (if add_intent_to_memory):
- Create `raw_dump` with `{ text_dump: intent, meta: { source: 'compose_from_memory', document_id, document_version_id } }` (P0).
- P1 later proposes context_item(kind='intent'); on approval, UI may auto-attach to the document (P4) as a reference.

## Composition Signature
`composition_signature = sha256(basket_id + document_type + normalized_intent + normalized_window + pinned_ids)`
- If a document with the same signature exists, offer: Open existing | Create new version | Create new doc (escape hatch).
- Prevents ambiguous duplicates from repeated runs without intent/window changes.

## Guardrails
- No P1/P2 RPCs from this endpoint.
- References may include: block, dump, context_item, timeline_event only (peers).
- Reflections are artifacts and not included as substrate references.

## Acceptance
- Distinct UX and endpoint path from “Start Blank”.
- Produces document + initial version and attaches references across all substrate types.
- Stores composition_context + signature; idempotent per signature.
- Optional intent-to-memory flows through P0/P1; P4 remains artifact-only.

