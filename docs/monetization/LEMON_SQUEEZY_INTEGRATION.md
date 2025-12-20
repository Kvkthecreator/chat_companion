# Lemon Squeezy Integration Guide

## Overview

This document outlines the integration of Lemon Squeezy as Fantazy's payment provider for subscription management.

**Why Lemon Squeezy?**
- Merchant of Record (handles tax, compliance, chargebacks)
- Simple API and webhook system
- Built-in subscription management portal
- Competitive fees (~5% + $0.50 per transaction)
- Good for indie/startup products

---

## Prerequisites

Before implementing, you'll need:

1. **Lemon Squeezy Account** (you have this)
2. **Store Setup** in Lemon Squeezy dashboard
3. **Product(s) Created** for your subscription tiers
4. **API Key** from Settings > API
5. **Webhook Signing Secret** from Settings > Webhooks

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │   Backend API   │     │  Lemon Squeezy  │
│   (Next.js)     │────▶│   (FastAPI)     │────▶│   (Checkout)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                        │
                                │◀───────────────────────│
                                │     Webhooks           │
                                ▼                        │
                        ┌─────────────────┐              │
                        │   Supabase      │              │
                        │   (users table) │◀─────────────┘
                        └─────────────────┘
```

---

## Database Schema (Current State)

The `users` table already has subscription fields:

```sql
-- Already exists in 001_users.sql
subscription_status TEXT DEFAULT 'free',     -- 'free', 'premium', 'cancelled'
subscription_expires_at TIMESTAMPTZ,
```

### Recommended Schema Extension

Create a new migration for additional tracking:

```sql
-- Migration: XXX_subscription_tracking.sql

-- Store Lemon Squeezy customer/subscription IDs
ALTER TABLE users ADD COLUMN IF NOT EXISTS
    lemonsqueezy_customer_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS
    lemonsqueezy_subscription_id TEXT;

