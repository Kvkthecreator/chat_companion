# YARNNN External Sharing & Integrations — Thought Paper

Version: 0.1.0
Status: Future (Not Implemented)
Last Updated: 2025-09-09

## Purpose
Outline a canon-compliant approach for publishing and integrating documents with external systems while preserving strict substrate/artifact boundaries. This is a forward-looking scaffold for future implementation — not a commitment or spec.

## Non‑Goals (Explicit)
- No substrate writes from integrations (ever).
- No artifact recursion (reflections-about-reflections, documents-of-documents).
- Not an implementation spec; details may change.

## Canon Principles (Applied)
- Publish snapshots only: integrations operate on `document_versions`, not live documents.
- Artifact plane only: connectors read immutable versions and metadata; they never mutate substrate.
- Provenance preserved: exports include a JSON manifest of substrate references for traceability.
- Workspace isolation: access control and auditing remain enforced.

## Core Concepts

### 1) Publishable Snapshots
- Lock a document into an immutable `document_version` ("publishable" flag and `version_hash`).
- Optional: mark a version as "published" for external distribution while retaining prior versions.

### 2) Artifact Outbox Pattern
Tables (future):
- `artifact_outbox` — queue of publish jobs
  - `id`, `document_version_id`, `target` (e.g., `markdown_file`, `slack`, `confluence`, `custom_webhook`), `status` (`pending|claimed|processing|completed|failed`), `attempts`, `error`, `payload_manifest`, `created_at`, `updated_at`, `correlation_id`.
- `external_publications` — records per successful publish
  - `id`, `document_version_id`, `target`, `external_id_or_url`, `published_at`, `checksum`, `meta`.

### 3) Manifests & Rendering
- Rendered content formats: `html`, `md`, `pdf` (future), plus a `manifest.json`.
- Manifest fields (indicative):
  - `document_version`: `{ id, version_hash, title, created_at }`
  - `references`: array of `{ substrate_type, substrate_id, role, weight, snippets[], provenance, checksum? }`
  - `workspace_id`, `basket_id`, `source_document_id`
  - `render`: `{ format, checksum, bytes }` (checksum only if bytes not inlined)
  - `integrity`: `{ coverage_percent, reference_counts_by_type }`

### 4) Security & Access Control
- Signed, time-limited URLs for rendered assets and manifests.
- Connector tokens scoped to workspace with least privilege.
- Audit events on create/claim/complete/fail for outbox jobs.
- No direct DB access for external services; use API with RLS-backed views or worker credentials.

### 5) Events (Minimal Vocabulary)
- `doc.version_locked` — document fixed into `document_version`.
- `doc.version_published` — publish initiated/confirmed.
- `integration.sent|succeeded|failed` — outbox lifecycle events.

## API Surfaces (Future Sketch)
- `POST /api/documents/:id/lock` → returns `document_version_id` (no external side effects).
- `POST /api/integrations/publish` → body: `{ document_version_id, target }` → enqueues outbox job.
- `GET /api/integrations/outbox?status=pending&limit=...` → connector polling (internal).
- `POST /api/integrations/outbox/:id/claim` → atomic claim by connector worker.
- `POST /api/integrations/outbox/:id/complete` → finalize, create `external_publications` record.
- `GET /api/artifacts/document-versions/:id/render?format=html|md&manifest=1` → signed, ephemeral.

All endpoints are artifact-plane only and must not mutate substrate tables.

## Workflow (Happy Path)
1) Author/compose document (artifact).
2) Lock version → `document_version` created; emit `doc.version_locked`.
3) Enqueue publish → `artifact_outbox(pending)`.
4) Connector claims job; fetches render + manifest via signed URLs.
5) Push to target; on success: mark completed, write `external_publications`; emit `integration.succeeded`.

## Governance & Canon Boundaries
- P4 may lock/publish versions and enqueue outbox entries.
- Connectors must never call P1/P2 RPCs or write to substrate tables.
- Reflections may target `document_versions` for analytics, but are not exported as authoritative content.

## Open Questions
- Idempotency: deduplicate publishes by `(document_version_id, target)`.
- Revocation: how to signal downstream recall/update of published artifacts.
- Drift policy: behavior when referenced substrate changes post-publication.
- Long-term access: TTLs for signed links and archival strategy for renders.
- Checksum standards: manifest, render content, and reference set hashing.

## Phased Delivery (Future)
1) Lock & Render: implement `document_version` locking + render service with manifest.
2) Outbox MVP: `artifact_outbox` table + polling connector shim.
3) Targets: Markdown export (download) → Slack/Email webhook → Confluence.
4) Publication Registry: `external_publications` + recall hooks.
5) Observability: events, dashboards, failure retry strategy.

## Testing Notes (When Implemented)
- Verify artifact-only operations (no substrate writes) via RPC allow-lists.
- Ensure manifests match references; checksums stable across re-renders of same version.
- Enforce idempotent publish behavior per version/target.

---

This document is intentionally non-binding and not implemented. It exists to capture future integration patterns aligned with YARNNN canon so we can revisit with clear boundaries once document modes are hardened.

