Canon v1.3.1 — docs clarification (no code change)
Aligns reflections (derived + optional cache), sacred write path endpoints, DTO wording (file_url), schema term context_blocks, basket lifecycle, and event tokens.

## Yarnnn Interface Spec — Basket Create & Dump Ingest (v0.1.0)
Last updated: 2025-08-15 (Asia/Seoul)

## 0) Scope & Versioning
Scope: End-to-end contracts and endpoints for Basket creation and Raw Dump ingestion.
Spec version: v0.1.0 (semver)
Consumers: Web frontend (Next.js), FastAPI server, E2E tests.

The sacred write path is **POST /api/dumps/new** (one dump per call).
**Optional onboarding alias:** **POST /api/baskets/ingest** orchestrates basket + multiple dumps in one transaction; it performs **no additional side-effects** beyond the split endpoints and is idempotent on both the basket and each dump.

**IMPLEMENTED**: This specification has been fully implemented as of 2025-08-15. All features, database migrations, API endpoints, and frontend flows are complete and tested.

Single source of truth: DTOs in `shared/contracts/*` (imported by FE & BE). This doc mirrors those contracts and defines transport semantics. Legacy notes in earlier API docs have been removed so this file remains canonical.

## 1) Global Conventions
Auth: Bearer JWT (Supabase) on all endpoints.
Content-Type: application/json; charset=utf-8
Time: ISO-8601 UTC in payloads/logs.
Idempotency:
idempotency_key (UUID) on Basket Create, unique on (creator_user_id, idempotency_key).
dump_request_id (UUID) on Dump Create, unique on (basket_id, dump_request_id).
Error envelope:
{ "error": { "code": "STRING", "message": "HUMAN_READABLE", "details": { } } }
RLS: All inserts must satisfy workspace membership policies; server derives user_id and workspace_id from auth context (never sent by client).

## 2) Memory Plane APIs

#### Memory Plane
```
GET /api/baskets/{id}/timeline?cursor=...
→ Returns: { items: [{ kind, ts, ref_id, preview, payload }], next_cursor }

GET /api/baskets/{id}/reflections/latest  
→ Returns: { pattern, tension, question, computed_at }
```

## 3) Data Contracts (Shared DTOs)
**IMPLEMENTED**: All DTOs are in `shared/contracts/` and imported by both FE & BE. No inline redefinition.

```typescript
// shared/contracts/baskets.ts exports CreateBasketReq/CreateBasketRes
// shared/contracts/dumps.ts exports CreateDumpReq/CreateDumpRes
// shared/contracts/ingest.ts (optional combined flow)
import type { CreateBasketRes } from "./baskets";
import type { CreateDumpRes } from "./dumps";
export type IngestItem = {
  dump_request_id: string; // UUID
  text_dump?: string;
  file_url?: string;
  meta?: Record<string, unknown>;
};
export type IngestReq = {
  idempotency_key: string; // UUID
  basket?: { name?: string };
  dumps: IngestItem[];
};
export type IngestRes = {
  basket_id: string;
  id: string;
  name: string;
  dumps: CreateDumpRes[];
};
```

**Runtime validation**: Implemented with Zod schemas validating at API boundary.

**Basket schema fields**
- `raw_dump_id` (UUID, nullable): first dump linked to this basket.
- `status` (`basket_state` enum, default `INIT`): lifecycle state of the basket.

