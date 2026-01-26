# Channel Simplification Implementation Plan

> **Status**: Implemented
> **Date**: January 2026
> **Related**: [Notification Channel Philosophy](./notification-channel-philosophy.md)

---

## Overview

This document outlines the concrete code changes needed to simplify our notification and channel architecture to a dedicated app model (mobile + web only, push notifications only).

---

## Summary of Changes

| Category | Files Affected | Effort |
|----------|---------------|--------|
| Web UI | 3 files | Medium |
| Mobile UI | 1 file | Low |
| API/Backend | 2 files | Medium |
| Type Definitions | 2 files | Low |
| Database | 1 migration | Low |

**Total: ~9 files to modify**

---

## Phase 1: UI Simplification

### 1.1 Web Onboarding - Remove Channel Step

**File**: `web/src/app/(onboarding)/onboarding/page.tsx`

Changes:
- Remove `"channel"` from STEPS array (line 21)
- Remove `telegramLinked` and `telegramDeepLink` state variables (lines 102-103)
- Remove `getTelegramDeepLink()` function (lines 230-237)
- Remove entire channel step UI (lines 494-564)
- Update step count references if hardcoded

### 1.2 Web Settings - Simplify Channels Tab

**File**: `web/src/app/(dashboard)/settings/page.tsx`

Option A (Recommended): Remove Channels tab entirely
- Remove "Channels" from tab list
- Remove lines 160-241 (channels tab content)

Option B: Keep tab but simplify
- Show only "Mobile App (Push)" and "Web Chat" as the two available surfaces
- Remove Telegram connect button
- Remove WhatsApp "Coming Soon" section

### 1.3 Mobile Settings - Simplify Channels Tab

**File**: `mobile/app/(main)/settings.tsx`

Modify `renderChannelsTab()` function (lines 163-228):
- Keep only "Mobile Push" section showing "Active" status
- Remove Telegram section (lines 186-198)
- Remove Web Chat section (lines 200-212) - not relevant for mobile users
- Remove WhatsApp section (lines 214-224)

Result: Tab shows single item confirming push notifications are active

---

## Phase 2: Type System Cleanup

### 2.1 Web API Client Types

**File**: `web/src/lib/api/client.ts`

Remove from User interface (around line 81):
```typescript
// REMOVE THIS LINE:
preferred_channel?: "push" | "telegram" | "whatsapp" | "none";
```

Keep these (for data integrity with existing users):
```typescript
telegram_user_id?: number;
telegram_username?: string;
telegram_linked_at?: string;
whatsapp_number?: string;
whatsapp_linked_at?: string;
```

### 2.2 Mobile API Client Types

**File**: `mobile/lib/api/client.ts`

Same change - remove `preferred_channel` from User interface (around line 82)

---

## Phase 3: Backend Logic Updates

### 3.1 Scheduler Service - Critical Path

**File**: `api/api/src/app/services/scheduler.py`

#### Update `send_scheduled_message()` method

Current flow (lines 293-345):
```python
if user.get("telegram_user_id"):
    # Send via Telegram
elif user.get("whatsapp_number"):
    # TODO: WhatsApp
else:
    # No channel available
```

New flow:
```python
# Send via push notification to most recent active device
push_service = ExpoPushService(self.db)
results = await push_service.send_notification(
    user_id=user_id,
    title=f"Hey {companion_name} is here",
    body="Time for your daily check-in 💭",
    data={
        "type": "daily-checkin",
        "conversation_id": str(conversation_id),
        "scheduled_message_id": str(scheduled_message_id)
    },
    scheduled_message_id=scheduled_message_id,
    channel_id="daily-checkin"
)

if not results or all(r.success is False for r in results):
    # No push delivery - user will see message when they open app
    logger.info(f"No push delivery for user {user_id}, message waiting in app")
```

#### Update `get_users_for_scheduled_message()` query

