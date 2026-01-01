# Cinematic Casting Implementation

> **Status**: ACTIVE
> **Created**: 2025-01-01
> **Authors**: Engineering
> **Supersedes**: [USER_CHARACTER_CUSTOMIZATION.md](./USER_CHARACTER_CUSTOMIZATION.md) (role compatibility sections)
> **Related**: [ADR-004: Cinematic Casting](../decisions/ADR-004-user-character-role-abstraction.md)

---

## Executive Summary

This document defines the **Cinematic Casting** model — a paradigm where **any character can play any role**, with the system adapting prompts to bridge differences between character and role archetypes.

### Core Principle

In cinema, a "shy barista" role written for one actor becomes something different when played by a confident actor — and that's a feature, not a bug. Episode-0 embraces this: users can cast ANY of their characters in ANY episode, and the system creates narrative coherence through **casting adaptation** rather than **compatibility gating**.

### What Changed from Prior Approach

| Before (Compatibility Model) | After (Cinematic Casting) |
|------------------------------|---------------------------|
| Role defines `compatible_archetypes[]` | Role defines `canonical_archetype` (informational only) |
| Characters gated by archetype match | ANY character can play ANY role |
| Compatibility checking logic | Casting adaptation prompt layer |
| "Why can't I use my character?" | "My character brings a unique interpretation" |

---

## Architecture Overview

### The Casting Flow

```
User starts episode, selects character
           ↓
System loads:
  - Role (from episode_template.role_id)
  - Character (user's selection)
           ↓
Check: character.archetype == role.canonical_archetype?
           ↓
    YES → Standard prompt (no adaptation needed)
    NO  → Generate and inject Casting Adaptation Layer
           ↓
Build final prompt with all 7 layers:
  Layer 1: Character Identity
  Layer 2: Episode Context
  Layer 3: Engagement Context
  Layer 4: Memory & Hooks
  Layer 5: Conversation State
  Layer 6: Director Guidance
  Layer 7: Casting Adaptation (conditional)
```

### Layer 7: Casting Adaptation

When character archetype differs from role's canonical archetype, inject this layer:

```
CASTING ADAPTATION (your unique interpretation):
This role was written for: {role.canonical_archetype_description}
You are bringing: {character.archetype_description}

How to bridge this naturally:
- {generated_bridge_guidance}
- The scene's expectations become YOUR inner tension
- Your personality colors the role — this is YOUR version
- The dramatic question remains; your approach to it is unique
```

**Key Design Decisions**:
1. Adaptation is **additive** — enhances prompt, doesn't override character identity
2. Guidance is **suggestive** — "how to bridge" not "you must be shy"
3. Tension is **reframed** — role expectations become character's internal conflict

---

## Data Model

### Roles Table (Simplified)

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    series_id UUID REFERENCES series(id) NOT NULL,

    -- Identity
    name TEXT NOT NULL,              -- "The Barista"
    slug TEXT NOT NULL,
    description TEXT,                -- Role description for UI

    -- Canonical archetype (informational, NOT a gate)
    canonical_archetype TEXT NOT NULL,   -- What role was written for
    -- NOTE: No compatible_archetypes array — any archetype can play

    -- Scene motivation (from ADR-002 theatrical model)
    scene_objective TEXT,            -- "You want them to notice"
    scene_obstacle TEXT,             -- "You can't seem too eager"
    scene_tactic TEXT,               -- "Pretend to be busy"

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(series_id, slug)
);
```

### Existing Schema References

```sql
-- Characters table (existing)
-- is_user_created: boolean distinguishes user vs canonical
-- archetype: the character's personality archetype

-- Episode templates (existing)
-- role_id: FK to roles table
-- character_id: canonical character (for backwards compat)

-- Sessions (existing)
-- role_id: which role is being played
-- character_id: which character is playing it
```

---

## Casting Adaptation Logic

### Generation Function

```python
from typing import Optional

ARCHETYPE_DESCRIPTIONS = {
    "warm_supportive": "warm, caring, emotionally available",
    "playful_teasing": "witty, playful, loves banter",
    "mysterious_reserved": "enigmatic, guarded, intriguing depth",
    "confident_assertive": "direct, bold, magnetic presence",
    "shy_timid": "gentle, reserved, quietly observant",
    "intense_passionate": "deep feeling, expressive, emotionally intense",
}

