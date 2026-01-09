# Dynamic Episode Scaffolding

> **Status**: Concept / Discovery
> **Created**: 2025-01-09
> **Last Updated**: 2025-01-09

## Overview

Instead of pre-authoring all episodes in a series, the system generates subsequent episodes dynamically based on user conversation outcomes. This creates truly emergent narratives where user choices **actually** shape the story arc.

## The Core Idea

```
Episode 1 (Authored)
    ↓ User plays, conversation happens
    ↓ Director extracts: emotional beats, user choices, unresolved tensions
    ↓ [Generation Gap - AI scaffolds next episode]
    ↓
Episode 2 (AI Scaffolded)
    ├── Setting: Generated based on E1 outcome
    ├── Dramatic question: Escalation of E1's tension
    ├── Scene motivation: What character wants NOW given what happened
    └── Opening: Drops user into new high-tension moment
    ↓ User plays...
    ↓
Episode 3 (AI Scaffolded)
    ... and so on
```

## Why This Matters

### Current Model (Pre-Authored)
- All episodes written in advance
- User choices affect conversation tone, not story direction
- Content bottleneck: need to author every episode
- Replayability limited to "same story, different dialogue"

### Dynamic Model
- Only Episode 1 needs authoring
- User choices **actually** determine what happens next
- Infinite content from single starting point
- True replayability: different conversations → different Episode 2 → divergent arcs

## Key Differentiator

**Character.AI can't do this.** They have no narrative architecture.

We have:
- Episode scaffolding system
- Director service
- Beat guidance structure
- Memory system
- Genre settings

All the pieces exist. The question is: can we connect them to generate coherent episode scaffolds?

---

## Technical Foundation (What We Have)

### Data Available at Episode End

When an episode completes, we have rich context:

**From Session:**
```
turn_count              → How many exchanges happened
director_state          → All evaluations, visual decisions, beat tracking
resolution_type         → How it ended (positive/neutral/negative/faded)
completion_trigger      → What triggered completion
summary                 → Generated summary of conversation
emotional_tags          → Detected emotions
key_events              → Significant moments
```

**From Director (beat_data):**
```
recent_beats[]          → Last 10 beat types (playful, tense, vulnerable, charged, etc.)
tension_level           → 0-100 current tension
milestones[]            → Reached milestones (first_spark, vulnerability_shared, etc.)
```

**From Memory System:**
```
memory_events[]         → Facts, preferences, events extracted
  - type                → fact/preference/event/goal/relationship/emotion
  - importance_score    → 0.0-1.0
  - emotional_valence   → -2 to +2
hooks[]                 → Follow-up triggers created
  - content             → What to follow up about
  - suggested_opener    → Natural way to bring it up
```

**From Episode Template:**
```
dramatic_question       → What tension was being explored
scene_objective         → What character wanted
scene_obstacle          → What was blocking them
genre                   → Genre doctrine applied
turn_budget             → Pacing expectation
```

### Underutilized Fields We Can Leverage

| Field | Current State | Potential Use |
|-------|---------------|---------------|
| `beat_guidance` | Exists but never used | Store generated beat structure for next episode |
| `fade_hints` | Exists but never used | Signal natural transition points |
| `completion_criteria` | Only used for gated modes | Could store "what must happen next" |
| `metadata` (JSONB) | Empty | Store generation context, parent episode link |

---

## Dynamic Scaffolding Architecture

### Trigger Point

Episode completion when `suggest_next = true` (turn_count == turn_budget)

Instead of looking up pre-authored Episode N+1, we **generate** it.

### Generation Input Bundle

```python
ScaffoldInput:
  # Episode Context
  series_id: UUID
  current_episode_number: int
  genre: str

  # What Just Happened
  conversation_summary: str          # From session.summary
  resolution_type: str               # How it ended
  dramatic_question: str             # What was being explored
  key_events: List[str]              # Significant moments
  emotional_tags: List[str]          # Detected emotions

  # Relationship State
  tension_level: int                 # 0-100
  recent_beats: List[str]            # Last 10 beat types
  milestones: List[str]              # All reached milestones

  # Memory Context
  important_memories: List[Memory]   # High importance_score memories
  active_hooks: List[Hook]           # Unresolved follow-ups

  # Arc Position
  episodes_played: int               # How far into the story
  arc_position: str                  # "rising", "peak", "falling", "resolution"
```

