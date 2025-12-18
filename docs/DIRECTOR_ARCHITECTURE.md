# Director Architecture

> **Status**: Draft
> **Created**: 2024-12-19
> **Purpose**: Define the Director/Observer entity for episode management, evaluation, and narrative continuity.

---

## Overview

The **Director** is a system entity that observes, evaluates, and guides conversations without being visible to users. It operates alongside the Character (the "actor") to enable bounded episodes, progression tracking, and derived outputs like scores and recommendations.

### Metaphor

| Role | Responsibility | Visibility |
|------|----------------|------------|
| **Character** | Acting — dialogue, emotion, persona | User sees |
| **Director** | Observing, judging, guiding — state management | Hidden |

The Director is the **brain, eyes, and ears** of the interaction:
- **Eyes & Ears**: Observes all exchanges, user signals, character responses
- **Brain**: Interprets state, decides beat progression, detects completion
- **Hands**: Triggers system actions (completion, UI elements, next-episode suggestions)

---

## Director Capabilities

| Capability | Description | Use Case |
|------------|-------------|----------|
| **Beat Tracking** | Track progression through narrative beats | Guided/gated episodes |
| **Turn Counting** | Track exchange count per session | Turn-limited games |
| **Signal Collection** | Gather user behavior patterns | Scoring, personalization |
| **Completion Detection** | Determine when episode is "done" | Bounded episodes |
| **Evaluation Generation** | Produce reports, scores, summaries | Games, episode summaries |
| **Next Episode Suggestion** | Recommend continuation | **All episodes** |
| **State Injection** | Provide context to character LLM | Memory, flags, nudges |
| **UI Triggers** | Surface choices, scene cards, prompts | Structured content |

### Universal Application: Next Episode Suggestion

The Director's `suggest_next_episode` capability applies to **all episode types**, not just bounded ones:

| Scenario | Director Action |
|----------|-----------------|
| Flirt test completes | Evaluate → Result → Suggest Episode 1 of series |
| Mystery episode completes | Clue revealed → Suggest next episode |
| Open-ended episode fades | Detect natural pause → Suggest related episode |
| Series completed | Suggest thematically matched series |

---

## Integration with Current Architecture

### Current Flow (from `conversation.py`)

```
User message
    ↓
ConversationService.send_message_stream()
    ↓
Build ConversationContext (memories, hooks, episode dynamics)
    ↓
LLM.generate_stream() → Character response
    ↓
_process_exchange() → Extract memories, update relationship_dynamic
    ↓
Return to user
```

### Proposed Flow with Director

```
User message
    ↓
ConversationService.send_message_stream()
    ↓
Build ConversationContext
    ↓
LLM.generate_stream() → Character response
    ↓
_process_exchange() → Memories, beats (existing)
    ↓
DirectorService.evaluate() → NEW
    ├── Update director_state (beat_reached, turn_count, signals)
    ├── Check completion conditions
    ├── If complete: generate evaluation, suggest next
    └── Return director output
    ↓
Return to user (with director signals if relevant)
```

### Implementation: Post-Processing Model

The Director runs **after** each exchange as a post-processing step. This:
- Keeps character generation pure and fast
- Allows Director logic to be optional (skip for open-ended content)
- Enables gradual rollout

```python
# In conversation.py send_message_stream()

# After _process_exchange()
if episode_template.completion_mode != 'open':
    director_output = await self.director_service.evaluate(
        session_id=session.id,
        messages=context.messages + [{"role": "assistant", "content": response_content}],
        episode_template=episode_template,
    )

    if director_output.is_complete:
        yield json.dumps({
            "type": "episode_complete",
            "evaluation": director_output.evaluation,
            "next_episode": director_output.next_suggestion,
        })
```

---

## Schema Extensions

### Session Extensions

```sql
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS
    turn_count INT DEFAULT 0,
    director_state JSONB DEFAULT '{}',
    completion_trigger TEXT DEFAULT NULL;

-- director_state structure:
-- {
--   "current_beat": "escalation",
--   "beats_completed": ["establishment", "complication"],
--   "user_signals": {"confident": 3, "hesitant": 1, "playful": 2},
--   "tension_curve": [0.3, 0.5, 0.7],
--   "flags": {"key_moment_reached": true}
-- }
```

