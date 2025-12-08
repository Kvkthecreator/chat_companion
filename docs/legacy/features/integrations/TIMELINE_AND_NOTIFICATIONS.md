# Timeline and Notifications

**Event Stream and User Notification System**

**Version**: 4.0
**Date**: 2025-10-31
**Status**: ✅ Canonical
**Layer**: 1 (Substrate Core) + 4 (Presentation)
**Category**: Feature Specification

---

## 🎯 Overview

YARNNN uses an **append-only timeline** as the source of truth for all system events. Notifications are derived from timeline events via database triggers, ensuring consistent event handling and audit trails.

**Key Concepts**:
- Timeline events are append-only (never modified or deleted)
- Database triggers generate notifications from timeline events
- Supabase Realtime broadcasts notifications to connected clients
- Timeline provides complete audit trail + time-travel queries

---

## 📊 Timeline Events

### Schema

```sql
CREATE TABLE timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),
    basket_id UUID REFERENCES baskets(id),

    -- Event details
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL,

    -- Actor
    actor_type TEXT NOT NULL,           -- user | agent | system
    actor_id UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_timeline_workspace_time
ON timeline_events(workspace_id, created_at DESC);

CREATE INDEX idx_timeline_event_type
ON timeline_events(event_type);

CREATE INDEX idx_timeline_actor
ON timeline_events(actor_type, actor_id);

-- RLS policies
ALTER TABLE timeline_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view timeline for their workspaces"
ON timeline_events
FOR SELECT
TO authenticated
USING (
    workspace_id IN (
        SELECT workspace_id
        FROM workspace_members
        WHERE user_id = auth.uid()
    )
);
```

---

## 📋 Event Types

### Work Events

```typescript
// Work session created
{
  event_type: 'work_session_created',
  event_data: {
    session_id: UUID,
    task_intent: string,
    task_type: string,
    initiated_by_user_id: UUID
  },
  actor_type: 'user',
  actor_id: UUID
}

// Work session started
{
  event_type: 'work_session_started',
  event_data: {
    session_id: UUID,
    executed_by_agent_id: string,
    agent_session_id: string
  },
  actor_type: 'agent',
  actor_id: null
}

// Work session completed
{
  event_type: 'work_session_completed',
  event_data: {
    session_id: UUID,
    artifacts_count: number,
    execution_time_seconds: number
  },
  actor_type: 'agent',
  actor_id: null
}

// Work session approved
{
  event_type: 'work_session_approved',
  event_data: {
    session_id: UUID,
    approved_by: UUID,
    blocks_created: UUID[],
    documents_created: UUID[],
    substrate_mutations_count: number
  },
  actor_type: 'user',
  actor_id: UUID
}

// Work session rejected
{
  event_type: 'work_session_rejected',
  event_data: {
    session_id: UUID,
    rejected_by: UUID,
    rejection_feedback: string
  },
  actor_type: 'user',
  actor_id: UUID
}

// Iteration requested
{
  event_type: 'iteration_requested',
  event_data: {
    session_id: UUID,
    iteration_number: number,
    changes_requested: ChangeRequest[],
    requested_by: UUID
  },
  actor_type: 'user',
  actor_id: UUID
}
```

### Substrate Events

```typescript
// Block created
{
  event_type: 'block_created',
  event_data: {
    block_id: UUID,
    block_type: string,
    created_via_work_session: boolean,
    work_session_id?: UUID
  },
  actor_type: 'user' | 'agent',
  actor_id: UUID | null
}

// Block updated (superseded)
{
  event_type: 'block_updated',
  event_data: {
    old_block_id: UUID,
    new_block_id: UUID,
    supersession_reason: string
  },
  actor_type: 'user',
  actor_id: UUID
}

// Document created
{
  event_type: 'document_created',
  event_data: {
    document_id: UUID,
    title: string,
    document_type: string,
    blocks_count: number
  },
  actor_type: 'user' | 'agent',
  actor_id: UUID | null
}
```

### Governance Events

```typescript
// Checkpoint created
{
  event_type: 'checkpoint_created',
  event_data: {
    checkpoint_id: UUID,
    checkpoint_type: CheckpointType,
    session_id: UUID
  },
  actor_type: 'system',
  actor_id: null
}

// Checkpoint reviewed
{
  event_type: 'checkpoint_reviewed',
  event_data: {
    checkpoint_id: UUID,
    checkpoint_type: CheckpointType,
    decision: string,
    reviewed_by: UUID
  },
  actor_type: 'user',
  actor_id: UUID
}

// Policy changed
{
  event_type: 'policy_changed',
  event_data: {
    policy_changes: Record<string, any>,
    changed_by: UUID
  },
  actor_type: 'user',
  actor_id: UUID
}
```

---

## 🔔 Notifications

### Schema

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),

    -- Notification details
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    action_url TEXT,

    -- State
    read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_notifications_user_unread
ON notifications(user_id, created_at DESC)
WHERE NOT read;