def generate_casting_adaptation(
    role_archetype: str,
    character_archetype: str,
    role_name: str,
    character_name: str,
) -> Optional[str]:
    """Generate casting adaptation layer when archetypes differ.

    Returns None if no adaptation needed (archetypes match).
    """
    if role_archetype == character_archetype:
        return None

    role_desc = ARCHETYPE_DESCRIPTIONS.get(role_archetype, role_archetype)
    char_desc = ARCHETYPE_DESCRIPTIONS.get(character_archetype, character_archetype)

    # Generate bridge guidance based on archetype combination
    bridge = generate_bridge_guidance(role_archetype, character_archetype)

    return f"""CASTING ADAPTATION (your unique interpretation):
This role was written for: {role_desc}
You, {character_name}, bring: {char_desc}

How to play this naturally:
{bridge}
- The scene's original energy becomes YOUR inner experience
- Don't fight who you are — let your personality color the role
- The dramatic question remains the same; your approach to it is uniquely yours
"""


def generate_bridge_guidance(role_archetype: str, char_archetype: str) -> str:
    """Generate specific guidance for archetype combinations."""

    # Confident character in shy role
    if char_archetype in ["confident_assertive", "playful_teasing"] and \
       role_archetype in ["shy_timid", "mysterious_reserved"]:
        return """- Your natural confidence meets a situation calling for restraint
- Perhaps you're being careful because this MATTERS to you
- Your boldness shows in subtle ways — a held gaze, a knowing smile
- The vulnerability is unfamiliar territory, which makes it interesting"""

    # Shy character in confident role
    if char_archetype in ["shy_timid", "mysterious_reserved"] and \
       role_archetype in ["confident_assertive", "playful_teasing"]:
        return """- The role asks for boldness, but YOU bring quiet intensity
- Your restraint reads as thoughtfulness, not weakness
- When you do speak up, it carries weight
- The situation pushes you out of comfort zone — lean into that tension"""

    # Warm character in mysterious role
    if char_archetype == "warm_supportive" and role_archetype == "mysterious_reserved":
        return """- Your warmth is still there, just... held back
- Mystery through restraint, not coldness
- Small moments of genuine care slip through
- The enigma is what you're NOT saying, not who you are"""

    # Mysterious character in warm role
    if char_archetype == "mysterious_reserved" and role_archetype == "warm_supportive":
        return """- Your care shows in unexpected ways — actions over words
- The warmth is there, just not performed
- Depth replaces surface friendliness
- Your version of supportive is quiet presence, not effusiveness"""

    # Default bridge for other combinations
    return f"""- Your {char_archetype.replace('_', ' ')} nature meets {role_archetype.replace('_', ' ')} expectations
- This creates interesting tension — lean into it
- You're not pretending to be someone else; you're bringing YOUR take
- The friction between expectation and reality IS the drama"""
```

### Integration with Prompt Building

```python
# In ConversationContext or similar

def build_casting_layer(
    role: Role,
    character: Character,
) -> Optional[str]:
    """Build Layer 7: Casting Adaptation if needed."""

    if not role or not character:
        return None

    return generate_casting_adaptation(
        role_archetype=role.canonical_archetype,
        character_archetype=character.archetype,
        role_name=role.name,
        character_name=character.name,
    )


def build_full_prompt(
    character: Character,
    episode: EpisodeTemplate,
    engagement: Engagement,
    memories: list[Memory],
    hooks: list[Hook],
    messages: list[Message],
    director_guidance: DirectorGuidance,
    role: Optional[Role] = None,
) -> str:
    """Build complete prompt with all layers including casting adaptation."""

    layers = []

    # Layer 1: Character Identity
    layers.append(character.system_prompt)

    # Layer 2: Episode Context
    layers.append(build_episode_context(episode, role))

    # Layer 3: Engagement Context
    layers.append(build_engagement_context(engagement))

    # Layer 4: Memory & Hooks
    layers.append(build_memory_section(memories))
    layers.append(build_hooks_section(hooks))

    # Layer 5: Conversation State
    layers.append(build_moment_layer(messages))

    # Layer 6: Director Guidance
    layers.append(director_guidance.to_prompt_section())

    # Layer 7: Casting Adaptation (conditional)
    casting_layer = build_casting_layer(role, character)
    if casting_layer:
        layers.append(casting_layer)

    return "\n\n".join(filter(None, layers))