-- Index for lookups
CREATE INDEX IF NOT EXISTS idx_users_ls_customer
    ON users(lemonsqueezy_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_ls_subscription
    ON users(lemonsqueezy_subscription_id);

-- Subscription events log (optional but recommended)
CREATE TABLE IF NOT EXISTS subscription_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,  -- 'created', 'updated', 'cancelled', 'resumed', 'expired'
    event_source TEXT NOT NULL DEFAULT 'lemonsqueezy',
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscription_events_user
    ON subscription_events(user_id);
```

---

## Lemon Squeezy Setup

### 1. Create Store

In Lemon Squeezy Dashboard:
1. Go to **Stores** > Create new store
2. Set store name: "Fantazy"
3. Configure payment methods, currency (USD recommended)

### 2. Create Product(s)

Create subscription product(s):

| Product | Price | Billing | Variant ID |
|---------|-------|---------|------------|
| Fantazy Premium | $12/month | Monthly | `variant_xxx` |
| Fantazy Premium (Annual) | $99/year | Yearly | `variant_yyy` |

**Key settings:**
- Subscription type: Recurring
- Trial period: 0 days (or 7 days if offering trial)
- License key: Not needed for SaaS

### 3. Get Credentials

From **Settings > API**:
- `LEMONSQUEEZY_API_KEY` - Your API key
- `LEMONSQUEEZY_STORE_ID` - Your store ID

From **Settings > Webhooks**:
- Create webhook endpoint: `https://your-api.com/webhooks/lemonsqueezy`
- Copy `LEMONSQUEEZY_WEBHOOK_SECRET`
- Select events: `subscription_created`, `subscription_updated`, `subscription_cancelled`, `subscription_expired`, `subscription_resumed`

---

## Environment Variables

Add to your backend `.env`:

```env
# Lemon Squeezy
LEMONSQUEEZY_API_KEY=your_api_key_here
LEMONSQUEEZY_STORE_ID=your_store_id
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret
LEMONSQUEEZY_VARIANT_ID_MONTHLY=variant_xxx
LEMONSQUEEZY_VARIANT_ID_ANNUAL=variant_yyy

# Optional: Customer portal
LEMONSQUEEZY_PORTAL_ENABLED=true
```

---

## Implementation Steps

### Step 1: Checkout Flow

**Frontend: Create checkout button**

```tsx
// web/src/components/subscription/UpgradeButton.tsx

async function handleUpgrade(variantId: string) {
  const response = await api.post('/subscription/checkout', { variant_id: variantId });
  const { checkout_url } = response.data;
  window.location.href = checkout_url;
}
```

**Backend: Generate checkout URL**

```python
# substrate-api/api/src/app/routes/subscription.py

from fastapi import APIRouter, Depends
import httpx

router = APIRouter(prefix="/subscription", tags=["subscription"])

@router.post("/checkout")
async def create_checkout(
    variant_id: str,
    user = Depends(get_current_user)
):
    """Create Lemon Squeezy checkout session."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.lemonsqueezy.com/v1/checkouts",
            headers={
                "Authorization": f"Bearer {settings.LEMONSQUEEZY_API_KEY}",
                "Content-Type": "application/vnd.api+json",
            },
            json={
                "data": {
                    "type": "checkouts",
                    "attributes": {
                        "checkout_data": {
                            "custom": {
                                "user_id": str(user.id)  # Critical: links payment to user
                            }
                        }
                    },
                    "relationships": {
                        "store": {
                            "data": {"type": "stores", "id": settings.LEMONSQUEEZY_STORE_ID}
                        },
                        "variant": {
                            "data": {"type": "variants", "id": variant_id}
                        }
                    }
                }
            }
        )

    data = response.json()
    return {"checkout_url": data["data"]["attributes"]["url"]}
```

### Step 2: Webhook Handler

**Backend: Process Lemon Squeezy webhooks**

```python
# substrate-api/api/src/app/routes/webhooks.py

import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request):
    """Handle Lemon Squeezy webhook events."""

    # Verify signature
    signature = request.headers.get("X-Signature")
    body = await request.body()

    expected = hmac.new(
        settings.LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if signature != expected:
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event_name = payload["meta"]["event_name"]

    # Extract user_id from custom data
    custom_data = payload["meta"].get("custom_data", {})
    user_id = custom_data.get("user_id")

    if not user_id:
        # Try to find user by customer email
        email = payload["data"]["attributes"].get("user_email")
        # Look up user by auth email...

    # Handle events
    if event_name == "subscription_created":
        await handle_subscription_created(user_id, payload)
    elif event_name == "subscription_updated":
        await handle_subscription_updated(user_id, payload)
    elif event_name in ["subscription_cancelled", "subscription_expired"]:
        await handle_subscription_ended(user_id, payload)
    elif event_name == "subscription_resumed":
        await handle_subscription_resumed(user_id, payload)

    return {"status": "ok"}


async def handle_subscription_created(user_id: str, payload: dict):
    """Activate premium subscription."""
    attrs = payload["data"]["attributes"]

    await db.execute("""
        UPDATE users SET
            subscription_status = 'premium',
            subscription_expires_at = $2,
            lemonsqueezy_customer_id = $3,
            lemonsqueezy_subscription_id = $4,
            updated_at = NOW()
        WHERE id = $1
    """, user_id, attrs["renews_at"], attrs["customer_id"], attrs["id"])

    # Log event
    await db.execute("""
        INSERT INTO subscription_events (user_id, event_type, payload)
        VALUES ($1, 'created', $2)
    """, user_id, payload)


async def handle_subscription_ended(user_id: str, payload: dict):
    """Downgrade to free tier."""
    await db.execute("""
        UPDATE users SET
            subscription_status = 'free',
            subscription_expires_at = NULL,
            updated_at = NOW()
        WHERE id = $1
    """, user_id)
```

### Step 3: Customer Portal

Lemon Squeezy provides a hosted customer portal for managing subscriptions.

```python
@router.get("/subscription/portal")
async def get_portal_url(user = Depends(get_current_user)):
    """Get Lemon Squeezy customer portal URL."""

    if not user.lemonsqueezy_customer_id:
        raise HTTPException(status_code=404, detail="No subscription found")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.lemonsqueezy.com/v1/customers/{user.lemonsqueezy_customer_id}/portal",
            headers={"Authorization": f"Bearer {settings.LEMONSQUEEZY_API_KEY}"}
        )

    data = response.json()
    return {"portal_url": data["data"]["attributes"]["urls"]["customer_portal"]}
```

### Step 4: Subscription Status Check

**Backend: Middleware or dependency**

```python
# substrate-api/api/src/app/dependencies.py

async def require_premium(user = Depends(get_current_user)):
    """Dependency that requires premium subscription."""
    if user.subscription_status != "premium":
        raise HTTPException(
            status_code=403,
            detail="Premium subscription required"
        )
    return user
```

**Frontend: Check subscription status**

```tsx
// web/src/hooks/useSubscription.ts

export function useSubscription() {
  const { user } = useAuth();

  return {
    isPremium: user?.subscription_status === 'premium',
    expiresAt: user?.subscription_expires_at,
  };
}
```

---

## Subscription Tiers Mapping

| Lemon Squeezy Status | Fantazy Status | User Experience |
|---------------------|----------------|-----------------|
| `active` | `premium` | Full premium features |
| `on_trial` | `premium` | Premium with trial badge |
| `past_due` | `premium` | Premium (grace period) |
| `paused` | `free` | Downgraded |
| `cancelled` | `free` | Downgraded (at period end) |
| `expired` | `free` | Downgraded |

---

## Feature Gating

### What Premium Unlocks

Based on [IMAGE_GENERATION_COSTS.md](./IMAGE_GENERATION_COSTS.md):

| Feature | Free | Premium |
|---------|------|---------|
| Daily messages | Limited (e.g., 20) | Unlimited |
| Pre-generated scenes | Yes | Yes |
| Flux scene generation | No | 20-30/month |
| Parallax/animated panels | No | Yes |
| Priority support | No | Yes |

### Implementation Pattern

```tsx
// Frontend gating
function SceneGenerateButton() {
  const { isPremium } = useSubscription();

  if (!isPremium) {
    return <UpgradePrompt feature="AI scene generation" />;
  }

  return <button onClick={generateScene}>Generate Scene</button>;
}
```

```python
# Backend gating
@router.post("/scenes/generate")
async def generate_scene(
    request: SceneGenerateRequest,
    user = Depends(require_premium)  # Premium only
):
    # Check monthly quota
    quota = await get_user_flux_quota(user.id)
    if quota.used >= quota.limit:
        raise HTTPException(status_code=429, detail="Monthly quota exceeded")

    # Generate scene...
```

---

## Testing

### Lemon Squeezy Test Mode

1. In LS dashboard, toggle to **Test Mode**
2. Use test card: `4242 4242 4242 4242`
3. Webhooks work the same in test mode

### Webhook Testing (Local)

Use ngrok or similar to expose local endpoint:

```bash
ngrok http 8000
# Update webhook URL in LS dashboard to ngrok URL
```

---

## Checklist

### Lemon Squeezy Dashboard
- [ ] Create store
- [ ] Create monthly subscription product ($12/mo)
- [ ] Create annual subscription product ($99/yr) - optional
- [ ] Generate API key
- [ ] Configure webhook endpoint
- [ ] Copy webhook signing secret

### Database
- [ ] Run migration for `lemonsqueezy_customer_id`, `lemonsqueezy_subscription_id`
- [ ] Create `subscription_events` table (optional)

### Backend (FastAPI)
- [ ] Add environment variables
- [ ] Implement `/subscription/checkout` endpoint
- [ ] Implement `/webhooks/lemonsqueezy` endpoint
- [ ] Implement `/subscription/portal` endpoint
- [ ] Add `require_premium` dependency

### Frontend (Next.js)
- [ ] Create upgrade button/page
- [ ] Create subscription management UI
- [ ] Implement feature gating based on `subscription_status`
- [ ] Add success/cancel redirect pages

### Testing
- [ ] Test checkout flow in test mode
- [ ] Verify webhook updates user status
- [ ] Test cancellation flow
- [ ] Test portal access

---

## Pricing Decisions (Finalized)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Monthly Price** | $19/month | Higher margin, premium positioning |
| **Annual Plan** | Not yet | Validate monthly first |
| **Trial Period** | No | Higher quality signals from paying users upfront |
| **Flux Quota** | 50/month | ~$2.50 cost, generous for most users |
| **Cancellation** | End of billing period | Industry standard, reduces refunds |
| **Promo Codes** | Yes (simple) | Friends/family, early adopters, creators |

### Unit Economics at $19/month

```
Revenue:              $19.00
- Lemon Squeezy fee:  -$1.45 (~5% + $0.50)
- Flux (50 images):   -$2.50
- Chat API:           -$2.00
- Infra overhead:     -$1.00
= Net margin:         $12.05 (~63%)
```

### Promo Code Strategy

| Code Type | Discount | Use Case |
|-----------|----------|----------|
| `FRIENDS50` | 50% off first month | Friends & family testing |
| `EARLY100` | 50% off first month | First 100 subscribers |
| `CREATOR` | 100% off (free month) | Influencer partnerships |

---

## Top-Up (Spark Packs) Setup

The Sparks system uses one-time purchases for top-up packs in addition to subscriptions.

### Creating Top-Up Products in Lemon Squeezy

1. In Lemon Squeezy Dashboard, go to **Products** > **Create Product**
2. Create THREE products (one for each pack):

| Pack Name | Sparks | Price | Product Type | Margin |
|-----------|--------|-------|--------------|--------|
| Starter | 25 | $4.99 | One-time | ~66% |
| Popular | 50 | $9.99 | One-time | ~60% |
| Best Value | 100 | $19.99 | One-time | ~60% |

> **Note (Hardened Economics v2.0)**: Pack values reduced from 25/60/150 to 25/50/100 to maintain ~60% margin across all tiers.

3. For each product:
   - Set **Product Type**: One-time purchase (NOT subscription)
   - **License Key**: Disabled (not needed)
   - **Custom Fields**: Not needed (we use checkout custom data)

4. After creating, note each product's **Variant ID** (found in product details)

### Environment Variables for Top-Ups

Add these to your backend `.env`:

```env
# Lemon Squeezy Top-Up Products
TOPUP_VARIANT_STARTER=variant_123456
TOPUP_VARIANT_POPULAR=variant_234567
TOPUP_VARIANT_BEST_VALUE=variant_345678
```

### How Top-Ups Work

1. **User clicks "Buy Spark Pack"** → Frontend calls `/topup/checkout`
2. **Backend creates checkout** with custom data:
   ```python
   custom_data = {
       "user_id": str(user.id),
       "purchase_type": "topup",
       "pack_name": "popular"
   }
   ```
3. **User completes payment** → Lemon Squeezy fires `order_created` webhook
4. **Webhook handler** checks `purchase_type == "topup"` and grants Sparks

### Webhook Handling for Top-Ups

The existing webhook endpoint handles `order_created` events:

```python
# In routes/subscription.py webhook handler
elif event_name == "order_created":
    custom_data = payload["meta"].get("custom_data", {})
    purchase_type = custom_data.get("purchase_type")

    if purchase_type == "topup":
        pack_name = custom_data.get("pack_name")
        await handle_topup_purchase(db, user_id, custom_data, attrs)
```

### Top-Up Pack Configuration

Packs are configured in the backend (`routes/credits.py`):

```python
## Top-up pack configurations (Hardened Economics v2.0)
# Margins optimized for bootstrap sustainability (~60%+ across all packs)
TOPUP_PACKS = {
    "starter": {
        "sparks": 25,
        "price_cents": 499,
        "variant_id": os.getenv("TOPUP_STARTER_VARIANT_ID", ""),
    },
    "popular": {
        "sparks": 50,  # Reduced from 60 to maintain ~60% margin
        "price_cents": 999,
        "variant_id": os.getenv("TOPUP_POPULAR_VARIANT_ID", ""),
    },
    "best_value": {
        "sparks": 100,  # Reduced from 150 to maintain ~60% margin
        "price_cents": 1999,
        "variant_id": os.getenv("TOPUP_BESTVALUE_VARIANT_ID", ""),
    },
}
```

### Testing Top-Ups

1. In Lemon Squeezy, switch to **Test Mode**
2. Create test products with same structure as production
3. Use test card: `4242 4242 4242 4242`
4. Verify webhook fires and Sparks are credited

### Success URL

After successful top-up, redirect to Settings with success indicator:

```
/settings?tab=sparks&topup=success
```

The Settings page handles this by showing a success banner and reloading Spark balance.

### Checklist for Top-Up Setup

**Lemon Squeezy Dashboard:**
- [ ] Create "Starter" one-time product ($4.99, 25 Sparks)
- [ ] Create "Popular" one-time product ($9.99, 50 Sparks)
- [ ] Create "Best Value" one-time product ($19.99, 100 Sparks)
- [ ] Note all three Variant IDs
- [ ] Ensure `order_created` webhook event is enabled

**Environment Variables:**
- [ ] `TOPUP_VARIANT_STARTER` set
- [ ] `TOPUP_VARIANT_POPULAR` set
- [ ] `TOPUP_VARIANT_BEST_VALUE` set

**Testing:**
- [ ] Test checkout creates correct Lemon Squeezy URL
- [ ] Complete test purchase in test mode
- [ ] Verify `order_created` webhook received
- [ ] Verify Sparks credited to user
- [ ] Verify success redirect shows banner

---

## References

- [Lemon Squeezy API Docs](https://docs.lemonsqueezy.com/api)
- [Webhook Events Reference](https://docs.lemonsqueezy.com/guides/developer-guide/webhooks)
- [Checkout API](https://docs.lemonsqueezy.com/guides/tutorials/custom-checkout-links)
