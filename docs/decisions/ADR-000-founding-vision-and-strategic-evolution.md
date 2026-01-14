# ADR-000: Founding Vision and Strategic Evolution

> **Status**: Foundational
> **Date**: 2026-01-12
> **Context**: This ADR documents the origin story, strategic pivots, and fundamental product decisions that shaped ep-0

---

## Executive Summary

**ep-0 is a chat-based interactive fiction platform combining Character.AI-style conversations with Netflix-style episodic structure.**

This is the **third iteration** of attempts to build a monetizable generative AI product as a bootstrapped solo founder, evolving from:
1. ❌ Context management systems
2. ❌ IP/legal AI tools
3. ✅ ep-0: Character AI + narrative structure

**Core bet:** There exists an underserved market for structured narrative experiences in a chat format, positioned between pure AI roleplay (Character.AI) and visual novels (Choices/Episode).

---

## Historical Context: Why ep-0 Exists

### The Productivity Burnout (Pre-2025)

**Problem identified:**
- Solo founder, bootstrap constraints
- Previous attempts in "productivity apps" space failed
- Needed high monetization potential
- Wanted to avoid commoditized B2B SaaS

**Market observation (Late 2024):**
- Character.AI had massive traction but recent PR issues (quality degradation)
- Korean startup "Babe Chat" showed demand for character-based interaction
- Generative AI space was hot but most apps were productivity-focused
- Entertainment/companion AI had clear monetization (subscriptions, tokens)

**Decision:** Pivot to AI companion/character chat space targeting English-speaking markets.

---

## Phase 1: Initial Direction (Dec 2024 - Early Jan 2025)

### Core Hypothesis

**"Character.AI + stronger narrative = competitive advantage"**

**Positioning:**
- Better quality than Character.AI (post-degradation)
- Narrative structure that Character.AI lacks
- English market focus (less competition than Korean market)

### Major Obstacles Encountered

#### 1. **Quantity Problem**
Character.AI has **millions of characters**. Building a competitive character library would require:
- Massive content creation effort
- User-generated content (UGC) platform (complex moderation)
- Years to reach competitive scale

**Impact:** Pure character quantity approach deemed infeasible for solo founder.

#### 2. **NSFW Content Dilemma**
**Observation:** Most character AI usage is flirty/romantic/NSFW-adjacent

**Options considered:**
- A) Lean into NSFW (monetizes well but platform risk, payment processor issues)
- B) Stay SFW (harder to monetize, less differentiated)
- C) "Romantic tension" without explicit content (middle ground)

**Decision:** Focus on romantic tension, emotional connection, not explicit NSFW.

**Rationale:**
- Reduces platform/payment risk
- Still serves romantic/companion use case
- Allows App Store distribution
- Differentiates from pure "AI girlfriend" apps

#### 3. **Resource Constraints**
Solo founder cannot:
- Build massive character library
- Moderate UGC at scale
- Compete on character diversity
- Hire writers/artists for content

**Constraint forced innovation:** Need structure that scales without massive content creation.

---

## Phase 2: The Netflix + Character.AI Synthesis (Jan 2025)

### The Breakthrough Insight

**"Instead of infinite characters, create episodic series with recurring characters"**

**Inspiration sources:**
1. **Netflix:** Series → Episodes structure
2. **Character.AI:** Conversational interaction
3. **Visual novels:** Branching narratives, character relationships
4. **Webtoons:** Serialized storytelling

### Architectural Decisions

#### Series + Episode Structure

**Why:**
- ✅ **Finite content** - Can ship with 8-10 episodes per series
- ✅ **Narrative arc** - Beginning, middle, end (vs infinite chat)
- ✅ **Monetization hooks** - Paywall after free Episode 0
- ✅ **Retention driver** - Users return for next episode
- ✅ **Production scalable** - Can add series over time

**Tradeoffs:**
- ❌ Less flexible than pure roleplay
- ❌ Can't compete on character count
- ✅ Can compete on narrative quality

**Documented in:** ADR-002 (Theatrical Architecture)

#### Character + Director System

**Why:**
- **Character agents** maintain personality consistency
- **Director agents** drive plot forward
- **Separation of concerns** - Character responds, Director advances story

