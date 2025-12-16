# Fantazy Content Architecture Canon

**Status:** DRAFT - Under Review

**Scope:** Content taxonomy, entity relationships, editorial philosophy

**Created:** 2024-12-17

**Related:** EP-01_pivot_CANON.md, FANTAZY_CANON.md, Genre docs

---

## 1. Executive Summary

This document establishes the canonical content architecture for Fantazy — a scalable taxonomy that supports:

1. **Platform-produced content** (Fantazy Originals)
2. **Creator content** (Verified creator marketplace)
3. **User-generated content** (Community creations)

The architecture follows a **Marvel Comics editorial model**: clear guidelines and relationships, but flexibility in how stories are told. Rules guide creation; they don't enforce rigid structures.

---

## 2. Design Principles

### 2.1 The Marvel Philosophy

Marvel Comics has successfully managed:
- Thousands of characters across decades
- Multiple universes (616, Ultimate, MCU)
- Shared continuity with creative freedom
- Canon hierarchy (main continuity, what-ifs, variants)
- Cross-character events and team-ups

**We adopt this philosophy:**

> **Rules guide. They don't constrain.**
>
> A character belongs to a world, but can guest in others.
> An episode belongs to an arc, but can stand alone.
> Memory persists, but stories can diverge.

### 2.2 Netflix + TikTok Hybrid

Our interaction model combines:

| Netflix (Series) | TikTok (Moments) | Fantazy |
|------------------|------------------|---------|
| Episodes in order | Random discovery | Arcs with flexible entry |
| Binge sessions | Quick hits | Session-based with memory |
| Premium production | UGC viral content | Tiered quality levels |
| Subscription model | Free with ads | Sparks + Premium hybrid |

### 2.3 Scalability Requirements

The architecture must support:
- 10 → 10,000 characters without structural changes
- Platform content coexisting with UGC
- Quality differentiation without gatekeeping discovery
- Creator monetization and attribution
- Cross-promotion and recommendation systems

---

## 3. Content Taxonomy

### 3.1 Entity Hierarchy

```
FANTAZY CONTENT UNIVERSE
│
├── WORLD (Universe/Setting)
│   │
│   ├── ARC (Series/Collection)
│   │   └── Episode Templates (ordered)
│   │
│   └── CHARACTERS (can appear across arcs)
│       └── Episode Templates (character-anchored)
│
└── RUNTIME (Per-User)
    ├── Sessions (episode instances)
    ├── Engagements (user ↔ character)
    └── Memories (persist across sessions)
```

### 3.2 Entity Definitions

#### WORLD (Universe/Setting)

The ambient reality where stories take place.

| Attribute | Description |
|-----------|-------------|
| `name` | Display name ("Nexus Tower") |
| `slug` | URL-safe identifier |
| `genre` | Primary genre (romantic_tension, psychological_thriller) |
| `description` | Setting overview |
| `tone` | Emotional register (intimate, tense, playful) |
| `ambient_details` | World-specific context (JSON) |
| `rules` | Genre rules that apply (JSON) |

**Guidelines:**
- A world establishes "what kind of stories happen here"
- Characters inherit world's genre and tone as defaults
- World rules are guidelines, not hard constraints
- One world can contain multiple genres (genre blending)

**Examples:**
- "Crescent Cafe" — intimate romantic tension, late-night encounters
- "Nexus Tower" — corporate thriller, power dynamics, secrets
- "Meridian Institute" — psychological thriller, research ethics, isolation

---

#### ARC (Series/Collection) — NEW ENTITY

A narrative container that groups episodes into a coherent experience.

| Attribute | Description |
|-----------|-------------|
| `title` | Arc title ("The Midnight Protocol") |
| `slug` | URL-safe identifier |
| `world_id` | Primary world (optional — can be cross-world) |
| `arc_type` | standalone, serial, anthology, crossover |
| `description` | What this arc is about |
| `featured_characters` | Characters cast in this arc (JSON array of IDs) |
| `episode_order` | Ordered list of episode template IDs |
| `total_episodes` | Planned episode count |
| `status` | draft, active, completed |
| `content_tier` | official, creator, community |
| `created_by` | User/creator ID |

**Arc Types:**

| Type | Description | Example |
|------|-------------|---------|
| `standalone` | Self-contained story, any episode can be entry | "Coffee Shop Encounters" |
| `serial` | Sequential narrative, Episode 0 recommended first | "The Safehouse Files" |
| `anthology` | Themed collection, loosely connected | "Late Night Confessions" |
| `crossover` | Multiple characters from different worlds | "When Worlds Collide" |