### Episode Template Extensions

```sql
ALTER TABLE episode_templates ADD COLUMN IF NOT EXISTS
    completion_mode TEXT DEFAULT 'open',  -- open, beat_gated, turn_limited, objective
    turn_budget INT DEFAULT NULL,
    completion_criteria JSONB DEFAULT NULL;

-- completion_criteria structure (varies by mode):
-- turn_limited: {"max_turns": 8}
-- beat_gated: {"required_beat": "pivot", "require_resolution": true}
-- objective: {"objective_key": "accusation_made"}
```

### Session Evaluations (New Table)

```sql
CREATE TABLE session_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    evaluation_type TEXT NOT NULL,  -- 'flirt_archetype', 'episode_summary', 'mystery_progress'
    result JSONB NOT NULL,
    model_used TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- result structure varies by type:
-- flirt_archetype: {"archetype": "tension_builder", "scores": {...}, "description": "..."}
-- episode_summary: {"summary": "...", "key_moments": [...], "emotional_arc": "..."}
-- mystery_progress: {"clues_found": [...], "suspects_cleared": [...], "current_theory": "..."}
```

---

## Completion Modes

| Mode | Trigger | Use Case |
|------|---------|----------|
| `open` | Never (user decides) | Default, open-ended chat |
| `beat_gated` | Final beat + resolution detected | Most series episodes |
| `turn_limited` | Turn budget exhausted | Games, quick challenges |
| `objective` | Specific flag set | Mystery (accusation), choices |

### Completion Detection Logic

```python
class DirectorService:
    async def check_completion(
        self,
        session: Session,
        episode_template: EpisodeTemplate,
        director_state: dict,
    ) -> tuple[bool, str | None]:
        """Check if episode should complete.

        Returns (is_complete, trigger_reason)
        """
        mode = episode_template.completion_mode

        if mode == 'open':
            return False, None

        if mode == 'turn_limited':
            budget = episode_template.turn_budget or 10
            if director_state.get('turn_count', 0) >= budget:
                return True, 'turn_limit'

        if mode == 'beat_gated':
            criteria = episode_template.completion_criteria or {}
            required_beat = criteria.get('required_beat', 'pivot')
            beats_completed = director_state.get('beats_completed', [])
            if required_beat in beats_completed:
                return True, 'beat_complete'

        if mode == 'objective':
            criteria = episode_template.completion_criteria or {}
            objective_key = criteria.get('objective_key')
            flags = director_state.get('flags', {})
            if flags.get(objective_key):
                return True, 'objective_met'

        return False, None
```

---

## Director Evaluation

When episode completes, Director generates an evaluation based on episode type.

### Flirt Test Evaluation

```python
async def evaluate_flirt_test(
    self,
    session_id: UUID,
    messages: list[dict],
    director_state: dict,
) -> dict:
    """Evaluate flirt conversation and assign archetype."""

    prompt = """Analyze this flirtatious conversation and classify the user's flirt style.

CONVERSATION:
{conversation}

USER SIGNALS OBSERVED:
{signals}

Based on the user's responses, determine their flirt archetype:
- tension_builder: Masters the pause, creates anticipation
- bold_mover: Direct, confident, takes initiative
- playful_tease: Light, fun, uses humor
- slow_burn: Patient, builds connection over time
- mysterious_allure: Intriguing, doesn't reveal everything

Return JSON:
{
  "archetype": "<archetype_key>",
  "confidence": 0.0-1.0,
  "primary_signals": ["signal1", "signal2"],
  "description": "One sentence describing their style"
}"""

    # Call evaluation LLM
    result = await self.llm.generate_json(prompt.format(
        conversation=self._format_conversation(messages),
        signals=json.dumps(director_state.get('user_signals', {})),
    ))

    return result
```

### Episode Summary Evaluation

```python
async def evaluate_episode_summary(
    self,
    session_id: UUID,
    messages: list[dict],
    character_name: str,
) -> dict:
    """Generate episode summary for serial continuity."""

    # Similar pattern - LLM generates structured summary
    # Used for series_context in subsequent episodes
```

---

## Next Episode Suggestion

The Director suggests next steps based on context:

