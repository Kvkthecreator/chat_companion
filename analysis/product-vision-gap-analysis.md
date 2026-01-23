# Product Vision Gap Analysis

> **Status**: Audit Complete - Key Gap Identified
> **Date**: January 2026
> **Purpose**: Reverse-engineer from first principles to create comprehensive architecture

---

## 🚨 Executive Summary: The Gap

**The backend is 80% complete. The critical missing piece is one function call.**

| Component | Status | Notes |
|-----------|--------|-------|
| Context Extraction | ✅ Working | Runs after every conversation |
| Thread Service | ✅ Built | Full priority stack implementation |
| Pattern Detection | ✅ Built | Cron job runs daily |
| Scheduler Priority | ✅ Working | Uses `get_message_context()` |
| **Thread Detection** | ❌ **NOT WIRED** | `extract_from_conversation()` exists but never called |

### The Single Fix Needed

In [conversation.py](api/api/src/app/services/conversation.py), after context extraction, we need to add:

```python
# Extract threads in background
from app.services.threads import ThreadService
thread_service = ThreadService(db)
await thread_service.extract_from_conversation(user_id, conversation_id, recent_messages)
```

This would enable:
- Automatic thread creation from conversations
- Priority 1 (FOLLOW_UP) messages
- Priority 2 (THREAD) messages

Without this, the system falls back to Priority 4-5 (TEXTURE/GENERIC) most of the time.

---

## The Core Truth

From MEMORY_SYSTEM.md:

> "A friend who texts you 'it's going to rain today' isn't solving your loneliness because they gave you weather information. They're solving it because **they thought of you**. The weather is just the excuse to reach out."

This is the **axiomatic truth** the entire product must be built on.

---

## First Principles Decomposition

### What does "someone thought of you" require?

For a message to feel like someone **thought of you**, it must:

