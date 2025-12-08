# YARNNN Notification Canon v1.0.0
## Unified Notification Architecture - Sacred Design Document

### Canon Principles

**Sacred Principle #1: Notification Purity**
Notifications must respect the fundamental separation between substrate (P1-P3) and presentation (P4) layers. Substrate notifications are governance-bound, while presentation notifications are user experience focused.

**Sacred Principle #2: Governance Integration**  
All notifications flow through workspace governance controls. Users configure notification routing, filtering, and persistence according to their cognitive preferences and workspace permissions.

**Sacred Principle #3: Cross-Page Persistence**
Notifications survive page navigation and reconnections. The notification state is workspace-bound, not session-bound, maintaining continuity across the YARNNN experience.

**Sacred Principle #4: Unified Taxonomy**
One canonical notification type system across all workflows. No fragmented notification schemas or inconsistent message patterns.

---

### Architecture Overview

```typescript
// Unified Notification Store (Zustand + Supabase Sync)
interface YARNNNNotificationStore {
  // Core state
  notifications: UnifiedNotification[];
  workspace_id: string;
  user_id: string;
  
  // Governance-controlled settings
  governance: NotificationGovernance;
  
  // Real-time subscriptions
  realtime_channel: RealtimeChannel;
  
  // Actions
  addNotification: (notification: CreateNotificationRequest) => void;
  dismissNotification: (id: string) => void;
  markAsRead: (id: string) => void;
  
  // Cross-page persistence
  hydrate: (workspace_id: string) => Promise<void>;
  sync: () => Promise<void>;
}
```

### Canonical Notification Schema

```typescript
interface UnifiedNotification {
  // Identity
  id: string;
  workspace_id: string;
  user_id: string;
  
  // Classification (Canon-compliant)
  type: NotificationType;
  category: 'substrate' | 'presentation' | 'work' | 'governance' | 'system';
  severity: 'info' | 'success' | 'warning' | 'error' | 'critical';
  
  // Content
  title: string;
  message: string;
  timestamp: string;
  
  // Governance Integration
  governance_context: {
    requires_approval: boolean;
    auto_approvable: boolean;
    smart_review_eligible: boolean;
    permission_level: 'viewer' | 'editor' | 'admin';
  };
  
  // Routing & Display
  channels: NotificationChannel[];
  persistence: {
    cross_page: boolean;
    auto_dismiss: boolean | number; // false, true, or seconds
    requires_acknowledgment: boolean;
  };
  
  // Interactions
  actions?: NotificationAction[];
  related_entities: {
    basket_id?: string;
    document_id?: string;
    substrate_ids?: string[];
    work_id?: string;
  };
  
  // State tracking
  status: 'unread' | 'read' | 'dismissed' | 'acknowledged';
  read_at?: string;
  dismissed_at?: string;
  acknowledged_at?: string;
}
```

### Canon-Compliant Type Taxonomy

```typescript
enum NotificationType {
  // ── Substrate Layer (P1-P3) - Governance Bound ──
  'substrate.block.created',
  'substrate.block.approved', 
  'substrate.block.rejected',
  'substrate.context_item.created',
  'substrate.context_item.approved',
  'substrate.dump.processed',
  'substrate.relationships.mapped',
  
  // ── Presentation Layer (P4) - User Experience ──
  'presentation.document.composed',
  'presentation.document.impact_ready',
  'presentation.document.composition_failed',
  
  // ── Work Orchestration - System Operations ──
  'work.queued',
  'work.processing', 
  'work.completed',
  'work.failed',
  'work.cascade.initiated',
  'work.cascade.completed',
  
  // ── Governance & Smart Approval ──
  'governance.approval.required',
  'governance.approval.batch_ready',
  'governance.settings.changed',
  'governance.smart_review.completed',
  'governance.permissions.changed',
  
  // ── System & Collaboration ──
  'system.user.joined_workspace',
  'system.user.left_workspace', 
  'system.user.editing_document',
  'system.conflict.detected',
  'system.performance.alert'
}
```

### Governance Integration

```typescript
interface NotificationGovernance {
  workspace_id: string;
  
  // Substrate notification controls
  substrate_notifications: {
    enabled: boolean;
    filter: 'all' | 'approvals_only' | 'high_confidence_only';
    batch_low_priority: boolean;
    smart_approval_integration: boolean;
  };
  
  // Presentation layer controls  
  presentation_notifications: {
    enabled: boolean;
    document_composition: boolean;
    document_impacts: boolean;
    cross_page_persist: boolean;
  };
  
  // Work queue controls
  work_notifications: {
    enabled: boolean;
    show_all_workspace_work: boolean;
    cascade_notifications: boolean;
    failure_alerts: boolean;
  };
  
  // User experience settings
  ui_preferences: {
    position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
    max_visible: number;
    auto_dismiss_delay: number;
    sound_enabled: boolean;
    badge_counts: boolean;
  };
  
  // Permission-based routing
  role_based_routing: {
    admin_escalations: boolean;
    collaborator_mentions: boolean;
    governance_alerts: boolean;
  };
}
```

### Implementation Architecture

**Core Components:**
1. **UnifiedNotificationService** - Central notification management
2. **NotificationStore** - Zustand store with Supabase persistence  
3. **NotificationCenter** - Cross-page persistent UI component
4. **NotificationChannels** - Toast, Badge, Persistent, Modal channels
5. **GovernanceIntegration** - Workspace settings integration

**Real-time Synchronization:**
- Supabase Realtime subscriptions for live notifications
- Automatic conflict resolution for cross-device sync
- Offline-first with sync queue for reliability

**Legacy Migration Strategy:**
1. Deprecate react-hot-toast usage progressively
2. Replace custom yarnnn-notification events with unified system
3. Migrate specialized systems (DocumentImpact, WorkStatus) to unified channels
4. Remove fragmented notification components

---

### Sacred Guarantees

1. **No Notification Loss**: All notifications persist across page navigation and reconnections
2. **Governance Compliance**: Notification routing respects workspace governance at all times  
3. **Canon Purity**: Clear separation between substrate and presentation layer notifications
4. **User Control**: Granular notification preferences without overwhelming complexity
5. **Performance**: Minimal resource usage with intelligent batching and filtering

This canon establishes the unified notification architecture as a first-class citizen in the YARNNN ecosystem, ensuring consistency, governance integration, and exceptional user experience across all workflows.