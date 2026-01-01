# User Character Customization

> **Status**: PROPOSED
> **Created**: 2025-01-01
> **Authors**: Engineering
> **Related**: [EPISODE-0_CANON.md](../EPISODE-0_CANON.md), [GLOSSARY.md](../GLOSSARY.md), [SYSTEM_ARCHITECTURE.md](../architecture/SYSTEM_ARCHITECTURE.md)

---

## Executive Summary

This document defines the architecture and implementation plan for **user character customization** — enabling users to create their own characters that play in platform-authored episodes.

### Core Thesis

Episode-0's moat is **authored episodes** — manufactured moments with dramatic stakes, situational clarity, and reply gravity. User-customized characters strengthen this moat by enabling "MY character in YOUR compelling situation" — more emotionally charged than pre-cast experiences.

### What This Is

- Users create characters (name, appearance, personality archetype, energy level)
- User-created characters play in platform-authored episodes
- Episodes remain curated; character is the customization layer

### What This Is NOT

- User-generated episodes (Phase 2+)
- Shareable/public characters (Phase 2+)
- Full character editing (backstory, system prompt, etc.)

---

## Architecture Decision: The Role Abstraction

> **See**: [ADR-004: User Character & Role Abstraction](../decisions/ADR-004-user-character-role-abstraction.md)

**Summary**: Introduce **Role** as a conceptual abstraction that defines the archetype slot an episode requires, which can be filled by canonical OR user-created characters.

**Key consequences**:
- Episodes become character-agnostic (written for roles, not specific characters)
- User characters can "audition" for roles based on archetype compatibility
- Scene motivation (objective/obstacle/tactic) stays with the role/episode, not the character
- Canonical characters remain as pre-cast defaults for roles

### The Role Entity

```
EpisodeTemplate → defines → Role (archetype slot)
                              ↓
                         "The barista in this café scene"
                              ↓
                    filled by → Character (canonical OR user-created)
```

**Role** represents:
- The **archetype** required (e.g., "warm café worker," "mysterious stranger")
- The **constraints** a character must satisfy to play this role
- The **scene motivation** (objective/obstacle/tactic) — authored per role

---

## Terminology Updates

### New Terms (add to GLOSSARY.md)

| Term | Definition | DB Table | Notes |
|------|------------|----------|-------|
| **Role** | Archetype slot in an episode that a character fills. Defines scene motivation and compatibility constraints. | `roles` | Bridge between episode and character |
| **User Character** | Character created by a user (vs. canonical/platform character). Private to the creating user. | `characters` | `is_user_created = true` |
| **Canonical Character** | Platform-authored character with full backstory, curated quality. | `characters` | `is_user_created = false` |
| **Character Casting** | The assignment of a character (canonical or user) to a role in an episode. | `session.character_id` | Runtime decision |

### Updated Terms

| Term | Current | Updated |
|------|---------|---------|
| **Episode Template** | "Every episode has ONE anchor character" | "Every episode has ONE anchor role, which can be filled by compatible characters" |
| **Genesis Stage** | "No user/creator content" | Phase complete — user character creation now supported |

---

## Data Model

### New: Role Entity

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name TEXT NOT NULL,                    -- "The Barista", "The Stranger"
    slug TEXT UNIQUE NOT NULL,
    description TEXT,                      -- For content authoring UI

    -- Compatibility constraints
    archetype TEXT NOT NULL,               -- Required archetype (warm_supportive, mysterious_reserved, etc.)
    compatible_archetypes TEXT[],          -- Additional compatible archetypes
    required_traits JSONB DEFAULT '{}',    -- Minimum personality requirements

    -- Scene motivation (moved from episode_template per ADR-002)
    scene_objective TEXT,                  -- "You want them to notice you've been waiting"
    scene_obstacle TEXT,                   -- "You can't seem too eager, you have pride"
    scene_tactic TEXT,                     -- "Pretend to be busy, but leave openings"

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for archetype lookup
CREATE INDEX idx_roles_archetype ON roles(archetype);
```

### Modified: Episode Template

```sql
ALTER TABLE episode_templates
    ADD COLUMN role_id UUID REFERENCES roles(id),
    -- scene_objective, scene_obstacle, scene_tactic remain for backward compat
    -- but are deprecated in favor of role.scene_*
    ADD COLUMN is_role_generic BOOLEAN DEFAULT FALSE;  -- True if written for any compatible character

-- Migration: existing episodes keep character_id, role_id is optional
-- New episodes should use role_id
```

### Modified: Characters

```sql
ALTER TABLE characters
    ADD COLUMN is_user_created BOOLEAN DEFAULT FALSE,
    ADD COLUMN created_by_user_id UUID REFERENCES users(id),
    ADD COLUMN is_public BOOLEAN DEFAULT FALSE;  -- Future: shareable characters

