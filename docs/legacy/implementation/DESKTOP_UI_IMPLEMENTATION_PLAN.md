# Desktop UI Implementation Plan

**Version**: 1.0
**Date**: 2025-12-07
**Status**: Approved for Implementation
**Author**: Claude Code + User Collaboration
**Dependencies**: Chat-First Architecture v1.0, TP Implementation

---

## Executive Summary

This document outlines the implementation of the **Desktop UI** pattern for YARNNN's Thinking Partner interface. The core concept is **chat as wallpaper** - a persistent, always-visible chat layer with floating windows that overlay on top, triggered by TP tool executions.

### Core Metaphor

Like a macOS desktop where apps float over the wallpaper:
- **Chat = Desktop wallpaper**: Always visible, fixed, the "home" you never leave
- **Windows = Floating panels**: Context, Work, Outputs, Recipes - open/close/stack
- **Dock = Top bar**: Quick access to minimized windows with notification badges

### Key Differentiators from Previous Approaches

| Previous Approach | Desktop UI Approach |
|-------------------|---------------------|
| Right panel (60/40 split) | Full-overlay floating windows |
| Side-by-side layout steals space | Windows float on top, chat remains full-width |
| Panel open = chat cramped | Window open = focused view, chat visible behind |
| Static panel tabs | Dynamic windows triggered by TP actions |

---

## 1. Visual Architecture

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                      │
│  │ 📋   │ │ ⚡•  │ │ 📊   │ │ 🎯   │ │ 📅   │     ← Top Dock       │
│  │Context│ │Work │ │Output│ │Recipe│ │Sched │                      │
│  │  (2) │ │ (1) │ │      │ │      │ │      │                      │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   TP Chat (Wallpaper Layer - Always Full Width)                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ User: Research AI agent platforms                           │   │
│   └─────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ TP: I'll run deep research. Here's what I'm using:          │   │
│   │                                                             │   │
│   │  ┌─────────────────────────────────┐                        │   │
│   │  │ 🔗 Context: 2 items attached    │  ← In-chat indicator   │   │
│   │  │    customer, problem            │    (clickable)         │   │
│   │  └─────────────────────────────────┘                        │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   ╔═══════════════════════════════════════════════╗                │
│   ║ 📋 Context                       [_] [×]      ║ ← Floating     │
│   ║ ──────────────────────────────────────────    ║   Window       │
│   ║ 🏷️ Foundation                                ║   (Centered    │
│   ║ ┌─────────────────────────────────────────┐  ║    Overlay)    │
│   ║ │ 👥 Customer                    ✓ used   │  ║                │
│   ║ │ Solo founders building products...      │  ║                │
│   ║ └─────────────────────────────────────────┘  ║                │
│   ║ ┌─────────────────────────────────────────┐  ║                │
│   ║ │ 🎯 Problem                     ✓ used   │  ║                │
│   ║ │ Manual work overhead...                 │  ║                │
│   ║ └─────────────────────────────────────────┘  ║                │
│   ╚═══════════════════════════════════════════════╝                │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ Ask Thinking Partner...                                 ▶   │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Window Overlay Behavior

When a window is open:
- Window appears **centered** over the chat
- Chat remains visible but **dimmed/blurred** behind
- Clicking outside the window (on chat backdrop) closes the window
- Window is the **primary focus** - not a side panel

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Dock]                                                             │
├─────────────────────────────────────────────────────────────────────┤
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░╔═══════════════════════════════════╗░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░║ 📋 Context              [_] [×]   ║░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░║ ─────────────────────────────────  ║░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░║ Content here...                   ║░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░║                                   ║░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░║                                   ║░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░║                                   ║░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░╚═══════════════════════════════════╝░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Ask Thinking Partner...                                 ▶   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
     ↑ Chat visible but dimmed (backdrop-blur + opacity)
```

---

## 2. Window Types and Content

### 2.1 Window Definitions

| Window ID | Icon | Label | Content | Triggered By |
|-----------|------|-------|---------|--------------|
| `context` | 📋 | Context | Context items by tier | `read_context`, `write_context`, `list_context` |
| `work` | ⚡ | Work | Active work tickets | `trigger_recipe`, work ticket events |
| `outputs` | 📊 | Outputs | Work outputs for review | Work completion, `emit_work_output` |
| `recipes` | 🎯 | Recipes | Available recipes | `list_recipes` |
| `schedule` | 📅 | Schedule | Scheduled work | `schedule_recipe` (future) |

### 2.2 Window Content Components

Reuse and adapt existing detail panel components:

```typescript
// Existing components to reuse
ContextDetailPanel   → ContextWindowContent
OutputsDetailPanel   → OutputsWindowContent
TicketsDetailPanel   → WorkWindowContent