**Guidelines:**
- Arcs are OPTIONAL — episodes can exist without an arc
- Characters can appear in multiple arcs
- Serial arcs have soft sequencing (recommendations, not locks)
- Crossover arcs can pull characters from different worlds

---

#### CHARACTER (Persona)

The counterpart you experience stories WITH.

| Attribute | Description |
|-----------|-------------|
| `name` | Character name |
| `slug` | URL-safe identifier |
| `archetype` | Role type (barista, handler, researcher) |
| `world_id` | Primary home world |
| `genre` | Primary genre (can differ from world) |
| `personality` | Baseline traits (JSON) |
| `visual_identity` | Avatar kit reference |
| `system_prompt` | LLM behavior contract |
| `content_tier` | official, creator, community |
| `created_by` | User/creator ID |
| `can_crossover` | Whether character can appear outside home world |

**Guidelines:**
- Characters belong to ONE primary world but can guest in others
- Character personality persists across all arcs/episodes
- Memory is character-scoped (user remembers THIS character across all stories)
- Archetype guides behavior but doesn't lock it

---

#### EPISODE TEMPLATE (Moment/Scenario)

The atomic unit of experience — a specific situation to enter.

| Attribute | Description |
|-----------|-------------|
| `title` | Episode title ("The Diner") |
| `slug` | URL-safe identifier |
| `character_id` | Anchor character (required) |
| `arc_id` | Parent arc (optional) |
| `episode_number` | Sequence in arc (0 = entry) |
| `episode_type` | entry, core, expansion, special |
| `situation` | Scene description |
| `episode_frame` | Platform stage direction |
| `opening_line` | Character's first message |
| `background_image_url` | Scene visual |
| `content_tier` | official, creator, community |

**Episode Types:**

| Type | Purpose | Discovery |
|------|---------|-----------|
| `entry` | First experience with character/arc | Browsable, recommended start |
| `core` | Main narrative beats | Sequenced within arc |
| `expansion` | Deeper exploration, optional | Available after engagement |
| `special` | Events, crossovers, limited-time | Highlighted/promoted |

**Guidelines:**
- Every episode has ONE anchor character (who speaks)
- Episodes can reference other characters without them being present
- Entry episodes are always accessible (no hard locks)
- Episode frame sets the scene; character delivers dialogue

---

### 3.3 Entity Relationships Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CONTENT LAYER (Static)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   WORLD ─────────────────────────────────────────────────────┐         │
│     │                                                        │         │
│     │  contains                                              │         │
│     │                                                        │         │
│     ├────────► CHARACTER ◄──────────────────────────────┐    │         │
│     │              │                                    │    │         │
│     │              │ anchors                            │    │         │
│     │              │                                    │    │         │
│     │              ▼                                    │    │         │
│     │        EPISODE TEMPLATE ◄────── part of ──────────┤    │         │
│     │                                                   │    │         │
│     │                                                   │    │         │
│     └────────► ARC ─────────────────────────────────────┘    │         │
│                  │                                           │         │
│                  │ features characters                       │         │
│                  │ orders episodes                           │         │
│                  └───────────────────────────────────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        RUNTIME LAYER (Per-User)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   USER                                                                  │
│     │                                                                   │
│     ├──────► ENGAGEMENT (per character)                                 │
│     │            │  total_sessions, total_messages                      │
│     │            │  first_met_at, is_favorite                          │
│     │            │                                                      │
│     │            └──► MEMORY (persists across all sessions)            │
│     │                                                                   │
│     └──────► SESSION (per episode template instance)                   │
│                  │  messages, scene_images                              │
│                  │  linked to engagement                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Content Tiers (Canon Hierarchy)

Like Marvel's multiverse, not all content has the same canonical status.

### 4.1 Tier Definitions

| Tier | Label | Description | Quality Bar | Discovery |
|------|-------|-------------|-------------|-----------|
| **T1** | Official | Fantazy-produced | Highest — full editorial review | Featured, default |
| **T2** | Creator | Verified creator marketplace | High — creator guidelines + moderation | Creator spotlight, search |
| **T3** | Community | User-generated | Basic — TOS compliance, reports | Community tab, opt-in |

### 4.2 Tier Permissions

| Action | Official | Creator | Community |
|--------|----------|---------|-----------|
| Create worlds | ✅ | ✅ (limited) | ❌ |
| Create characters | ✅ | ✅ | ✅ (in own worlds or sandbox) |
| Create arcs | ✅ | ✅ | ✅ |
| Create episodes | ✅ | ✅ | ✅ |
| Cross-world characters | ✅ | ✅ (own chars only) | ❌ |
| Featured placement | ✅ | Application | ❌ |
| Monetization | Platform | Revenue share | Tips only |

