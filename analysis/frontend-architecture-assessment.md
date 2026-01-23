# Frontend Architecture Assessment

> **Status**: Audit Complete
> **Date**: January 2026
> **Purpose**: Assess frontend alignment with product vision

---

## Executive Summary

**The frontend is structurally complete but underutilizes the backend's memory capabilities.**

| Page | Status | Gap |
|------|--------|-----|
| **Companion Page** | ✅ Feature-complete | UI exists for threads, facts, patterns - will populate once thread extraction is wired |
| **Chat Page** | ⚠️ Functional but isolated | No memory context shown - chat feels disconnected from companion "knowing" you |
| **Dashboard** | ✅ Good | Shows memory preview, links to companion |

### Key Insight

The Companion page is ready to display threads, follow-ups, and patterns. The gap was in the **backend wiring** (now fixed). Once users have conversations, the Memory tab will populate automatically.

The Chat page, however, has a UX gap: **the companion's "knowledge" is invisible during conversation**. The user can't see that the companion remembers things about them.

---

## Page-by-Page Analysis

### 1. Companion Page (`/companion`)

**File**: [web/src/app/(dashboard)/companion/page.tsx](web/src/app/(dashboard)/companion/page.tsx)

#### Current Structure
```
┌─────────────────────────────────────────────────────────┐
│  [Memory Tab]  [Personality Tab]                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  MEMORY TAB:                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🎯 Active Threads                               │   │
│  │    (expand/collapse, resolve, delete)           │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ❓ Things to Follow Up On                       │   │
│  │    (shows pending follow-ups)                   │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 👤 Things I Know About You                      │   │
│  │    (facts grouped by category)                  │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 💡 Patterns I've Noticed                        │   │
│  │    (mood trends, engagement patterns)           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  PERSONALITY TAB:                                      │
│  - Companion Name                                      │
│  - Support Style (4 options)                           │
│  - Message Schedule (timezone, timing preferences)     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Assessment: ✅ Feature-Complete

| Feature | Status | Notes |
|---------|--------|-------|
| Active Threads display | ✅ Built | Expand/collapse, key details |
| Thread resolve action | ✅ Built | Calls `api.memory.resolveThread()` |
| Thread delete action | ✅ Built | Calls `api.memory.deleteItem()` |
| Follow-ups display | ✅ Built | Shows question, context, date |
| Facts by category | ✅ Built | Grouped display with delete |
| Patterns display | ✅ Built | Human-readable descriptions |
| Companion name edit | ✅ Built | Saves to user preferences |
| Support style select | ✅ Built | 4 options with descriptions |
| Timezone select | ✅ Built | 15 timezone options |
| Message timing | ✅ Built | Exact/around/window options |

#### What's Missing

| Feature | Impact | Priority |
|---------|--------|----------|
| Memory editing (inline) | Can only delete, not edit values | Low |
| Add manual memory | Can't manually tell companion something | Medium |
| Thread status badges | Visual indicator of thread status | Low |
| Pattern confidence display | Patterns don't show confidence level | Low |

---

### 2. Chat Page (`/chat/[id]`)

**File**: [web/src/app/chat/[id]/page.tsx](web/src/app/chat/[id]/page.tsx)

#### Current Structure
```
┌─────────────────────────────────────────────────────────┐
│  [← Back]  Companion Name  [Settings]                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [Assistant message bubble]                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│              ┌─────────────────────────────────────┐   │
│              │ [User message bubble]              │   │
│              └─────────────────────────────────────┘   │
│                                                         │
│  [Streaming indicator when AI is responding]           │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [Text input]                              [Send]       │
└─────────────────────────────────────────────────────────┘
```

#### Assessment: ⚠️ Functional but Isolated

| Feature | Status | Notes |
|---------|--------|-------|
| Message display | ✅ Built | Bubbles with timestamps |
| Streaming responses | ✅ Built | Real-time streaming display |
| Optimistic UI | ✅ Built | User message appears immediately |
| Message history | ✅ Built | Loads 50 most recent |
| Auto-scroll | ✅ Built | Scrolls to new messages |
| Empty state | ✅ Built | Friendly prompt to start |

#### What's Missing (Vision Gap)

| Feature | Impact | Priority |
|---------|--------|----------|
| **Memory context sidebar** | User doesn't see what companion "knows" | High |
| **Active thread indicator** | No awareness of ongoing situations | High |
| **"Why this message?" hint** | No transparency on daily message priority | Medium |
| Conversation topic tags | Can't see what topics are being discussed | Low |
| Mood indicator | No reflection of detected mood | Low |

---

### 3. Dashboard (`/dashboard`)

**File**: [web/src/app/(dashboard)/dashboard/page.tsx](web/src/app/(dashboard)/dashboard/page.tsx)

#### Assessment: ✅ Good

| Feature | Status |
|---------|--------|
| Memory preview card | ✅ Shows threads + follow-ups (limited) |
| Quick chat link | ✅ "Chat Now" button |
| Recent conversations | ✅ Last 5 with topics/mood |
| Check-in time display | ✅ Shows scheduled message time |

---

## The Vision Gap: Chat ↔ Memory Integration

### Problem Statement

The product vision says:
> "A friend who texts you 'it's going to rain today' isn't solving your loneliness because they gave you weather information. They're solving it because **they thought of you**."

Currently, the Chat page provides **no visibility** into the companion's memory. The user:
- Can't see what the companion knows about them
- Can't see active threads being tracked
- Doesn't know why a particular message was sent
- Has no sense of continuity between conversations

### Proposed Solution: Context Drawer

Add a collapsible drawer/sidebar to the Chat page showing:

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Messages]                               │ [Context (collapsed)] → │
├───────────────────────────────────────────┼─────────────────────────┤
│                                           │                         │
│  Message bubbles...                       │  📋 Active Threads      │
│                                           │  • Job search (interviewing) │
│                                           │  • Project deadline (Fri)│
│                                           │                         │
│                                           │  💭 Things I Know       │
│                                           │  • Lives in Tokyo       │
│                                           │  • Software engineer    │
│                                           │                         │
│                                           │  🔔 Following Up On     │
│                                           │  • "How did interview go?"│
│                                           │                         │
├───────────────────────────────────────────┴─────────────────────────┤
│  [Text input]                                              [Send]   │
└─────────────────────────────────────────────────────────────────────┘
```

