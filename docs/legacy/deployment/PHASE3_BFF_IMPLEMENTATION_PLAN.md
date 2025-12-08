# Phase 3: BFF Implementation Plan

## Executive Summary

Phase 3 implements the Backend-for-Frontend (BFF) architectural pattern by establishing HTTP-based communication between Platform API and Substrate API, eliminating direct substrate database access from Platform.

**Current State (Pre-BFF)**:
- Platform API incorrectly contains P0-P4 agent pipeline code
- Both Platform and Substrate access substrate tables directly
- Code duplication and unclear domain boundaries

**Target State (Post-BFF)**:
- **Platform API** = Work/consumer-facing application only
- **Substrate API** = P0-P4 agent pipeline + memory/context domain
- Platform calls Substrate via HTTP only (no direct DB access)

**Key Insight**: Substrate-API already implements **Canon v2.1 Universal Work Orchestration** - perfect foundation for BFF pattern.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Platform API (BFF Layer)                                   │
│  - Work/consumer-facing application (WIP/to-be-built)       │
│  - Business logic for end-user features                     │
│  - Orchestrates Substrate API calls                         │
│                                                              │
│  ┌────────────────────────────────────────┐                │
│  │  HTTP Client (substrate_client.py)     │                │
│  │  - Service-to-service auth             │                │
│  │  - Retry logic & circuit breaker       │                │
│  │  - Response caching                    │                │
│  └────────────────┬───────────────────────┘                │
└───────────────────┼────────────────────────────────────────┘
                    │ HTTP/REST
                    │ (Service Token Auth)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Substrate API (Core Domain)                                │
│  - P0-P4 Agent Pipeline (Capture → Validate → Reflect       │
│    → Compose → Canon)                                       │
│  - Memory blocks, documents, relationships                  │
│  - Embeddings & semantic search                             │
│  - Universal work orchestration (Canon v2.1)                │
│                                                              │
│  ┌────────────────────────────────────────┐                │
│  │  Service Auth Middleware               │                │
│  │  - Validates service tokens            │                │
│  │  - Rate limiting per service           │                │
│  └────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Strategy

### Strategy: **Incremental Migration with Feature Flags**

We'll migrate in phases, maintaining backward compatibility via feature flags. Each service can be migrated independently and rolled back if issues arise.

**Why this approach?**
1. **Risk Mitigation**: Gradual rollout reduces blast radius
2. **Testing**: Each migration can be tested in isolation
3. **Rollback**: Feature flags enable instant rollback without redeployment
4. **Performance**: Monitor latency impact before full migration

---

## Phase 3 Breakdown

### Phase 3.1: Foundation (Week 1)
**Goal**: Establish HTTP communication infrastructure

**Tasks**:
1. Create `platform/api/src/clients/substrate_client.py` - HTTP client for Substrate API
2. Add service-to-service authentication (shared secret or service tokens)
3. Create `substrate-api/api/src/middleware/service_auth.py` - Service auth middleware
4. Add environment variables: `SUBSTRATE_API_URL`, `SERVICE_AUTH_SECRET`
5. Implement health check endpoint call from Platform to Substrate

**Deliverables**:
- Working HTTP client with retry logic
- Service auth middleware protecting Substrate endpoints
- End-to-end health check: Platform → Substrate → DB

---

### Phase 3.2: Core Read Operations (Week 2)
**Goal**: Migrate read-only substrate access to HTTP

**Priority Services** (already exist in Substrate API):
1. **Block Listing**: `GET /baskets/{basket_id}/blocks`
2. **Dump Listing**: `GET /baskets/{basket_id}/inputs`
3. **Work Status**: `GET /api/work/{work_id}/status`

**Platform Files to Migrate**:
- `platform/api/src/app/routes/blocks.py` - Use substrate_client instead of direct DB
- `platform/api/src/app/routes/basket_snapshot.py` - Use substrate_client for blocks/dumps
- `platform/api/src/services/substrate_ops.py` - Wrap with HTTP calls

