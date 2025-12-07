# Desktop UI User Flows

**Version**: 1.0
**Date**: 2025-12-07
**Status**: Draft for Review
**Context**: Documents user journeys under the new Desktop UI paradigm

---

## Executive Summary

The Desktop UI fundamentally changes how users interact with YARNNN. Instead of navigating between pages with a TP sidebar, users now:

1. **Chat with TP as the primary interface** (the "wallpaper")
2. **View results in floating windows** triggered by TP actions
3. **Use dock icons** for quick access to Context, Work, Outputs, Recipes, Schedule

This document maps out user journeys to identify:
- What the onboarding experience should look like
- Which existing pages remain essential vs. become "advanced views"
- How users interact with TP when not actively chatting
- Gaps and open questions

---

## 1. Mental Model Shift

### Previous Model (Page-Centric + Sidebar TP)

```
┌─────────────────────────────────────────────────────────────┐
│ [Nav: Overview | Context | Work Tickets | Schedules | ...]  │
├─────────────────────────────────────────────────────────────┤
│                                              │              │
│   Page Content                               │   TP         │
│   (e.g., Context list,                       │   Sidebar    │
│    Work tickets table)                       │   Chat       │
│                                              │              │
│   ← User navigates here                      │   ← Helper   │
│                                              │              │
└─────────────────────────────────────────────────────────────┘

User thinks: "I go to pages to do work, TP helps me on the side"
```

### New Model (Chat-Centric + Desktop Windows)

```
┌─────────────────────────────────────────────────────────────┐
│ [Dock: Context | Work | Outputs | Recipes | Schedule]       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   TP Chat (Full Width)                                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ Me: Research AI agent platforms                     │   │
│   │                                                     │   │
│   │ TP: I found 5 competitors. [Context: 2 items] ←─────┼───┼─→ Click opens window
│   │     Starting deep research. [Work: Running] ←───────┼───┼─→ Click opens window
│   │                                                     │   │
│   │ [Ask TP...]                                         │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
│   ← User works HERE, windows show results                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

User thinks: "I tell TP what I need, windows show the results"
```

---

## 2. User Journeys

### 2.1 New User: First-Time Experience

**Current Flow:**
1. Sign up / Login → `/welcome` onboarding
2. Complete profile (identity genesis)
3. Redirect to `/projects` (project list)
4. Create or select project
5. Land on `/projects/[id]/overview`
6. Discover TP sidebar by clicking or noticing it

**Proposed Flow (Desktop UI):**

```
Sign Up → Welcome Wizard → Create First Project
                              ↓
         ┌────────────────────────────────────────────────┐
         │  "Welcome to your project workspace!"          │
         │                                                │
         │  This is your Thinking Partner.                │
         │  Chat here to:                                 │
         │  • Define your project's context               │
         │  • Research competitors and markets            │
         │  • Generate content and strategies             │
         │                                                │
         │  [Dock icons highlighted with tooltips]        │
         │  ↑ Results appear here when TP works           │
         │                                                │
         │  ┌────────────────────────────────────────┐    │
         │  │ Try: "Help me define my target         │    │
         │  │       customer for this project"       │    │
         │  └────────────────────────────────────────┘    │
         │                                                │
         └────────────────────────────────────────────────┘
```

**Key Changes:**
- First project creation happens in `/welcome` flow
- User lands **directly in TP Desktop UI** (not overview page)
- Brief guided tour introduces dock + chat interaction model
- Suggested first message gets them started immediately

**Open Questions:**
- [ ] Do we create a default project during onboarding, or let user create one?
- [ ] Should overview page even exist for new users, or just TP?
- [ ] How much "hand-holding" in the tour vs. letting them explore?

---

### 2.2 Returning User: Project Resume

**Current Flow:**
1. Login → `/projects` (project list)
2. Select project → `/projects/[id]/overview`
3. Click TP sidebar to chat
4. Navigate to specific pages for details

**Proposed Flow (Desktop UI):**

```
Login → Project List → Select Project
                          ↓
      ┌──────────────────────────────────────────────────┐
      │ [Context(2)] [Work(1•)] [Outputs(3)] [...]       │  ← Badges show state
      ├──────────────────────────────────────────────────┤
      │                                                  │
      │  Recent conversation with TP...                  │
      │                                                  │
      │  ┌────────────────────────────────────────────┐  │
      │  │ 📋 Context: 2 items attached               │  │  ← Last context used
      │  └────────────────────────────────────────────┘  │
      │                                                  │
      │  ┌────────────────────────────────────────────┐  │
      │  │ ⚡ Work Completed: Research finished       │  │  ← Work done since last visit
      │  │    3 outputs ready for review              │  │
      │  └────────────────────────────────────────────┘  │
      │                                                  │
      │  [Continue chatting...]                          │
      │                                                  │
      └──────────────────────────────────────────────────┘
```