-- Index for user's characters
CREATE INDEX idx_characters_user_created ON characters(created_by_user_id)
    WHERE is_user_created = TRUE;

-- Constraint: user-created characters must have created_by_user_id
ALTER TABLE characters ADD CONSTRAINT chk_user_created_has_owner
    CHECK (is_user_created = FALSE OR created_by_user_id IS NOT NULL);
```

### Modified: Sessions

```sql
-- Sessions already have character_id
-- Add role_id for explicit role tracking
ALTER TABLE sessions
    ADD COLUMN role_id UUID REFERENCES roles(id);

-- The (character_id, role_id) pair defines "who is playing what"
```

### Memory Scoping (Confirmed)

Memories remain scoped to `(user_id, character_id, series_id)`:

```sql
-- Existing: memory_events table
-- user_id: who the memory is for
-- character_id: which character (canonical OR user-created)
-- series_id: which series context

-- This means:
-- - Same user-created character in different series = different memories
-- - Same user-created character replaying same series = memories persist
```

---

## Character Creation: Exposed Parameters

### Definitely Exposed (Phase 1)

| Field | UI Element | Maps To | Constraints |
|-------|------------|---------|-------------|
| **Name** | Text input | `characters.name` | 2-30 chars, content filter |
| **Appearance** | Text input + image gen | `avatar_kits.appearance_prompt` | Content filter, generates anchor |
| **Archetype** | Dropdown | `characters.archetype` | Preset list only |
| **Flirting Level** | Dropdown/slider | `characters.boundaries.flirting_level` | reserved/playful/flirty/bold |

### Maybe Exposed (Phase 1.5)

| Field | UI Element | Maps To | Notes |
|-------|------------|---------|-------|
| **Personality sliders** | 3-5 range inputs | `characters.baseline_personality` | Simplified Big Five |
| **Speech style** | Toggle/dropdown | `characters.tone_style` | Emoji usage, formality |

### Not Exposed

| Field | Reason |
|-------|--------|
| **Backstory** | Free text = quality risk, moderation burden |
| **System prompt** | Technical, quality risk |
| **Genre** | Platform-controlled (ADR-001) |
| **Scene motivation** | Authored content, lives in Role |
| **Likes/Dislikes** | Could add later, low priority |

---

## User Experience Flow

### Pattern: "Choose Your Character" (RPG/Visual Novel)

```
User browses episodes
    ↓
Taps episode card: "Hometown Crush: The Café Meet-Cute"
    ↓
Pre-episode screen: "Choose who you'll meet"
    ├── [Minji] - Canonical character, with preview
    ├── [Your Characters] - User's created characters
    │       ├── [Alex] - Previously created
    │       └── [+ Create New]
    └── (Future: [Browse Community])
    ↓
User selects or creates character
    ↓
Episode starts with selected character in the role
```

### Character Creation Flow

```
[+ Create New Character]
    ↓
Step 1: Name
    "What's their name?"
    [Text input with validation]
    ↓
Step 2: Appearance
    "Describe how they look"
    [Text input] → [Generate Preview] → [Regenerate or Accept]
    ↓
Step 3: Personality
    "What are they like?"
    [Archetype dropdown: Warm & Supportive, Playful & Teasing, etc.]
    ↓
Step 4: Energy
    "How do they flirt?"
    [Slider or dropdown: Reserved → Playful → Flirty → Bold]
    ↓
[Create Character]
    ↓
Character saved, avatar generated, returned to episode selection
```

### Character Management

```
Profile → My Characters
    ├── [Alex] - Edit, Delete
    ├── [Jordan] - Edit, Delete
    └── [+ Create New]

Edit flow:
    - Name: editable
    - Appearance: regenerate avatar
    - Archetype: editable (may affect role compatibility)
    - Flirting level: editable
