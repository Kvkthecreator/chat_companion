# Personalization System

> How the companion adapts to you

## Overview

Personalization determines how the companion behaves with each user. It combines explicit user preferences with learned patterns from interactions.

## Current Implementation

### User Preferences (Explicit)

Stored in `users` table:

| Field | Description | Values |
|-------|-------------|--------|
| `companion_name` | Name for the AI | "Aria", "Luna", etc. |
| `support_style` | Communication approach | friendly_checkin, motivational, accountability, listener |
| `preferred_message_time` | Daily check-in time | TIME (e.g., "09:00:00") |
| `timezone` | User's timezone | "America/New_York", etc. |
| `preferences` | JSONB for additional settings | `{}` |

### Set During Onboarding

1. Display name
2. Companion name
3. Support style
4. Preferred message time
5. Timezone

## Architecture (Planned)

See [ADR-002: Personalization System](../adr/ADR-002-personalization-system.md) for full design.

### Two Types of Personalization

```
┌─────────────────────────────────────────┐
│       Explicit Preferences              │
│   (User-controlled settings)            │
│                                         │
│   - Communication style                 │
│   - Message timing                      │
│   - Topic boundaries                    │
│   - Emoji/formality preferences         │
│                                         │
│   Source: Onboarding + Settings UI      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│       Learned Preferences               │
│   (Inferred from interactions)          │
│                                         │
│   - Response length preference          │
│   - Topics they engage with most        │
│   - Time of day engagement patterns     │
│   - Emotional support vs practical help │
│                                         │
│   Source: Conversation analysis         │
└─────────────────────────────────────────┘
```

### Preference Categories

| Category | Examples | Source |
|----------|----------|--------|
| **Communication** | Emoji usage, formality, humor | Explicit + Learned |
| **Timing** | Best time for messages, response speed | Explicit |
| **Content** | Topics to discuss, topics to avoid | Explicit + Learned |
| **Support** | Validation vs challenge, questions vs statements | Explicit + Learned |
| **Boundaries** | What not to bring up, sensitivity areas | Explicit |

### How It Affects Behavior

```
User Message
      │
      ▼
[Load User Profile]
      │
      ├── Explicit preferences (users table)
      ├── Learned preferences (user_context)
      └── Companion persona (support_style)
      │
      ▼
[Build System Prompt]
      │
      ├── Base companion personality
      ├── + User-specific adaptations
      └── + Current context
      │
      ▼
[Generate Response]
      │
      ▼
[Learn from Interaction] (async)
      │
      └── Did they engage? Re-engage? End conversation?
```

### Learning Signals

| Signal | Indicates | Updates |
|--------|-----------|---------|
| Long responses from user | They're engaged | Topic preference |
| Quick conversation end | Disengagement | Avoid similar approach |
| Follow-up questions | Interest | Topic preference |
| Emoji usage | Communication style | Mirror preference |
| Time of replies | Availability patterns | Timing preference |

## Integration with Memory

Memory and personalization work together:

- **Memory** tells us what they said → "User mentioned job interview next week"
- **Personalization** tells us how to respond → "User prefers supportive check-ins, not advice"

Combined: "Ask how they're feeling about the interview" (not "Here's interview tips")

## Settings UI (Planned)

Users can:
- View current preferences
- Adjust communication style
- Set topic boundaries
- See learned patterns (transparency)
- Override learned preferences

## TODO

- [ ] Expand preferences JSONB schema
- [ ] Build settings management UI
- [ ] Implement preference learning from conversations
- [ ] Add "companion personality" customization
- [ ] Create preference import/export
