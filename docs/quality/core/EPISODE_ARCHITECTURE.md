# Episode Architecture: Principles of Interactive Narrative

> **Status**: Reference Pattern (not mandatory, but proven effective)
> **Applies to**: Episode/series scaffolding, prop design, pacing decisions

## Part I: First Principles

Before examining specific patterns, we establish the axiomatic elements that make interactive fiction work. These principles hold regardless of genre, setting, or implementation.

### The Fundamental Problem

Interactive fiction occupies an unstable position between two failure modes:

| Mode | Problem | User Experience |
|------|---------|-----------------|
| **Too open** | No narrative gravity | Wandering, boredom, "what am I supposed to do?" |
| **Too closed** | No meaningful agency | Reading, not playing, "why am I here?" |

The goal is **constrained agency**: the user feels free while the narrative maintains coherent momentum.

### Axiom 1: Tension Requires Constraint

> *Infinite possibility produces zero stakes.*

Tension arises from limitation. A character who can leave anytime has no reason to stay. A mystery that can be ignored isn't urgent. A relationship with no obstacles requires no effort.

**Implication**: Every episode needs a constraint that makes the interaction non-optional. The constraint can be:
- Physical (locked in, stranded, trapped)
- Temporal (deadline, ticking clock, limited window)
- Social (can't walk away without consequence)
- Psychological (compulsion, obsession, need to know)

### Axiom 2: Agency Requires Legibility

> *Choice without understanding is noise.*

For user input to feel meaningful, they must understand:
1. What they're trying to achieve (stakes)
2. What options are available (possibility space)
3. How the world responds (feedback)

**Implication**: Stakes must be implicit in the situation, not explained. "You're trapped in a facility with someone who might be lying" is legible. "Your goal is to build trust while uncovering secrets" is instruction.

### Axiom 3: Progression Requires Anchors

> *Abstract narrative beats don't stick. Objects do.*

LLMs struggle to maintain consistent facts across long conversations. Users struggle to feel progress in pure dialogue. Physical objects solve both problems:
- They're concrete (easier to track than "relationship deepened")
- They're discoverable (creates moments of revelation)
- They're collectible (gamifies the experience)
- They're referenceable (character can return to them)

**Implication**: Every significant narrative beat should have a tangible anchor—a prop, artifact, or discoverable element that externalizes the abstract.

### Axiom 4: Pacing Requires Structure

> *LLMs can't pace themselves. Designers must.*

Left unconstrained, an LLM will:
- Reveal too much too quickly
- Escalate without earning it
- Forget to breathe between beats
- Miss the resolution entirely

**Implication**: Pacing must be externally enforced through turn budgets, reveal hints, and gated progression. The LLM provides texture; the system provides structure.

### Axiom 5: Interaction Requires Mutual Need

> *One-sided dependency kills chemistry.*

If only one party needs the other, the interaction becomes transactional. Compelling dynamics require mutual stakes:
- Both need something from the other
- Both are vulnerable to the other
- Both are changed by the encounter

**Implication**: Design situations where both character and player are invested. The player wants answers; the character needs an ally. The player is intrigued; the character is lonely. Symmetry creates tension.

---

## Part II: The Escape Room Pattern

The "escape room" is a concrete instantiation of these axioms. It works because it naturally satisfies all five principles. When this metaphor stops serving, return to the axioms above.

### Pattern Definition

| Element | Axiom Served | Description |
|---------|--------------|-------------|
| **Bounded space** | Constraint (#1) | Physical or situational limit that makes interaction non-optional |
| **Clear stakes** | Legibility (#2) | Obvious goal without explicit instruction |
| **Gated progression** | Anchors (#3) + Pacing (#4) | Props unlock at designed intervals |
| **Forced interaction** | Mutual Need (#5) | Both parties require each other |

### Why It Works

**Psychologically:**
1. Stakes without instructions—you know what you need (escape/solve) without being told what to say
2. Props as progress markers—physical objects anchor abstract narrative beats
3. Constraint creates intimacy—"trapped together" forces vulnerability naturally
4. Discovery pacing—turn hints gate reveals, story breathes at designed intervals

**Technically:**
1. Automatic reveal mode—props fire at exact turns via Director (no LLM judgment needed)
2. Predictable session length—turn budget creates natural episode boundaries
3. Designable, not just writable—structure carries content; quality more consistent
4. Collectible layer—props become game-like inventory items

### Genre Adaptation

The skeleton remains constant; the emotional texture changes:

| Element | Thriller | Romance | Mystery |
|---------|----------|---------|---------|
| Bounded space | Underground facility | Stuck in elevator | Investigation window |
| Stakes | Escape alive | Emotional connection | Find the truth |
| Progression gate | Access keycards | Shared vulnerabilities | Clues/evidence |
| Forced interaction | Survival requires cooperation | Can't avoid each other | Must engage to solve |

### Examples in Codebase

**The Blacksite** (survival_thriller):
- Bounded: Underground research facility
- Stakes: Escape before they find you
- Props: Subject tag → Keycard → Facility map → Override code
- Forced: Alex is your only ally; you need each other

**Locked In** (forced_proximity):
- Bounded: Elevator → Cabin → Escape room
- Stakes: Stuck together, tension building
- Props: Dying phone → Shared blanket → Booking confirmation
- Forced: Literally cannot leave; must interact

---

## Part III: Implementation Details

### Prop Design Principles

**1. Two Props Per Episode**
Consistent pacing. One early (establish), one mid-to-late (escalate or reveal).

**2. Staggered Turn Hints**
```
Episode 0: turns 0, 3
Episode 1: turns 2, 5
Episode 2: turns 4, 8
Episode 3: turns 2, 6
```
Creates rhythm without predictability.

**3. Automatic Reveal Mode**
For thriller/mystery genres, use `reveal_mode: automatic`. Director fires props at exact turn—no reliance on LLM to weave keywords.

For romance, `character_initiated` can work if prop guidelines encourage natural mention.

**4. Props Should Feel Discovered**
Good: "She notices your wristband for the first time. 'A-7749. That's... that's a subject number.'"
Bad: "Here is a wristband with the number A-7749."

### Episode Arc Structure

Standard 4-episode arc with escalating stakes:

| Episode | Pacing Phase | Tension | Props Role |
|---------|--------------|---------|------------|
| 0 | Establish | Low → Medium | Introduce world, first mystery |
| 1 | Develop | Medium | Deepen relationship, complicate situation |
| 2 | Escalate | Medium → High | Stakes rise, trust tested |
| 3 | Peak/Resolve | High → Resolution | Truth revealed, choice made |

### Implementation Checklist

When scaffolding a new series:

- [ ] Define the constraint (what makes interaction non-optional?)
- [ ] Identify the stakes (what do they want/fear?)
- [ ] Establish mutual need (why do both parties engage?)
- [ ] Design 2 props per episode with turn hints
- [ ] Set reveal_mode to `automatic` for reliability
- [ ] Write situation that establishes constraint immediately
- [ ] Ensure dramatic_question creates tension, not just curiosity
- [ ] Map props to narrative beats (discovery, complication, revelation)

### Anti-Patterns

| Anti-Pattern | Axiom Violated | Why It Fails |
|--------------|----------------|--------------|
| No constraint on exit | #1 Constraint | Zero stakes if they can just leave |
| Explicit goal instructions | #2 Legibility | Breaks immersion, feels like tutorial |
| Props without turn hints | #4 Pacing | When do they appear? LLM can't decide |
| More than 3 props per episode | #3 Anchors | Diluted impact, cluttered |
| `player_requested` for key reveals | #4 Pacing | Player may never ask |
| One-sided dependency | #5 Mutual Need | Transactional, not compelling |

---

## Part IV: Beyond Escape Rooms

When the escape room metaphor doesn't fit, derive alternatives from the axioms:

### Alternative Constraint Mechanisms

| Mechanism | How It Works | Genre Fit |
|-----------|--------------|-----------|
| **Temporal deadline** | Event occurs in X turns regardless | Heist, disaster |
| **Social obligation** | Walking away has consequences | Drama, workplace |
| **Psychological compulsion** | Character can't let go | Obsession, addiction |
| **Mystery hook** | Need to know outweighs discomfort | Investigation, thriller |
| **Shared secret** | Bound by mutual knowledge | Conspiracy, affair |

### Alternative Anchor Types

| Anchor | How It Works | When to Use |
|--------|--------------|-------------|
| **Physical props** | Tangible objects discovered | Default, works everywhere |
| **Revelations** | Information that changes understanding | Mystery, drama |
| **Commitments** | Promises/decisions that bind | Romance, moral choice |
| **Transformations** | Visible change in character | Character study |
| **Rituals** | Repeated actions that gain meaning | Relationship, habit |

### Alternative Mutual Need Structures

| Structure | Player Needs | Character Needs |
|-----------|--------------|-----------------|
| **Alliance** | Capability/knowledge | Ally/validation |
| **Confession** | Truth | Absolution/understanding |
| **Challenge** | Proof of self | Worthy opponent |
| **Rescue** | Help | To be needed |
| **Seduction** | Connection | To be wanted |

---

## Relationship to Other Docs

- **DIRECTOR_PROTOCOL.md**: How Director uses genre doctrines and turn hints
- **EPISODE_STATUS_MODEL.md**: How turn budgets create session boundaries
- **CONTEXT_LAYERS.md**: How props feed into character context

---

*This document captures learnings from The Blacksite, Locked In, Blackout, and The Last Message series development. The escape room pattern emerged organically; the axioms were derived by analyzing why it worked.*
