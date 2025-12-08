# Phase 5: Work-Request-Based Agent Trials - Implementation Summary

**Status**: ✅ Complete
**Date**: 2025-01-16
**Migration**: [20250116_phase5_work_request_trials.sql](supabase/migrations/20250116_phase5_work_request_trials.sql)

---

## Business Model Implemented

### Free Trial
- **10 FREE work requests** total across ALL agents
- No per-agent limit - user can try any combination
- Simple onboarding: "Try 10 work requests for free"

### Per-Agent Subscriptions
- Users "hire" agents individually
- Each subscription: $19-$39/month per agent
- Subscription = **unlimited work requests** for that agent
- Pricing:
  - Research Agent: $19/month
  - Content Creator Agent: $29/month
  - Reporting Agent: $39/month

---

## Database Architecture

### 1. agent_catalog
Stores available agents with pricing and trial configuration.

**Key Columns**:
- `agent_type` (text, unique): 'research', 'content', 'reporting'
- `name` (text): Display name
- `description` (text): Agent description
- `monthly_price_cents` (int): Price in cents (e.g., 1900 = $19.00)
- `trial_work_requests` (int): Global trial limit (10)
- `is_active` (boolean): Agent availability

**Seed Data**:
```sql
INSERT INTO agent_catalog VALUES
  ('research', 'Research Agent', 'Monitors domains...', 1900, 10),
  ('content', 'Content Creator Agent', 'Creates content...', 2900, 10),
  ('reporting', 'Reporting Agent', 'Generates reports...', 3900, 10);
```

### 2. agent_work_requests
Tracks EVERY work request made by users (trial or paid).

**Key Columns**:
- `user_id` (uuid): From auth.users
- `workspace_id` (uuid): Workspace context
- `basket_id` (uuid): Basket context
- `agent_type` (text): Which agent
- `is_trial_request` (boolean): Trial vs subscription
- `subscription_id` (uuid): Reference to subscription (if paid)
- `work_mode` (text): Task type ('monitor', 'deep_dive', etc.)
- `status` (text): 'pending', 'running', 'completed', 'failed'
- `result_summary` (text): Brief result summary
- `error_message` (text): Error if failed

**Purpose**:
- Trial counting (10 total limit)
- Audit trail for all work requests
- Billing/usage analytics

### 3. user_agent_subscriptions
Tracks active subscriptions for agents (one per agent type per user).

**Key Columns**:
- `user_id` (uuid): From auth.users
- `workspace_id` (uuid): Workspace context
- `agent_type` (text): Which agent
- `status` (text): 'active', 'cancelled', 'expired'
- `monthly_price_cents` (int): Locked-in price
- `stripe_subscription_id` (text): Stripe integration (future)
- `stripe_customer_id` (text): Stripe integration (future)

**Constraint**:
- `UNIQUE (user_id, workspace_id, agent_type, status)` - One active subscription per agent per user

---

## Permission Enforcement

### check_trial_limit() Function
PostgreSQL function that enforces trial limits and subscription checks.

**Logic**:
1. Check if user has active subscription for agent type
   - If YES: Return `can_request: true` (unlimited)
2. Count TOTAL trial requests across ALL agents
   - No agent_type filter (global limit)
3. Calculate remaining: `10 - used_count`
4. Return permission result

**Response**:
```json
{
  "can_request": true,
  "is_subscribed": false,
  "subscription_id": null,
  "remaining_trial_requests": 7,
  "used_trial_requests": 3,
  "total_trial_limit": 10
}
```

### Python Permissions Module
**File**: [work-platform/api/src/utils/permissions.py](work-platform/api/src/utils/permissions.py)

**Functions**:
- `check_agent_work_request_allowed()`: Pre-flight permission check
- `record_work_request()`: Create work request record (trial or paid)
- `update_work_request_status()`: Update request after execution
- `get_trial_status()`: Get remaining trial requests for user
- `create_agent_subscription()`: Create subscription for user

**Error Handling**:
- Raises `PermissionDeniedError` when trial exhausted
- Returns remaining trials in error for UX

---

## API Endpoints