1. **Reference something specific to YOU** (not generic)
2. **Be timely** (relevant to what's happening in your life now)
3. **Show continuity** (remember what was said before)
4. **Demonstrate care** (follow up on things that matter)

### What does the system need to deliver this?

```
USER SHARES SOMETHING
        ↓
SYSTEM EXTRACTS & STORES (Memory)
        ↓
SYSTEM TRACKS ONGOING SITUATIONS (Threads)
        ↓
SYSTEM DETECTS PATTERNS (Analysis)
        ↓
SYSTEM GENERATES RELEVANT OUTREACH (Scheduler)
        ↓
USER FEELS KNOWN
```

Each step is **load-bearing**. If any fails, the experience collapses to "generic chatbot."

---

## The Priority Stack (From Vision)

| Priority | Type | Example | Feeling Created |
|----------|------|---------|-----------------|
| 1 | FOLLOW_UP | "How did the interview go?" | "They remembered" |
| 2 | THREAD | "How's the job search feeling this week?" | "They're tracking my life" |
| 3 | PATTERN | "You've seemed flat this week. Everything okay?" | "They notice me" |
| 4 | TEXTURE | "Rain in Tokyo today. How are you?" | "They thought of me" |
| 5 | GENERIC | "Hey, how's your day going?" | **FAILURE** - feels like spam |

**Critical insight**: Priority 5 should be rare. If it's common, the system is broken.

---

## Current State Assessment

### What's Built (Infrastructure)

| Component | Status | Notes |
|-----------|--------|-------|
| User authentication | ✅ Complete | Supabase Auth |
| Basic chat interface | ✅ Complete | Web + Mobile |
| Message storage | ✅ Complete | conversations, companion_messages |
| User preferences | ✅ Complete | timezone, message_time, support_style |
| Scheduler infrastructure | ✅ Complete | Cron job, push notifications |
| Memory tables | ✅ Complete | user_context, life_threads |
| Memory UI (basic) | ✅ Complete | Shows "Things I Know About You" |

### What's Fully Built (Verified)

| Component | Status | Evidence |
|-----------|--------|----------|
| Context extraction | ✅ **Working** | `conversation.py:72-81` - runs after every message |
| Thread service | ✅ **Complete** | Full priority stack, follow-ups, status tracking |
| Pattern detection | ✅ **Complete** | `jobs/patterns.py` cron job runs daily |
| Priority-based scheduler | ✅ **Complete** | `scheduler.py:247-255` uses `get_message_context()` |
| Memory API | ✅ **Complete** | Full CRUD, thread resolve, pattern display |

### What's NOT Wired (The Gap)

| Component | Status | Impact |
|-----------|--------|--------|
| **Thread extraction** | ❌ **NOT WIRED** | `extract_from_conversation()` never called → No Priority 1-2 messages |

### What's Missing (Frontend/UX)

| Component | Status | Impact |
|-----------|--------|--------|
| Memory editing UI | ⚠️ API exists, UI minimal | Users can't easily correct mistakes |
| Thread visualization | ⚠️ API exists, UI empty | "Active Threads" shows empty |
| Pattern visualization | ⚠️ API exists, UI minimal | Patterns not surfaced well |
| "Why did you say that?" | ❌ Not built | No transparency on message generation |

---

## The Real Questions (ANSWERED)

> **Audit Date**: January 2026
> **Status**: Backend services are MORE complete than expected. Key gap identified.

### 1. Is context being extracted from conversations?

When a user says "I have a job interview tomorrow", does the system:
- [x] Detect this as important? ✅ **YES** - `ContextService.extract_context()` uses LLM
- [x] Store it in user_context or life_threads? ✅ **YES** - `save_context()` with upsert
- [ ] Create a follow-up trigger for tomorrow/day after? ⚠️ **PARTIAL** - Extraction happens, but thread-level follow-ups need verification

**Evidence**: [conversation.py:72-81](api/api/src/app/services/conversation.py#L72-L81) - Context extraction runs after every message:
```python
# Extract context in background (don't block response)
context_items, mood = await self.context_service.extract_context(...)
if context_items:
    await self.context_service.save_context(user_id, context_items)
```

### 2. Are threads being created and tracked?

When a user mentions ongoing situations (job search, relationship issue, project), does the system:
- [x] Detect this is an ongoing thread vs. one-off mention? ✅ **YES** - `ThreadService.extract_from_conversation()` exists
- [ ] Create a life_thread record? ❌ **NOT WIRED** - Method exists but never called!
- [x] Track status changes over time? ✅ **YES** - Full status tracking in ThreadService
- [x] Know when to follow up? ✅ **YES** - `follow_up_date` logic in ThreadService

**🚨 CRITICAL GAP**: `extract_from_conversation()` is defined in [threads.py:474](api/api/src/app/services/threads.py#L474) but **never invoked**. Thread detection exists but isn't running.

### 3. Is the scheduler using memory?

When generating daily messages, does the scheduler:
- [x] Query for follow-up opportunities (Priority 1)? ✅ **YES**
- [x] Query for active threads (Priority 2)? ✅ **YES**
- [x] Query for patterns (Priority 3)? ✅ **YES**
- [x] Fall back gracefully through priorities? ✅ **YES**
- [x] Track which priority was used (for monitoring)? ✅ **YES** - `priority_level` column in scheduled_messages

**Evidence**: [scheduler.py:247-255](api/api/src/app/services/scheduler.py#L247-L255):
```python
# Get priority-based message context from ThreadService
thread_service = ThreadService(db)
message_context = await thread_service.get_message_context(UUID(str(user_id)))

# Log priority level for metrics
log.info(f"Message priority for user {user_id}: {message_context.priority.name}")
```

### 4. Are patterns being detected?

Does the system:
- [x] Track mood over time? ✅ **YES** - `PatternService.compute_mood_trend()`
- [x] Notice engagement patterns (response length, frequency)? ✅ **YES** - `compute_engagement_trend()`
- [x] Detect concerning trends? ✅ **YES** - `get_actionable_patterns()`
- [x] Generate insights from patterns? ✅ **YES** - Cron job in `jobs/patterns.py`

**Evidence**: [jobs/patterns.py](api/api/src/app/jobs/patterns.py) - Daily cron job computes patterns for active users.

---

## Architecture Requirements (From First Principles)

### Layer 1: Memory Extraction

**Purpose**: Turn conversations into structured, queryable knowledge

```
Conversation Message
        ↓
    [Extraction Service]
        ↓
    ┌─────────────────────────────────────┐
    │  Core Facts    │  Threads  │  Events │
    │  (permanent)   │ (temporal)│ (dated) │
    └─────────────────────────────────────┘
```

**Requirements**:
- Real-time or near-real-time extraction
- Structured output (not free text)
- Confidence scoring
- Deduplication (don't store same fact twice)
- Validation before storage (optional human-in-loop)

### Layer 2: Thread Management

**Purpose**: Track ongoing life situations

```
Thread Lifecycle:

    DETECTED → ACTIVE → RESOLVED/STALE
        ↓         ↓          ↓
    (first    (ongoing    (concluded
    mention)  updates)    or expired)
```

**Requirements**:
- Thread detection from conversation
- Status tracking (waiting, in_progress, resolved)
- Follow-up timing (when to ask about it)
- Importance scoring (not all threads are equal)
- Expiration logic (stale threads fade)

### Layer 3: Pattern Analysis

**Purpose**: Notice trends the user might not see

**Requirements**:
- Mood tracking over time
- Engagement analysis
- Topic frequency analysis
- Time-of-day patterns
- Concerning trend detection

### Layer 4: Message Generation

**Purpose**: Create outreach that feels personal

```
Generate Message:

    1. Check for follow-ups due → Priority 1
    2. Check for active threads → Priority 2
    3. Check for patterns to mention → Priority 3
    4. Add contextual texture → Priority 4
    5. Generic fallback → Priority 5 (FAILURE)
```

**Requirements**:
- Strict priority ordering
- Context injection into prompts
- Variety (don't repeat same follow-up style)
- Tone matching (support_style)
- Priority tracking (monitor failure rate)

### Layer 5: User Transparency

**Purpose**: Build trust through visibility

**Requirements**:
- View all stored memories
- View active threads
- Edit/delete memories
- See what companion "knows"
- Understand why a message was sent

---

## Frontend Architecture (Needed)

### Current State

```
┌─────────────────────────────────────┐
│            Companion Page           │
│  ┌─────────┐  ┌─────────────────┐  │
│  │ Memory  │  │  Personality    │  │
│  │  Tab    │  │     Tab         │  │
│  └─────────┘  └─────────────────┘  │
│                                     │
│  - Active Threads (empty)           │
│  - Things I Know (basic list)       │
└─────────────────────────────────────┘
```

### Required State

```
┌─────────────────────────────────────────────────────────┐
│                    Companion Page                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Memory  │  │  Threads │  │ Patterns │  │Settings │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘

MEMORY TAB:
┌─────────────────────────────────────┐
│ Things I Know About You             │
│ ┌─────────────────────────────────┐ │
│ │ 📍 Lives in Tokyo               │←─ Edit/Delete
│ │ 💼 Works as software engineer   │
│ │ 🗣️ Speaks Korean and English    │
│ │ 👨‍👩‍👧 Mom visiting next week       │←─ Has expiry
│ └─────────────────────────────────┘ │
│                                     │
│ [+ Add something I should know]     │
└─────────────────────────────────────┘

THREADS TAB:
┌─────────────────────────────────────┐
│ What I'm Tracking                   │
│ ┌─────────────────────────────────┐ │
│ │ 🔄 Job Search                   │ │
│ │    Status: Interviewing         │ │
│ │    Last mentioned: 2 days ago   │ │
│ │    [Mark Resolved]              │ │
│ ├─────────────────────────────────┤ │
│ │ 🔄 Project deadline             │ │
│ │    Due: Friday                  │ │
│ │    [Mark Complete]              │ │
│ └─────────────────────────────────┘ │
│                                     │
│ No resolved threads yet.            │
└─────────────────────────────────────┘

PATTERNS TAB:
┌─────────────────────────────────────┐
│ What I've Noticed                   │
│ ┌─────────────────────────────────┐ │
│ │ 📊 Mood This Week               │ │
│ │    [visual: mostly positive]    │ │
│ │                                 │ │
│ │ 💬 You tend to chat more in     │ │
│ │    the evenings                 │ │
│ │                                 │ │
│ │ 📈 Energy seems higher on       │ │
│ │    weekends                     │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## Backend Services (Needed)

### Current Services

```
api/src/app/services/
├── companion.py      # Prompt building
├── conversation.py   # Message handling
├── llm.py           # LLM abstraction
├── push.py          # Push notifications
├── scheduler.py     # Daily messages
├── telegram.py      # Telegram bot
└── threads.py       # Thread service (exists!)
```

### Required Services

```
api/src/app/services/
├── companion.py      # ✅ Exists
├── conversation.py   # ✅ Exists
├── llm.py           # ✅ Exists
├── push.py          # ✅ Exists
├── scheduler.py     # ⚠️ Needs priority integration
├── threads.py       # ⚠️ Needs verification
├── extraction.py    # ❓ Does this exist? Core need.
├── patterns.py      # ❌ Needed for Priority 3
└── memory.py        # ❌ Needed for memory CRUD
```

---

## API Endpoints (Needed)

### Current (Assumed)

```
GET  /users/me
GET  /conversations
POST /conversations/{id}/messages
GET  /context                    # Memory items?
```

### Required

```
# Memory Management
GET    /memory                   # All user memories
POST   /memory                   # Add memory manually
PATCH  /memory/{id}              # Edit memory
DELETE /memory/{id}              # Delete memory

# Thread Management
GET    /threads                  # All threads
GET    /threads/active           # Active threads only
PATCH  /threads/{id}             # Update thread status
POST   /threads/{id}/resolve     # Mark resolved

# Patterns
GET    /patterns                 # All detected patterns
GET    /patterns/mood            # Mood over time
GET    /patterns/engagement      # Engagement metrics

# Transparency
GET    /companion/context        # What companion knows for next message
GET    /companion/last-message-reason  # Why the last message was sent
```

---

## Database Schema (Verification Needed)

### Expected Tables

```sql
-- Core facts about user (permanent)
user_context (
    id, user_id, category, key, value,
    importance_score, expires_at, created_at
)

-- Ongoing life situations (temporal)
life_threads (
    id, user_id, title, description, status,
    importance_score, last_mentioned_at,
    follow_up_after, created_at, resolved_at
)

-- Detected patterns (computed)
user_patterns (
    id, user_id, pattern_type, description,
    confidence, detected_at, expires_at
)

-- Events with dates
user_events (
    id, user_id, title, event_date,
    reminder_before, created_at
)
```

---

## Implementation Roadmap (Revised After Audit)

### Phase 0: Audit ✅ COMPLETE
- [x] Verify extraction service exists and runs → **YES, working**
- [x] Verify thread detection works → **EXISTS but NOT WIRED**
- [x] Check scheduler priority integration → **YES, fully working**
- [x] Identify actual gaps vs. perceived gaps → **Gap identified: thread extraction not called**

### Phase 1: Wire Thread Extraction (CRITICAL - Single Fix)
- [ ] Add `ThreadService.extract_from_conversation()` call in `conversation.py`
- [ ] Test that threads are created from conversation
- [ ] Verify follow-ups are generated with correct dates
- [ ] Monitor Priority 1-2 message rate (should increase from 0%)

**Estimated impact**: This single change enables the entire Priority 1-2 message stack.

### Phase 2: Frontend Enhancement (API Already Exists)
- [ ] Populate "Active Threads" section in Memory UI
- [ ] Add thread resolve/dismiss actions
- [ ] Show follow-up questions pending
- [ ] Improve memory editing UX

### Phase 3: Pattern Visibility (Backend Complete)
- [ ] Surface patterns in Memory UI
- [ ] Add mood trend visualization
- [ ] Show engagement insights
- [ ] Connect patterns to Priority 3 messages

### Phase 4: User Transparency (New)
- [ ] "Why did you say that?" feature
- [ ] Show what companion knows before message
- [ ] Message priority indicator (debug mode)
- [ ] Full companion context view

---

## Success Criteria

### Quantitative
- **<20% of messages are Priority 5 (generic)**
- **>50% of messages reference specific user context**
- **Active threads exist for users with >5 conversations**
- **Follow-ups happen within 48 hours of relevant events**

### Qualitative
- User says "how did you know to ask about that?"
- User shares unprompted personal information
- User corrects a memory (means they care about accuracy)
- User initiates conversation (relationship feels real)

---

## Next Steps

1. **Audit current extraction/thread services** - What actually exists?
2. **Test with real conversation** - Does memory get created?
3. **Check scheduler logs** - What priority are messages using?
4. **Identify smallest fix** - What's the minimum to move from Priority 5 to Priority 1-4?

---

## Open Questions (ANSWERED)

1. **Is there an extraction service that runs on new messages?**
   → ✅ YES. `ContextService.extract_context()` called in `conversation.py:72-81`

2. **How does `threads.py` get invoked?**
   → ✅ Scheduler calls `ThreadService.get_message_context()` in `scheduler.py:248-249`
   → ❌ BUT `extract_from_conversation()` is never called (the gap)

3. **What triggers thread creation?**
   → ❌ NOTHING currently. The method exists but isn't wired.

4. **Is pattern detection implemented anywhere?**
   → ✅ YES. `jobs/patterns.py` runs as a daily cron job

5. **What's the actual flow from conversation → memory → daily message?**
   → Current flow:
   ```
   Conversation → extract_context() → user_context table
                                            ↓
   Scheduler → get_message_context() → reads user_context
                                            ↓
                                   BUT no threads exist
                                            ↓
                                   Falls to Priority 4-5
   ```
   → Fixed flow (after wiring thread extraction):
   ```
   Conversation → extract_context() → user_context table
              → extract_from_conversation() → life_threads + follow_ups
                                                      ↓
   Scheduler → get_message_context() → finds threads/follow-ups
                                                      ↓
                                          Returns Priority 1-2
   ```
