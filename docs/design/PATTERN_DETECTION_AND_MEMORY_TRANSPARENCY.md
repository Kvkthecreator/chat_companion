# Pattern Detection & Memory Transparency Design

> Extending the memory system to detect patterns and surface memory as a feature

---

## Part 1: Pattern Detection

### Goal

Enable Priority 3 messages like:
- "You've seemed a bit flat this week. Everything okay?"
- "You've been crushing it lately—what's fueling that?"
- "I noticed you light up when you talk about your side project."

### Architecture: Patterns as Memory Tier

Patterns aren't separate from memory—they're **derived insights** stored in the same `user_context` table but with a new category.

```
┌─────────────────────────────────────────────────────────┐
│  Existing Memory Tiers                                  │
├─────────────────────────────────────────────────────────┤
│  Tier 1: Working Memory (in-memory during conversation) │
│  Tier 2: Active Memory (threads, expires_at set)        │
│  Tier 3: Core Memory (facts, no expiration)             │
├─────────────────────────────────────────────────────────┤
│  NEW: Derived Memory (patterns, computed periodically)  │
│  - Category: 'pattern'                                  │
│  - Tier: 'derived'                                      │
│  - Recomputed on schedule (not per-conversation)        │
└─────────────────────────────────────────────────────────┘
```

### Data Sources for Pattern Detection

| Source | What We Capture | Location |
|--------|----------------|----------|
| Conversation mood | `mood_summary` from context extraction | `conversations.mood_summary` |
| Emotional valence | Per-item valence (-2 to +2) | `user_context.emotional_valence` |
| Engagement signals | Message count, response length, initiation | `conversations`, `companion_messages` |
| Topic correlation | Which topics → positive/negative mood | Cross-reference topics + mood |
| Time patterns | When they respond, how quickly | `companion_messages.created_at` |

### New Tables/Columns

**Option A: Use existing `user_context` with new category**

```sql
-- No schema change needed, just new category values:
-- category = 'pattern'
-- tier = 'derived'
-- key = pattern type (e.g., 'mood_trend_7d', 'engagement_trend', 'topic_sentiment_work')
-- value = JSON with pattern data
-- expires_at = recomputation date (patterns are recalculated, not permanent)
```

**Option B: Dedicated pattern/insight storage** (if we want richer structure)

```sql
CREATE TABLE IF NOT EXISTS user_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Pattern identification
    pattern_type TEXT NOT NULL,  -- mood_trend, engagement_trend, topic_sentiment, time_pattern
    pattern_key TEXT NOT NULL,   -- 7d, 14d, work, side_project, weekday_response

    -- Pattern data
    value JSONB NOT NULL,        -- Type-specific data structure
    confidence FLOAT DEFAULT 0.5,

    -- Validity
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ,     -- When to recompute

    -- Usage
    last_used_at TIMESTAMPTZ,    -- When last used in a message
    times_used INT DEFAULT 0,

    UNIQUE(user_id, pattern_type, pattern_key)
);
```

**Recommendation:** Start with Option A (reuse `user_context`), migrate to Option B if patterns become complex.

### Pattern Types

#### 1. Mood Trend (Rolling Window)

```python
@dataclass
class MoodTrendPattern:
    pattern_type = "mood_trend"

    # Data structure
    window_days: int           # 7, 14, 30
    average_valence: float     # -2.0 to +2.0
    trend_direction: str       # "improving", "declining", "stable"
    notable_shift: bool        # Significant change from baseline?
    baseline_valence: float    # User's typical mood

    # Message generation hints
    message_templates: List[str]
    # e.g., ["You've seemed a bit down this week.", "Things seem to be looking up lately."]
```

**Computation:**
```python
async def compute_mood_trend(user_id: UUID, window_days: int = 7) -> MoodTrendPattern:
    # 1. Get conversations in window
    recent = await db.fetch_all("""
        SELECT mood_summary, started_at
        FROM conversations
        WHERE user_id = :user_id
          AND started_at > NOW() - INTERVAL ':window days'
        ORDER BY started_at DESC
    """, {"user_id": user_id, "window": window_days})

    # 2. Get baseline (30-day average excluding recent window)
    baseline = await db.fetch_one("""
        SELECT AVG(
            CASE mood_summary
                WHEN 'happy' THEN 2
                WHEN 'hopeful' THEN 1
                WHEN 'neutral' THEN 0
                WHEN 'anxious' THEN -1
                WHEN 'sad' THEN -2
                ELSE 0
            END
        ) as avg_valence
        FROM conversations
        WHERE user_id = :user_id
          AND started_at BETWEEN NOW() - INTERVAL '37 days' AND NOW() - INTERVAL '7 days'
    """, {"user_id": user_id})

    # 3. Compare recent to baseline
    # 4. Determine trend direction
    # 5. Return pattern with message hints
```

