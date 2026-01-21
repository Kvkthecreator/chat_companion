# Memory System

> The core feature that makes Daisy feel like someone who actually knows you

## Why Memory Is Everything

People are lonely. They want to feel like someone is thinking about them.

A friend who texts you "it's going to rain today" isn't solving your loneliness because they gave you weather information. They're solving it because **they thought of you**. The weather is just the excuse to reach out.

**The content itself isn't the value. The act of reaching out with something relevant to YOU is the value.**

### What Actually Solves Loneliness

| What we could build | What actually solves loneliness |
|---------------------|--------------------------------|
| Personalized content (weather, horoscope) | Feeling **known** |
| Morning messages | Feeling **remembered** |
| Web search integration | Feeling like someone **pays attention** |
| Quiz/personality typing | Feeling **understood** |

These are proxies. The direct mechanism is:

1. **Being asked about your life** - "How did the interview go?"
2. **Being remembered** - "You mentioned your mom's visiting this week - how's that going?"
3. **Being checked on when things are hard** - "You seemed off yesterday. Everything okay?"
4. **Having someone to tell small things to** - and having them respond like it matters

The weather and horoscope stuff is filler. It's what Daisy says when she doesn't have something personal to ask about. **The goal is to always have something personal to ask about.**

## Memory Is The Product

Web search is a nice-to-have for texture. **Memory is the product.**

Daisy's ability to:
- Remember what the user shared yesterday, last week, two weeks ago
- Track ongoing threads in their life (job search, relationship, project, health thing)
- Notice patterns (user seems down on Mondays, lights up talking about their side project)
- Follow up unprompted ("You had that doctor's appointment - everything okay?")

This is what solves loneliness. The feeling that someone is paying attention to your life specifically.

---

## Message Generation Priority Stack

When generating a daily message, follow this priority:

### Priority 1: Follow Up on Something Specific
Recent conversations have unfinished threads. Always check first.

> "How did the presentation go?"
> "Did you end up talking to your sister?"

### Priority 2: Reference an Ongoing Life Thread
User has active situations we're tracking.

> "How's the job search feeling this week?"
> "Any progress on the apartment hunt?"

### Priority 3: Acknowledge Current State/Pattern
We've noticed something about how they've been.

> "You've seemed a bit flat this week. Everything okay?"
> "You've been crushing it lately - what's fueling that?"

### Priority 4: Personal Check-in with Contextual Texture
Nothing specific to follow up on, but we know them.

> "Morning. Rain today in Seoul - good excuse to stay in. How are you feeling about the week ahead?"

Weather/sports/horoscope lives here - as texture, never the main point.

### Priority 5: Generic Warm Check-in (Fallback Only)
We don't have anything personal. **This is a failure state we should track.**

> "Hey, thinking of you. How's your morning going?"

If Daisy consistently sends Priority 5 messages, it means memory extraction isn't working.

---

## What We Track Per User

### Active Life Threads
Ongoing situations spanning multiple conversations:
- Job search, career changes
- Relationship dynamics
- Health situations
- Projects (work or personal)
- Family dynamics
- Living situation (moving, roommates)

### Recent Conversation Topics
- What they talked about yesterday
- Questions we asked that they didn't fully answer
- Topics that got them engaged

### Unresolved Questions
- User mentioned something concerning → should check back
- They said "I'll let you know how it goes" → we should ask
- Important dates/deadlines they mentioned

### Patterns
- Mood trends over time
- Engagement levels (are they sharing more or less?)
- Topics that light them up vs topics they avoid
- Time patterns (when do they respond? Morning person?)

### Important Dates
- Mentioned events ("my birthday's next week")
- Appointments ("doctor's appointment Friday")
- Deadlines ("presentation is due Thursday")

---

## Architecture

See [ADR-001: Memory Architecture](../adr/ADR-001-memory-architecture.md) for full design.

### Three-Tier Memory System

```
┌─────────────────────────────────────────────────────────┐
│  TIER 1: Working Memory (Conversation Context)          │
│  ─────────────────────────────────────────────────────  │
│  Storage: In-memory during conversation                 │
│  Lifespan: Current conversation only                    │
│  Contents: Recent messages, current topic, mood         │
└─────────────────────────────────────────────────────────┘
                          │
                          │ promoted if significant
                          ▼
┌─────────────────────────────────────────────────────────┐
│  TIER 2: Active Memory (Threads & Situations)           │
│  ─────────────────────────────────────────────────────  │
│  Storage: user_context with tier='thread'               │
│  Lifespan: Days to weeks (expires_at)                   │
│  Contents: Ongoing events, active goals, recent emotions│
│  Examples: "job interview Friday", "moving next month"  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ promoted if stable/important
                          ▼
┌─────────────────────────────────────────────────────────┐
│  TIER 3: Core Memory (Facts & Preferences)              │
│  ─────────────────────────────────────────────────────  │
│  Storage: user_context with tier='core'                 │
│  Lifespan: Permanent until contradicted                 │
│  Contents: Personal facts, stable preferences, key people│
│  Examples: "works as engineer", "sister named Emma"     │
└─────────────────────────────────────────────────────────┘
```