**Key Observations:**
- User sees **dock badges** indicating state changes since last visit
- Chat history shows where they left off
- In-chat indicators highlight completed work
- No need to navigate to pages to see what happened

**Key Question:** Should we show a "What's new" summary at the top when returning?

---

### 2.3 Active Work: Chat-Driven Flow

**Scenario:** User wants to research competitors

**Current Flow:**
1. Navigate to Context page, review existing context
2. Open TP sidebar, ask for research
3. TP responds, suggests recipe
4. Navigate to Work Tickets to see progress
5. Navigate to Outputs to review results
6. Navigate back to Context to see updated items

**Proposed Flow (Desktop UI):**

```
User: "Research the top 5 AI agent platforms competing with us"
        │
        ↓
TP: "I'll use your existing context about your product vision
     and run a deep research recipe."

     [Context: 2 items attached]  ← Click to see what TP is using
     [Work: Deep Research - Running]  ← Click to see progress
        │
        ↓
    (Work completes in background)
        │
        ↓
TP: "Research complete! I found detailed analysis on 5 competitors."

     [Outputs: 3 ready for review]  ← Click to review and approve
        │
        ↓
User clicks [Outputs] indicator or dock icon
        │
        ↓
    ┌──────────────────────────────────────────┐
    │ 📊 Outputs                    [_] [×]    │
    ├──────────────────────────────────────────┤
    │ ⏳ Pending Review                         │
    │ ┌──────────────────────────────────────┐ │
    │ │ Competitor Analysis: Genspark        │ │
    │ │ [Approve] [Edit] [Reject]            │ │
    │ └──────────────────────────────────────┘ │
    │ ...                                      │
    └──────────────────────────────────────────┘
```

**Key Benefits:**
- User never leaves chat
- All actions (view context, check progress, review outputs) via windows
- Clear visibility into what TP is doing at each step

---

### 2.4 Async/Background Work: Returning After Work Completes

**Scenario:** User triggers research, closes browser, returns later

**Current Flow:**
1. Return to project
2. Check Work Tickets page for status
3. Navigate to Outputs to see results
4. Manually cross-reference with Context

**Proposed Flow (Desktop UI):**

```
User returns to project
        │
        ↓
┌──────────────────────────────────────────────────────┐
│ [Context(2)] [Work(✓)] [Outputs(3•)] [...]           │  ← Pulse on Outputs
├──────────────────────────────────────────────────────┤
│                                                      │
│  Previous conversation...                            │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │ ⚡ Work Completed                              │  │
│  │    Deep Research finished 2 hours ago          │  │
│  │    3 outputs ready for review                  │  │
│  │    [Review Outputs →]                          │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Enhancement Opportunity:** Add a "Since you've been away" summary message:

```
┌────────────────────────────────────────────────────┐
│ 🔔 Since you've been away:                         │
│                                                    │
│ • Deep Research completed (2 hours ago)            │
│   → 3 outputs ready for review                     │
│                                                    │
│ • Context updated: competitor_analysis added       │
│                                                    │
│ [Dismiss] [Review Outputs]                         │
└────────────────────────────────────────────────────┘
```

---

### 2.5 Power User: Direct Page Access

**Scenario:** User wants to bulk-edit context items or export data

**Question:** When do users need the traditional pages?

**Page-Appropriate Tasks:**
| Task | Best Interface | Reason |
|------|----------------|--------|
| View single context item | Window | Quick peek |
| Edit context item inline | Window | Quick edit |
| Bulk delete context items | Page | Multi-select, table view |
| Export context to file | Page | Download action |
| View all historical tickets | Page | Pagination, filtering |
| Configure project settings | Page | Form-heavy |
| Manage recipes (admin) | Page | CRUD operations |

**Proposed Hybrid:**
- **Windows** = 80% of tasks (view, quick actions, review)
- **Pages** = 20% of tasks (bulk ops, settings, history, exports)
- Each window has "Open Full Page →" link for power users

---

## 3. Page Hierarchy Re-evaluation

### Current Page Structure

```
/projects/[id]/
├── overview        # Dashboard stats
├── context         # Context items list + CRUD
├── work-tickets-view  # Tickets table
├── schedules       # Scheduled work
├── settings        # Project config
└── agents/
    ├── thinking    # TP Desktop UI ← NEW PRIMARY
    ├── research    # Research agent dashboard
    └── content     # Content agent dashboard
