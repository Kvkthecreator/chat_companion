# YARNNN_SUBSTRATE_DELTA_ENGINE.md
Version: 2.0
Status: Canon — P1 Substrate Resolver (Proposal-first)

## Purpose
Define how P1 converts a new `raw_dump` into **governance proposals** by comparing **what is** (basket snapshot) with **what is proposed** (extracted candidates). All substrate mutations flow through governance.

---

## Inputs
- `new_dump` — text + file refs
- `basket_snapshot`:
  - `CTX_INDEX`: (kind, normalized_label) → context_item_id, stats
  - `BLOCK_INDEX`: signature_hash → block_id, variants

## Normalization & Similarity
- Normalize labels; compute `normalized_label`
- Fuzzy matching per kind with thresholds `SIM_THRESH_{kind}`
- `signature_hash` for blocks: sha256 over normalized core fields

---

## Decision Table

| Candidate | Exact Match | Fuzzy ≥ τ | Else |
|---|---|---|---|
| context_item | PROPOSE: Attach to existing | PROPOSE: Attach nearest (or create with merge hint) | PROPOSE: Create new |
| block | PROPOSE: Revision (if content changed) | PROPOSE: Revision (if same signature class) | PROPOSE: Create new |

All decisions create **governance proposals** that require approval before substrate commitment.

## Governance Integration

### Proposal Generation
- Agent extracts candidates → generates operations → packages as proposal
- Proposal includes: operations list, validation report, confidence scores
- No direct substrate writes - everything flows through governance

### Validation Pipeline  
- Duplicate detection across existing substrate
- Impact analysis (affected documents, relationships)  
- Confidence scoring for human review prioritization

---

## Idempotency & Determinism
- `delta_id = sha256(dump_id + sorted(candidate_signatures))`
- Pass `delta_id` to bulk RPCs for safe retries.

---

## Pseudo-code (resolver)
```pseudo
snapshot = load_snapshot(basket_id)
candidates = extract_candidates(dump)
delta_id = compute_delta_id(dump_id, candidates)

for c in candidates.context_items:
  k = (c.kind, c.normalized_label)
  if k in snapshot.CTX_INDEX: attach(c, snapshot.CTX_INDEX[k])
  else:
    m = fuzzy_match(k, snapshot.CTX_INDEX, τ_by_kind)
    if m: attach(c, m.id) else: create(c)

for b in candidates.blocks:
  sig = signature(b)
  if sig in snapshot.BLOCK_INDEX: revise(b, BLOCK_INDEX[sig])
  else: create(b)

emit_summary(delta_id, counts)
```

---

## Acceptance
`rg -n "delta_id|CTX_INDEX|BLOCK_INDEX|Decision Table" docs/YARNNN_SUBSTRATE_DELTA_ENGINE.md`

---

## Commit
docs: add YARNNN_SUBSTRATE_DELTA_ENGINE with snapshot, thresholds, and resolver spec