# Companion Presence System

> Design document for creating genuine emotional connection through proactive messaging

**Status:** Phase 1 Implemented
**Author:** Claude + Kevin
**Created:** 2026-01-25
**Updated:** 2026-01-25

---

## Implementation Status

### Phase 1 (Implemented) - Stop the Bleeding
- [x] `topic_key` column added to `scheduled_messages` for deduplication
- [x] `message_type` column added to track PRESENCE vs other types
- [x] Filter out topics used in last 7 days
- [x] PRESENCE message type (~20% of messages, no questions asked)
- [x] Back-off logic: prefer PRESENCE if user didn't respond to last outreach
- [x] Migration: `105_message_variety.sql`

### Phase 2 (Planned) - Companion State
- [ ] `companion_state` table for relationship tracking
- [ ] Closeness score, concern level
- [ ] Message type selection based on state

### Phase 3+ (Future)
- [ ] Inference layer
- [ ] Skip logic
- [ ] Richer relationship modeling

---

## 1. The Problem We're Solving

### Current State
The system treats daily messages as a **data retrieval problem**:
- Find things we know about the user
- Pick the "best" thing to mention
- Generate a message that references it

This produces messages that feel robotic even when technically "personalized":
- "How's testing the scheduler going?" (two days in a row)
- Always asks questions
- References data without judgment about relevance
- No sense of relationship rhythm

### The Real Challenge
**Data recall ≠ Understanding ≠ Connection**

A friend who remembers everything you said but brings it up awkwardly is worse than a friend who remembers less but has good timing and judgment.

---

## 2. Philosophy: What Makes Connection Feel Real

### Observations from Human Relationships

When someone checks in and it feels genuine, what's happening?

| Quality | Description | Current System |
|---------|-------------|----------------|
| **Timing intuition** | They reach out when it matters | Scheduled, mechanical |
| **Varied modes** | Sometimes ask, share, or just presence | Always asks questions |
| **Earned references** | Choose what's relevant *now*, not everything they know | Uses whatever data exists |
| **Surprise** | Notice things not explicitly stated | Only explicit data |
| **Restraint** | Don't over-ask, let silence exist | Fills every message slot |
| **Accumulation** | Relationship deepens over time | Each message is independent |

### The Insight

The goal isn't "mention personal data" — it's **"create a moment that feels right."**

Sometimes that moment is:
- Following up on something specific
- Acknowledging the vibe without asking anything
- Sharing something (thought, observation, quote)
- Just expressing presence ("thinking of you")
- Nothing at all (skip today)

---

## 3. Core Concept: Companion State

### Shift in Mental Model

**From:** Priority stack of things to mention
**To:** Companion has an internal state that informs what feels right

```
┌─────────────────────────────────────────────────────────┐
│                    COMPANION STATE                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Relationship Layer                                     │
│  ├─ closeness_level: How much have they shared?        │
│  ├─ recent_interaction_tone: Last few conversations    │
│  └─ relationship_age: Days since first conversation    │
│                                                         │
│  Awareness Layer                                        │
│  ├─ active_threads: What's happening in their life     │
│  ├─ pending_followups: Things to potentially ask about │
│  ├─ patterns: Mood/energy trends observed              │
│  └─ core_facts: Stable things we know                  │
│                                                         │
│  Message History Layer                                  │
│  ├─ last_outreach_type: What kind of message last?     │
│  ├─ last_outreach_topic: What did we mention?          │
│  ├─ topics_asked_recently: Don't repeat within N days  │
│  └─ days_since_outreach: Gap since last message        │
│                                                         │
│  Intuition Layer                                        │
│  ├─ concern_level: Should we be worried about them?    │
│  ├─ energy_read: What's their likely state today?      │
│  └─ receptivity_guess: Are they likely to engage?      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### How State Informs Messages

The companion "thinks":

> "Kevin and I have been talking for 2 weeks. He's shared a lot about work stuff.
> Yesterday I asked about the scheduler — he didn't respond yet.
> It's Sunday afternoon. He mentioned wanting weekends to be relaxing.
> I shouldn't ask about work again. Maybe just a low-key presence message."

This produces: *"Happy Sunday, Kevin. Hope you're getting some rest."*

Not: *"How's testing the scheduler going?"* (again)

---

## 4. Message Types (Not Priorities)

### Reframing

Current system has "priorities" (1-5) where lower numbers are "better."
This frames generic messages as failures.

**New framing:** Different message types for different moments. None are failures.

### Message Type Taxonomy

| Type | Intent | When to Use | Example |
|------|--------|-------------|---------|
| **FOLLOWUP** | Check on something specific | Has unresolved followup, hasn't been asked recently, timing is right | "How did the presentation go?" |
| **THREAD_CHECKIN** | Touch on ongoing situation | Active thread exists, feels natural to mention | "Hope the apartment search isn't too stressful" |
| **VIBE_READ** | Acknowledge their state | Pattern detected, or contextual (weather, day) | "Rainy Monday — hope you're hanging in there" |
| **PRESENCE** | Just show up, no ask | Don't have anything specific, or asked recently, or sensing they need space | "Thinking of you today" |
| **SHARE** | Offer something from companion | Build relationship texture, vary the dynamic | "Saw this and thought of you: [quote]" |
| **SKIP** | No message today | Asked something yesterday with no response, or intuition says give space | (no message sent) |

### Selection Logic (Conceptual)

```python
def choose_message_type(companion_state: CompanionState) -> MessageType:

    # Rule 1: Don't repeat the same type back-to-back
    if state.last_outreach_type == FOLLOWUP:
        exclude(FOLLOWUP)

    # Rule 2: If we asked something and got no response, back off
    if state.last_outreach_type in [FOLLOWUP, THREAD_CHECKIN]:
        if not state.user_responded_since_last_outreach:
            prefer(PRESENCE, SKIP)

    # Rule 3: Don't mention the same topic within N days
    if topic in state.topics_asked_recently:
        exclude that topic from FOLLOWUP/THREAD options

    # Rule 4: Weekend/evening might favor lighter touch
    if is_weekend or is_evening:
        prefer(PRESENCE, VIBE_READ)

    # Rule 5: If concern_level is high, lean toward checking in
    if state.concern_level > threshold:
        prefer(FOLLOWUP, THREAD_CHECKIN)

    # Rule 6: Occasionally share something (variety)
    if random() < 0.1 and has_shareable_content:
        consider(SHARE)

    # Rule 7: Sometimes just be present
    if no_urgent_followups and random() < 0.2:
        prefer(PRESENCE)

    return weighted_selection(available_types)