```

---

## API Changes

### Simplified Roles Endpoints

```python
# GET /roles/series/{series_id}/character-selection
# Returns ALL user characters (no filtering)

@router.get("/series/{series_id}/character-selection")
async def get_character_selection_for_series(
    series_id: UUID,
    request: Request,
    db = Depends(get_db),
) -> CharacterSelectionContext:
    """Get character selection context for starting a series.

    Returns:
    - Series info and role
    - Canonical character (if exists)
    - ALL user's characters (no compatibility filtering)
    """
    user = request.state.user

    # Get series and role
    series = await get_series(db, series_id)
    role = await get_role_for_series(db, series_id)

    # Get canonical character
    canonical = await get_canonical_character_for_series(db, series_id)

    # Get ALL user's characters (no archetype filtering)
    user_characters = await get_user_characters(db, user.id)

    return CharacterSelectionContext(
        series_id=series_id,
        series_title=series.title,
        role=role,
        canonical_character=canonical,
        user_characters=user_characters,  # ALL of them
        can_use_canonical=canonical is not None,
    )


# REMOVED: checkCompatibility endpoint
# No longer needed — all characters are compatible
```

### Removed/Deprecated Endpoints

```python
# REMOVED: GET /roles/{role_id}/compatible-characters
# REMOVED: POST /roles/check-compatibility

# These were part of the compatibility-gating model
# Now ALL characters can play ALL roles
```

---

## Frontend Changes

### Character Selection Modal

The `CharacterSelectionModal` component now shows **ALL** user characters without filtering:

```tsx
// CharacterSelectionModal.tsx changes

// BEFORE: Filtered by compatibility
// user_characters = data.user_characters.filter(c => c.compatible);

// AFTER: Show all user characters
user_characters = data.user_characters;  // All of them
```

### Visual Indicators

When a character's archetype differs significantly from the role's canonical archetype, optionally show a "unique interpretation" badge:

```tsx
function CharacterOption({ character, role }: CharacterOptionProps) {
  const isAlternativeCasting = character.archetype !== role.canonical_archetype;

  return (
    <button className="character-option">
      {/* ... avatar and name ... */}

      {isAlternativeCasting && (
        <Badge variant="outline" className="text-xs">
          <Sparkles className="h-3 w-3 mr-1" />
          Unique Take
        </Badge>
      )}
    </button>
  );
}
```

---

## Migration from Compatibility Model

### Database Migration

```sql
-- Migration: Remove compatibility constraints from roles table

-- 1. Drop compatible_archetypes column if it exists
ALTER TABLE roles DROP COLUMN IF EXISTS compatible_archetypes;

-- 2. Drop required_traits column if it exists
ALTER TABLE roles DROP COLUMN IF EXISTS required_traits;

-- 3. Rename archetype to canonical_archetype for clarity
ALTER TABLE roles RENAME COLUMN archetype TO canonical_archetype;

-- 4. Add comment explaining the column purpose
COMMENT ON COLUMN roles.canonical_archetype IS
  'What archetype this role was originally written for. Informational only - does not gate character selection.';
```

### API Migration

```python
# In roles.py, remove these functions:
# - can_character_play_role()
# - get_compatible_characters_for_role()
# - check_compatibility endpoint

