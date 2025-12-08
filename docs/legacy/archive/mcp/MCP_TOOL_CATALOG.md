# YARNNN MCP Tool Catalog

This document inventories the tools exposed via `@yarnnn/integration-core` and
describes how each adapter should present them to host platforms (Claude MCP,
OpenAI Apps, etc.). It should stay in sync with the tool implementations.

## 1. Tool Summary

| Tool ID                  | Purpose                                       | Pipeline Touchpoints |
|-------------------------|-----------------------------------------------|----------------------|
| `create_memory_from_chat` | Capture a chat transcript into a new basket   | P0 → P1 → P2         |
| `get_substrate`           | Retrieve substrate/context for a session      | P1/P2 (read-only)    |
| `add_to_substrate`        | Append incremental knowledge to a basket      | P0 → P1              |
| `validate_against_substrate` | Compare new idea vs existing memory         | P2/P3 (analysis)     |
| `config_settings` (planned) | Surface ambient governance/auto-approve state | Governance metadata  |

## 2. Tool Behaviour (Core Contract)

### 2.1 `create_memory_from_chat`
- Input: conversation transcript, optional basket name, anchor suggestions.  
- Flow: creates raw dump(s) → triggers governed substrate extraction → returns
  basket info + governance actions.
- Response fields: `basket_id`, `basket_name`, `blocks_created`, `visualization`, `actions[]`.
- Adapters: may follow-up with basket confirmation (see Basket Inference spec).

### 2.2 `get_substrate`
- Input: optional basket, keywords, anchors, output format.  
- Flow: read substrate (blocks/context/raw dumps) filtered by session.  
- Response: `substrate[]`, `total_count`, `substrate_snapshot_id` (for caching).
- Adapters: present result as text or structured cards.

### 2.3 `add_to_substrate`
- Input: content snippet, metadata, target basket.  
- Flow: create raw dump (P0) → propose substrate updates → return governance state.  
- Response: `raw_dump_id`, `proposed_blocks`, `governance_mode`.
- Adapters: must show confirmation chip if basket score < 0.80.
- If basket inference returns `pick`, Yarnnn surfaces the capture in the
  Unassigned queue so a human can assign a basket before proposals run.

### 2.4 `validate_against_substrate`
- Input: new idea text, optional focus list/keywords.  
- Flow: run analysis vs existing substrate (conflict detection, alignment score).  
- Response: `alignment_score`, `conflicts[]`, `recommendation`, optional analysis details.  
- Adapters: render conflict summary; may insert caution banners for low alignment.

### 2.5 `config_settings` *(planned)*
- Input: none (read) or setting updates (write).  
- Flow: fetch governance flags (auto/manual) at workspace level.  
- Response: e.g., `{ auto_approve: true, manual_review: false }`.  
- Adapters: simple two-option component for users to view/adjust preferences.

## 3. Basket Inference & Confidence UX
- Follows `docs/BASKET_INFERENCE_SPEC.md`.  
- Adapters call `/api/mcp/baskets/infer` with the session fingerprint; the
  backend responds with scored candidates derived from `basket_signatures`.
- Both adapters call `selectBasket()` before tool execution using the provided
  `session_fingerprint`.  
- Confidence states: `auto` (≥0.80), `confirm` (0.55–0.79), `pick` (<0.55).  
- Writes auto-confirm only when score ≥0.80; otherwise prompt with “Change basket”.
- Tie-break (Δ<0.06) triggers secondary reflection check or multi-choice UI.

### 3.1 Implementation Rules (Canon)
- Substrate-writing tools (`create_memory_from_chat`, `add_to_substrate`) **must**
  receive a `session_fingerprint` (embedding + summary metadata). Requests without
  embeddings are rejected at the core layer.
- Adapters must validate auth (JWT or integration token) before invoking any tool.
- The fingerprint used for inference should be forwarded to the backend payload for
  auditability.

> **Management Scope:** Basket creation/renaming/anchor editing remains in the
> YARNNN web app. MCP adapters MAY offer lightweight controls (e.g., “switch to
> another basket” or “create new basket for this chat”) but MUST redirect users
> to YARNNN for deeper management. This keeps governance UX centralized.

## 4. Auth & Onboarding Expectations
- Users must have a YARNNN account + workspace (Supabase auth).  
- Claude/Cursor: user pastes integration token into client (generated in web UI).  
- ChatGPT Apps: OAuth flow (Apps SDK) stores credentials server-side.  
- Adapters return CTA “Visit https://yarnnn.com/connect” on 401/missing token.

## 5. Adapter Responsibilities

### 5.1 Anthropic MCP
- Transport: stdio or HTTP/SSE.  
- Response metadata: include `_basket_selection` (confidence info) when available.  
- Error handling: map HTTP 401 → `InvalidRequest` with CTA; other errors → `InternalError`.

### 5.2 OpenAI Apps (scaffold)
- HTTP adapter that will integrate with Apps SDK once OAuth/UI is ready.  
- Should log basket selection intent; eventually register tools with metadata,
  structured responses, and component templates.

## 6. Roadmap Notes
- Implement `config_settings` tool once governance API endpoints are exposed.  
- After Apps SDK OAuth work, surface the same tool catalogue with component-based UI.  
- Add “unassigned inbox” flow for low-confidence writes.  
- Ensure captures/proposals/timeline events carry `source_host` metadata so the UI
  surfaces which platform (Claude, ChatGPT, web, or agents) triggered them.
- Track per-host observability via `mcp_activity_logs` (dashboard status badges rely on the `mcp_activity_host_recent` view).
- Capture user confirmations to improve affinity scoring.

This catalog acts as the canonical reference for tool behaviour regardless of
platform. Update it whenever tool inputs/outputs change or new tools are added.
