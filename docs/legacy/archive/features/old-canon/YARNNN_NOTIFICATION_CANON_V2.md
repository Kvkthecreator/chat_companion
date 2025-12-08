# YARNNN Notification Canon v2.0.0
## Domain-Agnostic Event Communication Architecture

### Canon Principles

**Sacred Principle #1: Domain Agnosticism**
Notifications are a **cross-cutting observability concern**. They communicate events from ANY domain (governance, processing, integration, etc.) but do not participate in those domains.

**Sacred Principle #2: Workspace-Level Scope**
Notifications are workspace-scoped. Users receive alerts for events across all their baskets within the workspace, with deep links to appropriate action locations.

**Sacred Principle #3: Event Observer Pattern**
Notifications **observe** domain events, they do not **drive** domain logic. Governance generates notifications, but notifications do not control governance.

**Sacred Principle #4: Single Source of Truth**
One notification table (`user_alerts`), one notification store, one notification center UI. No fragmented systems.

---

## 🏗️ Domain Boundaries (Critical Distinction)

### What Notifications ARE
- **Purpose**: Communicate events requiring user attention or awareness
- **Scope**: Workspace-level (user sees events across all baskets)
- **Pattern**: Observer (watch domain events, emit alerts)
- **UI**: Notification center, badge counts, toasts

### What Notifications are NOT
- ❌ Not governance (change requests are a separate domain)
- ❌ Not timeline (knowledge narrative is basket-scoped history)
- ❌ Not work orchestration (canonical queue is execution infrastructure)
- ❌ Not domain-specific (they observe all domains equally)

### Relationship to Other Domains

```
┌─────────────────────────────────────────┐
│     Governance Domain                   │
│  (Change Requests)                      │
│                                         │
│  Proposal Created ────────┐             │
│  Proposal Approved ───────┼─────> Emit Notification
│  Proposal Rejected ───────┘             │
│                                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│     Processing Domain                   │
│  (Canonical Queue)                      │
│                                         │
│  Work Failed ──────────────┐            │
│  Cascade Completed ────────┼────> Emit Notification
│  Job Stalled ──────────────┘            │
│                                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│     Integration Domain                  │
│  (MCP Connections)                      │
│                                         │
│  Connection Lost ──────────┐            │
│  Capture Arrived ──────────┼────> Emit Notification
│  Error Threshold Hit ──────┘            │
│                                         │
└─────────────────────────────────────────┘

                ↓
                ↓
    ┌───────────────────────┐
    │  Notification Domain  │
    │  (Observability)      │
    │                       │
    │  ├─ user_alerts DB    │
    │  ├─ Toast system      │
    │  └─ NotificationCenter│
    └───────────────────────┘
```

**Key Insight**: Notifications are **horizontal** (cross all domains), domains are **vertical** (self-contained logic).

---

## 📊 Canonical Notification Schema

### Database Table: `user_alerts`

```sql
CREATE TABLE user_alerts (
  -- Identity
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id),
  user_id uuid NOT NULL,

  -- Classification (Domain-Agnostic)
  alert_type text NOT NULL,  -- governance | processing | integration | capture | system
  severity text NOT NULL CHECK (severity IN ('info', 'success', 'warning', 'error', 'critical')),

  -- Content
  title text NOT NULL,
  message text NOT NULL,
  created_at timestamptz DEFAULT now(),

  -- Deep Linking (to source domain)
  action_href text,          -- Where to navigate (e.g., /workspace/change-requests#id)
  action_label text,         -- CTA text (e.g., "Review", "Retry", "View")

  -- Related Entities (for filtering/grouping)
  related_basket_id uuid REFERENCES baskets(id),
  related_proposal_id uuid REFERENCES proposals(id),
  related_work_id uuid,      -- canonical_queue.id
  related_metadata jsonb DEFAULT '{}',

  -- User Interaction Tracking
  read_at timestamptz,
  dismissed_at timestamptz,
  acknowledged_at timestamptz
);

-- Indexes for common queries
CREATE INDEX idx_user_alerts_workspace_user
  ON user_alerts(workspace_id, user_id, created_at DESC)
  WHERE dismissed_at IS NULL;

CREATE INDEX idx_user_alerts_type
  ON user_alerts(alert_type, severity)
  WHERE dismissed_at IS NULL;
```