#### 2. Engagement Trend

```python
@dataclass
class EngagementTrendPattern:
    pattern_type = "engagement_trend"

    window_days: int
    avg_messages_per_conversation: float
    avg_response_length: float        # Characters
    user_initiation_rate: float       # % of conversations user started
    trend_direction: str              # "more_engaged", "less_engaged", "stable"
    baseline_engagement: float
```

**Signals of engagement:**
- User sends multiple messages (not just one-word replies)
- User initiates conversations
- Longer response length
- Asks questions back
- Shares unprompted personal information

#### 3. Topic Sentiment

```python
@dataclass
class TopicSentimentPattern:
    pattern_type = "topic_sentiment"

    topic: str                    # "work", "family", "side_project", "health"
    sentiment: str                # "positive", "negative", "mixed", "avoidant"
    evidence_count: int           # How many conversations inform this
    confidence: float

    # e.g., "User lights up talking about side_project but avoids work discussions"
```

**Computation:**
- Correlate `conversations.topics` with `conversations.mood_summary`
- Build topic → sentiment map
- Flag topics with strong positive/negative correlation

#### 4. Time Patterns

```python
@dataclass
class TimePattern:
    pattern_type = "time_pattern"

    pattern_key: str              # "response_speed", "active_days", "active_hours"
    value: Any

    # Examples:
    # response_speed: {"avg_minutes": 15, "quick_responder": True}
    # active_days: {"most_active": ["saturday", "sunday"], "least_active": ["monday"]}
    # active_hours: {"peak": "evening", "quiet": "morning"}
```

### Pattern Computation Schedule

Patterns should be computed **periodically**, not on every conversation:

```python
# In scheduler.py or dedicated job

async def compute_user_patterns(user_id: UUID):
    """Compute all patterns for a user. Run daily or when triggered."""

    patterns = []

    # Mood trend (7-day and 14-day windows)
    patterns.append(await compute_mood_trend(user_id, window_days=7))
    patterns.append(await compute_mood_trend(user_id, window_days=14))

    # Engagement trend
    patterns.append(await compute_engagement_trend(user_id))

    # Topic sentiment (for known topics)
    for topic in ["work", "family", "health", "relationships", "hobbies"]:
        if pattern := await compute_topic_sentiment(user_id, topic):
            patterns.append(pattern)

    # Time patterns
    patterns.append(await compute_time_patterns(user_id))

    # Save to user_context
    for pattern in patterns:
        await save_pattern(user_id, pattern)
```

**Trigger options:**
1. **Daily cron job** - Run after daily messages sent, compute patterns for active users
2. **Post-conversation** - Recompute after every N conversations (e.g., every 3)
3. **On-demand** - Compute when generating a Priority 3 message

### Integration with Message Generation

Update `ThreadService.get_message_context()`:

```python
async def get_message_context(self, user_id: UUID) -> MessageContext:
    # ... existing code for follow_ups, threads, core_facts ...

    # Priority 3: Patterns
    patterns = await self.get_actionable_patterns(user_id)

    # Pattern is "actionable" if:
    # - It represents a notable deviation from baseline
    # - It hasn't been referenced recently (avoid repetition)
    # - Confidence is high enough

    # Determine priority
    if follow_ups:
        priority = MessagePriority.FOLLOW_UP
    elif threads_needing_followup or threads:
        priority = MessagePriority.THREAD
    elif patterns:  # NEW
        priority = MessagePriority.PATTERN
    elif core_facts:
        priority = MessagePriority.TEXTURE
    else:
        priority = MessagePriority.GENERIC
```

### Service Structure

