# Director UI Toolkit

> **Version**: 2.3.0
> **Status**: Canonical
> **Updated**: 2024-12-24

---

## Purpose

This document defines all UI/UX elements the Director controls during the conversation experience. It serves as the authoritative reference for what the Director can surface, when, and how.

**Relationship to DIRECTOR_PROTOCOL.md**: That document defines Director's evaluation logic and theatrical model; this document defines its UI outputs.

---

## The Theatrical Model (Director's Role)

**Director Protocol v2.2+** reframes the system through theatrical production:

| Layer | Theater Equivalent | What It Provides | When Defined |
|-------|-------------------|------------------|--------------|
| **Genre (Series)** | The Play's Style | Genre conventions, energy descriptions | Series creation |
| **Episode** | The Scene | Situation, dramatic question, scene motivation | Episode authoring |
| **Director (Runtime)** | Stage Manager | Pacing calls, physical grounding | During conversation |
| **Character** | Actor | Improvises within the established frame | Real-time LLM |

**Key Insight**: The director doesn't whisper motivation in the actor's ear during the show. Direction was *internalized* during rehearsal (Episode setup). During performance (chat), the stage manager only calls pacing and grounding.

---

## Director UI Responsibility

The Director is the **runtime stage manager** of the conversation experience. It surfaces:

| Responsibility | Output | User Sees |
|----------------|--------|-----------|
| Pacing phase | `pacing` | (Internal, affects character energy) |
| Episode progress | `turn_count`, `turns_remaining` | Progress tracking in UI |
| Episode completion | `status: done` | Completion card with next episode |
| Visual moments | `visual_type` | Scene card, instruction card, or nothing |
| Episode state | `is_complete`, `status` | UI state changes |