```

---

## 5. Data Model Changes

### New: `companion_state` Table

Tracks the evolving relationship state per user.

```sql
CREATE TABLE companion_state (
    user_id UUID PRIMARY KEY REFERENCES users(id),

    -- Relationship
    relationship_age_days INTEGER DEFAULT 0,
    closeness_score FLOAT DEFAULT 0.0,  -- 0-1, grows with engagement

    -- Message history
    last_outreach_at TIMESTAMPTZ,
    last_outreach_type TEXT,  -- FOLLOWUP, PRESENCE, etc.
    last_outreach_topic TEXT, -- What thread/followup was referenced
    user_responded_since BOOLEAN DEFAULT FALSE,

    -- Intuition signals
    concern_level FLOAT DEFAULT 0.0,  -- 0-1
    energy_read TEXT,  -- 'low', 'neutral', 'high'

    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### New: `outreach_history` Table

Track what we've mentioned to avoid repetition.

```sql
CREATE TABLE outreach_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),

    message_type TEXT NOT NULL,
    topic_referenced TEXT,  -- thread_id or followup question
    sent_at TIMESTAMPTZ DEFAULT NOW(),

    -- Did they engage?
    user_responded BOOLEAN DEFAULT FALSE,
    response_at TIMESTAMPTZ
);

-- Index for "what have we asked about recently?"
CREATE INDEX idx_outreach_recent ON outreach_history(user_id, sent_at DESC);
```

### Modify: `scheduled_messages` Table

Add richer tracking.

```sql
ALTER TABLE scheduled_messages
    ADD COLUMN message_type TEXT,  -- Replace priority_level conceptually
    ADD COLUMN topic_referenced TEXT,
    ADD COLUMN companion_state_snapshot JSONB;  -- State at generation time
```

---

## 6. Companion State Updates

### When State Changes

| Event | State Update |
|-------|--------------|
| User sends message | `user_responded_since = TRUE`, update `closeness_score` |
| Companion sends outreach | `last_outreach_at`, `last_outreach_type`, `user_responded_since = FALSE` |
| User engages with outreach | `user_responded_since = TRUE`, record in `outreach_history` |
| Pattern detected (low mood) | `concern_level` increases |
| Days pass with no interaction | `concern_level` may increase, `energy_read` uncertain |
| Thread resolved | Remove from active considerations |

### Closeness Score Factors

```python
def update_closeness(state: CompanionState, event: Event):
    """
    Closeness grows with:
    - Conversation depth (longer exchanges)
    - Vulnerability (emotional topics shared)
    - Consistency (regular engagement over time)
    - Reciprocity (they respond to our outreach)

    Closeness decays with:
    - Long silences (slowly)
    - Ignored outreach (they don't respond)
    """
    pass
```

---

## 7. Generation Architecture

### Current Flow (Problematic)

```
Scheduler triggers
    → Get user context (facts, threads, patterns)
    → Pick highest priority
    → Generate message with that priority's template
    → Send
```

### New Flow

```
Scheduler triggers
    → Load CompanionState
    → Choose MessageType based on state + rules
    → If SKIP: record skip, done
    → Build prompt with:
        - Message type intent
        - Relevant context for that type
        - What NOT to mention (recent topics)
        - Tone guidance from relationship state
    → Generate message
    → Update CompanionState (last_outreach_*, etc.)
    → Record in outreach_history
    → Send
```

### Prompt Structure (New)

```python
def build_outreach_prompt(state: CompanionState, message_type: MessageType) -> str:

    prompt = f"""You are {companion_name}, reaching out to {user_name}.

RELATIONSHIP CONTEXT:
- You've known them for {state.relationship_age_days} days
- Recent tone: {state.recent_interaction_tone}
- Last outreach: {state.last_outreach_type} about "{state.last_outreach_topic}"
- They {'responded' if state.user_responded_since else 'haven\'t responded yet'}

TODAY'S CONTEXT:
- Day: {day_of_week}, Time: {local_time}
- Weather: {weather}

YOUR INTENT TODAY: {message_type.description}
{message_type.specific_context}

DO NOT:
- Ask about: {state.topics_asked_recently}  # Avoid repetition
- {'Ask any questions' if message_type == PRESENCE else ''}
- Sound like a notification or reminder
- Be overly enthusiastic or performative

DO:
- Sound like a real friend checking in
- Keep it brief (1-3 sentences)
- Match their energy ({state.energy_read})

Just write the message, nothing else."""

    return prompt
```

---

## 8. Implementation Phases

### Phase 1: Foundation (Stop the Bleeding)
**Goal:** Stop obvious repetition, add basic variety

- [ ] Add `outreach_history` table
- [ ] Track what topic was used in each message
- [ ] Filter out recently-used topics from consideration
- [ ] Add PRESENCE message type (no question asked)
- [ ] 20% of messages randomly choose PRESENCE over FOLLOWUP

**Outcome:** Messages won't repeat the same topic back-to-back

### Phase 2: Companion State (Basic)
**Goal:** Messages aware of relationship rhythm

- [ ] Add `companion_state` table
- [ ] Track `last_outreach_type`, `user_responded_since`
- [ ] If user didn't respond to last outreach, prefer PRESENCE/lighter touch
- [ ] Basic message type selection logic

**Outcome:** Companion "backs off" if messages aren't landing

### Phase 3: Richer State
**Goal:** Genuine intuition

- [ ] Implement `closeness_score` calculation
- [ ] Implement `concern_level` from patterns
- [ ] Add SKIP logic (sometimes send nothing)
- [ ] Time-of-day and day-of-week awareness in type selection

**Outcome:** Messages feel more situationally appropriate

### Phase 4: Inference Layer
**Goal:** Companion notices things not explicitly stated

- [ ] "They've seemed stressed lately" (inferred from message tone)
- [ ] "They might be busy with X" (inferred from context)
- [ ] Companion can reference these inferences carefully

**Outcome:** Companion feels perceptive, not just recall-based

---

## 9. Success Metrics

### Qualitative
- Messages feel varied week-over-week
- User doesn't notice patterns/templates
- Messages feel "right" for the moment

### Quantitative
- **Topic repetition rate:** Same topic within 7 days (target: <5%)
- **Message type distribution:** No single type >50% of messages
- **Response rate by type:** Does FOLLOWUP actually get more responses than PRESENCE?
- **Skip rate:** ~10-20% of slots result in no message (healthy restraint)

---

## 10. Open Questions

1. **Should the companion have "moods"?** Could vary message style based on companion's simulated state, not just user's.

2. **How do we handle new users?** Before we know them, what's the right approach? Probably more PRESENCE, fewer specific asks.

3. **Should users see/control this?** "Kiko seems to understand when to give me space" — or explicit settings?

4. **How does this interact with user-initiated conversations?** If they message us, does that reset outreach timing?

5. **What about multi-channel?** If we send email and push, how does state track across?

---

## 11. Appendix: Current vs. New Comparison

### Scenario: User mentioned job interview on Monday

**Current System (Tuesday):**
```
Priority 1: FOLLOWUP detected
Prompt: "The user mentioned something we should ask about:
        - How did the interview go?"
Output: "Hey! How did the interview go yesterday?"
```

**Current System (Wednesday, user didn't respond):**
```
Priority 1: FOLLOWUP still pending
Prompt: (same as above)
Output: "Hey! Curious how that interview went!"
```

**New System (Tuesday):**
```
State: relationship_age=14d, closeness=0.6, last_outreach=PRESENCE
Type selection: FOLLOWUP (have pending, timing right, haven't asked)
Output: "Hey! How did the interview go yesterday?"
Update: last_outreach_type=FOLLOWUP, topic="job_interview", user_responded_since=FALSE
```

**New System (Wednesday, user didn't respond):**
```
State: last_outreach=FOLLOWUP about "job_interview", user_responded_since=FALSE
Type selection: Exclude FOLLOWUP (just asked, no response). Prefer PRESENCE.
Output: "Hope your week is off to a good start."
Update: last_outreach_type=PRESENCE, topic=NULL
```

**New System (Thursday):**
```
State: last_outreach=PRESENCE, 2 days since interview with no update
Type selection: Could try THREAD_CHECKIN (softer than direct followup)
Output: "Been thinking about you — hope the job search is going okay."
```

---

## 12. Next Steps

1. **Review this document** — Does this philosophy resonate?
2. **Prioritize phases** — Start with Phase 1 to stop immediate pain?
3. **Schema review** — Any concerns with proposed tables?
4. **Prompt iteration** — Test new prompt structures before full implementation

---

*"The goal isn't to remember everything. It's to know when to remember, and when to just be there."*
