# Canon v2.0 — Substrate/Artifact Model
Pure substrate pipelines with separate artifact generation. Clear governance boundaries.

# YARNNN_GUARDRAILS_CANON.md
Version: 2.0
Status: Canon — Substrate/Artifact Enforcement

## Purpose
Make the P0–P4 separation enforceable and auditable: code, database, CI, and secrets. This doc lists controls, how we verify them, and the runbooks to react when something drifts.

---

## 1) Invariants (deny-by-default)
- **P0** only ingests `raw_dumps`.  
- **P1** only mutates pure substrates: `context_items`, `context_blocks`, `proposals`.
- **P2** only mutates `substrate_relationships`.
- **P3** generates artifacts: writes `reflections_artifact` and `document_versions`.
- **P4** composes documents: mutates `documents` and `substrate_references`.
- Cross-pipeline substrate writes forbidden; artifacts generated separately.

Reflections are artifacts stored in reflections_artifact with flexible targeting (substrate or document versions).

---

## 2) Enforcement Matrix

| Layer | Control | Where | How we check |
|---|---|---|---|
| Code | RPC allow-lists per pipeline | `api/pipelines/_rules/rpc_allowlist.json` | `npm run guard:pipelines` (CI required) |
| Code | Import boundaries | ESLint `no-restricted-imports` | `npm run lint` |
| DB | Function-level roles | `supabase/migrations/*_p5_roles.sql` | `\dp` verifies EXECUTE privileges |
| DB | Directed-edge uniqueness | `uq_substrate_rel_directed` | `\d+ substrate_relationships` |
| Events | Kind segregation | `events` (free-form), `timeline_events` (constrained) | Sampling query in runbook |
| Secrets | No secrets in code/logs | Secret scanner + rotation policy | Tooling + checklist below |

---

## 3) CI & Tooling

### RPC allow-list (required)
- Command: `npm run guard:pipelines`
- Blocks PRs if a pipeline calls a forbidden `public.fn_*`.

### ESLint imports (required)
- Disallow cross-pipeline imports except shared read-only libs.

### Secret scanning (required)
- Enable GitHub Advanced Security / Secret Scanning or pre-commit hook (`git-secrets`, `gitleaks`).

---

## 4) Database Roles (principle of least privilege)
Roles:
- `substrate_writer` → P1 RPCs  
- `graph_writer` → P2 RPCs  
- `derived_writer` → P3 cache RPC  
- `presentation_writer` → P4 RPCs

**Provisioning snippet (example):**
```sql
-- Create least-privilege users (rotate secrets out-of-band)
create user p1_app with password 'REDACTED' nologin;  -- or login if used directly
grant substrate_writer to p1_app;

create user p2_app with password 'REDACTED' nologin;
grant graph_writer to p2_app;

create user p3_app with password 'REDACTED' nologin;
grant derived_writer to p3_app;

create user p4_app with password 'REDACTED' nologin;
grant presentation_writer to p4_app;
```

---

## 5) Runbooks & Monitoring

### Pipeline Health
Check the pipeline consumer status:
```bash
curl -s https://yarnnn.com/api/_health/pipelines | jq
```
Expected: `{ p3_consumer: {...}, latest_timeline: {...} }`

### Event Kind Distribution
Query to verify event segregation:
```sql
-- Check events distribution by pipeline
select 
  kind,
  count(*) as events_count,
  date_trunc('day', ts) as day
from public.events 
where ts >= now() - interval '7 days'
group by kind, date_trunc('day', ts)
order by day desc, events_count desc;

-- Verify timeline events use constrained kinds only
select distinct kind from public.timeline_events;
-- Expected: dump, reflection, narrative, system_note
```

### RPC Usage Audit
Check for unauthorized RPC calls:
```sql
-- Look for function calls in logs (if query logging is enabled)
-- This is Supabase/Postgres specific
select 
  log_time,
  message
from pg_log 
where message ~* 'fn_[a-z_]+' 
  and log_time >= now() - interval '1 hour'
order by log_time desc;
```

---

## 6) Violation Response

### Code Violations
1. **RPC Guard Failure**: PR blocked automatically by CI
   - Action: Fix the RPC call or update allowlist with justification
   - Escalation: Architecture review if cross-pipeline call is needed

2. **Import Boundary Violation**: ESLint failure
   - Action: Refactor to use shared utilities or proper pipeline APIs
   - Escalation: Consider if boundary definition needs update

### Database Violations
1. **Unauthorized Function Access**: Role permission denied
   - Action: Check if service is using correct DB user/role
   - Escalation: If access is needed, update role grants with approval

2. **Substrate Relationship Duplicate**: Unique constraint violation
   - Action: Expected behavior - handle gracefully in application
   - Monitoring: Track frequency; high rates may indicate logic bugs

### Secret Violations
1. **Hardcoded Secrets Detected**: Secret scanner alert
   - Action: Rotate affected secrets immediately
   - Action: Remove from code history (`git-filter-branch` or `BFG`)
   - Action: Update secret management process

---

## 7) Compliance Checklist

### Monthly Review
- [ ] Run `npm run guard:pipelines` on main branch
- [ ] Review pipeline health metrics
- [ ] Audit event kind distribution
- [ ] Check for new secret scanning alerts
- [ ] Verify DB role permissions are minimal

### Pre-deployment
- [ ] CI pipeline passes (includes guards)
- [ ] No hardcoded secrets in diff
- [ ] RPC calls match pipeline boundaries
- [ ] Import statements follow boundaries

### Incident Response
- [ ] Identify which pipeline(s) involved
- [ ] Check if violation was in code, DB, or operational
- [ ] Apply immediate containment if needed
- [ ] Root cause analysis and prevention update

---

## 8) Exceptions & Waivers
Rare cases may require cross-pipeline access. Document with:
- Business justification
- Technical alternatives considered
- Security review approval
- Monitoring/alerting plan
- Sunset timeline

**Example waiver record:**
```
Date: 2025-01-01
Waiver: P4 reading from P2 substrate_relationships for document suggestions
Justification: Performance optimization - avoid event round-trip
Review: @security-team, @arch-team
Monitoring: Query frequency dashboard
Sunset: Q2 2025 (replace with dedicated suggestion API)
```

---

## Acceptance
- `npm run guard:pipelines` passes
- ESLint rules enforce import boundaries
- DB roles migration applied successfully
- Health endpoints return valid data
- CI workflow blocks violations in PRs

---

## References
- [YARNNN_SUBSTRATE_RUNTIME.md](./YARNNN_SUBSTRATE_RUNTIME.md) - Pipeline definitions
- [YARNNN_GRAPH_CANON.md](./YARNNN_GRAPH_CANON.md) - Graph semantics
- [GitHub Actions Workflow](../.github/workflows/pipeline-guard.yml) - CI enforcement