// New components needed
RecipesWindowContent  // List available recipes
ScheduleWindowContent // Scheduled work (future)
```

### 2.3 Window State

```typescript
interface WindowState {
  isOpen: boolean;
  isMinimized: boolean;      // In dock, not visible
  zIndex: number;            // For stacking (if multiple open)
  highlight?: {
    itemIds?: string[];      // Items to highlight (e.g., "these are being used")
    action?: 'reading' | 'writing' | 'using';
  };
}
```

---

## 3. In-Chat Indicators

Small, inline badges in messages that link to windows:

### 3.1 Indicator Types

```typescript
// Context usage indicator
┌─────────────────────────────────┐
│ 🔗 Context: 2 items attached    │
│    customer, problem            │
│    [View in window →]           │
└─────────────────────────────────┘

// Work started indicator
┌─────────────────────────────────┐
│ ⚡ Work Started: Deep Research  │
│    Recipe: research.deep_dive   │
│    [View Progress →]            │
└─────────────────────────────────┘

// Output ready indicator
┌─────────────────────────────────┐
│ 📊 Output Ready: 3 findings     │
│    Pending review               │
│    [Review Outputs →]           │
└─────────────────────────────────┘
```

### 3.2 Indicator Behavior

- Click indicator → Opens corresponding window
- Indicator persists in message (doesn't scroll away with chat)
- Indicators update badges in dock when created

---

## 4. Dock Behavior

### 4.1 Dock Location

**Top of screen** (not bottom) because:
1. Avoids conflict with OS docks (macOS, Windows)
2. Chat input is at bottom - dock at top balances layout
3. Natural "tab bar" position for web apps

### 4.2 Dock Item States

```typescript
interface DockItemState {
  badge?: number;           // Count (e.g., "2" items used)
  pulse?: boolean;          // Attention indicator (e.g., new output)
  active?: boolean;         // Window is currently open
  notification?: string;    // Tooltip on hover
}
```

### 4.3 Dock Visual States

```
Normal:        Active:        Badge:         Pulse:
┌──────┐      ┌──────┐       ┌──────┐       ┌──────┐
│ 📋   │      │ 📋   │       │ 📋   │       │ 📋 • │
│Context│     │Context│      │Context│      │Context│
│      │      │ ──── │       │  (2) │       │      │
└──────┘      └──────┘       └──────┘       └──────┘
              ↑ underline     ↑ badge        ↑ pulse dot
