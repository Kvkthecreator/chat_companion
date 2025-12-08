# MCP Observability + Notification Roadmap

## Goals
- Track ambient MCP activity end-to-end (per host, per tool) with auditable metrics. *(Raw activity logging landed in `mcp_activity_logs`; dashboard and `/api/alerts/current` now surface host health + queue pressure.)*
- Surface service health in the Control Tower dashboard and a public status page.
- Replace the legacy notification plumbing with an ambient-first alert loop (queues → notifications → governance).

## Instrumentation
1. **Structured logs**
   - Emit `mcp_request` events from Claude/OpenAI adapters with: `workspace_id`, `host`, `tool`, `latency_ms`, `result`, `basket_id`, `confidence`, `error_code`.
   - Forward to Supabase `logs` or external sink (Logflare/DataDog); enforce retention.
2. **Database metrics**
   - Add nightly rollups for `mcp_unassigned_captures`, `proposals` by `source_host`.
   - Create materialized view for dashboard cards (`integration_status`, `pending_counts`, `last_seen_per_host`).
3. **Tracing hooks**
   - Tag FastAPI endpoints (`/api/mcp/baskets/infer`, `/api/memory/unassigned`) and Supabase RPCs with request IDs and propagate to adapters.

## Dashboard Enhancements
- **Status badge**: summarise latency & error rate thresholds (green <500 ms p95 & <1% error, amber otherwise).
- **Activity chart**: sparkline of last 24 h MCP calls per host with basket confidence breakdown.
- **Incident feed**: link to status page + show live incidents (manual entry or pulled from Statuspage).

## Notification System Reset
1. **Decommission legacy queue**
   - Audit `/api/user/alerts` usage; archive or remove unused components.
2. **New alert pipeline**
   - Trigger when:
     - unassigned queue > threshold,
     - proposal stuck > SLA,
     - host dormant > N hours,
     - adapter error spikes.
   - Deliver via email + in-app banner tied to workspace governance settings.
3. **User preferences**
   - Simple settings: `critical` (always on), `summary` (daily digest), `mute` per host.

## Operations
- Stand up `/status` endpoint (API + web) fed by health checks and incident log.
- Define alert escalation runbook (Slack pager, email tree) and document in `docs/OPERATIONS_RUNBOOK.md` (to create).
- Add cron/scheduled job to vacuum resolved unassigned captures & archive metrics.

## Sequencing
1. Implement adapter logging + DB rollups.
2. Build status badge & activity chart on dashboard.
3. Ship new notification pipeline and UI.
4. Launch public status page + operations runbook.