CREATE INDEX idx_notifications_workspace
ON notifications(workspace_id, created_at DESC);

-- RLS policies
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own notifications"
ON notifications
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Users can update their own notifications"
ON notifications
FOR UPDATE
TO authenticated
USING (user_id = auth.uid());
```

---

## 🔄 Timeline → Notifications (Database Triggers)

### Trigger Function

```sql
CREATE OR REPLACE FUNCTION generate_notifications_from_timeline()
RETURNS TRIGGER AS $$
BEGIN
    -- Work session completed → Notify initiator
    IF NEW.event_type = 'work_session_completed' THEN
        INSERT INTO notifications (
            user_id,
            workspace_id,
            notification_type,
            title,
            message,
            action_url
        )
        SELECT
            ws.initiated_by_user_id,
            NEW.workspace_id,
            'work_completed',
            'Work session completed',
            'Task "' || ws.task_intent || '" is ready for review',
            '/work/' || (NEW.event_data->>'session_id')
        FROM work_sessions ws
        WHERE ws.id = (NEW.event_data->>'session_id')::UUID;
    END IF;

    -- Work session approved → Notify workspace members
    IF NEW.event_type = 'work_session_approved' THEN
        INSERT INTO notifications (
            user_id,
            workspace_id,
            notification_type,
            title,
            message,
            action_url
        )
        SELECT
            wm.user_id,
            NEW.workspace_id,
            'work_approved',
            'Work approved',
            (NEW.event_data->>'substrate_mutations_count')::TEXT || ' substrate changes applied',
            '/work/' || (NEW.event_data->>'session_id')
        FROM workspace_members wm
        WHERE wm.workspace_id = NEW.workspace_id
          AND wm.user_id != NEW.actor_id;  -- Don't notify approver
    END IF;

    -- Iteration requested → Notify agent (if automated)
    IF NEW.event_type = 'iteration_requested' THEN
        INSERT INTO notifications (
            user_id,
            workspace_id,
            notification_type,
            title,
            message,
            action_url
        )
        SELECT
            ws.initiated_by_user_id,
            NEW.workspace_id,
            'iteration_requested',
            'Revision requested',
            'Feedback provided for "' || ws.task_intent || '"',
            '/work/' || (NEW.event_data->>'session_id')
        FROM work_sessions ws
        WHERE ws.id = (NEW.event_data->>'session_id')::UUID;
    END IF;

    -- Block created → Notify subscribers (if any)
    IF NEW.event_type = 'block_created' THEN
        -- Future: Implement block subscriptions
        NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger
CREATE TRIGGER timeline_to_notifications
AFTER INSERT ON timeline_events
FOR EACH ROW
EXECUTE FUNCTION generate_notifications_from_timeline();
```

---

## 🔴 Realtime Notifications

### Supabase Realtime Subscription

```typescript
// Frontend: Subscribe to notifications
// File: web/lib/hooks/useNotifications.ts

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const supabase = createClient()

  useEffect(() => {
    // Subscribe to new notifications
    const channel = supabase
      .channel('notifications')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${currentUser.id}`
        },
        (payload) => {
          const notification = payload.new as Notification

          // Add to list
          setNotifications(prev => [notification, ...prev])

          // Increment unread
          setUnreadCount(prev => prev + 1)

          // Show toast
          toast.info(notification.title, {
            description: notification.message,
            action: {
              label: 'View',
              onClick: () => router.push(notification.action_url)
            }
          })
        }
      )
      .subscribe()

    return () => {
      channel.unsubscribe()
    }
  }, [currentUser.id])

  return { notifications, unreadCount }
}
```

---

## 📡 API Endpoints

### List Notifications

**GET** `/api/notifications`

**Query Parameters**:
```typescript
{
  workspace_id?: UUID
  read?: boolean
  notification_type?: string[]
  limit?: number
  offset?: number
}
```

**Response**:
```json
{
  "notifications": [
    {
      "id": "notif-uuid-123",
      "user_id": "user-uuid-456",
      "workspace_id": "ws-uuid-789",
      "notification_type": "work_completed",
      "title": "Work session completed",
      "message": "Task \"Research competitors\" is ready for review",
      "action_url": "/work/session-uuid-abc",
      "read": false,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "unreadCount": 5,
  "total": 42
}
```

---

### Mark Notification Read

**PATCH** `/api/notifications/{notification_id}/read`

**Response**:
```json
{
  "notification": {
    "id": "notif-uuid-123",
    "read": true,
    "read_at": "2025-01-15T10:35:00Z"
  }
}
```

---

### Mark All Read

**POST** `/api/notifications/mark-all-read`

**Request Body**:
```json
{
  "workspace_id": "ws-uuid-789"
}
```

**Response**:
```json
{
  "success": true,
  "markedCount": 12
}
```

---

### List Timeline Events

**GET** `/api/timeline/events`

**Query Parameters**:
```typescript
{
  workspace_id: UUID
  basket_id?: UUID
  event_type?: string[]
  actor_type?: string[]
  after?: ISO8601
  before?: ISO8601
  limit?: number
  offset?: number
}
```

**Response**:
```json
{
  "events": [
    {
      "id": "event-uuid-123",
      "workspace_id": "ws-uuid-789",
      "event_type": "work_session_approved",
      "event_data": {
        "session_id": "session-uuid-abc",
        "approved_by": "user-uuid-def",
        "blocks_created": ["block-1", "block-2"],
        "substrate_mutations_count": 2
      },
      "actor_type": "user",
      "actor_id": "user-uuid-def",
      "created_at": "2025-01-15T10:45:00Z"
    }
  ],
  "total": 156
}
```

---

## 📊 Notification Preferences

### Schema

```sql
CREATE TABLE user_notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id),

    -- Email notifications
    email_notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_digest_frequency TEXT NOT NULL DEFAULT 'daily',  -- none | daily | weekly

    -- In-app notifications
    notify_work_completed BOOLEAN NOT NULL DEFAULT TRUE,
    notify_work_approved BOOLEAN NOT NULL DEFAULT TRUE,
    notify_work_rejected BOOLEAN NOT NULL DEFAULT TRUE,
    notify_iteration_requested BOOLEAN NOT NULL DEFAULT TRUE,
    notify_checkpoint_ready BOOLEAN NOT NULL DEFAULT TRUE,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Applying Preferences

```python
async def should_notify_user(
    user_id: UUID,
    notification_type: str
) -> bool:
    """
    Check if user should receive notification based on preferences
    """

    prefs = await db.user_notification_preferences.get(user_id)

    if not prefs:
        return True  # Default: all notifications enabled

    notification_pref_map = {
        'work_completed': prefs.notify_work_completed,
        'work_approved': prefs.notify_work_approved,
        'work_rejected': prefs.notify_work_rejected,
        'iteration_requested': prefs.notify_iteration_requested,
        'checkpoint_ready': prefs.notify_checkpoint_ready
    }

    return notification_pref_map.get(notification_type, True)
```

---

## 🔍 Timeline Queries

### Query 1: Workspace Activity Feed

```sql
-- Last 50 events in workspace
SELECT
    te.event_type,
    te.event_data,
    te.actor_type,
    u.name AS actor_name,
    te.created_at
FROM timeline_events te
LEFT JOIN users u ON u.id = te.actor_id
WHERE te.workspace_id = $1
ORDER BY te.created_at DESC
LIMIT 50;
```

### Query 2: User Activity (Audit Trail)

```sql
-- All actions by specific user
SELECT
    te.event_type,
    te.event_data,
    te.workspace_id,
    w.name AS workspace_name,
    te.created_at
FROM timeline_events te
LEFT JOIN workspaces w ON w.id = te.workspace_id
WHERE te.actor_type = 'user'
  AND te.actor_id = $1
ORDER BY te.created_at DESC;
```

### Query 3: Work Session Timeline

```sql
-- All events for specific work session
SELECT
    te.event_type,
    te.event_data,
    te.actor_type,
    u.name AS actor_name,
    te.created_at
FROM timeline_events te
LEFT JOIN users u ON u.id = te.actor_id
WHERE te.event_data->>'session_id' = $1
ORDER BY te.created_at ASC;
```

### Query 4: Event Statistics

```sql
-- Event counts by type (last 30 days)
SELECT
    event_type,
    COUNT(*) AS count,
    COUNT(DISTINCT actor_id) AS unique_actors
FROM timeline_events
WHERE workspace_id = $1
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY event_type
ORDER BY count DESC;
```

---

## 📈 Metrics

### Timeline Metrics

```typescript
interface TimelineMetrics {
  workspace_id: UUID
  time_range: string

  // Volume
  totalEvents: number
  eventsByType: Record<string, number>
  eventsPerDay: number

  // Actors
  uniqueUsers: number
  uniqueAgents: number

  // Activity patterns
  peakActivityHour: number
  peakActivityDay: string
}
```

### Notification Metrics

```typescript
interface NotificationMetrics {
  user_id: UUID
  time_range: string

  // Volume
  totalNotifications: number
  unreadNotifications: number

  // Engagement
  notificationOpenRate: number       // Read / Total
  avgTimeToReadSeconds: number

  // By type
  notificationsByType: Record<string, number>
}
```

---

## 📎 See Also

- [AUDIT_TRAILS.md](../governance/AUDIT_TRAILS.md) - Complete provenance tracking
- [WORK_SESSION_LIFECYCLE.md](../work-management/WORK_SESSION_LIFECYCLE.md) - Session states
- [YARNNN_DATA_FLOW_V4.md](../../architecture/YARNNN_DATA_FLOW_V4.md) - Complete request flows

---

**Timeline: Append-only event stream. Notifications: Derived via triggers. Realtime: Supabase broadcasts. Complete audit trail.**