```

---

## 5. TP Tool → Window Trigger Matrix

| TP Tool Call | Window Opened | Highlight | Dock Badge |
|--------------|---------------|-----------|------------|
| `read_context(types)` | context | Items being read | Count of items |
| `write_context(type, content)` | context | New/updated item | +1 |
| `list_context()` | None (info only) | - | - |
| `trigger_recipe(slug)` | work | New ticket | +1 |
| `list_recipes()` | recipes | - | - |
| Work ticket completes | outputs | New outputs | Count pending |
| `emit_work_output(...)` | outputs | New output | +1 |
| `schedule_recipe(...)` | schedule | New schedule | +1 |

### 5.1 Trigger Logic

```typescript
// In TP response handler
const handleTPToolCall = (toolCall: ToolCall, result: ToolResult) => {
  const { openWindow, setHighlight, setBadge, setPulse } = useDesktop();

  switch (toolCall.name) {
    case 'read_context':
      openWindow('context');
      setHighlight('context', {
        itemIds: result.items.map(i => i.id),
        action: 'reading'
      });
      setBadge('context', result.items.length);
      break;

    case 'write_context':
      openWindow('context');
      setHighlight('context', {
        itemIds: [result.item_id],
        action: 'writing'
      });
      setBadge('context', prev => prev + 1);
      break;

    case 'trigger_recipe':
      openWindow('work');
      setHighlight('work', {
        itemIds: [result.ticket_id],
        action: 'using'
      });
      setBadge('work', prev => prev + 1);
      setPulse('work', true);
      break;

    case 'list_recipes':
      openWindow('recipes');
      break;
  }
};
```

### 5.2 Window Auto-Close Rules

To avoid window clutter:
1. Only one window open at a time (new open closes previous)
2. OR: Allow stacking with z-index, most recent on top
3. User can close anytime via [×] or backdrop click
4. Auto-close after N seconds of inactivity (optional, default: off)

**Phase 1 Decision**: Single window at a time. Simpler UX, easier to implement.

---

## 6. Component Architecture

### 6.1 New Directory Structure

```
work-platform/web/
├── components/
│   └── desktop/                      # New: Desktop UI system
│       ├── DesktopProvider.tsx       # React Context + state management
│       ├── Desktop.tsx               # Main layout container
│       ├── Dock.tsx                  # Top dock bar
│       ├── DockItem.tsx              # Individual dock icon
│       ├── Window.tsx                # Base floating window
│       ├── WindowBackdrop.tsx        # Dimmed/blurred backdrop
│       ├── windows/                  # Window content components
│       │   ├── ContextWindowContent.tsx
│       │   ├── WorkWindowContent.tsx
│       │   ├── OutputsWindowContent.tsx
│       │   ├── RecipesWindowContent.tsx
│       │   └── ScheduleWindowContent.tsx
│       └── index.ts                  # Barrel export
│
├── components/thinking/
│   └── chat-indicators/              # In-chat indicators
│       ├── ContextIndicator.tsx
│       ├── WorkIndicator.tsx
│       ├── OutputIndicator.tsx
│       └── index.ts
│
└── hooks/
    └── useDesktop.ts                 # Hook for controlling windows
```

### 6.2 State Management

```typescript
// DesktopProvider.tsx

type WindowId = 'context' | 'work' | 'outputs' | 'recipes' | 'schedule';

interface DesktopState {
  windows: Record<WindowId, WindowState>;
  dock: Record<WindowId, DockItemState>;
  activeWindow: WindowId | null;
}

interface WindowState {
  isOpen: boolean;
  highlight?: {
    itemIds?: string[];
    action?: 'reading' | 'writing' | 'using';
  };
}

interface DockItemState {
  badge?: number;
  pulse?: boolean;
}

type DesktopAction =
  | { type: 'OPEN_WINDOW'; windowId: WindowId; highlight?: WindowState['highlight'] }
  | { type: 'CLOSE_WINDOW'; windowId: WindowId }
  | { type: 'CLOSE_ALL_WINDOWS' }
  | { type: 'SET_BADGE'; windowId: WindowId; badge: number }
  | { type: 'INCREMENT_BADGE'; windowId: WindowId }
  | { type: 'SET_PULSE'; windowId: WindowId; pulse: boolean }
  | { type: 'CLEAR_HIGHLIGHT'; windowId: WindowId };

function desktopReducer(state: DesktopState, action: DesktopAction): DesktopState {
  switch (action.type) {
    case 'OPEN_WINDOW':
      return {
        ...state,
        activeWindow: action.windowId,
        windows: {
          ...state.windows,
          // Close all other windows (single window mode)
          ...Object.keys(state.windows).reduce((acc, id) => ({
            ...acc,
            [id]: { ...state.windows[id as WindowId], isOpen: id === action.windowId }
          }), {}),
          [action.windowId]: {
            isOpen: true,
            highlight: action.highlight,
          },
        },
        dock: {
          ...state.dock,
          [action.windowId]: {
            ...state.dock[action.windowId],
            pulse: false, // Clear pulse when opened
          },
        },
      };
    // ... other cases
  }
}
```

### 6.3 useDesktop Hook

```typescript
// hooks/useDesktop.ts

