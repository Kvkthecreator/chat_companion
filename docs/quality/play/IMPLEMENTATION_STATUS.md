# Play Mode Implementation Status

> **Version**: 1.1.0
> **Status**: Living Document
> **Updated**: 2024-12-20

---

## Critical Path Items

### Before Any Content Creation

| Item | Status | Notes |
|------|--------|-------|
| Add 'play' to series_type CHECK constraint | 🔴 Blocked | Migration required |
| Implement `get_evaluation_by_share_id()` | ⚠️ Called but missing | In DirectorService |
| Implement `increment_share_count()` | ⚠️ Called but missing | In DirectorService |

### Content Isolation Verified

The API already filters `series_type = 'play'` from core endpoints:
- `routes/series.py:123` — Default excludes play
- `routes/series.py:809` — Continue suggestions exclude play
- Studio UI already has 'play' as option

**Blocker**: DB CHECK constraint only allows: `standalone`, `serial`, `anthology`, `crossover`

---

## Current State: Flirt Test v1

### What's Implemented

| Component | Status | Location |
|-----------|--------|----------|
| **Backend** | | |
| `EvaluationType.FLIRT_ARCHETYPE` | ✅ Live | `models/evaluation.py` |
| `FLIRT_ARCHETYPES` metadata | ✅ Live | `models/evaluation.py` |
| `FlirtArchetypeResult` model | ✅ Live | `models/evaluation.py` |
| `SessionEvaluation` model | ✅ Live | `models/evaluation.py` |
| `generate_share_id()` | ✅ Live | `models/evaluation.py` |
| `GamesService` | ✅ Live | `services/games.py` |
| Director integration | ✅ Live | `services/director.py` |
| Games API routes | ✅ Live | `routes/games.py` |
| **Database** | | |
| `session_evaluations` table | ✅ Live | Migration 025 |
| `sessions.turn_count` | ✅ Live | Migration 025 |
| `sessions.director_state` | ✅ Live | Migration 025 |
| `episode_templates.completion_mode` | ✅ Live | Migration 025 |
| `episode_templates.turn_budget` | ✅ Live | Migration 025 |
| **Content** | | |
| Flirt Test series (m/f) | ✅ Live | Migration 026 |
| Mina/Alex characters | ✅ Live | Migration 026 |
| Episode template (7 turns) | ✅ Live | Migration 026 |
| **Frontend** | | |
| `/play/flirt-test` (start) | ✅ Live | `web/src/app/play/flirt-test/` |
| `/play/flirt-test/chat` | ✅ Live | `web/src/app/play/flirt-test/chat/` |
| `/play/flirt-test/result` | ✅ Live | `web/src/app/play/flirt-test/result/` |
| `/r/[shareId]` (share page) | ✅ Live | `web/src/app/r/[shareId]/` |
| `FlirtArchetype` types | ✅ Live | `web/src/types/index.ts` |
| `ARCHETYPE_META` (emoji, colors) | ✅ Live | Result components |
| **API Client** | | |
| `api.games.start()` | ✅ Live | `lib/api/client.ts` |
| `api.games.sendMessage()` | ✅ Live | `lib/api/client.ts` |
| `api.games.getResult()` | ✅ Live | `lib/api/client.ts` |
| `api.games.getSharedResult()` | ✅ Live | `lib/api/client.ts` |

### What's Missing for v1 Completion

| Component | Status | Notes |
|-----------|--------|-------|
| `get_evaluation_by_share_id()` | ⚠️ Called but not implemented | In routes, needs DirectorService method |
| `increment_share_count()` | ⚠️ Called but not implemented | In routes, needs DirectorService method |
| OG image generation | 🔴 Not implemented | Static fallback exists |

---

## Target State: Romantic Trope v2

### New Components Required

| Component | Priority | Complexity | Notes |
|-----------|----------|------------|-------|
| **Taxonomy** | | | |
| `RomanticTrope` type | P0 | Low | Replace `FlirtArchetype` |
| `ROMANTIC_TROPES` metadata | P0 | Low | With taglines, descriptions, signals |
| `RomanticTropeResult` model | P0 | Low | With evidence, callback_quote |
| **Content** | | | |
| Hometown Crush series (x2) | P0 | Medium | Male + Female variants |
| Jack character | P0 | Medium | System prompt for trope detection |
| Emma character | P0 | Medium | Female variant |
| Episode templates (x2) | P0 | Low | 7 turns, romantic_trope evaluation |
| **Evaluation** | | | |
| Trope evaluation prompt | P0 | Medium | LLM prompt for classification |
| Evidence generation | P1 | Medium | "Why this fits you" observations |
| Callback quote extraction | P1 | Medium | User's defining moment |
| Signal extraction per turn | P2 | High | Progressive signal detection |
| **Frontend** | | | |
| `/play` landing page | P0 | Medium | List of play experiences |
| `/play/hometown-crush` | P0 | Low | Adapt from flirt-test |
| `TropeResultCard` | P0 | Medium | New design with sections |
| `EvidenceSection` | P1 | Low | "Why this fits you" |
| `CallbackSection` | P1 | Low | "Your moment" |
| `InTheWildSection` | P0 | Low | Cultural references |
| Updated share card | P1 | Medium | New OG image design |
| **Routing** | | | |
| `/play` route | P0 | Low | Landing page |
| `/play/[slug]` dynamic | P0 | Medium | Generic play experience |