**Technical implementation:**
- Multi-agent LLM orchestration
- Persistent character state
- Dynamic prompt construction based on user choices

**Documented in:** ADR-004 (User Character Role Abstraction)

#### Image Generation Strategy

**Why:**
- Pure text can't compete with visual novels
- Full visual novel production too expensive
- AI image generation = middle ground

**Approach:**
- Flux 1.1 Pro for quality
- Dynamic prompts from episode context
- "Prompt-first" strategy for consistency

**Documented in:** ADR-003, ADR-007

---

## Phase 3: Content Strategy Evolution (Jan 2025 - Jan 2026)

### Initial Content (Dec 17-28, 2025): Romantic Tension

**First 20 series all focused on:**
- Romantic tension (crush, enemies-to-lovers, workplace romance)
- Contemporary settings (K-pop, coffee shops, campus)
- Relatable scenarios for broad audience

**Rationale:**
- Safe, SFW content
- Emotional connection without NSFW
- Proven romance genre popularity

**Results:**
- ✅ Content was producible
- ✅ AI image quality acceptable
- ⚠️ No clear differentiation from existing apps
- ❌ Broad targeting = hard to acquire users

### The Niche Pivot (Jan 5-9, 2026): OI/Manhwa Focus

**Strategic shift:** From broad romance → niche genre targeting

**New series added:**
- **Otome Isekai:** "The Villainess Survives", "Death Flag: Deleted"
- **Manhwa Regressor:** "The Regressor's Last Chance", "Seventeen Days"
- **BL/GL:** "Ink & Canvas", "Debate Partners"
- **Shoujo/AI Shoujo:** Multiple series
- **Genre expansion:** Historical, psychological, workplace, cozy

**Why this shift:**

#### 1. **Targeting Hypothesis**
```
Assumption: Niche genres = passionate, engaged audiences

Evidence supporting:
- r/OtomeIsekai: 100k+ engaged members
- r/manhwa: 400k+ members
- Clear subreddit communities for targeting
- Genre-specific Discord servers
- Fans already consuming similar content
```

**Reasoning:**
- Easier to target ads (Reddit subreddits)
- Passionate fans more willing to try new formats
- Less competition in niche vs broad romance

#### 2. **Content Quality Hypothesis**
```
Assumption: AI performs better with genre-specific prompts

Observed results:
- OI/manhwa prompts → better image consistency
- Genre conventions → stronger narrative scaffolding
- Specific tropes → clearer character archetypes
```

**Examples:**
- "Villainess transmigration" = clear visual style
- "Regressor remembering past life" = strong narrative hook
- Genre familiarity = better AI context

#### 3. **The Dual Optimization**
```
High genre targeting + High content quality = Ideal activation match

Expected funnel:
1. Target r/OtomeIsekai fans
2. Ad shows villainess series (genre match)
3. User clicks (relevant)
4. Series page shows clear genre content
5. User signs up and activates (familiarity)
```

**This was the operating thesis from Jan 9-12.**

---

## Current Status (Jan 12, 2026): The Awakening

### What We've Learned

#### The Expectation Mismatch Problem

**What we discovered:**
- ✅ Targeting niche genres works (signups increased 175%)
- ❌ Activation remains near 0%
- ⚠️ **Format doesn't match audience expectations**

**Root cause identified:**
```
Manhwa/OI fans consume VISUAL content:
- Webtoons with art panels
- Visual novels with sprites
- Animated adaptations

We deliver TEXT-BASED chat:
- Message bubbles
- Occasional AI images
- No consistent art style
```

**The paradox:**
- Best targeting = OI/manhwa fans (passionate, engaged)
- Best AI content quality = OI/manhwa genres
- Worst format match = OI/manhwa fans expect visuals

#### The Positioning Problem

**We're stuck in "uncanny valley":**
```
Character.AI          ep-0          Visual Novels
(Pure text)          (Text + AI)     (Full visuals)
     ↓                   ↓                  ↓
  Infinite           Structured         Polished
   Free              Episodes            Premium
  Flexible           Narrative           Guided
```

**We're not:**
- Infinite enough to compete with Character.AI
- Visual enough to compete with Choices/Episode
- Polished enough to justify premium pricing

---

## Open Questions (As of Jan 12, 2026)

