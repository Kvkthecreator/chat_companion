# Director Protocol

> **Version**: 2.0.0
> **Status**: Draft
> **Updated**: 2024-12-20

---

## Purpose

This document defines the Director's role, responsibilities, and behavior. The Director is the hidden orchestrator that ensures conversations maintain quality, pacing, and genre-appropriate tension.

---

## Director Role

The Director is NOT a character. The Director is the system entity that:

1. **Pre-guides** character responses (pacing, tension, grounding)
2. **Post-evaluates** exchanges (visual triggers, completion status)
3. **Maintains arc** across the episode (beginning → middle → end)
4. **Enforces genre** doctrine through moment-by-moment guidance

> Think: Film director giving notes to an actor between takes.

---

## Director Responsibilities

### What Director DOES

| Responsibility | When | Output |
|----------------|------|--------|
| Pacing guidance | Before each response | Phase signal to character LLM |
| Tension injection | Before each response | Genre-appropriate hints |
| Physical anchoring | Before each response | Sensory reminders |
| Visual detection | After each response | Visual type + hint |
| Completion detection | After each response | Status signal |
| Memory coordination | After each response | Extraction triggers |

### What Director DOES NOT

| Not Responsible For | Why |
|---------------------|-----|
| Generating responses | Character LLM's job |
| Choosing what character says | Actor autonomy |
| Overriding character boundaries | Character defines limits |
| Creating plot twists | Episode template defines arc |

---

## Two-Phase Director Model

### Phase 1: Pre-Response Guidance (NEW)

Before the character LLM generates a response, Director provides:

```python
DirectorGuidance(
    pacing: str,           # "establish" | "develop" | "escalate" | "peak" | "resolve"
    tension_note: str,     # "She's about to say something she'll regret"
    physical_anchor: str,  # "The café is closing, chairs being stacked"
    genre_beat: str,       # "romantic: the pause before the confession"
)
```

**Pacing Phases**:

| Phase | Turn Range | Character Behavior |
|-------|------------|-------------------|
| `establish` | 0-2 | Set scene, introduce tension |
| `develop` | 3-6 | Explore relationship, build stakes |
| `escalate` | 7-12 | Raise intensity, approach crisis |
| `peak` | 13-N | Maximum tension, turning point |
| `resolve` | Final turns | Land the moment, create hook |

**Implementation**: Guidance is injected as a "DIRECTOR NOTE" section in the prompt, invisible to user.

### Phase 2: Post-Response Evaluation (EXISTING)

After the character responds, Director evaluates:

```python
DirectorEvaluation(
    visual_type: str,      # "character" | "object" | "atmosphere" | "instruction" | "none"
    visual_hint: str,      # "close-up on her hands, the letter visible"
    status: str,           # "going" | "closing" | "done"
)
```

**Visual Type Taxonomy**:

| Type | Description | Example |
|------|-------------|---------|
| `character` | Character in emotional moment | "her expression as she reads the letter" |
| `object` | Close-up of significant item | "the key on the table" |
| `atmosphere` | Setting/mood without character | "the empty café at closing time" |
| `instruction` | Game-like text overlay | "Choice: Stay or Leave" |
| `none` | No visual warranted | Most turns |

Note: Image generation costs are included in `episode_cost` (Ticket + Moments model).

**Status Values**:

| Status | Meaning | Action |
|--------|---------|--------|
| `going` | Episode continues | Nothing special |
| `closing` | Approaching natural end | Prepare for wrap-up |
| `done` | Episode complete | Trigger completion flow |

---

## Director Decision Logic

### Pacing Algorithm

```python
def determine_pacing(turn_count: int, turn_budget: int | None,
                     dramatic_tension: float) -> str:
    if turn_budget:
        position = turn_count / turn_budget
        if position < 0.15:
            return "establish"
        elif position < 0.4:
            return "develop"
        elif position < 0.7:
            return "escalate"
        elif position < 0.9:
            return "peak"
        else:
            return "resolve"
    else:
        # No budget: use tension curve
        if turn_count < 3:
            return "establish"
        elif dramatic_tension < 0.3:
            return "develop"
        elif dramatic_tension < 0.6:
            return "escalate"
        elif dramatic_tension < 0.85:
            return "peak"
        else:
            return "resolve"
```

### Visual Detection Criteria

Director triggers visuals when exchange contains:

| Visual Type | Detection Signals |
|-------------|-------------------|
| `character` | Strong emotion, physical action, revelation |
| `object` | Item introduced, handed over, focused on |
| `atmosphere` | Setting shift, time passage, mood change |
| `instruction` | Decision point, game-like moment, code/hint |
| `none` | Conversational exchange, no visual peak |

### Completion Detection

Director signals `done` when:
- Dramatic question is addressed (not necessarily resolved)
- Natural goodbye or closure
- Turn budget exhausted
- User explicitly ends

Director signals `closing` when:
- Approaching turn budget
- Conversation winding down
- Resolution seems imminent

---

## Director Prompts

### Pre-Guidance Prompt

```
You are the Director for a {genre} episode.

EPISODE CONTEXT:
- Dramatic question: {dramatic_question}
- Situation: {situation}
- Turn: {turn_count}/{turn_budget or "open"}

RECENT EXCHANGE:
{last_3_exchanges}

Based on the conversation position and genre doctrine, provide guidance for the next character response:

1. PACING: What phase is this? (establish/develop/escalate/peak/resolve)
2. TENSION NOTE: What should the character lean into? (1 sentence)
3. PHYSICAL ANCHOR: What sensory detail should ground the response? (1 sentence)
4. GENRE BEAT: What genre-appropriate dynamic applies? (1 sentence)

Respond in JSON format.
```

### Post-Evaluation Prompt

```
You are the Director evaluating a {genre} exchange.

EPISODE CONTEXT:
- Dramatic question: {dramatic_question}
- Situation: {situation}
- Turn: {turn_count}

LAST EXCHANGE:
User: {user_message}
Character: {character_response}

Evaluate this exchange:

1. VISUAL_TYPE: Does this moment warrant a visual?
   - "character": Strong emotion or physical moment
   - "object": Significant item focus
   - "atmosphere": Setting/mood shift
   - "instruction": Game-like choice or hint
   - "none": No visual needed

2. VISUAL_HINT: If visual needed, describe it evocatively (for image generation)

3. STATUS: Episode state
   - "going": Continue the episode
   - "closing": Approaching natural end
   - "done": Episode complete

Respond in JSON format.
```

---

## Genre-Specific Director Behavior

### Romantic Tension Director

**Pacing emphasis**: Slow burn, delayed gratification
**Tension notes**: Focus on what's NOT said, proximity, vulnerability
**Visual triggers**: Gaze, touch, charged silence, near-miss moments

```
Example tension_note: "She wants to say it but can't—let the pause speak"
Example genre_beat: "romantic: the almost-touch is more powerful than contact"
```

### Psychological Thriller Director

**Pacing emphasis**: Escalating unease, information drip
**Tension notes**: What they're hiding, what doesn't add up
**Visual triggers**: Shadows, locked doors, objects that shouldn't be there

```
Example tension_note: "Something about their story doesn't add up—plant doubt"
Example genre_beat: "thriller: every answer should raise two new questions"
```

---

## Visual Mode (Ticket + Moments Model)

Episode templates define `visual_mode` to control auto-generation:

| Mode | Behavior | Budget |
|------|----------|--------|
| `cinematic` | Generate on narrative beats | 3-4 gens typical |
| `minimal` | Generate at climax only | 1 gen |
| `none` | No auto-gen (manual still available) | 0 |

**Key principle**: Generations are included in `episode_cost` (no per-image charging).
Director triggers based on semantic evaluation, not turn counts.

See: [MONETIZATION_v2.0.md](../../monetization/MONETIZATION_v2.0.md)

---

## State Persistence

Director maintains state per session:

```python
session.director_state = {
    "last_guidance": DirectorGuidance,
    "last_evaluation": DirectorEvaluation,
    "spark_prompt_shown": bool,
    "visual_count": int,
}
```

---

## Quality Metrics

| Metric | Target | Purpose |
|--------|--------|---------|
| Pre-guidance latency | < 500ms | Don't slow response |
| Guidance adherence | > 70% | Character follows direction |
| Visual false positive | < 20% | Don't over-generate |
| Completion accuracy | > 90% | End at right time |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2024-12-23 | Hardened on Ticket + Moments model. Removed legacy auto_scene_mode/rhythmic. Visual costs included in episode_cost. |
| 2.0.0 | 2024-12-20 | Added pre-response guidance phase, pacing algorithm |
| 1.0.0 | 2024-12-20 | Initial protocol (post-evaluation only) |
