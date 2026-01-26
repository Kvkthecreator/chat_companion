# API Endpoints Reference

> **Status**: Current as of 2026-01-26
> **Base URL**: Production on Render

---

## Overview

| Route Group | Prefix | Purpose |
|-------------|--------|---------|
| Health | `/health` | API and database health |
| Users | `/users` | User profiles |
| Conversation | `/conversation` | Chat messaging |
| Memory | `/memory` | Memory/thread management |
| Onboarding | `/onboarding` | Onboarding flow |
| Telegram | `/telegram` | Telegram integration |
| Devices | `/devices` | Mobile device registration |
| Push | `/push` | Push notifications |
| Subscription | `/subscription` | Payments (LemonSqueezy) |
| Admin | `/admin` | Analytics dashboard (admin only) |
| Webhooks | `/webhooks` | External service webhooks |

---

## Authentication

All endpoints (except health and webhooks) require a Supabase JWT token:

```
Authorization: Bearer <supabase_access_token>
```

---

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

---

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

---

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

### GET /conversation/{conversation_id}/messages

Get messages from a conversation.

**Query Parameters**:
- `limit` (default: 50)
- `offset` (default: 0)

### POST /conversation/{conversation_id}/end

End a conversation and generate summary.

---

## Memory

Memory endpoints provide access to the companion's stored knowledge about the user.

### GET /memory/summary

Get memory summary for dashboard card (active threads, follow-ups, counts).

**Response**:
```json
{
  "active_threads": [
    {
      "id": "uuid",
      "topic": "Job interview at Google",
      "summary": "Interview scheduled for Friday",
      "status": "active",
      "follow_up_date": "2024-01-19",
      "key_details": ["Senior role", "Remote friendly"]
    }
  ],
  "pending_follow_ups": [
    {
      "id": "uuid",
      "question": "How did the interview go?",
      "context": "Google interview",
      "follow_up_date": "2024-01-19"
    }
  ],
  "thread_count": 3,
  "fact_count": 12
}
```

### GET /memory/full

Get full memory for management page (all threads, facts, patterns).

**Response**:
```json
{
  "threads": [...],
  "follow_ups": [...],
  "facts": {
    "personal": [...],
    "preferences": [...],
    "relationships": [...],
    "goals": [...]
  },
  "patterns": [
    {
      "id": "uuid",
      "pattern_type": "mood_trend",
      "description": "Your mood has been improving over the past 7 days",
      "confidence": 0.85
    }
  ]
}
```

### DELETE /memory/context/{context_id}

Delete a memory item (fact, thread, or follow-up).

### PATCH /memory/context/{context_id}

Update a memory item.

**Body**:
```json
{
  "value": "Updated value",
  "importance_score": 0.8
}
```

### POST /memory/threads/{thread_id}/resolve

Mark a thread as resolved.

---

## Onboarding

### GET /onboarding

Get current onboarding state.

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

---

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

---

## Devices

Mobile device registration for push notifications.

### POST /devices

Register a device or update existing registration (upsert).

**Body**:
```json
{
  "device_id": "expo-device-id",
  "platform": "ios",
  "push_token": "ExponentPushToken[...]",
  "app_version": "1.0.0"
}
```

### PATCH /devices/{device_id}

Update device push token or status.

### DELETE /devices/{device_id}

Unregister a device (soft delete).

### GET /devices

List all registered devices for current user.

### POST /devices/{device_id}/heartbeat

Update device last_active_at timestamp.

---

## Push

Push notification management.

### POST /push/test

Send a test push notification to the current user's devices.

**Body**:
```json
{
  "title": "Test Notification",
  "body": "This is a test push notification!"
}
```

### GET /push/history

Get push notification history for the current user.

**Query Parameters**:
- `limit` (default: 20, max: 100)
- `offset` (default: 0)

### PATCH /push/{notification_id}/clicked

Mark a notification as clicked (for analytics).

### GET /push/stats

Get push notification statistics (delivery rate, click rate).

**Query Parameters**:
- `days` (default: 7, max: 30)

---

## Subscription

### GET /subscription/status

Get current subscription status.

### POST /subscription/checkout

Create checkout session.

**Body**:
```json
{
  "variant_id": "123456"
}
```

### GET /subscription/portal

Get customer portal URL.

---

## Admin

Admin endpoints require email allowlist verification.

### GET /admin/stats

Comprehensive admin stats (users, signups, purchases, guest sessions).

### GET /admin/funnel

Activation funnel analysis (dropoff points, cohort retention).

**Query Parameters**:
- `days` (default: 30) - lookback period

### GET /admin/message-priority

Message priority distribution (memory system health).

**Query Parameters**:
- `days` (default: 30)

**Response**:
```json
{
  "total_messages": 150,
  "distribution": [
    {"priority": "FOLLOW_UP", "count": 30, "percentage": 20.0},
    {"priority": "THREAD", "count": 45, "percentage": 30.0},
    {"priority": "PATTERN", "count": 25, "percentage": 16.7},
    {"priority": "TEXTURE", "count": 35, "percentage": 23.3},
    {"priority": "GENERIC", "count": 15, "percentage": 10.0}
  ],
  "generic_rate": 10.0,
  "personal_rate": 66.7,
  "insights": ["✅ Memory system healthy: Only 10.0% generic messages"]
}
```

### GET /admin/extraction-stats

Extraction health metrics (success/failure rates).

---

## Webhooks

### POST /webhooks/lemonsqueezy

Lemon Squeezy payment webhook.

**Auth**: Verified via `X-Signature` header

---

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
