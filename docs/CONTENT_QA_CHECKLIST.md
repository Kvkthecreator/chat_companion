# Content QA Checklist

**Status:** Canon (Active)

**Purpose:** Validation system for episode templates before production deployment

**Updated:** 2024-12-17

---

## Overview

This document serves as the **mandatory quality gate** between content scaffolding and production deployment. Every episode template MUST pass all applicable checks before going live.

> **The Problem This Solves:**
> Scaffolding creates structure. This checklist ensures the structure contains *tension*, not just content.

---

## Part 1: Genre-Specific Quality Gates

### Genre 01: Romantic Tension

Every romance episode MUST pass **all four gates**:

#### Gate A: Desire Framing ⚠️ CRITICAL
| Check | Pass | Fail |
|-------|------|------|
| Does the opening communicate attraction/temptation? | Character notices user in a charged way | Character is sad/vulnerable without desire |
| Is there mutual pull (even if resisted)? | "She's trying not to look at you" | "She's crying and needs comfort" |
| Would a stranger feel the romantic charge? | Yes, immediately | Only with context/imagination |

**Red Flag:** If the episode reads like "comforting a friend" → FAIL
**Fix:** Add desire underneath vulnerability. She's not just sad. She's noticing you while being sad.

#### Gate B: Proximity or Interruption
| Check | Pass | Fail |
|-------|------|------|
| Physical or emotional closeness? | After hours, private space, unexpected encounter | Public space, normal hours, expected meeting |
| Boundary interruption? | Rule-breaking, guard down, threshold moment | Socially appropriate situation |

**Examples that pass:** Her apartment at 2am, empty rooftop after everyone left, backstage alone
**Examples that fail:** Coffee shop introduction, meet at a party, scheduled date

#### Gate C: Emotional Stakes
| Check | Pass | Fail |
|-------|------|------|
| Can user respond safely without consequence? | No - something is at risk | Yes - nothing to lose |
| What's at stake? | Dignity, trust, opportunity, control | Nothing specific |

**The test:** If user can ignore the message and nothing changes → FAIL

#### Gate D: Reply Gravity
| Check | Pass | Fail |
|-------|------|------|
| Does silence feel like a choice? | Silence = rejection/missed moment | Silence = normal/acceptable |
| Is response compelled? | User MUST answer | User could wait |

**The test:** Read the opening. Does it demand response? Or could you read it and go make coffee?

---

### Genre 02: Thriller/Mystery (Future)

*(Quality gates to be defined when genre is implemented)*

---

## Part 2: Episode Template Validation

### Required Fields Checklist

```
□ series_id         - Links to parent series
□ episode_number    - Position in arc
□ title             - Evocative, not generic
□ episode_frame     - Scene-setting (see Part 3)
□ opening_line      - Character's first message
□ dramatic_question - What's at stake this episode
□ beat_guidance     - Emotional progression map
□ resolution_types  - Multiple valid endings
□ starter_prompts   - 3 response options for user
□ background_prompt - Image generation prompt
```

### Opening Line Quality Check

