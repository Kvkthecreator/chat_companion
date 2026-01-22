# Daisy Mobile App — Full Product Launch Plan

## Overview

Full-featured mobile app launch for Daisy, the push-first AI companion. This plan maintains all features from the current web implementation while adding native mobile capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MOBILE APP (Expo)                             │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Onboarding   │  │ Chat         │  │ Dashboard    │  │ Settings    │ │
│  │ (native)     │  │ (native)     │  │ (native)     │  │ (native)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Memory       │  │ Subscription │  │ Channel      │                  │
│  │ Management   │  │ Management   │  │ Settings     │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
├─────────────────────────────────────────────────────────────────────────┤
│                     Expo Push Notifications                             │
│                     Supabase Auth (AsyncStorage)                        │
│                     Deep Linking (Universal/App Links)                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXISTING BACKEND (FastAPI)                       │
├─────────────────────────────────────────────────────────────────────────┤
│  /users/*          /conversations/*       /memory/*       /onboarding/* │
│  /subscription/*   /telegram/*            /context/*                    │
├─────────────────────────────────────────────────────────────────────────┤
│  NEW: /push/*      NEW: /devices/*                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           SERVICES                                       │
├──────────────────┬──────────────────┬───────────────────────────────────┤
│ Supabase         │ Claude API       │ Expo Push Service                 │
│ (auth + db)      │ (AI responses)   │ (notification delivery)           │
├──────────────────┼──────────────────┼───────────────────────────────────┤
│ Stripe           │ Render           │ Cron Jobs                         │
│ (payments)       │ (hosting)        │ (scheduled messages, patterns)   │
└──────────────────┴──────────────────┴───────────────────────────────────┘
```

## Feature Parity Matrix

| Feature | Web (Current) | Mobile (Planned) |
|---------|---------------|------------------|
| **Auth** |
| Email/password signup | ✅ | ✅ Native UI |
| Google OAuth | ✅ | ✅ Native OAuth |
| Session persistence | ✅ Cookie | ✅ SecureStore |
| **Onboarding** |
| Chat-based onboarding | ✅ | ✅ Native chat UI |
| Companion naming | ✅ | ✅ |
| Support style selection | ✅ | ✅ |
| Timezone detection | ✅ Manual | ✅ Auto-detect |
| **Chat** |
| Streaming responses | ✅ SSE | ✅ SSE |
| Message history | ✅ | ✅ |
| Conversation list | ✅ | ✅ |
| **Push Notifications** |
| Daily check-ins | ✅ Telegram | ✅ Native push |
| Timing flexibility (exact/around/window) | ✅ | ✅ |
| Rich notifications | ❌ | ✅ With actions |
| **Memory** |
| Dashboard insight card | ✅ | ✅ |
| Full memory management | ✅ | ✅ |
| Thread tracking | ✅ | ✅ |
| Pattern detection | ✅ | ✅ |
| Delete/edit memories | ✅ | ✅ |
| **Settings** |
| Profile editing | ✅ | ✅ |
| Timing preferences | ✅ | ✅ |
| Support style | ✅ | ✅ |
| Channel management | ✅ Telegram | ✅ Push + Telegram |
| Account deletion | ✅ | ✅ |
| **Subscription** |
| Web checkout (Stripe) | ✅ | ✅ In-app browser |
| Subscription status | ✅ | ✅ |
| Customer portal | ✅ | ✅ |

## Database Schema Changes

```sql
-- =============================================================================
-- Mobile Device Support Migration
-- =============================================================================

-- Device tokens for push notifications
CREATE TABLE IF NOT EXISTS user_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL,  -- Unique device identifier
    platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
    push_token TEXT,  -- Expo push token
    push_token_updated_at TIMESTAMPTZ,
    app_version TEXT,
    os_version TEXT,
    device_model TEXT,
    is_active BOOLEAN DEFAULT true,
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, device_id)
);

-- Index for push notification queries
CREATE INDEX idx_user_devices_push ON user_devices(user_id, is_active, push_token)
    WHERE is_active = true AND push_token IS NOT NULL;

-- Track push notification delivery
CREATE TABLE IF NOT EXISTS push_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id UUID REFERENCES user_devices(id) ON DELETE SET NULL,
    scheduled_message_id UUID REFERENCES scheduled_messages(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'clicked')),
    expo_receipt_id TEXT,
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_push_notifications_user ON push_notifications(user_id, created_at DESC);
CREATE INDEX idx_push_notifications_status ON push_notifications(status, created_at)
    WHERE status = 'pending';

-- Add preferred notification channel to users
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_channel TEXT
    DEFAULT 'push' CHECK (preferred_channel IN ('push', 'telegram', 'whatsapp', 'none'));

-- Update scheduled message function for multi-channel support
CREATE OR REPLACE FUNCTION get_users_for_scheduled_message(
    check_time TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
    user_id UUID,
    display_name TEXT,
    companion_name TEXT,
    support_style TEXT,
    timezone TEXT,
    telegram_user_id BIGINT,
    location TEXT,
    message_time_flexibility TEXT,
    message_time_window TEXT,
    preferred_channel TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id as user_id,
        u.display_name,
        u.companion_name,
        u.support_style,
        u.timezone,
        u.telegram_user_id,
        u.location,
        u.message_time_flexibility,
        u.message_time_window,
        u.preferred_channel
    FROM users u
    WHERE
        u.onboarding_completed_at IS NOT NULL
        AND (
            u.telegram_user_id IS NOT NULL
            OR u.whatsapp_number IS NOT NULL
            OR EXISTS (
                SELECT 1 FROM user_devices ud
                WHERE ud.user_id = u.id
                AND ud.is_active = true
                AND ud.push_token IS NOT NULL
            )
        )
        AND COALESCE((u.preferences->>'daily_messages_paused')::boolean, false) = false
        AND NOT EXISTS (
            SELECT 1 FROM scheduled_messages sm
            WHERE sm.user_id = u.id
            AND sm.status = 'sent'
            AND (sm.sent_at AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date
                = (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date
        )
        AND (
            (COALESCE(u.message_time_flexibility, 'exact') = 'exact'
             AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                 BETWEEN u.preferred_message_time
                 AND (u.preferred_message_time + interval '2 minutes'))
            OR
            (u.message_time_flexibility = 'around'
             AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                 BETWEEN (u.preferred_message_time - interval '15 minutes')
                 AND (u.preferred_message_time + interval '15 minutes'))
            OR
            (u.message_time_flexibility = 'window'
             AND (
                 (u.message_time_window = 'morning'
                  AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                      BETWEEN '06:00'::time AND '10:00'::time)
                 OR
                 (u.message_time_window = 'midday'
                  AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                      BETWEEN '11:00'::time AND '14:00'::time)
                 OR
                 (u.message_time_window = 'evening'
                  AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                      BETWEEN '17:00'::time AND '20:00'::time)
                 OR
                 (u.message_time_window = 'night'
                  AND (check_time AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                      BETWEEN '20:00'::time AND '23:00'::time)
             ))
        );
END;
$$ LANGUAGE plpgsql;

-- Helper to get active push tokens for a user
CREATE OR REPLACE FUNCTION get_user_push_tokens(p_user_id UUID)
RETURNS TABLE (
    device_id UUID,
    push_token TEXT,
    platform TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT ud.id, ud.push_token, ud.platform
    FROM user_devices ud
    WHERE ud.user_id = p_user_id
      AND ud.is_active = true
      AND ud.push_token IS NOT NULL;
END;
$$ LANGUAGE plpgsql;
```

## API Endpoints (New)

### Device Management

```
POST   /devices              Register device, save push token
PATCH  /devices/{device_id}  Update push token or device info
DELETE /devices/{device_id}  Unregister device
GET    /devices              List user's registered devices
```

### Push Notifications

```
POST   /push/test            Send test notification to current device
GET    /push/history         Get notification history
PATCH  /push/{id}/clicked    Mark notification as clicked (for analytics)
```

## Implementation Phases

### Phase 1: Project Setup & Auth (Days 1-3)

**1.1 Expo Project Initialization**
```
mobile/
├── app/                    # Expo Router file-based routing
│   ├── (auth)/
│   │   ├── login.tsx
│   │   ├── signup.tsx
│   │   └── forgot-password.tsx
│   ├── (onboarding)/
│   │   └── chat.tsx
│   ├── (main)/
│   │   ├── _layout.tsx     # Tab navigator
│   │   ├── index.tsx       # Dashboard
│   │   ├── chat/
│   │   │   ├── index.tsx   # Conversation list
│   │   │   └── [id].tsx    # Chat screen
│   │   ├── memory.tsx
│   │   └── settings.tsx
│   └── _layout.tsx         # Root layout with auth check
├── components/
├── lib/
│   ├── api/               # API client (port from web)
│   ├── supabase/          # Supabase client for RN
│   └── push/              # Push notification helpers
├── hooks/
├── stores/                # Zustand stores
└── assets/
```

**1.2 Authentication**
- Supabase Auth with `@supabase/supabase-js` + `expo-secure-store`
- Google OAuth via `expo-auth-session`
- Deep link handling for OAuth callback
- Biometric unlock option (Face ID / Fingerprint)

**1.3 API Client**
- Port `web/src/lib/api/client.ts` to React Native
- Handle token refresh in background
- Offline queue for failed requests

### Phase 2: Push Notification Infrastructure (Days 4-7)

**2.1 Backend: Push Service**

```python
# api/api/src/app/services/push.py

import httpx
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass
from enum import Enum

class PushPriority(str, Enum):
    DEFAULT = "default"
    HIGH = "high"

@dataclass
class PushMessage:
    to: str
    title: str
    body: str
    data: dict = None
    sound: str = "default"
    priority: PushPriority = PushPriority.HIGH
    badge: int = None
    category_id: str = None  # For actionable notifications

class ExpoPushService:
    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
    EXPO_RECEIPTS_URL = "https://exp.host/--/api/v2/push/getReceipts"

    def __init__(self, db):
        self.db = db

    async def send_notification(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: dict = None,
        scheduled_message_id: UUID = None
    ) -> List[dict]:
        """Send push notification to all user's active devices."""

        # Get all active push tokens
        tokens = await self.db.fetch_all(
            "SELECT * FROM get_user_push_tokens(:user_id)",
            {"user_id": str(user_id)}
        )

        if not tokens:
            return []

        results = []
        messages = []

        for token in tokens:
            msg = {
                "to": token["push_token"],
                "title": title,
                "body": body,
                "data": data or {},
                "sound": "default",
                "priority": "high",
            }
            messages.append(msg)

            # Record in database
            row = await self.db.fetch_one(
                """
                INSERT INTO push_notifications
                    (user_id, device_id, scheduled_message_id, title, body, data, status)
                VALUES (:user_id, :device_id, :scheduled_message_id, :title, :body, :data, 'pending')
                RETURNING id
                """,
                {
                    "user_id": str(user_id),
                    "device_id": str(token["device_id"]),
                    "scheduled_message_id": str(scheduled_message_id) if scheduled_message_id else None,
                    "title": title,
                    "body": body,
                    "data": data or {},
                }
            )
            results.append({"notification_id": row["id"], "device_id": token["device_id"]})

        # Send batch to Expo
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.EXPO_PUSH_URL,
                json=messages,
                headers={"Accept": "application/json", "Content-Type": "application/json"}
            )

            if response.status_code == 200:
                tickets = response.json().get("data", [])
                for i, ticket in enumerate(tickets):
                    status = "sent" if ticket.get("status") == "ok" else "failed"
                    await self.db.execute(
                        """
                        UPDATE push_notifications
                        SET status = :status,
                            expo_receipt_id = :receipt_id,
                            sent_at = NOW(),
                            error_message = :error
                        WHERE id = :id
                        """,
                        {
                            "id": str(results[i]["notification_id"]),
                            "status": status,
                            "receipt_id": ticket.get("id"),
                            "error": ticket.get("message") if status == "failed" else None,
                        }
                    )

        return results

    async def check_receipts(self, receipt_ids: List[str]):
        """Check delivery receipts from Expo."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.EXPO_RECEIPTS_URL,
                json={"ids": receipt_ids}
            )

            if response.status_code == 200:
                receipts = response.json().get("data", {})
                for receipt_id, receipt in receipts.items():
                    if receipt.get("status") == "ok":
                        await self.db.execute(
                            """
                            UPDATE push_notifications
                            SET status = 'delivered', delivered_at = NOW()
                            WHERE expo_receipt_id = :receipt_id
                            """,
                            {"receipt_id": receipt_id}
                        )
                    elif receipt.get("status") == "error":
                        # Handle invalid tokens
                        if receipt.get("details", {}).get("error") == "DeviceNotRegistered":
                            await self._invalidate_token(receipt_id)

    async def _invalidate_token(self, receipt_id: str):
        """Mark device as inactive when token is invalid."""
        await self.db.execute(
            """
            UPDATE user_devices
            SET is_active = false, updated_at = NOW()
            WHERE id = (
                SELECT device_id FROM push_notifications
                WHERE expo_receipt_id = :receipt_id
            )
            """,
            {"receipt_id": receipt_id}
        )
```

**2.2 Backend: Device Routes**

```python
# api/api/src/app/routes/devices.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

router = APIRouter(prefix="/devices", tags=["Devices"])

class DeviceRegister(BaseModel):
    device_id: str
    platform: str  # 'ios' or 'android'
    push_token: Optional[str] = None
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    device_model: Optional[str] = None

class DeviceUpdate(BaseModel):
    push_token: Optional[str] = None
    app_version: Optional[str] = None
    is_active: Optional[bool] = None

class DeviceResponse(BaseModel):
    id: str
    device_id: str
    platform: str
    has_push_token: bool
    app_version: Optional[str]
    last_active_at: str

@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    data: DeviceRegister,
    user_id: UUID = Depends(get_current_user_id),
    db = Depends(get_db),
):
    """Register a device or update existing registration."""
    row = await db.fetch_one(
        """
        INSERT INTO user_devices (user_id, device_id, platform, push_token,
                                   push_token_updated_at, app_version, os_version, device_model)
        VALUES (:user_id, :device_id, :platform, :push_token,
                CASE WHEN :push_token IS NOT NULL THEN NOW() END,
                :app_version, :os_version, :device_model)
        ON CONFLICT (user_id, device_id)
        DO UPDATE SET
            push_token = EXCLUDED.push_token,
            push_token_updated_at = CASE WHEN EXCLUDED.push_token IS NOT NULL THEN NOW()
                                         ELSE user_devices.push_token_updated_at END,
            app_version = EXCLUDED.app_version,
            os_version = EXCLUDED.os_version,
            device_model = EXCLUDED.device_model,
            is_active = true,
            last_active_at = NOW(),
            updated_at = NOW()
        RETURNING id, device_id, platform, push_token IS NOT NULL as has_push_token,
                  app_version, last_active_at
        """,
        {
            "user_id": str(user_id),
            "device_id": data.device_id,
            "platform": data.platform,
            "push_token": data.push_token,
            "app_version": data.app_version,
            "os_version": data.os_version,
            "device_model": data.device_model,
        }
    )
    return DeviceResponse(**dict(row))

@router.patch("/{device_id}")
async def update_device(
    device_id: str,
    data: DeviceUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db = Depends(get_db),
):
    """Update device push token or status."""
    updates = []
    values = {"user_id": str(user_id), "device_id": device_id}

    if data.push_token is not None:
        updates.append("push_token = :push_token")
        updates.append("push_token_updated_at = NOW()")
        values["push_token"] = data.push_token

    if data.is_active is not None:
        updates.append("is_active = :is_active")
        values["is_active"] = data.is_active

    if data.app_version is not None:
        updates.append("app_version = :app_version")
        values["app_version"] = data.app_version

    updates.append("last_active_at = NOW()")
    updates.append("updated_at = NOW()")

    query = f"""
        UPDATE user_devices
        SET {', '.join(updates)}
        WHERE user_id = :user_id AND device_id = :device_id
        RETURNING *
    """

    row = await db.fetch_one(query, values)
    if not row:
        raise HTTPException(status_code=404, detail="Device not found")

    return {"status": "updated"}

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device(
    device_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db = Depends(get_db),
):
    """Unregister a device (soft delete)."""
    await db.execute(
        """
        UPDATE user_devices
        SET is_active = false, push_token = NULL, updated_at = NOW()
        WHERE user_id = :user_id AND device_id = :device_id
        """,
        {"user_id": str(user_id), "device_id": device_id}
    )

@router.get("", response_model=List[DeviceResponse])
async def list_devices(
    user_id: UUID = Depends(get_current_user_id),
    db = Depends(get_db),
):
    """List all registered devices for the user."""
    rows = await db.fetch_all(
        """
        SELECT id, device_id, platform, push_token IS NOT NULL as has_push_token,
               app_version, last_active_at
        FROM user_devices
        WHERE user_id = :user_id AND is_active = true
        ORDER BY last_active_at DESC
        """,
        {"user_id": str(user_id)}
    )
    return [DeviceResponse(**dict(row)) for row in rows]
```

**2.3 Mobile: Push Registration**

```typescript
// mobile/lib/push/notifications.ts

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { api } from '../api/client';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export async function registerForPushNotifications(): Promise<string | null> {
  if (!Device.isDevice) {
    console.log('Push notifications require a physical device');
    return null;
  }

  // Check existing permissions
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  // Request permissions if not granted
  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.log('Push notification permission denied');
    return null;
  }

  // Get Expo push token
  const tokenData = await Notifications.getExpoPushTokenAsync({
    projectId: Constants.expoConfig?.extra?.eas?.projectId,
  });
  const pushToken = tokenData.data;

  // Register device with backend
  await api.devices.register({
    device_id: Constants.installationId || Device.modelId || 'unknown',
    platform: Platform.OS as 'ios' | 'android',
    push_token: pushToken,
    app_version: Constants.expoConfig?.version,
    os_version: Device.osVersion,
    device_model: Device.modelName,
  });

  // Android-specific channel setup
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('daily-checkin', {
      name: 'Daily Check-ins',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF6B6B',
    });
  }

  return pushToken;
}

export function setupNotificationListeners(
  onNotificationReceived: (notification: Notifications.Notification) => void,
  onNotificationResponse: (response: Notifications.NotificationResponse) => void
) {
  const receivedSubscription = Notifications.addNotificationReceivedListener(
    onNotificationReceived
  );

  const responseSubscription = Notifications.addNotificationResponseReceivedListener(
    async (response) => {
      // Track click for analytics
      const notificationId = response.notification.request.content.data?.notification_id;
      if (notificationId) {
        await api.push.markClicked(notificationId);
      }
      onNotificationResponse(response);
    }
  );

  return () => {
    receivedSubscription.remove();
    responseSubscription.remove();
  };
}
```

### Phase 3: Core Screens (Days 8-14)

**3.1 Onboarding (Chat-based)**
- Port chat onboarding UI to React Native
- Auto-detect timezone via `expo-localization`
- Request notification permission during flow
- Smooth animations with `react-native-reanimated`

**3.2 Dashboard**
- Companion card with avatar
- Memory insight card
- Daily check-in status
- Recent conversations
- Quick actions

**3.3 Chat Interface**
- Message list with `FlashList` for performance
- Streaming response display
- Typing indicator
- Pull-to-refresh for history
- Keyboard handling with `KeyboardAvoidingView`

**3.4 Memory Management**
- Active threads list
- Follow-ups section
- Facts by category (collapsible)
- Patterns display
- Swipe-to-delete with confirmation
- Edit fact values

**3.5 Settings**
- Profile section (name, companion name)
- Preferences section (timezone, timing, support style)
- Notification settings
- Channel management (Push + Telegram)
- Subscription status
- Account deletion

### Phase 4: Subscription & Payments (Days 15-17)

**4.1 In-App Browser Checkout**
```typescript
// mobile/lib/payments/checkout.ts

import * as WebBrowser from 'expo-web-browser';
import * as Linking from 'expo-linking';
import { api } from '../api/client';

export async function openCheckout(variantId?: string): Promise<boolean> {
  try {
    // Get checkout URL from backend
    const { checkout_url } = await api.subscription.createCheckout(variantId);

    // Add return URL for deep linking back to app
    const returnUrl = Linking.createURL('subscription/success');
    const urlWithReturn = `${checkout_url}&redirect_url=${encodeURIComponent(returnUrl)}`;

    // Open in-app browser
    const result = await WebBrowser.openAuthSessionAsync(
      urlWithReturn,
      returnUrl
    );

    return result.type === 'success';
  } catch (error) {
    console.error('Checkout failed:', error);
    return false;
  }
}

export async function openCustomerPortal(): Promise<void> {
  const { portal_url } = await api.subscription.getPortal();
  await WebBrowser.openBrowserAsync(portal_url);
}
```

**4.2 Subscription UI**
- Current plan display
- Upgrade prompts (if on free tier)
- Manage subscription button → Customer Portal
- Receipt/billing history link

### Phase 5: Polish & Launch Prep (Days 18-21)

**5.1 Deep Linking**
```typescript
// mobile/app/_layout.tsx

import { useEffect } from 'react';
import * as Linking from 'expo-linking';
import { useRouter } from 'expo-router';

export default function RootLayout() {
  const router = useRouter();

  useEffect(() => {
    // Handle deep links
    const subscription = Linking.addEventListener('url', ({ url }) => {
      const { path, queryParams } = Linking.parse(url);

      if (path === 'chat' && queryParams?.conversation_id) {
        router.push(`/chat/${queryParams.conversation_id}`);
      } else if (path === 'subscription/success') {
        router.push('/settings?subscribed=true');
      }
    });

    return () => subscription.remove();
  }, []);

  // ... rest of layout
}
```

**5.2 App Configuration**
```json
// app.json
{
  "expo": {
    "name": "Daisy",
    "slug": "daisy",
    "version": "1.0.0",
    "scheme": "daisy",
    "ios": {
      "bundleIdentifier": "com.daisy.companion",
      "supportsTablet": false,
      "infoPlist": {
        "NSFaceIDUsageDescription": "Use Face ID to unlock Daisy"
      }
    },
    "android": {
      "package": "com.daisy.companion",
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#FF6B6B"
      }
    },
    "plugins": [
      "expo-router",
      "expo-secure-store",
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#FF6B6B"
        }
      ]
    ],
    "extra": {
      "eas": {
        "projectId": "your-project-id"
      }
    }
  }
}
```

**5.3 App Store Assets**
- App icon (1024x1024)
- Screenshots (6.5", 5.5" iPhone, Android)
- App Store description
- Privacy policy URL
- Terms of service URL

**5.4 Testing Checklist**
- [ ] Push notifications on iOS (TestFlight)
- [ ] Push notifications on Android (Internal testing)
- [ ] Scheduled message delivery
- [ ] Timing flexibility (all 3 modes)
- [ ] Auth flow (signup, login, forgot password)
- [ ] OAuth (Google)
- [ ] Chat streaming
- [ ] Memory CRUD operations
- [ ] Subscription checkout flow
- [ ] Deep linking from notifications
- [ ] Offline behavior
- [ ] Background token refresh

## File Structure Summary

```
chat_companion/
├── api/                          # Existing FastAPI backend
│   └── api/src/app/
│       ├── routes/
│       │   ├── devices.py        # NEW: Device registration
│       │   └── push.py           # NEW: Push endpoints
│       ├── services/
│       │   └── push.py           # NEW: Expo push service
│       └── jobs/
│           └── scheduled_messages.py  # MODIFIED: Multi-channel
│
├── mobile/                       # NEW: Expo app
│   ├── app/                      # Expo Router screens
│   ├── components/               # Shared components
│   ├── lib/
│   │   ├── api/                  # API client
│   │   ├── supabase/             # Auth
│   │   └── push/                 # Push notifications
│   ├── hooks/
│   ├── stores/                   # Zustand
│   └── assets/
│
├── web/                          # Existing Next.js web app
│
└── supabase/
    └── migrations/
        └── 102_mobile_devices.sql  # NEW: Device tables
```

## Environment Variables (Mobile)

```
# .env (mobile)
EXPO_PUBLIC_API_URL=https://api.daisy.app
EXPO_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=xxx
```

## Launch Checklist

### Pre-Launch
- [ ] Apple Developer account ($99/year)
- [ ] Google Play Developer account ($25 one-time)
- [ ] Push notification certificates configured in EAS
- [ ] Privacy policy page live
- [ ] Terms of service page live
- [ ] App Store Connect listing prepared
- [ ] Google Play Console listing prepared

### Launch Day
- [ ] Submit to App Store Review
- [ ] Submit to Google Play Review
- [ ] Monitor Sentry/error tracking
- [ ] Monitor push delivery rates
- [ ] Customer support ready

### Post-Launch
- [ ] Monitor App Store reviews
- [ ] A/B test notification copy
- [ ] Iterate on timing defaults
- [ ] Add notification preferences granularity
