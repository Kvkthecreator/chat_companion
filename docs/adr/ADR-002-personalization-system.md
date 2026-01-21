# ADR-002: Personalization System

**Status**: Draft
**Date**: 2025-01-21
**Deciders**: Kevin, Claude

## Context

The companion needs to adapt its behavior to each user. Currently, personalization is limited to:
- `companion_name` - What the user calls the AI
- `support_style` - General approach (friendly, motivational, etc.)
- `preferred_message_time` - When to send daily messages
- `preferences` - JSONB for misc settings (mostly unused)

This is insufficient because:
- Users can't control communication style (emoji, formality, length)
- No way to set boundaries (topics to avoid)
- Companion doesn't learn from interactions
- No feedback loop for what works

### Relationship to Memory (ADR-001)

Memory and personalization are intertwined:
- **Memory** = What the companion *knows* about you
- **Personalization** = How the companion *behaves* with you

Memory informs personalization ("They mentioned disliking long messages")
Personalization guides memory retrieval ("Focus on work topics, they care about career")

## Decision

Implement a **dual-source personalization system**: explicit preferences (user-controlled) + learned preferences (AI-inferred).

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│            Explicit Preferences                          │
│  ─────────────────────────────────────────────────────  │
│  Source: User settings, onboarding                      │
│  Storage: users.preferences JSONB                       │
│  Examples:                                               │
│    - communication.emoji_level: "minimal"               │
│    - communication.formality: "casual"                  │
│    - boundaries.avoid_topics: ["politics", "religion"]  │
│    - support.style: "accountability"                    │
│  User Control: Full (settings UI)                       │
└─────────────────────────────────────────────────────────┘
                          │
                          │ combined at prompt time
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Companion Behavior                          │
│  ─────────────────────────────────────────────────────  │
│  System prompt adapts based on:                         │
│    - Explicit preferences (primary)                     │
│    - Learned preferences (secondary, if no conflict)    │
│    - User context (memory)                              │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ inferred from interactions
                          │
┌─────────────────────────────────────────────────────────┐
│            Learned Preferences                           │
│  ─────────────────────────────────────────────────────  │
│  Source: Conversation analysis                          │
│  Storage: user_context with category='preference_learned'│
│  Examples:                                               │
│    - "Tends to send short replies"                      │
│    - "Engages most on career topics"                    │
│    - "Usually responds within 5 minutes"                │
│  User Control: View + override in settings              │
└─────────────────────────────────────────────────────────┘
```

### Preference Schema

#### Explicit Preferences (users.preferences JSONB)

```typescript
interface UserPreferences {
  // Communication style
  communication: {
    emoji_level: 'none' | 'minimal' | 'moderate' | 'expressive';
    formality: 'formal' | 'casual' | 'match_mine';
    message_length: 'brief' | 'moderate' | 'detailed';
    humor: 'none' | 'light' | 'playful';
  };

  // Support approach
  support: {
    style: 'friendly_checkin' | 'motivational' | 'accountability' | 'listener';
    feedback_type: 'validation' | 'challenge' | 'balanced';
    questions: 'few' | 'moderate' | 'many';
  };

  // Boundaries
  boundaries: {
    avoid_topics: string[];          // e.g., ["politics", "weight"]
    sensitive_topics: string[];      // handle with care
    no_advice_on: string[];          // e.g., ["medical", "legal"]
  };

  // Timing
  timing: {
    preferred_time: string;          // "09:00"
    timezone: string;
    quiet_hours_start?: string;
    quiet_hours_end?: string;
  };

  // Companion identity
  companion: {
    name: string;                    // "Aria"
    personality_notes?: string;      // User-defined personality tweaks
  };
}
```

#### Learned Preferences (user_context)

```sql
-- Stored in user_context with category='preference_learned'
-- key = preference type, value = observation

