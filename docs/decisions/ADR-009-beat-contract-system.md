# ADR-009: Beat Contract System

> **Status**: Accepted
> **Date**: 2026-01-19
> **Deciders**: Kevin Kim (Founder)
> **Builds On**: ADR-002 (Theatrical Model), ADR-008 (User Objectives)

---

## Context

ADR-008 introduced User Objectives and Choice Points to give users explicit goals and meaningful decisions. However, implementation revealed a **coupling gap**:

### The Problem

Choice points trigger on turn count, but nothing ensures the character delivers the narrative beat that makes the choice meaningful:

```python
# Episode Template defines:
choice_points=[{
    "id": "salary_question",
    "trigger": "turn:4",
    "prompt": "Morgan asks about your salary expectations. How do you respond?",
    "choices": [...]
}]

# At turn 4:
# - Choice card appears with "Morgan asks about salary..."
# - But Morgan's actual dialogue might be about something else entirely
# - User sees a choice disconnected from the conversation
```

### Why This Happens

The theatrical model (ADR-002) correctly separates concerns:
- **Episode**: Defines what MUST happen (scene motivation, choice points)
- **Director**: Provides pacing and grounding
- **Character**: Improvises within the frame

But we're missing the **rehearsal → performance** link. In theater, actors know which beats they must hit. Currently, our characters don't receive beat instructions—they improvise freely while the system expects specific moments to occur.

### The Metaphor Gap

| Theater | Current System | Missing |
|---------|----------------|---------|
| "In Act 2, you MUST ask about the letter" | `trigger: turn:4` | Instruction to character |
| Director ensures beat lands | Director checks turn count | Director shaping character toward beat |
| Audience sees organic delivery | User sees disconnected UI | Integration of choice with dialogue |

---

## Decision

Implement a **Beat Contract System** that:

1. **Defines beats** as first-class objects (not just trigger conditions)
2. **Instructs characters** to deliver beats organically
3. **Detects beat completion** semantically (not just turn-based)
4. **Surfaces choices** as the user's response to what was actually said

### Core Principle

> **Choices are dialogue, not UI.** When a choice point triggers, the user's selection becomes their message in the conversation.

---

## Architecture

### Beat Lifecycle

```
Episode Start
    ↓
Beats loaded from EpisodeTemplate.beats[]
    ↓
Each turn, Director checks: "Which beats are due?"
    ↓
If beat approaching deadline:
    → Inject BeatDirective into character prompt
    → Character works beat into their response organically
    ↓
Director Phase 2 analyzes response:
    → Did the beat land? (semantic detection)
    ↓
If beat landed AND beat has choice_point:
    → Emit "choice_point" event with actual context
    → Frontend shows choices as input replacement
    ↓
User selects choice:
    → Selection becomes their message
    → Flag set from choice
    → Conversation continues
```

### Data Model

#### Beat Definition (in EpisodeTemplate)

```python
@dataclass
class Beat:
    """A narrative moment that must occur in the episode."""
    id: str                          # Unique identifier
    description: str                 # What must happen
    character_instruction: str       # How to tell the character
    target_turn: int                 # Ideal turn for this beat
    deadline_turn: int               # Must complete by this turn
    detection_type: str              # "semantic" | "keyword" | "automatic"
    detection_criteria: str          # Criteria for semantic/keywords

    # Optional: Choice that surfaces when beat lands
    choice_point: Optional[ChoicePoint] = None

    # Optional: Dependencies
    requires_beat: Optional[str] = None  # Must complete after this beat
    requires_flag: Optional[str] = None  # Must have this flag set
```

#### Director Pre-Guidance Extension

```python
@dataclass
class DirectorGuidance:
    pacing: str
    physical_anchor: str
    genre: str
    energy_level: str

    # NEW: Beat directive for this turn
    beat_directive: Optional[BeatDirective] = None

@dataclass
class BeatDirective:
    """Instruction to character to deliver a specific beat."""
    beat_id: str
    instruction: str                 # Natural language for character
    urgency: str                     # "suggested" | "required" | "overdue"
    context: str                     # Why this beat matters now
```