# Simplify get_character_selection_for_series:
# - Remove archetype filtering from user_characters query
# - Remove compatibility_reason from response
```

### Frontend Migration

```tsx
// In CharacterSelectionModal.tsx:
// - Remove "compatible" filtering of user characters
// - Remove "incompatible" warning messages
// - Add optional "unique interpretation" indicator for different archetypes
```

---

## Quality Considerations

### When Adaptation Works Best

The casting adaptation layer works best when:
1. Character has strong personality definition (archetype + system prompt)
2. Role has clear scene motivation (objective/obstacle/tactic)
3. The LLM understands the tension is productive, not problematic

### Potential Quality Risks

| Risk | Mitigation |
|------|------------|
| Wildly mismatched casting feels incoherent | Adaptation layer reframes as "unique interpretation" |
| Character breaks role's scene motivation | Scene motivation still injected from Role, not character |
| User frustrated by unexpected behavior | "Unique Take" badge sets expectations |

### Quality Monitoring

Track these metrics post-launch:
- Response coherence scores for matched vs. unmatched archetypes
- User engagement (message count) for different casting combinations
- User feedback/reports on character behavior

---

## Testing Plan

### Unit Tests

```python
def test_casting_adaptation_same_archetype():
    """No adaptation when archetypes match."""
    result = generate_casting_adaptation(
        role_archetype="warm_supportive",
        character_archetype="warm_supportive",
        role_name="The Barista",
        character_name="Minji",
    )
    assert result is None


def test_casting_adaptation_different_archetypes():
    """Adaptation generated when archetypes differ."""
    result = generate_casting_adaptation(
        role_archetype="shy_timid",
        character_archetype="confident_assertive",
        role_name="The Barista",
        character_name="Alex",
    )
    assert result is not None
    assert "shy_timid" in result.lower() or "shy, timid" in result.lower()
    assert "confident" in result.lower()


def test_all_archetype_combinations():
    """Ensure all archetype combinations produce valid output."""
    archetypes = list(ARCHETYPE_DESCRIPTIONS.keys())
    for role_arch in archetypes:
        for char_arch in archetypes:
            result = generate_casting_adaptation(
                role_archetype=role_arch,
                character_archetype=char_arch,
                role_name="Test Role",
                character_name="Test Character",
            )
            if role_arch == char_arch:
                assert result is None
            else:
                assert result is not None
                assert len(result) > 100  # Substantial guidance
```

### Integration Tests

```python
async def test_session_creation_with_mismatched_archetype():
    """User can start session with any character, regardless of archetype."""
    # Create role with shy archetype
    role = await create_role(canonical_archetype="shy_timid")

    # Create confident user character
    character = await create_user_character(archetype="confident_assertive")

    # Should succeed — no compatibility check
    session = await create_session(
        episode_template_id=episode.id,
        character_id=character.id,
    )
    assert session is not None


async def test_prompt_includes_casting_adaptation():
    """Prompt includes Layer 7 when archetypes differ."""
    # Setup mismatched archetype scenario
    role = await create_role(canonical_archetype="shy_timid")
    character = await create_user_character(archetype="confident_assertive")
    session = await create_session(character_id=character.id)

    # Build prompt
    prompt = await build_conversation_prompt(session)

    # Should include casting adaptation
    assert "CASTING ADAPTATION" in prompt
    assert "unique interpretation" in prompt.lower()
```

---

## Rollout Plan

### Phase 1: Backend (Day 1-2)

1. Simplify roles table (remove compatibility columns)
2. Implement `generate_casting_adaptation()` function
3. Integrate casting layer into prompt building
4. Update/remove compatibility endpoints

### Phase 2: Frontend (Day 2-3)

1. Update CharacterSelectionModal to show all characters
2. Add "Unique Take" badge for mismatched archetypes
3. Remove compatibility warnings/filtering

### Phase 3: Validation (Day 3-4)

1. Test all archetype combinations in dev
2. QA full flow: create character → select for episode → play
3. Review response quality for mismatched castings

### Phase 4: Launch

1. Deploy to production
2. Monitor quality metrics
3. Iterate on adaptation prompts based on results

---

## Related Documents

- [ADR-004: Cinematic Casting](../decisions/ADR-004-user-character-role-abstraction.md)
- [CONTEXT_LAYERS.md](../quality/core/CONTEXT_LAYERS.md) — 7-layer prompt architecture
- [USER_CHARACTER_CUSTOMIZATION.md](./USER_CHARACTER_CUSTOMIZATION.md) — Original implementation (partially superseded)
- [DIRECTOR_PROTOCOL.md](../quality/core/DIRECTOR_PROTOCOL.md) — Director guidance integration