```

---

## System Prompt Generation

User-created characters need system prompts generated from their parameters.

### Generation Logic

```python
def generate_user_character_system_prompt(
    name: str,
    archetype: str,
    flirting_level: str,
    personality: Optional[dict] = None,
    tone_style: Optional[dict] = None,
) -> str:
    """Generate system prompt for user-created character.

    Key differences from canonical characters:
    - No backstory section (user didn't provide one)
    - Simplified personality from archetype preset
    - Genre doctrine injected at runtime by Director (ADR-001)
    """

    # Get archetype preset (existing PERSONALITY_PRESETS)
    archetype_config = PERSONALITY_PRESETS.get(archetype, PERSONALITY_PRESETS["warm_supportive"])

    # Build prompt from archetype + user params
    prompt = f"""You are {name}, a {archetype_config['description']}.

PERSONALITY:
{format_personality_traits(archetype_config['traits'])}

COMMUNICATION STYLE:
- Energy level: {FLIRTING_LEVEL_DESCRIPTIONS[flirting_level]}
- {format_tone_style(tone_style or archetype_config.get('default_tone', {}))}

CORE BEHAVIORS:
- Stay in character as {name}
- Respond naturally to the situation
- Follow the scene's dramatic tension
- Never break character or acknowledge being AI

{{genre_doctrine}}
{{scene_motivation}}
{{memories}}
{{hooks}}
"""
    return prompt
```

### Runtime Injection

At conversation time, Director injects:
- `{genre_doctrine}` — from episode's series genre
- `{scene_motivation}` — from role's objective/obstacle/tactic
- `{memories}` — from memory_events
- `{hooks}` — from hooks table

---

## Role Compatibility

### Matching Characters to Roles

```python
def can_character_play_role(character: Character, role: Role) -> bool:
    """Check if a character is compatible with a role."""

    # Primary archetype match
    if character.archetype == role.archetype:
        return True

    # Compatible archetypes list
    if role.compatible_archetypes and character.archetype in role.compatible_archetypes:
        return True

    # Trait requirements (if any)
    if role.required_traits:
        char_traits = character.baseline_personality.get('traits', {})
        for trait, min_value in role.required_traits.items():
            if char_traits.get(trait, 0) < min_value:
                return False

    return False

def get_compatible_roles_for_character(character: Character) -> list[Role]:
    """Get all roles a character can play."""
    # Query roles where archetype matches or is in compatible list
    pass

def get_compatible_characters_for_role(role: Role, user_id: UUID) -> list[Character]:
    """Get canonical + user's characters that can play a role."""
    pass
```

### Archetype Compatibility Matrix (Example)

| Role Archetype | Compatible Character Archetypes |
|----------------|--------------------------------|
| warm_supportive | warm_supportive, playful_teasing |
| mysterious_reserved | mysterious_reserved, intense_passionate |
| playful_teasing | playful_teasing, warm_supportive |
| confident_assertive | confident_assertive, intense_passionate |

---

## API Endpoints

### Character CRUD

```
# Create user character
POST /api/characters
Body: { name, appearance_prompt, archetype, flirting_level }
Response: Character with generated avatar

# List user's characters
GET /api/characters/mine
Response: [Character, ...]

# Get single character
GET /api/characters/{id}
Response: Character

# Update character
PATCH /api/characters/{id}
Body: { name?, archetype?, flirting_level? }
Response: Character (system_prompt regenerated if needed)

# Regenerate avatar
POST /api/characters/{id}/regenerate-avatar
Body: { appearance_prompt? }  # Optional new prompt
Response: Character with new avatar

# Delete character
DELETE /api/characters/{id}
Response: 204
```

### Episode Character Selection

```
# Get characters available for an episode
GET /api/episodes/{episode_id}/available-characters
Response: {
    canonical: [Character],      # Platform characters for this role
    user_characters: [Character] # User's compatible characters
}

