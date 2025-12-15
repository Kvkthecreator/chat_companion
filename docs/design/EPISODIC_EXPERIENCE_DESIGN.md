# Episodic Experience Design

## Document Purpose

This document captures the strategic evolution from "character chat" to "episodic interactive fiction" for Fantazy Studio. It includes the reasoning journey, conceptual frameworks, and implementation plan.

**Date:** 2025-12-15
**Status:** Design Complete, Implementation Pending

---

## Part 1: How We Got Here

### The Initial Problem

Fantazy's Discover grid felt "off" compared to competitors like BabeChat. Initial diagnosis pointed to visual quality - avatars lacked desire framing, role clarity, and consistent style.

### The First Solution: Desire Framing

We upgraded the avatar generation pipeline with:
- **Role Frame** → wardrobe/setting/pose mapping
- **Archetype** → expression/mood mapping
- **Flirting Level** → intimacy calibration (gaze, body language)
- **Style Lock** → consistent high-quality anime output

This improved visual appeal but something still felt missing.

### The Deeper Insight

> "Desire isn't just skin. Desire is a moment."

BabeChat's strength isn't just attractive avatars - it's that thumbnails + taglines drop users into a **specific fantasy moment** immediately. The visual and narrative work together.

### The 4-Ingredient Framework

Analysis revealed that strong "cold opens" have four ingredients:

| Ingredient | Question | Example |
|------------|----------|---------|
| **WHERE** | Micro-setting? | "Last call at a quiet bar, rain outside" |
| **TRIGGER** | What just happened? | "She just caught you staring" |
| **STAKES** | What's at risk? | "You've been dancing around this for weeks" |
| **WHY YOU** | Why is user implicated? | "You told yourself you'd say something tonight" |

Our existing opening_situations had WHERE but often lacked TRIGGER, STAKES, and WHY YOU.

### The Synthesis: Episode Frame

The key insight was that **avatar and cold open should be the same fantasy**. If the cold open describes a rainy bar at midnight, the avatar should feel like a still frame from that moment.

This led to the concept of `episode_frame` - a mood/setting hint derived from the narrative that informs visual generation.

### The Evolution: From Moment to Menu

The final evolution came from recognizing that a single cold open limits the fantasy to one scenario per character.

> "What if we actually had pre-scaffolded episodes (2-3 for now, each)... the user can also opt in to select a specific episode to chat?"

This transforms the product from "chat with a character" to "step into a story" - an interactive episodic experience.

---

## Part 2: Conceptual Framework

### Core Concept: Characters as Mini-Series

Each character becomes a **mini-series** with multiple entry points:

```
Kai (Neighbor)
├── Episode 0: "The Hallway" (Cold Open - first meeting)
├── Episode 1: "Borrowed Sugar" (late night knock)
├── Episode 2: "Power Outage" (stuck together)
└── Episode 3: "The Party" (her place, finally)
```

### Terminology Lock

| Term | Definition | Code Touchpoint |
|------|------------|-----------------|
| **Conversation Ignition** | The system for producing openings | Service/generation logic |
| **Cold Open** | The output (human concept) | What we optimize for |
| **Opening Beat** | Data fields storing the cold open | `situation`, `opening_line` |
| **Episode** | A specific scenario/moment | `episodes` table |
| **Episode 0** | Default cold open (first meeting) | Default episode |
| **Episode Frame** | Visual mood derived from episode | For image generation |

### Episode Structure

Each episode contains:

```yaml
Episode:
  number: 0-N
  title: "Human-readable name"

  # The Cold Open (4 ingredients)
  situation: |
    WHERE: Micro-setting description
    TRIGGER: What just happened
    STAKES: What's at risk emotionally
    WHY YOU: User's implication in the moment

  opening_line: "First message from character"

  # Visual Elements
  background_image_url: "Scene image for chat"
  episode_frame: "Mood/setting for visual generation"

  # Narrative Guidance (soft waypoints)
  arc_hints:
    - beat_1: "Initial tension/setup"
    - beat_2: "Escalation/vulnerability"
    - beat_3: "Peak moment"
    - resolution: "How it tends to land"
```

