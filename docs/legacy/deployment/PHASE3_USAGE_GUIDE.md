# Phase 3 BFF Usage Guide

## Quick Start

The BFF (Backend-for-Frontend) infrastructure is now in place. Platform API can communicate with Substrate API via HTTP.

### Environment Setup

**Platform API** needs these environment variables:
```bash
SUBSTRATE_API_URL=https://yarnnn-substrate-api.onrender.com
SUBSTRATE_SERVICE_SECRET=<your-shared-secret>
```

**Substrate API** needs these (service auth is **disabled by default**):
```bash
ENABLE_SERVICE_AUTH=false  # Set to "true" to enable
SUBSTRATE_SERVICE_SECRET=<your-shared-secret>
ALLOWED_SERVICES=platform-api,chatgpt-app
```

### Using the Substrate Client

#### Option 1: Direct Usage (Simple)

```python
from clients.substrate_client import get_substrate_client

# Get singleton client
client = get_substrate_client()

# Health check
health = client.health_check()
print(health)  # {"status": "ok"}

# Get blocks for a basket
blocks = client.get_basket_blocks(
    basket_id="123e4567-e89b-12d3-a456-426614174000",
    states=["ACCEPTED", "LOCKED"]
)

# Initiate work via Universal Work Orchestration
work = client.initiate_work(
    basket_id="123e4567-e89b-12d3-a456-426614174000",
    work_mode="compose_canon",
    payload={"document_intent": "product_brief"}
)
work_id = work["work_id"]

# Poll work status
status = client.get_work_status(work_id)
print(status["state"])  # "pending", "processing", "completed", "failed"
```

#### Option 2: Context Manager (Resource Cleanup)

```python
from clients.substrate_client import SubstrateClient

with SubstrateClient() as client:
    blocks = client.get_basket_blocks(basket_id)
    # HTTP connection automatically closed
```

#### Option 3: Convenience Functions

```python
from clients.substrate_client import health_check, get_basket_blocks, initiate_work

# Direct function calls
health = health_check()
blocks = get_basket_blocks(basket_id, states=["ACCEPTED"])
work = initiate_work(basket_id=basket_id, work_mode="compose_canon", payload={})
```

### Error Handling

```python
from clients.substrate_client import SubstrateClient, SubstrateAPIError

client = SubstrateClient()

try:
    blocks = client.get_basket_blocks(basket_id)
except SubstrateAPIError as e:
    # Structured error with details
    print(f"Status: {e.status_code}")
    print(f"Message: {e.message}")
    print(f"Details: {e.details}")

    # Check if retryable
    if e.is_retryable():
        # Automatic retries already happened (3 attempts)
        # This is a persistent failure
        logger.error("Substrate API unavailable after retries")
    else:
        # Client error (4xx) - don't retry
        logger.error("Invalid request to Substrate API")
```

### Circuit Breaker

The client has a built-in circuit breaker to prevent cascading failures:

```python
# Circuit states:
# - CLOSED: Normal operation (all requests allowed)
# - OPEN: Too many failures (requests blocked for cooldown)
# - HALF_OPEN: Testing recovery (limited requests allowed)

try:
    result = client.health_check()
except SubstrateAPIError as e:
    if "circuit breaker is OPEN" in e.message:
        # Service is down, circuit is protecting us
        # Fall back to cached data or return error to user
        return cached_blocks
```

### Available Methods

#### Health & Status
- `health_check()` - Basic health check
- `work_queue_health()` - Queue health metrics

#### Blocks (Read-Only)
- `get_basket_blocks(basket_id, states=None, limit=None)` - List blocks

#### Work Orchestration (Canon v2.1)
- `initiate_work(basket_id, work_mode, payload, user_id=None)` - Submit work
- `get_work_status(work_id)` - Get work status
- `retry_work(work_id)` - Retry failed work

#### Documents
- `compose_document(basket_id, context_blocks, composition_intent=None)` - Compose document

#### Raw Dumps / Inputs
- `get_basket_inputs(basket_id)` - List dumps
- `create_dump(basket_id, content, metadata=None)` - Create dump

#### Insights (P3)
- `generate_insight_canon(basket_id, force_regenerate=False)` - Generate insight

## Testing

Run the test suite to validate BFF infrastructure:

```bash
# Set environment variables
export SUBSTRATE_API_URL=https://yarnnn-substrate-api.onrender.com
export SUBSTRATE_SERVICE_SECRET=your-secret

# Run tests
python test_bff_foundation.py
```

