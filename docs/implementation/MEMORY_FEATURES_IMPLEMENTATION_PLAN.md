# Memory Features Implementation Plan

> Pattern Detection, Memory Transparency, and Timing Flexibility

**Created:** 2026-01-22
**Status:** Complete
**Design Doc:** [PATTERN_DETECTION_AND_MEMORY_TRANSPARENCY.md](../design/PATTERN_DETECTION_AND_MEMORY_TRANSPARENCY.md)

## Implementation Summary

All four phases have been implemented:

### Files Created
- `api/api/src/app/services/patterns.py` - Pattern detection service
- `api/api/src/app/jobs/patterns.py` - Daily pattern computation job
- `api/api/src/app/routes/memory.py` - Extended with summary/full endpoints
- `web/src/components/MemoryInsightCard.tsx` - Dashboard memory card
- `web/src/app/(dashboard)/memory/page.tsx` - Memory management page
- `web/src/app/(dashboard)/memory/layout.tsx` - Memory page layout
- `supabase/migrations/101_timing_flexibility.sql` - Timing columns

### Files Modified
- `api/api/src/app/services/threads.py` - Integrated pattern service
- `web/src/app/(dashboard)/dashboard/page.tsx` - Added MemoryInsightCard
- `web/src/app/(dashboard)/settings/page.tsx` - Added timing flexibility UI
- `web/src/lib/api/client.ts` - Added memory API + timing types

---

## Overview

Four features to implement in order:

| # | Feature | Effort | Dependencies |
|---|---------|--------|--------------|
| 1 | Pattern Detection Service | Medium | None |
| 2 | Memory Transparency - Dashboard | Small | Pattern Detection (optional) |
| 3 | Memory Management Page | Medium | Dashboard card |
| 4 | Timing Flexibility | Small | None |

---

## Phase 1: Pattern Detection Service

### Goal
Enable Priority 3 messages like "You've seemed a bit flat this week" by computing behavioral patterns from conversation history.

### Tasks

#### 1.1 Create PatternService
**File:** `api/api/src/app/services/patterns.py`

- [ ] Define pattern data classes:
  - `MoodTrendPattern` - rolling sentiment analysis
  - `EngagementTrendPattern` - message frequency, length, initiation
  - `TopicSentimentPattern` - topic → mood correlation
  - `TimePattern` - response timing patterns

- [ ] Implement computation methods:
  - `compute_mood_trend(user_id, window_days)` - compare recent mood to baseline
  - `compute_engagement_trend(user_id)` - track engagement changes
  - `compute_topic_sentiment(user_id, topic)` - correlate topics with mood
  - `compute_all_patterns(user_id)` - run all computations

- [ ] Implement storage methods:
  - `save_pattern(user_id, pattern)` - store in user_context with category='pattern'
  - `get_patterns(user_id)` - retrieve all patterns
  - `get_actionable_patterns(user_id)` - patterns worth mentioning (notable deviation, not recently used)
  - `mark_pattern_used(pattern_id)` - track when pattern was referenced

#### 1.2 Add Mood Mapping
**File:** `api/api/src/app/services/patterns.py`

- [ ] Create mood → valence mapping:
  ```python
  MOOD_VALENCE = {
      "happy": 2, "excited": 2, "grateful": 2,
      "hopeful": 1, "calm": 1, "content": 1,
      "neutral": 0, "tired": 0,
      "anxious": -1, "stressed": -1, "frustrated": -1,
      "sad": -2, "angry": -2, "hopeless": -2,
  }
  ```

- [ ] Handle unknown moods gracefully (default to 0)

#### 1.3 Integrate with ThreadService
**File:** `api/api/src/app/services/threads.py`

- [ ] Update `get_message_context()`:
  - Import PatternService
  - Call `get_actionable_patterns()` for Priority 3
  - Include patterns in MessageContext

- [ ] Update MessageContext dataclass if needed