```python
async def suggest_next_episode(
    self,
    session: Session,
    evaluation: dict | None,
    series: Series | None,
) -> dict | None:
    """Suggest next episode or series."""

    # 1. If in a series, suggest next episode in order
    if series and series.episode_order:
        current_idx = series.episode_order.index(str(session.episode_template_id))
        if current_idx < len(series.episode_order) - 1:
            next_template_id = series.episode_order[current_idx + 1]
            return {
                "type": "next_episode",
                "episode_template_id": next_template_id,
                "series_id": series.id,
            }

    # 2. If evaluation has archetype, suggest matched series
    if evaluation and evaluation.get('archetype'):
        matched_series = await self._get_archetype_matched_series(
            evaluation['archetype']
        )
        return {
            "type": "matched_series",
            "series": matched_series,
        }

    # 3. Default: suggest same character's other content
    return {
        "type": "character_content",
        "character_id": session.character_id,
    }
```

---

## Message Parsing (Deferred)

Current message format mixes dialogue and actions:

```
*She raises an eyebrow* "You're brave, I'll give you that."
```

**Current approach**: Keep as-is for display. Director reads raw text.

**Future consideration**: Parse into structured format for richer Director analysis:

```json
{
  "content": "*She raises an eyebrow* \"You're brave, I'll give you that.\"",
  "parsed": {
    "action": "She raises an eyebrow",
    "dialogue": "You're brave, I'll give you that.",
    "internal": null
  }
}
```

This is **deferred** — Director can work with raw text initially. Parsing adds value for:
- Richer signal extraction
- Better beat detection
- Dialogue-only analysis

---

## Director Service Interface

```python
class DirectorService:
    """Service for episode observation, evaluation, and guidance."""

    async def evaluate(
        self,
        session_id: UUID,
        messages: list[dict],
        episode_template: EpisodeTemplate,
    ) -> DirectorOutput:
        """Run Director evaluation after exchange.

        Returns:
            DirectorOutput with updated state, completion status,
            evaluation if complete, next suggestion.
        """

    async def update_turn_count(self, session_id: UUID) -> int:
        """Increment and return turn count."""

    async def update_beat(
        self,
        session_id: UUID,
        beat: str,
        signals: dict,
    ) -> None:
        """Update current beat and user signals."""

    async def check_completion(
        self,
        session: Session,
        episode_template: EpisodeTemplate,
        director_state: dict,
    ) -> tuple[bool, str | None]:
        """Check if episode should complete."""

    async def generate_evaluation(
        self,
        session_id: UUID,
        evaluation_type: str,
        messages: list[dict],
        director_state: dict,
    ) -> dict:
        """Generate evaluation (score, summary, etc.)."""

    async def suggest_next_episode(
        self,
        session: Session,
        evaluation: dict | None,
        series: Series | None,
    ) -> dict | None:
        """Suggest next episode or content."""


@dataclass
class DirectorOutput:
    """Output from Director evaluation."""

    director_state: dict
    turn_count: int
    is_complete: bool
    completion_trigger: str | None
    evaluation: dict | None
    next_suggestion: dict | None
```

---

## Implementation Priority

1. **Schema extensions** — Add columns to sessions, episode_templates
2. **DirectorService skeleton** — Basic service with turn counting
3. **Completion detection** — Implement for turn_limited mode (flirt test)
4. **Flirt test evaluation** — LLM-based archetype classification
5. **Next episode suggestion** — Basic series continuation
6. **Beat tracking** — For mystery/thriller serials (future)

---

## Relationship to GTM Plan

This architecture enables the Viral Play Feature:

| GTM Requirement | Director Capability |
|-----------------|---------------------|
| Bounded flirt test | `completion_mode: turn_limited` |
| Archetype result | `evaluate_flirt_test()` |
| "Continue with character" CTA | `suggest_next_episode()` |
| Series-matched suggestions | Archetype → series matching |

The Director is **built for games, reusable for all content**.

---

## References

- [VIRAL_PLAY_FEATURE_GTM.md](plans/VIRAL_PLAY_FEATURE_GTM.md) — GTM strategy
- [EPISODE_DYNAMICS_CANON.md](EPISODE_DYNAMICS_CANON.md) — Episode philosophy
- [conversation.py](../substrate-api/api/src/app/services/conversation.py) — Current implementation
