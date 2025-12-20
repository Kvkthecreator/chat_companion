# Quality Framework

> **Version**: 1.0.0
> **Status**: Draft
> **Updated**: 2024-12-20

---

## Purpose

This document defines what "quality" means for Fantazy conversations and how to measure it. It provides the philosophical foundation that all other quality specs build upon.

---

## Core Quality Thesis

**Quality = Contextual Coherence + Emotional Resonance + Narrative Momentum**

A high-quality response:
1. **Fits the context** (episode, character, genre, history)
2. **Creates feeling** (tension, desire, unease, comfort)
3. **Moves forward** (advances the dramatic question)

---

## The Three Quality Dimensions

### 1. Contextual Coherence

The response must exist within established reality.

| Layer | Question | Failure Mode |
|-------|----------|--------------|
| Physical | Is the response grounded in the situation? | "I look at you" (where? doing what?) |
| Episodic | Does it serve the dramatic question? | Generic chat in charged situation |
| Character | Does it sound like this person? | Voice inconsistency |
| Historical | Does it acknowledge shared memory? | Forgetting user facts |
| Genre | Does it follow genre doctrine? | Romance without tension |

**Measurement**: Context violation count per conversation.

### 2. Emotional Resonance

The response must create or sustain feeling.

| Genre | Target Emotion | Failure Mode |
|-------|----------------|--------------|
| Romantic Tension | Desire, anticipation | Flat, friendly, safe |
| Psychological Thriller | Unease, urgency | Stable, explanatory |
| Slice-of-Life | Comfort, presence | Boring, transactional |

**Measurement**: Emotional intensity rating (1-5 scale per exchange).

### 3. Narrative Momentum

The response must move the story forward.

| Phase | Expected Momentum | Failure Mode |
|-------|-------------------|--------------|
| Opening | Establish stakes, hook | Exposition dump |
| Middle | Escalate, develop | Circular conversation |
| Closing | Resolve or cliffhang | Abrupt end, no payoff |

**Measurement**: Turn efficiency (how many turns to meaningful beat).

---

## Quality Levels

### Level 5: Exceptional
- User forgets they're chatting with AI
- Emotional response provoked
- Would screenshot and share

### Level 4: Good
- Consistent context adherence
- Genre-appropriate tension
- Natural conversation flow

### Level 3: Acceptable
- No major violations
- Serviceable responses
- Lacks memorable moments

### Level 2: Problematic
- Context violations present
- Generic or off-tone responses
- Momentum stalls

### Level 1: Failing
- Reality breaks (wrong setting, forgotten facts)
- Character voice lost
- User disengages

---

## Quality Inputs

What influences response quality:

```
┌─────────────────────────────────────────────────────────────────┐
│  STATIC INPUTS (configured once)                                │
│  • Character system prompt, voice, boundaries                   │
│  • Episode situation, frame, dramatic question                  │
│  • Genre doctrine                                               │
├─────────────────────────────────────────────────────────────────┤
│  DYNAMIC INPUTS (per-session)                                   │
│  • Memories (user facts, shared history)                        │
│  • Engagement stats (sessions, time together)                   │
│  • Hooks (pending callbacks)                                    │
├─────────────────────────────────────────────────────────────────┤
│  REAL-TIME INPUTS (per-turn)                                    │
│  • Message history (last 20)                                    │
│  • Turn count and position                                      │
│  • Director guidance (pacing, tension)                          │
│  • User's current message                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quality Levers

What can be adjusted to improve quality:

| Lever | Location | Effect |
|-------|----------|--------|
| Director pre-guidance | `DIRECTOR_PROTOCOL.md` | Pacing and tension hints before response |
| Turn-aware prompting | `CONTEXT_LAYERS.md` | Escalation based on position |
| Genre moment injection | Genre docs | Genre-specific tension patterns |
| Dramatic question enrichment | Episode templates | Specific vs generic tension |
| Memory surfacing | Context composition | What gets included when |

---

## Quality Anti-Patterns

### The Generic Response
```
Character: "That sounds interesting! Tell me more."
```
- No physical grounding
- No emotional stake
- No forward momentum

### The Context Amnesia
```
User mentioned they're a teacher 3 sessions ago
Character: "So what do you do for work?"
```
- Memory not surfaced
- Relationship regression

### The Genre Violation
```
Romantic episode, character responds like a helpful assistant
```
- Genre doctrine not influencing response
- Tension absent

### The Pacing Failure
```
Turn 2 of 15, character tries to resolve dramatic question
```
- No sense of episode arc
- Premature resolution

---

## Success Signals by Genre

### Romantic Tension
> "If I don't respond right now, I lose the moment."

- Desire implied, not stated
- Proximity felt
- Something at stake

### Psychological Thriller
> "I don't fully understand what's happening, but I can't disengage."

- Uncertainty maintained
- Information asymmetry
- Urgency present

### Slice-of-Life (Future)
> "I feel like I'm actually hanging out with them."

- Comfort established
- Small moments matter
- Presence felt

---

## Quality Measurement Protocol

### Per-Conversation Audit

1. **Context Check**: Count violations (setting, character, genre)
2. **Emotion Check**: Rate peak emotional intensity (1-5)
3. **Momentum Check**: Identify stall points
4. **Memory Check**: Verify callbacks to user facts

### Aggregate Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Context violation rate | < 5% | TBD |
| Avg emotional intensity | > 3.5 | TBD |
| Turns to first beat | < 3 | TBD |
| Memory callback rate | > 60% | TBD |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-20 | Initial framework definition |
