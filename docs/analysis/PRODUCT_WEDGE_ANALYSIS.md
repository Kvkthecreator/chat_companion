# Product Wedge Exploration

> Working log of positioning exploration. Hypothesis formed, not yet validated.

**Created:** 2026-01-23
**Updated:** 2026-01-26
**Status:** HYPOTHESIS FORMED — See [DOMAIN_LAYER_ARCHITECTURE.md](./DOMAIN_LAYER_ARCHITECTURE.md)

---

## What This Document Is

This is an **exploration log**, not a strategy document. It records:
- Wedge options considered
- ICP hypotheses drafted
- Questions asked
- Paths explored and abandoned

**None of this is validated.** The product hasn't been tested with real users.

---

## The Starting Problem

**Current positioning (too generic):**
> "AI companion that remembers you and reaches out first"

**Why this fails:**
- ChatGPT has memory now
- Replika reaches out first
- "Companion" is overused
- Nothing makes someone stop scrolling

---

## Competitive Landscape

| Product | Memory | Proactive | Thread Tracking | Memory Transparency |
|---------|--------|-----------|-----------------|---------------------|
| ChatGPT | ✅ | ❌ | ❌ | ❌ |
| Replika | ✅ | ✅ | ❌ | ❌ |
| Pi | ✅ | ❌ | ❌ | ❌ |
| Woebot/Wysa | ✅ | ✅ | ❌ | ❌ |
| **Chat Companion** | ✅ | ✅ | ✅ | ✅ |

