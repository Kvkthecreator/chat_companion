# ADR-001: Genre Architecture

**Status**: On Hold
**Date**: 2024-12-23
**Deciders**: Product/Engineering

---

## Context

Genre currently exists at three independent levels in the architecture:

| Level | Field | Purpose |
|-------|-------|---------|
| Character | `character.genre` | Doctrine selection in `build_system_prompt()` |
| Episode | `episode_template.genre` | Director semantic evaluation context |
| Series | `series.genre` + `genre_settings` | Runtime prompt injection, override system |

This scatter is not a technical bug—it's **archaeological evidence of product exploration**.

---

## Decision History

### Phase 1: Romantic Tension Hypothesis

Initial product hypothesis: **Romantic tension = highest engagement = monetization**

- Genre was introduced at the character level to select "doctrine" (behavioral rules)
- `romantic_tension` and `psychological_thriller` were the two doctrines
- Character prompt builder (`build_system_prompt()`) uses genre to inject doctrine
- Heavy bias toward romantic cues, flirtation, affection baked into prompting DNA

### Phase 2: Content Expansion Attempt

Expanded architecture to support non-romantic content:

- Added genre at series level with `genre_settings` override system
- Added genre at episode level for Director evaluation context
- Goal: Enable sci-fi thriller, historical drama, etc.

### Phase 3: Stress Test Results

Dog-fooding attempts (sci-fi thriller, WW2 reenactment) revealed:

- Framework technically worked
- **Could not articulate the user value proposition** for non-romantic experiences
- Romantic bias in prompting made other genres feel "off"
- Question emerged: What makes interactive fiction valuable outside romance/companionship?

---

## Current State

The 3-level genre architecture is **intentionally preserved** because:

1. **Optionality**: Preserves ability to pivot if product direction clarifies
2. **Working romantic path**: Current architecture works well for romantic tension
3. **Premature to consolidate**: No clear answer to "what non-romantic experiences are we building?"

---

## Consequences

### Positive
- Flexibility to experiment with content types
- Romantic tension path is well-optimized
- No breaking changes needed if we pivot

### Negative
- Cognitive overhead for engineers (which genre wins?)
- Potential for inconsistency between levels
- Documentation burden

### Neutral
- Technical debt is contained (not blocking features)
- Can consolidate when product direction is clear

---

## Blocked By

This decision is blocked by a **product question**, not a technical one:

> "What user experiences beyond romantic AI companions are we building, and what makes them valuable?"

Possible answers that would unblock:
- "We're only doing romantic tension" → Consolidate to character level, remove series override
- "We're a content platform for many genres" → Consolidate to series level, character inherits
- "Different products need different genre handling" → Keep current architecture, document clearly

---

## Related Documents

- [CONTEXT_LAYERS.md](../quality/core/CONTEXT_LAYERS.md) - Genre Architecture section
- [GENRE_DOCTRINES in character.py](../../substrate-api/api/src/app/models/character.py) - Doctrine definitions
- [GenreSettings in series.py](../../substrate-api/api/src/app/models/series.py) - Override system

---

## Version History

| Date | Change |
|------|--------|
| 2024-12-23 | Initial ADR created during data model audit |