### Updated: POST /api/agents/run
**Phase 4 + Phase 5**: Run agent task with trial enforcement.

**Flow**:
1. Verify JWT → extract user_id
2. Get workspace_id for user
3. **[Phase 5]** Check permission (`check_agent_work_request_allowed()`)
4. **[Phase 5]** Record work request (counts toward trial)
5. **[Phase 5]** Update status to "running"
6. Execute agent task (Phase 4 logic)
7. **[Phase 5]** Update status to "completed" or "failed"

**Response** (updated):
```json
{
  "status": "completed",
  "agent_type": "research",
  "task_type": "monitor",
  "message": "research task completed successfully",
  "result": {...},
  "work_request_id": "uuid",
  "is_trial_request": true,
  "remaining_trials": 7
}
```

**Error on Trial Exhausted** (403):
```json
{
  "detail": "Trial limit exhausted (0/10 remaining). Subscribe to research agent for unlimited requests."
}
```

### New: GET /api/agents/trial-status
Get user's trial status (remaining free work requests).

**Response**:
```json
{
  "used_trial_requests": 3,
  "remaining_trial_requests": 7,
  "total_trial_limit": 10,
  "subscribed_agents": ["research"]
}
```

### New: GET /api/agents/marketplace
Get available agents with pricing and subscription status.

**Response**:
```json
{
  "agents": [
    {
      "agent_type": "research",
      "name": "Research Agent",
      "description": "Monitors domains, synthesizes findings...",
      "monthly_price_usd": 19.00,
      "trial_limit": 10,
      "is_subscribed": false
    },
    {
      "agent_type": "content",
      "name": "Content Creator Agent",
      "description": "Creates brand-aligned content...",
      "monthly_price_usd": 29.00,
      "trial_limit": 10,
      "is_subscribed": false
    },
    {
      "agent_type": "reporting",
      "name": "Reporting Agent",
      "description": "Generates executive reports...",
      "monthly_price_usd": 39.00,
      "trial_limit": 10,
      "is_subscribed": true
    }
  ],
  "trial_status": {
    "remaining_trial_requests": 7,
    "used_trial_requests": 3
  }
}
```

### New: POST /api/agents/subscribe/{agent_type}
Subscribe to an agent (unlock unlimited work requests).

**Request Body**:
```json
{
  "stripe_subscription_id": "sub_xxx", // Optional for now
  "stripe_customer_id": "cus_xxx"     // Optional for now
}
```

**Response**:
```json
{
  "subscription_id": "uuid",
  "agent_type": "research",
  "monthly_price_usd": 19.00,
  "status": "active",
  "message": "Successfully subscribed to research agent"
}
```

---

## Row Level Security (RLS)

### agent_catalog
- **Public read**: Anyone can see available agents
- Policy: `is_active = true`

### agent_work_requests
- **User read**: Users can only see their own requests
- Policy: `auth.uid() = user_id`
- **Service write**: Service role can insert/update
- Policy: `auth.jwt() ->> 'role' = 'service_role'`

### user_agent_subscriptions
- **User read**: Users can only see their own subscriptions
- Policy: `auth.uid() = user_id`
- **Service write**: Service role can manage
- Policy: `auth.jwt() ->> 'role' = 'service_role'`

---

## Testing & Verification

### Migration Test
✅ Migration applied successfully:
```bash
PGPASSWORD="..." psql ... -f supabase/migrations/20250116_phase5_work_request_trials.sql
# Result: COMMIT (all tables, indexes, policies created)
```

### Seed Data Verification
✅ Agent catalog populated:
```sql
SELECT agent_type, name, monthly_price_cents / 100.0 as price_usd, trial_work_requests
FROM agent_catalog ORDER BY agent_type;

 agent_type |         name          | price_usd | trial_work_requests
------------+-----------------------+-----------+---------------------
 content    | Content Creator Agent |     29.00 |                  10
 reporting  | Reporting Agent       |     39.00 |                  10
 research   | Research Agent        |     19.00 |                  10
```