### TypeScript Interface

```typescript
interface UserAlert {
  // Identity
  id: string;
  workspace_id: string;
  user_id: string;

  // Classification
  alert_type: 'governance' | 'processing' | 'integration' | 'capture' | 'system';
  severity: 'info' | 'success' | 'warning' | 'error' | 'critical';

  // Content
  title: string;
  message: string;
  created_at: string;

  // Actions
  action_href?: string;
  action_label?: string;

  // Relations
  related_basket_id?: string;
  related_proposal_id?: string;
  related_work_id?: string;
  related_metadata?: Record<string, unknown>;

  // State
  read_at?: string;
  dismissed_at?: string;
  acknowledged_at?: string;
}
```

---

## 🔔 Alert Types & Examples

### Type 1: Governance Alerts

**When change request events occur:**

```typescript
// Workspace-level proposal created
{
  alert_type: 'governance',
  severity: 'info',
  title: 'Workspace change request pending',
  message: 'Basket assignment for "API design notes" awaiting review',
  action_href: '/workspace/change-requests#prop-123',
  action_label: 'Review',
  related_proposal_id: 'prop-123'
}

// Basket-level proposal needs approval
{
  alert_type: 'governance',
  severity: 'info',
  title: 'Change request in "Project X"',
  message: '3 new blocks proposed from recent dumps',
  action_href: '/baskets/basket-456/change-requests#prop-789',
  action_label: 'Review',
  related_basket_id: 'basket-456',
  related_proposal_id: 'prop-789'
}

// Proposal auto-approved
{
  alert_type: 'governance',
  severity: 'success',
  title: 'Change request auto-approved',
  message: 'High-confidence proposal committed to "Research Notes"',
  action_href: '/baskets/basket-111/timeline#event-222',
  action_label: 'View',
  related_basket_id: 'basket-111',
  related_proposal_id: 'prop-333'
}
```

### Type 2: Capture Alerts

**When MCP captures arrive:**

```typescript
// Unassigned capture needs basket assignment
{
  alert_type: 'capture',
  severity: 'info',
  title: 'Unassigned capture',
  message: 'Claude captured: "Meeting notes - Q1 planning"',
  action_href: '/workspace/change-requests?view=assignments#capture-abc',
  action_label: 'Assign',
  related_metadata: { tool: 'claude.memory', confidence: 0.45 }
}

// High-confidence capture auto-assigned
{
  alert_type: 'capture',
  severity: 'success',
  title: 'Capture auto-assigned',
  message: 'ChatGPT memory added to "Work Journal" (confidence: 0.92)',
  action_href: '/baskets/basket-xyz/timeline?view=uploads&highlight=dump-def',
  action_label: 'View',
  related_basket_id: 'basket-xyz'
}
```

### Type 3: Processing Alerts

**When background work events occur:**

```typescript
// Job failed
{
  alert_type: 'processing',
  severity: 'error',
  title: 'Processing failed',
  message: 'P2_GRAPH failed for dump "Product ideas": Timeout exceeded',
  action_href: '/workspace/processing#work-ghi',
  action_label: 'Retry',
  related_work_id: 'work-ghi',
  related_basket_id: 'basket-jkl'
}

// Cascade completed
{
  alert_type: 'processing',
  severity: 'success',
  title: 'Reflection computed',
  message: 'P3 insights generated for "Project X"',
  action_href: '/baskets/basket-mno/insights',
  action_label: 'View',
  related_basket_id: 'basket-mno'
}
```

### Type 4: Integration Alerts

**When MCP/connection events occur:**

