# ADR-001: Memory System Architecture

**Status**: Draft
**Date**: 2025-01-21
**Deciders**: Kevin, Claude

## Context

Chat Companion is a push-based AI companion that reaches out daily. For the companion to feel personal and continuous, it needs to remember:
- Who the user is (facts, relationships)
- What's happening in their life (situations, events)
- How they prefer to interact (communication style)

The current implementation has a single `user_context` table that stores all memories flat. This works but lacks:
- Temporal awareness (recent vs old memories)
- Validation pipeline (not everything should become memory)
- Clear separation between memory tiers
- Thread tracking for ongoing situations

### Key Insight from YARNNN Architecture

YARNNN tried "unified governance" where one approval meant both "good output" and "save to memory". It failed because it bypassed memory validation. Their lesson: **extraction ≠ storage**. The memory layer needs its own validation.

## Decision

Implement a **three-tier memory architecture** with **separated extraction and validation**.

### Memory Tiers

```
┌─────────────────────────────────────────────────────────┐
│  TIER 1: Working Memory (Conversation Context)          │
│  ─────────────────────────────────────────────────────  │
│  Storage: In-memory during conversation                 │
│  Lifespan: Current conversation only                    │
│  Contents: Recent messages, current topic, mood         │
│  Access: Always loaded for active conversations         │
└─────────────────────────────────────────────────────────┘
                          │
                          │ promoted if significant
                          ▼
┌─────────────────────────────────────────────────────────┐
│  TIER 2: Active Memory (Threads & Situations)           │
│  ─────────────────────────────────────────────────────  │
│  Storage: user_context with category='thread'           │
│  Lifespan: Days to weeks (expires_at)                   │
│  Contents: Ongoing events, active goals, recent emotions│
│  Examples: "job interview Friday", "moving next month"  │
│  Access: Loaded based on recency + relevance            │
└─────────────────────────────────────────────────────────┘
                          │
                          │ promoted if stable/important
                          ▼
┌─────────────────────────────────────────────────────────┐
│  TIER 3: Core Memory (Facts & Preferences)              │
│  ─────────────────────────────────────────────────────  │
│  Storage: user_context with no expires_at               │
│  Lifespan: Permanent until contradicted                 │
│  Contents: Personal facts, stable preferences, key people│
│  Examples: "works as engineer", "sister named Emma"     │
│  Access: Always loaded (limited set)                    │
└─────────────────────────────────────────────────────────┘
```

### Extraction → Validation Pipeline

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

### Schema Changes

Extend `user_context` table:

```sql
ALTER TABLE user_context ADD COLUMN tier TEXT DEFAULT 'core';
-- Values: 'thread' (Tier 2), 'core' (Tier 3)
-- Tier 1 is in-memory only

ALTER TABLE user_context ADD COLUMN thread_id UUID;
-- Links related context items (e.g., all items about "job interview")

ALTER TABLE user_context ADD COLUMN confidence FLOAT DEFAULT 1.0;
-- How confident are we in this extraction? (0.0-1.0)

ALTER TABLE user_context ADD COLUMN extracted_from UUID;
-- Reference to message_id this was extracted from

CREATE INDEX idx_user_context_tier ON user_context(tier);
CREATE INDEX idx_user_context_thread ON user_context(thread_id);
```

### Categories (Refined)

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

### Retrieval Strategy

```python
async def load_context_for_conversation(user_id: UUID) -> ContextBundle:
    # Always load: Core tier (limited)
    core = await load_tier('core', user_id, limit=20)

    # Load recent: Active tier from last 14 days
    active = await load_tier('thread', user_id,
                             since=days_ago(14),
                             limit=10)

    # Load relevant: Semantic match to current topic
    relevant = await semantic_search(user_id,
                                     current_topic,
                                     limit=5)

    return ContextBundle(core=core, active=active, relevant=relevant)
```

### Thread Tracking

"Threads" are ongoing situations that span multiple conversations:

```python
# When user mentions interview
thread = await find_or_create_thread(
    user_id=user_id,
    topic="job_interview",
    summary="Interviewing at Google for SWE role"
)

# Link new context to thread
await save_context(
    user_id=user_id,
    category='event',
    key='interview_date',
    value='Friday 10am',
    thread_id=thread.id,
    tier='thread',
    expires_at=friday + days(7)  # Expire week after
)
```

## Consequences

### Positive

- **Better continuity**: Threads track ongoing situations naturally
- **Cleaner context**: Validation prevents noise in memories
- **Temporal relevance**: Active memories decay, core memories persist
- **Transparency**: Users can see what companion remembers (by tier)
- **Scalable**: Core tier stays small, active tier rotates

### Negative

- **More complexity**: Three tiers vs one flat table
- **Extraction cost**: LLM call for every conversation (async mitigates)
- **Migration needed**: Existing user_context needs tier assignment

### Neutral

- **Storage similar**: Still using user_context table (extended)
- **Query patterns change**: Need tier-aware queries

## Alternatives Considered

### Option A: Vector-Only Memory (RAG)

Store all context as embeddings, retrieve via semantic search.

**Rejected because**:
- Loses structure (categories, importance)
- Can't easily show user "what we remember"
- Overkill for companion use case
- Harder to debug/explain

### Option B: Keep Flat Structure

Continue with current single-tier user_context.

**Rejected because**:
- No temporal awareness
- Core facts get lost in noise
- Can't track ongoing situations
- No validation pipeline

### Option C: Separate Tables Per Tier

Create `core_memory`, `active_memory`, `working_memory` tables.

**Rejected because**:
- More schema complexity
- Same data model, just split
- Harder to query across tiers
- Migration complexity

## Implementation Plan

### Phase 1: Schema Extension
- Add `tier`, `thread_id`, `confidence`, `extracted_from` columns
- Migrate existing data (default to 'core' tier)
- Add indexes

### Phase 2: Extraction Pipeline
- Implement async extraction after conversations
- Add deduplication check
- Add validation rules

### Phase 3: Thread Tracking
- Implement thread detection
- Link related context items
- Add thread-based retrieval

### Phase 4: Retrieval Enhancement
- Implement tier-aware loading
- Add recency weighting
- Add relevance scoring

### Phase 5: User Transparency
- Memory viewer in settings
- Edit/delete capabilities
- Thread visualization

## References

- [YARNNN Layered Architecture v4.1](reference) - Separated governance lesson
- [features/MEMORY_SYSTEM.md](../features/MEMORY_SYSTEM.md) - Feature documentation
- [database/DATA_MODEL.md](../database/DATA_MODEL.md) - Current schema
