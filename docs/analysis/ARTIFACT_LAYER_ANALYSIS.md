# Artifact Layer Analysis: Memory Output Modality

> **Status**: ✅ Implemented
> **Created**: 2026-01-26
> **Implemented**: 2026-01-26
> **Context**: Strategic assessment of adding structured artifacts/reports as a memory output

## Implementation Summary

**Backend**:
- Migration: `supabase/migrations/107_artifacts.sql`
- Service: `api/api/src/app/services/artifacts.py` - ArtifactService with 4 artifact types
- Routes: `api/api/src/app/routes/artifacts.py` - Full REST API

**Frontend**:
- Types and API: `web/src/lib/api/client.ts` - `api.artifacts.*` methods

**Database Tables**:
- `artifacts` - Stored artifacts (first-class citizens)
- `artifact_events` - Timeline events for Thread Journey
- `thread_templates.artifact_config` - Template-specific artifact configuration

**API Endpoints**:
- `GET /artifacts/available` - Check artifact availability
- `GET /artifacts` - List all artifacts
- `GET /artifacts/thread-journey/{thread_id}` - Thread Journey artifact
- `GET /artifacts/domain-health/{domain}` - Domain Health artifact
- `GET /artifacts/communication-profile` - Communication Profile artifact
- `GET /artifacts/relationship-summary` - Relationship Summary artifact
- `POST /artifacts/events` - Log thread events

---

---

## Discourse Progression

### 1. Initial Proposition

The idea emerged from observing that the current dashboard (`/dashboard`) focuses on **infrastructure display** — showing raw memory, companion settings, conversation history — rather than **interpreted value**.

The metaphor offered was **건강검진 (health checkup)**: periodic structured evaluations that synthesize data into actionable reports. Examples cited:
- MBTI → produces a "type"
- Horoscope → produces a "reading"
- Personality tests → produce a "profile"
- Health checkups → produce a "report with metrics"

The pattern: **structured input → interpretive framework → named output artifact**

### 2. Initial Concerns Raised

Before accepting the proposition, several validity questions emerged:

| Concern | Question |
|---------|----------|
| Strategic fit | Does this align with "memory is the product" thesis? |
| Relationship model | Does this preserve companion-as-friend or create companion-as-analytics-tool? |
| GTM impact | Does this help activation or create distraction? |
| Gimmick risk | Would this feel like manufactured personality quizzes? |

### 3. Critical Reframe

The breakthrough came from reframing the proposition:

**Original framing**: "Should we add assessments as a feature?"

**Reframed**: "Should we add artifacts as an output modality of the memory system?"

This shifts artifacts from being a **parallel feature** to being a **different rendering** of the same underlying data:

```
Memory System (infrastructure)
    ↓
    ├─→ Daily Messages (push, conversational)
    ├─→ Chat Context (pull, conversational)
    └─→ Artifacts (pull, structured synthesis)
```

All three consume the same data. The difference is **output shape and delivery mechanism**, not source.

### 4. Key Insight: Accumulated Conversation Outputs

Artifacts should feel **earned from relationship**, not generated on demand.

Example flow:
```
Week 1-4: Daily messages about job search thread
    ↓
Companion observes: phase progression, sentiment, entities
    ↓
End of month: "Job Search Journey" artifact generated
    - Not new analysis
    - Structured rendering of what was already discussed
    - Feels earned, not manufactured
```

The artifact is a **collection of moments** the companion already delivered, now organized.

### 5. First Principles Validation

| Principle | Assessment |
|-----------|------------|
| Product thesis ("memory is the product") | ✅ Artifacts make memory more visible/valuable |
| Relationship model (companion as friend) | ✅ If framed as "what I've learned about you" |
| Value for ICP (people in transition) | ✅ Progress visibility, deeper understanding |
| Dashboard purpose | ✅ Transforms admin panel → reflection space |
| Constraint discipline | ⚠️ Requires artifacts to be memory-derived only |

### 6. Hard Constraints Established

**Must be true for artifacts to be valid**:

1. **Derived from conversation** — Every artifact line traces to real data
2. **Companion-voiced** — Feels like companion reflecting, not system analyzing
3. **Earned over time** — Can't generate meaningful artifact on day 1
4. **Additive, not distracting** — Doesn't compete with core daily message loop

**Red lines**:
- No generic personality quizzes that ignore conversation history
- No "take this assessment" that collects new data parallel to conversation
- No artifacts that make companion feel like a productivity tool

---

## Architectural Position

### Artifacts as Memory Output Modality

