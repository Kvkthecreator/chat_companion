# Yarnnn Canon — Alerts & Notifications (v1.0)

## Scope & Purpose

Governs all user-facing system alerts and product notifications. APIs may change; event contracts must remain stable.

## Taxonomy (Domains)

- **system_alert** - auth, billing, offline, quotas, maintenance
- **action_result** - direct response to user action  
- **job_update** - started|progress|succeeded|failed
- **collab_activity** - changes by others you care about
- **validation** - always inline; never toast

*(Audit log is separate; not a notification surface)*

## Severity

`info` | `success` | `warning` | `error`

## UI Policy Matrix (MUST follow)

| Type | Default UI | Toast? | Persist? |
|------|-----------|--------|----------|
| **system_alert** | Banner (sticky until fixed) | Optional entrance toast | Yes (until resolved) |
| **action_result** | Inline near control | Only if cross-context | No |
| **job_update** | Inline "started…", then toast | Yes for started/succeeded/failed | Failures only |
| **collab_activity** | Badge/counter + Activity list | Sometimes (highly relevant only) | Usually yes |
| **validation** | Inline help/error | Never | No |

## Event Envelope (v1)

```json
{
  "id": "evt_…",
  "v": 1,
  "type": "job_update|system_alert|action_result|collab_activity|validation",
  "name": "brief.compose|block.create|…",
  "phase": "started|progress|succeeded|failed",
  "severity": "info|success|warning|error",
  "message": "Human-readable message",
  "correlation_id": "req_…",
  "scope": { "workspace_id": "…", "basket_id": "…", "entity_id": "…" },
  "dedupe_key": "name:scope[:job_id]",
  "ttl_ms": 4000,
  "payload": { "job_id": "…", "progress": 0.35 },
  "created_at": "ISO8601"
}
```

## HTTP Response Envelope (Controllers → Client)

```json
{
  "ok": true,
  "data": {},
  "notifications": [ <Event Envelope> ],
  "correlation_id": "req_…"
}
```

Long tasks return 202 Accepted:
```json
{ 
  "ok": true, 
  "accepted": true, 
  "job_id": "…", 
  "correlation_id": "req_…" 
}
```

## Transport Rules

1. Every request carries/echoes `X-Correlation-Id`
2. Long tasks must publish `job_update` via `app_events` (Supabase Realtime)

## Presentation Rules

1. **Inline first**; toast only for cross-context & async job transitions
2. **Single ToastHost** at root; queue, dedupe by `dedupe_key`, throttle to 3 visible

## Persistence Rules

Persist system alerts and job failures in `app_events` (Activity surface). Not all events are persisted.

## Ownership & Change Process

Changes require Canon PR + version bump (v1.1, v2.0 if breaking).

## SLIs (initial)

- 95% of `job_update.succeeded` UI-visible < 3s
- Duplicate toast rate < 1% per session

## Security & Privacy

Enforce workspace/basket scoping; no cross-tenant leaks.

## Implementation References

- Event Types: `/web/lib/events/types.ts`
- Event Store: `/web/lib/events/store.ts`
- Toast Host: `/web/components/notifications/ToastHost.tsx`
- API Client: `/web/lib/api/apiClient.ts`
- Realtime: `/web/lib/events/realtime.ts`

## Version History

- **v1.0** (2024-01-24) - Initial Canon establishing unified event system