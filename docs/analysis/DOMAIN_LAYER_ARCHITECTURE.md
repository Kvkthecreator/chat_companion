# Domain Layer Architecture

> **Status**: Strategic Analysis
> **Created**: 2026-01-26
> **Purpose**: Document the gap between infrastructure and consumer product, and propose a domain layer solution

---

## Executive Summary

**The Insight**: We've built infrastructure-grade capabilities (memory extraction, thread tracking, priority-based messaging) wrapped in a generic consumer shell. The shell doesn't expose our differentiation.

**The Problem**: The product works, but it feels generic. The user's Day 1 experience is indistinguishable from Replika or Pi. Our differentiation (thread follow-up) only manifests on Day 3+.

**The Solution**: Add a **domain layer** between the infrastructure and consumer surface. This layer tunes the system for a specific ICP by defining which threads matter, how to talk about them, and what vocabulary resonates.

---

## The Gap: Infrastructure vs. Consumer Product

### What We Built (Infrastructure Layer)

| Component | What It Does | Status |
|-----------|--------------|--------|
| Three-tier memory | Working → Active → Core memory | ✅ Solid |
| Thread extraction | Detects ongoing life situations | ✅ Working |
| Priority stack | 5-level message prioritization | ✅ Working |
| Follow-up scheduling | Tracks when to check back in | ✅ Working |
| Pattern detection | Mood trends, engagement patterns | ✅ Working |
| Extraction observability | Health monitoring for background jobs | ✅ Working |

This is sophisticated plumbing. The architecture documents read like infrastructure docs — they describe *mechanisms*, not *experiences*.

### What We Built (Consumer Surface)

| Component | What User Experiences | Differentiation? |
|-----------|----------------------|------------------|
| Chat interface | Send messages, get responses | No — every chat app has this |
| Daily check-in | Receive a message at set time | Weak — Replika does this |
| Memory page | See what companion knows | Unique, but hidden |
| Onboarding | Tell companion about yourself | Standard |

### The Gap

The infrastructure is **ICP-agnostic**. It can extract any thread, follow up on anything, detect any pattern.

But without domain knowledge, it treats all threads equally:
- "Job interview on Friday" = same weight as "Had pizza for dinner"
- "Just moved to a new city" = same follow-up style as "Watched a movie"

**The follow-up behavior is our differentiator, but it doesn't feel tuned for anyone specifically.**

---

## The Axiom (Unchanged)

From [FIRST_PRINCIPLES_FRAMEWORK.md](./FIRST_PRINCIPLES_FRAMEWORK.md):

> **People are lonely. They want to feel like someone is thinking about them.**

This is universal. Everyone experiences this.

### The Derived Problem

Universal problems create positioning problems:
- If everyone has the problem, you can't speak to anyone specifically
- If you can't speak specifically, your message is generic
- Generic messages don't cut through noise

### The Missing Corollary

> **"Things that matter" is not universal. It's context-dependent.**

A solo founder and a new parent care about different things. A job seeker and a recent graduate have different threads that feel important.

**The same follow-up behavior feels caring or tone-deaf depending on whether you're tracking the right threads.**

---

## Thread-First ICP Selection

Instead of starting with "who is the user?", we start with "what threads are most powerful to follow up on?"

### What Makes a Thread High-Power?

| Property | Why It Matters | Example |
|----------|----------------|---------|
| **Stakes** | User cares about outcome | Job interview vs. what they had for lunch |
| **Uncertainty** | Outcome wasn't known when shared | Waiting to hear back vs. routine task |
| **Temporal gap** | Time passed between sharing and follow-up | 3 days later vs. same conversation |
| **Unprompted** | User didn't remind the system | System remembered on its own |
| **Emotional weight** | Thread carries feeling | Nervous about presentation vs. having a meeting |

**High-power threads = high stakes + uncertain outcome + emotional weight**

### Thread Types Mapped to Life Situations