```
┌─────────────────────────────────────────────────────────────────┐
│                      MEMORY SYSTEM                               │
│  (threads, facts, patterns, follow-ups, conversation history)   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Conversation  │    │    Chat       │    │   Artifact    │
│    Output     │    │   Context     │    │    Output     │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ Daily messages│    │ Response gen  │    │ Structured    │
│ Push delivery │    │ Real-time     │    │ synthesis     │
│ Companion     │    │ Companion     │    │ Companion     │
│ speaks        │    │ responds      │    │ reflects      │
└───────────────┘    └───────────────┘    └───────────────┘
```

**Key principle**: All three are **renderers of the same underlying data**. Different shape, same source.

---

## Current Decision Point

The discourse has established:
1. ✅ Conceptual validity of artifacts as memory output
2. ✅ Alignment with service philosophy (if companion-voiced)
3. ✅ Hard constraints to prevent gimmickry
4. ⏳ **Pending**: Full scaffolding design that integrates with existing architecture

The next step is designing the artifact layer as an **integrated extension** of the existing memory system, templates, and domain layer — not as a bolted-on feature.

---

## Full Scaffolding Analysis

### Existing Architecture to Integrate With

| Component | Current Purpose | Artifact Layer Integration |
|-----------|-----------------|---------------------------|
| **user_context** | Stores facts, threads, follow-ups | Source data for all artifacts |
| **thread_templates** | Structures transitions with phases | Defines artifact types per domain |
| **patterns** (PatternService) | Detects mood/engagement trends | Feeds "What I've Noticed" artifacts |
| **scheduled_messages** | Tracks what companion has said | Source for "Our Conversations" artifacts |
| **MessageContext** | Aggregates data for message gen | Could aggregate for artifact gen |
| **domain_preferences** | User's primary life domains | Determines which artifacts are relevant |

### Artifact Types Derived from Existing Data

#### Type 1: Thread Journey Artifact
**Source**: `user_context` (category='thread') + `scheduled_messages` (topic_key references)

```
"Your Job Search Journey"
────────────────────────
Started: January 5, 2026
Current Phase: Interviewing

Timeline:
• Jan 5: You mentioned starting to look for new opportunities
• Jan 12: Applied to 3 companies (Google, Stripe, Notion)
• Jan 18: Phone screen with Google went well
• Jan 23: On-site scheduled for next week

What I've noticed:
• You're more energized talking about Stripe than Google
• You've mentioned "remote work" 8 times — seems important

Key details I'm tracking:
• Target role: Senior Engineer
• Timeline: Want decision by March
• Blocker: Negotiation anxiety
```

**Data mapping**:
- Timeline events → `scheduled_messages` where `topic_key` = this thread
- Phase → `user_context.phase`
- "What I've noticed" → PatternService observations
- Key details → `user_context.value.key_details`

#### Type 2: Domain Health Artifact
**Source**: All threads in domain + activity metrics

```
"Career Domain Overview"
────────────────────────
Active threads: 2
• Job Search (primary, interviewing phase)
• Side Project (stalled since Jan 10)

Activity: High
• 12 mentions in last 2 weeks
• You engage most when I ask about interviews

Momentum: ↑ Increasing
• Job search progressing through phases
• Side project may need attention or archiving
```

**Data mapping**:
- Thread list → `user_context` WHERE domain='career'
- Activity → COUNT of messages mentioning domain topics
- Momentum → Phase progression + recency

#### Type 3: Communication Profile Artifact
**Source**: Conversation history analysis

```
"How You Communicate"
────────────────────────
Based on 47 conversations over 6 weeks:

Your style: Processor
• You think out loud before deciding
• You rarely ask for direct advice
• Open-ended questions work better than yes/no

What helps you:
• Space to work through options
• Validation before suggestions
• Morning check-ins (you respond 80% more before noon)

How I'll adapt:
• I'll ask "what are you thinking?" more
• I'll hold suggestions until you've processed
```

**Data mapping**:
- Style inference → LLM analysis of conversation patterns
- Response patterns → `messages` timestamps + engagement
- Adaptation → Stored in `user_context` as companion behavior hints

#### Type 4: Relationship Summary Artifact
**Source**: Aggregate stats + highlights

```
"Our Relationship So Far"
────────────────────────
Together since: January 5, 2026 (21 days)
Conversations: 47
Things I've learned: 23 facts, 3 patterns

Highlights:
• Jan 12: You shared about the interview anxiety
• Jan 18: Celebrated the phone screen success
• Jan 20: Talked through the offer negotiation fears

What I'm following:
• Job search → Waiting on Google decision
• New city → Still exploring neighborhoods
• Side project → On pause

You've taught me:
• You need processing time before big decisions
• You appreciate direct questions over soft check-ins
• Weekend mornings are your reflective time
```