# Start episode with character selection
POST /api/sessions
Body: {
    episode_template_id,
    character_id  # Canonical or user-created
}
Response: Session
```

---

## Frontend Specification

### New Screens

| Screen | Route | Purpose |
|--------|-------|---------|
| **My Characters** | `/characters` | List user's created characters with edit/delete actions |
| **Create Character** | `/characters/new` | Multi-step character creation flow |
| **Edit Character** | `/characters/[id]/edit` | Modify existing character |
| **Character Selection** | Modal pre-episode | Choose canonical or user character for episode |

### Create Character Flow (UI Steps)

```
┌─────────────────────────────────────────────┐
│  Step 1: Name                               │
│  ─────────────────────────────────────────  │
│  "What's their name?"                       │
│  ┌─────────────────────────────────────┐    │
│  │ [Text input: 2-30 chars]            │    │
│  └─────────────────────────────────────┘    │
│                              [Next →]       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Step 2: Appearance                         │
│  ─────────────────────────────────────────  │
│  "Describe how they look"                   │
│  ┌─────────────────────────────────────┐    │
│  │ [Textarea: appearance description]  │    │
│  └─────────────────────────────────────┘    │
│  Examples: "young woman with short blue     │
│  hair and warm smile" / "tall man with      │
│  silver hair and mysterious eyes"           │
│                                             │
│  [← Back]              [Generate Preview →] │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Step 2b: Avatar Preview                    │
│  ─────────────────────────────────────────  │
│  ┌───────────────────┐                      │
│  │                   │                      │
│  │   [Generated      │   ✓ Accept           │
│  │    Avatar]        │                      │
│  │                   │   ↻ Regenerate       │
│  │                   │     (5 sparks)       │
│  └───────────────────┘                      │
│                                             │
│  [← Back to description]      [Accept →]    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Step 3: Personality                        │
│  ─────────────────────────────────────────  │
│  "What are they like?"                      │
│                                             │
│  ○ Warm & Supportive                        │
│    Caring, attentive, emotionally available │
│                                             │
│  ○ Playful & Teasing                        │
│    Witty, flirty, loves banter              │
│                                             │
│  ○ Mysterious & Reserved                    │
│    Enigmatic, guarded, intriguing           │
│                                             │
│  ○ Confident & Bold                         │
│    Direct, assertive, magnetic              │
│                                             │
│  [← Back]                        [Next →]   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Step 4: Energy Level                       │
│  ─────────────────────────────────────────  │
│  "How do they express interest?"            │
│                                             │
│  Reserved ──●────────────────────── Bold    │
│             ↑                               │
│          Playful                            │
│                                             │
│  Preview: "Hints at interest through        │
│  subtle gestures and playful teasing"       │
│                                             │
│  [← Back]              [Create Character →] │
└─────────────────────────────────────────────┘
```

### Character Selection Modal (Pre-Episode)

```
┌─────────────────────────────────────────────┐
│  Choose who you'll meet                     │
│  ─────────────────────────────────────────  │
│                                             │
│  OFFICIAL                                   │
│  ┌─────────┐                                │
│  │ [Minji] │  Minji - The Barista           │
│  │  avatar │  Warm, playful, your regular   │
│  └─────────┘  spot's favorite               │
│                                             │
│  YOUR CHARACTERS                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ [Alex]  │  │ [Jordan]│  │  [+]    │     │
│  │  avatar │  │  avatar │  │ Create  │     │
│  └─────────┘  └─────────┘  └─────────┘     │
│                                             │
│  [Cancel]                    [Start →]      │
└─────────────────────────────────────────────┘
```

### API Integration

| Action | Endpoint | Notes |
|--------|----------|-------|
| List my characters | `GET /characters/mine` | Paginated |
| Create character | `POST /characters` | Returns character with avatar URL |
| Update character | `PATCH /characters/{id}` | Ownership validated |
| Delete character | `DELETE /characters/{id}` | Cascade deletes avatar_kit |
| Regenerate avatar | `POST /characters/{id}/regenerate-avatar` | Costs 5 sparks |
| Get episode characters | `GET /episodes/{id}/available-characters` | Returns canonical + compatible user chars |
| Start episode | `POST /sessions` with `character_id` | Works with any compatible character |

---

## Content Moderation

### Name Filtering

```python
async def validate_character_name(name: str) -> tuple[bool, str]:
    """Validate character name against content policy."""

    # Length check
    if len(name) < 2 or len(name) > 30:
        return False, "Name must be 2-30 characters"

    # Blocklist check (slurs, banned terms)
    if contains_blocked_terms(name):
        return False, "Name contains prohibited content"

    # Real person detection (optional, can be ML-based)
    if is_likely_real_person(name):
        return False, "Name appears to reference a real person"

    return True, ""
```

### Appearance Prompt Filtering

```python
async def validate_appearance_prompt(prompt: str) -> tuple[bool, str]:
    """Validate appearance prompt against content policy."""

    # Length check
    if len(prompt) > 500:
        return False, "Description too long"

    # NSFW detection
    if contains_nsfw_content(prompt):
        return False, "Description contains prohibited content"

    # Real person detection
    if references_real_person(prompt):
        return False, "Cannot create characters resembling real people"

    # IP detection (celebrities, fictional characters)
    if references_protected_ip(prompt):
        return False, "Cannot create characters from copyrighted works"

    return True, ""