### Strategic Uncertainty

1. **Is the format viable?**
   - Can chat-based IF work for ANY audience?
   - Or is it fundamentally flawed positioning?

2. **Who actually wants this?**
   - ❌ Manhwa fans (want visuals)
   - ❌ Visual novel fans (want polish)
   - ✅ Character.AI users who want structure?
   - ✅ Text-IF enthusiasts (small market)?
   - ✅ "AI companion" seekers (different positioning)?

3. **Should we pivot format or audience?**
   - **Option A:** Add visuals (become visual novel)
   - **Option B:** Find text-lovers (different targeting)
   - **Option C:** Lean into pure chat roleplay (drop episodes)

### Recent Changes (Jan 12)

**Implemented:**
- ✅ Changed ad copy from "Play Now" → "Start Chat"
- ✅ Added UTM tracking for campaign attribution
- ✅ Updated URLs to series-specific landing pages

**Testing hypothesis:**
```
If users KNOW it's chat-based upfront, will they activate?

Expected outcomes:
- Lower CTR (fewer clicks)
- Higher activation (right expectations)
- Better cost-per-engaged-user
```

**Decision point:** Wait 5-7 days for data before major pivot.

---

## Architectural Decisions Driven by This Evolution

### ADR-001: Genre Architecture
**Why:** Need scalable content organization
**Decision:** Genre-based series taxonomy
**Status:** Validated by recent genre expansion

### ADR-002: Theatrical Architecture
**Why:** Need structure vs infinite chat
**Decision:** Series → Episodes → Scenes
**Status:** Core to differentiation, but may be limiting

### ADR-003: Image Generation Strategy
**Why:** Can't afford artists, need visuals
**Decision:** AI-generated images with Flux
**Status:** Works but inconsistent quality

### ADR-004: Character Role Abstraction
**Why:** Users want to BE in the story
**Decision:** User plays a role, can create custom characters
**Status:** Low adoption, complex UX

### ADR-005: Props Domain
**Why:** Need game-like engagement elements
**Decision:** Props system for choices
**Status:** Built but not core to experience

### ADR-006: Props Progression
**Why:** Need retention mechanics
**Decision:** Unlock system for props
**Status:** Over-engineered for current activation

### ADR-007: Prompt-First Image Generation
**Why:** Image consistency is critical
**Decision:** Store prompts, generate on demand
**Status:** Good engineering, doesn't solve content mismatch

---

## Lessons Learned

### What Worked

1. **Rapid iteration** - 40 series in 3 weeks
2. **AI leveraging** - Solo founder shipped AAA volume
3. **Niche targeting** - Increased signups 175%
4. **Technical execution** - Product is stable, scalable
5. **Data instrumentation** - UTM tracking, admin analytics

### What Didn't Work

1. **Assumption: "Better than Character.AI" = competitive**
   - Reality: Different format entirely, not a substitute

2. **Assumption: "Niche targeting + niche content = activation"**
   - Reality: Format mismatch trumps content relevance

3. **Assumption: "AI images = good enough for visual novel fans"**
   - Reality: Expectations set by webtoons/games are too high

4. **Assumption: "Episode structure = better than infinite chat"**
   - Reality: Structure may actually limit the format's strengths

### What We Don't Know Yet

1. **Is there a market for structured chat-based IF?**
   - New "Start Chat" ads will tell us

2. **Can we find the right audience?**
   - Maybe text-IF fans, not visual media fans

3. **Is the product execution the problem, or the concept?**
   - Need user interviews to know

---

## Founding Principles (Still Valid)

### 1. Bootstrap Constraints Drive Innovation
- ✅ Can't compete on quantity → Create structure
- ✅ Can't hire artists → Use AI generation
- ✅ Can't moderate UGC → Curate series

### 2. Monetization Must Be Built In
- ✅ Free Episode 0, paid continuation
- ✅ Spark token system
- ⚠️ Only works if users activate

### 3. AI-Native, Not AI-Wrapper
- ✅ Multi-agent orchestration (Character + Director)
- ✅ Dynamic prompt construction
- ✅ Real-time image generation
- ✅ Not just ChatGPT with a UI

### 4. Narrative Over Novelty
- ✅ Focus on story quality
- ✅ Emotional connection
- ⚠️ May be wrong format for narrative-first audience