| Thread Type | Stakes | Uncertainty | Emotional Weight | Who Has These |
|-------------|--------|-------------|------------------|---------------|
| **Job/career transitions** | High | High | High | Job seekers, career changers |
| **Relationship milestones** | High | High | High | Dating, new relationships, breakups |
| **Creative/project launches** | High | Medium | High | Founders, makers, artists |
| **Health situations** | High | High | High | Anyone with ongoing health threads |
| **Relocation/life moves** | High | Medium | High | Expats, movers, life transitioners |
| **Learning/growth goals** | Medium | Medium | Medium | Self-improvers |
| **Daily routine** | Low | Low | Low | Everyone (but low power) |

### The Insight

**The highest-power threads cluster around TRANSITIONS.**

- Career transition (interview → waiting → outcome)
- Relationship transition (dating → exclusive → living together OR breakup)
- Location transition (considering move → moving → settling in)
- Health transition (symptom → diagnosis → treatment → recovery)
- Creative transition (idea → building → launching → feedback)

---

## ICP Recommendation: People in Transition

Not a demographic. A life state.

### Examples

| Life Situation | Their Threads |
|----------------|---------------|
| Just started a new job | How's the new team? Did you figure out that thing that was confusing? |
| Just moved to a new city | Have you found your coffee shop? Made any friends yet? |
| Going through a breakup | How are you holding up? Did you end up talking to them? |
| Launching something | How's prep going? Did you ship? How did it land? |
| Job hunting | How did the interview go? Did you hear back? What's next? |
| Starting therapy | How was the session? Are you finding it helpful? |

### Why This Works

1. **High-power threads are guaranteed** — transitions are inherently uncertain and high-stakes
2. **Temporal structure is built-in** — transitions have before/during/after phases
3. **Emotional weight is automatic** — transitions are stressful
4. **Follow-up is natural** — "How's the new job?" is a normal human question
5. **Universal but specific** — everyone goes through transitions, but you're speaking to them *during* one

---

## The Domain Layer

### What It Provides

| Component | What It Does | Example |
|-----------|--------------|---------|
| **Thread Templates** | Pre-defined high-signal thread types | `job_search`, `new_city`, `relationship_change`, `health_situation`, `creative_project` |
| **Phase Detection** | Recognize where in transition they are | `considering`, `in_progress`, `just_happened`, `settling_in`, `resolved` |
| **Follow-up Prompts** | Domain-specific questions per phase | Job search + waiting → "Have you heard back yet?" |
| **Vocabulary/Tone** | How to talk about this thread type | Health: gentle. Launch: excited. Breakup: careful. |
| **Importance Weighting** | Which threads to prioritize | Transition threads > routine threads |
| **Bootstrap Questions** | Onboarding questions that seed high-power threads | "What's changing in your life right now?" |

### Architectural Position

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONSUMER SURFACE                             │
│              (Chat UI, Daily Messages, Memory Page)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                     DOMAIN LAYER (NEW)                           │
│                  (Transition-Focused)                            │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Thread Templates│  │ Phase Detection │  │ Follow-up Bank  │  │
│  │                 │  │                 │  │                 │  │
│  │ - job_search    │  │ - considering   │  │ "How did X go?" │  │
│  │ - new_city      │  │ - in_progress   │  │ "Any news on Y?"│  │
│  │ - relationship  │  │ - just_happened │  │ "How are you    │  │
│  │ - health        │  │ - settling_in   │  │  feeling about  │  │
│  │ - creative      │  │ - resolved      │  │  Z now?"        │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                │                                │
│                                ▼                                │
│                    ┌───────────────────────┐                    │
│                    │ Thread Classifier     │                    │
│                    │                       │                    │
│                    │ Input: raw extraction │                    │
│                    │ Output: typed thread  │                    │
│                    │         + phase       │                    │
│                    │         + importance  │                    │
│                    └───────────────────────┘                    │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                   INFRASTRUCTURE LAYER                           │
│                      (Already Built)                             │
│                                                                  │
│  Memory Extraction → Thread Tracking → Priority Stack → Output   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Changes in the Product

