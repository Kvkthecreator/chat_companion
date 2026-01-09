# Activation & Growth Analysis

> Last updated: 2026-01-09
> Status: Early data collection phase

## Current Metrics (as of Jan 9, 2026)

| Metric | Value | Notes |
|--------|-------|-------|
| Total Signups | ~13 | Excluding test accounts |
| Engaged Users | 2 | Sent 1+ messages |
| Activation Rate | 15% | Signups → First message |
| Paid Users | 0 | Excluding founder |
| Visitor → Signup | 12.7% | 102 visitors → 13 signups |
| Bounce Rate | 65% | Typical for landing pages |

## Key Insight: Activation is the Problem

85% of signups never send a single message. This is the critical bottleneck.

### Known Issues (Fixed)

| Issue | Status | Date Fixed |
|-------|--------|------------|
| Episode 0 charged 3 Sparks instead of 0 | Fixed | 2026-01-09 |

Users hitting the paywall on the "free trial" episode explains much of the drop-off. Monitor next 20-30 signups to see if activation improves.

## Funnel Analysis

```
Visitor (100%)
    ↓ 12.7% convert
Signup (12.7%)
    ↓ 15% activate  ← BOTTLENECK
First Message (1.9%)
    ↓ ???
Engaged (5+ msgs)
    ↓ ???
Paid
```

## User Behavior Patterns

| Pattern | Count | Likely Cause |
|---------|-------|--------------|
| Signed up, never opened chat | 9 | Onboarding unclear, paywall |
| Opened chat, sent 0 msgs | 2 | Confused by UI, waiting for AI |
| Sent messages, engaged | 2 | Success case |

## Hypotheses to Test

### Why users don't activate

1. **Paywall on Episode 0** (fixed) - New users had 0 Sparks, Episode 0 cost 3
2. **Category confusion** - Expect a game/visual novel, see chat UI
3. **No clear "start here"** - Don't know what to click after signup
4. **Waiting for AI** - Don't realize they need to send first message

### Potential Fixes (Prioritized)

| Priority | Fix | Effort | Impact |
|----------|-----|--------|--------|
| P0 | Episode 0 free (done) | Done | High |
| P1 | Auto-send opening message from character | Medium | High |
| P2 | "Start your first story" CTA post-signup | Low | Medium |
| P3 | Landing page shows chat UI in action | Medium | Medium |
| P4 | Onboarding tooltip/tour | Medium | Low |

## Reddit Ads Performance

### Current Campaign: reddit_romance

| Metric | Value |
|--------|-------|
| Spend | $5.82 |
| Impressions | 10,082 |
| Clicks | 40 |
| CPC | $0.15 |
| CTR | 0.397% |

### New Campaigns (Created Jan 9)

**otome_isekai**
- Target: r/OtomeIsekai, r/otomegames, r/RomanceBooks, r/shoujo
- Series: Villainess Survives, Death Flag: Deleted
- Headlines:
  - "Transmigrated as the villainess. Now what?"
  - "You know how this novel ends. Change it."
  - "The death flag is in 6 days. Survive."

**manhwa_regressor**
- Target: r/manhwa, r/sololeveling, r/OmniscientReader
- Series: Regressor's Last Chance
- Headlines:
  - "You died. You regressed. Rewrite the ending."
  - "The Hero failed. This time, you won't."
  - "10 years back. You remember everything."

### CTA Considerations

Reddit CTAs are pre-set (not customizable). Options:

| CTA | Recommendation |
|-----|----------------|
| "Learn More" | Safer - sets expectation of info page first |
| "Play Now" | Higher intent but risks expectation mismatch |
| "Sign Up" | Honest but lower CTR |
| "Get Started" | Good middle ground |

**Current choice: "Learn More"** - More honest about the flow, reduces bounce from users expecting instant gameplay.

### Category Education Challenge

Users from Reddit romance/manhwa communities may not understand "interactive chat fiction" as a category. They might expect:
- Visual novel
- Mobile game
- Quiz

**Potential solutions:**
- Landing page copy: "It's like texting a character from your favorite manhwa"
- Show chat UI screenshot/GIF on landing page
- Ad copy that sets expectations: "Text-based interactive story"

## Conversion Benchmarks

| Metric | Industry Typical | Our Target |
|--------|------------------|------------|
| Free → Paid | 2-5% | 3% |
| Freemium games | 1-3% | - |
| Niche passionate audience | 5-10% | 5% |

## Pre-Seed VC Readiness

### What VCs want to see

| Signal | Threshold | Our Status |
|--------|-----------|------------|
| Retention D7 | >20% | Unknown |
| Retention D30 | >10% | Unknown |
| Conversion | 2-3%+ | Unknown |
| MRR | $1-5K | $0 |
| Signups | 500-1000 | 13 |

### Milestones before VC conversations

1. [ ] 100 signups
2. [ ] 20+ engaged users (sent messages)
3. [ ] Measure activation rate post-Episode-0-fix
4. [ ] First organic paid conversion
5. [ ] D7 retention data

**Estimated timeline:** 4-6 weeks at current ad spend

## Next Actions

### This Week
- [x] Fix Episode 0 paywall (done)
- [ ] Launch otome_isekai campaign
- [ ] Launch manhwa_regressor campaign
- [ ] Monitor next 20 signups for activation

### Next 2 Weeks
- [ ] Reach 50 signups
- [ ] Measure post-fix activation rate
- [ ] Interview churned users (if possible)
- [ ] Decide on P1 fix (auto-send opening message?)

### Month 1 Goals
- [ ] 100 signups
- [ ] 20+ engaged users
- [ ] First paid conversion
- [ ] Identify top-performing ad campaign/audience

## Appendix: User Engagement Data (Jan 9)

| User | Messages | Sessions | Status | Signed Up |
|------|----------|----------|--------|-----------|
| kevin | 26 | 7 | Engaged | Dec 12 |
| User | 30 | 2 | Engaged | Jan 8 |
| Hubba Subba | 0 | 1 | Opened, didn't send | Jan 8 |
| Nicky Nicholas | 0 | 1 | Opened, didn't send | Dec 17 |
| Others (9) | 0 | 0 | Never tried | Various |
