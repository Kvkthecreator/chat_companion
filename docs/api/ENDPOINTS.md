# API Endpoints Reference

Base URL: `https://your-api.onrender.com`

## Authentication

All endpoints (except health and webhooks) require a Supabase JWT token:

```
Authorization: Bearer <supabase_access_token>
```

## Health

### GET /health

Check API and database status.

**Auth**: None required

**Response**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Users

### GET /users/me

Get current user profile.

**Response**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "Alex",
  "companion_name": "Aria",
  "timezone": "America/New_York",
  "preferred_message_time": "09:00:00",
  "support_style": "friendly_checkin",
  "location": "New York",
  "telegram_user_id": 123456789,
  "onboarding_completed_at": "2024-01-15T10:30:00Z"
}
```

### PATCH /users/me

Update user profile.

**Body**:
```json
{
  "display_name": "Alex",
  "companion_name": "Luna",
  "timezone": "America/Los_Angeles",
  "preferred_message_time": "08:00:00",
  "support_style": "motivational",
  "location": "San Francisco"
}
```

## Conversation

### POST /conversation/send

Send a message and get a response.

**Body**:
```json
{
  "content": "Hey, how are you?"
}
```

**Response**:
```json
{
  "id": "uuid",
  "role": "assistant",
  "content": "Hey Alex! I'm doing well, thanks for asking...",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### POST /conversation/send/stream

Send a message and stream the response (SSE).

**Body**:
```json
{
  "content": "Tell me about your day"
}
```

**Response**: Server-Sent Events stream
```
data: {"type": "chunk", "content": "Hey"}
data: {"type": "chunk", "content": " Alex"}
data: {"type": "chunk", "content": "!"}
data: {"type": "done", "content": "Hey Alex!", "message_id": "uuid"}
data: [DONE]
```

### GET /conversation/current

Get current (today's) conversation.

**Response**:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "channel": "web",
  "started_at": "2024-01-15T00:00:00Z",
  "message_count": 5,
  "initiated_by": "user",
  "mood_summary": "upbeat",
  "topics": ["work", "weekend plans"]
}
```

### GET /conversation/{conversation_id}/messages

Get messages from a conversation.

**Query Parameters**:
- `limit` (default: 50)
- `offset` (default: 0)

**Response**:
```json
{
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Hey!",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "Hey Alex! How's your day going?",
      "created_at": "2024-01-15T10:30:05Z"
    }
  ],
  "total": 2
}
```

### POST /conversation/{conversation_id}/end

End a conversation and generate summary.

**Response**:
```json
{
  "id": "uuid",
  "ended_at": "2024-01-15T12:00:00Z",
  "mood_summary": "positive",
  "topics": ["work", "lunch plans"]
}
```

## Onboarding

### GET /onboarding

Get current onboarding state.

**Response**:
```json
{
  "user_id": "uuid",
  "current_step": "companion_name",
  "completed_at": null,
  "data": {
    "display_name": "Alex"
  },
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### PATCH /onboarding

Update onboarding state.

**Body**:
```json
{
  "step": "support_style",
  "data": {
    "companion_name": "Luna"
  }
}
```

### POST /onboarding/complete

Mark onboarding as complete.

**Response**:
```json
{
  "user_id": "uuid",
  "current_step": "complete",
  "completed_at": "2024-01-15T10:35:00Z",
  "data": {...}
}
```

## Telegram

### GET /telegram/link/{user_id}

Get deep link URL for connecting Telegram.

**Response**:
```json
{
  "deep_link_url": "https://t.me/YourBot?start=abc123",
  "expires_in_minutes": 30
}
```

### POST /telegram/webhook

Telegram webhook endpoint (called by Telegram servers).

**Auth**: Verified via `X-Telegram-Bot-Api-Secret-Token` header

## Subscription

### GET /subscription/status

Get current subscription status.

**Response**:
```json
{
  "status": "premium",
  "expires_at": "2024-02-15T00:00:00Z",
  "customer_id": "cus_123",
  "subscription_id": "sub_456"
}
```

### POST /subscription/checkout

Create checkout session.

**Body**:
```json
{
  "variant_id": "123456"  // optional, uses default if not provided
}
```

**Response**:
```json
{
  "checkout_url": "https://checkout.lemonsqueezy.com/..."
}
```

### GET /subscription/portal

Get customer portal URL.

**Response**:
```json
{
  "portal_url": "https://app.lemonsqueezy.com/my-orders/..."
}
```

## Webhooks

### POST /webhooks/lemonsqueezy

Lemon Squeezy payment webhook.

**Auth**: Verified via `X-Signature` header

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

Common status codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error
