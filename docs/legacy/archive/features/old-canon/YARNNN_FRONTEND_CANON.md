# Yarnnn Frontend Canon (Ambient v2)

## Core Principles
- **Ambient-first**: Users spend most time in Claude/ChatGPT; the web app operates as the governance/control surface.
- **Pure substrate composition**: Capture (P0/P1) and governance remain basket-scoped; documents (P4) only reference substrate.
- **Contracts and RLS everywhere**: All data flows through shared contracts with workspace-level row security.

## User-facing Surfaces
1. **Control Tower (`/dashboard`)**
   - Integration health (Claude & ChatGPT)
   - Global queues (Unassigned captures, Pending proposals)
   - Recent ambient activity summaries

2. **Unassigned Queue (`/memory/unassigned`)**
   - Low-confidence MCP captures awaiting human routing
   - Assign basket or dismiss capture before proposals run

3. **Integrations Settings (`/dashboard/settings`)**
   - Token generation + status for Claude and ChatGPT
   - Links to integration guides

4. **Context Library (`/baskets`)**
   - Directory of baskets with mode, last activity, pending proposal counts
   - Jump into basket views for anchors, blocks, timelines, governance, documents

## Basket Pages (Deep Curation)
- **Memory**: capture history, anchors, blocks
- **Governance**: proposal queue, approval workflow
- **Timeline**: audit trail including governance events
- **Documents**: P4 artifacts with Read / Analyze / Compare tabs, plus composition instructions

### Documents Surface
- Pin the canonical artifacts at the top: Basket Context Canon, Prompt Starter. Show regenerate buttons when health checks fail.
- Document creation modal gathers intent and optional template selection; after submit, navigate to the document detail page with a “Composing…” banner.
- Detail page tabs:
  - **Read**: renders latest `document_version`, references, and optional export actions.
  - **Analyze**: displays structured metrics, doc insight (themes/tensions/actions), freshness status, and recomposition controls.
  - **Compare**: exposes version history and diffs.
- Document insight regeneration is triggered automatically when a new version arrives; manual refresh button available in Analyze tab.

## Governance & Queue Integration
- MCP writes call basket inference. `auto` runs instantly, `confirm` prompts, `pick` creates an Unassigned capture.
- All substrate mutations still pass through governance policies; dashboard and basket views surface pending proposals with origin metadata (ambient vs manual).

## Development Pointers
- Use contracts in `shared/` for all API↔UI interactions.
- Follow the control-tower navigation (Dashboard → Unassigned → Integrations → Baskets) for new features.
- Canon health (insight, document, prompt starter) is enforced client-side: the banner component calls `/api/health/basket/:id` and auto-triggers regeneration when required artifacts are missing or stale.
- Keep documentation guides in `/docs/integrations/*` in sync with UI changes.

That’s the canon: ambient control surfaces for triage and integration status, basket views for deep context, and substrate/governance purity underneath.