**Data mapping**:
- Stats → Aggregate queries on `conversations`, `user_context`
- Highlights → `messages` with high importance or milestone metadata
- "What I'm following" → Active threads
- "You've taught me" → `user_context` category='preference' or 'pattern'

### Artifact Generation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ArtifactService                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  generate_artifact(user_id, artifact_type) → Artifact           │
│                                                                  │
│  Artifact Types:                                                 │
│  ├─ THREAD_JOURNEY    → Per-thread timeline + insights          │
│  ├─ DOMAIN_HEALTH     → Per-domain overview                     │
│  ├─ COMMUNICATION     → How user communicates                   │
│  └─ RELATIONSHIP      → Overall companion relationship          │
│                                                                  │
│  Generation Flow:                                                │
│  1. Gather raw data from memory system                          │
│  2. Apply artifact template structure                           │
│  3. LLM synthesis for natural language sections                 │
│  4. Return structured artifact (not stored, generated fresh)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Artifact (dataclass)                         │
├─────────────────────────────────────────────────────────────────┤
│  artifact_type: ArtifactType                                    │
│  title: str                                                      │
│  generated_at: datetime                                          │
│  sections: List[ArtifactSection]                                │
│  data_sources: List[str]  # For transparency                    │
│  companion_voice: str  # Overall companion reflection           │
│  is_meaningful: bool  # False if insufficient data              │
└─────────────────────────────────────────────────────────────────┘
```

### Integration with Domain Layer

The domain layer (just implemented) provides natural artifact boundaries:

```
thread_templates
├── domain: "career"
├── template_key: "job_search"
├── phases: ["exploring", "applying", "interviewing", "waiting", "decided"]
└── NEW: artifact_config (JSONB)
    ├── journey_artifact_enabled: true
    ├── journey_milestones: ["first_application", "first_interview", "offer_received"]
    └── domain_health_weight: 1.0  # How much this template contributes to domain health
```

This allows **template-aware artifact generation**:
- Job search template knows what milestones matter
- Health templates might have different reflection prompts
- Creative templates might emphasize output over timeline

### API Design

```
GET /artifacts/available
→ Returns which artifacts have enough data to be meaningful

GET /artifacts/thread-journey/{thread_id}
→ Returns journey artifact for specific thread

GET /artifacts/domain-health/{domain}
→ Returns health artifact for domain

GET /artifacts/communication-profile
→ Returns communication style artifact

GET /artifacts/relationship-summary
→ Returns overall relationship artifact
```

**Key design choice**: Artifacts are **generated on request**, not stored. This ensures they're always current and reduces storage complexity. Only the **availability check** needs to be fast (can be cached).

### Availability Thresholds

Artifacts shouldn't be offered until meaningful:

| Artifact Type | Minimum Threshold |
|---------------|-------------------|
| Thread Journey | 3+ messages about thread, 7+ days old |
| Domain Health | 2+ threads in domain |
| Communication Profile | 20+ user messages |
| Relationship Summary | 14+ days, 10+ conversations |

### Dashboard Integration

Current dashboard sections:
- Memory (threads, facts)
- Companion Settings
- Conversation History

New section: **"Reflections"** or **"What I've Learned"**

```
┌─────────────────────────────────────────────────────────────────┐
│  Dashboard                                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Memory]  [Reflections]  [Settings]  [History]                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  What I've Learned About You                                ││
│  │                                                              ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      ││
│  │  │ Job Search   │  │ Career       │  │ How You      │      ││
│  │  │ Journey      │  │ Overview     │  │ Communicate  │      ││
│  │  │              │  │              │  │              │      ││
│  │  │ 21 days      │  │ 2 threads    │  │ 47 convos    │      ││
│  │  │ [View →]     │  │ [View →]     │  │ [View →]     │      ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘      ││
│  │                                                              ││
│  │  ┌──────────────────────────────────────────────────────┐  ││
│  │  │ "You've been on this journey for 3 weeks now.        │  ││
│  │  │  I've noticed you're most energized when talking     │  ││
│  │  │  about the Stripe opportunity. Want to explore why?" │  ││
│  │  └──────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Companion Voice Integration

Each artifact should feel like it comes **from** the companion:

**Not this** (system voice):
```
Analysis: User has shown 73% engagement with career topics.
Recommendation: Focus on career domain in future interactions.
```