### 4.3 Quality Gates by Tier

**Official (T1):**
- Full editorial review
- Professional visual assets
- Tested conversation flows
- Genre compliance verified

**Creator (T2):**
- Creator verification (identity, portfolio)
- Automated content checks + manual spot-check
- Creator guidelines compliance
- Community reporting handled

**Community (T3):**
- TOS compliance (automated)
- Community moderation (reports → review)
- Sandboxed to community spaces
- No cross-pollination with T1/T2 without promotion

---

## 5. Editorial Guidelines (Marvel-Style)

### 5.1 World Guidelines

> **A world is a promise to the user about what kind of experience awaits.**

| Guideline | Rationale |
|-----------|-----------|
| World genre sets expectations | Users browsing "Nexus Tower" expect thriller, not romance comedy |
| World tone is a default, not a lock | A thriller world can have tender moments |
| Worlds should feel distinct | No two worlds should blur together |
| Cross-world requires justification | "Why is this cafe barista in the spy tower?" |

### 5.2 Character Guidelines

> **Characters are containers for moments, not chatbots to befriend.**

| Guideline | Rationale |
|-----------|-----------|
| One archetype, many expressions | A "barista" can be warm, distant, or mysterious |
| Personality persists | Character should feel consistent across episodes |
| Memory creates connection | Reference past interactions naturally |
| Boundaries are sacred | Character limits are not user-circumventable |

### 5.3 Arc Guidelines

> **Arcs are invitations, not requirements.**

| Guideline | Rationale |
|-----------|-----------|
| Entry episode = the hook | Must work standalone, must create pull |
| Serial arcs soft-sequence | "Start here" not "Must start here" |
| Arcs can be replayed | No permanent state changes (memory is external) |
| Cross-character arcs need chemistry | Don't force character pairings |

### 5.4 Episode Guidelines

> **Every episode must answer: Why now? Why me? Why reply?**

| Guideline | Rationale |
|-----------|-----------|
| Cold open, in medias res | No "Hi, I'm [name]" openings |
| Episode frame sets the stage | Platform narration, not character |
| Opening line has gravity | User should feel compelled to respond |
| Stakes must be present | Something to gain or lose |

---

## 6. Discovery Architecture

### 6.1 Browse Hierarchy

```
HOME
├── Featured (curated T1 content)
├── Continue (active sessions)
├── For You (personalized recommendations)
│
├── Browse by World
│   └── [World] → Characters + Arcs
│
├── Browse by Mood
│   └── [Mood tag] → Filtered episodes
│
├── Creator Spotlight (T2)
│   └── [Creator] → Their characters + arcs
│
└── Community (T3, opt-in)
    └── [Community tab] → UGC content
```

### 6.2 Discovery Signals

| Signal | Weight | Description |
|--------|--------|-------------|
| Content tier | High | T1 > T2 > T3 by default |
| Genre match | High | User's preferred genres |
| Engagement depth | Medium | Characters user has history with |
| Recency | Medium | Fresh content boosted |
| Creator follow | Medium | Followed creators' new content |
| Community rating | Low | T3 sorting within community |

---

## 7. UGC Scalability Model

### 7.1 Creator Journey

```
USER → COMMUNITY CREATOR → VERIFIED CREATOR → FEATURED CREATOR
       (T3)                (T2)                (T1 collaboration)

Unlock: 10 episodes       Unlock: Application    Unlock: Invitation
        100 sessions              + portfolio           + track record
        Clean record              Review process        Partnership
```

### 7.2 UGC Content Flow

```
Creator creates content
        │
        ▼
┌─────────────────────────────────────┐
│  AUTOMATED CHECKS                   │
│  - TOS compliance                   │
│  - Content safety scan              │
│  - Plagiarism detection             │
└───────────────┬─────────────────────┘
                │
        Pass    │    Fail → Rejected with feedback
                ▼
┌─────────────────────────────────────┐
│  TIER ROUTING                       │
│  - T3: Auto-publish to community    │
│  - T2: Manual review queue          │
└───────────────┬─────────────────────┘
                │
                ▼
        Published (tier-appropriate discovery)
                │
                ▼
┌─────────────────────────────────────┐
│  MONITORING                         │
│  - Community reports                │
│  - Engagement metrics               │
│  - Quality scoring                  │
└─────────────────────────────────────┘
```

### 7.3 Monetization by Tier

