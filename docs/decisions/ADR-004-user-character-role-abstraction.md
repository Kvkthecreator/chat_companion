# ADR-004: User Character & Cinematic Casting

> **Status**: ACCEPTED (Revised)
> **Date**: 2025-01-01
> **Revised**: 2025-01-01
> **Deciders**: Engineering
> **Related**: [ADR-001](./ADR-001-genre-architecture.md), [ADR-002](./ADR-002-theatrical-architecture.md)

---

## Context

Episode-0 wants to enable **user-created characters** that can play in platform-authored episodes. Currently, episode templates are tightly coupled to specific canonical characters — the `character_id` field directly references who appears in the episode.

To support user customization while preserving the quality of authored episodes, we need an architecture that:
1. Decouples episodes from specific characters
2. Allows **any** character (canonical or user-created) to play any role
3. Preserves scene motivation and dramatic tension through **prompt adaptation**

---

## Decision

### Part 1: The Cinematic Casting Model

Adopt a **cinematic casting** philosophy: any character can play any role, just as any actor can be cast in any film role. The system adapts to the casting choice rather than gatekeeping it.

```
Series/Episode → defines → Role (the part to be played)
                              ↓
                         "The barista in this café scene"
                              ↓
                    cast as → ANY Character (canonical OR user-created)
                              ↓
                    adapted via → Casting Adaptation Layer (prompt injection)
```

**Key Insight**: In cinema, a "shy barista" role written for one actor becomes something different when played by a confident actor — and that's not a bug, it's a feature. The same applies here:
- A shy archetype playing a confident role brings **unexpected vulnerability**
- A confident archetype playing a shy role brings **hidden depths**
- The narrative bends to the character, not the other way around

### Part 2: Role as Narrative Container (Not Gate)

**Role** represents the narrative container — the "part" in the script:
- The **scene motivation** (objective/obstacle/tactic) — what this part wants
- The **canonical archetype** — what the role was originally written for (informational only)
- The **situation and dramatic question** — the stage on which the character performs

**Role does NOT**:
- Gate which characters can play it
- Enforce archetype compatibility
- Restrict user choice

### Part 3: Casting Adaptation Layer

When a character's archetype differs from the role's canonical archetype, the **Casting Adaptation Layer** injects prompt guidance that bridges the gap:

```
CASTING ADAPTATION (when character differs from canonical role):
Role written for: shy, reserved barista
You are playing as: confident, bold personality

How to bridge this:
- Your natural confidence meets a situation that calls for vulnerability
- The scene's shyness expectations become YOUR inner tension
- You bring YOUR interpretation — confidence masking nervousness, boldness as overcompensation
- The dramatic question remains the same; your approach to it is uniquely yours
```

This layer is **additive** — it enhances the prompt when needed, but doesn't modify the core character identity or scene motivation.

### Part 4: Explicit Role Table

**Decision**: Create `roles` table with scene motivation, canonical archetype (for reference), but NO compatibility constraints.

**Schema**:
```sql
CREATE TABLE roles (
  id UUID PRIMARY KEY,
  series_id UUID REFERENCES series(id),
  name TEXT NOT NULL,                    -- "The Barista", "The Stranger"
  slug TEXT NOT NULL,
  description TEXT,                      -- Role description
  canonical_archetype TEXT NOT NULL,     -- What role was written for (informational)
  scene_objective TEXT,                  -- What this role wants
  scene_obstacle TEXT,                   -- What's stopping them
  scene_tactic TEXT,                     -- How they're playing it
  -- NO compatible_archetypes field
);
```

### Part 5: User Character Scope

User-created characters have **personality customization**:

| Exposed | Not Exposed |
|---------|-------------|
| Name | Backstory |
| Appearance (for avatar gen) | System prompt |
| Archetype (dropdown) | Genre |
| Flirting level | Scene motivation |

The system generates appropriate backstory and system prompt based on archetype selection. Scene motivation comes from the Role, not the character.

---

## The Casting Adaptation Flow

```
User selects character for episode
           ↓
System loads Role (scene motivation, canonical archetype)
           ↓
System loads Character (personality, archetype, voice)
           ↓
Character archetype == Role canonical archetype?
           ↓
    YES → Standard prompt (no adaptation needed)
    NO  → Inject Casting Adaptation Layer
           ↓
Build final prompt:
  Layer 1: Character Identity
  Layer 2: Episode Context
  Layer 3: Engagement Context
  Layer 4: Memory & Hooks
  Layer 5: Conversation State
  Layer 6: Director Guidance
  Layer 7: Casting Adaptation (if applicable)  ← NEW
```

---

## Consequences

### Positive

1. **Maximum user agency** — users can cast ANY of their characters in ANY episode
2. **Narrative richness** — unexpected castings create unique story possibilities
3. **Simplified architecture** — no compatibility logic to maintain
4. **Quality preserved** — scene motivation, genre doctrine, and dramatic tension remain platform-controlled
5. **User investment** — "MY character, MY interpretation of YOUR story"

### Negative

1. **Some castings may feel awkward** — a wildly mismatched character may strain the narrative
2. **Prompt complexity** — adaptation layer adds tokens and complexity
3. **Quality variance** — user choice introduces unpredictability

### Neutral

1. **Existing episodes unchanged** — canonical character remains available as "original casting"
2. **Memory scoping unchanged** — memories remain (user, character, series) scoped
3. **Episode authoring unchanged** — episodes still written for canonical archetype

---

## Alternatives Considered

### Alternative A: Archetype Compatibility Gating

Only allow characters with compatible archetypes to play a role.

**Rejected**: Limits user agency, requires maintaining compatibility rules, creates frustrating UX ("why can't I use my character?"). The cinematic casting model is more flexible and user-empowering.

### Alternative B: Full Character Replacement

User fully replaces canonical character — including backstory, system prompt, etc.

**Rejected**: Quality risk too high. User-authored backstory and system prompts would degrade episode coherence.

### Alternative C: Separate User Character Track

User characters exist in a parallel experience — free chat only, no authored episodes.

**Rejected**: Creates bifurcated product. Users either get premium authored experience OR degraded free-form.

### Alternative D: Character "Skins" Only

User customizes only visual appearance, not personality.

**Rejected**: Too limited for emotional investment. Users want "their" character, not just "their" face.

---

## Implementation Notes

See: [CINEMATIC_CASTING.md](../implementation/CINEMATIC_CASTING.md)

Key components:
- `roles` table with scene motivation (no compatibility constraints)
- `role_id` on `episode_templates` and `sessions`
- Casting Adaptation Layer in prompt building
- Character selection UI showing ALL user characters

---

## References

- [EPISODE-0_CANON.md](../EPISODE-0_CANON.md) — Platform philosophy
- [ADR-001: Genre Architecture](./ADR-001-genre-architecture.md) — Genre belongs to Story
- [ADR-002: Theatrical Architecture](./ADR-002-theatrical-architecture.md) — Scene motivation model
- [CONTEXT_LAYERS.md](../quality/core/CONTEXT_LAYERS.md) — 7-layer prompt architecture
