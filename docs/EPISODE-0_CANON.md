# Episode-0 Platform Canon

> This document defines what Episode-0 is, regardless of genre, theme, or studio.
> Updated 2024-12-23 with architecture audit findings.

---

## 1. What Episode-0 Is (Platform Definition)

Episode-0 is a **chat-based episodic experience platform**.

It enables users to:

- enter **pre-authored narrative moments**
- interact in real time
- influence how scenes emotionally and narratively unfold

Episode-0 is not defined by romance, fantasy, or any single genre.

> Episode-0 is a system for turning moments into interactive stories.

**Characters** are containers.

**Episodes** are entry points.

**Chats** are live scenes.

---

## 2. The Episode-0 Thesis (Genre-Agnostic)

> People don't engage with characters. They engage with situations.

Across genres — romance, thriller, mystery, horror, slice-of-life, sci-fi — high engagement comes from:

- immediacy
- emotional stakes
- narrative implication
- being personally implicated in a moment

Episode-0's job is to **manufacture that moment instantly**.

---

## 3. Core Structural Primitive: Episodes

Episode-0 treats **episodes as first-class citizens**.

An episode is:

- a specific situation
- at a specific moment in time
- with something already in motion
- where the user matters *now*

This holds true whether the episode is:

- a romantic tension beat
- a mystery reveal
- a horror encounter
- a dramatic confrontation
- a cozy slice-of-life moment

> The platform is episode-first. Themes are layered on top.

---

## 4. Platform Content Standards (Universal)

Regardless of genre, every Episode-0 episode must pass:

### A. Instant Situational Clarity

Within seconds, the user understands:

- where they are
- what's happening
- why they're involved

### B. Narrative Tension

There is *something unresolved*:

- emotional
- informational
- relational
- situational

### C. User Implication

The moment would be different **without the user**.

### D. Reply Gravity

The opening demands response.

Silence feels like loss.

These standards apply to **all studios**, all themes.

---

## 5. Episode-0's Role vs. Studios

**Episode-0 (Platform)** provides:

- the episodic engine
- the conversation ignition system
- visual layering (background + avatar)
- memory and relationship tracking
- safety, moderation, tooling
- distribution and monetization

**Studios** provide:

- genre
- tone
- narrative rules
- creative constraints
- content-specific quality bars

> Episode-0 is the Netflix.
>
> Studios are the Netflix Originals teams.

---

## 6. Core Data Model (Genre-Agnostic)

The platform engine is built on generic primitives:

| Primitive | Purpose |
|-----------|---------|
| `Character` | Container for personality, voice, boundaries |
| `World` | Setting context (café, apartment, office, etc.) |
| `EpisodeTemplate` | Pre-authored scenario entry point |
| `Session` | User's conversation instance (runtime) |
| `Engagement` | User ↔ Character stats link (lightweight) |
| `MemoryEvent` | Extracted facts, events, preferences |
| `Hook` | Future engagement triggers |

> **Note (EP-01 Pivot):** Session replaced the runtime Episode concept. Engagement replaced Relationship
> and removed stage progression — connection depth is now implicit via memory accumulation and
> episode count rather than explicit stage labels.

These primitives power any genre. The theme is layered via studio configuration.

---

## 7. The 6-Layer Context Architecture

Per architecture audit (2024-12-23), context flows through 6 layers:

| Layer | Owner | Responsibility |
|-------|-------|----------------|
| **1. Character** | Character DNA | WHO they are: personality, voice, boundaries |
| **2. Episode** | EpisodeTemplate | WHERE/WHEN: physical setting, dramatic question |
| **3. Engagement** | Engagement record | HISTORY: total episodes, time since meeting |
| **4. Memory** | MemoryService | WHAT WE KNOW: extracted facts, preferences |
| **5. Conversation** | Message history | IMMEDIATE: last 20 messages in current session |
| **6. Director** | DirectorService | HOW TO PLAY: pacing, tension, genre doctrine |

### ADR-001: Genre Architecture Decision

**Genre belongs to Story (Series/Episode), not Character.**

- Characters define WHO someone is (personality, voice, boundaries)
- Genre defines WHAT KIND OF STORY they're in
- These are orthogonal concerns

Genre doctrine is now injected by Director at runtime, not baked into character system_prompt.

---

## 8. The Director Protocol v2.0

The Director is the "brain, eyes, ears, and hands" of the conversation system:

### Phase 1: Pre-Guidance (before character responds)

- **Pacing**: establish → develop → escalate → peak → resolve
- **Tension Note**: contextual direction for the actor
- **Physical Anchor**: ground in sensory reality
- **Genre Beat**: what this phase means for this genre

### Phase 2: Post-Evaluation (after character responds)

- **Visual Detection**: should we generate an image?
- **Completion Status**: is this episode ready to close?
- **Memory Extraction**: what should we remember?

---

## 9. Quality Gap Analysis (2024-12-23)

### What's Working

| Aspect | Evidence |
|--------|----------|
| Physical Grounding | "*She sets down your coffee but doesn't move. Her fingers are fidgeting.*" |
| Character Voice | Minji's ellipsis usage, hesitation, shyness match baseline_personality |
| Genre Separation | ADR-001 cleanly separates character identity from genre doctrine |
| Micro-Action Pattern | Responses lead with sensory beats before dialogue |