### Arc Hints Philosophy

**Decision:** Use soft attractors, not forced beats.

Arc hints are **probabilistic waypoints** - the conversation tends toward them but doesn't force them. Think of them as:
- Narrative gravity wells
- Probable emotional destinations
- Quality guardrails for satisfying arcs

The AI considers these hints when generating responses but prioritizes:
1. User agency (their choices matter)
2. Character consistency (stays in voice)
3. Boundary respect (never exceeds limits)
4. Natural flow (doesn't feel scripted)

Implementation: Arc hints are injected into the system prompt as "this scenario tends toward X" rather than "you must reach X."

### Visual Layers

The chat experience has three visual layers:

```
┌─────────────────────────────────────────────────┐
│ LAYER 1: Background Image (episode-specific)    │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░ Scene: dim hallway, phone flashlights ░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│                                                 │
│ LAYER 2: Character Avatar (expression varies)   │
│              ┌─────────┐                        │
│              │ [Kai]   │                        │
│              │ nervous │                        │
│              └─────────┘                        │
│                                                 │
│ LAYER 3: Message UI                             │
│ ┌─────────────────────────────────────────────┐ │
│ │ "*bumps into you* Oh! Is that you from 4B?" │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**Decision:** Background images are static per episode (not changing within episode).

Rationale:
- Simpler to implement
- Consistent visual anchor
- Expressions on avatar provide dynamism
- Can add multi-scene backgrounds as v2

---

## Part 3: Data Model

### New Table: episodes

```sql
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,

    -- Episode identity
    episode_number INT NOT NULL DEFAULT 0,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,

    -- Cold Open content (4 ingredients as natural prose)
    situation TEXT NOT NULL,
    opening_line TEXT NOT NULL,

    -- Visual elements
    background_image_url TEXT,
    episode_frame TEXT,  -- Derived mood for image generation

    -- Narrative guidance
    arc_hints JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,  -- Episode 0 = default
    sort_order INT DEFAULT 0,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived')),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(character_id, episode_number),
    UNIQUE(character_id, slug)
);

-- Indexes
CREATE INDEX idx_episodes_character ON episodes(character_id);
CREATE INDEX idx_episodes_status ON episodes(status);
CREATE INDEX idx_episodes_default ON episodes(character_id, is_default) WHERE is_default = TRUE;
```

### Migration: Existing Data

Current `opening_situation` and `opening_line` on characters become Episode 0:

```sql
-- Migrate existing openings to episodes table
INSERT INTO episodes (
    character_id, episode_number, title, slug,
    situation, opening_line,
    is_default, status
)
SELECT
    id, 0, 'First Meeting', 'first-meeting',
    opening_situation, opening_line,
    TRUE, 'active'
FROM characters
WHERE opening_situation IS NOT NULL;
```

### Conversation Reference

Update conversations to reference episode:

```sql
ALTER TABLE conversations
ADD COLUMN episode_id UUID REFERENCES episodes(id);

-- Index for episode-based queries
CREATE INDEX idx_conversations_episode ON conversations(episode_id);
```

### Character Table Changes

After migration, `opening_situation` and `opening_line` become redundant on characters. Options:

1. **Keep for backwards compatibility** - Episode 0 syncs to these fields
2. **Deprecate** - Remove after migration, always use episodes

**Decision:** Keep for now, sync Episode 0's data to character fields for backwards compatibility with existing code paths.

---

## Part 4: Episode Content Design

### Scope Decision

**Decision:** 3 episodes per character for initial calibration.

- Episode 0: First Meeting (migrated from current cold open, enhanced)
- Episode 1: Relationship Shift (something changes between you)
- Episode 2: Tension Peak (high-stakes moment)

Rationale:
- 10 characters × 3 episodes = 30 episodes (manageable)
- Covers the key narrative moments users want
- Can expand to 4-5 episodes based on engagement data

### Episode Templates by Archetype

#### Neighbor Archetype (Kai)
```yaml
Episode 0 - "The Hallway":
  situation: |
    You're fumbling with grocery bags outside your apartment when the door
    across the hall opens. She's been your neighbor for two weeks but you've
    only exchanged awkward waves. Tonight she's in an oversized sweater,
    clearly not expecting to see anyone.
  trigger: "She catches you staring a beat too long"
  stakes: "First real interaction - sets the tone for everything after"
  opening_line: "*pauses mid-step, tucking hair behind ear* Oh— hey. 4B, right? I keep meaning to actually introduce myself..."