### Onboarding

| Current | With Domain Layer |
|---------|-------------------|
| "What's going on in your life?" | "What's changing in your life right now?" |
| Open-ended, captures anything | Transition-focused, captures high-power threads |

### Thread Extraction

| Current | With Domain Layer |
|---------|-------------------|
| Extracts any mentioned situation | Classifies into transition types |
| All threads weighted equally | Transition threads weighted higher |

### Follow-up Messages

| Current | With Domain Layer |
|---------|-------------------|
| Generic: "How did that go?" | Typed: "Did you hear back about the job?" |
| No phase awareness | Phase-aware: "You've been in the new city for a month - feeling more settled?" |

### Positioning

| Current | With Domain Layer |
|---------|-------------------|
| "AI companion that remembers you" | "Going through something? This AI actually follows up." |
| Competes with ChatGPT on memory | Competes on behavior during transitions |

---

## Implementation Scope

| Component | Effort | Priority | Notes |
|-----------|--------|----------|-------|
| Thread templates (schema) | Medium | High | Define 5-6 transition types |
| Classification prompt | Medium | High | Extend extraction to classify |
| Phase detection | Medium | High | Add to thread model |
| Transition-focused onboarding | Low | High | Change one question |
| Follow-up prompt bank | Low | Medium | Per-type follow-up templates |
| Importance weighting | Low | Medium | Simple scoring adjustment |
| Landing page copy | Low | High | Lead with transitions |

### Suggested Sequence

1. **Update onboarding question** — "What's changing in your life right now?"
2. **Add thread templates to extraction prompt** — Classify into types
3. **Update landing page** — Lead with transitions, not memory
4. **Find 10 users in transition** — Validate the hypothesis
5. **Iterate on follow-up prompts** — Based on what resonates

---

## The Wedge, Sharpened

### Before

> "An AI companion that remembers you and reaches out first"

**Problem**: ChatGPT has memory. Replika reaches out. This doesn't cut through.

### After

> "Going through something? New job, new city, big change? This is the AI that actually follows up. You tell it once. It checks back in."

**Why this works**:
- Speaks to a specific moment (transition)
- Promises specific behavior (follow-up)
- Differentiates on action, not feature

---

## Validation Plan

1. **Update onboarding** — Change situation question to be transition-focused
2. **Update landing page** — Lead with transitions
3. **Find 10 people in transition** — Specifically recruit: new job, new city, recent breakup, launching something
4. **After Day 7, ask one question**: "What surprised you about this?"
5. **Listen to their language** — How do they describe it to others?

The wedge will emerge from what they say.

---

## Open Questions

| Question | Status |
|----------|--------|
| Is the infrastructure sound? | ✅ High confidence — architecture is solid |
| Is a domain layer needed? | ✅ High confidence — analysis confirms |
| Is "transitions" the right domain? | ⚠️ Medium-high — strongest thread-power, but unvalidated |
| Will this resonate with users? | ❓ Unknown — requires validation |

---

## Related Documents

- [FIRST_PRINCIPLES_FRAMEWORK.md](./FIRST_PRINCIPLES_FRAMEWORK.md) — Axiom and derivation
- [PRODUCT_WEDGE_ANALYSIS.md](./PRODUCT_WEDGE_ANALYSIS.md) — Wedge exploration log
- [FOUNDER_JOURNEY_SYNTHESIS.md](./FOUNDER_JOURNEY_SYNTHESIS.md) — Product evolution history
- [../features/MEMORY_SYSTEM.md](../features/MEMORY_SYSTEM.md) — Memory architecture details
- [../design/COMPANION_OUTREACH_SYSTEM.md](../design/COMPANION_OUTREACH_SYSTEM.md) — Outreach implementation

---

## Changelog

**2026-01-26**: Initial document created from strategic analysis session
- Identified infrastructure vs. consumer gap
- Proposed domain layer architecture
- Recommended "people in transition" as ICP
- Outlined implementation scope
