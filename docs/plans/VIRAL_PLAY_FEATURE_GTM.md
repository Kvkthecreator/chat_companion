# Viral Play Feature — GTM Strategy

> **Status**: Planning
> **Created**: 2024-12-18
> **Domain**: ep-0.com
> **Purpose**: Document the strategic rationale and architectural decisions for a viral, shareable feature as a customer acquisition channel.

---

## Executive Summary

Instead of traditional marketing spend (ads → landing page → conversion funnel), build a **viral feature** that organically pulls users into the Fantazy ecosystem. The feature is a "trojan horse" — a standalone, shareable experience that creates awareness and drives core service discovery.

**Core Example**: "Are you a good flirt?" — a conversation-based personality test that produces shareable results.

---

## Strategic Rationale

### Why This Over Traditional Marketing

| Traditional Marketing | Viral Feature |
|-----------------------|---------------|
| Requires: creative iteration, A/B testing, ad platform learning, budget | Requires: what we already build, but constrained |
| Predictable spend-to-impression ratio | Unpredictable virality (could flop or explode) |
| Builds brand awareness deliberately | Builds awareness through product experience |
| Message control | User-generated context around shares |

**Key Insight**: The feature *is* the product demo. Users experience the core value proposition (AI conversation) before ever seeing the main product.

### Alignment with Fantazy's DNA

- We're already in the business of creating emotionally resonant, conversation-based experiences
- A "flirt test" is a *constrained episode* — existing infrastructure applies
- Episode-0 philosophy (cold open, dramatic tension, reply gravity) transfers directly

### Virality Mechanics

- **Identity-based results**: "You're a Slow Burn Romantic" vs "Chaotic Flirt Energy"
- **Social comparison**: "I got 87%, what did you get?"
- **Low commitment**: 2-3 minute test vs full episode
- **Screenshot-friendly**: Result cards optimized for sharing

---

## Architectural Decisions

### 1. Domain Strategy

**Decision**: Route (`ep-0.com/games/flirt-test`)

**Rejected Alternative**: Subdomain (`games.ep-0.com`)

**Reasoning**:
- **SEO**: Routes inherit parent domain authority. Subdomains are treated as separate sites.
- **Infrastructure**: No additional SSL/cert management, no separate deployment config.
- **User Mental Model**: `/games/X` signals "part of ep-0" — supports awareness goal.
- **Future Extensibility**: `/games/` becomes the namespace for all viral/challenge features (`/games/mystery-challenge`, `/games/compatibility`).
- **Kill Switch**: Delete a route, done. No DNS cleanup.

**URL Structure**:
```
ep-0.com/games/flirt-test     → Take the test
ep-0.com/r/abc123             → View/share result (short URL)
```

### 2. Authentication Model

**Decision**: Anonymous first, account optional

**Industry Benchmark**:
| Service | Auth Model |
|---------|------------|
| 16personalities (MBTI) | No auth. Email optional for "save results" |
| BuzzFeed quizzes | No auth. Share directly |
| "Which character are you" tests | No auth, instant result |

**Flow**:
```
Take test → Get result → Share
                ↓
         Optional: "Save to your profile" (creates account)
                ↓
         Optional: "Keep chatting with [Character]" (creates account)
```

**Why This Works**:
- Maximum top-of-funnel (no drop-off at auth wall)
- Result is the hook; account creation is the upsell
- Capture intent signal without auth (analytics on result type, share rate)
- Those who convert are higher intent

**Implementation**: Generate session token for anonymous users. If they create account, link result to new `user_id`.

### 3. Result Persistence

**Decision**: Permanent shareable links, ephemeral conversation data

**Industry Benchmark**:
| Service | Persistence |
|---------|-------------|
| 16personalities | Permanent |
| BuzzFeed | Permanent |
| Spotify Wrapped | Annual refresh |

**Reasoning**:
- Shares have long tails — link discovered months later should work
- Storage cost is trivial (small JSON per result)
- Link rot on viral content is brand damage
- Evergreen SEO value from inbound links

**Data Retention**:
- **Result**: Permanent (archetype, score, metadata)
- **Conversation Transcript**: Expire after 30 days for anonymous users

### 4. Conversion Funnel

**Primary CTA**: Character Continuity
> "You talked to Mina for 2 minutes. She has more to say."
> [Continue conversation with Mina →]

This leverages the relationship seed — they've already "met" the character.

**Secondary CTA**: Series Discovery (Archetype-Matched)

Rather than showing individual characters, surface **series** that match the user's result archetype. Series are the primary content unit in ep-0 — each has:
- A **title** and **tagline** (hook)
- A **genre** (romantic_tension, thriller, etc.)
- **Cover art** for visual appeal
- **Episode count** for depth signal

> "Stories for Tension Builders like you:"
> [Series cards with cover, title, tagline, genre badge]

This aligns with the episode-first, series-based architecture and introduces users to the content model they'll engage with.

**Result Screen Layout**:
```
┌─────────────────────────────────────────┐
│  YOUR RESULT: The Tension Builder       │
│  "You know exactly when to pause..."    │
│                                         │
│  [Share Result]  [Save to Profile]      │
│                                         │
├─────────────────────────────────────────┤
│  Mina enjoyed that. Keep going?         │
│  [Continue with Mina →]                 │
│                                         │
│  Stories for Tension Builders:          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Series  │ │ Series  │ │ Series  │   │
│  │ cover   │ │ cover   │ │ cover   │   │
│  │ +title  │ │ +title  │ │ +title  │   │
│  │ +genre  │ │ +genre  │ │ +genre  │   │
│  └─────────┘ └─────────┘ └─────────┘   │
└─────────────────────────────────────────┘
```

