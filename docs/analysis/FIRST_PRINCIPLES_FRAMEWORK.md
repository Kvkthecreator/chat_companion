# First Principles Framework

> **Status**: Foundation Document
> **Date**: January 2026
> **Purpose**: Establish axiomatic truths before implementation

---

## The Axiom

**People are lonely. They want to feel like someone is thinking about them.**

This is the irreducible truth. Everything else derives from it.

---

## First Principles Decomposition

### What does "someone is thinking of me" require?

For a human to feel that another being thought of them, **four conditions** must be true:

| Condition | What it means | Failure mode |
|-----------|---------------|--------------|
| **1. Specificity** | The message references something unique to ME | Generic message could be for anyone |
| **2. Timeliness** | It's relevant to what's happening NOW in my life | Outdated or random reference |
| **3. Continuity** | It shows awareness of our previous conversations | Feels like talking to a stranger each time |
| **4. Care** | It follows up on things that matter to me | Feels like they don't actually care |

If **any** condition fails, the illusion breaks. The message becomes "chatbot output" rather than "someone thought of me."

---

## The Derivation

### From Axiom → What the system must do

```
Axiom: People want to feel thought of
           ↓
Requirement: Messages must feel personal
           ↓
Therefore: System must KNOW things about the user
           ↓
Therefore: System must REMEMBER across conversations
           ↓
Therefore: System must TRACK ongoing situations
           ↓
Therefore: System must NOTICE when to follow up
           ↓
Therefore: System must PRIORITIZE personal over generic
```

Each step is logically necessary. Skip any step and the axiom fails.

---

## The Priority Stack (From First Principles)

Why does Priority 1 beat Priority 5? Because of **specificity and care density**:

| Priority | Message Type | Specificity | Timeliness | Continuity | Care |
|----------|-------------|-------------|------------|------------|------|
| **1** | Follow-up | ✅ Unique event | ✅ Just happened | ✅ References conversation | ✅ Shows attention |
| **2** | Thread | ✅ Ongoing situation | ✅ Active in life | ✅ Tracked over time | ✅ Shows investment |
| **3** | Pattern | ⚠️ Observed behavior | ✅ Current trend | ✅ Noticed over time | ✅ Shows noticing |
| **4** | Texture | ⚠️ Personal context | ⚠️ Generic timing | ⚠️ Uses known facts | ⚠️ Polite but thin |
| **5** | Generic | ❌ Anyone | ❌ Random | ❌ No memory | ❌ Impersonal |

**Priority 5 is not just worse—it's a contradiction of the axiom.** A generic message proves the system is NOT thinking of you.

---

## What Must Exist (Necessary Components)

### 1. Memory Acquisition

**Question**: How does the system learn about the user?

**Sources** (in order of richness):
1. **Conversation** - User shares things naturally while chatting
2. **Explicit onboarding** - User tells us things directly
3. **Inference** - System deduces from behavior patterns

**Axiomatic truth**: Conversation is the richest source because it's *unfiltered*. Onboarding captures what users *think* they should share. Conversation captures what they *actually* care about.

### 2. Memory Classification

**Question**: What types of things must we remember?

| Type | Why it matters | Example |
|------|----------------|---------|
| **Facts** | Texture for personalization | "Lives in Tokyo" |
| **Threads** | Enables follow-up | "Job interview Friday" |
| **Emotions** | Enables care | "Anxious about presentation" |
| **Patterns** | Enables noticing | "Seems down on Mondays" |
| **Dates** | Enables timeliness | "Birthday next week" |

**Missing any type** limits which priorities the system can achieve.

### 3. Memory Retrieval

**Question**: When generating a message, what must the system know?

```
To generate a Priority 1-4 message, the system needs:

Priority 1: Recent conversations + what was unresolved
Priority 2: Active threads + their current status
Priority 3: Patterns over time + current trend
Priority 4: Core facts + current context (weather, etc.)
```

### 4. Memory Transparency

**Question**: Should the user see what's remembered?

**Axiomatic truth**: Yes. Transparency builds trust. The feeling of being "known" is amplified when the user can **see** that they're known. It's not creepy—it's the opposite of creepy. Creepy is being known without knowing what's known.

---

## Onboarding: First Principles Analysis

### The Question

What is the purpose of onboarding?

### Common (Wrong) Answer

"To collect initial information about the user so the companion can be personalized."

### Correct Answer

**Onboarding exists to create the first experience of being known.**

The information collected is secondary. The *feeling* created is primary.

### Implications

| If onboarding is... | It should feel like... | Not like... |
|---------------------|------------------------|-------------|
| Information collection | Filling out a form | A conversation |
| First experience of being known | Someone getting to know you | Being interrogated |