```

### Proposed Changes

| Page | Current Role | Proposed Role | Action |
|------|--------------|---------------|--------|
| `/overview` | Dashboard | Optional summary | Keep, but not default landing |
| `/context` | Context CRUD | Bulk operations only | Keep for power users |
| `/work-tickets-view` | Tickets table | Historical view, filtering | Keep for power users |
| `/schedules` | Schedule management | Direct access (no window equivalent?) | Keep |
| `/settings` | Project config | No change | Keep |
| `/agents/thinking` | TP page | **Default project landing** | Elevate |
| `/agents/research` | Agent dashboard | Secondary | Demote or merge |
| `/agents/content` | Agent dashboard | Secondary | Demote or merge |

### Default Landing Change

**Current:** `/projects/[id]` → redirects to `/projects/[id]/overview`

**Proposed:** `/projects/[id]` → redirects to `/projects/[id]/agents/thinking`

This makes TP the default experience, with navigation to other pages as needed.

---

## 4. Navigation Redesign Options

### Option A: Keep Current Nav, Add TP as Default

```
[Overview] [Context] [Work Tickets] [Schedules] [Settings]

TP is just another page, but it's the default landing.
Sidebar TP hidden when on /agents/thinking.
```

**Pros:** Minimal change, familiar nav pattern
**Cons:** TP feels like "just another page," not the central hub

### Option B: TP-Centric Nav with Page Links

```
[Thinking Partner]                    [Pages ▾] [Settings]
                                        ├─ Overview
                                        ├─ Context (full)
                                        ├─ Work History
                                        └─ Schedules
```

**Pros:** TP clearly primary, pages demoted to "advanced"
**Cons:** Users may miss pages, bigger redesign

### Option C: Remove Nav on TP, Keep for Other Pages

```
On /agents/thinking:
  [No nav bar - just dock]

On other pages:
  [Overview] [Context] [Work Tickets] [Schedules] [Settings]
  + TP Sidebar
```

**Pros:** Clean TP experience, pages still accessible
**Cons:** Jarring transition between TP and pages

### Option D: Unified Dock + Minimal Nav

```
┌─────────────────────────────────────────────────────────────┐
│ Project: My Startup    [Context] [Work] [Outputs] [...]     │
│                        └── Dock (always visible) ──┘        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   TP Chat or Page Content (depending on route)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘

- Dock is always there
- Clicking dock on TP page = window
- Clicking dock on other pages = navigates to page
- Small [≡ Pages] menu for Settings, Schedules, etc.
```

**Pros:** Consistent dock everywhere, clear hierarchy
**Cons:** Complex behavior (dock does different things in different contexts)

---

## 5. TP When Not Chatting

### Scenarios Where User Isn't Actively Chatting

1. **Reviewing outputs** - Reading generated content, approving/rejecting
2. **Browsing context** - Looking at what TP knows
3. **Checking work status** - Monitoring running tickets
4. **Idle/away** - Browser open but not interacting

### Current Handling

- TP sidebar is always visible
- Realtime updates via Supabase subscriptions
- No proactive notifications

### Proposed Enhancements

#### 5.1 Work Status Toast Notifications

When work completes while user is on the page:

```
┌───────────────────────────────────────┐
│ ✅ Deep Research completed            │
│    3 outputs ready for review         │
│    [View] [Dismiss]                   │
└───────────────────────────────────────┘
```

#### 5.2 Dock Badge Updates (Already Implemented)

Badges and pulse indicators show real-time changes.

#### 5.3 "Away" Summary (New)

When returning after inactivity:

```
TP: "While you were away:
     • Research completed with 3 findings
     • I updated competitor_analysis in context

     Want me to summarize the results?"
```

#### 5.4 Browser Notifications (Optional, User-Enabled)

```
🔔 YARNNN: Research completed - 3 outputs ready
   [View Now]