export function useDesktop() {
  const context = useContext(DesktopContext);
  if (!context) {
    throw new Error('useDesktop must be used within DesktopProvider');
  }

  const { state, dispatch } = context;

  return {
    // Window controls
    openWindow: (windowId: WindowId, highlight?: WindowState['highlight']) =>
      dispatch({ type: 'OPEN_WINDOW', windowId, highlight }),
    closeWindow: (windowId: WindowId) =>
      dispatch({ type: 'CLOSE_WINDOW', windowId }),
    closeAllWindows: () =>
      dispatch({ type: 'CLOSE_ALL_WINDOWS' }),

    // Dock controls
    setBadge: (windowId: WindowId, badge: number) =>
      dispatch({ type: 'SET_BADGE', windowId, badge }),
    incrementBadge: (windowId: WindowId) =>
      dispatch({ type: 'INCREMENT_BADGE', windowId }),
    setPulse: (windowId: WindowId, pulse: boolean) =>
      dispatch({ type: 'SET_PULSE', windowId, pulse }),

    // State accessors
    activeWindow: state.activeWindow,
    isWindowOpen: (windowId: WindowId) => state.windows[windowId]?.isOpen,
    getHighlight: (windowId: WindowId) => state.windows[windowId]?.highlight,
    getBadge: (windowId: WindowId) => state.dock[windowId]?.badge,
    isPulsing: (windowId: WindowId) => state.dock[windowId]?.pulse,
  };
}
```

---

## 7. Integration with Existing Components

### 7.1 Replacing ChatFirstLayout

The new Desktop component will replace the current `ChatFirstLayout`:

```typescript
// Before (ChatFirstLayout - side panel)
<ChatFirstLayout
  contextPanel={<ContextDetailPanel />}
  outputsPanel={<OutputsDetailPanel />}
  ...
>
  <TPChatInterface />
</ChatFirstLayout>

// After (Desktop - floating windows)
<Desktop>
  <TPChatInterface />
</Desktop>
```

### 7.2 TPChatInterface Updates

```typescript
// TPChatInterface.tsx - Add indicator rendering

import { useDesktop } from '@/hooks/useDesktop';
import { ContextIndicator, WorkIndicator, OutputIndicator } from './chat-indicators';

// In message rendering
{message.context_changes?.length > 0 && (
  <ContextIndicator
    changes={message.context_changes}
    onClick={() => openWindow('context', { itemIds: message.context_changes.map(c => c.item_id) })}
  />
)}

{message.recipe_execution && (
  <WorkIndicator
    execution={message.recipe_execution}
    onClick={() => openWindow('work', { itemIds: [message.recipe_execution.ticket_id] })}
  />
)}

{message.work_outputs?.length > 0 && (
  <OutputIndicator
    outputs={message.work_outputs}
    onClick={() => openWindow('outputs', { itemIds: message.work_outputs.map(o => o.id) })}
  />
)}
```

### 7.3 ThinkingAgentClient Updates

```typescript
// ThinkingAgentClient.tsx - Use Desktop instead of ChatFirstLayout

import { Desktop, DesktopProvider } from '@/components/desktop';