```typescript
// Connection degraded
{
  alert_type: 'integration',
  severity: 'warning',
  title: 'Claude connection slow',
  message: 'P95 latency: 1200ms (threshold: 800ms)',
  action_href: '/dashboard/integrations',
  action_label: 'Check Status',
  related_metadata: { host: 'claude', p95_ms: 1200 }
}

// Error threshold exceeded
{
  alert_type: 'integration',
  severity: 'error',
  title: 'ChatGPT errors detected',
  message: '5 errors in last hour - connection may need reset',
  action_href: '/dashboard/integrations',
  action_label: 'Troubleshoot',
  related_metadata: { host: 'chatgpt', error_count: 5 }
}
```

### Type 5: System Alerts

**When system events occur:**

```typescript
// Workspace event
{
  alert_type: 'system',
  severity: 'info',
  title: 'Workspace member added',
  message: 'Alice joined your workspace',
  action_href: '/workspace/settings/members',
  action_label: 'View',
  related_metadata: { member_email: 'alice@example.com' }
}
```

---

## 🎨 UI Components

### NotificationCenter (Primary UI)

**Location**: Top nav dropdown (bell icon with badge)

**Features**:
- Query `user_alerts` table (not in-memory event store)
- Group by alert type (Governance, Captures, Processing, etc.)
- Show unread count badge
- Deep link to action locations
- Dismiss/acknowledge actions
- Mark as read on view

```typescript
// NotificationCenter.tsx
export function NotificationCenter() {
  const { workspace_id, user_id } = useWorkspace();

  // Query database (not event store!)
  const { data: alerts } = useQuery({
    queryKey: ['alerts', workspace_id, user_id],
    queryFn: async () => {
      const { data } = await supabase
        .from('user_alerts')
        .select('*')
        .eq('workspace_id', workspace_id)
        .eq('user_id', user_id)
        .is('dismissed_at', null)
        .order('created_at', { desc: true })
        .limit(20);
      return data;
    }
  });

  // Group by type
  const grouped = groupBy(alerts, 'alert_type');

  return (
    <div>
      {/* Governance section */}
      {grouped.governance?.length > 0 && (
        <AlertGroup
          title="Change Requests"
          alerts={grouped.governance}
        />
      )}

      {/* Captures section */}
      {grouped.capture?.length > 0 && (
        <AlertGroup
          title="Unassigned Captures"
          alerts={grouped.capture}
        />
      )}

      {/* Processing section */}
      {grouped.processing?.length > 0 && (
        <AlertGroup
          title="Processing"
          alerts={grouped.processing}
        />
      )}
    </div>
  );
}
```

### Toast System (Transient Feedback)

**Purpose**: Immediate, ephemeral feedback for user actions

**Use Cases**:
- "Block created successfully"
- "Proposal approved"
- "Connection restored"

**Implementation**: Keep existing toast system (react-hot-toast or similar)

**Key**: Toasts are **transient**, alerts are **persistent**

---

## 🔌 Notification Service (Emission Layer)

### NotificationService API

```typescript
class NotificationService {
  // Emit alert to database
  async emit(params: {
    workspace_id: string;
    user_id: string;
    alert_type: AlertType;
    severity: Severity;
    title: string;
    message: string;
    action_href?: string;
    action_label?: string;
    related_basket_id?: string;
    related_proposal_id?: string;
    related_work_id?: string;
    related_metadata?: Record<string, unknown>;
  }): Promise<void> {
    await supabase.from('user_alerts').insert(params);
  }

  // Dismiss alert
  async dismiss(alert_id: string): Promise<void> {
    await supabase
      .from('user_alerts')
      .update({ dismissed_at: new Date().toISOString() })
      .eq('id', alert_id);
  }

  // Mark as read
  async markRead(alert_id: string): Promise<void> {
    await supabase
      .from('user_alerts')
      .update({ read_at: new Date().toISOString() })
      .eq('id', alert_id);
  }
}
```

### Integration Points