### The Core Problem: FLATNESS

**Structural correctness ≠ Emotional pull**

The architecture is sound, but conversations lack:

- **Magnetic tension** — the feeling that you WANT to keep talking
- **Stakes** — something must be won or lost in THIS moment
- **Subtext** — what's NOT being said matters more than what is
- **Character agency** — the character wants something FROM the user

### Root Cause Hypothesis

The system provides **data** but not **desire**.

Current prompt structure:
```
[Character DNA] — who I am
[Relationship Context] — how long we've known each other
[Episode Dynamics] — where we are, what's happening
[Director Guidance] — pacing phase, tension note
```

What's missing:
```
[Character Want] — what I want from YOU, right now, in this moment
[Stakes] — what happens if I don't get it
[Subtext] — what I'm afraid to say directly
```

The Director provides pacing guidance but not **character motivation**.

---

## 10. The Missing Layer: Character Want

### The Netflix Analogy

When you watch a great show, every scene has:
1. **What the character says** (dialogue)
2. **What the character does** (action)
3. **What the character WANTS** (motivation)
4. **What's at stake** (consequences)
5. **What they can't say** (subtext)

Episode-0 currently delivers 1 and 2 well. 3, 4, and 5 are implicit or absent.

### Proposed Enhancement: Want/Stakes/Subtext Injection

Director pre-guidance should include per-exchange motivation:

```
DIRECTOR NOTE: ROMANTIC TENSION

Pacing: DEVELOP
Ground in: warm café interior, afternoon sun

YOUR WANT (this moment):
You want them to notice you're lingering. You want them to give you a reason to stay.
If they don't, you'll have to leave—and you don't want to.

WHAT YOU CAN'T SAY:
You've memorized their order. You noticed when they changed laptops.
You can't say any of this out loud. Not yet.

STAKES:
If this goes well, you might actually talk like real people.
If this goes badly, you're just the barista again.
```

This transforms the character from **reactive** to **wanting**.

---

## 11. Architectural Recommendations

### Priority 1: Enhance Director Pre-Guidance

Add `character_want`, `stakes`, and `subtext` fields to `DirectorGuidance`:

```python
@dataclass
class DirectorGuidance:
    pacing: str = "develop"
    tension_note: Optional[str] = None
    physical_anchor: Optional[str] = None
    genre_beat: Optional[str] = None
    genre: str = "romantic_tension"
    energy_level: str = "playful"
    # NEW: Motivation layer
    character_want: Optional[str] = None  # What they want from user THIS moment
    stakes: Optional[str] = None          # What happens if they don't get it
    subtext: Optional[str] = None         # What they can't say directly
```

### Priority 2: Make Want Generation Contextual

Director should generate `character_want` based on:
- Episode situation (what's physically happening)
- Dramatic question (what's unresolved)
- Conversation state (what just happened)
- Character boundaries (how bold they can be)

### Priority 3: Reduce Prompt Verbosity

Current prompt has ~15 section headers. Consolidate to 4:

1. **IDENTITY** — who you are (character DNA)
2. **SCENE** — where you are (physical grounding + situation)
3. **DIRECTOR** — how to play this moment (pacing + want + stakes + subtext)
4. **MEMORY** — what you know about them

### Priority 4: Test the Pull

After implementing Want/Stakes/Subtext:
- A/B test conversation length
- Measure re-engagement within 24h
- Qualitative review: does it feel different?

---

## 12. North Star Metric

**Episodes Started per User per Week (ESPW)**

→ "How often do users engage with narrative moments?"

**Secondary Metrics:**

- Episode Completion Rate
- Return Rate (users coming back within 72h)
- Cross-character exploration
- Conversion to premium

**Quality Metric (new):**

- Average conversation length per episode
- User re-engagement with same character within 24h

---

## 13. Active Studios

### Studio 1: Romantic Tension
- Focus: desire, attraction, vulnerability, proximity
- See: `docs/character-philosophy/Genre 01 — Romantic Tension.md`

### Studio 2: Psychological Thriller
- Focus: suspense, paranoia, secrecy, moral pressure
- See: `docs/character-philosophy/Genre 02 — Psychological Thriller- Suspense.md`

### Future Studios (Planned)
- Cozy Slice-of-Life
- Mystery / Investigation
- Fantasy Adventure

Each studio follows Episode-0 platform rules while defining its own creative bar.

---

## 14. Key Strategic Takeaway

You are **not** building a romance app.

You are:

- **elevating Episode-0 above any single genre**
- while allowing genres to thrive *inside it*

This is the difference between:

- a category app
- and a **content platform**

---

## Related Documents

- `docs/character-philosophy/PHILOSOPHY.md` — Character design philosophy
- `docs/character-philosophy/Genre 01 — Romantic Tension.md` — Romance studio doctrine
- `docs/character-philosophy/Genre 02 — Psychological Thriller- Suspense.md` — Thriller studio doctrine
- `docs/decisions/ADR-001-genre-architecture.md` — Genre belongs to Story, not Character
- `docs/quality/core/DIRECTOR_PROTOCOL.md` — Director two-phase model