export function ThinkingAgentClient({ ... }) {
  return (
    <DesktopProvider basketId={basketId}>
      <div className="flex h-full flex-col">
        {/* Header stays the same */}
        <header>...</header>

        {/* Desktop replaces ChatFirstLayout */}
        <div className="flex-1 overflow-hidden">
          <Desktop>
            <TPChatInterface
              basketId={basketId}
              workspaceId={workspaceId}
            />
          </Desktop>
        </div>
      </div>
    </DesktopProvider>
  );
}
```

---

## 8. Implementation Phases

### Phase 1: Core Desktop System (MVP)

**Goal**: Basic floating window system with dock

**Tasks**:
1. Create `DesktopProvider` with state management
2. Create `Desktop` container component
3. Create `Dock` and `DockItem` components
4. Create `Window` and `WindowBackdrop` components
5. Create `useDesktop` hook
6. Wire up Context window with existing `ContextDetailPanel` content

**Deliverables**:
- Desktop layout with chat as wallpaper
- Top dock with 5 window icons
- Context window opens/closes via dock click
- Backdrop click closes window

**Files to Create**:
- `components/desktop/DesktopProvider.tsx`
- `components/desktop/Desktop.tsx`
- `components/desktop/Dock.tsx`
- `components/desktop/DockItem.tsx`
- `components/desktop/Window.tsx`
- `components/desktop/WindowBackdrop.tsx`
- `components/desktop/windows/ContextWindowContent.tsx`
- `components/desktop/index.ts`
- `hooks/useDesktop.ts`

### Phase 2: Window Contents

**Goal**: All window types with content

**Tasks**:
1. Create `WorkWindowContent` (active tickets)
2. Create `OutputsWindowContent` (outputs for review)
3. Create `RecipesWindowContent` (available recipes)
4. Stub `ScheduleWindowContent` (future)
5. Add highlighting support (items "in use")

**Files to Create**:
- `components/desktop/windows/WorkWindowContent.tsx`
- `components/desktop/windows/OutputsWindowContent.tsx`
- `components/desktop/windows/RecipesWindowContent.tsx`
- `components/desktop/windows/ScheduleWindowContent.tsx`

### Phase 3: In-Chat Indicators

**Goal**: Inline indicators that link to windows

**Tasks**:
1. Create `ContextIndicator` component
2. Create `WorkIndicator` component
3. Create `OutputIndicator` component
4. Integrate into `TPMessageList` rendering
5. Wire indicator clicks to window opening

**Files to Create**:
- `components/thinking/chat-indicators/ContextIndicator.tsx`
- `components/thinking/chat-indicators/WorkIndicator.tsx`
- `components/thinking/chat-indicators/OutputIndicator.tsx`
- `components/thinking/chat-indicators/index.ts`

**Files to Modify**:
- `components/thinking/TPMessageList.tsx`

### Phase 4: TP Tool Integration

**Goal**: Windows open automatically on TP tool calls

**Tasks**:
1. Create tool call handler utility
2. Integrate handler into TP response processing
3. Add badge/pulse updates on tool results
4. Test all trigger scenarios

**Files to Create**:
- `lib/desktop/tool-handlers.ts`

**Files to Modify**:
- `hooks/useTPChat.ts` (add desktop integration)

### Phase 5: Polish & Cleanup

**Goal**: Remove old layout, refine UX

**Tasks**:
1. Remove `ChatFirstLayout` usage from `ThinkingAgentClient`
2. Remove or deprecate `ChatFirstLayout` component
3. Add keyboard shortcuts (Esc to close, etc.)
4. Add window animations (open/close transitions)
5. Add responsive behavior (mobile: full-screen windows)

---

## 9. Window Component Specification

### 9.1 Window Props

```typescript
interface WindowProps {
  windowId: WindowId;
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}
```

### 9.2 Window Layout

```typescript
// Window.tsx

export function Window({ windowId, title, icon, children, className }: WindowProps) {
  const { closeWindow, getHighlight } = useDesktop();
  const highlight = getHighlight(windowId);

  return (
    <div className={cn(
      // Centered overlay
      "fixed inset-0 z-50 flex items-center justify-center",
      className
    )}>
      {/* Backdrop */}
      <WindowBackdrop onClick={() => closeWindow(windowId)} />

      {/* Window */}
      <div className={cn(
        "relative z-10 w-full max-w-2xl max-h-[80vh]",
        "bg-card rounded-lg border border-border shadow-xl",
        "flex flex-col overflow-hidden",
        // Animation
        "animate-in fade-in zoom-in-95 duration-200"
      )}>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            {icon}
            <h2 className="font-semibold">{title}</h2>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => closeWindow(windowId)}
              className="h-8 w-8 p-0"
            >
              <Minimize2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => closeWindow(windowId)}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {children}
        </div>
      </div>
    </div>
  );
}
```

### 9.3 Window Backdrop

```typescript
// WindowBackdrop.tsx

export function WindowBackdrop({ onClick }: { onClick: () => void }) {
  return (
    <div
      className={cn(
        "fixed inset-0 bg-black/40 backdrop-blur-sm",
        "animate-in fade-in duration-200"
      )}
      onClick={onClick}
    />
  );
}
```

---

## 10. Dock Component Specification

### 10.1 Dock Layout

```typescript
// Dock.tsx

const DOCK_ITEMS: Array<{
  id: WindowId;
  icon: React.ElementType;
  label: string;
}> = [
  { id: 'context', icon: FileText, label: 'Context' },
  { id: 'work', icon: Zap, label: 'Work' },
  { id: 'outputs', icon: Lightbulb, label: 'Outputs' },
  { id: 'recipes', icon: Target, label: 'Recipes' },
  { id: 'schedule', icon: Calendar, label: 'Schedule' },
];

export function Dock() {
  return (
    <div className="flex items-center gap-1 border-b border-border bg-muted/30 px-3 py-2">
      {DOCK_ITEMS.map((item) => (
        <DockItem key={item.id} {...item} />
      ))}
    </div>
  );
}
```

### 10.2 DockItem Component

```typescript
// DockItem.tsx