#### Director State Extension

```python
director_state = {
    # Existing...
    "objectives": {...},
    "flags": {...},
    "choices_made": [...],

    # NEW: Beat tracking
    "beats": {
        "salary_question": {
            "status": "pending",       # pending | delivered | detected | completed
            "delivered_at_turn": None, # When character delivered the beat
            "detected_at_turn": None,  # When system detected it landed
            "choice_pending": False,   # Waiting for user choice
        }
    }
}
```

### Integration Points

#### 1. Pre-Guidance Phase (Director shapes character)

```python
def generate_pre_guidance(self, ..., pending_beats: List[Beat]) -> DirectorGuidance:
    """Generate guidance including beat directives."""

    guidance = DirectorGuidance(
        pacing=self.determine_pacing(turn_count, turn_budget),
        physical_anchor=self._extract_physical_anchor(situation),
        genre=genre,
        energy_level=energy_level,
    )

    # Check for beats that need delivery
    for beat in pending_beats:
        if beat.status == "pending":
            if turn_count >= beat.deadline_turn:
                # Overdue - must deliver now
                guidance.beat_directive = BeatDirective(
                    beat_id=beat.id,
                    instruction=beat.character_instruction,
                    urgency="overdue",
                    context=f"This must happen now (deadline was turn {beat.deadline_turn})"
                )
                break
            elif turn_count >= beat.target_turn:
                # At target - should deliver
                guidance.beat_directive = BeatDirective(
                    beat_id=beat.id,
                    instruction=beat.character_instruction,
                    urgency="required",
                    context="This is the right moment for this beat"
                )
                break
            elif turn_count >= beat.target_turn - 1:
                # Approaching - prepare
                guidance.beat_directive = BeatDirective(
                    beat_id=beat.id,
                    instruction=beat.character_instruction,
                    urgency="suggested",
                    context="Look for a natural opening for this"
                )
                break

    return guidance
```

#### 2. Prompt Injection

```python
def to_prompt_section(self) -> str:
    """Format guidance for character prompt."""

    section = f"""
═══════════════════════════════════════════════════════════════
DIRECTOR: {self.genre.upper().replace('_', ' ')}
═══════════════════════════════════════════════════════════════

Ground in: {self.physical_anchor}

Pacing: {self.pacing.upper()}
Energy: {GENRE_DOCTRINES[self.genre]['energy_descriptions'][self.energy_level]}
"""

    if self.beat_directive:
        urgency_label = {
            "suggested": "OPPORTUNITY",
            "required": "THIS TURN",
            "overdue": "MUST HAPPEN NOW"
        }[self.beat_directive.urgency]

        section += f"""
─────────────────────────────────────────────────────────────────
BEAT [{urgency_label}]: {self.beat_directive.instruction}
─────────────────────────────────────────────────────────────────
{self.beat_directive.context}

Work this into your response naturally. Don't force it—find the organic moment.
"""

    section += f"""
Remember: You are a person with your own desires, moods, and boundaries.
"""

    return section
```

#### 3. Post-Evaluation Phase (Director detects beats)

```python
async def detect_beat_completion(
    self,
    beat: Beat,
    character_response: str,
    messages: List[Dict],
) -> bool:
    """Detect if a beat was delivered in the response."""

    if beat.detection_type == "automatic":
        # Character was instructed; assume delivered
        return True

    elif beat.detection_type == "keyword":
        keywords = beat.detection_criteria.split(",")
        response_lower = character_response.lower()
        return any(kw.strip().lower() in response_lower for kw in keywords)

    elif beat.detection_type == "semantic":
        # LLM evaluation
        prompt = f"""Did the character's response accomplish this beat?

Beat: {beat.description}
Criteria: {beat.detection_criteria}

Character's response:
{character_response}

Answer only: YES or NO"""

        result = await self._call_llm(prompt, model="haiku")
        return "YES" in result.upper()

    return False
```