INSERT INTO user_context (user_id, category, key, value, confidence, source)
VALUES (
  user_id,
  'preference_learned',
  'response_length',
  'User typically sends 1-2 sentence replies, prefers brief exchanges',
  0.8,
  'inferred'
);
```

### Learning Signals

| Signal | What It Indicates | Preference Updated |
|--------|-------------------|-------------------|
| User sends short replies | Prefers brief exchanges | message_length |
| User uses many emojis | Comfortable with expressive style | emoji_level |
| Quick conversation end | Current approach not engaging | support style |
| User asks follow-up questions | Topic interests them | topic preferences |
| User changes subject | Topic uncomfortable | boundaries |
| Response time patterns | Availability windows | timing |
| Explicit feedback ("too long") | Direct preference signal | relevant pref |

### Preference Priority

When explicit and learned preferences conflict:

```
1. Explicit preference (user set it intentionally)
2. Learned preference with high confidence (>0.8)
3. Learned preference with moderate confidence
4. Default behavior
```

User can always override learned preferences in settings.

### Prompt Integration

```python
def build_personalized_prompt(user: User, context: ContextBundle) -> str:
    prefs = user.preferences
    learned = context.learned_preferences

    prompt_parts = [
        f"You are {prefs.companion.name}, a {prefs.support.style} companion.",
        "",
        "## Communication Style",
        f"- Emoji usage: {prefs.communication.emoji_level}",
        f"- Formality: {prefs.communication.formality}",
        f"- Message length: {prefs.communication.message_length}",
    ]

    if prefs.boundaries.avoid_topics:
        prompt_parts.append(f"\n## Boundaries")
        prompt_parts.append(f"- Avoid topics: {', '.join(prefs.boundaries.avoid_topics)}")

    if learned:
        prompt_parts.append(f"\n## Observed Patterns")
        for pref in learned:
            prompt_parts.append(f"- {pref.value}")

    return "\n".join(prompt_parts)
```

### Settings UI

Users can:

1. **Set explicit preferences** (onboarding + settings)
   - Communication style sliders/toggles
   - Boundary configuration
   - Support style selection

2. **View learned preferences** (transparency)
   - "Here's what I've noticed about our conversations"
   - Option to confirm or reject each

3. **Override learned preferences**
   - "Actually, I do want detailed responses"
   - Converts learned → explicit

4. **Reset preferences**
   - Clear learned preferences
   - Reset to defaults

## Consequences

### Positive

- **User control**: Explicit preferences give users agency
- **Adaptation**: Learned preferences make companion feel attentive
- **Transparency**: Users can see and edit what's learned
- **Boundaries respected**: Clear mechanism for sensitive topics
- **Progressive**: Starts simple, learns over time

### Negative

- **Complexity**: Two preference sources to manage
- **Learning overhead**: Need conversation analysis (async)
- **UI work**: Settings interface needs significant design
- **Cold start**: New users have no learned preferences

### Neutral

- **Storage minimal**: JSONB + few user_context rows
- **Backward compatible**: Current users get defaults

## Alternatives Considered

### Option A: Explicit Only

Only use user-set preferences, no learning.

**Rejected because**:
- Users won't set everything
- Misses opportunity to adapt
- Companion feels static

### Option B: Learned Only

Only infer preferences, no explicit settings.

**Rejected because**:
- Users can't control boundaries
- Learning takes time
- No way to correct wrong inferences
- Privacy concerns

### Option C: Single Preference Table

New `user_preferences` table instead of JSONB.

**Rejected because**:
- Adds schema complexity
- JSONB is flexible enough
- Learned prefs fit well in user_context

## Implementation Plan

### Phase 1: Explicit Preferences Schema
- Define preferences JSONB structure
- Update onboarding to capture key preferences
- Add basic settings UI

### Phase 2: Prompt Integration
- Update system prompt builder to use preferences
- Test with different preference combinations
- Refine prompt templates

### Phase 3: Learning Infrastructure
- Implement conversation analysis (async)
- Define learning signals and rules
- Store learned preferences in user_context

### Phase 4: Settings UI
- Build preferences management interface
- Show learned preferences with transparency
- Enable override/confirmation flow

### Phase 5: Refinement
- Tune learning sensitivity
- Add confidence thresholds
- Implement preference decay for learned prefs

## References

- [ADR-001: Memory Architecture](ADR-001-memory-architecture.md) - Memory system design
- [features/PERSONALIZATION.md](../features/PERSONALIZATION.md) - Feature documentation
- [features/MEMORY_SYSTEM.md](../features/MEMORY_SYSTEM.md) - Memory integration