```

---

## Monetization

### Character Creation Cost Model

**Decision**: Free creation with bundled avatar + paid regeneration.

| Action | Cost | Notes |
|--------|------|-------|
| Create character (name, archetype, flirting level) | FREE | Zero friction to start |
| First avatar generation | FREE | Included with creation (1 auto-attempt) |
| Avatar regeneration | 5 sparks | Per attempt |
| Change appearance prompt + regenerate | 5 sparks | Per attempt |
| Edit name/archetype/flirting level | FREE | No avatar regen needed |

**Rationale**:
- Zero friction drives adoption — users get complete character for free
- Monetization on iteration (users who want "perfect" avatar will pay)
- Aligns with existing spark economy (scene generation = 5 sparks)

### Character Slots

| Tier | Slots | Notes |
|------|-------|-------|
| Free | 3 | Sufficient for experimentation |
| Premium | 10+ | Or unlimited with subscription |

### Avatar Generation Flow

```
Character Creation:
1. User enters name, appearance, archetype, flirting level → FREE
2. System generates avatar (1 auto-attempt) → FREE
3. User sees result → Accept or Regenerate
4. Regenerate → 5 sparks per attempt
5. Character saved with accepted avatar

Post-Creation Regeneration:
1. User taps "Regenerate Avatar"
2. Optionally edits appearance prompt
3. Confirm spark spend (5 sparks)
4. New avatar generated
5. Accept or try again (5 more sparks)
```

---

## Migration Strategy

### Phase 1a: Schema & Backend (Week 1-2)

1. Add `is_user_created`, `created_by_user_id` to characters table
2. Create roles table
3. Add `role_id` to episode_templates and sessions
4. Implement character CRUD endpoints
5. Implement system prompt generation for user characters
6. Implement role compatibility checking

### Phase 1b: Avatar Generation (Week 2-3)

1. Create user character avatar generation flow
2. Implement appearance prompt validation
3. Wire to existing AvatarGenerationService

### Phase 1c: Episode Integration (Week 3-4)

1. Implement character selection UI pre-episode
2. Update session creation to accept any compatible character
3. Update conversation context to inject role's scene motivation
4. Test full flow: create character → select in episode → play

### Phase 1d: Character Management (Week 4)

1. My Characters list UI
2. Edit character flow
3. Delete character flow
4. Avatar regeneration flow

---

## Migration: Existing Episodes

Existing episodes have `character_id` directly. Migration options:

### Option A: Implicit Roles (Recommended for Phase 1)

- Don't require explicit Role entity for existing episodes
- Treat existing `character_id` as "this episode has a built-in role matching this character's archetype"
- User characters can play if archetype matches the canonical character's archetype

```python
def get_episode_role(episode: EpisodeTemplate) -> Role:
    """Get or infer role for an episode."""
    if episode.role_id:
        return get_role(episode.role_id)

    # Implicit role from canonical character
    canonical_char = get_character(episode.character_id)
    return Role(
        archetype=canonical_char.archetype,
        compatible_archetypes=[canonical_char.archetype],
        scene_objective=episode.scene_objective,
        scene_obstacle=episode.scene_obstacle,
        scene_tactic=episode.scene_tactic,
    )
```

### Option B: Explicit Migration (Phase 2)

- Create Role entities for all existing episodes
- Migrate scene motivation from episode to role
- Update all episodes to reference role_id

---

## Success Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Character Creation Rate** | % of users who create a character | >20% of active users |
| **Custom Character Usage** | % of sessions using user-created characters | >30% of sessions |
| **Creation Completion** | % who complete character creation flow | >70% |
| **Episode Compatibility** | % of episodes playable with user characters | 100% (via implicit roles) |

---

## Future Phases (Not in Scope)

### Phase 2: User-Created Episodes
- Users define situations, dramatic questions
- Platform validates quality (dramatic question strength, etc.)
- Requires Role to be fully explicit

### Phase 3: Shareable Characters
- `is_public` flag on characters
- Discovery/browse community characters
- Moderation pipeline for public content
- Creator attribution and potential monetization

---

## Resolved Decisions

| Question | Decision |
|----------|----------|
| **Canonical character coexistence** | Yes — users see both Minji AND their characters as options |
| **Character limit per user** | 3 free slots, 10+ with premium |
| **Cross-series character usage** | Yes — same character can play in different series, memories are series-scoped |
| **Archetype change impact** | Natural behavior — active sessions have loaded context, new sessions get updated character |
| **Role table** | Create now (not deferred) — explicit schema from the start |
| **Avatar generation cost** | First avatar free, regeneration costs 5 sparks |

---

## Related Documents

- [EPISODE-0_CANON.md](../EPISODE-0_CANON.md) — Platform philosophy
- [GLOSSARY.md](../GLOSSARY.md) — Terminology (needs Role addition)
- [SYSTEM_ARCHITECTURE.md](../architecture/SYSTEM_ARCHITECTURE.md) — Technical architecture
- [CHARACTER_DATA_MODEL.md](../quality/core/CHARACTER_DATA_MODEL.md) — Character schema
- [CONTEXT_LAYERS.md](../quality/core/CONTEXT_LAYERS.md) — Prompt composition