---

## Gap Analysis

### 1. Taxonomy Gap

**Current**: 5 Flirt Archetypes (technique-focused)
```
tension_builder, bold_mover, playful_tease, slow_burn, mysterious_allure
```

**Target**: 5 Romantic Tropes (narrative-focused)
```
slow_burn, second_chance, all_in, push_pull, slow_reveal
```

**Migration**:
- Add new `ROMANTIC_TROPES` constant alongside `FLIRT_ARCHETYPES`
- Add `EvaluationType.ROMANTIC_TROPE`
- Keep backward compatibility

### 2. Result Personalization Gap

**Current**: Generic result with archetype + description
```python
{
    "archetype": "slow_burn",
    "confidence": 0.85,
    "primary_signals": ["deep_questions", "patient_pacing"],
    "title": "The Slow Burn",
    "description": "Patient and deliberate..."
}
```

**Target**: Personalized result with evidence + callback
```python
{
    "trope": "slow_burn",
    "confidence": 0.85,
    "primary_signals": ["comfortable_with_pauses", "deep_questions"],
    "evidence": [
        "You didn't rush the silences — you let them breathe",
        "When he pushed, you held your ground",
        "You asked about the past, not just the surface"
    ],
    "callback_quote": "Some things are worth waiting for",
    "title": "The Slow Burn",
    "tagline": "You know the best things take time",
    "description": "You're not in a rush..."
}
```

**Implementation**: Enhanced LLM evaluation prompt

### 3. Content Gap

**Current**: Generic flirt test characters (Mina/Alex)

**Target**: Hometown Crush series with Jack character
- Narrative context (hometown return, second chance energy)
- System prompt optimized for trope detection
- Situation aligned with trope taxonomy

**Implementation**: New series + character + episode template migration

### 4. UI Gap

**Current**: Simple result card
- Emoji + title + description
- Confidence bar
- Signal tags
- Share button

**Target**: Rich result report
- Identity statement (name + tagline)
- Why This Fits You (3 personalized observations)
- Your Moment (callback quote)
- In The Wild (cultural references)
- Enhanced share card

**Implementation**: New React components

### 5. Routing Gap

**Current**: `/play/flirt-test/*`

**Target**:
- `/play` (landing)
- `/play/[slug]` (generic)
- `/play/hometown-crush` (first implementation)

**Implementation**: New Next.js routes with dynamic slugs

---

## Implementation Plan

### Phase 1: Taxonomy Foundation (Backend)

**Scope**: Add trope system alongside existing archetypes

1. Add `ROMANTIC_TROPES` constant to `evaluation.py`
2. Add `EvaluationType.ROMANTIC_TROPE`
3. Add `RomanticTropeResult` model
4. Update TypeScript types

**Files**:
- `substrate-api/.../models/evaluation.py`
- `web/src/types/index.ts`

### Phase 2: Content Creation (Database)

**Scope**: Create Hometown Crush series

1. Create migration for Hometown Crush series
2. Create Jack character with trope-detection prompt
3. Create episode template (7 turns, romantic_trope)

**Files**:
- `supabase/migrations/XXX_hometown_crush_content.sql`

### Phase 3: Evaluation Enhancement (Backend)

**Scope**: Personalized evaluation generation

1. Create trope evaluation prompt
2. Add evidence generation to evaluation
3. Add callback quote extraction
4. Update DirectorService.generate_evaluation()

**Files**:
- `substrate-api/.../services/director.py`

### Phase 4: Frontend Foundation

**Scope**: New routes and basic UI

1. Create `/play` landing page
2. Create `/play/[slug]` dynamic route
3. Adapt existing chat flow for hometown-crush
4. Create basic TropeResultCard

**Files**:
- `web/src/app/play/page.tsx`
- `web/src/app/play/[slug]/page.tsx`
- `web/src/app/play/[slug]/chat/page.tsx`
- `web/src/app/play/[slug]/result/page.tsx`
- `web/src/components/play/TropeResultCard.tsx`

### Phase 5: Result Report Enhancement

**Scope**: Full result report UI

1. Create EvidenceSection component
2. Create CallbackSection component
3. Create InTheWildSection component
4. Update share functionality

**Files**:
- `web/src/components/play/EvidenceSection.tsx`
- `web/src/components/play/CallbackSection.tsx`
- `web/src/components/play/InTheWildSection.tsx`

### Phase 6: Polish & Launch

**Scope**: OG images, testing, launch

1. Create/update OG images for tropes
2. Test full flow end-to-end
3. Update share page for tropes
4. Launch at `/play`

---

## Backward Compatibility

### Preserved

- `/play/flirt-test` continues to work
- `evaluation_type: "flirt_archetype"` supported
- Existing share links functional
- API contracts unchanged

### Deprecated (Not Removed)

- `FlirtArchetype` type (keep for existing results)
- `FLIRT_ARCHETYPES` constant (keep for display)
- `/play/flirt-test` routes (keep functional)

---

## Open Questions

1. **Content**: Who writes Jack's system prompt?
2. **OG Images**: Static per trope or dynamic generation?
3. **Analytics**: What events to track for viral metrics?
4. **A/B Testing**: Run flirt-test vs hometown-crush in parallel?

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-20 | Initial implementation status |