#### 1.4 Add Pattern Computation Job
**File:** `api/api/src/app/jobs/patterns.py` (new)

- [ ] Create daily pattern computation job:
  ```python
  async def compute_patterns_for_active_users():
      # Get users with recent conversations
      # Compute patterns for each
      # Log metrics (patterns computed, users processed)
  ```

- [ ] Add to cron schedule (run after daily messages, e.g., 2am UTC)

#### 1.5 Update Daily Message Prompt
**File:** `api/api/src/app/services/companion.py` (or equivalent)

- [ ] Add pattern context to prompt when Priority 3:
  ```
  PATTERN OBSERVATION:
  {pattern.description}

  Consider acknowledging this pattern naturally, like:
  - "You've seemed [observation] lately..."
  - "I've noticed [pattern]..."
  ```

### Verification
- [ ] Unit tests for pattern computation
- [ ] Integration test: conversation → pattern extraction → message generation
- [ ] Manual test: create user with varied mood history, verify pattern detection

---

## Phase 2: Memory Transparency - Dashboard

### Goal
Show users what Daisy is "paying attention to" on the dashboard—threads and follow-ups.

### Tasks

#### 2.1 Create Memory Summary API Endpoint
**File:** `api/api/src/app/routes/memory.py` (new)

- [ ] Create router with prefix `/memory`

- [ ] `GET /memory/summary` endpoint:
  ```python
  @router.get("/summary")
  async def get_memory_summary(user: User = Depends(get_current_user)):
      # Get active threads (limit 5)
      # Get pending follow-ups (limit 3)
      # Return structured response
      return {
          "active_threads": [...],
          "pending_follow_ups": [...],
          "thread_count": int,
          "fact_count": int
      }
  ```

- [ ] Register router in main app

#### 2.2 Add API Client Method
**File:** `web/src/lib/api/client.ts`

- [ ] Add memory namespace:
  ```typescript
  memory: {
    getSummary: () => Promise<MemorySummary>,
  }
  ```

- [ ] Define TypeScript types:
  ```typescript
  interface MemorySummary {
    active_threads: Thread[];
    pending_follow_ups: FollowUp[];
    thread_count: number;
    fact_count: number;
  }
  ```

#### 2.3 Create MemoryInsightCard Component
**File:** `web/src/components/MemoryInsightCard.tsx` (new)

- [ ] Component structure:
  ```tsx
  export function MemoryInsightCard({ companionName }: Props) {
    // Fetch memory summary
    // Show loading skeleton
    // Render threads and follow-ups
    // Link to /memory for full management
  }
  ```

- [ ] Empty state: "No active threads yet. As we chat, I'll keep track of what's going on in your life."

- [ ] Design:
  - Card with title "What {companionName} is paying attention to"
  - Bulleted list of threads (max 3)
  - Bulleted list of follow-ups (max 2)
  - "See all →" link to /memory

#### 2.4 Add to Dashboard
**File:** `web/src/app/(dashboard)/dashboard/page.tsx`

- [ ] Import MemoryInsightCard
- [ ] Add after CompanionCard, before CheckInTimeCard
- [ ] Pass companionName prop

### Verification
- [ ] API returns correct data for user with threads
- [ ] API returns empty arrays for new user
- [ ] Dashboard card renders correctly
- [ ] Empty state displays appropriately

---

## Phase 3: Memory Management Page

### Goal
Full page for viewing and managing what Daisy remembers.

### Tasks

#### 3.1 Extend Memory API
**File:** `api/api/src/app/routes/memory.py`

- [ ] `GET /memory` - Full memory retrieval:
  ```python
  @router.get("/")
  async def get_full_memory(user: User = Depends(get_current_user)):
      return {
          "threads": [...],          # All threads with full details
          "follow_ups": [...],       # All follow-ups
          "facts": {
              "personal": [...],
              "relationships": [...],
              "preferences": [...],
              "goals": [...],
          },
          "patterns": [...]          # Computed patterns
      }
  ```