### Generation Output (Episode Scaffold)

```python
ScaffoldOutput:
  # Core Episode Identity
  title: str
  episode_number: int
  episode_type: str                  # "core" or "special" (if climax)

  # Scene Setup
  situation: str                     # Present-tense scene description
  episode_frame: str                 # Stage direction for LLM
  opening_line: str                  # Character's first message
  starter_prompts: List[str]         # 3 alternative openers

  # Dramatic Structure
  dramatic_question: str             # New tension to explore
  scene_objective: str               # What character wants now
  scene_obstacle: str                # What's blocking them
  scene_tactic: str                  # How they're playing it

  # Director Config
  turn_budget: int                   # Suggested length (default 10)
  visual_mode: str                   # cinematic/minimal/none

  # Beat Guidance (NEW - actually use this field)
  beat_guidance: {
    "establishment": str,            # Opening beat
    "complication": str,             # Rising tension
    "escalation": str,               # Peak moment
    "pivot_opportunity": str         # User decision point
  }

  # Metadata
  parent_episode_id: UUID            # Link to episode that spawned this
  generation_context: {              # For debugging/analysis
    "input_hash": str,
    "model_used": str,
    "generated_at": timestamp
  }
```

### Arc Position Logic

```python
def determine_arc_position(episodes_played: int, tension_level: int, milestones: List[str]) -> str:
    """
    Determine where we are in the story arc.

    Standard 5-episode arc:
      Ep 1-2: Rising (establishment, building tension)
      Ep 3-4: Peak (maximum tension, crisis)
      Ep 5:   Resolution (payoff, closure)

    Adjustments based on:
      - tension_level: High tension might accelerate to peak
      - milestones: Key milestones might signal arc transitions
    """

    # Base position from episode count
    if episodes_played <= 2:
        base = "rising"
    elif episodes_played <= 4:
        base = "peak"
    else:
        base = "resolution"

    # Tension override: very high tension → force toward peak/resolution
    if tension_level > 80 and base == "rising":
        return "peak"

    # Milestone signals
    if "deep_confession" in milestones or "desire_expressed" in milestones:
        if base == "rising":
            return "peak"

    return base
```

### Genre-Aware Generation

Each genre has different arc patterns:

| Genre | Arc Shape | Peak Characteristics |
|-------|-----------|---------------------|
| `romantic_tension` | Slow burn → confession → resolution | Vulnerability, intimacy moments |
| `dark_romance` | Power dynamics → crisis → ownership/freedom | Control, submission, choice |
| `mystery` | Clues → revelation → confrontation | Discovery, accusation, truth |
| `thriller` | Danger → escape → confrontation | Action, stakes, survival |

Generator uses genre to shape:
- What kind of `dramatic_question` to pose
- What `scene_objective` makes sense
- What `beat_guidance` pattern to follow

---

## Open Questions

### 1. Generation Timing
- **Real-time**: Generate scaffold during conversation (latency concern)
- **End-of-episode**: Generate after episode completes (natural gap)
- **Async overnight**: "Next episode available tomorrow" (Mystic Messenger style)

**Current thinking**: End-of-episode seems natural. When `suggest_next` triggers, we can:
1. Show user "Next episode generating..."
2. Generate scaffold (5-10 seconds)
3. Present new episode immediately OR
4. Say "Your next episode is ready" (push notification later)

### 2. Quality Control
- How do we ensure AI-generated scaffolds maintain dramatic structure?
- What guardrails prevent repetitive or incoherent episodes?
- Do we need human review before episode goes live?

**Current thinking**:
- Validate output against schema (required fields)
- Check dramatic_question isn't duplicate of previous
- Score opening_line for "show don't tell" patterns
- For MVP: Auto-publish. Track quality metrics. Iterate.