**This** (companion voice):
```
I've noticed you light up when we talk about your career.
Out of our 47 conversations, you've brought up work in 34 of them.
It seems like this is where your energy is right now — and that makes sense
given everything happening with the job search.
```

### Future Extension: Push-Delivered Artifacts

Once pull-based artifacts are validated, natural extension:

```
Scheduler detects: User completed job search (phase = "decided")
    ↓
Generate: "Your Job Search Journey" artifact
    ↓
Push notification: "I put together a reflection on your job search journey. Want to see it?"
    ↓
Deep link to dashboard/artifacts
```

This creates **milestone moments** beyond daily check-ins.

---

## Implementation Considerations

### What Exists That Can Be Reused

| Existing | Reuse for Artifacts |
|----------|---------------------|
| `ThreadService.get_active_threads()` | Source thread data |
| `ThreadService.get_message_context()` | Pattern for aggregating user data |
| `PatternService.get_actionable_patterns()` | Source pattern observations |
| `DomainClassifier.get_template_by_key()` | Template-aware artifact config |
| `CompanionService.build_*_prompt()` | Pattern for LLM prompt construction |
| `LLMService.generate()` | Natural language synthesis |

### New Components Needed

1. **ArtifactService** — Orchestrates artifact generation
2. **Artifact models** — Dataclasses for artifact types
3. **Artifact API routes** — `/artifacts/*` endpoints
4. **Availability checker** — Determines which artifacts are ready
5. **Frontend components** — Artifact cards, detail views

### Estimated Scope

| Component | Effort | Dependencies |
|-----------|--------|--------------|
| ArtifactService + models | 4-6h | Existing services |
| API routes | 2h | ArtifactService |
| Availability logic | 2h | Query optimization |
| Frontend (basic) | 4-6h | API complete |
| Template integration | 2h | Domain layer (done) |
| **Total** | **14-18h** | — |

---

## Decision Framework

### Should We Build This?

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Strategic alignment | High | ✅ | Memory becomes more valuable |
| User value | High | ✅ | Progress visibility, reflection |
| GTM/Activation | Medium | ✅ | Dashboard return visits |
| Implementation cost | Medium | ⚠️ | 2-3 days focused work |
| Risk of distraction | Medium | ⚠️ | Must not compete with core loop |
| Differentiation | Low | ✅ | Most companions don't do this |

### Recommendation

**Build it, but sequence correctly**:

1. **First**: Validate core loop (daily messages → response → extraction)
2. **Then**: Add artifact layer as retention/depth feature
3. **Constraint**: Every artifact must trace to real conversation data

### What Would Change This Recommendation

- If core message loop isn't working → Fix that first
- If users don't visit dashboard → Artifacts won't help
- If implementation takes >1 week → Scope is too big, reduce

---

## Appendix: Example Artifact Response

```json
{
  "artifact_type": "thread_journey",
  "title": "Your Job Search Journey",
  "generated_at": "2026-01-26T10:30:00Z",
  "thread_id": "uuid-here",
  "is_meaningful": true,
  "sections": [
    {
      "type": "header",
      "content": {
        "started": "2026-01-05",
        "current_phase": "interviewing",
        "days_active": 21
      }
    },
    {
      "type": "timeline",
      "events": [
        {"date": "2026-01-05", "description": "Started exploring opportunities"},
        {"date": "2026-01-12", "description": "Applied to Google, Stripe, Notion"},
        {"date": "2026-01-18", "description": "Phone screen with Google"},
        {"date": "2026-01-23", "description": "On-site scheduled"}
      ]
    },
    {
      "type": "observations",
      "content": "You seem more energized when talking about Stripe than Google. You've mentioned 'remote work' 8 times — it seems important to you."
    },
    {
      "type": "key_details",
      "items": [
        {"label": "Target role", "value": "Senior Engineer"},
        {"label": "Timeline", "value": "Decision by March"},
        {"label": "Blocker", "value": "Negotiation anxiety"}
      ]
    }
  ],
  "companion_voice": "You've come a long way in three weeks. From 'maybe I should look around' to having an on-site scheduled — that's real momentum. I'll keep following along.",
  "data_sources": ["thread:job_search", "messages:34", "patterns:2"]
}
```

---

## References

- Domain Layer Implementation: [DOMAIN_LAYER_IMPLEMENTATION.md](../implementation/DOMAIN_LAYER_IMPLEMENTATION.md)
- Memory System: [MEMORY_SYSTEM.md](../design/MEMORY_SYSTEM.md) (if exists)
- GTM Definition of Done: [GTM_DEFINITION_OF_DONE.md](../GTM_DEFINITION_OF_DONE.md)