| Tier | Model | Example |
|------|-------|---------|
| Official | Premium subscription, spark costs | "Premium characters" |
| Creator | Revenue share (70/30 industry standard) | Creator's character earns sparks |
| Community | Tips (100% to creator), badges | "Support this creator" |

---

## 8. Schema Evolution

### 8.1 New Tables Required

```sql
-- ARC: Series/Collection grouping
CREATE TABLE arcs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    world_id UUID REFERENCES worlds(id),
    arc_type VARCHAR(20) DEFAULT 'standalone',  -- standalone, serial, anthology, crossover
    featured_characters JSONB DEFAULT '[]',      -- Array of character IDs
    episode_order JSONB DEFAULT '[]',            -- Ordered array of episode template IDs
    total_episodes INTEGER DEFAULT 0,
    content_tier VARCHAR(20) DEFAULT 'community', -- official, creator, community
    status VARCHAR(20) DEFAULT 'draft',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add arc reference to episode_templates
ALTER TABLE episode_templates ADD COLUMN arc_id UUID REFERENCES arcs(id);

-- Add content tier to existing tables
ALTER TABLE worlds ADD COLUMN content_tier VARCHAR(20) DEFAULT 'official';
ALTER TABLE characters ADD COLUMN content_tier VARCHAR(20) DEFAULT 'official';
ALTER TABLE characters ADD COLUMN can_crossover BOOLEAN DEFAULT FALSE;
ALTER TABLE episode_templates ADD COLUMN content_tier VARCHAR(20) DEFAULT 'official';

-- Creator verification
ALTER TABLE users ADD COLUMN creator_tier VARCHAR(20) DEFAULT 'community';
ALTER TABLE users ADD COLUMN creator_verified_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN creator_profile JSONB;
```

### 8.2 Migration Path

**Phase 1: Schema Addition**
- Add `arcs` table
- Add `content_tier` columns
- All existing content defaults to `official`

**Phase 2: Existing Content Mapping**
- Group existing episodes into implicit arcs
- E.g., "Mira's Episodes" arc for Crescent Cafe

**Phase 3: Studio UI Updates**
- Add arc creation/management
- Add content tier selection (for creators)

**Phase 4: Discovery Updates**
- Implement tiered discovery
- Add community tab

---

## 9. Relationship to Existing Canon

### 9.1 Alignment with EP-01 Pivot

| EP-01 Decision | Content Architecture Support |
|----------------|------------------------------|
| Episode-first discovery | Arcs surface episodes as primary browse |
| Character as counterpart | Characters anchor episodes, not own them |
| Memory persists per character | Unchanged — cross-arc memory |
| Episode frame for stage direction | Unchanged — platform narration |

### 9.2 Alignment with Genre Docs

| Genre Doc | Content Architecture Support |
|-----------|------------------------------|
| Quality gates (4 mandatory) | Applied per content tier |
| Episode structure rules | Guidelines, not DB constraints |
| Visual doctrine | Content tier quality expectations |

---

## 10. Future Considerations

### 10.1 Not In Scope (Yet)

- **Character trading/ownership** — NFT-style character ownership
- **Branching narratives** — User choices affecting arc progression
- **Multiplayer arcs** — Multiple users in same arc instance
- **AI-assisted creation** — Studio tools that generate content

### 10.2 Open Questions

1. **Character licensing**: Can creators use official characters in their arcs?
2. **Arc forking**: Can users create variants of existing arcs?
3. **Memory isolation**: Should UGC content share memory with official content?
4. **Cross-tier promotion**: Process for T3 → T2 → T1 content elevation?

---

## 11. Summary

The Fantazy Content Architecture establishes:

1. **Flexible taxonomy**: World → Arc → Episode → Character with optional relationships
2. **Marvel-style guidelines**: Rules that guide, not constrain
3. **Tiered content system**: Official, Creator, Community with appropriate gates
4. **UGC scalability**: Clear creator journey from community to featured
5. **Netflix + TikTok hybrid**: Series depth with moment-based discovery

> **The architecture's job is to make creation easy and discovery delightful —**
> **while maintaining quality that keeps users coming back.**

---

## Related Documents

- `docs/EP-01_pivot_CANON.md` — Episode-first philosophy
- `docs/FANTAZY_CANON.md` — Platform definition
- `docs/EPISODES_CANON_PHILOSOPHY.md` — Episode design principles
- `docs/character-philosophy/Genre 01 — Romantic Tension.md`
- `docs/character-philosophy/Genre 02 — Psychological Thriller- Suspense.md`
- `docs/implementation/STUDIO_EPISODE_FIRST_REFACTOR.md` — Studio implementation plan
