# YARNNN Batch Ingestion Spec (Canon v2.0)

Version: 1.0.0
Status: Authoritative
Last Updated: 2025-09-10

## Purpose
Define a single request that captures N heterogeneous inputs (text, files) and ensures they are processed coherently as one batch for P1 extraction and governance.

## Sacred Pathways
- P0 Capture: `/api/baskets/ingest` (preferred for batch) or repeated `/api/dumps/new` calls with the same `batch_id`.
- P1 Governance: Batch grouping by `source_meta.batch_id` enables cross-dump extraction and a unified proposal.
- P2 Graph: Relationships created after substrate commit.

## Request (Client → Server)
POST `/api/baskets/ingest`
- Accepts `idempotency_key`, optional `basket.name`, and `dumps[]` with `dump_request_id`, `text_dump?`, `file_url?`, `meta?`.
- Optionally include `batch_id` and `comprehensive_review` in the POST body; the server adds them to each dump’s `source_meta`.

Example
```
{
  "idempotency_key": "uuid",
  "basket": { "name": "EV Pilot" },
  "batch_id": "share_update_2025_09_10_001",
  "comprehensive_review": true,
  "dumps": [
    { "dump_request_id": "uuid-1", "text_dump": "..." },
    { "dump_request_id": "uuid-2", "file_url": "https://.../brief.pdf" }
  ]
}
```

## Server Behavior
- Creates or replays a basket by idempotency (workspace-scoped).
- Calls `fn_ingest_dumps(p_workspace_id, p_basket_id, p_dumps jsonb)` once, passing all enriched dumps.
- Emits `dump.created` events for new dumps (in DB function).
- Insert trigger `queue_agent_processing` enqueues each dump in `agent_processing_queue`.

## Batch Grouping (P1)
- The batch processor groups dumps by `raw_dumps.source_meta->>batch_id` and uses `P1SubstrateAgentV2` in batch mode to:
  - Analyze all dumps together
  - Create a single, unified governance proposal (Extraction) with structured blocks and sparse, high-confidence context_items
  - Proposal provenance lists contributing dump_ids

## Governance Fairness (v2)
- Dedup context_items by (kind|label) and cap volume per proposal
- Prefer ~10–12 blocks per batch; ~25–35 context_items
- Stricter auto-approve thresholds prevent noisy auto-execution
- Failed auto-exec proposals revert to PROPOSED for review (no auto-REJECT)

## Definition of Done
- A single request ingests N dumps; each dump has `source_meta.batch_id`.
- P1 groups by batch_id and emits a single, reviewable Extraction proposal.
- Subsequent batches evolve substrate via Create/Revise/Merge and link to existing blocks.

## References
- `web/app/api/baskets/ingest/route.ts`
- `web/lib/server/ingest.ts`
- `supabase/functions/fn_ingest_dumps.sql`
- `api/src/services/canonical_queue_processor.py`
- `api/src/app/agents/pipeline/governance_processor_v2.py`

