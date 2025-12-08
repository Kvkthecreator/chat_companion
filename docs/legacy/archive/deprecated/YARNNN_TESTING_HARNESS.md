# YARNNN Testing Harness — Canon Smoke and Quality Checks

Purpose: provide repeatable, low‑friction checks for P0→P1 (and optional P2), aligned with the canon. Designed to run locally or in CI with the same env.

## Environment

Required env for scripts using the service role (internal verification):

```
SUPABASE_URL=…
SUPABASE_ANON_KEY=…
SUPABASE_SERVICE_ROLE_KEY=…
YARNNN_TEST_WORKSPACE_ID=31ee30fe-6ae3-4604-ab6d-ac9b9f06dfde
```

Optional tuning:
- `YARNNN_P1_CONFIDENCE_MIN` (default `0.70`)
- `YARNNN_WAIT_PROPOSALS_SEC` (default `30`)

Note: The workspace ID above is the shared test workspace you provided. If you prefer isolation, set `YARNNN_TEST_WORKSPACE_ID` to a different workspace for future runs.

## Canon Smoke: P0 + P1 Quality

Script: `scripts/canon_p0_p1_quality_suite.py`

What it does:
- Creates a fresh basket in your test workspace.
- Ingests a deterministic dump (P0) using `fn_ingest_dumps`.
- Polls `proposals` for provenance matching the dump.
- Validates P1 canon quality:
  - Only substrate ops in proposal (`CreateBlock`, `CreateContextItem`)
  - No relationships/artifacts in P1 ops
  - Minimum counts (≥1 block, ≥2 context_items)
  - `validator_report.confidence ≥ YARNNN_P1_CONFIDENCE_MIN`

Run:
```
python3 scripts/canon_p0_p1_quality_suite.py
```

Output: JSON summary with basket_id, dump_id, proposal_id, op counts, and confidence.

Optional: best‑effort P2 insert for a single relationship
```
python3 scripts/canon_p0_p1_quality_suite.py --p2
```

Notes:
- If the P1 queue is not running, proposals may not appear in time. In that case, either:
  - Start your agent workers / queue processor; or
  - Use the "existing data" validator: `scripts/test_existing_raw_dump_p1_flow.py` (already present) to confirm P1 behavior on recent dumps.
- For a full E2E (basket, work orchestration, proposals, and substrate verification), see `scripts/test_raw_dump_to_p1_pipeline.py`.

## Frontend P0 Capture Smoke (optional)

If the Next.js server is running, exercise the governed capture path via `/api/dumps/new`:

```
export NEXT_PUBLIC_SUPABASE_URL=$SUPABASE_URL
export NEXT_PUBLIC_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY
export SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY
npm --prefix web run start

curl -s -H 'x-playwright-test: true' -H 'content-type: application/json' \
  -d '{
        "basket_id": "<new-or-existing-basket-uuid>",
        "dump_request_id": "<uuid>",
        "text_dump": "Canon route test"
      }' \
  http://localhost:3000/api/dumps/new
```

Expected: `201` with `{ success: true, route: 'direct' | 'proposal' }` and a corresponding `timeline_events` row (`kind='dump'`).

## P2 Relationships (lightweight)

To validate P2 created edges exist after P1:
- Use `substrate_relationships` count for the new basket
- Or call the P2 agent (when workers are available) or approve proposals, then re‑check

The smoke script supports a best‑effort insert (`--p2`) to validate read paths.

## Reflections (P3) — current mismatch

Recent refactors changed reflections to `reflections_artifact` with RPCs. If your DB migration set has the newer variant, use:
- `POST /api/baskets/[id]/reflections` or `/reflections/latest` (FE routes), or
- `fn_reflection_create_from_substrate(...)` (service‑role RPC)

Action item captured separately: align agent write path with current function signature and add a tiny smoke to compute for one basket.

## CI/Automation

Recommended:
- Add a GitHub Actions job that runs `scripts/canon_p0_p1_quality_suite.py` with secrets, using the provided test workspace.
- Make P1 quality thresholds (confidence, op counts) configurable via env.

## Guarantees Checked vs. Canon
- P0: Sacred write path; no interpretation.
- P1: Proposal‑first substrate evolution; only blocks/context_items; provenance present; validator confidence high.
- P2: (optional) edges exist and readable via `substrate_relationships`.
- Timeline: `dump` events recorded for the action.