#### 4. Choice-as-Message Flow

When a beat with a choice_point is detected:

```python
# In conversation.py streaming

if beat.choice_point and beat_detected:
    # Mark beat as awaiting choice
    director_state["beats"][beat.id]["choice_pending"] = True

    # Emit choice event with ACTUAL context from conversation
    yield {
        "type": "choice_point",
        "id": beat.choice_point.id,
        "prompt": beat.choice_point.prompt,  # Can be overridden with actual dialogue
        "choices": beat.choice_point.choices,
        "context": {
            "character_said": character_response[-200:],  # Last part of response
            "beat_id": beat.id,
        },
        "mode": "message_replacement",  # NEW: Tells frontend this replaces input
    }
```

### Frontend Changes

#### Choice as Message Input

```tsx
// In ChatContainer.tsx

{activeChoicePoint?.mode === "message_replacement" ? (
  // Choice replaces the message input entirely
  <div className="px-4 pb-4">
    <ChoiceInputCard
      prompt={activeChoicePoint.prompt}
      context={activeChoicePoint.context?.character_said}
      choices={activeChoicePoint.choices}
      onChoiceSelect={async (choiceId) => {
        // Selection becomes the user's message
        const choice = activeChoicePoint.choices.find(c => c.id === choiceId);
        await selectChoiceAsMessage(activeChoicePoint.id, choiceId, choice.label);
      }}
    />
  </div>
) : (
  // Normal message input
  <MessageInput ... />
)}
```

#### selectChoiceAsMessage

```typescript
const selectChoiceAsMessage = async (
  choicePointId: string,
  choiceId: string,
  choiceLabel: string
) => {
  // 1. Record the choice (sets flag)
  await api.sessions.recordChoice(sessionId, choicePointId, choiceId);

  // 2. Add choice as user message
  const userMessage: Message = {
    id: `user-${Date.now()}`,
    episode_id: episode.id,
    role: "user",
    content: choiceLabel,  // The choice becomes the message
    metadata: {
      is_choice: true,
      choice_point_id: choicePointId,
      choice_id: choiceId,
    },
    created_at: new Date().toISOString(),
  };
  setMessages(prev => [...prev, userMessage]);

  // 3. Clear choice state
  setActiveChoicePoint(null);

  // 4. Send to backend for character response
  // Note: Backend knows this was a choice, can respond appropriately
  await sendMessage(choiceLabel, { isChoice: true, choiceId });
};
```

---

## Migration from ADR-008

### Phase 1: Parallel Support

Both systems work simultaneously:

```python
# Old choice_points (turn-based) still work
choice_points=[{
    "id": "salary_question",
    "trigger": "turn:4",  # Legacy: turn-based
    ...
}]

# New beats with integrated choices
beats=[{
    "id": "ask_salary",
    "description": "Morgan asks about salary expectations",
    "character_instruction": "Find a natural moment to ask about their salary expectations",
    "target_turn": 3,
    "deadline_turn": 5,
    "detection_type": "semantic",
    "detection_criteria": "character asks about salary, compensation, or pay expectations",
    "choice_point": {
        "id": "salary_response",
        "prompt": "How do you respond?",
        "choices": [...]
    }
}]
```

### Phase 2: Migration

Update existing choice_points to beats:

```python
# Before (ADR-008)
choice_points=[{
    "id": "salary_question",
    "trigger": "turn:4",
    "prompt": "Morgan asks about your salary expectations. How do you respond?",
    "choices": [...]
}]

# After (ADR-009)
beats=[{
    "id": "salary_question_beat",
    "description": "Morgan asks about salary",
    "character_instruction": "Ask about their salary expectations. Be direct but warm.",
    "target_turn": 4,
    "deadline_turn": 6,
    "detection_type": "keyword",
    "detection_criteria": "salary,compensation,pay,money,expecting",
    "choice_point": {
        "id": "salary_question",
        "prompt": "How do you respond?",
        "choices": [...]
    }
}]
```