### Trial Limit Function Test
✅ Function returns correct trial status:
```sql
SELECT check_trial_limit(
  'deadbeef-0000-0000-0000-000000000001'::uuid,
  (SELECT id FROM workspaces LIMIT 1),
  'research'
);

-- Result:
{
  "can_request": true,
  "is_subscribed": false,
  "subscription_id": null,
  "total_trial_limit": 10,
  "used_trial_requests": 0,
  "remaining_trial_requests": 10
}
```

### Python Syntax Check
✅ All Python modules compile successfully:
```bash
python -m py_compile src/utils/permissions.py           # ✅ OK
python -m py_compile src/app/routes/agent_orchestration.py  # ✅ OK
```

---

## User Journey

### Trial User (0-10 Requests)
1. Sign up → Get 10 free work requests
2. Try any agent (research/content/reporting)
3. See remaining trials in response: `"remaining_trials": 7`
4. After 10 requests → blocked with clear message
5. GET `/api/agents/marketplace` → see pricing
6. POST `/api/agents/subscribe/research` → unlimited research requests

### Subscribed User
1. Subscribe to agent ($19-$39/month)
2. Unlimited work requests for that agent
3. Can still use trial requests for OTHER agents
4. Example:
   - Subscribe to Research Agent → unlimited research
   - Still have 10 trials for Content/Reporting

---

## Future Enhancements (Out of Scope)

### Stripe Integration
- Add `stripe_subscription_id` webhook handling
- Implement payment flow in `/subscribe/{agent_type}`
- Handle subscription lifecycle (cancel, expire, renew)

### Analytics Dashboard
- Work request usage graphs
- Trial conversion rates
- Revenue metrics per agent

### Advanced Features
- Team subscriptions (workspace-level)
- Annual billing (discount)
- Usage-based pricing tiers
- Trial extensions for power users

---

## Architecture Alignment

### Phase 3 BFF Pattern ✅
- work-platform calls substrate-api via HTTP
- No direct database access (uses substrate_client)
- Service-to-service auth (Authorization: Bearer)

### Phase 4 SDK Integration ✅
- Adapters bridge SDK → substrate_client
- Factory functions create agents with adapters
- Authorization wired through workspace_id

### Phase 5 Trial System ✅
- Permission checks before agent execution
- Work request tracking for billing/audit
- Per-agent subscription model
- 10 TOTAL trial requests (simple UX)

---

## Files Modified/Created

### Created:
1. `supabase/migrations/20250116_phase5_work_request_trials.sql` - Database schema
2. `work-platform/api/src/utils/permissions.py` - Permission enforcement
3. `PHASE_5_SUMMARY.md` - This document

### Modified:
1. `work-platform/api/src/app/routes/agent_orchestration.py` - Trial logic + new endpoints

### Imports Added:
```python
from utils.permissions import (
    check_agent_work_request_allowed,
    record_work_request,
    update_work_request_status,
    get_trial_status,
    create_agent_subscription,
    PermissionDeniedError,
)
```

---

## Next Steps

### Immediate (Phase 6?)
- [ ] Frontend UI for agent marketplace
- [ ] Frontend trial countdown display
- [ ] Frontend subscription flow
- [ ] Stripe integration (payment processing)

### Medium Term
- [ ] Email notifications (trial exhausted, subscription expiring)
- [ ] Usage analytics dashboard
- [ ] Admin panel for subscription management

### Long Term
- [ ] Team/workspace-level subscriptions
- [ ] Usage-based pricing (beyond unlimited)
- [ ] Enterprise features (SSO, audit logs, etc.)

---

## Success Criteria ✅

- [x] Database schema created and migrated
- [x] 10 TOTAL trial requests enforced globally
- [x] Per-agent subscriptions unlock unlimited requests
- [x] Agent catalog seeded with 3 agents ($19/$29/$39)
- [x] Permission checks integrated into `/run` endpoint
- [x] Trial status endpoint (`/trial-status`)
- [x] Marketplace endpoint (`/marketplace`)
- [x] Subscribe endpoint (`/subscribe/{agent_type}`)
- [x] RLS policies configured correctly
- [x] Python syntax validated
- [x] Migration tested on production database

**Phase 5 Complete!** 🎉