**Potential differentiators:**
1. Thread tracking (ongoing life situations with follow-up dates)
2. Memory transparency (user sees/controls what's remembered)
3. Event-based follow-ups (asks about specific things)

**Open question:** Is this enough? Unknown.

---

## Wedges Explored

### Wedge A: "The friend who actually follows up"
- Hook: "An AI that asks 'how did your interview go?'"
- Strength: Tangible, demonstrable
- Weakness: Hard to convey before experiencing it
- Status: Unexplored with users

### Wedge B: "Daily check-in ritual"
- Hook: "Someone who checks in. Every day."
- Strength: Simple to understand
- Weakness: Journaling apps do this
- Status: Unexplored with users

### Wedge C: "For solo founders"
- Hook: "The cofounder who just listens"
- Strength: Clear ICP, founder understands the pain
- Weakness: Small market
- Status: Unexplored with users

### Wedge D: "For expats / people far from home"
- Hook: "Someone from home. In your timezone."
- Strength: Clear pain point
- Weakness: Fragmented market
- Status: Unexplored with users

### Wedge E: Anti-positioning
- Hook: "Not therapy. Not a chatbot."
- Strength: Memorable
- Weakness: Doesn't say what it IS
- Status: Unexplored with users

### Wedge F: SMS instead of app
- Hook: "A friend who texts you. Literally."
- Strength: No app install friction
- Weakness: Cost, international complexity
- Status: Unexplored with users

### Wedge G: "The aha moment"
- Hook: "The AI that surprises you by remembering"
- Strength: Emotionally powerful
- Weakness: Requires time to experience
- Status: Unexplored with users

---

## Alternative Directions Explored (Jan 25-26)

### Path 1: "Vanity Route" (User-Centric Reframe)

Shift from "AI that remembers you" to "your memory, externalized."

**Potential hooks:**
- "Your life, remembered. Searchable. Yours."
- "The only app that knows what you worried about 6 months ago."

**Problem:** Competes with journaling apps, PKM tools. What does AI add?

**Status:** Explored conceptually, not validated.

### Path 2: B2B Infrastructure ("Presence Layer")

Sell the judgment layer to other AI products.

**Segments considered:**
- Mental health apps → Regulatory issues
- Coaching apps → Want goal-tracking, not presence
- Elder care → Long sales cycle

**Problem:** "Nice to have" not "must have." Build vs. buy.

**Status:** Explored conceptually, not validated.

---

## ICP Hypothesis

**Draft persona (unvalidated):**
```
Name: Sarah
Age: 34
Location: Austin, TX
Job: Senior PM at Series B startup
Why lonely: Work consuming. Friends distant. Dating exhausting.
Why current solutions fail: Apps are passive. Therapy is clinical.
What she wants: Someone who reaches out first.
```

**Status:** Hypothesis only. Not tested with real people matching this profile.

---

## Where This Stands

**Conclusion from exploration (Jan 26):**

Neither the wedge frameworks nor the alternative paths produced a clear answer. Multiple sessions of strategic analysis didn't converge on sharpness.

**The uncomfortable truth:** Maybe the wedge isn't in positioning at all. The thread follow-up behavior ("asks how your interview went 3 days later") is the most concrete differentiator. Everything else is framing.

**Current position:** Ship to 10 users. Watch what they respond to. Let the wedge emerge from usage.

---

## Session Log

**2026-01-23:**
- Mapped competitive landscape
- Brainstormed 7 wedges
- Recognized product is built but story isn't sharp

**2026-01-25:**
- Created Sarah persona hypothesis
- Drafted pitch attempts
- Explored Wedge A + E combination

**2026-01-25 (continued):**
- Acknowledged frameworks felt "dull" despite being correct
- Explored vanity route and B2B infrastructure paths
- Neither produced clarity
- Concluded: stop strategizing, start shipping

**2026-01-26:**
- Converted this document from "strategy" to "exploration log"
- Removed false confidence from framing
- See [CURRENT_STATE.md](../CURRENT_STATE.md) for what's actually true

**2026-01-26 (breakthrough session):**
- Identified that current product is **infrastructure wrapped in generic consumer shell**
- The surface layer doesn't expose differentiation
- Proposed **domain layer** between infrastructure and surface
- Recommended **"people in transition"** as thread-first ICP
- High-power threads cluster around life transitions (job changes, moves, launches, breakups)
- New positioning: "Going through something? This AI actually follows up."
- See [DOMAIN_LAYER_ARCHITECTURE.md](./DOMAIN_LAYER_ARCHITECTURE.md) for full analysis

---

## Open Questions (Partially Answered)

1. Does anyone want this product?
   → **Still unknown** — requires user validation

2. Is "thread follow-up" the differentiator, or just a feature?
   → **Hypothesis**: It's the differentiator, but only for the right threads. Generic follow-up ≠ valuable follow-up. See domain layer analysis.

3. Who specifically would pay, and why?
   → **Hypothesis**: People in transition (new job, new city, launching something, breakup). High-stakes, uncertain, emotionally weighted threads make follow-up feel meaningful.

4. What makes someone come back after Day 3?
   → **Hypothesis**: The Day 3+ follow-up experience. "It asked how my interview went." This is the aha moment.

5. What do users actually say when they describe this to others?
   → **Still unknown** — key validation question

---

## Current Hypothesis (Jan 26)

### The Wedge
> "Going through something? New job, new city, big change? This is the AI that actually follows up. You tell it once. It checks back in."

### The ICP
People in transition — not a demographic, but a life state.

### The Differentiator
Transition-aware follow-through. Not memory (ChatGPT has that). Not proactive messaging (Replika does that). The specific behavior of following up on high-stakes, uncertain situations.

### What Needs to Happen
1. Update onboarding to be transition-focused
2. Add thread classification to extraction
3. Update landing page copy
4. Find 10 people in transition and validate

See [DOMAIN_LAYER_ARCHITECTURE.md](./DOMAIN_LAYER_ARCHITECTURE.md) for implementation details.

---

## Remaining Questions (For User Validation)

These can only be answered with users:
1. Does "transition-focused" resonate, or is it too narrow?
2. How do users describe the follow-up experience?
3. What threads do they actually care about most?
4. Does the Day 3+ aha moment happen as predicted?