The Director does NOT decide:
- **Scene motivation** (Episode's job - authored as `scene_objective`, `scene_obstacle`, `scene_tactic`)
- **Genre conventions** (Series' job - defined in Genre Doctrines)
- **Message content** (Character LLM's job - actor improvisation)
- **Static layout** (Frontend's job)
- **User preferences** (Settings' job - e.g., `visual_mode_override`)

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
| `visual_pending` | Visual moment detected (if auto-gen enabled) | `{ visual_type, visual_hint }` | SceneCard (skeleton) | Free (included in episode cost) |
| `visual_ready` | Image generation complete | `{ image_url, caption }` | SceneCard | — |
| `instruction_card` | Game-like moment | `{ content }` | InstructionCard | Free |

**Note**: `sparks_deducted` field removed in v2.0. Auto-gen is included in episode entry cost (Ticket + Moments model). Manual "Capture Moment" charges separately (1 Spark T2I / 3 Sparks Kontext Pro).

### State Events

| Event | Trigger | Payload | Component |
|-------|---------|---------|-----------|
| `episode_complete` | Episode done | `{ turn_count, trigger, next_suggestion, evaluation? }` | InlineCompletionCard |

**Note**: `needs_sparks` event removed in v2.0. Spark checks happen at episode entry, not per-generation.

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

---

## Interjection System Architecture

**Director Protocol v2.2** clarifies the fundamental distinction between interjections that display pre-authored/generated content vs. interjections driven by runtime Director evaluation. This distinction is **architecturally decisive** for implementation paths.

### The Core Distinction

```
┌──────────────────────────────────────────────────────────────────┐
│ UPSTREAM-DRIVEN INTERJECTIONS                                    │
│ (Display pre-authored/generated data through Director domain)   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Data Source: Episode templates, Genre definitions, Series config │
│ Director Role: Format, coordinate display timing                 │
│ Service Boundary: Episode/Series Service owns data               │
│ Error Handling: Missing data (graceful degradation)              │
│ Testing Strategy: Test formatting & conditional display logic    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ RUNTIME-DRIVEN INTERJECTIONS                                     │
│ (Director semantic evaluation during conversation)              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Data Source: Director Phase 2 LLM evaluation                     │
│ Director Role: Semantic judgment, trigger actions                │
│ Service Boundary: Director Service owns evaluation logic         │
│ Error Handling: Evaluation failure (fallback to safe defaults)   │
│ Testing Strategy: Test LLM evaluation quality & edge cases       │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Interjection Types by Category

#### UPSTREAM-DRIVEN Interjections

| Component | Data Source | Trigger Condition | Behavior |
|-----------|-------------|-------------------|----------|
| **EpisodeOpeningCard** | `episode_templates` table (`title`, `situation`, `dramatic_question`) | Episode start | Persisted as first chat item (scrollable history) |

**Key Characteristics**:
- **Deterministic Display**: No LLM evaluation needed (data either exists or doesn't)
- **Authored Content**: Created during Episode authoring, not generated at runtime
- **Persistent in Chat**: Remains as first item in chat history (not ephemeral)
- **Graceful Degradation**: Missing optional fields don't break experience

**Error Handling Strategy**:
```python
# EpisodeOpeningCard display logic
if episode.situation:
    display_opening_card(
        title=episode.title,
        situation=episode.situation,
        dramatic_question=episode.dramatic_question  # Optional, may be None
    )
# If no situation, card simply doesn't render (character-only chat fallback)
```

#### RUNTIME-DRIVEN Interjections

| Component | Evaluation Trigger | Decision Logic | Behavior |
|-----------|-------------------|----------------|----------|
| **SceneCard** | After Character message | LLM determines `visual_type` (character/object/atmosphere) | Inline image with caption |
| **InstructionCard** | Character LLM output | Director detects instruction pattern in response | Game-like text overlay |
| **InlineCompletionCard** | After Character message | `status=done` OR `turn_count >= turn_budget` | Episode complete + next suggestion |
| **InlineSuggestionCard** | Director state | Pacing/narrative cues | Lighter "continue to next" nudge |

**Key Characteristics**:
- **Semantic Judgment**: Requires LLM evaluation or algorithmic threshold
- **Runtime Decisions**: When/whether to display determined during conversation
- **Fallback Required**: Evaluation failures → safe defaults (no visual, continue episode)
- **Director Owns Logic**: Evaluation prompts, trigger logic, error handling

**Error Handling Strategy**:
```python
# SceneCard visual evaluation
try:
    visual_eval = await director.evaluate_visual_moment(...)
    if visual_eval.visual_type != "none":
        emit_visual_pending(visual_eval.visual_type, visual_eval.hint)
except LLMEvaluationError:
    # Fallback: No visual generation (safe default)
    visual_type = "none"
```

### Complete Interjection Reference

| Component | Category | Data Source | Trigger | Persistence |
|-----------|----------|-------------|---------|-------------|
| EpisodeOpeningCard | UPSTREAM | Episode template | Episode start | First chat item (permanent) |
| SceneCard | RUNTIME | Phase 2 visual eval | Visual moment detected | Inline in chat history |
| InstructionCard | RUNTIME | Character output detection | Instruction pattern | Inline in chat history |
| InlineCompletionCard | RUNTIME | Phase 2 completion check | Episode done | End of chat |
| InlineSuggestionCard | RUNTIME | Director state | Pacing cues | End of chat |

### Deprecated: StageDirection

**v2.3.0**: The `StageDirection` component (displaying `episode_frame` inline) has been removed.

**Rationale**: `episode_frame` is actor blocking notes for the Character LLM, not user-facing content. User-facing scene-setting belongs in `situation` field, displayed by `EpisodeOpeningCard`.

| Field | Purpose | Audience |
|-------|---------|----------|
| `situation` | Scene-setting paragraph (where, mood, physical details) | **User** (via EpisodeOpeningCard) |
| `episode_frame` | Stage direction / blocking notes | **Character LLM** (context injection) |

---

## Visual Mode (Manual-First Strategy)

**Director Protocol v2.5** implements a **manual-first philosophy** after quality assessment:

### Episode-Level Defaults

All episodes default to `visual_mode='none'` (text-only, fast, no interruptions):

| Mode | Behavior | Default Budget | Usage |
|------|----------|----------------|-------|
| `none` | No auto-gen | 0 | **Default for all episodes** |
| `minimal` | Generate at climax only | 1 gen | Opt-in via user preference |
| `cinematic` | Generate on narrative beats | 3-4 gens | Opt-in via user preference |

### User Preference Override (v2.5)

Users can override episode defaults via Settings > Preferences:

| Override | Behavior | When to Use |
|----------|----------|-------------|
| `"episode_default"` or `null` | Respect episode setting (typically `none`) | **Default for all users** |
| `"always_off"` | Force text-only mode | Accessibility, slow connections, data-saving |
| `"always_on"` | Enable experimental auto-gen (upgrades none→minimal→cinematic) | Power users who want auto-gen |

**Resolution Logic**:
```python
# Episodes default to 'none', users can opt-in for auto-gen
resolved_mode = episode.visual_mode  # Typically 'none'
if user.preferences.visual_mode_override == "always_on":
    resolved_mode = upgrade(episode.visual_mode)  # none→minimal, minimal→cinematic
elif user.preferences.visual_mode_override == "always_off":
    resolved_mode = "none"
```

### Configuration

Set per episode template:
```
visual_mode: "none"           # Default: text-only (manual-first)
generation_budget: 0          # No auto-gen by default
episode_cost: 3               # Sparks to start episode (entry fee)
```

### Manual Generation (Primary Path)

Manual "Capture Moment" is the **primary, proven path** for image generation:
- **T2I mode**: 1 Spark - Reliable character portraits in narrative composition
- **Kontext Pro**: 3 Sparks - High-fidelity character likeness with facial expressions
- Always available regardless of `visual_mode` setting

**Rationale for Manual-First**:
- Auto-gen quality not yet consistent (abstract/confusing images in testing)
- Generation time (5-10 seconds) interrupts narrative flow
- Manual generation provides reliable results when users want images
- Opt-in approach allows testing improvements without degrading default experience

See: [IMAGE_GENERATION.md](../modalities/IMAGE_GENERATION.md) for quality standards

---

## UI Components

### EpisodeOpeningCard

**Purpose**: Render episode setup as the first item in chat history ("program notes" that persist).

**Content Source**: Episode-authored metadata (not Director runtime)
- `episode.title` - Episode name
- `episode.situation` - Scene-setting paragraph (where we are, physical details)
- `episode.dramatic_question` - What's at stake, what tension drives this scene (optional)

**When Shown**: Always as first item in chat history (persists when scrolling up)

**Owner**: Episode domain (authored content), not Director runtime evaluation

**Analogy**: Theater program notes / "Previously on..." recap card

**Visual Design Requirements**:
- Full-width card (matches SceneCard, InstructionCard width)
- `rounded-2xl` with `shadow-2xl` (Director UI design language)
- Gradient background with subtle pattern overlay
- Icon badge: Book/Script icon representing "authored scene"
- Typography hierarchy:
  - Title: Large, bold, white text
  - Situation: Medium paragraph, white/80 opacity
  - Dramatic question: Smaller italicized text with accent color (purple)
- Vertical spacing: `my-6` (consistent with other Director cards)

**Design Principles**:
- **Authored, not generated**: Static content from Episode template
- **Scene establishment**: Sets physical and emotional stage before conversation
- **Visual consistency**: Matches runtime Director cards (SceneCard, InstructionCard)
- **Persistent**: Remains as first chat item (user can scroll up to review)

**Implementation Notes**:
- Rendered as first item in chat message list (not in EmptyState)
- Displayed above all messages, always visible when scrolling to top
- Fade-in animation on initial render
- No dismiss button (permanent part of episode context)

**Current Status**: ✅ Implemented (v2.3.0)

---

### SceneCard

**Purpose**: Render generated scene images inline in chat (runtime visual moments).

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

## Spark Balance Handling (Ticket + Moments Model)

Sparks are checked at **episode entry** for ticket cost, and per-action for manual generation:

### Episode Entry (Ticket Cost)
1. User starts episode → Check `episode_cost` against balance
2. If insufficient → Show `InsufficientSparksModal`
3. Deduct `episode_cost` sparks (typically 3 Sparks for paid episodes)

### During Episode (Manual Generation)
4. User clicks "Capture Moment" → Deduct 1 Spark (T2I) or 3 Sparks (Kontext Pro)
5. Auto-generated visuals (if user opted in) → Free (included in episode entry cost)

**Default Behavior**: No auto-gen (manual-first), so episode cost is pure entry fee

---

## Data Flow (Director Protocol v2.2+)

```
┌─────────────────────────────────────────────────────────────────┐
│ EPISODE SETUP (Authored Content - "Rehearsal")                  │
│ - Series: Genre conventions (GENRE_DOCTRINES)                   │
│ - Episode: Situation, dramatic question                         │
│ - Episode: Scene motivation (objective/obstacle/tactic)         │
│ → Injected into character context before conversation starts    │
└─────────────────────────────────────────────────────────────────┘
        ↓
User sends message
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ DIRECTOR PHASE 1: Pre-Guidance (Deterministic - "Stage Manager")│
│ - Pacing: Algorithmic from turn_count/turn_budget              │
│ - Physical anchor: Extract from episode.situation               │
│ - Genre energy: Lookup from GENRE_DOCTRINES                    │
│ → Formatted into director guidance section of prompt            │
└─────────────────────────────────────────────────────────────────┘
        ↓
Character LLM generates response (Actor improvises within frame)
  → [chunk, chunk, chunk...]
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ DIRECTOR PHASE 2: Post-Evaluation (Semantic + Extraction)       │
│ - Visual evaluation: LLM determines visual_type + hint          │
│ - Completion check: Semantic "status" (going/closing/done)      │
│ - Memory extraction: Facts, preferences, relationships          │
│ - Hook extraction: Character callbacks across episodes          │
│ - Beat tracking: Update relationship dynamics                   │
└─────────────────────────────────────────────────────────────────┘
        ↓
Stream events emitted:
  [done] ─────────────────→ MessageBubble + ChatHeader update
      director: { turn_count, turns_remaining, is_complete, status, pacing }
  [visual_pending] ───────→ SceneCard skeleton (if auto-gen enabled + budget allows)
  [instruction_card] ─────→ InstructionCard (game-like moments)
  [episode_complete] ─────→ InlineCompletionCard
        ↓
Async: Image generation completes (if triggered)
  [visual_ready] ─────────→ SceneCard updates with image
```

**Key Changes from v1.0**:
- Episode-authored motivation (no longer generated per-turn)
- Deterministic Phase 1 (no LLM call for pacing/grounding)
- Director owns memory/hook extraction (Phase 2 expanded)
- Manual-first visuals (auto-gen is opt-in)

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

  // Actions
  clearVisualPending: () => void,
  clearCompletion: () => void,
}
```

---

## Future Capabilities (Not Yet Implemented)

| Capability | Description | Status |
|------------|-------------|--------|
| Interactive instructions | "Choice: A / B" as clickable buttons | Planned |
| Pacing visualization | Show narrative arc progress in chat header | Consideration |
| Visual cancellation | Cancel pending image generation | Not planned |
| Director debug mode | Show evaluation reasoning in dev mode | Not planned |
| Auto-gen quality improvements | Better prompt engineering, model upgrades | Active (experimental opt-in) |

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
| 2.3.0 | 2024-12-24 | **Simplified interjection model**: EpisodeOpeningCard now persists as first chat item (not ephemeral). Deprecated StageDirection component (`episode_frame` is for Character LLM, not user display). Streamlined interjection reference table. |
| 2.2.0 | 2024-12-24 | **Architectural addition**: Interjection System Architecture section documenting upstream vs runtime categorization, implementation decision tree, service boundaries, error handling strategies |
| 2.1.0 | 2024-12-24 | Added EpisodeOpeningCard specification (authored scene setup card before conversation start) |
| 2.0.0 | 2024-12-24 | **Major update**: Theatrical model (v2.2+), manual-first visuals (v2.5), user preference override, removed `sparks_deducted` field, updated data flow diagram, Episode-authored motivation |
| 1.1.0 | 2024-12-23 | Hardened on Ticket + Moments model. Removed legacy auto_scene_mode config. |
| 1.0.0 | 2024-12-20 | Initial UI toolkit specification |
