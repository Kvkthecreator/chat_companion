# Context Layers

> **Version**: 1.0.0
> **Status**: Draft
> **Updated**: 2024-12-20

---

## Purpose

This document defines the 6-layer context architecture that composes every character prompt. It specifies what each layer contributes and how layers interact.

---

## Layer Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: CHARACTER IDENTITY                                    │
│  Static per character. Voice, personality, boundaries.          │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: EPISODE CONTEXT                                       │
│  Static per episode. Situation, frame, dramatic question.       │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: ENGAGEMENT CONTEXT                                    │
│  Dynamic per user. Session count, time together, dynamic.       │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 4: MEMORY & HOOKS                                        │
│  Dynamic, retrieved. User facts, pending callbacks.             │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 5: CONVERSATION STATE                                    │
│  Per-turn. Recent messages, turn count, moment focus.           │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 6: DIRECTOR GUIDANCE                                     │
│  Per-turn. Pacing hint, tension note, genre beat.               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Character Identity

**Source**: `characters` table
**Refresh**: Never (static)

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| System Prompt | Core voice and behavior | Genre doctrine, communication style |
| Life Arc | Current journey | `{current_goal, struggle, secret_dream}` |
| Personality | Trait weights | Warmth: 0.8, Wit: 0.6, Intensity: 0.7 |
| Boundaries | What they won't do | Topics avoided, intimacy limits |
| Speech Patterns | Voice consistency | Emoji usage, slang level, message length |

### Quality Impact
- **High**: Determines voice consistency
- **Failure mode**: Character sounds generic or inconsistent

---

## Layer 2: Episode Context

**Source**: `episode_templates` table
**Refresh**: Per episode

### Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| **Situation** | Physical grounding | CRITICAL |
| Episode Frame | Stage direction | High |
| Dramatic Question | Core tension | High |
| Genre | Doctrine selection | High |
| Resolution Types | Valid endings | Medium |

### The Situation Imperative

The `situation` field is the most important context element. It must be:
- Specific (not "a café" but "late-night café, rain on windows, just the two of you")
- Sensory (lighting, sounds, physical details)
- Tension-laden (why is this moment charged?)

**Quality Impact**:
```
Good (with situation): "I glance up from the espresso machine, steam rising..."
Bad (without situation): "I look at you with a mysterious smile..."
```

### Dramatic Question Quality

| Weak | Strong |
|------|--------|
| "Will they connect?" | "Will she show you the sketch she's been hiding?" |
| "Will the moment pass?" | "Can you make her laugh before the café closes?" |

Dramatic questions must be:
- Episode-specific (not reusable)
- Action-oriented (implies what could happen)
- Tension-sustaining (not resolved in 2 turns)

---

## Layer 3: Engagement Context

**Source**: `engagements` table
**Refresh**: Per session

### Components

| Component | Calculation | Purpose |
|-----------|-------------|---------|
| Session Count | `total_sessions` | Relationship depth signal |
| Time Together | `NOW() - first_met_at` | Temporal grounding |
| Dynamic | `{tone, tension_level}` | Current mood |
| Recent Beats | `dynamic.recent_beats[]` | What just happened |

### Format in Prompt

```
RELATIONSHIP CONTEXT:
- Episodes together: 5
- Time since meeting: 2 weeks
- Current dynamic: warm at intensity 65/100
- Recent beats: ["shared a secret", "argued about music"]
```

### Quality Impact
- Prevents relationship regression ("So what do you do?")
- Enables natural evolution (more casual over time)

---

## Layer 4: Memory & Hooks

**Source**: `memory_events`, `hooks` tables
**Refresh**: Per session (retrieved)
**Scope**: Series-level (not character-level)

### Memory Retrieval

```sql
-- Top 10 memories, max 3 per type
SELECT * FROM memory_events
WHERE user_id = ? AND series_id = ?
  AND is_active = TRUE
ORDER BY importance_score DESC, created_at DESC
LIMIT 10
```

| Type | Example | Prompt Section |
|------|---------|----------------|
| `fact` | "Works as a teacher" | "About them:" |
| `event` | "Starting new job Monday" | "Recent in their life:" |
| `preference` | "Loves indie rock" | "Their tastes:" |
| `relationship` | "Close with their mom" | "People in their life:" |
| `goal` | "Wants to travel to Japan" | "Goals/aspirations:" |
| `emotion` | "Nervous about the move" | "How they've been feeling:" |

### Hook Retrieval

```sql
SELECT * FROM hooks
WHERE user_id = ? AND character_id = ?
  AND is_active = TRUE
  AND trigger_after <= NOW()
  AND triggered_at IS NULL
ORDER BY priority DESC
LIMIT 5
```

| Type | Example | Use |
|------|---------|-----|
| `reminder` | "Job interview Thursday" | Time-based callback |
| `follow_up` | "Sister's wedding" | Topic to revisit |
| `milestone` | "One month together" | Relationship marker |

### Quality Impact
- Enables "she remembers me" feeling
- Prevents repetitive questions
- Creates natural callbacks

---

## Layer 5: Conversation State

**Source**: `messages` table, `sessions` table
**Refresh**: Per turn

### Components

| Component | Source | Purpose |
|-----------|--------|---------|
| Message History | Last 20 messages | Immediate context |
| Turn Count | `session.turn_count` | Pacing awareness |
| Session State | `active/paused/faded/complete` | Lifecycle |

### Moment Layer Format

```
MOMENT LAYER (Priority - respond to THIS):
- Their last line: "I guess I should go..."
- Your last line: "Wait—"
- Unresolved tension: Will she stay?
- Setting anchor: doorway, 2am, rain outside
```

### Quality Impact
- Focuses response on immediate moment
- Prevents wandering off-topic
- Maintains physical grounding

---

## Layer 6: Director Guidance

**Source**: `DirectorService` (new)
**Refresh**: Per turn (pre-response)
**Status**: PROPOSED

### Components

| Component | Values | Purpose |
|-----------|--------|---------|
| Pacing Phase | `establish/develop/escalate/peak/resolve` | Where in arc |
| Tension Note | Free text | Subtle direction |
| Physical Anchor | Free text | Sensory reminder |
| Genre Beat | Free text | Genre-appropriate hint |

### Format in Prompt

```
DIRECTOR NOTE (internal guidance):
- Pacing: escalate (turn 8/15)
- Tension: She's holding back—let the silence speak
- Anchor: The rain on windows, steam from her cup
- Beat: romantic tension—unspoken words matter more than said
```

### Quality Impact
- Pre-guides response quality (not post-evaluation)
- Turn-aware pacing
- Genre-specific tension

---

## Layer Composition Order

Layers are assembled in this order (later = higher priority):

1. Character system prompt (foundation)
2. Episode dynamics (situation, frame, question)
3. Engagement context (relationship stats)
4. Memory section (retrieved facts)
5. Hook section (pending callbacks)
6. Moment layer (immediate focus)
7. Director note (guidance) ← NEW

---

## Token Budget

| Layer | Est. Tokens | Priority |
|-------|-------------|----------|
| Character prompt | 300-500 | Critical |
| Episode context | 150-250 | Critical |
| Engagement | 50-100 | High |
| Memories | 200-400 | High |
| Hooks | 50-150 | Medium |
| Message history | 1000-3000 | Sliding window |
| Moment layer | 100-150 | Critical |
| Director note | 50-100 | High |
| **Total Input** | ~2000-4500 | |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-20 | Initial 6-layer specification, added Layer 6 (Director Guidance) |