Expected output:
```
🚀 Phase 3.1 BFF Foundation Test Suite

Test 1: Health Check
✅ Health check passed: {'status': 'ok'}

Test 2: Work Queue Health
✅ Work queue health check passed

Test 3: Circuit Breaker
✅ Circuit breaker correctly blocked request

Test 4: Service Authentication
✅ Service authentication passed

Total: 4/4 tests passed
🎉 All tests passed! BFF foundation is working.
```

## Migration Example

**Before (Direct DB Access)**:
```python
# platform/api/src/app/routes/blocks.py
from app.utils.supabase_client import supabase_client

def get_blocks(basket_id: str):
    result = supabase_client.table("blocks")\
        .select("*")\
        .eq("basket_id", basket_id)\
        .eq("state", "ACCEPTED")\
        .execute()
    return result.data
```

**After (HTTP via Substrate API)**:
```python
# platform/api/src/app/routes/blocks.py
from clients.substrate_client import get_substrate_client

def get_blocks(basket_id: str):
    client = get_substrate_client()
    blocks = client.get_basket_blocks(
        basket_id=basket_id,
        states=["ACCEPTED"]
    )
    return blocks
```

## Feature Flag Pattern (Gradual Rollout)

For safe migration, use feature flags:

```python
import os
from clients.substrate_client import get_substrate_client
from app.utils.supabase_client import supabase_client

USE_SUBSTRATE_HTTP = os.getenv("USE_SUBSTRATE_HTTP_READS", "false").lower() == "true"

def get_blocks(basket_id: str):
    if USE_SUBSTRATE_HTTP:
        # New: via HTTP
        client = get_substrate_client()
        return client.get_basket_blocks(basket_id, states=["ACCEPTED"])
    else:
        # Old: direct DB
        result = supabase_client.table("blocks")\
            .select("*")\
            .eq("basket_id", basket_id)\
            .eq("state", "ACCEPTED")\
            .execute()
        return result.data
```

Then in render.yaml:
```yaml
envVars:
  - key: USE_SUBSTRATE_HTTP_READS
    value: "true"  # Enable when ready
```

## Performance Considerations

**Latency**:
- Direct DB: ~50ms
- HTTP via Substrate: ~200ms (includes network + auth)

**Mitigation**:
- Connection pooling (enabled by default)
- Response caching (future enhancement)
- Batch requests (future enhancement)

**When to Use BFF**:
- ✅ Non-latency-critical operations
- ✅ Complex substrate operations (composition, semantic search)
- ✅ Operations that benefit from centralized logic
- ❌ Hot path queries (consider caching)

## Troubleshooting

### "circuit breaker is OPEN"
**Cause**: Substrate API is down or unresponsive
**Solution**: Check Substrate API health, wait for cooldown (60s), service will auto-recover

### "Invalid service token"
**Cause**: `SUBSTRATE_SERVICE_SECRET` mismatch
**Solution**: Ensure both Platform and Substrate have same secret

### "Missing Authorization header"
**Cause**: Service auth enabled but client not configured
**Solution**: Set `SUBSTRATE_SERVICE_SECRET` in Platform env vars

### "Rate limit exceeded"
**Cause**: Too many requests (>1000/min default)
**Solution**: Increase `SUBSTRATE_RATE_LIMIT_PER_SERVICE` or implement backoff

## Next Steps

See [PHASE3_BFF_IMPLEMENTATION_PLAN.md](PHASE3_BFF_IMPLEMENTATION_PLAN.md) for complete migration roadmap:

- **Phase 3.2**: Migrate read operations (blocks, dumps, snapshots)
- **Phase 3.3**: Route all mutations via Universal Work API
- **Phase 3.4**: Document composition via HTTP
- **Phase 3.5**: Semantic search & embeddings
- **Phase 3.6**: P3 insights
- **Phase 3.7**: Final cleanup (remove all direct substrate DB access)

## Status: Stable Landing Ground ✅

The BFF infrastructure is production-ready:
- ✅ HTTP client with resilience patterns
- ✅ Service authentication (optional, disabled by default)
- ✅ Circuit breaker & retries
- ✅ Comprehensive test suite
- ✅ Environment variables configured in render.yaml
- ✅ Migration patterns documented

**You can now deploy both services and start migrating operations incrementally.**
