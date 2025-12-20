# Play Mode System

> **Version**: 1.0.0
> **Status**: Canonical
> **Updated**: 2024-12-20

---

## Purpose

This folder contains the **Play Mode System** — specifications for viral, shareable bounded experiences that serve as customer acquisition channels.

Play Mode experiences are:
- **Bounded episodes** within the existing series architecture
- **Anonymous until conversion** — no auth wall before result
- **Designed for virality** — identity-based results, shareable cards
- **Platform primitives** — Director, evaluation, and share infrastructure are reusable

---

## Document Structure

```
docs/quality/play/
├── README.md                    ← You are here
├── PLAY_MODE_ARCHITECTURE.md    ← Core architecture and routing
├── TROPE_SYSTEM.md              ← Romantic Trope taxonomy (Play Mode v2)
├── RESULT_REPORT_SPEC.md        ← Share card and result page design
└── IMPLEMENTATION_STATUS.md     ← Current vs. target state tracking
```

---

## Decision Log

| Decision | Status | Notes |
|----------|--------|-------|
| Play Mode = bounded episode (not separate product) | ✅ Locked | Uses existing series architecture |
| First implementation: Hometown Crush + Jack | 🔄 Next | Replaces Flirt Test as primary |
| Routing: `/play`, `/play/[slug]`, `/r/[id]` | ✅ Locked | Clean viral entry points |
| Anonymous until conversion | ✅ Locked | Result is end of free experience |
| 5 Romantic Tropes (replacing 5 Flirt Archetypes) | ✅ Locked | New taxonomy for Play v2 |
| Result report structure | ✅ Locked | Identity + evidence + callback + cultural |

---

## Current State (Flirt Test v1)

| Component | Location | Status |
|-----------|----------|--------|
| Backend models | `substrate-api/.../models/evaluation.py` | ✅ Live |
| Games service | `substrate-api/.../services/games.py` | ✅ Live |
| Director integration | `substrate-api/.../services/director.py` | ✅ Live |
| API routes | `substrate-api/.../routes/games.py` | ✅ Live |
| Frontend pages | `web/src/app/play/flirt-test/` | ✅ Live |
| Share page | `web/src/app/r/[shareId]/` | ✅ Live |
| Types | `web/src/types/index.ts` | ✅ Live |

### Current Archetype System

5 Flirt Archetypes (defined in `evaluation.py`):
- `tension_builder` — The Tension Builder
- `bold_mover` — The Bold Mover
- `playful_tease` — The Playful Tease
- `slow_burn` — The Slow Burn
- `mysterious_allure` — The Mysterious Allure

---

## Target State (Romantic Trope v2)

| Component | Changes Required |
|-----------|-----------------|
| Trope taxonomy | Replace archetypes with tropes |
| Result report | Add personalized evidence, callback quote, cultural references |
| LLM evaluation | Update prompts for trope detection |
| Share card | New OG image design |
| Content | Hometown Crush series + Jack character |
| Routing | `/play` landing + `/play/hometown-crush` |

### New Trope System

5 Romantic Tropes:
- `slow_burn` — The Slow Burn
- `second_chance` — The Second Chance
- `all_in` — The All In
- `push_pull` — The Push & Pull
- `slow_reveal` — The Slow Reveal

See [TROPE_SYSTEM.md](TROPE_SYSTEM.md) for full specification.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [DIRECTOR_PROTOCOL.md](../core/DIRECTOR_PROTOCOL.md) | Director evaluation logic |
| [DIRECTOR_UI_TOOLKIT.md](../core/DIRECTOR_UI_TOOLKIT.md) | Stream events and UI components |
| [../plans/FLIRT_TEST_IMPLEMENTATION_PLAN.md](/docs/plans/FLIRT_TEST_IMPLEMENTATION_PLAN.md) | Original implementation plan |
| [../plans/VIRAL_PLAY_FEATURE_GTM.md](/docs/plans/VIRAL_PLAY_FEATURE_GTM.md) | GTM strategy |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-20 | Initial Play Mode system documentation |