---

## The Path Forward (Validation Required)

### Immediate (Next 7 Days)

**Test the hypothesis:**
```
"Honest ad copy" → Right audience → Higher activation
```

**Data needed:**
- Activation rate of "Start Chat" ads
- User interviews (why activate or not)
- Campaign performance by source

### Decision Tree (Jan 19, 2026)

```
IF activation >40% with honest ads:
  → Format is viable, keep optimizing
  → Focus on content quality
  → Find more text-loving audiences

ELSE IF activation still 0-10%:
  → Format has fundamental issues
  → Consider pivot:
     A) Add visual novel elements
     B) Target different audience
     C) Lean into pure chat roleplay

ELSE IF no signups at all:
  → Honest ads scared everyone away
  → Market doesn't exist
  → Reconsider entire direction
```

---

## Appendices

### A. Product Evolution Timeline

| Date | Milestone | Impact |
|------|-----------|--------|
| Late 2024 | Decision to build AI companion product | - |
| Dec 2024 | Initial Character.AI + narrative concept | - |
| Dec 17-28 | First 20 romantic tension series | Proof of concept |
| Jan 5-9 | Pivot to OI/manhwa niche genres | Signups +175% |
| Jan 10 | Public series pages launched | - |
| Jan 12 | "Start Chat" ad copy + UTM tracking | Testing phase |

### B. Content Library Growth

```
Phase 1 (Dec 17-28): 20 series
- All romantic tension
- Contemporary settings
- Broad audience

Phase 2 (Jan 5-9): +20 series
- Genre diversification
- Niche targeting
- OI/manhwa focus

Total: 40 series, ~300+ episodes
```

### C. Key Metrics Progression

| Metric | Dec 2025 | Jan 12, 2026 |
|--------|----------|--------------|
| Total signups | 8 | 22 (+175%) |
| Premium users | 1 | 1 (4.5%) |
| Activated users | 2-3 | 2-3 (0% growth) |
| Weekly signups | 1-2 | 14 |
| Ad spend | ~$20 | ~$50 |

**The gap:** Signups scaling, activation not.

### D. Related Documents

- [ACTIVATION_AND_GROWTH_ANALYSIS.md](../plans/ACTIVATION_AND_GROWTH_ANALYSIS.md)
- [CHANNEL_STRATEGY.md](../plans/CHANNEL_STRATEGY.md) - BOC Framework
- [SERIES_URL_QUICK_REFERENCE.md](../plans/SERIES_URL_QUICK_REFERENCE.md)
- [UTM_TRACKING_COMPLETE.md](../implementation/UTM_TRACKING_COMPLETE.md)

---

## Meta: Why This ADR Exists

**Purpose:**
- Prevent "amnesia" about why decisions were made
- Document the strategic journey for future reference
- Provide context for new team members (if any)
- Serve as "founder's journal" during pivot discussions

**When to update:**
- Major strategic pivots
- Significant validation/invalidation of hypotheses
- New fundamental insights about product-market fit

**Current status:** Living document, high uncertainty phase.

---

## Phase 4: The Clarity (Jan 14, 2026)

### Technical Validation Complete

**Activation fix timeline:**
- **Jan 12**: Opening messages display as chat bubbles ✅
- **Jan 12**: Starter prompts added to database ✅
- **Jan 14**: Starter prompts now visible in UI ✅ (was hidden in EmptyState)

**Root cause:** Starter prompts only rendered when `chatItems.length === 0`, but backend auto-injected opening message, so prompts never showed. Fixed by rendering prompts after messages when user hasn't sent first message yet.

**Technical foundation is now solid.** Users see:
1. Opening message as chat bubble (992+ chars)
2. 3 clickable starter prompts below
3. Clear guidance for first interaction

### Strategic Realization: Right Product, Wrong Audience

**Key insight from reviewing ADRs 000-007:**

The episode structure is NOT the problem — **it's the core differentiator.**

**What we learned:**
```
Assumption: OI/manhwa fans will try chat-based stories
Reality: They want VISUAL content (webtoons, art panels)

New understanding: We're not "between" Character.AI and visual novels
We're ORTHOGONAL — offering something neither can provide:
  - Character.AI can't add structure (breaks their model)
  - Visual novels can't match our speed/cost/agency
```

