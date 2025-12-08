# MCP Integration Launch Checklist

This checklist captures the hardening work needed to operate YARNNN as a
service-level integration on ChatGPT (Apps SDK) and Claude. It supplements the
architecture and tool catalog docs with operational requirements.

## 1. Security & Governance
- **Auth enforcement:** All requests require a Supabase JWT or integration
  token. Rotate tokens quarterly and provide user-facing revocation controls.
- **Governance defaults:** New workspaces start in `review_all` mode. Auto
  approval is opt-in and must be surfaced in the integrations settings UI.
- **Consent copy:** Before every write, the adapter must surface a clear
  confirmation (“Summarize & store this thread to <basket>?”). Reads may include
  a lightweight banner.
- **Adapter secrets:** MCP server-to-backend communication uses
  `MCP_SHARED_SECRET`; rotate it alongside service tokens and distribute via
  Render environment variables only.
- **Undo window:** Maintain an API to undo the last write (10-minute retention)
  and surface it in notifications.

## 2. Reliability & Rate Limits
- **SLO targets:** 99.9% monthly uptime and p95 < 800 ms for read tools.
- **Rate limits:** Enforce per-token QPS (e.g., 10 req/s burst 30). Return
  `429` with `Retry-After` headers; adapters should relay the message to users.
- **Timeout budget:** Guard long-running operations. Replies after 30s must be
  async (job ID or SSE progress updates).
- **Observability:** Log host (`chatgpt` or `claude`), tool name, duration (
  p50/p95), error codes, and basket decisions. Ship metrics to the monitoring
  stack before public pilots.

## 3. Platform-Specific Work
- **ChatGPT Apps:**
  - Build the custom UI bundle (`npm --prefix mcp-server/adapters/openai-apps/ui run build`).
  - Implement OAuth code exchange + Supabase token storage (pending).
  - Prepare discovery prompts and connector metadata (≤200 characters) for
    submission when the app directory opens.
- **Claude MCP:**
  - Publish an “Add Yarnnn to Claude” guide with endpoint URL, auth header
    format, and smoke-test instructions.
  - Document org rollout steps (provision tokens, set default baskets, audit
    logs).

## 4. Documentation & Support
- **Status page:** Publicly report incidents and planned maintenance.
- **Support channel:** Provide contact information for tenant admins during
  review submissions.
- **Release notes:** Maintain a change log for adapters, noting schema changes
  or new tools.

Keep this checklist in sync as we move from private pilots to GA. Every launch
review (internal or platform) should confirm these boxes are checked.
