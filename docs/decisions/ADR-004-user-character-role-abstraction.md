# ADR-004: User Character & Role Abstraction

> **Status**: ACCEPTED
> **Date**: 2025-01-01
> **Deciders**: Engineering
> **Related**: [ADR-001](./ADR-001-genre-architecture.md), [ADR-002](./ADR-002-theatrical-architecture.md)

---

## Context

Episode-0 wants to enable **user-created characters** that can play in platform-authored episodes. Currently, episode templates are tightly coupled to specific canonical characters — the `character_id` field directly references who appears in the episode.

To support user customization while preserving the quality of authored episodes, we need an architecture that:
1. Decouples episodes from specific characters
2. Allows any compatible character (canonical or user-created) to fill a role
3. Preserves scene motivation and dramatic tension (the "authored" quality)

---

## Decision

### Part 1: Role as Episode-Character Bridge

Introduce **Role** as a conceptual abstraction that defines the archetype slot an episode requires. A role can be filled by any compatible character.

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
- The **scene motivation** (objective/obstacle/tactic) — lives with the role, not the character

### Part 2: Explicit Role Table

**Decision**: Create `roles` table upfront (not deferred).

**Rationale**:
- The conceptual work is done — Role is a real abstraction
- Schema is simple (< 10 fields)
- Avoids "implicit magic" where role is inferred from canonical character
- Makes the architecture explicit and queryable
- Scene motivation moves to its proper home (Role owns the "director's notes")
- Lower migration cost now vs. retrofitting later

**Implementation**:
- Create `roles` table with archetype, compatibility constraints, scene motivation
- Add `role_id` to `episode_templates` and `sessions`
- Existing episodes can have NULL `role_id` — implicit role derived from canonical character
- New episodes should use explicit roles

### Part 3: User Character Scope

User-created characters have **limited customization**:

| Exposed | Not Exposed |
|---------|-------------|
| Name | Backstory |
| Appearance (for avatar gen) | System prompt |
| Archetype (dropdown) | Genre |
| Flirting level | Scene motivation |

Genre doctrine and scene motivation remain platform-controlled, preserving authored quality.

---

## Consequences

### Positive

1. **Authored episodes remain high quality** — dramatic tension, scene motivation, and genre doctrine are platform-controlled
2. **User emotional investment increases** — "MY character in YOUR compelling situation"
3. **Clean separation of concerns** — character is WHO, role is WHAT THEY DO in this scene
4. **Downstream-ready** — Phase 2 (user-created episodes) and Phase 3 (shareable characters) become natural extensions

### Negative

1. **Episode authoring changes** — new episodes should be written role-generically where possible
2. **Complexity for content creators** — must think about role compatibility, not just specific characters
3. **Implicit roles are less flexible** — Phase 1 limits customization to archetype-matching

### Neutral

1. **Existing episodes unchanged** — canonical character remains the default; user characters are additive
2. **Memory scoping unchanged** — memories remain (user, character, series) scoped

---

## Alternatives Considered

### Alternative A: Full Character Replacement

User fully replaces canonical character — including backstory, system prompt, etc.

**Rejected**: Quality risk too high. User-authored backstory and system prompts would degrade episode coherence.

### Alternative B: Separate User Character Track

User characters exist in a parallel experience — free chat only, no authored episodes.

**Rejected**: Creates bifurcated product. Users either get premium authored experience OR degraded free-form. Harder to monetize, muddies value proposition.

### Alternative C: Character "Skins" Only

User customizes only visual appearance, not personality.

**Rejected**: Too limited for emotional investment. Users want "their" character, not just "their" face on platform character.

---

## Implementation Notes

See: [USER_CHARACTER_CUSTOMIZATION.md](../implementation/USER_CHARACTER_CUSTOMIZATION.md)

Key schema changes:
- Add `is_user_created`, `is_public` to `characters` table
- Phase 1: No new tables, role is implicit
- Phase 2: Add `roles` table, `role_id` to `episode_templates` and `sessions`

---

## References

- [EPISODE-0_CANON.md](../EPISODE-0_CANON.md) — Platform philosophy
- [ADR-001: Genre Architecture](./ADR-001-genre-architecture.md) — Genre belongs to Story
- [ADR-002: Theatrical Architecture](./ADR-002-theatrical-architecture.md) — Scene motivation model