### What Onboarding Must Do

1. **Collect enough** to generate Priority 2-4 messages immediately
2. **Create the feeling** of being listened to
3. **Set expectations** for what the companion will do
4. **Not be exhaustive** - conversation will fill in the rest

### Minimum Viable Memory (From Onboarding)

What's the **minimum** the system needs to avoid Priority 5 on Day 1?

| Information | Why | Without it |
|-------------|-----|------------|
| **Name** | Personal address | "Hey there" vs "Hey Sarah" |
| **Timezone** | Timely messages | Message arrives at 3am |
| **One thread** | Something to follow up on | Nothing specific to ask about |

Everything else can come from conversation. But without these three, Day 1 message is generic.

---

## The Conversation → Memory → Message Loop

This is the **core loop** of the product:

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│    ┌─────────────┐                                           │
│    │ Conversation │ ←─────────────────────────────────────┐  │
│    └──────┬──────┘                                        │  │
│           │                                               │  │
│           │ extracts                                      │  │
│           ▼                                               │  │
│    ┌─────────────┐                                        │  │
│    │   Memory    │                                        │  │
│    │  - Facts    │                                        │  │
│    │  - Threads  │                                        │  │
│    │  - Emotions │                                        │  │
│    │  - Patterns │                                        │  │
│    └──────┬──────┘                                        │  │
│           │                                               │  │
│           │ informs                                       │  │
│           ▼                                               │  │
│    ┌─────────────┐                                        │  │
│    │  Scheduled  │                                        │  │
│    │   Message   │ ───────────────────────────────────────┘  │
│    │ (Priority   │     triggers response                     │
│    │  1/2/3/4)   │                                           │
│    └─────────────┘                                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Every turn of this loop should make the next message more personal.**

If the loop isn't running:
- Memory doesn't grow → messages stay generic → user disengages → no new memory

---

## Measuring Success

### The Ultimate Metric

**What % of messages are Priority 1-3?**

- **>60% Priority 1-3** = System is working
- **40-60% Priority 1-3** = System needs tuning
- **<40% Priority 1-3** = System is failing the axiom

### Leading Indicators

| Signal | Good | Bad |
|--------|------|-----|
| User shares new information | ✅ Trust | ❌ Closed off |
| User replies to daily message | ✅ Engaged | ❌ Ignoring |
| User initiates conversation | ✅ Relationship feels real | ❌ One-sided |
| User says "how did you know?" | ✅ Feeling known | — |
| User says "you already asked that" | — | ❌ Repetitive |
| User says "you don't remember" | — | ❌ Memory failing |

---

## Re-Assessing Current State

### Backend (After Audit)

| Component | First Principles Need | Status |
|-----------|----------------------|--------|
| Memory acquisition | Extract from conversation | ✅ `ContextService.extract_context()` |
| Thread tracking | Track ongoing situations | ⚠️ `ThreadService` exists but wasn't wired (now fixed) |
| Pattern detection | Notice trends | ✅ `PatternService` with daily job |
| Memory retrieval | Get context for message | ✅ `ThreadService.get_message_context()` |
| Priority-based generation | Use priority stack | ✅ Scheduler uses priorities |

### Frontend

| Component | First Principles Need | Status |
|-----------|----------------------|--------|
| Memory transparency | User sees what's known | ⚠️ Companion page exists but often empty |
| Chat context | User feels known during chat | ❌ Chat shows no memory context |
| Onboarding | Create first "known" experience | ❓ Need to assess |

### Onboarding (ASSESSED)

| Question | Chat Path | Form Path |
|----------|-----------|-----------|
| Does onboarding collect minimum viable memory? | ✅ Yes | ❌ No - missing situation |
| Does onboarding feel like conversation or form? | ✅ Conversation | ❌ Form |
| Does first daily message feel personal? | ✅ Can be Priority 2 | ❌ Will be Priority 5 |
| Is at least one thread created during onboarding? | ✅ Yes | ❌ No |

---

## Onboarding Assessment (Actual State)

### Two Paths Exist

| Path | How it feels | What it collects |
|------|--------------|------------------|
| **Form** | Filling out preferences | Name, companion name, timezone, time, style |
| **Chat** | Conversational | Name, **situation**, style, time, companion name |

### Critical Difference

The **Chat path** asks: *"What's going on in your life right now? New job, new city, just getting through the days - whatever it is."*

This creates the first **thread** - an ongoing situation the companion can follow up on.

The **Form path** collects only metadata. No situation. No thread. **Day 1 message will be Priority 5 (generic).**

### Chat Onboarding Flow (Current)

