# Memory & Messaging System - Implementation Status

> Tracking the journey from "scheduled notifications" to "companion that knows you"

**Last Updated:** 2026-01-23
**Previous Session Context:** Fixed memory extraction bugs (thread args, JSON parsing)

---

## The Vision (Why This Matters)

**Memory is the product.** Not content delivery. Not notifications.

A friend who texts "it's going to rain today" isn't solving loneliness with weather info—they're solving it because **they thought of you**. The weather is just an excuse.

The goal is a companion that:
1. **Remembers** what you shared yesterday, last week, two weeks ago
2. **Tracks threads** in your life (job search, relationship, project)
3. **Notices patterns** (you seem down on Mondays)
4. **Follows up unprompted** ("How did the interview go?")
5. **Reaches out when you've been quiet** (without guilt-tripping)

---

## Current State (What's Working)

### Memory Extraction ✅ FIXED (Jan 23, 2026)

| Component | Status | Notes |
|-----------|--------|-------|
| Context extraction from conversations | ✅ Working | Extracts facts, preferences, goals, relationships |
| Thread detection and tracking | ✅ Working | Tracks ongoing situations with follow-up dates |
| Follow-up question generation | ✅ Working | Creates questions from threads |
| Storage in `user_context` | ✅ Working | Upsert pattern, tiered memory |

**Recent Fixes:**
- Fixed `ThreadService.extract_from_conversation()` wrong argument count
- Fixed JSON parsing truncation (increased `max_tokens` to 2048)
- Added retry logic with error feedback for malformed LLM responses
- Added better logging for debugging

**Test Results:** Before fixes: 1 thread, 6 facts → After: 6 threads, 17 facts

### Companion Outreach System ✅ Phase 1-2 Complete

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Daily Scheduler | ✅ Complete | Time-based daily check-ins with priority stack |
| Phase 2: Silence Detection | ✅ Complete | Reaches out when user goes quiet (configurable) |
| Phase 3: Event-Based Follow-ups | ⏳ Planned | Follow up on specific threads/dates |
| Phase 4: Earned Spontaneity | ⏳ Future | Timing jitter, pattern-based outreach |

### Memory UI ✅ Complete

| Feature | Status | Location |
|---------|--------|----------|
| Memory Insight Card | ✅ Complete | Dashboard - shows threads & follow-ups |
| Memory Management Page | ✅ Complete | `/companion` (Memory tab) |
| Edit/Delete memory items | ✅ Complete | `/companion` Memory tab |
| Resolve threads | ✅ Complete | `/companion` Memory tab |
| Silence check-in settings | ✅ Complete | `/companion` Personality tab |

---

## What's NOT Working / Needs Attention

### 1. Memory Versioning / Evolution
**Problem:** When a fact changes (e.g., "works at Google" → "works at Meta"), we just overwrite. No history.

**Current behavior:**
```sql
ON CONFLICT (user_id, category, key) DO UPDATE SET value = EXCLUDED.value
```

**Desired behavior:** Maintain version history for important facts so companion can say "You mentioned you used to work at Google—how's the new job at Meta going?"

**Questions to resolve:**
- Which categories need versioning? (probably `fact`, `situation`, not `emotion`)
- How long to keep old versions?
- How does companion reference old vs new?

### 2. Manual Memory Updates
**Problem:** User can't easily add/edit facts from the UI. They can delete, but adding is missing.

**Current state:** Memory is only populated via extraction from conversations.

**Desired:** User should be able to manually add facts like:
- "My dog's name is Max"
- "I'm allergic to peanuts"
- "My anniversary is June 15th"

**Implementation needed:**
- Add "Add Memory" button to Memory tab
- Create API endpoint `POST /memory/context`
- Form with category dropdown + key + value fields

### 3. Thread-to-Fact Promotion
**Problem:** Active threads that resolve don't become permanent facts.

**Example:** Thread "job_interview" with details about interviewing at Google should, when resolved with "got the job", create a permanent fact "works at Google".

**Current state:** Threads just get marked `resolved` and eventually expire.

**Desired:** When marking thread resolved, optionally promote key details to core facts.

### 4. Reference Tracking
**Problem:** We don't track when memory items are actually used in conversation.

**The `last_referenced_at` column exists but isn't being updated.**

**Why it matters:**
- Can decay importance of unused memories
- Can surface "did you know I remember X?" moments
- Helps with deduplication ("we already talked about this")

**Implementation needed:**
- After generating response, extract which context items were referenced
- Update `last_referenced_at` for those items