**Why This Works**:
- Primary CTA is specific and emotionally warm (character continuity)
- Secondary CTA introduces the series model naturally
- Series cards (cover + tagline + genre) are visually compelling
- Both require account creation to proceed (natural gate)
- The test *was* the demo — they know what "chatting" feels like

---

## Technical Architecture

### Isolation Strategy

**Pattern**: Separate domain tables, shared infrastructure (Pattern A)

**Principle**: Don't pollute core canon tables (`sessions`, `engagements`, `memory`).

**New Tables**:
- `game_sessions` — Runtime state for play features
- `game_results` — Shareable outcomes with permanent links

**Shared Infrastructure**:
- Supabase auth
- Conversation engine
- Character data (read-only reference)

**Kill Switch**: Drop tables, remove route. Core service unaffected.

### Proposed Schema

```sql
-- Game sessions (isolated from core sessions)
CREATE TABLE game_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_type TEXT NOT NULL,  -- 'flirt-test', 'mystery-challenge', etc.
  character_id UUID REFERENCES characters(id),
  user_id UUID REFERENCES auth.users(id),  -- nullable for anonymous
  anonymous_token TEXT,  -- for anonymous users
  conversation JSONB,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Game results (permanent, shareable)
CREATE TABLE game_results (
  id TEXT PRIMARY KEY,  -- short hash for URL (e.g., 'abc123')
  game_session_id UUID REFERENCES game_sessions(id),
  game_type TEXT NOT NULL,
  result_archetype TEXT NOT NULL,
  result_metadata JSONB,  -- scores, character used, etc.
  user_id UUID REFERENCES auth.users(id),  -- nullable, linked on account creation
  created_at TIMESTAMPTZ DEFAULT NOW(),
  share_count INT DEFAULT 0
);
```

### Share Infrastructure (Reusable Primitive)

This is **platform infrastructure**, not one-off work. Will be reused for:
- Game/test results
- "Share this episode moment" (future)
- Series completion badges
- Character compatibility results

**Components**:
| Component | Purpose |
|-----------|---------|
| Result artifact | Structured data (archetype, score, metadata) |
| Result card renderer | OG image generation for social previews |
| Share link with state | `ep-0.com/r/abc123` → resolves to result |
| Comparison flow | "Take the same test to compare" |
| Attribution | Who shared, conversion tracking |

---

## Canon Extension: Episode Modes

This feature surfaces a need to extend Episode Dynamics Canon.

### Current Philosophy vs. New Consideration

| Current | New |
|---------|-----|
| Open improvisation | Guided/gated progression |
| No defined end | Defined resolution |
| Freedom to explore | Objective to reach |

### Proposed Episode Modes

```
mode: "open"        → Current default (romantic tension, slice of life)
mode: "guided"      → Soft beats, flexible resolution (most series)
mode: "structured"  → Gated progression, defined checkpoints (mystery, thriller)
mode: "challenge"   → Time/turn limited, scored outcome (games, tests)
```

**Flirt Test** = `mode: "challenge"`
**Knives Out Mystery Episode** = `mode: "structured"`

This doesn't break canon — it extends the Episode Dynamics framework.

**New Fields on Episode Templates** (future):
- `episode_mode` (enum)
- `progression_gates` (for structured mode)
- `scoring_criteria` (for challenge mode)

---

## Platform Primitives Unlocked

```
┌─────────────────────────────────────────────────────────────┐
│                     PLATFORM PRIMITIVES                      │
├─────────────────────────────────────────────────────────────┤
│  Conversation Engine  │  Share System  │  Episode Modes     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   Core Service          Play/Games            Future Series
   (Episodes)         (Flirt Test, etc.)    (Mystery, Thriller)
   mode: open/guided   mode: challenge       mode: structured
```

**Key Insight**: The viral feature isn't a distraction — it forces building primitives (share system, episode modes) that the core product needs anyway.

---

## Open Questions for Implementation

> **Note**: Items 1-4 are aligned and decided. Remaining questions below.

1. **Result Archetype System**: What archetypes? How scored from conversation?
2. **Share Card Design**: OG image generation requirements, visual style
3. **Character Selection**: Which character(s) for launch? Mina? New character?
4. **Conversation Length**: Optimal turn count for engagement vs. completion rate
5. **Scoring Logic**: LLM-based evaluation? Explicit criteria?

---

## Success Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Test completion rate | >70% | Of those who start |
| Share rate | >30% | Of those who complete |
| Click-through on shared links | >20% | Recipients who take test |
| Account creation | >10% | Of test completers |
| Core service trial | >5% | Of account creators |

---

## Next Steps

1. Finalize archetype system design
2. Design share card visual format
3. Schema implementation (`game_sessions`, `game_results`)
4. Share link infrastructure
5. Conversation flow design (character, prompts, turn limit)
6. OG image generation service
7. Frontend implementation (`/games/` routes)
8. Analytics integration

---

## References

- [EPISODE_DYNAMICS_CANON.md](../EPISODE_DYNAMICS_CANON.md) — Session states, guided improvisation
- [CONTENT_ARCHITECTURE_CANON.md](../CONTENT_ARCHITECTURE_CANON.md) — Two-layer architecture
- [EPISODES_CANON_PHILOSOPHY.md](../EPISODES_CANON_PHILOSOPHY.md) — Episode philosophy