# Subscription Implementation Guide

Complete technical documentation for Fantazy's subscription system powered by Lemon Squeezy.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Lemon Squeezy Configuration](#2-lemon-squeezy-configuration)
3. [Database Schema](#3-database-schema)
4. [Backend API](#4-backend-api)
5. [Frontend Implementation](#5-frontend-implementation)
6. [User Flow Diagrams](#6-user-flow-diagrams)
7. [Environment Variables](#7-environment-variables)
8. [Testing Guide](#8-testing-guide)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. System Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER JOURNEY                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [User]  →  [Frontend]  →  [Backend API]  →  [Lemon Squeezy]            │
│     │           │               │                   │                    │
│     │    Click Upgrade    POST /checkout      Create Session             │
│     │           │               │                   │                    │
│     │           ←───────────────←────── checkout_url ─┘                  │
│     │                                                                    │
│     └──────── Redirect to LS Checkout ──────────────→                   │
│                                                                          │
│                        [Payment Complete]                                │
│                              │                                           │
│     ←──────── Redirect to success URL ───────────────                   │
│                              │                                           │
│                    [Lemon Squeezy Webhook]                               │
│                              │                                           │
│              POST /webhooks/lemonsqueezy                                 │
│                              │                                           │
│                    [Update User Status]                                  │
│                              │                                           │
│              subscription_status = 'premium'                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Payment Provider | Lemon Squeezy | Checkout, billing, customer portal |
| Backend | FastAPI (Python) | API endpoints, webhook handler |
| Database | Supabase (PostgreSQL) | User subscription state |
| Frontend | Next.js (React) | UI, upgrade flows |

---

## 2. Lemon Squeezy Configuration

### Account Details

| Setting | Value |
|---------|-------|
| Store | KVKlabs |
| Store ID | `221652` |
| Store URL | `kvklabs.lemonsqueezy.com` |

### Product: Fantazy Premium

| Setting | Value |
|---------|-------|
| Name | Fantazy Premium |
| Price | $19.99/month |
| Billing | Monthly recurring |
| Trial | None |
| Variant ID | `90f25ea9-0c71-4007-a61b-9df15094e3dc` |
| Checkout URL | `https://kvklabs.lemonsqueezy.com/buy/90f25ea9-0c71-4007-a61b-9df15094e3dc` |

### Webhook Configuration

| Setting | Value |
|---------|-------|
| Endpoint URL | `https://fantazy-api.onrender.com/webhooks/lemonsqueezy` |
| Signing Secret | `ls_wh_ftz_7k9X2mPqR4vL8n` |

**Subscribed Events:**
- `subscription_created`
- `subscription_updated`
- `subscription_cancelled`
- `subscription_resumed`
- `subscription_expired`
- `subscription_paused`
- `subscription_unpaused`
- `subscription_payment_failed`
- `subscription_payment_success`
- `subscription_payment_recovered`
- `subscription_payment_refunded`
- `subscription_plan_changed`

### API Credentials

| Credential | Location |
|------------|----------|
| API Key | Render env var `LEMONSQUEEZY_API_KEY` |
| Store ID | Hardcoded in code (public) |
| Variant ID | Hardcoded in code (public) |
| Webhook Secret | Render env var `LEMONSQUEEZY_WEBHOOK_SECRET` |

---

## 3. Database Schema

### Migration: 013_lemonsqueezy_subscription.sql

**Users Table Extensions:**

```sql
-- New columns on users table
lemonsqueezy_customer_id TEXT      -- LS customer ID (links to their account)
lemonsqueezy_subscription_id TEXT  -- Active subscription ID

-- Indexes
idx_users_ls_customer (lemonsqueezy_customer_id)
idx_users_ls_subscription (lemonsqueezy_subscription_id)
```

**Subscription Events Table:**

```sql
CREATE TABLE subscription_events (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    event_type TEXT NOT NULL,        -- 'created', 'cancelled', etc.
    event_source TEXT DEFAULT 'lemonsqueezy',
    ls_subscription_id TEXT,
    ls_customer_id TEXT,
    payload JSONB,                   -- Full webhook payload
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Subscription Status Values

| Status | Meaning |
|--------|---------|
| `free` | Default, no active subscription |
| `premium` | Active paid subscription |

**Note:** We don't use `cancelled` as a status - when cancelled, it reverts to `free`.

---

## 4. Backend API

### File Location

```
substrate-api/api/src/app/routes/subscription.py
```

### Endpoints

#### GET /subscription/status

Get current user's subscription status.

**Auth:** Required (Bearer token)

**Response:**
```json
{
  "status": "free" | "premium",
  "expires_at": "2025-01-15T00:00:00Z" | null,
  "customer_id": "123456" | null,
  "subscription_id": "sub_xxx" | null
}
```

#### POST /subscription/checkout

Create a Lemon Squeezy checkout session.

**Auth:** Required (Bearer token)

**Request:**
```json
{
  "variant_id": "90f25ea9-..." // Optional, uses default if not provided
}
```

**Response:**
```json
{
  "checkout_url": "https://kvklabs.lemonsqueezy.com/checkout/..."
}
```

**Flow:**
1. Creates checkout session with LS API
2. Includes `user_id` in custom data (for webhook linking)
3. Sets redirect URL to frontend success page
4. Returns checkout URL for frontend redirect

#### GET /subscription/portal

Get customer portal URL for managing subscription.

**Auth:** Required (Bearer token)

**Response:**
```json
{
  "portal_url": "https://app.lemonsqueezy.com/my-orders/..."
}
```

**Error (404):** If user has no subscription history.

#### POST /webhooks/lemonsqueezy

Handle Lemon Squeezy webhook events.

**Auth:** Webhook signature verification (X-Signature header)

**Process:**
1. Verify HMAC signature
2. Extract event type and user_id from payload
3. Log event to `subscription_events` table
4. Update user subscription status based on event type

**Event Handlers:**

| Event | Action |
|-------|--------|
| `subscription_created` | Set status=premium, store LS IDs |
| `subscription_updated` | Update expiry, check status |
| `subscription_cancelled` | Set status=free |
| `subscription_expired` | Set status=free |
| `subscription_resumed` | Set status=premium |
| `subscription_payment_success` | Update expiry date |
| `subscription_payment_failed` | Log only (grace period) |

---

## 5. Frontend Implementation

### File Structure

```
web/src/
├── app/(dashboard)/
│   └── settings/
│       └── page.tsx              # Settings page with subscription section
├── components/
│   └── subscription/
│       ├── SubscriptionCard.tsx  # Main subscription UI component
│       ├── UpgradeButton.tsx     # Reusable upgrade CTA
│       └── PremiumBadge.tsx      # Premium indicator badge
├── hooks/
│   └── useSubscription.ts        # Subscription state hook
└── lib/api/
    └── client.ts                 # Extended with subscription endpoints
```

### API Client Extension

```typescript
// In web/src/lib/api/client.ts

subscription: {
  getStatus: async (): Promise<SubscriptionStatus> => {
    return request<SubscriptionStatus>("/subscription/status");
  },

  createCheckout: async (variantId?: string): Promise<{ checkout_url: string }> => {
    return request<{ checkout_url: string }>("/subscription/checkout", {
      method: "POST",
      body: JSON.stringify({ variant_id: variantId }),
    });
  },

  getPortal: async (): Promise<{ portal_url: string }> => {
    return request<{ portal_url: string }>("/subscription/portal");
  },
}
```

### Types

```typescript
// In web/src/types/index.ts

interface SubscriptionStatus {
  status: "free" | "premium";
  expires_at: string | null;
  customer_id: string | null;
  subscription_id: string | null;
}
```

### Hook: useSubscription

```typescript
// web/src/hooks/useSubscription.ts

export function useSubscription() {
  const { user, reload } = useUser();
  const [isLoading, setIsLoading] = useState(false);

  const isPremium = user?.subscription_status === "premium";
  const expiresAt = user?.subscription_expires_at;

  const upgrade = async () => {
    setIsLoading(true);
    try {
      const { checkout_url } = await api.subscription.createCheckout();
      window.location.href = checkout_url;
    } finally {
      setIsLoading(false);
    }
  };

  const manageSubscription = async () => {
    const { portal_url } = await api.subscription.getPortal();
    window.open(portal_url, "_blank");
  };

  return { isPremium, expiresAt, upgrade, manageSubscription, isLoading, reload };
}
```

### Components

#### SubscriptionCard

Main component for settings page showing current plan and upgrade/manage options.

**States:**
- Free user → Show upgrade prompt with pricing
- Premium user → Show current plan + manage button

#### UpgradeButton

Reusable CTA button that triggers checkout flow.

**Props:**
- `variant`: "default" | "outline" | "ghost"
- `size`: "sm" | "default" | "lg"
- `className`: Additional styling

#### PremiumBadge

Small badge indicator for premium users.

**Usage:** In header, sidebar, or user avatar area.

### Navigation Addition

Add Settings to Sidebar navigation:

```typescript
// In web/src/components/Sidebar.tsx

const navigation = [
  // ... existing items
  { name: "Settings", href: "/settings", icon: Settings },
];
```

### Success Page Handling

The checkout redirects to `/settings?subscription=success`. Handle this:

```typescript
// In settings/page.tsx

const searchParams = useSearchParams();
const success = searchParams.get("subscription");

useEffect(() => {
  if (success === "success") {
    // Show success toast
    // Reload user data
    reload();
  }
}, [success]);
```

---

## 6. User Flow Diagrams

### Upgrade Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     FREE USER                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Sees upgrade prompt in:                                     │
│  - Settings page                                             │
│  - Feature gate (when trying premium action)                 │
│  - Sidebar banner                                            │
└─────────────────────────────────────────────────────────────┘
                          │
                    Clicks "Upgrade"
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend calls POST /subscription/checkout                  │
│  Backend creates LS checkout with user_id                    │
│  Returns checkout_url                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                    Redirect to LS
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LEMON SQUEEZY CHECKOUT                                      │
│  - Enter payment details                                     │
│  - Apply discount code (if any)                              │
│  - Complete purchase                                         │
└─────────────────────────────────────────────────────────────┘
                          │
                   Payment success
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────┐            ┌─────────────────────────────┐
│ Redirect to     │            │ Webhook fires               │
│ /settings?      │            │ POST /webhooks/lemonsqueezy │
│ subscription=   │            │ event: subscription_created │
│ success         │            └─────────────────────────────┘
└─────────────────┘                        │
          │                                ▼
          │                   ┌─────────────────────────────┐
          │                   │ Backend updates user:       │
          │                   │ subscription_status=premium │
          │                   │ Stores LS customer/sub IDs  │
          │                   └─────────────────────────────┘
          │                                │
          └────────────────┬───────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend shows success message                              │
│  Reloads user data                                          │
│  User now has premium status                                │
└─────────────────────────────────────────────────────────────┘
```

### Cancellation Flow

```
Premium User → Settings → "Manage Subscription"
    │
    ▼
Opens LS Customer Portal (new tab)
    │
    ▼
User clicks "Cancel" in portal
    │
    ▼
LS sends webhook: subscription_cancelled
    │
    ▼
Backend sets subscription_status = 'free'
    │
    ▼
User reverts to free tier (at end of billing period)
```

---

## 7. Environment Variables

### Backend (Render)

| Variable | Value | Required |
|----------|-------|----------|
| `LEMONSQUEEZY_API_KEY` | `eyJ0eXAi...` (JWT) | Yes |
| `LEMONSQUEEZY_STORE_ID` | `221652` | No (hardcoded) |
| `LEMONSQUEEZY_VARIANT_ID` | `90f25ea9-...` | No (hardcoded) |
| `LEMONSQUEEZY_WEBHOOK_SECRET` | `ls_wh_ftz_7k9X2mPqR4vL8n` | Yes |
| `CHECKOUT_SUCCESS_URL` | `https://fantazy-five.vercel.app/settings?subscription=success` | No (has default) |

### Frontend (Vercel)

No subscription-specific env vars needed. All communication goes through backend API.

---

## 8. Testing Guide

### Test Mode

Lemon Squeezy has a test mode toggle in the dashboard. When enabled:
- Use test card: `4242 4242 4242 4242`
- Any future expiry, any CVC
- Webhooks fire the same as production

### Manual Testing Checklist

**Checkout Flow:**
- [ ] Click upgrade as free user
- [ ] Verify redirect to LS checkout
- [ ] Complete payment with test card
- [ ] Verify redirect back to success page
- [ ] Verify user status updated to premium
- [ ] Check subscription_events table for event log

**Webhook Verification:**
- [ ] Check webhook received in LS dashboard (Webhooks > Logs)
- [ ] Verify signature validation passes
- [ ] Check subscription_events table populated

**Customer Portal:**
- [ ] As premium user, click "Manage Subscription"
- [ ] Verify portal opens
- [ ] Test cancel flow (in test mode)
- [ ] Verify webhook fires and status reverts

**Edge Cases:**
- [ ] User with no subscription tries to access portal (should show error)
- [ ] Webhook with invalid signature (should reject)
- [ ] Double-click on upgrade (should handle gracefully)

### Local Development

For testing webhooks locally:

```bash
# Use ngrok to expose local API
ngrok http 8000

# Update webhook URL in LS dashboard temporarily
# https://xxxx.ngrok.io/webhooks/lemonsqueezy
```

---

## 9. Troubleshooting

### Common Issues

**"Payment service not configured"**
- Check `LEMONSQUEEZY_API_KEY` is set in Render env vars
- Redeploy after adding env var

**Webhook not updating user status**
- Check webhook URL is correct in LS dashboard
- Verify signing secret matches
- Check LS webhook logs for delivery status
- Check backend logs for errors

**User ID not found in webhook**
- Ensure checkout includes custom data with user_id
- Check webhook payload in subscription_events table

**Portal returns 404**
- User must have completed at least one checkout
- lemonsqueezy_customer_id must be set

### Debugging Queries

```sql
-- Check user subscription status
SELECT id, display_name, subscription_status, subscription_expires_at,
       lemonsqueezy_customer_id, lemonsqueezy_subscription_id
FROM users WHERE id = 'user-uuid';

-- View recent subscription events
SELECT * FROM subscription_events
ORDER BY created_at DESC
LIMIT 20;

-- Find events for specific user
SELECT event_type, created_at, payload->>'meta'->>'event_name'
FROM subscription_events
WHERE user_id = 'user-uuid'
ORDER BY created_at DESC;
```

### Webhook Signature Verification

If webhooks fail signature verification:

1. Check secret matches exactly (no trailing spaces)
2. Ensure using raw body bytes for HMAC, not parsed JSON
3. Compare with expected format: `sha256(secret + body)`

---

## Related Documents

- [IMAGE_GENERATION_COSTS.md](./IMAGE_GENERATION_COSTS.md) - Pricing rationale and unit economics
- [LEMON_SQUEEZY_INTEGRATION.md](./LEMON_SQUEEZY_INTEGRATION.md) - Original integration planning doc
- [DATABASE_ACCESS.md](../DATABASE_ACCESS.md) - Database connection details