- [ ] `DELETE /memory/{context_id}` - Delete memory item
- [ ] `PATCH /memory/{context_id}` - Update memory item
- [ ] `POST /memory/threads/{thread_id}/resolve` - Mark thread resolved

#### 3.2 Add API Client Methods
**File:** `web/src/lib/api/client.ts`

- [ ] Extend memory namespace:
  ```typescript
  memory: {
    getSummary: () => Promise<MemorySummary>,
    getFull: () => Promise<FullMemory>,
    deleteItem: (id: string) => Promise<void>,
    updateItem: (id: string, data: Partial<MemoryItem>) => Promise<MemoryItem>,
    resolveThread: (threadId: string) => Promise<void>,
  }
  ```

#### 3.3 Create Memory Page
**File:** `web/src/app/(dashboard)/memory/page.tsx` (new)

- [ ] Page structure:
  ```
  - Header: "What {companionName} Remembers"
  - Section: Active Threads (expandable cards with edit/resolve/delete)
  - Section: Things I Know About You (grouped by category)
  - Section: Patterns I've Noticed (read-only observations)
  ```

- [ ] Create sub-components:
  - `ThreadCard.tsx` - Editable thread display
  - `FactGroup.tsx` - Category-grouped facts
  - `PatternList.tsx` - Read-only pattern list

#### 3.4 Create Memory Layout
**File:** `web/src/app/(dashboard)/memory/layout.tsx` (new)

- [ ] Basic layout with metadata:
  ```tsx
  export const metadata = { title: "Memory" };
  export default function MemoryLayout({ children }) {
    return children;
  }
  ```

#### 3.5 Add Delete Confirmation Dialog
**File:** `web/src/components/memory/DeleteConfirmDialog.tsx` (new)

- [ ] Confirm before deleting memory items
- [ ] "Are you sure? This can't be undone."

### Verification
- [ ] Full memory page loads correctly
- [ ] Can expand/collapse thread details
- [ ] Can resolve thread (moves to resolved state)
- [ ] Can delete memory items
- [ ] Patterns display correctly (no edit capability)

---

## Phase 4: Timing Flexibility

### Goal
Let users choose exact time, approximate time, or time window for daily messages.

### Tasks

#### 4.1 Database Migration
**File:** `supabase/migrations/XXX_timing_flexibility.sql` (new)

- [ ] Add columns:
  ```sql
  ALTER TABLE users ADD COLUMN IF NOT EXISTS message_time_flexibility TEXT
      DEFAULT 'exact'
      CHECK (message_time_flexibility IN ('exact', 'around', 'window'));

  ALTER TABLE users ADD COLUMN IF NOT EXISTS message_time_window TEXT
      CHECK (message_time_window IN ('morning', 'midday', 'evening', 'night'));
  ```

#### 4.2 Update User Model
**File:** `api/api/src/app/models/user.py`

- [ ] Add fields to user model/schema
- [ ] Add to API response types

#### 4.3 Update Scheduler Logic
**File:** `api/api/src/app/services/scheduler.py`

- [ ] Update `get_users_for_scheduled_message()`:
  ```python
  # Handle three modes:
  # 1. exact: current behavior (2-min window)
  # 2. around: ±15 min of preferred time
  # 3. window: within time block, random trigger
  ```

- [ ] Add window bounds helper:
  ```python
  WINDOW_BOUNDS = {
      "morning": ("06:00", "10:00"),
      "midday": ("11:00", "14:00"),
      "evening": ("17:00", "20:00"),
      "night": ("20:00", "23:00"),
  }
  ```

#### 4.4 Update Onboarding Flow
**File:** `api/api/src/app/services/onboarding.py`