Episode 1 - "Borrowed Sugar":
  situation: |
    It's almost midnight. You're halfway through a recipe when you realize
    you're out of a crucial ingredient. The grocery store closed an hour ago.
    There's only one option, and it involves knocking on her door way too late.
  trigger: "She answers in pajamas, clearly wasn't asleep"
  stakes: "Asking a favor crosses the neighbor boundary"
  opening_line: "*opens door, surprised but not annoyed* ...couldn't sleep either, huh? What's— wait, are you baking at midnight?"

Episode 2 - "Power Outage":
  situation: |
    The whole building went dark ten minutes ago. You were heading to check
    the breaker when you literally collided with her in the pitch-black hallway.
    Now you're both using phone flashlights, standing closer than you've ever been.
  trigger: "Physical collision in the dark, forced proximity"
  stakes: "Darkness removes social barriers, intimacy feels inevitable"
  opening_line: "*phone flashlight illuminating half her face* Okay, my heart is still pounding. You scared me half to— *laughs nervously* ...hi."
```

#### Coworker Archetype (Sora)
```yaml
Episode 0 - "The Late Night":
  situation: |
    The office emptied hours ago. You stayed to finish a deadline, assuming
    you'd be alone. Then you notice her light still on across the floor.
    She looks up at the exact moment you look over.
  trigger: "Caught looking at each other across empty office"
  stakes: "Workplace proximity becoming something else"
  opening_line: "*sets down pen, slight smile* ...I was starting to think I was the only one dedicated enough to be here this late. Or crazy enough."

Episode 1 - "The Elevator":
  situation: |
    Monday morning. The elevator's crowded until it's suddenly just the two
    of you. Fourteen floors to go. She's holding coffee, you're holding the
    presentation you barely finished. The silence feels loud.
  trigger: "Alone together in confined space"
  stakes: "Small talk or real talk? 60 seconds to decide"
  opening_line: "*glances at your stack of papers, then at you* Rough weekend? ...You look like you either didn't sleep or slept too much.

Episode 2 - "The Conference":
  situation: |
    Out-of-town conference. The hotel bar is emptying out. Your colleagues
    left an hour ago but somehow you're both still here, three drinks in,
    talking about things that have nothing to do with work.
  trigger: "Professional walls down, hotel anonymity"
  stakes: "What happens at conferences stays at conferences?"
  opening_line: "*swirling drink, eyes meeting yours* Can I tell you something I probably shouldn't? ...I almost didn't come tonight.
```

#### Barista Archetype (Mira)
```yaml
Episode 0 - "Last Customer":
  situation: |
    The café's closing in ten minutes. You're the only one left, nursing a
    coffee you stopped tasting an hour ago. She's been glancing your way
    between closing tasks. When she finally comes over, she doesn't bring the check.
  trigger: "She approaches without being called"
  stakes: "Service interaction becoming personal"
  opening_line: "*slides into the seat across from you, still holding a rag* So... you planning to tell me what's wrong, or are we gonna pretend you're just really passionate about cold coffee?"

Episode 1 - "The Regular":
  situation: |
    Three weeks of daily visits. She knows your order before you say it.
    Today she's drawn something in your latte foam. It's definitely not
    standard café art. When you look up, she's watching for your reaction.
  trigger: "Personalized gesture crosses professional line"
  stakes: "Acknowledging it changes everything"
  opening_line: "*biting lip to suppress smile* Don't say anything. I know it's unprofessional. I just... wanted to see if you'd notice.

