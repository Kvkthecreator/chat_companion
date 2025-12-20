# Image Generation Costs & Subscription Model

> **Status**: Updated for Ticket + Moments model (v2.0)
> **Last Updated**: 2025-12-20
> **Related**: [MONETIZATION_v2.0.md](./MONETIZATION_v2.0.md) for episode-based pricing

## Overview

This document outlines the cost structure for character image generation and the subscription model for Fantazy.

**Key Change (v2.0)**: With the Ticket + Moments model, auto-generated images are **included in episode price** (not charged per-generation). Manual "Capture Moment" costs 1 Spark.

---

## Visual Rendering Approaches

### Approach Comparison

| Approach | Cost | Quality | Use Case |
|----------|------|---------|----------|
| Pre-generated Library | ~$0.05/image (one-time) | Good | Filler scenes, common scenarios |
| Runtime Flux Generation | ~$0.05/image (per use) | Excellent | High-impact moments, user-triggered |
| Overlay/Parallax | ~$0 (CSS only) | Limited | Simple VN-style presentations |

### Strategic Recommendation

Focus on **pre-generated library + sparse Flux moments** rather than complex overlay systems:
- Pre-generate 20-30 images per character covering common scenarios
- Reserve runtime Flux generation for high-impact story moments
- Overlay approach has positioning limitations (avatar poses don't fit all backgrounds naturally)

---

## Cost Breakdown

### Pre-Generated Library (One-Time)

| Item | Cost | Notes |
|------|------|-------|
| Per image (Flux) | ~$0.05 | BFL API pricing |
| Per character (20 images) | ~$1.00 | Covers common scenarios |
| Per character (30 images) | ~$1.50 | Extended coverage |
| 10 launch characters | ~$10-15 | Negligible startup cost |

**Batch generation is economically negligible** - even 100 characters with 30 images each = ~$150 total.

### Runtime Flux Generation (Per Use)

| Usage Pattern | Images/Month | Cost/User/Month |
|---------------|--------------|-----------------|
| Light user | 5 scenes | ~$0.25 |
| Average user | 20 scenes | ~$1.00 |
| Heavy user | 50 scenes | ~$2.50 |

### Chat API Costs (LLM)

| Usage Level | Est. Cost/User/Month |
|-------------|---------------------|
| Light | ~$0.50-1.00 |
| Average | ~$1.00-2.00 |
| Heavy | ~$2.00-4.00 |

---

## Subscription Model (v2.0 - Ticket + Moments)

### Tier Structure

#### Free Tier
- **0 Sparks on signup** (no onboarding giveaway)
- Episode 0 (entry) + Play Mode = **Free** (~$0.40 cost to you)
- Free Chat = **Free** (no images, ~$0.01-0.05 cost)
- Episodes 1+ cost **3 Sparks each** (must purchase or subscribe)
- **Cost to serve free-only users**: ~$0.40 one-time (Episode 0 + Play Mode)

#### Premium Tier ($19/month)
- **All episodes FREE** (unlimited access)
- 100 Sparks/month for manual "Capture Moment" generations
- Priority features
- Custom character requests
- **Cost to serve**: ~$5-7/active user/month (depends on episode consumption)

### Margin Analysis

| Tier | Revenue | Est. Cost | Gross Margin | Notes |
|------|---------|-----------|--------------|-------|
| Free | $0 | ~$0.50-1.00 | Negative | Acquisition funnel |
| Premium | $19 | ~$5-8 | **~60-75%** | Variable based on episode count |

**Note**: Premium costs are less predictable than before since episodes include auto-gen images. Heavy users may consume more, but this is offset by the $19 flat rate.

---

## Competitor Benchmarks

| Platform | Free Tier | Premium Price | Notes |
|----------|-----------|---------------|-------|
| Character.ai | Limited msgs | $10/month (c.ai+) | No image gen |
| NovelAI | Trial | $10-25/month | Image gen included |
| Replika | Basic chat | $15-20/month | Voice, AR features |
| Crushon.ai | Limited | $10-30/month | NSFW focus |

**Key insight**: $10-15/month is validated market pricing for AI companion apps.

---

## Economic Viability

### Unit Economics (Premium User) - v2.0

```
Revenue:              $19.00/month
- Lemon Squeezy fee:  -$1.45 (~5% + $0.50)
- Flux costs:         -$3.00 (avg 60 auto-gen across episodes)
- Chat API:           -$2.00 (average usage)
- Infra/other:        -$1.00
= Net margin:         $11.55/user/month (~61%)
```

**Assumptions**:
- Average Premium user plays ~15 episodes/month
- Each cinematic episode generates ~4 images (capped by `generation_budget`)
- 15 episodes × 4 images = 60 images × $0.05 = $3.00

### Unit Economics (Free User with Spark Purchases)

```
Pack purchase:        $9.99 (50 Sparks)
- Episodes played:    ~16 episodes (50 ÷ 3 Sparks)
- Cost per episode:   ~$0.20 (3-4 auto-gen images included)
- Our margin:         ~60% after LS fees
```

### Unit Economics (Free User - No Purchase)

```
Free content cost:    ~$0.40 (Episode 0 + Play Mode)
- Revenue:            $0
- Net:                -$0.40 per non-converting user
```

**Note**: Free tier burn is capped at ~$0.40/user. This is acceptable customer acquisition cost if even 10% convert to a $4.99 Starter pack.

### Scaling Considerations

- **Library generation**: Fixed cost, scales with characters not users
- **Runtime Flux**: Scales linearly with usage (capped by `generation_budget` per episode)
- **Chat API**: Primary variable cost, scales with engagement

### Risk Mitigation

1. **`generation_budget` caps** on auto-gen prevent runaway costs per episode
2. **Library-first strategy** reduces runtime generation needs
3. **Episode pricing** aligns user cost with our cost (more episodes = more images, but also more revenue)

---

## Implementation Notes

### Library Generation Strategy

1. Define 20-30 common scene types per character:
   - Emotional states (happy, sad, surprised, angry, embarrassed)
   - Settings (bedroom, cafe, school, park, night scene)
   - Actions (waving, sitting, standing, close-up)

2. Batch generate during character creation
3. Store in CDN for fast delivery
4. Cost is amortized across all users

### Runtime Generation Triggers

Reserve Flux generation for:
- User-requested custom scenes
- Story milestone moments
- Special character interactions
- Premium feature unlocks

---

## Summary

The Ticket + Moments model (v2.0) provides:
- **Clear value exchange** - users pay for episodes, not individual actions
- **Predictable costs** - `generation_budget` caps auto-gen per episode
- **Premium value** - unlimited episodes makes subscription compelling
- **Sustainable margins** at $19/month pricing (~61%)
- **Competitive positioning** in the AI companion market

See [MONETIZATION_v2.0.md](./MONETIZATION_v2.0.md) for complete implementation details.