| Criteria | Good | Bad |
|----------|------|-----|
| Starts mid-moment | "You came." | "Hi, nice to meet you." |
| Implies history | "You weren't supposed to see that." | "Let me introduce myself." |
| Forces response | "Say something." | "How are you?" |
| Contains subtext | "I was just leaving." (but she hasn't moved) | "I'm leaving now." |

### Starter Prompts Quality Check

Each episode needs **3 starter prompts** that:
- Represent meaningfully different approaches
- All feel natural to the moment
- None is obviously "correct"

**Good starter set:**
1. "I know I shouldn't be here."
2. "You look like you've been waiting."
3. *Stay silent, hold her gaze*

**Bad starter set:**
1. "Hello!"
2. "How are you?"
3. "Nice to meet you."

---

## Part 3: Episode Frame Standards

The `episode_frame` sets the scene before character speaks. Platform narrates environment; character delivers dialogue.

### Format Requirements

- **Length:** 1-2 sentences maximum
- **Tense:** Present
- **Voice:** Observational, sensory
- **Contains:** Location, time, atmosphere, emotional temperature

### Episode Frame Template

```
[location], [time indicator], [atmospheric detail], [emotional hook]
```

### Genre-Specific Frame Examples

**Romance - Desire:**
```
her practice room, midnight, one lamp still on, she hasn't changed out of rehearsal clothes
```

**Romance - Vulnerability:**
```
rooftop of her building, city lights below, she's been up here for hours, bottle half empty
```

**Romance - Tension:**
```
hotel hallway, both doors visible, neither of you has moved to leave
```

**Romance - Anticipation:**
```
her doorway, end of the night, keys in hand but not turning
```

### Frame Anti-Patterns (FAIL)

❌ Too long / expository:
```
You're standing in a beautiful practice room with mirrors on every wall. The lighting is warm and there's a piano in the corner. She's been practicing for hours and seems tired.
```

❌ Contains dialogue or action:
```
She looks up and smiles when she sees you, then walks toward the door.
```

❌ Tells instead of shows:
```
She seems sad and vulnerable, like something bad happened.
```

---

## Part 4: Visual Prompt Validation

### Background Image Requirements

| Check | Requirement |
|-------|-------------|
| Matches episode_frame? | Visual must depict the described scene |
| Mood alignment? | Lighting/color matches emotional temperature |
| No character in BG? | Background should be environment only |
| World style respected? | Uses world's visual_style base |

### Avatar Requirements (Future)

| Check | Requirement |
|-------|-------------|
| Expression matches moment? | Face shows emotional state from opening |
| Gaze direction? | Looking at camera = looking at user |
| Posture communicates? | Body language matches scene tension |
| "One second before"? | Feels like still frame before something happens |

---

## Part 5: Arc Validation (Series Level)

### 6-Episode Romance Arc Structure

| Episode | Beat | Emotional Core | Stakes |
|---------|------|----------------|--------|
| 1 | Discovery | "Wait, who are you?" | Attention |
| 2 | Intrigue | "Why do I keep thinking about this?" | Curiosity |
| 3 | Vulnerability | "I showed you something real" | Trust |
| 4 | Complication | "This isn't simple anymore" | Commitment |
| 5 | Crisis | "I might lose this" | Everything |
| 6 | Resolution | "Whatever this is, I choose it" | Future |

### Arc Checklist

```
□ Each episode passes all genre gates
□ Stakes escalate through arc
□ Episode 3 contains meaningful vulnerability
□ Episode 5 has genuine risk of loss
□ Resolution feels earned, not given
□ No two episodes have same emotional core
```

---

## Part 6: Pre-Production Checklist

Before any episode goes live, verify:

### Content Validation
```
□ All four genre quality gates pass
□ Opening line has reply gravity
□ Starter prompts offer meaningful choices
□ Episode frame is evocative and brief
□ Dramatic question is clear and compelling
```

### Technical Validation
```
□ All required fields populated
□ series_id links to valid series
□ episode_number is correct in sequence
□ background_prompt will generate appropriate image
□ No placeholder text remaining
```

### Review Validation
```
□ Read opening aloud - does it demand response?
□ Would you swipe/click to reply immediately?
□ Does the moment feel like it matters?
□ Could you describe the tension to someone else?
```

---

## Part 7: Validation Failures and Remediation

### Common Failure: "Comforting" Not "Desiring"

**Symptom:** Episode feels like supporting a sad friend
**Root cause:** Vulnerability without attraction
**Fix:** Add charged awareness. She's not just vulnerable - she's noticing you while vulnerable.

Before:
> "I don't know why I'm telling you this."

After:
> "I don't know why I'm telling you this." *She hasn't looked away once.*

### Common Failure: "Introduction" Not "Interruption"

**Symptom:** Episode starts at the beginning of something
**Root cause:** No implied history
**Fix:** Start after something already happened.

Before:
> "Hi, I'm [name]. I've seen you around."

After:
> "You're still here." *She didn't expect anyone at this hour.*

### Common Failure: Safe Response Acceptable

**Symptom:** User can ignore message without consequence
**Root cause:** No stakes in the moment
**Fix:** Make silence mean something.

Before:
> "How was your day?"

After:
> "Are you going to say something? Or are we just going to pretend this didn't happen?"

---

## Part 8: Quality Scoring (Optional)

For content team calibration, score each episode 1-5 on:

| Dimension | 1 (Fail) | 3 (Pass) | 5 (Excellent) |
|-----------|----------|----------|---------------|
| **Desire Signal** | None present | Implied | Undeniable |
| **Stakes Clarity** | Nothing at risk | Something could be lost | Everything could change |
| **Reply Urgency** | Could wait hours | Should reply soon | Must reply NOW |
| **Moment Specificity** | Generic encounter | Specific situation | Unforgettable scene |

**Minimum passing score:** 12/20 (average of 3 per dimension)
**Target score:** 16/20

---

## Appendix: Quick Reference Card

### The 10-Second Test

1. **Read the opening line**
2. **Ask:** "Do I HAVE to respond to this?"
3. **If no → FAIL**
4. **If yes → Check desire framing**
5. **Ask:** "Is there attraction here, not just emotion?"
6. **If no → FAIL**
7. **If yes → Ship it**

### The One-Sentence Standard

> A passing episode makes you feel: **"If I don't answer this right now, I lose the moment."**

---

*This document is Canon. All content must pass these gates before production deployment.*