**The product positioning is sound:**
- ✅ Structured narrative (vs Character.AI's infinite)
- ✅ Chat-based agency (vs visual novels' rigid paths)
- ✅ AI-native speed (vs expensive production)
- ✅ Bootstrap-compatible (finite content, clear monetization)

**The distribution targeting was wrong:**
- ❌ r/OtomeIsekai → Passive consumers (webtoon readers)
- ❌ r/manhwa → Visual media fans
- ✅ Need: Interactive fiction enthusiasts, Character.AI power users

### Market Position Clarified

**ep-0 is NOT:**
- A Character.AI clone with episodes (downgrade from infinite)
- A visual novel with worse graphics (downgrade from polish)
- A webtoon you chat with (format confusion)

**ep-0 IS:**
- Character.AI + narrative structure = Stories with beginnings/endings
- Visual novels + dynamic conversation = More agency, less cost
- Interactive fiction + AI generation = Faster content, visual elements

**Target users:**
1. **Character.AI power users** frustrated by lack of structure
2. **Interactive fiction readers** (Choice of Games, Twine enthusiasts)
3. **Visual novel fans on budget** (college students, casual players)
4. **Romance readers who want agency** (not passive consumption)

**This is a real market.** Choice of Games has paying users. Character.AI has 20M+ MAU. The intersection exists — we were just looking in the wrong subreddits.

### Architectural Validation

All ADRs (001-007) align with this understanding:

**ADR-002 (Theatrical Architecture):**
- Episode structure = MOAT, not limitation
- Enables authored quality at bootstrap scale
- Character.AI can't copy this

**ADR-004 (User Characters):**
- "Any character can play any episode"
- Already supports character-first discovery
- No hard fork needed between character/story focus

**ADR-001, 003, 005-007:**
- All support the "structured narrative chat" thesis
- Genre targeting, image generation, props system
- Built for THIS positioning, not borrowed from others

**Conclusion:** Architecture is solid. Distribution needs complete revision.

---

## Current Status (Jan 14, 2026): Validated Product, Need Distribution Reset

### What's Validated

1. ✅ **Technical execution works** - UX bugs fixed, product is stable
2. ✅ **Product architecture is sound** - ADRs support the core thesis
3. ✅ **Founding principles hold** - Bootstrap constraints drove right innovations
4. ✅ **Monetization model viable** - Free Episode 0 + paid continuations

### What's Invalidated

1. ❌ **OI/manhwa targeting** - Wrong audience (want visuals, not chat)
2. ❌ **"Better than Character.AI" positioning** - We're different, not better
3. ❌ **Reddit as primary channel** - Maybe viable, but wrong subreddits

### What's Unknown

1. ❓ **Will Character.AI users want structure?** - Need to test
2. ❓ **Will IF readers accept AI chat?** - Need to validate
3. ❓ **What's the right acquisition channel?** - TikTok? Discord? Direct?

### Next Phase: Distribution Experiments

**Hypothesis to test:**
```
IF we target interactive fiction / Character.AI audiences
AND show them structured episodic chat format
THEN activation rate will be 40-60% (vs current 0-25%)
```

**Test plan documented in:** [GTM_DISTRIBUTION_RESET.md](../marketing/GTM_DISTRIBUTION_RESET.md)

---

## Conclusion

**ep-0 represents a bet that structured narrative chat experiences can compete in the entertainment space.**

We've iterated from:
- Context management → IP tools → Character AI
- Pure character chat → Episodic structure
- Broad romance → Niche genres
- Generic landing → Series-specific targeting
- "Play Now" → "Start Chat"
- Visual media fans → Interactive fiction enthusiasts ← **NEW**

**Current understanding:** We're building the right product for the wrong audience.

**The core bet remains valid.** Episode structure is our moat, not our limitation. We just need to find users who want structured stories in chat format — they exist (Character.AI power users, IF readers, budget VN fans), we were just looking in the wrong places.

**Next 7-14 days:** Test distribution with intent-matched audiences.

---

**Last updated:** 2026-01-14
**Author:** Kevin Kim (Founder)
**Review cycle:** After each major validation/invalidation event