**Benefits**:
- User sees companion "remembers" them
- Builds trust through transparency
- Creates sense of continuity
- Explains why messages feel personal

---

## Mobile Parity Check

| Feature | Web | Mobile | Notes |
|---------|-----|--------|-------|
| Companion page | ✅ | ✅ | Same 2-tab structure |
| Chat page | ✅ | ✅ | Same bubble UI |
| Memory context in chat | ❌ | ❌ | Both missing |
| Dashboard preview | ✅ | ✅ | Same card |
| Navigation to Companion | Sidebar | Tab bar | Both accessible |

---

## Implementation Roadmap

### Phase 1: Verify Memory Population (Immediate)
- [x] Backend: Wire thread extraction ✅ (done)
- [ ] Test: Have conversations, verify threads appear in Memory tab
- [ ] Test: Verify scheduler uses Priority 1-2 messages

### Phase 2: Chat Context Visibility (High Priority)
- [ ] Add memory context drawer/sidebar to Chat page
- [ ] Show active threads relevant to conversation
- [ ] Show key facts about user
- [ ] Mobile: Bottom sheet or header expansion

### Phase 3: Message Transparency (Medium Priority)
- [ ] "Why this message?" hint on daily check-ins
- [ ] Priority indicator (debug mode)
- [ ] Link daily message to the thread/follow-up that triggered it

### Phase 4: Enhanced Memory Management (Lower Priority)
- [ ] Inline memory editing
- [ ] Manual memory addition
- [ ] Memory importance adjustment
- [ ] Thread status badges

---

## API Endpoints Used

### Currently Used by Frontend

| Endpoint | Web | Mobile | Purpose |
|----------|-----|--------|---------|
| `GET /memory/summary` | ✅ | ✅ | Dashboard preview |
| `GET /memory/full` | ✅ | ✅ | Companion page |
| `DELETE /memory/context/{id}` | ✅ | ✅ | Delete memory |
| `POST /memory/threads/{id}/resolve` | ✅ | ✅ | Resolve thread |
| `PATCH /memory/context/{id}` | ❌ | ❌ | Edit memory (exists, unused) |

### Not Yet Used

| Endpoint | Purpose | Potential Use |
|----------|---------|---------------|
| `PATCH /memory/context/{id}` | Edit memory value | Inline editing in Memory tab |
| `POST /memory` (doesn't exist) | Add manual memory | "Tell companion something" |
| `GET /companion/context` (proposed) | Get context for current message | Chat context drawer |

---

## Success Metrics

### After Phase 1 (Thread Extraction)
- [ ] Active Threads section populates after conversations
- [ ] Follow-ups appear for time-sensitive mentions
- [ ] Patterns show after sufficient conversation history

### After Phase 2 (Chat Context)
- [ ] Users report feeling "known" by companion
- [ ] Reduced "why did you say that?" confusion
- [ ] Higher engagement with memory features

### After Phase 3 (Transparency)
- [ ] Users understand message personalization
- [ ] Trust in companion increases
- [ ] Feature completion for "memory is the product" vision

---

## Files Reference

### Web Frontend
- [web/src/app/(dashboard)/companion/page.tsx](web/src/app/(dashboard)/companion/page.tsx) - Companion page
- [web/src/app/chat/[id]/page.tsx](web/src/app/chat/[id]/page.tsx) - Chat page
- [web/src/app/(dashboard)/dashboard/page.tsx](web/src/app/(dashboard)/dashboard/page.tsx) - Dashboard
- [web/src/lib/api/client.ts](web/src/lib/api/client.ts) - API client

### Mobile Frontend
- [mobile/app/(main)/companion.tsx](mobile/app/(main)/companion.tsx) - Companion screen
- [mobile/app/(main)/chat/[id].tsx](mobile/app/(main)/chat/[id].tsx) - Chat screen
- [mobile/app/(main)/index.tsx](mobile/app/(main)/index.tsx) - Dashboard
- [mobile/lib/api/client.ts](mobile/lib/api/client.ts) - API client

### Related Backend
- [api/api/src/app/routes/memory.py](api/api/src/app/routes/memory.py) - Memory API
- [api/api/src/app/services/threads.py](api/api/src/app/services/threads.py) - Thread service
- [api/api/src/app/services/context.py](api/api/src/app/services/context.py) - Context extraction
