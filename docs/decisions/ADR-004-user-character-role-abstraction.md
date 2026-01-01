# ADR-004: User Characters & Role Abstraction

> **Status**: ACCEPTED
> **Date**: 2025-01-01
> **Deciders**: Engineering
> **Related**: [ADR-001](./ADR-001-genre-architecture.md), [ADR-002](./ADR-002-theatrical-architecture.md)

---

## Context

Episode-0 wants to enable **user-created characters** that can play in platform-authored episodes. Currently, episode templates are tightly coupled to specific canonical characters — the `character_id` field directly references who appears in the episode.

To support user customization while preserving the quality of authored episodes, we need an architecture that:
1. Decouples episodes from specific characters
2. Allows **any** character (canonical or user-created) to play any episode
3. Preserves scene motivation and dramatic tension

---

## Decision

### Core Principle: Any Character Can Play Any Episode

There is no compatibility gating. Any character the user creates can be assigned to any episode. The existing 6-layer context architecture naturally handles this:

- **Layer 1 (Character)**: Defines WHO — personality, voice, boundaries, archetype
- **Layer 2 (Episode)**: Defines WHAT/WHERE — situation, dramatic question, scene motivation

When these layers compose, the character naturally interprets the scene through their own personality. No special adaptation layer is needed.

### Role as Scene Motivation Container

**Role** exists to enable scene motivation reuse across episodes:

```sql
CREATE TABLE roles (
  id UUID PRIMARY KEY,
  series_id UUID REFERENCES series(id),
  name TEXT NOT NULL,                    -- "The Barista", "The Stranger"
  slug TEXT NOT NULL,
  description TEXT,                      -- Role description for UI
  scene_objective TEXT,                  -- What this role wants
  scene_obstacle TEXT,                   -- What's stopping them
  scene_tactic TEXT                      -- How they're playing it
);
```

**Role provides**:
- Scene motivation (objective/obstacle/tactic) that can be shared across episodes
- A name and description for the UI

**Role does NOT provide**:
- Archetype constraints
- Compatibility gating
- Special adaptation logic

### User Character Scope

User-created characters have **limited customization**:

| User Controls | Platform Controls |
|---------------|-------------------|
| Name | Backstory |
| Appearance (for avatar gen) | System prompt |
| Archetype (dropdown) | Genre doctrine |
| Flirting level | Scene motivation (from Role/Episode) |

The system generates appropriate backstory and system prompt based on archetype selection. Scene motivation comes from the Episode/Role, not the character.

### Data Model

```
EpisodeTemplate
  ├── character_id → canonical/default character
  ├── role_id (optional) → for scene motivation reuse
  ├── situation, dramatic_question, etc.
  └── scene_objective, scene_obstacle, scene_tactic (can be on episode directly)

Session
  ├── episode_template_id → which episode
  └── character_id → who's actually playing (may differ from canonical)

Role (optional)
  └── scene_objective, scene_obstacle, scene_tactic (reusable across episodes)
```

---

## Consequences

### Positive

1. **Maximum user agency** — users can play ANY of their characters in ANY episode
2. **Simple architecture** — no compatibility logic, no adaptation layers
3. **Quality preserved** — scene motivation, genre doctrine remain platform-controlled
4. **Natural interpretation** — Character + Episode compose naturally without special handling
5. **User investment** — "MY character in YOUR compelling situation"

### Negative

1. **Some castings may feel unexpected** — a character's archetype may contrast with the scene
2. **Quality variance** — user choice introduces unpredictability

### Neutral

1. **Existing episodes unchanged** — canonical character remains as "default"
2. **Memory scoping unchanged** — memories remain (user, character, series) scoped
3. **Episode authoring unchanged** — episodes still written for canonical character

---

## Alternatives Considered

### Alternative A: Archetype Compatibility Gating

Only allow characters with compatible archetypes to play episodes.

**Rejected**: Limits user agency, requires maintaining compatibility rules, creates frustrating UX ("why can't I use my character?").

### Alternative B: Casting Adaptation Layer

Add special prompt injection when character archetype differs from "expected" archetype.

**Rejected**: Over-engineering. The existing Character + Episode composition already handles this naturally. Characters interpret scenes through their personality — no bridge needed.

### Alternative C: Full Character Replacement

User fully replaces canonical character — including backstory, system prompt, etc.

**Rejected**: Quality risk too high. User-authored backstory and system prompts would degrade episode coherence.

---

## References

- [EPISODE-0_CANON.md](../EPISODE-0_CANON.md) — Platform philosophy
- [ADR-001: Genre Architecture](./ADR-001-genre-architecture.md) — Genre belongs to Story
- [ADR-002: Theatrical Architecture](./ADR-002-theatrical-architecture.md) — Scene motivation model
- [CONTEXT_LAYERS.md](../quality/core/CONTEXT_LAYERS.md) — 6-layer prompt architecture
