# YARNNN Timeline & Notification Separation v3.0

**Fundamental refactoring to eliminate purpose confusion and establish clear boundaries**

## 🚨 Current Problems

### Timeline Chaos
- **40+ event types** mixing technical processing with user outcomes
- **Multiple implementations** (UnifiedTimeline, ConsumerTimeline, MemoryChainTimeline, ProcessingStoryTimeline)
- **Granularity confusion**: `queue.processing_started` + `document.composed` + `block.created`
- **Purpose confusion**: Technical audit log vs user knowledge story

### Notification Overlap  
- **50+ notification types** overlapping with timeline events
- **Complex channels/persistence/governance** creating implementation burden
- **Real-time vs historical** serving same events differently

## 🎯 Clean Separation Design

### **Timeline: Knowledge Evolution Story** (Artifact-like)
**Purpose**: "How did my knowledge/memory evolve over time?"
**Audience**: Users understanding their knowledge journey
**Granularity**: Major milestones, user-meaningful events only

#### Simplified Event Types (8 total):
```typescript
type KnowledgeEventType = 
  | 'memory.captured'        // Raw input added to memory
  | 'knowledge.evolved'      // Substrate approved/updated  
  | 'insights.discovered'    // Reflections computed
  | 'document.created'       // New narrative composed
  | 'document.updated'       // Document edited/recomposed
  | 'relationships.mapped'   // New connections found
  | 'governance.decided'     // Important approval/rejection
  | 'milestone.achieved'     // Significant knowledge growth
```

#### Timeline Schema (New):
```sql
CREATE TABLE knowledge_timeline (
  id uuid PRIMARY KEY,
  basket_id uuid NOT NULL,
  event_type knowledge_event_type NOT NULL,
  title text NOT NULL,           -- "Memory captured from upload"
  description text,              -- "3 new insights discovered"
  significance 'low' | 'medium' | 'high',
  metadata jsonb,                -- Event-specific data
  created_at timestamptz DEFAULT now()
);
```

### **Notifications: Real-Time Actionable Alerts** (Service Layer)
**Purpose**: "What needs my attention right now?"
**Audience**: Users needing to act or be aware of completions
**Granularity**: Actionable items and important status changes only

#### Simplified Notification Types (12 total):
```typescript
type AlertType = 
  // Actions Required
  | 'approval.required'      // Review proposal
  | 'decision.needed'        // User input required
  | 'error.attention'        // Something failed, user can fix
  
  // Completions (No action required, just awareness)
  | 'processing.completed'   // Your request finished
  | 'document.ready'         // Composition finished
  | 'insights.available'     // New reflections ready
  
  // Status Changes
  | 'governance.updated'     // Settings changed
  | 'collaboration.update'   // Team activity
  
  // System  
  | 'system.maintenance'     // Scheduled downtime
  | 'system.performance'     // Slow responses
  | 'system.security'        // Login alerts
  | 'system.storage'         // Space warnings
```

#### Notification Schema (Simplified):
```sql
CREATE TABLE user_alerts (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL,
  workspace_id uuid NOT NULL,
  alert_type alert_type NOT NULL,
  title text NOT NULL,
  message text NOT NULL,
  severity 'info' | 'warning' | 'error' NOT NULL,
  actionable boolean DEFAULT false,
  action_url text,               -- Where to go to act
  expires_at timestamptz,        -- Auto-dismiss time
  created_at timestamptz DEFAULT now(),
  read_at timestamptz,
  dismissed_at timestamptz
);
```

## 🔄 Event Flow Design

### Timeline Events (Knowledge Story)
```
Substrate Approved → knowledge.evolved
Document Composed → document.created  
Reflections Ready → insights.discovered
Major Upload Batch → memory.captured
```

### Notification Events (Actionable Alerts)
```
Proposal Submitted → approval.required
Processing Complete → processing.completed
Upload Failed → error.attention
Document Ready → document.ready
```

### No Overlap Examples:
- ✅ **Timeline**: "Knowledge evolved - 3 blocks approved"
- ✅ **Notification**: "Review proposal - 2 blocks pending approval"
- ❌ **No more**: Timeline AND notification for same substrate creation

## 📱 Frontend Architecture

### Timeline Component (Knowledge Story)
```typescript
// Simple, focused component
<KnowledgeTimeline basketId={id} />

// Queries: GET /api/baskets/{id}/knowledge-timeline
// Shows: Major knowledge milestones only
// UX: Story-like, progressive disclosure
```

### Notification Component (Action Center)  
```typescript
// Real-time, actionable component
<ActionCenter />

// Queries: GET /api/user/alerts + real-time subscription
// Shows: Things requiring attention/awareness
// UX: Badge counts, action buttons, dismissible
```

## 🗂️ Implementation Strategy

### Phase 1: Create New Clean Tables
- ✅ Create `knowledge_timeline` table
- ✅ Create `user_alerts` table (simplified)
- ✅ Keep old tables during migration

### Phase 2: Update Event Emission
- ✅ New timeline events: Only major milestones
- ✅ New notifications: Only actionable/completion alerts
- ✅ Stop dual-emission to old systems

### Phase 3: Frontend Migration
- ✅ New KnowledgeTimeline component
- ✅ New ActionCenter component  
- ✅ Remove old timeline implementations
- ✅ Remove old notification complexity

### Phase 4: Legacy Cleanup
- ✅ Drop old `timeline_events` table
- ✅ Drop old `user_notifications` table
- ✅ Remove unused notification types/channels
- ✅ Clean up service layer complexity

## 🎯 Success Metrics

### Timeline (Knowledge Story)
- **Event volume**: 90% reduction (40+ → 8 types)
- **User clarity**: Focus on "knowledge journey" not "processing steps"  
- **Performance**: Simpler queries, fewer events

### Notifications (Action Center)
- **Actionability**: 80% of notifications require user action
- **Relevance**: Significant reduction in notification fatigue
- **Response time**: Clear action paths for each alert

## 🚀 Canon v2.3 Alignment

### Timeline
- **Artifact-like**: Derived view of knowledge evolution
- **Direct API**: Simple REST, no governance needed
- **User-focused**: Knowledge story, not technical audit

### Notifications  
- **Service layer**: Real-time system communication
- **Action-oriented**: Clear user response paths
- **Ephemeral**: Auto-dismiss, not permanent record

**Clean separation**: Historical storytelling vs immediate action needs.