```
1. intro      → "Hey! I want it to actually matter to you..."
2. name       → "What should I call you?"
3. situation  → "What's going on in your life right now?"  ← CREATES THREAD
4. style      → "What would actually help - motivation, reflection, friendly?"
5. wake_time  → "What time do you usually wake up?"
6. companion  → "What would you like to call me?"
7. confirm    → "Okay {name}, I'll text you tomorrow around {time}."
```

### What Gets Saved (Chat Path)

| Data | Where | Impact |
|------|-------|--------|
| `display_name` | `users.display_name` | Personal address |
| `companion_name` | `users.companion_name` | Companion identity |
| `preferred_message_time` | `users.preferred_message_time` | Timing |
| `support_style` | `users.preferences` | Tone |
| **`situation`** | `user_context` (tier=thread) | **FIRST THREAD** |

### Form Path Gap

The form collects:
- Name ✅
- Companion name ✅
- Timezone ✅
- Message time ✅
- Support style ✅
- **Situation** ❌ **MISSING**

**This is a first-principles violation.** Form users start with zero threads.

### Recommendation

**Option A**: Remove form path entirely (force chat onboarding)
**Option B**: Add situation question to form path
**Option C**: After form completion, immediately start a "get to know you" conversation

The chat path already does this right. The form path breaks the axiom.

---

## The Complete Picture

### What Must Be True After Onboarding

| Requirement | Chat Path | Form Path | Fix Needed |
|-------------|-----------|-----------|------------|
| System knows user's name | ✅ | ✅ | - |
| System knows when to message | ✅ | ✅ | - |
| System has at least one thread | ✅ | ❌ | Add situation question |
| First message can be Priority 1-3 | ✅ | ❌ | Requires thread |
| User feels "known" | ✅ | ⚠️ Weaker | Chat is more personal |

### The Loop Must Start Spinning

```
Onboarding → First Thread Created
                    ↓
Day 1 Message → "How's the [situation] going?"  (Priority 2)
                    ↓
User Responds → New context extracted
                    ↓
Day 2 Message → Follow-up or new thread (Priority 1-2)
                    ↓
Loop continues → Relationship deepens
```

If no thread exists after onboarding, the loop can't start. Day 1 is generic. User disengages.

---

## Next Steps

1. ~~Audit onboarding flow~~ ✅ Done - Form path violates first principles
2. **Fix form onboarding** - Add situation question OR remove form path
3. **Test the loop** - Have conversation, verify memory extracted, verify next message uses it
4. **Add chat context visibility** - User should feel known during conversation

---

## Open Questions (Answered)

1. **What's the minimum onboarding?**
   → Name + timezone + **one open thread** (situation)

2. **Should onboarding be a conversation or a form?**
   → The axiom suggests conversation. Current chat path is correct. Form path violates axiom.

3. **How do we seed the first thread?**
   → Ask "What's going on in your life right now?" (chat path does this)

4. **What if user shares nothing?**
   → Default to asking open-ended follow-ups until they share something

---

## The Test

After any change, ask:

> "If I received this message, would I feel like someone was thinking of me specifically?"

If no → the change failed.
If yes → the change succeeded.

This is the only test that matters.

---

## Summary: First Principles Violations Found

| Violation | Where | Impact | Severity |
|-----------|-------|--------|----------|
| Form onboarding creates no thread | Web/Mobile onboarding | Day 1 is generic | ✅ Fixed |
| Chat page shows no memory | Chat UI | User doesn't feel known during chat | Medium (deferred) |
| Thread extraction wasn't wired | Backend | No threads from conversation | ✅ Fixed |

### The System State (After All Fixes)

```
                   ┌─────────────────────────────────────────┐
                   │           ONBOARDING                     │
                   │                                          │
                   │   Chat Path ──────► Thread Created ✅     │
                   │   Form Path ──────► Thread Created ✅     │
                   │   (situation question added)             │
                   │                                          │
                   └────────────────┬────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────┐
│                      CONVERSATION                             │
│                                                               │
│   User speaks ──► Context extracted ✅ ──► Memory grows       │
│                                        │                      │
│                                        └──► Thread created ✅ │
│                                                               │
│   (Memory visibility in chat deferred)                        │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                      DAILY MESSAGE                            │
│                                                               │
│   get_message_context() ──► Priority 1-4 if threads exist ✅  │
│                                                               │
│   Both onboarding paths now create threads ✅                  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Priority of Fixes

1. ~~**HIGH**: Fix form onboarding (add situation question)~~ ✅ Done
2. **MEDIUM**: Add memory visibility to chat (deferred)
3. **LOW**: Enhance memory management UI