## 3) Endpoints (Transport + Semantics)
POST /api/baskets/new
Purpose: Create a basket only. No side effects.
Auth: Required
Request: CreateBasketReq
Response: CreateBasketRes
Idempotency: Replay-safe on (creator_user_id, idempotency_key); returns the original basket_id if called again with same key.
Errors:
400.INVALID_INPUT — malformed UUIDs, missing required fields
409.IDEMPOTENCY_CONFLICT — same (creator_user_id, idempotency_key) but different payload detected (log & block)
Notes: This endpoint must never create dumps or perform any other writes.
POST /api/dumps/new
Purpose: Create exactly one raw dump row.
Auth: Required
Request: CreateDumpReq (must include text_dump or file_url)
Response: CreateDumpRes
Idempotency: Replay-safe on (basket_id, dump_request_id); returns existing dump_id on retry.
Validation:
At least one of text_dump or file_url is required.
basket_id must be accessible to the user via workspace RLS.
Errors:
400.INVALID_INPUT
403.FORBIDDEN
404.BASKET_NOT_FOUND
422.EMPTY_DUMP — neither text_dump nor file_url
(Optional) POST /api/baskets/ingest
Purpose: Atomic create-or-replay basket and create N dumps in a single transaction.
Auth: Required
Request: IngestReq
Response: IngestRes
Semantics: Single DB transaction. Basket is idempotent on idempotency_key. Each dump idempotent on its dump_request_id.
When to use: First-time onboarding to minimize client round-trips. Otherwise prefer the two endpoints above for clarity.

## 4) State Machine & Side Effects
Basket
States: INIT → ACTIVE (first dump attached) → ARCHIVED (future)
Creation does not create dumps or trigger processing.
Empty baskets older than 48h are eligible for cleanup.
Raw Dump
Stateless insert. Optional async enrichment (e.g., OCR, thumbnails) is out-of-band via events/queues; must not affect API success path.

## 5) Security & RLS
All writes must verify workspace membership through Postgres RLS, e.g.:
Baskets: workspace_id IN (SELECT workspace_id FROM workspace_memberships WHERE user_id = auth.uid())
Raw Dumps: enforce that raw_dumps.workspace_id = baskets.workspace_id and user is a member.
Server derives creator_user_id from JWT; client never sends it.
Structured logs at API boundary:
{ "route": "/api/dumps/new", "user_id": "…", "basket_id": "…", "dump_request_id": "…", "action": "created|replayed" }

## 6) Examples
Create Basket (replay-safe)
POST /api/baskets/new
Content-Type: application/json
Authorization: Bearer <jwt>

{
  "idempotency_key": "6f2d4c4e-1b4a-4c4e-9b32-2b9a1e0e8f91",
  "basket": { "name": "Brand Sprint" }
}

200 OK
{ "basket_id": "ba75c8a0-0f1e-4b1d-8c6e-1b2c3d4e5f60" }
Create Dump (file)
POST /api/dumps/new
Content-Type: application/json
Authorization: Bearer <jwt>

{
  "basket_id": "ba75c8a0-0f1e-4b1d-8c6e-1b2c3d4e5f60",
  "dump_request_id": "b8b6b3e1-1a8f-4a41-9d0f-9d3e3f6def0b",
  "file_url": "https://supabase.../user-library/brief.pdf",
  "meta": { "source": "upload" }
}

200 OK
{ "dump_id": "rd_12345678" }
Create Dump (text)
POST /api/dumps/new
{
  "basket_id": "ba75c8a0-0f1e-4b1d-8c6e-1b2c3d4e5f60",
  "dump_request_id": "a4c2e1b7-0a53-4f4a-9f8c-12e67b2dc001",
  "text_dump": "Campaign notes + links..."
}
→ 200 { "dump_id": "rd_98765432" }
Combined Ingest (optional)
POST /api/baskets/ingest
{
  "idempotency_key": "c2a8e0e2-3c9d-4c0d-9c7e-7a2f1d6e90ab",
  "basket": { "name": "Onboarding Ingest" },
  "dumps": [
    { "dump_request_id": "11111111-1111-1111-1111-111111111111", "file_url": "https://.../a.pdf" },
    { "dump_request_id": "22222222-2222-2222-2222-222222222222", "text_dump": "first notes" }
  ]
}
→ 200 { "basket_id": "ba75c8a0-...", "dumps": [{"dump_id": "rd_x"}, {"dump_id": "rd_y"}] }

## 7) Database Changes (SQL)
**IMPLEMENTED**: Migration `supabase/migrations/20250815_add_create_idempotency.sql` applied.