### 3. Dramatic Structure
- Can AI actually build rising tension → climax → resolution?
- How do we encode genre-specific arc patterns?
- What happens at "season finale" - does AI know when to end?

**Current thinking**:
- `arc_position` input guides the generator
- Explicit instruction: "This is episode N of ~5. We are in [rising/peak/resolution]."
- At episode 5+, generator should be prompted to create resolution opportunities
- User can always continue (generate episode 6) but natural ending is signaled

### 4. User Expectations
- How do we communicate this is "emergent" vs "authored"?
- Does it matter to users?
- Is there value in "canonical" vs "your version" of a story?

**Current thinking**: Don't communicate it at all initially. If quality is good, users won't notice/care. The magic is that "my choices shaped this."

### 5. Episode Persistence
- Generated episodes: save as episode_templates or separate table?
- Per-user or shared? (If two users play same series, different scaffolds?)

**Current thinking**:
- Per-user episodes (your story is yours)
- Store in episode_templates with `is_generated = true` flag
- Link via `parent_episode_id` for tracing
- OR: new `generated_episodes` table scoped to (user_id, series_id)

---

## Turn Budget & Pacing Strategy

### Current Turn Budget Behavior

```
turn_budget = 10 (default)
  → At turn 10, suggest_next = true
  → User sees "Continue to next episode?" prompt
  → User can ignore and keep chatting (no hard stop)

turn_budget = 0
  → Infinite/open-ended
  → Never suggests next (free chat mode)
```

### Pacing Curve (from Director)

```python
def determine_pacing(turn_count: int, turn_budget: int) -> str:
    if turn_budget == 0:
        # Open-ended heuristics
        if turn_count < 2: return "establish"
        if turn_count < 5: return "develop"
        if turn_count < 8: return "escalate"
        return "peak"

    # Bounded: position in arc
    position = turn_count / turn_budget

    if position < 0.2:   return "establish"
    if position < 0.5:   return "develop"
    if position < 0.8:   return "escalate"
    if position < 0.95:  return "peak"
    return "resolve"
```

### Dynamic Budget Adjustment

For generated episodes, we could adjust `turn_budget` based on:

| Signal | Adjustment |
|--------|------------|
| User sent short responses in previous episode | Decrease budget (they want faster pacing) |
| User sent long, elaborate responses | Increase budget (they want to linger) |
| High tension_level at end | Shorter budget (capitalize on momentum) |
| Low tension_level at end | Standard budget (rebuild) |
| "resolution" arc_position | Longer budget (give room to conclude) |

```python
def calculate_dynamic_budget(
    previous_avg_response_length: int,
    tension_level: int,
    arc_position: str
) -> int:
    base = 10

    # Response length signals
    if previous_avg_response_length < 50:
        base -= 2  # User is brief → faster episodes
    elif previous_avg_response_length > 200:
        base += 2  # User is elaborate → longer episodes

    # Tension momentum
    if tension_level > 70:
        base -= 2  # High tension → don't let it cool
    elif tension_level < 30:
        base += 1  # Low tension → more time to build

    # Arc position
    if arc_position == "resolution":
        base += 3  # Give room for satisfying ending

    return max(5, min(15, base))  # Clamp to 5-15 range
```

### Visual Mode for Generated Episodes

```python
def determine_visual_mode(
    tension_level: int,
    arc_position: str,
    genre: str
) -> tuple[str, int]:
    """Returns (visual_mode, generation_budget)"""

    if arc_position == "peak":
        return ("cinematic", 4)  # More visuals at climax

    if genre in ("thriller", "mystery"):
        return ("minimal", 2)   # Atmosphere > frequency

    if tension_level > 60:
        return ("cinematic", 3)  # Capture charged moments

    return ("cinematic", 3)      # Default
```

---

## Data Flow: End-to-End