```python
# app/services/patterns.py

class PatternService:
    """Compute and retrieve user behavior patterns."""

    def __init__(self, db):
        self.db = db

    # Computation
    async def compute_all_patterns(self, user_id: UUID) -> List[Pattern]
    async def compute_mood_trend(self, user_id: UUID, window_days: int) -> MoodTrendPattern
    async def compute_engagement_trend(self, user_id: UUID) -> EngagementTrendPattern
    async def compute_topic_sentiment(self, user_id: UUID, topic: str) -> TopicSentimentPattern

    # Retrieval
    async def get_patterns(self, user_id: UUID) -> List[Pattern]
    async def get_actionable_patterns(self, user_id: UUID) -> List[Pattern]

    # Storage
    async def save_pattern(self, user_id: UUID, pattern: Pattern) -> None
    async def mark_pattern_used(self, pattern_id: UUID) -> None
```

---

## Part 2: Memory Transparency

### Goal

Surface memory as a feature—not buried in settings, but a natural part of the experience.

> "I remember you mentioned the job interview. I'm keeping an eye on that."

### Design Principles

1. **Narrative, not database** - Show memory as what Daisy is "paying attention to," not a list of extracted facts
2. **Actionable** - Users can correct or delete, but it's not the primary interaction
3. **Trust-building** - Transparency that says "I'm paying attention to you specifically"
4. **Non-intrusive** - Available but not demanding attention

### Where It Lives

**Dashboard (Home) - Primary Surface**

The dashboard currently shows:
- Greeting
- Companion card with "Chat Now" button
- Daily check-in time
- Recent conversations

**Proposed addition: "What I'm paying attention to"**

```
┌─────────────────────────────────────────────────────────┐
│  What [Daisy] is paying attention to                    │
├─────────────────────────────────────────────────────────┤
│  📍 Active threads                                      │
│     • Job interview at Google - waiting to hear back    │
│     • Apartment hunt - 2 viewings this week             │
│                                                         │
│  💭 Things to follow up on                              │
│     • How did the presentation go?                      │
│     • Did you talk to your sister?                      │
│                                                         │
│  [Manage what I remember →]                             │
└─────────────────────────────────────────────────────────┘
```

### Component Structure

```
Dashboard
├── GreetingHeader
├── CompanionCard (existing)
├── MemoryInsightCard (NEW)
│   ├── ActiveThreads (threads with status != resolved)
│   ├── PendingFollowUps (due follow-up questions)
│   └── ManageLink → /memory or /settings/memory
├── CheckInTimeCard (existing)
└── RecentConversations (existing)
```

### Memory Management Page

Accessible via "Manage what I remember" link or Settings.

**Route:** `/memory` or `/settings/memory`

```
┌─────────────────────────────────────────────────────────┐
│  What [Daisy] Remembers                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ACTIVE THREADS                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🎯 Job interview at Google                      │   │
│  │    Status: Waiting to hear back                 │   │
│  │    Details: Technical round went well...        │   │
│  │    [Edit] [Resolve] [Delete]                    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  THINGS I KNOW ABOUT YOU                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Personal                                         │   │
│  │   • Works as software engineer                  │   │
│  │   • Lives in San Francisco                      │   │
│  │                                                  │   │
│  │ People                                           │   │
│  │   • Sister named Emma                           │   │
│  │   • Partner named Alex                          │   │
│  │                                                  │   │
│  │ Preferences                                      │   │
│  │   • Morning person                              │   │
│  │   • Likes direct feedback                       │   │
│  │                                                  │   │
│  │ [Edit any of these →]                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  PATTERNS I'VE NOTICED                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │ • You seem more energized on weekends           │   │
│  │ • You light up talking about your side project  │   │
│  │ • Mondays tend to be harder                     │   │
│  │                                                  │   │
│  │ These are observations, not facts. They help    │   │
│  │ me know when to check in differently.           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### API Endpoints

```python
# GET /api/memory/summary
# Returns structured memory for dashboard card
{
    "active_threads": [...],
    "pending_follow_ups": [...],
    "thread_count": 3,
    "fact_count": 12
}

# GET /api/memory
# Returns full memory for management page
{
    "threads": [...],
    "follow_ups": [...],
    "facts": {
        "personal": [...],
        "relationships": [...],
        "preferences": [...]
    },
    "patterns": [...]
}

# DELETE /api/memory/{context_id}
# Remove a specific memory item

# PATCH /api/memory/{context_id}
# Update a memory item (e.g., mark thread resolved)

