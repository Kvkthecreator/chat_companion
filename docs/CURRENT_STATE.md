# Chat Companion: Current State

> Single source of truth. What's built, what's unknown, what's next.

**Updated:** 2026-01-26

---

## What's Built

The product exists and works end-to-end:

| Feature | Status | Notes |
|---------|--------|-------|
| Daily check-in messages | ✅ Working | Sends at user's preferred time |
| Memory extraction | ✅ Working | Extracts facts, threads, follow-ups |
| Thread tracking | ✅ Working | Follows up on life situations |
| Silence detection | ✅ Working | Reaches out when user goes quiet |
| Web chat interface | ✅ Working | `/chat` route |
| Memory transparency UI | ✅ Working | User sees/edits what's remembered |
| Push notifications | ✅ Working | Via Expo |
| Email fallback | ✅ Working | For web users |
| Onboarding | ✅ Working | Chat-based |
| Message variety | ✅ Working | PRESENCE type, back-off logic, topic deduplication |

**Technical implementation:** See [MEMORY_SYSTEM.md](features/MEMORY_SYSTEM.md) and [COMPANION_OUTREACH_SYSTEM.md](design/COMPANION_OUTREACH_SYSTEM.md).

---

## What's Unknown

These questions cannot be answered without real users:

1. **Does anyone want this?** — No external users yet
2. **What's the wedge?** — Explored many options, none validated
3. **Who's the ICP?** — Hypotheses exist, untested
4. **Will people come back after Day 3?** — Unknown
5. **What makes someone pay?** — Unknown
6. **What do users actually say about it?** — Unknown

---

## What's NOT Built (Intentionally)

| Feature | Why Deferred |
|---------|--------------|
| Payments/subscriptions | Need users first |
| Companion state table | Premature optimization |
| Closeness/concern scores | Requires longitudinal data |
| Skip logic | Need to see if over-messaging is a problem |
| Manual memory creation | Nice-to-have |
| Multiple companions | One is enough for validation |

---

## Current Position

**The product is built. The story isn't sharp.**

Multiple sessions of strategic analysis explored:
- 7 wedge framings
- 2 ICP directions
- B2C vs B2B paths
- Vanity route vs companion route

None produced a clear answer. See [PRODUCT_WEDGE_ANALYSIS.md](analysis/PRODUCT_WEDGE_ANALYSIS.md) for the exploration log.

**Conclusion:** Stop strategizing. Ship to 10 users. Watch what they respond to.

---

## Next Steps

### Immediate
1. **Complete GTM checklist** — See [GTM_DEFINITION_OF_DONE.md](GTM_DEFINITION_OF_DONE.md)
2. **Get 10 real users** — Friends, communities, wherever
3. **Watch and listen** — What do they respond to? What surprises them?

### After 10 Users
- Revisit positioning based on what worked
- Decide on pricing/monetization
- Consider building more only if needed

---

## Documents Index

### Active (Use These)
- [GTM_DEFINITION_OF_DONE.md](GTM_DEFINITION_OF_DONE.md) — Launch checklist
- [MEMORY_SYSTEM.md](features/MEMORY_SYSTEM.md) — Core product philosophy
- [COMPANION_OUTREACH_SYSTEM.md](design/COMPANION_OUTREACH_SYSTEM.md) — How outreach works

### Reference (Historical)
- [FOUNDER_JOURNEY_SYNTHESIS.md](analysis/FOUNDER_JOURNEY_SYNTHESIS.md) — Product history (yarnnn → fantazy → companion)
- [PRODUCT_WEDGE_ANALYSIS.md](analysis/PRODUCT_WEDGE_ANALYSIS.md) — Exploration log (unvalidated)

### Technical
- [ARCHITECTURE.md](development/ARCHITECTURE.md)
- [SETUP.md](development/SETUP.md)
- ADRs in `/docs/adr/`

---

## Reminder

> The next 10 users will teach you more than the next 10 documents.
