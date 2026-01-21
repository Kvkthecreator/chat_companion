# Memory System

> How the companion remembers you

## Overview

The memory system enables the companion to maintain context about users across conversations. It extracts, stores, and retrieves relevant information to create continuity and personalization.

## Current Implementation

### Storage: `user_context` Table

```sql
user_context (
    id UUID,
    user_id UUID,
    category TEXT,      -- fact, preference, goal, relationship, emotion, situation
    key TEXT,           -- unique identifier within category
    value TEXT,         -- the actual information
    importance_score FLOAT,
    emotional_valence INT,  -- -2 to +2
    source TEXT,        -- extracted, manual
    expires_at TIMESTAMPTZ,
    last_referenced_at TIMESTAMPTZ,
    created_at, updated_at
)
```

### Categories

| Category | Description | Example |
|----------|-------------|---------|
| `fact` | Static personal info | "works as software engineer" |
| `preference` | Likes/dislikes | "prefers morning messages" |
| `goal` | Things working toward | "training for marathon" |
| `relationship` | People in their life | "sister named Emma" |
| `emotion` | Recurring feelings | "anxious about job interview" |
| `situation` | Ongoing circumstances | "moving to new apartment" |

## Architecture (Planned)

See [ADR-001: Memory Architecture](../adr/ADR-001-memory-architecture.md) for full design.

### Memory Tiers

```
┌─────────────────────────────────────────┐
│         Short-term Memory               │
│   (Current conversation context)        │
│   - In-memory during conversation       │
│   - Last few message exchanges          │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│         Mid-term Memory                 │
│   (Active threads & situations)         │
│   - Ongoing events (job interview)      │
│   - Recent emotional states             │
│   - Active goals                        │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│         Long-term Memory                │
│   (Core facts & stable preferences)     │
│   - Personal facts (job, location)      │
│   - Stable preferences                  │
│   - Important relationships             │
└─────────────────────────────────────────┘
```

### Extraction Pipeline

```
Message Exchange
      │
      ▼
[Context Extraction] ─── LLM extracts facts/events/emotions
      │
      ▼
[Deduplication] ─── Check for existing similar context
      │
      ▼
[Validation] ─── Is this worth remembering?
      │
      ▼
[Storage] ─── Write to user_context with appropriate tier
```

### Retrieval Pipeline

```
New Message
      │
      ▼
[Context Loading] ─── Load relevant user_context
      │
      ├── Recent (last 7 days, high relevance)
      ├── Relevant (keyword/semantic match)
      └── Important (high importance_score)
      │
      ▼
[Prompt Building] ─── Include context in system prompt
      │
      ▼
[Response Generation]
```

## Key Design Decisions

1. **Extraction is asynchronous** - Don't block response on context saving
2. **Deduplication before storage** - Avoid redundant memories
3. **Importance scoring** - Not all facts are equally valuable
4. **Temporal relevance** - Recent context weighted higher
5. **User transparency** - Users can view/edit their memories

## TODO

- [ ] Implement tiered memory architecture
- [ ] Add semantic deduplication
- [ ] Build memory management UI
- [ ] Add memory decay/expiration logic
- [ ] Implement "thread" tracking for ongoing situations