# POST /api/memory/threads/{thread_id}/resolve
# Mark a thread as resolved
```

### Frontend Components

```typescript
// components/MemoryInsightCard.tsx
// Dashboard card showing active threads and follow-ups

// app/(dashboard)/memory/page.tsx
// Full memory management page

// components/memory/ThreadCard.tsx
// Editable thread display

// components/memory/FactGroup.tsx
// Grouped facts by category

// components/memory/PatternList.tsx
// Read-only pattern observations
```

### Navigation

**Option 1: Top-level nav item**
```
Home | Chat | Memory | Settings
```

**Option 2: Dashboard feature + Settings deep link**
- Dashboard shows summary card
- "Manage" links to `/settings/memory`
- Memory is a section within Settings

**Option 3: Dashboard feature + Dedicated page**
- Dashboard shows summary card
- "Manage" links to `/memory` (top-level route)
- Settings has link to `/memory` but it's not nested

**Recommendation:** Option 3 - Memory is important enough to be a top-level page, but it's accessed primarily from the dashboard summary, not from nav.

---

## Part 3: User-Controlled Timing

### Current State

- `preferred_message_time` stored as exact TIME (e.g., `09:00:00`)
- Scheduler matches within 2-minute window

### Proposed Change

Add flexibility preference:

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS message_time_flexibility TEXT
    DEFAULT 'exact'
    CHECK (message_time_flexibility IN ('exact', 'around', 'window'));

-- 'exact': Message at preferred_message_time (current behavior)
-- 'around': ±15-30 minutes of preferred_message_time
-- 'window': Morning (6-10am), Midday (11am-2pm), Evening (5-8pm), Night (8-11pm)

ALTER TABLE users ADD COLUMN IF NOT EXISTS message_time_window TEXT
    CHECK (message_time_window IN ('morning', 'midday', 'evening', 'night'));
```

### Onboarding Change

Current: "What time do you usually wake up?"

Proposed:
1. "When do you usually want to hear from me?"
2. Options:
   - "Around a specific time" → ask for time
   - "Sometime in the morning" → set window
   - "Sometime in the evening" → set window

### Settings UI

```
Message Timing
─────────────────────────────────
○ At a specific time: [9:00 AM ▼]
○ Sometime in the morning (6am - 10am)
○ Sometime around midday (11am - 2pm)
○ Sometime in the evening (5pm - 8pm)
○ Sometime at night (8pm - 11pm)
```

### Scheduler Logic Update

```python
async def get_users_for_scheduled_message():
    # Current: exact time match
    # New: depends on flexibility preference

    return await db.fetch_all("""
        SELECT * FROM users u
        WHERE u.onboarding_completed_at IS NOT NULL
          AND (u.telegram_user_id IS NOT NULL OR u.whatsapp_number IS NOT NULL)
          AND (
            -- Exact time users
            (u.message_time_flexibility = 'exact'
             AND local_time BETWEEN preferred_message_time AND preferred_message_time + '2 min')
            OR
            -- Around time users (±30 min window, but only trigger once)
            (u.message_time_flexibility = 'around'
             AND local_time BETWEEN preferred_message_time - '15 min' AND preferred_message_time + '15 min'
             AND NOT already_sent_today)
            OR
            -- Window users (trigger at random time within window, once)
            (u.message_time_flexibility = 'window'
             AND local_time WITHIN window_bounds(u.message_time_window)
             AND NOT already_sent_today
             AND random_trigger_check(u.id))  -- Probabilistic to spread load
          )
          AND NOT already_sent_today
    """)
```

---

## Implementation Order

1. **Phase 1: Pattern Detection Foundation**
   - Add PatternService with mood trend computation
   - Store patterns in user_context with category='pattern'
   - Integrate into get_message_context() for Priority 3

2. **Phase 2: Memory Transparency - Dashboard**
   - Add API endpoint for memory summary
   - Create MemoryInsightCard component
   - Add to dashboard

3. **Phase 3: Memory Management Page**
   - Create /memory route
   - Full CRUD for threads and facts
   - Pattern display (read-only)

4. **Phase 4: Timing Flexibility**
   - Add database columns
   - Update onboarding flow
   - Update scheduler logic
   - Update settings UI

---

*Design document created: 2026-01-22*
