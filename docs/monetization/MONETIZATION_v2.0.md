# Monetization System v2.0: Ticket + Moments Model

> **Status**: Implemented (Migration 028)
> **Last Updated**: 2025-12-20

## Overview

EP-0 sells **crafted narrative experiences through episodes**, not "companionship through infinite chat." This fundamental difference drives our monetization model.

### The Problem with Incumbent Monetization

Character.ai has 2hr/day engagement but struggles to monetize because:
- Unclear value exchange ("what am I paying for?")
- Chat is infinite and undifferentiated
- No natural "units" of content to price

### Our Thesis

**Episodes are content units** — like TV episodes or arcade games. Users pay to enter experiences, not for chat or images directly. This creates:
- Clear value exchange ("I'm buying this story")
- Predictable costs (per episode, not per message)
- Natural upsell path ("play another?")

---

## Core Decisions

### Decision 1: "Ticket + Moments" Hybrid Model

**What**: Users pay Sparks to enter episodes. Auto-generated images are included. Manual generation is optional extra.

**Why**:
- Episode cost is predictable for user AND for us
- No mid-experience friction ("should I spend a Spark on this?")
- Images feel like rewards, not purchases
- Aligns with episode-first architecture

### Decision 2: Visual Mode is Episode Setting, Not User Setting

**What**: Episode templates define `visual_mode` (cinematic / minimal / none). Users don't toggle this.

**Why**:
- Author knows whether visuals matter for their episode
- Prevents mismatch (user disables images on visually-designed episode)
- Simpler UX — no settings to understand
- We control costs by designing episodes appropriately

### Decision 3: Director Triggers on Narrative Beats, Not Turn Counts

**What**: Auto-generation happens at tension peaks, location changes, emotional shifts — not every N turns.

**Why**:
- Avoids wasting generations on low-value moments
- Images feel earned and meaningful
- Better storytelling (visuals punctuate narrative)
- Cost optimization without degrading experience

### Decision 4: Same Episode Price Regardless of Visual Mode

**What**: All episodes cost the same (e.g., 3 Sparks) whether cinematic or minimal.

**Why**:
- Simple mental model for users
- Costs average out across catalog
- No complex pricing UI
- Reduces decision friction

### Decision 5: Free Chat Exists But Doesn't Auto-Generate

**What**: Users can "Free Chat" with characters outside episodes. No auto-gen, but manual gen available for Sparks.

**Why**:
- Maintains relationship between episodes
- Clear distinction: episodes = premium experience
- Low cost to us (just LLM)
- Users who want visuals in free chat can pay

---

## Pricing Structure

### Access Tiers

| Content Type | Free Tier | Premium ($19/mo) |
|-------------|-----------|------------------|
| Play Mode | Free | Free |
| Episode 0 (Entry) | Free | Free |
| Episodes 1+ | 3 Sparks each | Unlimited |
| Free Chat | Free | Free |

### Generation Costs

| Generation Type | Cost to User | Cost to Us |
|----------------|--------------|------------|
| Auto-gen (in episode) | Included in episode price | ~$0.05 each |
| Manual "Capture Moment" | 1 Spark | ~$0.05 |

### Spark Allocation (Hardened Economics v2.0)

| Tier | Sparks | Notes |
|------|--------|-------|
| Free (signup) | **0** | No onboarding giveaway - free content is already generous |
| Premium (monthly) | 100 | For manual "Capture Moment" generations |

**Rationale**: Free users get Episode 0 + Play Mode at no Spark cost (~$0.40 to us). This provides enough value to evaluate the product before purchasing.

---

## Data Model (Implemented)

### Episode Template Fields

```sql
-- episode_templates table
visual_mode TEXT DEFAULT 'none'        -- 'cinematic', 'minimal', 'none'
generation_budget INTEGER DEFAULT 0    -- Max auto-gens for this episode
episode_cost INTEGER DEFAULT 3         -- Sparks to start (0 for entry/play)
```

**Visual Mode Values**:
- `cinematic`: 3-4 auto-gens at narrative beats (Director decides when)
- `minimal`: 1 auto-gen at climax only
- `none`: No auto-gen (manual still available)

### Session Tracking Fields

```sql
-- sessions table
entry_paid BOOLEAN DEFAULT FALSE       -- Has user paid episode_cost?
generations_used INTEGER DEFAULT 0     -- Auto-gens triggered so far
manual_generations INTEGER DEFAULT 0   -- User-triggered "Capture Moment" gens
```

### Credit Costs

```sql
-- credit_costs table
('capture_moment', 'Capture This Moment', 1)  -- Manual generation
('episode_access', 'Episode Access', 3)        -- Default episode cost
```

---

## Director Logic (Implemented)

### Trigger Conditions (Cinematic Mode)