Current filter (line 118):
```sql
AND (u.telegram_user_id IS NOT NULL OR u.whatsapp_number IS NOT NULL)
```

New filter:
```sql
AND EXISTS (
    SELECT 1 FROM user_devices ud
    WHERE ud.user_id = u.id
    AND ud.is_active = true
    AND ud.push_token IS NOT NULL
)
```

Or alternatively, remove filter entirely - generate messages for all users, push delivery is best-effort.

### 3.2 Push Service - Single Device Delivery

**File**: `api/api/src/app/services/push.py`

Modify `send_notification()` to send to most recent device only:

```python
async def send_notification(
    self,
    user_id: UUID,
    ...
) -> List[PushResult]:
    # Get most recently active device only
    query = """
        SELECT id, push_token, platform
        FROM user_devices
        WHERE user_id = $1
          AND is_active = true
          AND push_token IS NOT NULL
        ORDER BY last_active_at DESC
        LIMIT 1
    """
    # ... rest of implementation
```

---

## Phase 4: Database Migration (Optional)

### 4.1 Deprecate preferred_channel

**File**: New migration `supabase/migrations/XXX_deprecate_preferred_channel.sql`

```sql
-- Mark preferred_channel as deprecated
-- We don't remove the column to preserve data integrity
-- Just update the default and add a comment

COMMENT ON COLUMN users.preferred_channel IS
  'DEPRECATED (Jan 2026): No longer used. App uses push notifications only.';

-- Optionally set all users to 'push' default
UPDATE users SET preferred_channel = 'push' WHERE preferred_channel != 'push';
```

---

## Files NOT Being Changed

These stay as-is for backward compatibility:

| File | Reason |
|------|--------|
| `api/src/app/routes/telegram.py` | Frozen - existing users can still use |
| `api/src/app/services/telegram.py` | Frozen - service still works |
| `supabase/migrations/100_companion_schema.sql` | Keep Telegram/WhatsApp columns |
| `supabase/migrations/102_mobile_devices.sql` | Keep as-is, just update function |

---

## Testing Checklist

### Before Implementation
- [ ] Verify at least one test user has push token registered
- [ ] Confirm Expo push credentials are configured

### After Phase 1 (UI)
- [ ] Web onboarding completes without channel step
- [ ] Web settings has no Telegram connect option
- [ ] Mobile settings shows push only

### After Phase 3 (Backend)
- [ ] Scheduler runs and sends push notification
- [ ] Push notification received on mobile device
- [ ] Tapping notification opens correct conversation
- [ ] User without push token still gets message in app (just no notification)

### Regression Testing
- [ ] Existing Telegram users can still receive messages (bot still running)
- [ ] Web chat still works
- [ ] Mobile chat still works
- [ ] Conversation sync works between mobile and web

---

## Rollback Plan

If issues arise:

1. **UI changes**: Revert git commits for web/mobile UI files
2. **Backend changes**: Revert scheduler.py, redeploy
3. **Database**: No destructive changes, nothing to rollback

Low risk overall - we're removing code paths, not adding complexity.

---

## Implementation Order

Recommended sequence:

1. **Phase 3 first** - Get push notifications working in scheduler
2. **Phase 1 second** - Remove UI once push is confirmed working
3. **Phase 2 third** - Clean up types
4. **Phase 4 last** - Database cleanup (optional, can defer)

This ensures push works before we hide Telegram from users.

---

## Estimated Scope

| Phase | Files | Complexity |
|-------|-------|------------|
| Phase 1 | 3 | UI removal - straightforward |
| Phase 2 | 2 | Type removal - trivial |
| Phase 3 | 2 | Logic change - moderate |
| Phase 4 | 1 | Migration - trivial |

---

## Next Steps

1. Review and approve this plan
2. Create branch: `feature/channel-simplification`
3. Implement Phase 3 (push integration)
4. Test push delivery end-to-end
5. Implement Phases 1, 2
6. Deploy and monitor
7. Phase 4 cleanup (optional, later)