**Governance Domain**:
```typescript
// When proposal created
await notificationService.emit({
  workspace_id,
  user_id,
  alert_type: 'governance',
  severity: 'info',
  title: 'Change request pending',
  message: proposal.ops_summary,
  action_href: proposal.basket_id
    ? `/baskets/${proposal.basket_id}/change-requests#${proposal.id}`
    : `/workspace/change-requests#${proposal.id}`,
  action_label: 'Review',
  related_basket_id: proposal.basket_id,
  related_proposal_id: proposal.id
});
```

**Processing Domain**:
```typescript
// When work fails
await notificationService.emit({
  workspace_id,
  user_id,
  alert_type: 'processing',
  severity: 'error',
  title: 'Processing failed',
  message: `${work_type} failed: ${error_message}`,
  action_href: `/workspace/processing#${work_id}`,
  action_label: 'Retry',
  related_work_id: work_id,
  related_basket_id: basket_id
});
```

**Capture Domain**:
```typescript
// When unassigned capture arrives
await notificationService.emit({
  workspace_id,
  user_id,
  alert_type: 'capture',
  severity: 'info',
  title: 'Unassigned capture',
  message: `${tool} captured: ${summary}`,
  action_href: `/workspace/change-requests?view=assignments#${capture_id}`,
  action_label: 'Assign',
  related_metadata: { tool, confidence }
});
```

---

## 🗑️ Legacy Cleanup

### DELETE Immediately

❌ **user_notifications table** - Unused, redundant with user_alerts
❌ **workspace_notification_settings table** - Unused
❌ **In-memory event store for persistent alerts** - Use DB for persistence
❌ **Custom notification components** - Consolidate to NotificationCenter

### KEEP

✅ **user_alerts table** - Single source of truth
✅ **Toast system** - Transient feedback (react-hot-toast)
✅ **NotificationBadge** - Unread count indicator

### MIGRATE

- NotificationCenter: Query `user_alerts` instead of event store
- Alert generation: Use NotificationService.emit() consistently
- Deep links: Ensure all alerts have action_href to source

---

## 🎯 Mental Model Summary

### For Users

**"Where do I see notifications?"**
- Top nav bell icon → NotificationCenter dropdown
- Badge shows unread count
- Grouped by type (Governance, Captures, Processing, etc.)

**"What happens when I click?"**
- Deep link takes you to source (change request page, processing queue, etc.)
- Notification marked as read automatically
- Can dismiss if no longer relevant

### For Developers

**"When do I emit a notification?"**
- Any time a domain event occurs that users should know about
- Examples: Proposal created, work failed, capture arrived, connection lost

**"How do I emit?"**
- Call `notificationService.emit()` with appropriate params
- Provide deep link (action_href) to let users act
- Choose correct alert_type and severity

**"What's the difference from timeline?"**
- Notifications = "Things you should know about NOW" (workspace-scoped, actionable)
- Timeline = "How this basket's knowledge evolved" (basket-scoped, historical narrative)

---

## 📋 Implementation Checklist

### Phase 1: Database Cleanup
- [ ] Drop `user_notifications` table (unused)
- [ ] Drop `workspace_notification_settings` table (unused)
- [ ] Ensure `user_alerts` has all required columns and indexes

### Phase 2: NotificationCenter Refactor
- [ ] Update NotificationCenter to query `user_alerts` DB
- [ ] Remove in-memory event store query for persistent alerts
- [ ] Add grouping by alert_type
- [ ] Add dismiss/mark read actions
- [ ] Add deep link navigation

### Phase 3: Notification Emission
- [ ] Create NotificationService class
- [ ] Add emit() calls in governance domain (proposal lifecycle)
- [ ] Add emit() calls in capture domain (unassigned arrivals)
- [ ] Add emit() calls in processing domain (work failures)
- [ ] Add emit() calls in integration domain (connection issues)

### Phase 4: Testing
- [ ] Test notification appears in center after proposal created
- [ ] Test deep link navigation to change request page
- [ ] Test dismiss action
- [ ] Test badge count updates
- [ ] Test grouping by type

---

*This canon establishes notifications as a pure observability concern - domain-agnostic, workspace-scoped, and cleanly separated from governance, timeline, and work orchestration domains.*