**Feature Flag**: `USE_SUBSTRATE_HTTP_READS` (default: false)

**Testing**:
```python
# Before migration
blocks = supabase_client.table("blocks").select("*").eq("basket_id", basket_id).execute()

# After migration (with feature flag)
if settings.USE_SUBSTRATE_HTTP_READS:
    blocks = substrate_client.get_basket_blocks(basket_id)
else:
    blocks = supabase_client.table("blocks").select("*").eq("basket_id", basket_id).execute()
```

---

### Phase 3.3: Work Orchestration Migration (Week 3)
**Goal**: Route all substrate mutations through Substrate API's Universal Work Orchestration

**Key Finding**: Substrate API already implements Canon v2.1 work queue system at `/api/work/*` endpoints. Platform should use these instead of direct queue access.

**Substrate Endpoints to Use**:
- `POST /api/work/initiate` - Create new substrate work
- `GET /api/work/{work_id}/status` - Poll work status
- `POST /api/work/{work_id}/retry` - Retry failed work
- `GET /api/work/health` - Queue health

**Platform Services to Migrate**:
1. `services/canonical_queue_processor.py` - Use substrate work API instead of direct queue
2. Agent pipeline processors - Submit work via HTTP
3. Background jobs - Use substrate work endpoints

**Migration Pattern**:
```python
# Before (direct queue access)
queue_item = {
    "basket_id": basket_id,
    "work_mode": "compose_canon",
    "payload": {...}
}
supabase_client.table("agent_processing_queue").insert(queue_item).execute()

# After (HTTP to Substrate API)
work_response = substrate_client.initiate_work(
    basket_id=basket_id,
    work_mode="compose_canon",
    payload={...}
)
work_id = work_response["work_id"]
```

---

### Phase 3.4: Document & Composition Operations (Week 4)
**Goal**: Migrate document composition to Substrate API

**Substrate Endpoints to Use**:
- `POST /api/documents/compose-contextual`
- `POST /api/documents/agents/compose-document` (P4 agent)
- `GET /api/documents/{document_id}/context-analysis`
- `POST /api/documents/{document_id}/evolve`

**Platform Files to Migrate**:
- `app/documents/services/context_composition.py`
- `app/agents/pipeline/composition_agent.py` (P4)
- `app/routes/p4_canon.py`

**Data Flow**:
```
Platform receives user request
    ↓
Platform validates & enriches request
    ↓
Platform calls Substrate: POST /api/documents/compose-contextual
    ↓
Substrate creates work item in queue
    ↓
Substrate worker processes composition
    ↓
Platform polls: GET /api/work/{work_id}/status
    ↓
Platform returns result to user
```

---

### Phase 3.5: Semantic Search & Embeddings (Week 5)
**Goal**: Centralize embedding generation and semantic search in Substrate

**New Substrate Endpoints Needed**:
```
POST   /api/substrate/embeddings/generate
  Body: { text: string, model?: string }
  Response: { embedding: float[], dimensions: int }

POST   /api/substrate/search/semantic
  Body: { query_embedding: float[], basket_id?: uuid, limit?: int, filters?: {} }
  Response: { results: [{ block_id, score, content, ... }] }

POST   /api/substrate/search/cross-basket
  Body: { query: string, workspace_id: uuid, limit?: int }
  Response: { results: [...] }
```

**Platform Services to Migrate**:
- `services/semantic_primitives.py` - Use HTTP instead of direct OpenAI + DB
- `services/embedding.py` - Delegate to Substrate
- `jobs/embedding_generator.py` - Use Substrate batch endpoint

**Why This Matters**:
- Embeddings are substrate domain, not platform domain
- Centralized rate limiting for OpenAI API
- Shared embedding cache across services
- Consistent embedding model versions

---

### Phase 3.6: Insights & Reflections (P3) (Week 6)
**Goal**: Use Substrate's existing P3 endpoints instead of direct DB access

**Substrate Endpoints to Use**:
- `POST /p3/insight-canon` - Generate basket insight
- `POST /p3/doc-insight` - Generate document insight
- `POST /p3/timeboxed-insight` - Temporal window insight

