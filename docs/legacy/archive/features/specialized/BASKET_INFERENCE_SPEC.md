# Basket Inference Specification

This document captures the heuristics YARNNN uses to infer the most relevant
basket for an AI session. It serves as the canonical reference for both MCP
adapters and any future clients.

## 1. Basket Signatures (P3 Reflections)
- Maintain a **single canonical reflection** per basket.
- Reflection fields:
  - `summary`: 3–6 sentences describing the problem, scope, and current focus.
  - `anchors[]`: key bullets (e.g., `core_problem`, `audience`, `goals`).
  - `entities[]`: names/products/teams mentioned frequently.
  - `keywords[]`: top terms or tags.
  - `last_updated`: timestamp of the reflection update.
  - `ttl`: refresh threshold (e.g., 14 days).
  - `embedding`: vector representation of `summary + anchors`.
- Refresh triggers:
  - ≥5 approved substrate mutations since last update.
  - TTL expired.
  - User marks “misrouted basket” feedback.

## 2. Session Fingerprint
For each conversation/request before a tool call:
- Generate `session_fingerprint` with:
  - `summary`: 2–4 sentence recap of the current chat.
  - `intent`: enum (`ask`, `create`, `validate`, `recall`).
  - `entities[]`, `keywords[]` extracted from the session.
  - `embedding`: vector built from `summary + entities`.
- Tools that mutate substrate (`create_memory_from_chat`, `add_to_substrate`) reject
  invocations without a populated `session_fingerprint.embedding` to enforce this canon.

## 3. Scoring & Selection
For each candidate basket `b`:
```
sim      = cosine(embedding_chat, embedding_basket)
boost    = 0.15 * recency_norm(b.last_updated)
affinity = 0.10 * user_affinity_norm(user, b)
penalty  = 0.15 if conflict_flag(session, b) else 0
score    = 0.75 * sim + boost + affinity - penalty
```
Keep the top candidate and retain the top three for display.

Thresholds:
- `score ≥ 0.80` → auto-select; respond “Using {basket} (high confidence).”
- `0.55 ≤ score < 0.80` → ask for confirmation with one-tap affordance.
- `score < 0.55` → present top-3 baskets (max 8 if ties).

Writes (create/add substrate):
- Require confirmation if `score < 0.80`.
- Otherwise auto-select but present a “Change basket” chip.
- Low-score writes can route to an **Unassigned** inbox.

## 4. Tie-Breaking
If top-2 scores differ by `< 0.06`:
1. Ask each basket’s reflection: “Does this session belong to you? Why?”
2. Use responses to break the tie or present both options with rationale.

## 5. Learning Signals
- Log `(fingerprint, chosen_basket)` for lightweight retraining
  (nearest-centroid or logistic regression).
- Use user confirmations to adjust affinity weights.

## 6. Adapter Behaviour
- Both Claude and ChatGPT adapters call the shared helper before every tool
  invocation.
- They display the confidence state (auto/confirm/select) per the thresholds.
- Writes respect the same rules and can queue to “Unassigned” when ambiguous.

This spec is referenced by `@yarnnn/integration-core` and should stay in sync
with the implementation of the `basketSelector` helper.
