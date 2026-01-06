# ADR-005: Props Domain - Canonical Story Objects

> **Status**: Implemented (v2 - Director-owned revelation)
> **Date**: 2025-01-05
> **Last Updated**: 2025-01-06 (v2 refactor)
> **Deciders**: Architecture Review

---

## Context

Episode-0's mystery and thriller series revealed a gap: **the vibe works, but details don't stick**.

During testing of "The Last Message" (mystery genre), Daniel the character successfully created tension and suspicion. However:

1. **The Yellow Note** - Referenced multiple times but content varied ("I have to finish this..." vs improvised variants)
2. **The Anonymous Text** - The inciting incident, but exact wording never anchored
3. **The Stalker** - Mentioned but no concrete details (photo, description) to track

This is the difference between:
- **Atmospheric storytelling** (mood, tension, suspicion) - working via Genre Doctrines
- **Evidential storytelling** (clues, objects, anchored facts) - not working

### Why This Matters Beyond Mystery

Props aren't just for mystery. Consider:

| Genre | Example Props | Purpose |
|-------|--------------|---------|
| **Mystery** | The note, the photo, the key | Evidence to track |
| **Romance** | The mixtape, the letter, the shared item | Relationship anchors |
| **Thriller** | The map, the supply list, the warning sign | Survival mechanics |
| **Drama** | The family heirloom, the contract | Emotional weight |