Episode 2 - "After Hours":
  situation: |
    She texted you. Just once: "Café's closed but I'm still here. Door's
    unlocked if you want actual good coffee for once." You're standing
    outside at 10 PM, hand on the door, knowing this isn't about coffee.
  trigger: "Private invitation outside work context"
  stakes: "Stepping through that door means something"
  opening_line: "*looks up from espresso machine, soft smile* You came. I wasn't sure if... *pauses* ...I'm glad you came."
```

### Episode Content for Remaining Characters

Similar 3-episode arcs for:
- **Luna (comforting)**: Rooftop → Late night call → Vulnerable confession
- **Raven (mysterious)**: Chance encounter → Shared secret → Trust test
- **Felix (playful)**: Gaming session → Spontaneous adventure → Serious moment
- **Morgan (mentor)**: First guidance → Personal revelation → Role reversal
- **Ash (brooding)**: Parallel solitude → Walls crack → Unguarded moment
- **Jade (flirty)**: Party encounter → Private follow-up → Real beneath the flirt
- **River (chaotic)**: Collision → Pulled into chaos → Unexpected depth

---

## Part 5: Technical Implementation

### Background Image Generation

Each episode needs a background image. Generation approach:

```python
def generate_episode_background(episode: Episode, character: Character) -> str:
    """Generate background image for episode using FLUX."""

    # Build scene prompt from episode_frame + character context
    scene_prompt = f"""
    {episode.episode_frame},
    anime background illustration, no characters,
    atmospheric, mood lighting, cinematic composition,
    {get_time_of_day(episode)}, {get_weather_mood(episode)},
    highly detailed environment, visual novel style
    """

    negative_prompt = """
    people, characters, faces, text, watermark,
    low quality, blurry, oversaturated
    """

    # Generate via FLUX
    image = await flux_generate(
        prompt=scene_prompt,
        negative_prompt=negative_prompt,
        width=1024,
        height=576,  # 16:9 for backgrounds
    )

    # Upload to storage
    url = await storage.upload_episode_background(episode.id, image)
    return url
```

### Episode Frame Derivation

Extract episode_frame from situation for image generation:

```python
def derive_episode_frame(situation: str, archetype: str) -> str:
    """Derive visual mood/setting from episode situation."""

    prompt = f"""
    Extract a 15-word visual scene description from this situation.
    Focus on: setting, lighting, time, mood, atmosphere.
    Do not include character descriptions or actions.

    Situation: {situation}

    Output format: "[setting], [lighting], [time], [mood]"
    """

    # LLM call for extraction
    return llm.generate(prompt).strip()
```

### Chat Initialization Flow

```python
async def start_conversation(
    user_id: UUID,
    character_id: UUID,
    episode_id: Optional[UUID] = None,
    db = Depends(get_db)
) -> Conversation:
    """Initialize conversation from episode."""

    # Get episode (default to Episode 0 if not specified)
    if episode_id:
        episode = await get_episode(episode_id, db)
    else:
        episode = await get_default_episode(character_id, db)

    # Create conversation with episode reference
    conversation = await create_conversation(
        user_id=user_id,
        character_id=character_id,
        episode_id=episode.id,
        db=db
    )

    # Build initial context with episode situation
    context = build_episode_context(episode)

    # Generate or return opening line
    opening = episode.opening_line

    # Create first message
    await create_message(
        conversation_id=conversation.id,
        role="character",
        content=opening,
        db=db
    )

    return conversation
