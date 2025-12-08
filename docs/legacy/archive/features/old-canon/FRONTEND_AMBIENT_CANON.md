# Frontend Ambient Canon

This note captures the UI principles for Yarnnn as an ambient MCP service.

## Control Tower vs Context Library
- **Dashboard** (“Control Tower”) is the ambient home: integration health, global
  queues (Unassigned, Governance), alerts, and quick jumps. All workspace-wide
  triage starts here.
- **Baskets** remain the per-context workspace. `/baskets` is now the "Context
  Library" listing baskets with their ambient activity (mode, last activity,
  pending proposals). Individual basket pages provide deep curation (anchors,
  blocks, timeline, proposals).

## Navigation Rules
- Primary sidebar order: Dashboard → Unassigned queue → Integrations → Baskets →
  Governance. Baskets are quick entry points; ambient triage happens before
  entering a basket.
- Dashboard widgets show live counts (unassigned captures, pending proposals) with
  links into detailed views.

## Queues
- **Unassigned Captures**: low-confidence MCP writes. Captures store fingerprint,
  payload, and basket candidates. Users assign or dismiss them.
- **Governance**: proposals pending review surface in dashboard summaries and in
  per-basket governance views.

## Integrations
- Settings → Integrations shows connection state for Claude and ChatGPT plus token
  management. The same status cards mirror on the dashboard.

Use this document when adjusting the navigation or adding new ambient surfaces to
ensure UI changes follow the control-tower + context-library model.
