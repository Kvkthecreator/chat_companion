# Director UI Toolkit

> **Version**: 1.0.0
> **Status**: Canonical
> **Updated**: 2024-12-20

---

## Purpose

This document defines all UI/UX elements the Director controls during the conversation experience. It serves as the authoritative reference for what the Director can surface, when, and how.

**Relationship to DIRECTOR_PROTOCOL.md**: That document defines Director's evaluation logic; this document defines its UI outputs.

---

## Director UI Responsibility

The Director is the **runtime orchestrator** of the conversation experience. It decides:

| Decision | Output | User Sees |
|----------|--------|-----------|
| What visual to show | `visual_type` | Scene card, instruction card, or nothing |
| When episode ends | `status: done` | Completion card with next episode |
| How pacing feels | `pacing` | (Internal, affects character response) |
| What costs sparks | `deduct_sparks` | Spark balance update |

The Director does NOT decide:
- Message content (Character LLM's job)
- Static layout (Frontend's job)
- User preferences (Settings' job)

---

## Stream Events

The Director emits these events through the conversation stream:

### Core Events

| Event | Trigger | Payload | Component |
|-------|---------|---------|-----------|
| `chunk` | Every text token | `{ content: string }` | StreamingBubble |
| `done` | Message complete | `{ content, director, episode_id }` | MessageBubble, ChatHeader |

### Visual Events

| Event | Trigger | Payload | Component | Cost |
|-------|---------|---------|-----------|------|
| `visual_pending` | Visual moment detected | `{ visual_type, visual_hint, sparks_deducted }` | SceneCard (skeleton) | Sparks |
| `visual_ready` | Image generation complete | `{ image_url, caption }` | SceneCard | — |
| `instruction_card` | Game-like moment | `{ content }` | InstructionCard | Free |

### State Events

| Event | Trigger | Payload | Component |
|-------|---------|---------|-----------|
| `needs_sparks` | Insufficient balance | `{ message }` | InsufficientSparksModal |
| `episode_complete` | Episode done | `{ turn_count, trigger, next_suggestion, evaluation? }` | InlineCompletionCard |

---

## Visual Type Taxonomy

The Director classifies visual moments into types:

| Type | Description | Example | Rendering |
|------|-------------|---------|-----------|
| `character` | Character in emotional moment | "Her expression as she reads the letter" | SceneCard, 4:3 aspect |
| `object` | Significant item close-up | "The key on the table" | SceneCard, square aspect |
| `atmosphere` | Setting/mood without character | "The empty café at closing time" | SceneCard, 4:3 aspect |
| `instruction` | Game-like text overlay | "Choice: Stay or Leave" | InstructionCard |
| `none` | No visual warranted | — | Nothing rendered |

### Cost Model

| Type | Sparks Cost | Notes |
|------|-------------|-------|
| `character` | Episode's `spark_cost_per_scene` (default: 5) | Image generation |
| `object` | Episode's `spark_cost_per_scene` (default: 5) | Image generation |
| `atmosphere` | Episode's `spark_cost_per_scene` (default: 5) | Image generation |
| `instruction` | Free | Text-only, no generation |
| `none` | Free | Nothing happens |

---

## Auto-Scene Modes

How the Director decides when to generate visuals:

| Mode | Behavior | Use Case |
|------|----------|----------|
| `off` | User must manually request | Default, user control |
| `peaks` | Generate on visual moments | Emotional highs |
| `rhythmic` | Every N turns + peaks | Comic-book pacing |

### Configuration

Set per episode template:
```
auto_scene_mode: "peaks"
scene_interval: 5        # For rhythmic mode
spark_cost_per_scene: 5  # Sparks per visual
```

---

## UI Components

### SceneCard

**Purpose**: Render generated scene images inline in chat.

**Visual Types**: `character`, `object`, `atmosphere`

**States**:
- Loading: Skeleton with shimmer
- Loaded: Image with gradient overlay
- Saved: Star icon filled

**Features**:
- Caption display (from `visual_hint`)
- Save-to-memory toggle
- Aspect ratio varies by type (4:3 or square)

### InstructionCard

**Purpose**: Render game-like text overlays without image generation.

**Visual Type**: `instruction`

**Formats Supported**:
- Choices: `"Option A / Option B"` → Rendered as choice buttons
- Key-value: `"Code: 4721"` → Rendered as label + value
- Multi-line: Rendered as formatted text block

**Styling**: Amber/gold theme, decorative corners, game UI feel

### InlineCompletionCard

**Purpose**: Show episode completion and guide to next content.

**Trigger**: `episode_complete` event

**Contains**:
- Evaluation result (if Games feature, e.g., Flirt Archetype)
- Confidence bar
- Primary signals (tags)
- Next episode CTA
- Share button (if shareable)

### InlineSuggestionCard

**Purpose**: Suggest next episode without evaluation.

**Variants**:
- `default`: Full card with episode details
- `compact`: Inline one-liner

---

## Director State

The Director maintains state surfaced to frontend on every exchange:

```typescript
interface StreamDirectorState {
  turn_count: number;           // Current turn
  turns_remaining: number | null; // null if open episode
  is_complete: boolean;         // Episode done?
  status: "going" | "closing" | "done";  // Semantic status
  pacing: "establish" | "develop" | "escalate" | "peak" | "resolve";
}
```

### Pacing Phase

| Phase | Position | Meaning |
|-------|----------|---------|
| `establish` | 0-15% | Setting scene, first spark |
| `develop` | 15-40% | Building rapport, testing |
| `escalate` | 40-70% | Tension rises, stakes increase |
| `peak` | 70-90% | Maximum tension, turning point |
| `resolve` | 90-100% | Landing the moment, hook for next |

### Status Lifecycle

```
going → closing → done
  ↑        ↓
  └────────┘ (can regress if conversation continues)
```

---

## Completion Triggers

What causes `episode_complete`:

| Trigger | Condition | Payload |
|---------|-----------|---------|
| `semantic` | Director evaluates `status: "done"` | Natural narrative end |
| `turn_limit` | `turn_count >= turn_budget` | Hard cap reached |

Both include `next_suggestion` pointing to recommended next episode.

---

## Spark Balance Handling

When Director wants to generate a visual but user lacks sparks:

1. First time per episode: Emit `needs_sparks`, show modal
2. Subsequent times: Skip silently (don't spam)
3. State tracked in: `session.director_state.spark_prompt_shown`

---

## Data Flow

```
User sends message
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ DIRECTOR PHASE 1: Pre-Guidance                                  │
│ (pacing, tension note → injected into character prompt)         │
└─────────────────────────────────────────────────────────────────┘
        ↓
Character LLM generates response → [chunk, chunk, chunk...]
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ DIRECTOR PHASE 2: Post-Evaluation                               │
│ (visual_type, status, hint → decides what to surface)           │
└─────────────────────────────────────────────────────────────────┘
        ↓
Stream events emitted:
  [done] ─────────────────→ MessageBubble + ChatHeader update
  [visual_pending] ───────→ SceneCard skeleton
  [instruction_card] ─────→ InstructionCard
  [needs_sparks] ─────────→ Modal (once)
  [episode_complete] ─────→ InlineCompletionCard
        ↓
Async: Image generation completes
  [visual_ready] ─────────→ SceneCard updates with image
```

---

## Frontend Hook Interface

The `useChat` hook exposes Director state:

```typescript
// From useChat return
{
  // Director state
  directorState: StreamDirectorState | null,
  isEpisodeComplete: boolean,
  nextSuggestion: EpisodeSuggestion | null,
  evaluation: GameEvaluation | undefined,

  // Visual state
  visualPending: VisualPendingState | null,
  instructionCards: string[],
  needsSparks: boolean,

  // Actions
  clearVisualPending: () => void,
  clearCompletion: () => void,
  clearNeedsSparks: () => void,
}
```

---

## Future Capabilities (Not Yet Implemented)

| Capability | Description | Status |
|------------|-------------|--------|
| Interactive instructions | "Choice: A / B" as clickable buttons | Planned |
| Pacing visualization | Show narrative arc progress | Not planned |
| Visual cancellation | Cancel pending image generation | Not planned |
| Director debug mode | Show evaluation reasoning | Not planned |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [DIRECTOR_PROTOCOL.md](DIRECTOR_PROTOCOL.md) | Evaluation logic and two-phase model |
| [QUALITY_FRAMEWORK.md](QUALITY_FRAMEWORK.md) | Quality dimensions and measurement |
| [CONTEXT_LAYERS.md](CONTEXT_LAYERS.md) | Prompt composition layers |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-20 | Initial UI toolkit specification |
