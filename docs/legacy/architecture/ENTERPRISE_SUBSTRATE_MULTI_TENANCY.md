# Enterprise Substrate Multi-Tenancy Notes

_Prepared to capture the current thinking before we commit to any code refactors or deployments._

## 1. Background & Current State

- `substrate-api` serves as the **BFF** for the work-platform (`yarnnn.com`).  
- Auth, users, and workspace membership all live in **one Supabase project** today.  
- The `substrate-api/web` frontend shares the same Supabase anon key and service key; there is no tenant concept.  
- All substrate mutations run through the canonical pipeline (P0 capture → P1 governance). Removing the legacy manager path keeps this invariant.

## 2. Desired Future State

- Run a dedicated enterprise surface (`enterprise.yarnnn.com` / `memory.yarnnn.com`) with **completely separate user management** (think Slack Enterprise Grid, GitHub Enterprise Cloud).  
- Enterprise auth may require different identity providers (SAML/SCIM/Okta) and separate billing.  
- The backend should still be a shared BFF where possible, but with **tenant awareness** so consumer and enterprise data never mix.

## 3. Architectural Options (High-Level)

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| **A. Dual Supabase Projects** (Recommended) | One Supabase instance for consumer, a second for enterprise users. Tenant detection via host/JWT issuer; backend routes to correct project/DB. | Strong isolation, separate auth configs, clear security boundary. | Need tenant-aware middleware and potentially dual DB connections. |
| **B. Single Supabase + tenant flag** | Keep one Supabase project; add `tenant_type` column and special RLS. | Less operational overhead, single auth infra. | Difficult to guarantee isolation, complicated RLS, harder to support custom auth for enterprise. |

Given the requirement for “completely separate” user management, Option A aligns best.

## 4. Decisions Needed Before Coding

1. **Auth Boundary** – Are we committing to two Supabase projects (consumer + enterprise)?  
2. **Tenant Detection** – Should backend infer tenant from host header, JWT issuer, explicit header, or a combination?  
3. **Data Plane Isolation** – Shared Postgres with per-schema data vs entirely separate DATABASE_URLs?  
4. **Enterprise Auth Features** – Do we need SSO/SAML/SCIM in phase 1, or is email/password acceptable?  
5. **Frontend Repo Strategy** – Clone `substrate-api/web` into `web-enterprise` inside the same repo, or spin out a new repo/service?

## 5. Proposed Implementation Outline (Once decisions are locked)

1. **Tenant-Aware Auth Middleware (substrate-api/api)**  
   - Detect tenant via host or JWT issuer.  
   - Validate tokens against the correct Supabase project’s JWT secret.  
   - Attach `request.state.tenant`, `request.state.user_id` for downstream handlers.

2. **Tenant-Aware DB Access**  
   - If using schemas: `SET search_path TO enterprise` vs `public`.  
   - If using separate DBs: route through different connection pools (`DATABASE_URL` vs `ENTERPRISE_DATABASE_URL`).

3. **Route Updates**  
   - Ensure every request-dependent query uses tenant context (consumer vs enterprise).  
   - Keep existing work-platform flows untouched (default tenant = consumer).

4. **Enterprise Frontend**  
   - Copy `substrate-api/web` → `substrate-api/web-enterprise`.  
   - Update branding, env vars (enterprise Supabase URL/anon key), and Vercel config.  
   - Deploy to `enterprise.yarnnn.com` (Vercel custom domain).

5. **Infrastructure / Env Vars**  
   - Add `ENTERPRISE_SUPABASE_URL`, `ENTERPRISE_SUPABASE_JWT_SECRET`, `ENTERPRISE_SUPABASE_SERVICE_ROLE_KEY`, etc.  
   - Configure Render/Vercel secrets for both tenant stacks.  
   - Update CORS allowlist to include the enterprise domain.

## 6. Open Questions / Follow-Ups

- Do we need per-tenant rate limiting / observability?  
- Will enterprise users need shared access to existing consumer baskets (unlikely, but worth confirming)?  
- Should we plan migrations to move certain “premium” workspaces from consumer → enterprise tenant?

## 7. Next Steps

1. Review and confirm the decisions outlined in Section 4.  
2. Once approved, implement tenant-aware auth & DB plumbing in `substrate-api/api`.  
3. Spin up the enterprise frontend deployment and wire it to the new Supabase project.  
4. Document rollout plan (staging/prod) + migration strategy if any existing customers transition to the enterprise stack.

_This document should be revisited before any coding effort, so we can ensure the chosen architecture still meets product, security, and operational requirements._

