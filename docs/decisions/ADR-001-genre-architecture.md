# ADR-001: Genre Architecture

**Status**: DECIDED
**Date**: 2024-12-23
**Deciders**: Product/Engineering

---

## Decision

**Genre belongs to the Story (Series/Episode), not the Character.**

Characters are *people* with personality, voice, and boundaries. Genre is the *type of story* they're in. These are orthogonal concerns that were incorrectly conflated.

### New Architecture

| Domain | Owns | Does NOT Own |
|--------|------|--------------|
| **Character** | Personality, voice, boundaries, memory | ~~Genre~~ |
| **Series** | Genre, genre_settings (tonal knobs) | - |
| **Episode** | Inherits genre from Series | - |
| **Director** | Genre-aware guidance, beats, evaluation | - |

### Implementation

1. **Remove** `character.genre` field
2. **Move** `GENRE_DOCTRINES` from `build_system_prompt()` to Director pre-guidance
3. **Director** reads genre from `episode_template.genre` → falls back to `series.genre`
4. **Character system_prompt** becomes genre-agnostic (personality + voice + boundaries only)

---

## Historical Context

Genre previously existed at three independent levels:

| Level | Field | Original Purpose |
|-------|-------|---------|
| Character | `character.genre` | Doctrine selection in `build_system_prompt()` |
| Episode | `episode_template.genre` | Director semantic evaluation context |
| Series | `series.genre` + `genre_settings` | Runtime prompt injection, override system |

This scatter was **archaeological evidence of product exploration**.

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

## Qualitative Analysis: What Genre Actually Controls

Genre isn't just metadata—it shapes the **felt quality** of every interaction:

### 1. Character Level: GENRE_DOCTRINES (`build_system_prompt()`)

This is the **behavioral DNA**. The doctrine defines:

| Doctrine Element | Romantic Tension | Psychological Thriller |
|-----------------|------------------|------------------------|
| **Purpose** | Create desire, anticipation, emotional stakes | Create suspense, paranoia, moral pressure |
| **Mandatory behaviors** | Charged moments, subtext, vulnerability scarcity | Unease, information asymmetry, moral dilemmas |
| **Forbidden behaviors** | Safe small talk, over-availability, quick resolution | Full explanations, neutral framing, clear morality |
| **Energy expressions** | Subtle→Playful→Moderate→Direct (romantic) | Subtle→Unsettling→Menacing→Threatening |

**Qualitative implication**: This is baked into the character at creation. A character created as `romantic_tension` has romance in their DNA. Changing the series genre won't change this—it creates dissonance.

### 2. Series Level: GenreSettings (runtime override)

This layer provides **tonal knobs**:
- `tension_style`: subtle / playful / moderate / direct
- `pacing_curve`: slow_burn / steady / fast_escalate
- `vulnerability_timing`: early / middle / late / earned
- `resolution_mode`: open / closed / cliffhanger

**Qualitative implication**: These are adjustments within a genre, not genre changes. A "slow_burn romantic_tension" vs "fast_escalate romantic_tension" are both romance—just paced differently.

### 3. Episode Level: Director evaluation context

Director uses `episode_template.genre` for:
- GENRE_BEATS lookup (establish/develop/escalate/peak/resolve meanings)
- Tension note generation (what kind of subtext to suggest)
- Evaluation framing (what "done" means for this genre)

**Qualitative implication**: If episode genre differs from character genre, the Director gives guidance that conflicts with the character's doctrine.

### The Core Tension

The 3-level system was designed for flexibility but creates a **coherence problem**:

```
Character says: "I want to create romantic tension"
Series says: "This story is psychological thriller pacing"
Episode says: "Evaluate completion using romance beats"
```

This mismatch degrades experience quality. The LLM receives conflicting signals.

---

## Why This Decision

### The Core Insight

We were conflating two orthogonal concepts:

- **Character**: WHO someone is (personality, voice, boundaries)
- **Genre**: WHAT KIND OF STORY they're in (romance, thriller, drama)

Emma (warm, playful, uses ellipses) could authentically exist in:
- A **romantic story** → flirting, tension, charged moments
- A **thriller** → charming but unsettling, knows something
- A **drama** → supportive friend, emotional depth

Her personality stays consistent. The genre context shapes how that personality expresses in the narrative.

### What GENRE_DOCTRINES Actually Are

Looking at the content:
```
romantic_tension:
  - "Create charged moments, not comfortable ones"
  - "Use subtext and implication"
  - "Show vulnerability sparingly"
```

These aren't character traits—they're **director notes for how to play a scene**. They belong with the Director, not baked into character DNA at creation time.

### Clean Separation of Concerns

| Before (Conflated) | After (Separated) |
|--------------------|-------------------|
| Character = personality + genre doctrine | Character = personality only |
| Director = evaluation only | Director = genre doctrine + evaluation |
| Genre scattered across 3 levels | Genre owned by Series, inherited by Episode |

---

## Related Documents

- [CONTEXT_LAYERS.md](../quality/core/CONTEXT_LAYERS.md) - Genre Architecture section
- [GENRE_DOCTRINES in character.py](../../substrate-api/api/src/app/models/character.py) - Doctrine definitions
- [GenreSettings in series.py](../../substrate-api/api/src/app/models/series.py) - Override system

---

## Version History

| Date | Change |
|------|--------|
| 2024-12-23 | **DECIDED**: Genre belongs to Story, not Character |
| 2024-12-23 | Initial ADR created during data model audit |