### 5. Priority 5 (Generic) Message Tracking
**Problem:** We're not tracking when the system falls back to generic messages.

**Why it matters:** Priority 5 messages ("Hey, how are you?") are a **failure state**. If this happens often, memory extraction isn't working.

**Current state:** `scheduled_messages.priority_level` exists but may not be reliably tracked.

**Needed:**
- Dashboard metric: "% of messages that were Priority 5 this week"
- Alert if > 40% are generic

---

## Implementation Priorities (Next Steps)

### Immediate (Before Next Session)

1. **Verify memory extraction in production**
   - Send a few test messages
   - Check that threads and facts are being created
   - Review logs for any remaining JSON parsing issues

### Short-term (This Week)

2. **Add manual memory creation**
   - UI: "Add Memory" button on Memory tab
   - API: `POST /memory/context` endpoint
   - Allow user to add personal facts directly

3. **Track generic message rate**
   - Ensure `priority_level` is saved on all scheduled messages
   - Add simple query to check Priority 5 rate

### Medium-term (Next 2 Weeks)

4. **Reference tracking**
   - Update `last_referenced_at` when memory is used
   - Decay importance over time for unused items

5. **Thread resolution → fact promotion**
   - When resolving thread, prompt: "Should I remember anything from this?"
   - Create core facts from key_details

### Future (Backlog)

6. **Memory versioning**
   - Design schema for version history
   - Implement for key categories

7. **Phase 3: Event-Based Follow-ups**
   - Trigger on `thread.follow_up_date = TODAY`
   - Same-day follow-up messages for specific events

8. **Phase 4: Earned Spontaneity**
   - Gate behind user maturity (30+ days, 30+ messages)
   - Timing jitter (±15-30 min)
   - "Thinking of you" messages without questions

---

## Key Files Reference

### Backend (Memory)
- `api/api/src/app/services/context.py` - Context extraction
- `api/api/src/app/services/threads.py` - Thread tracking
- `api/api/src/app/services/llm.py` - LLM service with JSON extraction
- `api/api/src/app/routes/memory.py` - Memory API endpoints

### Backend (Messaging)
- `api/api/src/app/services/scheduler.py` - Daily scheduler + silence detection
- `api/api/src/app/services/conversation.py` - Conversation handling
- `api/api/src/app/jobs/scheduler.py` - Scheduler cron job
- `api/api/src/app/jobs/silence_detection.py` - Silence detection cron job

### Frontend
- `web/src/app/(dashboard)/companion/page.tsx` - Companion page (Memory + Personality tabs)
- `web/src/components/MemoryInsightCard.tsx` - Dashboard memory card
- `web/src/lib/api/client.ts` - API client with memory methods

### Cron Jobs (Render)
- `message-scheduler` - Every minute, sends daily check-ins
- `silence-detection` - Every 6 hours, checks for quiet users
- `pattern-computation` - Daily at 2am UTC, computes behavioral patterns

---

## Design Docs Reference

- [MEMORY_SYSTEM.md](../features/MEMORY_SYSTEM.md) - Core memory philosophy and architecture
- [COMPANION_OUTREACH_SYSTEM.md](../design/COMPANION_OUTREACH_SYSTEM.md) - Outreach trigger architecture
- [PATTERN_DETECTION_AND_MEMORY_TRANSPARENCY.md](../design/PATTERN_DETECTION_AND_MEMORY_TRANSPARENCY.md) - Pattern detection design

---

## Session Notes

### 2026-01-23 Session
**Focus:** Memory extraction debugging

**Discovered bugs:**
1. `ThreadService.extract_from_conversation()` was called with wrong args (3 instead of 2)
2. JSON extraction was truncating due to low `max_tokens` (1024)

**Fixes applied:**
- Removed erroneous `conversation_id` argument from thread extraction calls
- Increased `max_tokens` to 2048 for JSON extraction
- Added retry logic with error feedback for malformed JSON
- Added `_try_fix_json()` helper for common formatting issues
- Added better logging of raw content on parse failures

**Commits:**
- `55193707` - Fix memory extraction bugs: thread args and JSON parsing
- `b792fad3` - Increase max_tokens for JSON extraction to prevent truncation

**Test results:**
- Before: 1 thread, 6 facts
- After: 6 threads, 17 facts (dentist_visit, sarah_visit, marathon_training, guitar_learning, pottery_interest, product_launch)

**Discussion topics raised but deferred:**
- Manual updates to memory from UI
- Memory versioning (tracking changes over time)
- Thread-to-fact promotion when resolving