```sql
-- Baskets: add idempotency and uniqueness per creator
ALTER TABLE public.baskets
  ADD COLUMN IF NOT EXISTS idempotency_key uuid;

CREATE UNIQUE INDEX IF NOT EXISTS uq_baskets_user_idem
  ON public.baskets (user_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

-- Raw dumps: per-basket idempotency  
ALTER TABLE public.raw_dumps
  ADD COLUMN IF NOT EXISTS dump_request_id uuid;

CREATE UNIQUE INDEX IF NOT EXISTS uq_dumps_basket_req
  ON public.raw_dumps (basket_id, dump_request_id)
  WHERE dump_request_id IS NOT NULL;
```

-- (Suggested) cleanup job for empty baskets (>48h)
-- Implement as a server cron or SQL scheduled task.
## 8) Client Usage Pattern (Golden Path)
// Pseudocode: single guarded entry point
const inFlight = useRef(false);

async function createBasketAndIngest(items: Array<{ text_dump?: string; file_url?: string; meta?: any }>) {
  if (inFlight.current) return;
  inFlight.current = true;
  try {
    const idem = crypto.randomUUID();
    const { basket_id } = await api.createBasket({ idempotency_key: idem, basket: { name } });

    await Promise.all(items.map(it =>
      api.createDump({
        basket_id,
        dump_request_id: crypto.randomUUID(),
        ...it,
      })
    ));

    router.push(`/baskets/${basket_id}/work`);
  } finally {
    inFlight.current = false;
  }
}

## 9) Definition of Done (Release Gate)
**COMPLETED**: All acceptance criteria met as of 2025-08-15.

✅ FE & BE import the same DTOs from `shared/contracts/*`.  
✅ POST `/api/baskets/new` is side-effect free; idempotent on `(user_id, idempotency_key)`.  
✅ POST `/api/dumps/new` is idempotent on `(basket_id, dump_request_id)`; exactly one dump per call.  
✅ Structured logs at API boundary show `created|replayed` outcomes.  
✅ E2E (Playwright) "golden path" implemented: `tests/idempotency-golden-path.spec.ts`  
   - Create basket → upload 2 files + add 1 text dump → reload → 1 basket, 3 dumps, 0 duplicates.  
⏳ Cleanup policy for empty baskets (>48h) - deferred to future iteration.

## 10) OpenAPI (Optional Stub)
You can generate OpenAPI from these DTOs or maintain a minimal YAML. The DTOs remain canonical.
openapi: 3.0.1
info:
  title: Yarnnn API
  version: v0.1.0
paths:
  /api/baskets/new:
    post:
      summary: Create basket (idempotent)
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CreateBasketReq' }
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema: { $ref: '#/components/schemas/CreateBasketRes' }
  /api/dumps/new:
    post:
      summary: Create dump (idempotent, single)
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CreateDumpReq' }
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema: { $ref: '#/components/schemas/CreateDumpRes' }
components:
  schemas:
    CreateBasketReq:
      type: object
      required: [idempotency_key]
      properties:
        name: { type: string }
        idempotency_key: { type: string, format: uuid }
    CreateBasketRes:
      type: object
      properties:
        basket_id: { type: string, format: uuid }
    CreateDumpReq:
      type: object
      required: [basket_id, dump_request_id]
      properties:
        basket_id: { type: string, format: uuid }
        dump_request_id: { type: string, format: uuid }
        text_dump: { type: string }
        file_url: { type: string }
        meta: { type: object, additionalProperties: true }
    CreateDumpRes:
      type: object
      properties:
        dump_id: { type: string }

## 11) Change Log
**v0.1.0 (2025-08-15)**: ✅ **IMPLEMENTED** - Full Interface Spec covering:
- Basket Create API with idempotency via `idempotency_key`
- Dump Create API with idempotency via `dump_request_id`  
- Optional combined Ingest API (future)
- Database migrations: partial unique indices for replay-safe operations
- Shared TypeScript contracts: `shared/contracts/{baskets,dumps,ingest}.ts`
- Frontend: UUID generation, in-flight guards, per-file fan-out
- RLS enforcement and structured boundary logging
- E2E test coverage: golden-path idempotency validation
- Error standardization with spec-compliant codes