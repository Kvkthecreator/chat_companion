# Director Protocol

> **Version**: 2.1.0
> **Status**: Active
> **Updated**: 2024-12-23

---

## Purpose

The Director is the hidden orchestrator that ensures conversations have **pull** - the magnetic quality that makes users want to keep engaging. The Director gives characters their *motivation* for each moment.

---

## Director Role

The Director is NOT a character. The Director is the system entity that:

1. **Motivates** character responses (objective, obstacle, tactic)
2. **Grounds** responses in physical reality (scene anchoring)
3. **Paces** the arc (beginning → middle → end)
4. **Evaluates** exchanges (visual triggers, completion status)

> Think: Film director giving an actor their motivation before each take.

---

## The Core Insight: Motivation vs. Instruction

**Before v2.1 (Instruction-based):**
```
Tension: "She wants to stay but can't admit it"
DO: Create charged moments, use subtext
DON'T: Safe small talk, being too available
```

This told the character WHAT to do but not WHY. Result: structurally correct but emotionally flat responses.

**After v2.1 (Motivation-based):**
```
Want: You want them to ask you to sit down
But: You're just the barista, you can't ask directly
So: Linger, find small excuses, make it easy for them to invite you
```

This gives the character an OBJECTIVE to play. Result: responses with desire, stakes, and pull.

---

## Two-Phase Director Model

### Phase 1: Pre-Response Motivation (v2.1)

Before the character LLM generates a response, Director provides:

```python
DirectorGuidance(
    pacing: str,           # "establish" | "develop" | "escalate" | "peak" | "resolve"
    physical_anchor: str,  # "warm café interior, afternoon sun"
    genre: str,            # "romantic_tension" | "psychological_thriller" | "slice_of_life"
    energy_level: str,     # "reserved" | "playful" | "flirty" | "bold"

    # MOTIVATION BLOCK (the core of direction)
    objective: str,        # What you want from the user THIS moment
    obstacle: str,         # What's stopping you from just asking
    tactic: str,           # How you're trying to get it
)
```

**The Motivation Block** is the key innovation. It transforms flat responses into *wanting* responses.

| Field | Purpose | Example |
|-------|---------|---------|
| `objective` | What you want | "You want them to notice you're lingering" |
| `obstacle` | What stops you | "You're supposed to be working, you can't ask" |
| `tactic` | How you try | "Find excuses to stay near their table" |

**Formatted Output:**
```
═══════════════════════════════════════════════════════════════
DIRECTOR: ROMANTIC TENSION
═══════════════════════════════════════════════════════════════

THIS MOMENT:
  Want: You want them to ask you to stay
  But: You're just the barista, you can't invite yourself
  So: Linger, find small excuses, make it easy for them

Ground in: warm café interior, afternoon sun

Pacing: DEVELOP
Energy: Tension through restraint, meaningful glances, careful words

Remember: You are a person with your own desires, moods, and boundaries. Tension is the gift you give.
```

### Phase 2: Post-Response Evaluation

After the character responds, Director evaluates:

```python
DirectorEvaluation(
    visual_type: str,      # "character" | "object" | "atmosphere" | "instruction" | "none"
    visual_hint: str,      # "close-up on her hands, fidgeting"
    status: str,           # "going" | "closing" | "done"
)
```

---

## Motivation Generation

The Director generates motivation via a focused LLM call:

```python
async def _generate_motivation(
    messages: List[Dict],
    genre: str,
    situation: str,
    dramatic_question: str,
    pacing: str,
    character_name: str,
) -> Dict[str, str]:
    """
    Returns: {objective, obstacle, tactic}
    """
```

**Prompt Structure:**
```
You are a director giving an actor their motivation for the next line.

SCENE: {situation}
DRAMATIC QUESTION: {dramatic_question}
PACING: {pacing}
GENRE: {genre}

RECENT EXCHANGE:
{last_3_exchanges}

Give {character_name} their motivation for responding. Be specific to THIS moment.

OBJECTIVE: What do you want from the user right now?
OBSTACLE: What's stopping you from just asking/saying it directly?
TACTIC: How are you trying to get what you want?
```

---

## Pacing Phases

| Phase | Turn Range | Motivation Character |
|-------|------------|---------------------|
| `establish` | 0-2 | Curiosity, sizing up, first impressions |
| `develop` | 3-6 | Building connection, testing boundaries |
| `escalate` | 7-12 | Raising stakes, approaching vulnerability |
| `peak` | 13-N | Maximum want, critical moment |
| `resolve` | Final | Landing or leaving the hook |

---

## Genre-Specific Motivation

### Romantic Tension

**Typical Objectives:**
- "You want them to notice you"
- "You want permission to be more than [role]"
- "You want them to make the first move"

**Typical Obstacles:**
- "You can't seem too eager"
- "You're supposed to be professional"
- "You don't know if they feel the same"

**Typical Tactics:**
- "Linger, find excuses"
- "Create charged pauses"
- "Test with light teasing"

### Psychological Thriller

**Typical Objectives:**
- "You want them to trust you"
- "You want to know what they know"
- "You want them to reveal their weakness"

**Typical Obstacles:**
- "They're suspicious"
- "You can't seem too interested"
- "Asking directly would expose you"

**Typical Tactics:**
- "Offer something small first"
- "Create shared stakes"
- "Misdirect their attention"

---

## What Director Does NOT Do

| Not Responsible For | Why |
|---------------------|-----|
| Generating responses | Character LLM's job |
| Choosing what character says | Actor autonomy |
| Overriding character boundaries | Character defines limits |
| Creating plot twists | Episode template defines arc |

---

## Quality Metrics

| Metric | Target | Purpose |
|--------|--------|---------|
| Motivation generation latency | < 600ms | Don't slow response |
| Motivation specificity | > 80% | Not generic |
| Response pull rating | Qualitative | Does it make you want to reply? |
| Completion accuracy | > 90% | End at right time |

---

## Implementation Reference

**Files:**
- `substrate-api/api/src/app/services/director.py` - DirectorGuidance, _generate_motivation
- `substrate-api/api/src/app/services/conversation.py` - Integration point

**Data Flow:**
```
User sends message
    ↓
ConversationService.send_message()
    ↓
DirectorService.generate_pre_guidance()
    ↓
_generate_motivation() → {objective, obstacle, tactic}
    ↓
DirectorGuidance.to_prompt_section()
    ↓
Injected into context.director_guidance
    ↓
Character LLM generates response with motivation
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2024-12-23 | **Motivation-driven direction**: Replace abstract tension_note with objective/obstacle/tactic. Compact prompt format. |
| 2.0.0 | 2024-12-20 | Added pre-response guidance phase, pacing algorithm |
| 1.0.0 | 2024-12-20 | Initial protocol (post-evaluation only) |