### Phase 3: Deprecation

Mark `choice_points` at episode level as deprecated. All interactive moments should be defined as `beats`.

---

## Comparison: Before and After

### Before (ADR-008)

```
Turn 4 starts
    ↓
Director checks: turn_count == 4?
    → YES: Trigger choice_point "salary_question"
    ↓
Frontend shows ChoiceCard with pre-written prompt:
    "Morgan asks about your salary expectations..."
    ↓
Meanwhile, Morgan's ACTUAL response might be:
    "So tell me about your experience at your last company..."
    ↓
User sees disconnected choice about salary
    ↓
User clicks choice → flag set
    ↓
User must still type a message
    ↓
Conversation continues (awkwardly)
```

### After (ADR-009)

```
Turn 3 starts (approaching target_turn 4)
    ↓
Director checks pending beats:
    → "ask_salary" beat approaching, add BeatDirective
    ↓
Director injects into character prompt:
    "BEAT [OPPORTUNITY]: Ask about their salary expectations.
     Find a natural moment for this."
    ↓
Morgan's response:
    "...I can tell you'd be a great fit. Before we go further,
     I should ask—what are you hoping for compensation-wise?"
    ↓
Director Phase 2 detects: beat landed (keyword: "compensation")
    → Mark beat as "detected"
    → Emit choice_point with mode: "message_replacement"
    ↓
Frontend shows ChoiceInputCard (replaces message input):
    "How do you respond?"
    - "I'm flexible, what's the range?"
    - "I'm looking for $X-Y"
    - "I'd rather discuss that later"
    ↓
User clicks choice
    → Choice becomes their message in conversation
    → Flag set
    → Morgan responds to what they said
    ↓
Conversation continues (seamlessly)
```

---

## Success Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Choice relevance | ~50% | 95%+ | Do choices match what character actually said? |
| Choice selection rate | Unknown | 80%+ | Do users engage with choices when shown? |
| Message after choice | Required | 0% | Choices should BE messages |
| Beat delivery rate | N/A | 90%+ | Do characters deliver beats when instructed? |

---

## Implementation Sequence

1. **Database**: Add `beats` JSONB column to `episode_templates`
2. **Models**: Add `Beat`, `BeatDirective` dataclasses
3. **Director Pre-Guidance**: Check pending beats, generate directives
4. **Director Post-Eval**: Detect beat completion semantically
5. **Conversation Service**: Emit choice events with `mode: message_replacement`
6. **Frontend**: `ChoiceInputCard` component that replaces input
7. **API**: Extend `recordChoice` to optionally send as message
8. **Migration**: Convert The Interview series to use beats

---

## Consequences

### Positive

1. **Coherent experience**: Choices respond to what character actually said
2. **Organic dialogue**: Characters work beats in naturally, not forced
3. **Unified flow**: No disconnect between UI elements and conversation
4. **Semantic detection**: System knows when beats land, not just when turns pass
5. **Author control**: Content creators specify beats, system ensures delivery

### Negative

1. **More authoring**: Beats require more detail than simple triggers
2. **LLM calls**: Semantic detection adds latency (mitigated by background processing)
3. **Complexity**: More state to track (beat status, directives)

### Neutral

1. **Backward compatible**: Existing choice_points still work
2. **Gradual migration**: Can convert series one at a time

---

## Related Documents

- **ADR-002**: Theatrical Production Model
- **ADR-008**: User Objectives System
- **DIRECTOR_PROTOCOL.md**: Director implementation details
- **EPISODE_STATUS_MODEL.md**: Episode lifecycle

---

## Conclusion

The Beat Contract System completes the theatrical model:

- **Episode** defines the beats that must occur (the script)
- **Director** ensures characters deliver them (rehearsal → performance)
- **Character** finds organic moments for each beat (actor interpretation)
- **User** responds to what actually happened (improv partner)

Choices become dialogue. Narrative becomes coherent. The user's presence truly matters.