- [ ] Modify WAKE_TIME step or add new step:
  ```
  "When would you like to hear from me?"
  Options:
  - "At a specific time" → ask for time, set flexibility='exact'
  - "Sometime in the morning" → set flexibility='window', window='morning'
  - "Sometime in the evening" → set flexibility='window', window='evening'
  ```

#### 4.5 Update Settings UI
**File:** `web/src/app/(dashboard)/settings/page.tsx`

- [ ] Add timing flexibility section:
  ```
  Message Timing
  ─────────────────────────────────
  ○ At a specific time: [9:00 AM ▼]
  ○ Sometime in the morning (6am - 10am)
  ○ Sometime around midday (11am - 2pm)
  ○ Sometime in the evening (5pm - 8pm)
  ○ Sometime at night (8pm - 11pm)
  ```

- [ ] Radio button group with time picker for "specific time" option

#### 4.6 Update API Client Types
**File:** `web/src/lib/api/client.ts`

- [ ] Add new fields to User type
- [ ] Update user update payload type

### Verification
- [ ] Migration runs without errors
- [ ] Onboarding captures timing preference correctly
- [ ] Settings UI shows current preference
- [ ] Settings UI saves changes correctly
- [ ] Scheduler respects each flexibility mode

---

## File Summary

### New Files
```
api/api/src/app/services/patterns.py       # Pattern computation service
api/api/src/app/jobs/patterns.py           # Daily pattern job
api/api/src/app/routes/memory.py           # Memory API endpoints

web/src/components/MemoryInsightCard.tsx   # Dashboard memory card
web/src/app/(dashboard)/memory/page.tsx    # Memory management page
web/src/app/(dashboard)/memory/layout.tsx  # Memory page layout
web/src/components/memory/ThreadCard.tsx   # Thread display component
web/src/components/memory/FactGroup.tsx    # Fact category component
web/src/components/memory/PatternList.tsx  # Pattern display component
web/src/components/memory/DeleteConfirmDialog.tsx

supabase/migrations/XXX_timing_flexibility.sql
```

### Modified Files
```
api/api/src/app/services/threads.py        # Integrate patterns into message context
api/api/src/app/services/scheduler.py      # Timing flexibility logic
api/api/src/app/services/onboarding.py     # Timing question update
api/api/src/app/main.py                    # Register memory router

web/src/app/(dashboard)/dashboard/page.tsx # Add MemoryInsightCard
web/src/app/(dashboard)/settings/page.tsx  # Timing flexibility UI
web/src/lib/api/client.ts                  # Memory API methods + types
```

---

## Progress Tracking

### Phase 1: Pattern Detection
- [ ] 1.1 Create PatternService
- [ ] 1.2 Add mood mapping
- [ ] 1.3 Integrate with ThreadService
- [ ] 1.4 Add pattern computation job
- [ ] 1.5 Update daily message prompt
- [ ] Verification complete

### Phase 2: Memory Dashboard Card
- [ ] 2.1 Create memory summary API
- [ ] 2.2 Add API client method
- [ ] 2.3 Create MemoryInsightCard
- [ ] 2.4 Add to dashboard
- [ ] Verification complete

### Phase 3: Memory Management Page
- [ ] 3.1 Extend memory API
- [ ] 3.2 Add API client methods
- [ ] 3.3 Create memory page
- [ ] 3.4 Create memory layout
- [ ] 3.5 Add delete confirmation
- [ ] Verification complete

### Phase 4: Timing Flexibility
- [ ] 4.1 Database migration
- [ ] 4.2 Update user model
- [ ] 4.3 Update scheduler logic
- [ ] 4.4 Update onboarding flow
- [ ] 4.5 Update settings UI
- [ ] 4.6 Update API client types
- [ ] Verification complete

---

## Notes

- Pattern detection can be deployed independently—dashboard card works without patterns initially
- Memory page can launch with threads/facts only, add patterns display later
- Timing flexibility is independent of other features
- All features are additive—no breaking changes to existing functionality