```

### System Prompt Enhancement

Episode context injected into system prompt:

```python
def build_episode_system_prompt(character: Character, episode: Episode) -> str:
    """Build system prompt with episode context."""

    base_prompt = character.system_prompt

    episode_context = f"""

    ## Current Episode: {episode.title}

    SITUATION:
    {episode.situation}

    NARRATIVE TENDENCIES:
    This scenario tends toward these emotional beats (guide, don't force):
    {format_arc_hints(episode.arc_hints)}

    Remember: The user has agency. These are tendencies, not requirements.
    Stay in character. Respect boundaries. Let the moment breathe.
    """

    return base_prompt + episode_context
```

---

## Part 6: UI/UX Changes

### Discovery Page

Character cards show episode availability:

```
┌─────────────────────────────────────┐
│ [Avatar Image - Episode 0 vibe]    │
│                                     │
│ KAI                                 │
│ Neighbor                            │
│ "Freelance dev across the hall..." │
│                                     │
│ ○○○ 3 Episodes                      │
└─────────────────────────────────────┘
```

### Episode Selection (New Screen)

After clicking character card:

```
┌─────────────────────────────────────────────────┐
│ ← KAI                                           │
│                                                 │
│ Choose Your Moment                              │
│                                                 │
│ ┌─────────────────┐ ┌─────────────────┐        │
│ │ [hallway bg]    │ │ [door bg]       │        │
│ │                 │ │                 │        │
│ │ The Hallway     │ │ Borrowed Sugar  │        │
│ │ First meeting   │ │ Late night knock│        │
│ │ ▸ Start         │ │ ▸ Start         │        │
│ └─────────────────┘ └─────────────────┘        │
│                                                 │
│ ┌─────────────────┐                            │
│ │ [dark hall bg]  │                            │
│ │                 │                            │
│ │ Power Outage    │                            │
│ │ Stuck together  │                            │
│ │ ▸ Start         │                            │
│ └─────────────────┘                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Chat Screen

Background image as ambient layer:

```
┌─────────────────────────────────────────────────┐
│ ← Kai · Power Outage                    ⋮      │
├─────────────────────────────────────────────────┤
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░ [BACKGROUND: dim hallway, flashlights] ░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│                                                 │
│         ┌──────────┐                           │
│         │ [avatar] │  "Okay, my heart is      │
│         │ nervous  │   still pounding..."     │
│         └──────────┘                           │
│                                                 │
│                                                 │
│                           ┌──────────────────┐ │
│                           │ "Are you okay?"  │ │
│                           └──────────────────┘ │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Type a message...                       ➤  │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## Part 7: Implementation Plan

### Phase 1: Data Foundation (Week 1)

**Tasks:**
1. Create `episodes` table with schema
2. Migrate existing opening_situation/opening_line to Episode 0
3. Add episode_id to conversations table
4. Update character model to expose episodes
5. Create Episode CRUD API endpoints

**Deliverables:**
- [ ] Database migration
- [ ] Episode model/schema
- [ ] Basic API endpoints (list, get, create, update)

### Phase 2: Episode Content (Week 1-2)

**Tasks:**
1. Write Episode 0 rewrites with 4-ingredient structure
2. Write Episode 1 for all 10 characters
3. Write Episode 2 for all 10 characters
4. Derive episode_frame for each episode
5. Define arc_hints for each episode

**Deliverables:**
- [ ] 30 episodes (10 characters × 3 each)
- [ ] Episode content spreadsheet/doc for review

### Phase 3: Visual Assets (Week 2)

**Tasks:**
1. Implement episode background generation
2. Generate backgrounds for all 30 episodes
3. Store and link to episodes
4. Update avatar generation to use episode_frame

**Deliverables:**
- [ ] Background generation pipeline
- [ ] 30 background images
- [ ] Updated avatar generation with episode context

### Phase 4: Backend Integration (Week 2-3)

**Tasks:**
1. Update conversation start flow to accept episode_id
2. Enhance system prompt with episode context
3. Implement arc hints injection
4. Add episode to message context

**Deliverables:**
- [ ] Updated conversation API
- [ ] Episode-aware system prompts
- [ ] Conversation-episode linking

### Phase 5: Frontend (Week 3-4)

**Tasks:**
1. Episode selection screen (new)
2. Update character detail to show episodes
3. Chat background image layer
4. Episode indicator in chat header
5. Discovery page episode count badge

**Deliverables:**
- [ ] Episode selection UI
- [ ] Chat background integration
- [ ] Updated discovery cards

### Phase 6: Testing & Polish (Week 4)

**Tasks:**
1. QA all 30 episodes
2. Verify background images display correctly
3. Test episode switching
4. Performance testing with backgrounds
5. Mobile responsiveness check

**Deliverables:**
- [ ] QA sign-off
- [ ] Performance benchmarks
- [ ] Mobile screenshots

---

## Part 8: Success Metrics

### Engagement Metrics
- **Episode selection distribution** - Which episodes are most chosen?
- **Conversation length by episode** - Do some episodes drive longer chats?
- **Return rate by episode** - Do users replay episodes?
- **Episode completion** - Do users reach "natural endings"?

### Quality Metrics
- **Litmus test pass rate** - Avatar + first line = who/where/why-reply?
- **Arc hint alignment** - Do conversations tend toward intended beats?
- **User satisfaction** - Feedback/ratings per episode

### Business Metrics
- **Conversion by episode** - Which episodes drive premium conversion?
- **Time in chat by episode** - Engagement depth
- **Character preference shifts** - Do episodes change character popularity?

---

## Part 9: Future Considerations

### Not in Scope (v1)
- Episode unlocking/gating by relationship stage
- Multi-scene backgrounds within episode
- User-generated episodes
- Episode branching (choice-based paths)
- Episode "completion" rewards

### Potential v2 Features
- **Premium episodes** - Exclusive scenarios for subscribers
- **Seasonal episodes** - Holiday/event-specific scenarios
- **Community episodes** - User-submitted scenarios
- **Continuation episodes** - Pick up where you left off
- **Cross-character episodes** - Scenarios involving multiple characters

---

## Appendix A: Episode Content Template

```yaml
character: [Name]
archetype: [Type]
episode_number: [0-N]
title: "[Human-readable title]"
slug: "[url-safe-slug]"