```
┌─────────────────────────────────────────────────────────────────┐
│                    EPISODE N (Authored or Generated)            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  User plays episode                                             │
│  - Messages exchanged                                           │
│  - Director tracks turns, beats, tension                        │
│  - Memory system extracts facts, preferences, hooks             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  turn_count == turn_budget                                      │
│  → suggest_next = true                                          │
│  → completion_trigger = "turn_limit"                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCAFFOLD GENERATOR TRIGGERED                                   │
│                                                                 │
│  Inputs collected:                                              │
│  ├── session.summary, resolution_type, key_events               │
│  ├── engagement.dynamic (tension, beats, milestones)            │
│  ├── memory_events (high importance)                            │
│  ├── hooks (active, unresolved)                                 │
│  ├── episode_template (genre, dramatic_question)                │
│  └── arc_position (calculated)                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  LLM GENERATION                                                 │
│                                                                 │
│  Prompt includes:                                               │
│  - Series context, character DNA                                │
│  - What just happened (summary, events, emotions)               │
│  - Relationship state (tension, milestones)                     │
│  - Arc position guidance ("You are in rising/peak/resolution")  │
│  - Genre-specific arc patterns                                  │
│  - Memory/hooks to weave in                                     │
│                                                                 │
│  Output: ScaffoldOutput (validated against schema)              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  EPISODE N+1 CREATED                                            │
│                                                                 │
│  Stored in episode_templates (or generated_episodes):           │
│  ├── is_generated = true                                        │
│  ├── parent_episode_id = Episode N                              │
│  ├── user_id = scoped to this user                              │
│  ├── series_id = same series                                    │
│  └── All scaffold fields populated                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  USER PRESENTED WITH NEXT EPISODE                               │
│                                                                 │
│  Options:                                                       │
│  A) Immediate: "Your next episode is ready. Step in."           │
│  B) Delayed: Push notification later "Episode 2 awaits"         │
│  C) User choice: "Generate next" button                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EPISODE N+1 (Generated)                      │
│                    ... cycle repeats ...                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Storage Options

### Option A: Extend episode_templates

Add columns:
```sql
ALTER TABLE episode_templates ADD COLUMN is_generated BOOLEAN DEFAULT false;
ALTER TABLE episode_templates ADD COLUMN generated_for_user_id UUID REFERENCES users(id);
ALTER TABLE episode_templates ADD COLUMN parent_episode_id UUID REFERENCES episode_templates(id);
ALTER TABLE episode_templates ADD COLUMN generation_context JSONB;
```

**Pros**: Single table, existing queries work
**Cons**: Mixes authored and generated, visibility complexity

### Option B: New generated_episodes table

```sql
CREATE TABLE generated_episodes (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    series_id UUID NOT NULL REFERENCES series(id),
    parent_session_id UUID REFERENCES sessions(id),

    episode_number INT NOT NULL,
    title TEXT NOT NULL,

    -- Same fields as episode_templates
    situation TEXT NOT NULL,
    opening_line TEXT NOT NULL,
    episode_frame TEXT,
    dramatic_question TEXT,
    scene_objective TEXT,
    scene_obstacle TEXT,
    scene_tactic TEXT,
    beat_guidance JSONB,
    starter_prompts TEXT[],

    turn_budget INT DEFAULT 10,
    visual_mode TEXT DEFAULT 'cinematic',
    generation_budget INT DEFAULT 3,

    -- Generation metadata
    generation_context JSONB NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, series_id, episode_number)
);
```

**Pros**: Clean separation, clear ownership, no pollution of authored content
**Cons**: Need to update episode lookup logic to check both tables

### Recommendation: Option B

Generated episodes are fundamentally different:
- User-scoped (my episode 2 ≠ your episode 2)
- Ephemeral (could be regenerated)
- Traceable (linked to parent session)

Keep them separate for clarity.

---

## Potential Approaches

### Approach A: Template + Fill
- Pre-define episode "shapes" (e.g., "escalation episode", "crisis episode", "resolution episode")
- AI selects appropriate shape based on conversation
- AI fills in specifics (setting, dramatic question, opening)

**Pros**: More controlled, predictable quality
**Cons**: Less emergent, could feel formulaic

### Approach B: Full Generation
- AI generates entire scaffold from scratch
- Only constrained by genre settings and series context
- Maximum emergence

**Pros**: True emergence, infinite variety
**Cons**: Quality variance, could go off-rails

### Approach C: Hybrid
- AI proposes scaffold
- System validates against dramatic structure rules
- Rejected scaffolds get regenerated with feedback

**Pros**: Balance of emergence and quality
**Cons**: More complex, potential latency

---

## Integration with Existing Systems

### Director Service
- Already tracks beat progression
- Could signal "episode ready to transition"
- Output could feed scaffold generator

### Memory System
- Extracted facts/preferences inform next episode
- "User revealed they have a fear of commitment" → Episode 3 tests that

### Genre Settings
- `tension_style`, `pacing_curve` guide generation
- Genre doctrine shapes what kinds of episodes are valid

### Episode Templates
- Generated scaffolds would populate same schema
- No frontend changes needed - just different source of data

---

## MVP Scope (If We Build This)

**Phase 1: Proof of Concept**
- Single series with 1 authored episode
- Manual trigger to generate Episode 2
- Human review before publishing
- Measure: Can AI produce coherent, playable scaffold?

**Phase 2: Automated Generation**
- Generate scaffold automatically at episode end
- Quality scoring / auto-rejection
- User sees "Episode 2 ready" after playing Episode 1

**Phase 3: Real-Time**
- Near real-time generation during conversation
- Seamless transition between episodes
- Full emergent narrative experience

---

## Risks & Concerns

1. **Quality degradation** - Each generation could drift further from coherence
2. **Repetitive patterns** - AI might fall into formulaic structures
3. **User confusion** - "Wait, this doesn't match what I expected"
4. **Cost** - Generation isn't free; need to model economics
5. **Loss of authorial voice** - Generated content may lack the craft of authored episodes

---

## Success Criteria

- [ ] Generated episodes feel as engaging as authored ones
- [ ] Users can't easily distinguish generated vs authored
- [ ] Story arcs feel coherent across 5+ episodes
- [ ] Generation latency acceptable for user experience
- [ ] Cost per generated episode within margin targets

---

## Notes & Discussion Log

### 2025-01-09 - Initial Concept

From product strategy session:
- This emerged as a potential "10x" differentiator
- Key insight: The gap between episodes is where AI does narrative work
- Comparison to Mystic Messenger: real-time pacing + AI generation could combine for powerful effect
- Architecture already supports this conceptually; execution is the question

### 2025-01-09 - Technical Deep Dive

Analyzed existing schema and found:
- **Rich data at episode end**: director_state, beat_data, memories, hooks all captured
- **Underutilized fields**: beat_guidance, fade_hints exist but never used
- **Turn budget system**: Already tracks pacing, triggers suggest_next
- **Memory scoping**: Series-scoped isolation means generated episodes can have clean context

Key decisions made:
1. **Storage**: Separate `generated_episodes` table (Option B) - cleaner separation
2. **Timing**: End-of-episode generation (when suggest_next triggers)
3. **Arc awareness**: Use tension_level + milestones + episode count to determine arc_position
4. **Dynamic turn_budget**: Adjust based on user response patterns
5. **Beat guidance**: Finally use this field - populate for generated episodes

Open items for next discussion:
- [ ] Generator prompt design (what makes a good scaffold prompt?)
- [ ] Quality metrics (how do we know generated episodes are good?)
- [ ] Regeneration UX (what if user doesn't like generated episode?)
- [ ] Series "ending" detection (when should we stop generating?)
- [ ] Cost modeling (LLM cost per generation, acceptable margin?)

---

## References

- [EPISODE_DYNAMICS_CANON.md](../implementation/EPISODE_DYNAMICS_CANON.md) - Current episode structure
- [DIRECTOR_SERVICE.md](../implementation/DIRECTOR_SERVICE.md) - Beat tracking and pacing
- [scaffold_series_first.py](../../substrate-api/api/src/app/scripts/scaffold_series_first.py) - Current authoring approach