interface DockItemProps {
  id: WindowId;
  icon: React.ElementType;
  label: string;
}

export function DockItem({ id, icon: Icon, label }: DockItemProps) {
  const { openWindow, isWindowOpen, getBadge, isPulsing } = useDesktop();

  const isActive = isWindowOpen(id);
  const badge = getBadge(id);
  const pulse = isPulsing(id);

  return (
    <button
      onClick={() => openWindow(id)}
      className={cn(
        "relative flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-md",
        "text-xs font-medium transition-colors",
        isActive
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      <div className="relative">
        <Icon className="h-4 w-4" />

        {/* Badge */}
        {badge !== undefined && badge > 0 && (
          <span className={cn(
            "absolute -right-1.5 -top-1.5",
            "flex h-4 min-w-4 items-center justify-center",
            "rounded-full bg-primary px-1 text-[10px] text-primary-foreground"
          )}>
            {badge > 9 ? '9+' : badge}
          </span>
        )}

        {/* Pulse indicator */}
        {pulse && (
          <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
        )}
      </div>

      <span>{label}</span>

      {/* Active indicator */}
      {isActive && (
        <span className="absolute bottom-0 left-1/2 h-0.5 w-6 -translate-x-1/2 rounded-full bg-primary" />
      )}
    </button>
  );
}
```

---

## 11. Success Criteria

### Phase 1 (MVP)

- [ ] Chat is always full-width (wallpaper behavior)
- [ ] Dock appears at top with 5 icons
- [ ] Clicking dock item opens floating window
- [ ] Window appears centered with backdrop
- [ ] Clicking backdrop closes window
- [ ] [×] button closes window
- [ ] Context window shows context items

### Phase 2

- [ ] All 5 window types have content
- [ ] Items can be highlighted ("in use" state)
- [ ] Badges show counts on dock items

### Phase 3

- [ ] In-chat indicators render in messages
- [ ] Clicking indicator opens corresponding window
- [ ] Indicators show relevant metadata

### Phase 4

- [ ] TP tool calls automatically open windows
- [ ] Badges update on tool results
- [ ] Pulse animation for attention

### Phase 5

- [ ] Old ChatFirstLayout removed
- [ ] Keyboard shortcuts work (Esc to close)
- [ ] Animations are smooth
- [ ] Mobile responsive (full-screen windows)

---

## 12. Migration Notes

### Components to Deprecate

After Desktop UI is complete:
- `ChatFirstLayout.tsx` - Replaced by `Desktop.tsx`
- `detail-panels/` directory - Content moved to `desktop/windows/`

### Components to Keep

- `chat-cards/` - Still used for in-chat card displays
- `TPChatInterface.tsx` - Core chat, just wrapped differently
- `TPMessageList.tsx` - Message rendering, adds indicators

---

## 13. Related Documentation

- [CHAT_FIRST_ARCHITECTURE_V1.md](../architecture/CHAT_FIRST_ARCHITECTURE_V1.md) - Previous architecture
- [THINKING_PARTNER_IMPLEMENTATION_PLAN.md](./THINKING_PARTNER_IMPLEMENTATION_PLAN.md) - TP backend
- [THINKING_PARTNER.md](../canon/THINKING_PARTNER.md) - TP philosophy

---

## Appendix A: Window Sizing

| Screen Size | Window Size | Behavior |
|-------------|-------------|----------|
| Desktop (≥1280px) | max-w-2xl (672px), max-h-[80vh] | Centered overlay |
| Tablet (768-1279px) | max-w-lg (512px), max-h-[85vh] | Centered overlay |
| Mobile (<768px) | Full screen | Full viewport with header |

---

## Appendix B: Animation Specs

```css
/* Window open */
.window-enter {
  animation: window-in 200ms ease-out;
}

@keyframes window-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Window close */
.window-exit {
  animation: window-out 150ms ease-in;
}

@keyframes window-out {
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(0.95);
  }
}

/* Backdrop */
.backdrop-enter {
  animation: fade-in 200ms ease-out;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

---

**Document Status**: Approved for Implementation
**Last Updated**: 2025-12-07
**Next Action**: Begin Phase 1 implementation