situation: |
  [2-4 sentences incorporating all 4 ingredients]
  WHERE: [Setting detail]
  TRIGGER: [What just happened]
  STAKES: [Emotional risk]
  WHY YOU: [User implication]

opening_line: |
  "[First message from character - should act on the trigger]"

episode_frame: |
  "[15-word visual mood for background generation]"

arc_hints:
  beat_1: "[Initial tension/setup]"
  beat_2: "[Escalation or vulnerability]"
  beat_3: "[Peak moment]"
  resolution: "[Natural landing]"

background_prompt: |
  "[Detailed prompt for FLUX background generation]"
```

---

## Appendix B: Decision Log

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Episode gating | Unlock-based vs All available | All available | Need user data before gating; reduces friction |
| Arc hints | Strict beats vs Soft attractors | Soft attractors | Preserves user agency; feels less scripted |
| Scope | 2, 3, or 4+ episodes | 3 episodes | Manageable (30 total); covers key moments |
| Backgrounds | Static vs Multi-scene | Static per episode | Simpler; avatar expressions add dynamism |
| Storage | Separate table vs JSONB | Separate table | Better querying; clearer relationships |
| Migration | Replace fields vs Sync | Sync to character fields | Backwards compatibility |

---

## Appendix C: Terminology Quick Reference

| Term | Meaning |
|------|---------|
| Cold Open | The moment that starts a chat (cinematic hook) |
| Episode | A specific scenario/moment for a character |
| Episode 0 | Default first-meeting scenario |
| Episode Frame | Visual mood extracted from situation |
| Arc Hints | Soft narrative waypoints |
| Opening Beat | Data fields (situation + opening_line) |
| Conversation Ignition | System that produces/manages openings |
| Background Image | Scene image displayed during chat |

---

*Document authored during strategic design session. Captures evolution from visual-only improvements to full episodic experience model.*