Generate a scene when ANY of these are true AND budget allows:
1. **Tension Peak**: Romantic/emotional tension spikes based on exchange analysis
2. **Location Change**: Scene moves to new setting
3. **Physical Proximity Shift**: Characters move closer or apart significantly
4. **Emotional Beat**: Matches beat_guidance from episode template
5. **Episode Climax**: Approaching resolution of episode arc
6. **User Action Description**: User describes physical action worth visualizing

### Skip Conditions

Do NOT generate even if triggered:
- Budget exhausted (`generations_used >= generation_budget`)
- Too recent (same turn as last generation)
- Visual mode is 'none'

### Minimal Mode Logic

For `visual_mode: minimal`:
- Only trigger on episode climax (status == "done" or "closing")
- Budget is 1
- All other triggers ignored

---

## Entry Gate Logic (To Implement)

### When User Starts Episode

```python
def can_access_episode(user, episode_template, session):
    # Free content
    if episode_template.episode_cost == 0:
        return True, None

    # Premium users
    if user.subscription_status == 'premium':
        return True, None

    # Check if already paid for this episode
    if session and session.entry_paid:
        return True, None

    # Check Spark balance
    if user.spark_balance >= episode_template.episode_cost:
        return True, 'deduct_sparks'

    return False, 'insufficient_sparks'
```

### Spark Deduction

- Deduct when episode starts, not when it completes
- If user abandons mid-episode, Sparks are not refunded (they accessed the content)
- Record transaction with `reference_type: 'episode_access'`
- Set `session.entry_paid = True` after deduction

---

## Manual Generation Flow

### User Triggers "Capture This Moment"

```python
def manual_generate_scene(user, session):
    # Check balance
    if user.spark_balance < 1:
        raise InsufficientSparksError()

    # Deduct Spark
    spend_sparks(user, 1, 'capture_moment', session.id)

    # Generate based on current conversation state
    scene = generate_scene(session, trigger_type='manual')

    # Track
    session.manual_generations += 1

    return scene
```

### Available In

- Episodes (regardless of visual_mode)
- Free Chat
- Play Mode (probably not needed, but allowed)

---

## Migration Status

### Completed (Migration 028)

- [x] Added `visual_mode`, `generation_budget`, `episode_cost` to episode_templates
- [x] Added `entry_paid`, `generations_used`, `manual_generations` to sessions
- [x] Migrated existing `auto_scene_mode: peaks` to `visual_mode: cinematic`
- [x] Set Play Mode episodes to free with cinematic visuals
- [x] Set Episode 0s to free
- [x] Grandfathered existing active sessions as `entry_paid = true`
- [x] Added credit_costs for `capture_moment` and `episode_access`
- [x] Updated Director service to use `visual_mode` and `generation_budget`

### Completed (Backend - conversation.py)

- [x] Episode access gate (check/deduct sparks on episode start)
- [x] Premium bypass for episode costs
- [x] 402 Payment Required response for insufficient sparks
- [x] `entry_paid` flag set after successful deduction

### Completed (Frontend)

- [x] `EpisodeAccessError` type in types/index.ts
- [x] `onEpisodeAccessDenied` callback in useChat.ts
- [x] Access denied modal handling in ChatContainer.tsx
- [x] InsufficientSparksModal component (already existed)

### Pending (Migration 029)

- [ ] User onboarding: Default `spark_balance = 0` for new users (hardened economics)
  - Migration file created: `029_user_onboarding_sparks.sql`
  - Needs to be run on production database

### To Implement

- [ ] Update frontend episode cards with cost display (show "3 Sparks" badge)
- [ ] "Capture Moment" button in chat UI (manual generation)
- [ ] Update documentation: CREDITS_SYSTEM_PROPOSAL.md, IMAGE_GENERATION_COSTS.md

---

## Related Documents

- [CREDITS_SYSTEM_PROPOSAL.md](./CREDITS_SYSTEM_PROPOSAL.md) - Spark currency system
- [IMAGE_GENERATION_COSTS.md](./IMAGE_GENERATION_COSTS.md) - Cost analysis
- [SUBSCRIPTION_IMPLEMENTATION.md](./SUBSCRIPTION_IMPLEMENTATION.md) - Premium tier

---

## Success Criteria

After full implementation:
- [x] Play Mode episodes are free with auto-visuals
- [x] Director respects generation_budget cap
- [x] Sparks are deducted on episode start (backend implemented)
- [x] Premium users access all episodes without Spark cost (backend implemented)
- [ ] Users see Spark cost before starting Episode 1+ (frontend pending)
- [ ] Auto-generated scenes appear at narrative beats (Director V2 pending)
- [ ] Users can manually generate for 1 Spark ("Capture Moment" button pending)