```

---

## 6. Open Questions for Decision

### Onboarding

1. **First project creation:** During `/welcome` flow or after landing on `/projects`?
2. **First-time TP experience:** Guided tour vs. suggested first message vs. both?
3. **Empty state:** What does TP say when project has no context yet?

### Navigation

4. **Default landing:** Change from `/overview` to `/agents/thinking`?
5. **Nav bar design:** Which option (A/B/C/D) or hybrid?
6. **Page access:** "Open Full Page" in windows, or separate nav?

### Pages

7. **Overview page:** Keep, deprecate, or merge into TP summary?
8. **Context page:** Keep for bulk ops, or build bulk ops into window?
9. **Agent dashboards:** Keep separate or consolidate into TP?

### TP Behavior

10. **Returning user summary:** Auto-show "since you've been away"?
11. **Browser notifications:** Offer as opt-in setting?
12. **Empty chat history:** Prompt user or show recent project activity?

---

## 7. Recommended Next Steps

### Immediate (Before More Implementation)

1. **Decide on default landing** - `/overview` vs `/agents/thinking`
2. **Decide on nav pattern** - Keep current or redesign?
3. **Sketch onboarding flow** - What does first-time TP experience look like?

### Short-Term (During Implementation)

4. **Add "Open Full Page" links** to windows
5. **Implement returning user summary** in chat
6. **Add toast notifications** for work completion

### Medium-Term (Polish)

7. **Onboarding tour** for first-time TP users
8. **Browser notification opt-in**
9. **Page consolidation** (if decided)

---

## 8. Visual Flow Diagrams

### New User Journey

```
                    ┌─────────────┐
                    │   Sign Up   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  /welcome   │
                    │  Onboarding │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Create    │
                    │   Project   │
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │  /projects/[id]/agents/ │
              │       thinking          │
              │                         │
              │  [Guided Tour Overlay]  │
              │  "Welcome! Chat here..."│
              │                         │
              │  ┌───────────────────┐  │
              │  │ Suggested: "Help  │  │
              │  │ me define my..."  │  │
              │  └───────────────────┘  │
              └─────────────────────────┘
```

### Returning User Journey

```
              ┌─────────────┐
              │    Login    │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  /projects  │
              │   (list)    │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │   Select    │
              │   Project   │
              └──────┬──────┘
                     │
    ┌────────────────▼─────────────────┐
    │  /projects/[id]/agents/thinking  │
    │                                  │
    │  [Dock badges show changes]      │
    │  [Outputs(3•)] ← pulse           │
    │                                  │
    │  Chat: "Since you left..."       │
    │        [Work completed]          │
    │        [3 outputs ready]         │
    │                                  │
    └──────────────────────────────────┘
```

### Active Session Flow

```
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │  User types in chat                                     │
    │         │                                               │
    │         ▼                                               │
    │  TP responds with action                                │
    │         │                                               │
    │         ├──→ Context used? → Badge on Context dock      │
    │         │                    In-chat [Context] indicator│
    │         │                                               │
    │         ├──→ Work triggered? → Badge on Work dock       │
    │         │                      In-chat [Work] indicator │
    │         │                      (pulse while running)    │
    │         │                                               │
    │         └──→ Outputs ready? → Badge on Outputs dock     │
    │                               In-chat [Outputs] indicator│
    │                               Toast notification        │
    │                                                         │
    │  User clicks indicator or dock                          │
    │         │                                               │
    │         ▼                                               │
    │  Window opens (floating, centered)                      │
    │         │                                               │
    │         ├──→ View details                               │
    │         ├──→ Take action (approve, edit, etc.)          │
    │         └──→ Close window → back to chat                │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
```

---

## Appendix A: Comparison with Similar Products

### ChatGPT Canvas
- Chat + canvas (right panel for artifacts)
- Canvas is for single artifact editing
- User switches between chat and canvas modes

### Claude Artifacts
- Chat + artifact viewer (right panel)
- Artifacts are outputs, not inputs
- No "dock" concept

### YARNNN Desktop UI (Proposed)
- Chat + multiple typed windows
- Windows are both inputs (context) and outputs (work results)
- Dock provides quick access to all window types
- Windows are transient overlays, not persistent panels

---

## Appendix B: Migration Considerations

### Users with Existing Projects

- Existing projects should work without changes
- First visit after update could show brief "What's New" modal
- No data migration needed (UI only)

### Saved Bookmarks

- `/projects/[id]/overview` still works
- `/projects/[id]/context` still works
- New default just changes redirect behavior

### API Compatibility

- No API changes needed
- All existing endpoints continue to work

---

**Document Status**: Draft for Review
**Last Updated**: 2025-12-07
**Next Action**: Review and decide on open questions (Section 6)