**Platform Files to Migrate**:
- `app/routes/p3_insights.py` - Proxy to Substrate instead of direct generation
- `app/agents/pipeline/reflection_agent_canon_v2.py` - Use HTTP endpoints

**Benefit**: P3 reflection logic lives in one place (Substrate), Platform just orchestrates when to call it.

---

### Phase 3.7: Cleanup & Optimization (Week 7)
**Goal**: Remove duplicate code and optimize performance

**Tasks**:
1. **Remove Duplicate Services**:
   - Delete `platform/api/src/services/substrate_ops.py` (replaced by substrate_client)
   - Delete `platform/api/src/services/semantic_primitives.py` (moved to Substrate)
   - Delete `platform/api/src/services/embedding.py` (moved to Substrate)

2. **Remove Direct DB Access**:
   - Search for `supabase_client.table("blocks")` in Platform - should be zero occurrences
   - Search for `supabase_client.table("documents")` - should be zero
   - Search for `supabase_client.table("substrate_relationships")` - should be zero

3. **Optimize HTTP Performance**:
   - Add response caching in substrate_client
   - Implement connection pooling
   - Add circuit breaker for Substrate downtime
   - Monitor latency metrics

4. **Update Documentation**:
   - Update `DEPLOYMENT_GUIDE_V4.md` with Phase 3 completion
   - Document all substrate_client methods
   - Create API contract reference

---

## API Contracts

### Service Authentication

**Option 1: Shared Secret (Simple)**
```python
# Platform request
headers = {
    "Authorization": f"Bearer {SUBSTRATE_SERVICE_SECRET}",
    "X-Service-Name": "platform-api"
}

# Substrate validation
def validate_service_token(token: str):
    return token == os.getenv("SUBSTRATE_SERVICE_SECRET")
```

**Option 2: JWT Service Tokens (Recommended)**
```python
# Platform generates service token
service_token = jwt.encode({
    "service": "platform-api",
    "exp": datetime.utcnow() + timedelta(hours=1)
}, SECRET_KEY, algorithm="HS256")

# Substrate validates
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
assert payload["service"] == "platform-api"
```

---

### Error Handling

**Standard Error Response Format**:
```json
{
  "error": {
    "code": "SUBSTRATE_ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... },
    "retry_after": 30  // Optional: seconds to wait before retry
  }
}
```

**Platform Error Handling**:
```python
try:
    result = substrate_client.get_basket_blocks(basket_id)
except SubstrateAPIError as e:
    if e.is_retryable():
        # Retry with exponential backoff
        result = await retry_with_backoff(lambda: substrate_client.get_basket_blocks(basket_id))
    else:
        # Fall back to cached data or return error to user
        logger.error(f"Substrate API error: {e}")
        raise HTTPException(status_code=503, detail="Substrate service unavailable")
```

---

### Rate Limiting

**Substrate API** should implement per-service rate limiting:
```python
# Example: 1000 requests per minute per service
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    service_name = request.headers.get("X-Service-Name")
    if not rate_limiter.check(service_name, limit=1000, window=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return await call_next(request)
```

---

## Environment Variables

### Platform API (New)
```bash
# Substrate API connection
SUBSTRATE_API_URL=https://yarnnn-substrate-api.onrender.com
SUBSTRATE_SERVICE_SECRET=<shared-secret>
USE_SUBSTRATE_HTTP_READS=true  # Feature flag
USE_SUBSTRATE_HTTP_WRITES=false  # Feature flag (gradual rollout)
SUBSTRATE_REQUEST_TIMEOUT=30  # seconds
```

### Substrate API (New)
```bash
# Service authentication
SUBSTRATE_SERVICE_SECRET=<shared-secret>
ALLOWED_SERVICES=platform-api,chatgpt-app  # Comma-separated
SUBSTRATE_RATE_LIMIT_PER_SERVICE=1000  # requests per minute
```

---

## Migration Checklist