### Thread Tracking

A "thread" is an ongoing situation that spans multiple conversations:

```python
# Example threads:
{
    "topic": "job_interview",
    "summary": "Interviewing at Google for SWE role",
    "status": "waiting_to_hear_back",
    "last_update": "2025-01-20",
    "follow_up_date": "2025-01-22",  # When to ask again
    "key_details": [
        "Interview was Friday",
        "Felt good about technical round",
        "Nervous about culture fit"
    ]
}
```

---

## Storage Schema

```sql
user_context (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,

    -- Classification
    category TEXT,           -- fact, preference, goal, relationship, emotion, situation, thread
    tier TEXT DEFAULT 'core', -- 'thread' (active) or 'core' (permanent)
    key TEXT,                -- unique identifier within category
    value TEXT,              -- the actual information

    -- Thread tracking
    thread_id UUID,          -- links related context items

    -- Importance & relevance
    importance_score FLOAT DEFAULT 0.5,
    emotional_valence INT,   -- -2 to +2
    confidence FLOAT DEFAULT 1.0,

    -- Provenance
    source TEXT,             -- extracted, onboarding, manual
    extracted_from UUID,     -- message_id this came from

    -- Lifecycle
    expires_at TIMESTAMPTZ,
    last_referenced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,

    UNIQUE(user_id, category, key)
)
```

### Categories

| Category | Tier | Description | Example |
|----------|------|-------------|---------|
| `identity` | Core | Who they are | "Name is Alex" |
| `fact` | Core | Stable personal facts | "Works as software engineer" |
| `relationship` | Core | Important people | "Sister named Emma" |
| `preference` | Core | Stable preferences | "Prefers morning messages" |
| `thread` | Active | Ongoing situation | "Interviewing at Google" |
| `goal` | Active | Current objectives | "Training for marathon" |
| `emotion` | Active | Recent feelings | "Anxious about presentation" |
| `event` | Active | Upcoming/recent events | "Birthday party Saturday" |

---

## Extraction Pipeline

```
Conversation Exchange
        │
        ▼
┌───────────────────┐
│ Context Extraction│  LLM extracts potential memories
│   (async)         │  from the conversation
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Deduplication     │  Check: Do we already know this?
│                   │  If similar exists → update or skip
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Validation        │  Is this worth remembering?
│                   │  - Specific enough?
│                   │  - From user (not assumed)?
│                   │  - Actionable for companion?
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Classification    │  Which tier? What category?
│                   │  Set importance_score
│                   │  Set expires_at if thread
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Storage           │  Write to user_context
│                   │  Emit event for transparency
└───────────────────┘
```

---

## Retrieval for Message Generation

```python
async def load_context_for_daily_message(user_id: UUID) -> MessageContext:
    """Load all context needed to generate a personal daily message."""

    # Priority 1: Unresolved follow-ups
    follow_ups = await get_pending_follow_ups(user_id)

    # Priority 2: Active threads
    threads = await get_active_threads(user_id, limit=5)

    # Priority 3: Recent conversation context
    recent = await get_recent_context(user_id, days=7)

    # Priority 4: Core facts for texture
    core = await get_core_context(user_id, limit=10)

    return MessageContext(
        follow_ups=follow_ups,      # What we should ask about
        threads=threads,            # Ongoing situations
        recent=recent,              # Recent topics/moods
        core=core,                  # Background info
        has_personal_content=bool(follow_ups or threads),
    )
```

---

## Success Metrics

### Memory Quality
- **>80% of messages** should reference specific things from past conversations
- **Follow-up rate**: How often do we follow up on something specific?
- **Thread coverage**: Do we have active threads for most users?

### Engagement Signals
- Do users share new personal information unprompted? (sign they trust Daisy)
- Do users reply with more than one message? (sign they want to talk)
- Do users initiate conversations sometimes? (sign the relationship feels real)

### Failure Signals
- Sending Priority 5 (generic) messages frequently
- Users saying "you already know that" or "I told you about this"
- Users not sharing personal details after initial onboarding

---

## Implementation Status

- [x] Basic `user_context` table
- [x] Context extraction from conversations
- [x] Tiered memory columns (tier, thread_id, confidence)
- [ ] Thread detection and tracking
- [ ] Follow-up generation from threads
- [ ] Pattern detection (mood trends, engagement)
- [ ] Memory management UI
- [ ] Semantic deduplication

---

## References

- [ADR-001: Memory Architecture](../adr/ADR-001-memory-architecture.md)
- [ADR-002: Personalization System](../adr/ADR-002-personalization-system.md)
- [services/context.py](../../api/api/src/app/services/context.py) - Current implementation