Props create **canonical anchors** that:
- Stay consistent across turns (LLM references exact content)
- Persist across episodes (Episode 2 can reference Episode 1's prop)
- Enable visual generation (pre-authored prompts, consistent imagery)
- Provide progression gates (can't proceed until player "examines the note")

---

## Decision

Introduce **Props** as a first-class domain, positioned as **Layer 2.5** in the Context Architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: CHARACTER IDENTITY                                    │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: EPISODE CONTEXT                                       │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2.5: PROPS (NEW)                                         │
│  Static per episode. Canonical objects with exact content.      │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: ENGAGEMENT CONTEXT                                    │
│  ... (continues as before)                                      │
```

### Key Design Principles

1. **Props are authored, not generated** - Like scene motivation (ADR-002), props are content authoring, not runtime generation
2. **Props have canonical content** - The note's text is exact and immutable
3. **Props track revelation state** - System knows which props player has "seen"
4. **Props can have visuals** - Pre-generated images for consistency

---

## Schema Design

### Props Table

```sql
CREATE TABLE props (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_template_id UUID NOT NULL REFERENCES episode_templates(id),

    -- Identity
    name VARCHAR(100) NOT NULL,           -- "The Yellow Note"
    slug VARCHAR(100) NOT NULL,           -- "yellow-note"

    -- What the prop IS
    prop_type VARCHAR(50) NOT NULL,       -- document, object, photo, recording, digital
    description TEXT NOT NULL,            -- "A torn piece of legal paper with hasty handwriting"

    -- Canonical content (if applicable)
    content TEXT,                         -- Exact text/transcript ON the prop
    content_format VARCHAR(50),           -- handwritten, typed, audio_transcript, null

    -- Visual representation
    image_url TEXT,                       -- Pre-generated image
    image_prompt TEXT,                    -- Prompt for regeneration/consistency

    -- Revelation mechanics
    reveal_mode VARCHAR(50) DEFAULT 'character_initiated',
        -- character_initiated: Character shows it naturally
        -- player_requested: Player must ask to see it
        -- automatic: Revealed at specific turn
        -- gated: Requires prior prop or condition
    reveal_turn_hint INT,                 -- Suggested turn (soft guidance for pacing)
    prerequisite_prop_id UUID REFERENCES props(id),  -- Must reveal X before Y

    -- Narrative weight
    is_key_evidence BOOLEAN DEFAULT FALSE,  -- Critical for mystery resolution
    evidence_tags JSONB DEFAULT '[]',       -- ["handwriting", "timeline", "suspect_A"]

    -- Ordering
    display_order INT DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(episode_template_id, slug)
);

-- Index for episode lookup
CREATE INDEX idx_props_episode ON props(episode_template_id);
```

### Session Props Table (Revelation Tracking)

```sql
CREATE TABLE session_props (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    prop_id UUID NOT NULL REFERENCES props(id) ON DELETE CASCADE,

    -- Revelation tracking
    revealed_at TIMESTAMPTZ DEFAULT NOW(),
    revealed_turn INT NOT NULL,
    reveal_trigger VARCHAR(100),          -- "character_showed", "player_asked", "automatic"

    -- Player interaction
    examined_count INT DEFAULT 1,         -- Times player asked to see/review
    last_examined_at TIMESTAMPTZ,

    UNIQUE(session_id, prop_id)
);

-- Index for session lookup
CREATE INDEX idx_session_props_session ON session_props(session_id);
```

---

## Context Injection

### v2: Director-Owned Revelation

**Key architectural change in v2:** The Director (not the character) owns prop revelation detection.

Previously, character context included revelation instructions like "[Introduce when dramatically appropriate]". This was problematic because:
1. The character LLM might or might not mention the prop
2. The system had no way to detect if the character actually revealed it
3. The `automatic` mode triggered at fixed turns regardless of conversation flow

**v2 approach:** Character knows props naturally (like an actor knows their props). The Director observes each exchange and detects when props are mentioned via keyword matching. This is efficient (no LLM call) and conversation-emergent.

```
┌─────────────────────────────────────────────────────────────┐
│  CHARACTER LLM                                               │
│  - Receives props in context (knows what exists)             │
│  - NO revelation instructions (just be the character)        │
│  - Naturally mentions props when it makes sense              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  DIRECTOR.detect_prop_revelations() [POST-RESPONSE]          │
│  - Scans assistant response for prop name/slug mentions      │
│  - If detected: INSERT into session_props, emit prop_reveal  │
│  - No LLM call required (keyword matching)                   │
└─────────────────────────────────────────────────────────────┘
```

### Character Context (v2)

Props are listed simply for character awareness, without revelation instructions:

```python
def _format_props(self) -> str:
    """Format props for LLM context - v2: No revelation instructions."""
    if not self.props:
        return ""

    lines = []
    for prop in self.props:
        evidence_tag = " [KEY]" if prop.is_key_evidence else ""
        lines.append(f"\n• {prop.name}{evidence_tag} ({prop.prop_type})")
        lines.append(f"  {prop.description}")

        if prop.is_revealed and prop.content:
            # Show full canonical content for revealed props
            lines.append(f'  Content: "{prop.content}"')
        elif not prop.is_revealed and prop.content:
            lines.append("  (has content - not yet shown)")

    return "\n".join(lines)
```

### Revelation Modes (v2)

| Mode | v1 Behavior | v2 Behavior |
|------|-------------|-------------|
| `automatic` | Turn-based trigger | **STRUCTURAL**: Director reveals at `reveal_turn_hint` (mystery/thriller) |
| `character_initiated` | Instructed to reveal | **SEMANTIC**: Director detects when character mentions |
| `player_requested` | Instructed to wait for ask | **SEMANTIC**: Director detects when shown after ask |
| `gated` | Required prior prop | **Deprecated** - order emerges from narrative |

In v2, Director owns all revelation detection via two paths:
- **STRUCTURAL** (`automatic` mode): Props reveal at authored turn - for mystery/thriller where props are plot-critical
- **SEMANTIC** (other modes): Keyword detection when character mentions prop naturally - for romance/drama

---

## Frontend Integration

### New SSE Event: `prop_reveal`

When a prop is revealed (turn-based automatic revelation or explicit player action):

```json
{
  "type": "prop_reveal",
  "prop": {
    "id": "uuid",
    "name": "The Yellow Note",
    "slug": "yellow-note",
    "prop_type": "document",
    "description": "A torn piece of yellow legal paper...",
    "content": "I have to finish this or he'll never stop watching us...",
    "content_format": "handwritten",
    "image_url": "https://...",
    "is_key_evidence": true,
    "evidence_tags": ["handwriting", "timeline"],
    "badge_label": "Key Evidence"
  },
  "turn": 5,
  "trigger": "automatic"
}
```

### UI Components

1. **PropCard** - Inline card shown when prop is revealed with noir/evidence aesthetic
   - Displays: icon, name, type, description, expandable content
   - Badge label support (custom or default "Key Evidence")
   - Evidence tags as pills
   - Image loading states with spinner and fallback
   - Click to expand/collapse content

2. **ItemsDrawer** - Genre-agnostic collapsible drawer showing all revealed props
   - Bottom sheet on mobile, side panel on desktop
   - Header displays item count and key evidence count
   - Pulse animation when new items discovered
   - Empty state messaging encourages continued interaction
   - Briefcase icon in ChatHeader with "X collected • Y key" summary
   - Visible even with 0 items (sets player expectations)

3. **PropsEditor** (Studio) - Full CRUD for props per episode
   - Create/edit/delete props with form validation
   - Image thumbnails with expand/download lightbox
   - Fields: name, slug, type, reveal mode, description, content, format, turn hint, badges, tags

### Items Drawer (All Genres)

Genre-agnostic "Items" drawer works for evidence, keepsakes, supplies:

```
┌─────────────────────────────────┐
│ 🗂️ Items (3 collected • 2 key) │
├─────────────────────────────────┤
│ ○ The Anonymous Text            │
│ ○ The Yellow Note               │
│ ○ The Coffee Shop Photo         │
└─────────────────────────────────┘
```

---

## Image Generation Strategy

### Pre-Generation at Scaffold Time

Props should have images generated during content authoring, not runtime:

1. **Consistency** - Same image every time prop is shown
2. **Quality control** - Author can approve/regenerate before publish
3. **No latency** - Image ready when prop is revealed

### Generation Approach

Use existing image generation infrastructure (Replicate/Flux or Gemini Imagen):

```python
# In scaffold script or Studio UI
PROP_IMAGE_PROMPTS = {
    "yellow-note": {
        "prompt": """photograph of a torn piece of yellow legal paper with handwritten cursive text,
        creased and slightly water-stained, dramatic side lighting, noir mystery aesthetic,
        on dark wood surface, shallow depth of field, no readable text""",
        "negative": "clear text, typed, printed, digital, bright colors, cheerful",
        "dimensions": (768, 768),  # Square for flexibility
    }
}
```

### Visual Style by Genre

| Genre | Prop Image Style |
|-------|-----------------|
| Mystery/Noir | High contrast, dramatic shadows, desaturated |
| Romance | Soft lighting, warm tones, intimate framing |
| Thriller | Cold tones, harsh light, clinical |
| Drama | Natural lighting, emotional focus |

---

## Series-Wide Implications

### Cross-Episode Prop References

Props can persist and evolve across episodes:

```sql
-- Episode 2 references Episode 1's note with new context
INSERT INTO props (episode_template_id, name, slug, ...)
VALUES (
    'episode-2-id',
    'The Yellow Note (Analyzed)',
    'yellow-note-analyzed',
    ...
);
-- Links to original via evidence_tags or narrative
```

### All Series Should Consider Props

| Series | Prop Opportunities |
|--------|-------------------|
| **The Last Message** | Note, text message, photo, security footage |
| **Blackout** | Map, supply inventory, warning signs, radio |
| **Cheerleader Crush** | Mixtape, yearbook note, team photo |
| **Hometown Crush** | Love letter, shared item, photo |

Props aren't mandatory but **enhance** any series with tangible story elements.

---

## Implementation Phases

### Phase 1: Schema + Scaffold ✅
- [x] Migration: `props` and `session_props` tables
- [x] Add props to scaffold_the_last_message.py (5 props)
- [x] Generate prop images via existing image scripts
- [x] Basic API endpoints: GET /sessions/{id}/props, POST /sessions/{id}/props/{prop_id}/reveal

### Phase 2: Context Integration ✅ (v2 refactored)
- [x] Director injects available props into context (via `_format_props`)
- [x] Track prop revelations in session_props
- [x] **v2: Director-owned revelation with dual paths:**
  - STRUCTURAL: `reveal_mode='automatic'` + `reveal_turn_hint` triggers at authored turn
  - SEMANTIC: Keyword detection when character mentions prop naturally

### Phase 3: Frontend ✅
- [x] `prop_reveal` SSE event handling (in `useChat.ts`)
- [x] `StreamPropRevealEvent` type definition
- [x] PropCard component with image, description, expandable content
- [x] PropCard rendering in ChatContainer (after instruction cards)
- [x] ItemsDrawer component (genre-agnostic items collection)
- [x] ChatHeader integration with briefcase icon and item count
- [x] Pulse animation on new item discovery
- [x] Items button visible even with 0 items (sets expectations)
- [ ] Prop detail modal - future enhancement

### Phase 4: Studio UI ✅
- [x] PropsEditor component with full CRUD
- [x] Prop form with all fields (name, slug, type, reveal mode, content, etc.)
- [x] Turn hint field (conditionally shown for `automatic` mode)
- [x] Image thumbnails with expand/download lightbox
- [x] Form validation (name, slug, description required)
- [ ] Preview props in episode preview - future enhancement

---

## Alternatives Considered

### 1. Inline Props in Episode Description

**Rejected**: Props mixed into `situation` or `dramatic_question` aren't trackable or referenceable.

### 2. Props as Special Memory Type

**Considered**: Store props in `memory_events` with type="prop".
**Rejected**: Props are authored content (static), memories are extracted content (dynamic). Different lifecycle.

### 3. Props Generated by LLM at Runtime

**Rejected**: Same reason as ADR-002 for scene motivation. Authored content > generated content for consistency.

---

## Consequences

### Positive

1. **Consistent details** - The note says the same thing every turn
2. **Cross-episode continuity** - Episode 2 can reference Episode 1's prop reliably
3. **Visual anchors** - Pre-generated images for key story objects
4. **Player engagement** - Evidence board creates investment in mystery
5. **Authoring clarity** - Writers define exactly what players can discover

### Negative

1. **Authoring burden** - Each episode needs prop definitions
2. **More tables** - Additional schema complexity
3. **Context tokens** - Props add to prompt length

### Neutral

1. **Optional feature** - Series without props continue working as before
2. **Genre-agnostic** - Useful for mystery but applicable to any genre

---

## Related Documents

- **ADR-002**: Theatrical Architecture (authored content philosophy)
- **CONTEXT_LAYERS.md**: Layer architecture (Props = Layer 2.5)
- **DIRECTOR_PROTOCOL.md**: Context injection patterns
- **ADR-003**: Image Generation Strategy (prop image generation)

---

## Open Questions

1. **Prop revelation detection**: ✅ Resolved in v2 - Director-owned detection via dual paths. STRUCTURAL: `automatic` mode reveals at authored turn (mystery/thriller). SEMANTIC: keyword detection for other modes (romance/drama). No LLM call required. `gated` mode deprecated.
2. **Cross-series props**: Can the same prop (e.g., character's signature item) appear in multiple series?
3. **User-created props**: Future consideration - can users add props in user-generated episodes?

---

## Review Notes

This ADR follows the platform's content-first philosophy (ADR-002). Props are authored artifacts that enable consistent, trackable story elements. The Director orchestrates revelation timing, but prop content is immutable once authored.

The key insight: **Mystery needs evidence, romance needs mementos, thriller needs supplies.** Props provide the tangible layer that makes interactive fiction feel real.