### Pre-Migration
- [ ] Deploy substrate-api with service auth middleware
- [ ] Add `SUBSTRATE_API_URL` to Platform environment
- [ ] Set `USE_SUBSTRATE_HTTP_READS=false` initially
- [ ] Set up monitoring for substrate_client metrics

### Phase 3.1: Foundation
- [ ] Implement substrate_client.py with health_check()
- [ ] Implement service_auth.py middleware
- [ ] Test end-to-end: Platform → Substrate health check
- [ ] Deploy both services

### Phase 3.2: Read Operations
- [ ] Migrate block listing with feature flag
- [ ] Test read performance vs direct DB
- [ ] Enable `USE_SUBSTRATE_HTTP_READS=true` in staging
- [ ] Monitor latency for 24 hours
- [ ] Enable in production if metrics are acceptable

### Phase 3.3: Work Orchestration
- [ ] Migrate queue submissions to POST /api/work/initiate
- [ ] Update polling to use GET /api/work/{work_id}/status
- [ ] Test async work flow end-to-end
- [ ] Deploy and monitor queue health

### Phase 3.4: Document Composition
- [ ] Migrate P4 composition agent
- [ ] Test document creation flow
- [ ] Verify document versioning works correctly

### Phase 3.5: Semantic Search
- [ ] Implement embedding endpoints in Substrate
- [ ] Migrate semantic search in Platform
- [ ] Test cross-basket search
- [ ] Monitor OpenAI API usage

### Phase 3.6: P3 Insights
- [ ] Migrate insight generation
- [ ] Test staleness detection
- [ ] Verify caching behavior

### Phase 3.7: Cleanup
- [ ] Remove duplicate services from Platform
- [ ] Search for any remaining direct substrate DB access
- [ ] Update documentation
- [ ] Remove feature flags (all migrations complete)

---

## Rollback Plan

**If migration causes issues:**

1. **Immediate Rollback** (< 5 minutes):
   ```bash
   # Set feature flags to false
   SUBSTRATE_API_URL="" USE_SUBSTRATE_HTTP_READS=false
   # Restart Platform API
   ```

2. **Investigate** root cause using logs:
   ```python
   logger.error("Substrate API call failed", extra={
       "endpoint": endpoint,
       "status_code": response.status_code,
       "latency_ms": latency,
       "error": error_details
   })
   ```

3. **Gradual Re-enable**:
   - Fix issue in substrate_client or Substrate API
   - Deploy fix
   - Re-enable feature flag for 10% of traffic (if using load balancer)
   - Monitor metrics
   - Gradually increase to 100%

---

## Success Metrics

### Performance
- **Latency P95** < 200ms for read operations (vs ~50ms direct DB)
- **Latency P95** < 500ms for write operations (async, so less critical)
- **Substrate API uptime** > 99.9%

### Code Quality
- **Zero** direct substrate table queries in Platform API
- **Reduced** lines of code in Platform (removed duplicates)
- **Test coverage** > 80% for substrate_client

### Business Impact
- **No regression** in user-facing features
- **Faster** feature development (clear API contracts)
- **Independent** service deployments (Platform can deploy without touching Substrate)

---

## Timeline

| Week | Phase | Key Deliverable |
|------|-------|----------------|
| 1 | 3.1 Foundation | HTTP client + service auth working |
| 2 | 3.2 Read Ops | Block/dump reads via HTTP |
| 3 | 3.3 Work Queue | All mutations via Substrate work API |
| 4 | 3.4 Documents | Document composition via HTTP |
| 5 | 3.5 Embeddings | Semantic search centralized |
| 6 | 3.6 Insights | P3 reflections via HTTP |
| 7 | 3.7 Cleanup | Zero direct substrate access in Platform |

**Total Duration**: 7 weeks (can be accelerated with parallel work)

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize** which phases are most critical
3. **Create** detailed implementation tickets for Phase 3.1
4. **Set up** monitoring/alerting for substrate_client metrics
5. **Begin** Phase 3.1 implementation
