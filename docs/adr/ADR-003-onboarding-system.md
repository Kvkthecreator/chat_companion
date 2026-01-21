# ADR-003: Onboarding System

**Status**: Draft
**Date**: 2025-01-21
**Deciders**: Kevin, Claude

## Context

Chat Companion's core value is personalized daily messages. But on Day 1, we know nothing about the user. Generic first messages ("Good morning! How are you?") are indistinguishable from other AI products, leading to churn before users experience the real value.

**The Cold Start Problem**: Users must provide enough context upfront for Day 1 to feel personal.

**The Solution**: Intentional friction via meaningful onboarding that:
1. Captures data for immediate personalization
2. Establishes the companion relationship
3. Creates user investment (completion = commitment)

## Decision

Implement **two distinct onboarding paths** that serve different user mindsets but produce the same output: a populated user profile ready for Day 1.

### Two Paths, One Outcome

```
┌─────────────────────────────────────────────────────────────┐
│                      Landing Page                            │
│                                                              │
│   "What if someone texted you first every morning?"         │
│                                                              │
│   [Take the Quiz - 2 min]        [Meet Your Companion →]    │
└─────────────────────────────────────────────────────────────┘
                    │                         │
                    ▼                         ▼
         ┌──────────────────┐      ┌──────────────────┐
         │   QUIZ PATH      │      │   CHAT PATH      │
         │                  │      │                  │
         │ User mindset:    │      │ User mindset:    │
         │ Curious, browsing│      │ Ready to try,    │
         │ Low commitment   │      │ High intent      │
         │                  │      │                  │
         │ Value prop:      │      │ Value prop:      │
         │ Self-discovery   │      │ Meet companion   │
         │ Shareable result │      │ immediately      │
         └────────┬─────────┘      └────────┬─────────┘
                  │                         │
                  ▼                         ▼
         ┌──────────────────┐      ┌──────────────────┐
         │ 8-10 questions   │      │ Conversational   │
         │ Multiple choice  │      │ onboarding with  │
         │ Fun, clickable   │      │ companion        │
         └────────┬─────────┘      └────────┬─────────┘
                  │                         │
                  ▼                         │
         ┌──────────────────┐               │
         │ Result: "You're  │               │
         │ a [Type]"        │               │
         │                  │               │
         │ [Share] [Continue]              │
         └────────┬─────────┘               │
                  │                         │
                  ▼                         │
         ┌──────────────────┐               │
         │ Brief companion  │               │
         │ intro + 2-3 Qs   │               │
         │ for context      │               │
         └────────┬─────────┘               │
                  │                         │
                  └────────────┬────────────┘
                               ▼
                  ┌──────────────────────────┐
                  │ Name your companion      │
                  │ Set timezone + wake time │
                  │ Connect Telegram         │
                  └────────────┬─────────────┘
                               ▼
                  ┌──────────────────────────┐
                  │ Day 1: Personalized      │
                  │ morning message          │
                  └──────────────────────────┘
```

### Path Comparison

| Aspect | Quiz Path | Chat Path |
|--------|-----------|-----------|
| **User mindset** | Curious, low commitment | Ready to try, high intent |
| **Entry friction** | Lower (clicking is easy) | Higher (requires engagement) |
| **Data quality** | Structured, clean | Rich, contextual |
| **Virality** | High (shareable results) | Low |
| **Relationship** | Delayed (companion intro after) | Immediate |
| **Time to complete** | 2-3 min | 3-5 min |
| **Best for** | Acquisition, top of funnel | Conversion, high-intent users |

### Quiz Path Details

#### Questions (8-10)

Questions reveal emotional patterns, social style, and support preferences.

```typescript
const quizQuestions = [
  {
    id: 'morning_first',
    question: "It's 7am. What do you reach for first?",
    options: [
      { value: 'messages', label: 'Phone (messages)' },
      { value: 'scroll', label: 'Phone (news/social)' },
      { value: 'linger', label: 'Lay there a while' },
      { value: 'coffee', label: 'Coffee first, always' }
    ]
  },
  {
    id: 'good_news',
    question: "When something good happens, you...",
    options: [
      { value: 'text', label: 'Text someone immediately' },
      { value: 'post', label: 'Post about it' },
      { value: 'private', label: 'Keep it to yourself' },
      { value: 'wait', label: 'Wait to tell someone in person' }
    ]
  },
  {
    id: 'cancelled_plans',
    question: "A friend cancels plans last minute. Honest reaction?",
    options: [
      { value: 'relieved', label: 'Relieved' },
      { value: 'disappointed', label: 'Disappointed but fine' },
      { value: 'annoyed', label: 'Annoyed' },
      { value: 'pivot', label: 'Already planning something else' }
    ]
  },
  {
    id: 'small_stuff',
    question: "How often do you feel like you have no one to tell the small stuff to?",
    options: [
      { value: 'often', label: 'Often' },
      { value: 'sometimes', label: 'Sometimes' },
      { value: 'rarely', label: 'Rarely' },
      { value: 'have_people', label: 'I have people for that' }
    ]
  },
  {
    id: 'ideal_message',
    question: "Your ideal morning message from a friend would be...",
    options: [
      { value: 'motivation', label: '"You\'ve got this today"' },
      { value: 'reflection', label: '"What\'s on your mind?"' },
      { value: 'warmth', label: '"Just thinking of you"' },
      { value: 'action', label: '"Let\'s make today count"' }
    ]
  },
  {
    id: 'stressed',
    question: "When you're stressed, you prefer...",
    options: [
      { value: 'listen', label: 'Someone to listen' },
      { value: 'advice', label: 'Practical advice' },
      { value: 'distraction', label: 'Distraction' },
      { value: 'space', label: 'Space' }
    ]
  },
  {
    id: 'routines',
    question: "How do you feel about routines?",
    options: [
      { value: 'love', label: 'Love them' },
      { value: 'aspirational', label: 'Aspirational but inconsistent' },
      { value: 'hate', label: 'Hate them' },
      { value: 'depends', label: 'Depends on the routine' }
    ]
  },
  {
    id: 'hardest',
    question: "What's hardest about your current life?",
    options: [
      { value: 'loneliness', label: 'Loneliness' },
      { value: 'motivation', label: 'Motivation' },
      { value: 'structure', label: 'Lack of structure' },
      { value: 'unseen', label: 'Feeling unseen' }
    ]
  }
];
```

#### Personality Types (4)

Each type maps to a companion communication style.

```typescript
const personalityTypes = {
  morning_reflector: {
    name: 'Morning Reflector',
    description: 'You process best in the quiet of morning. You want space to think before the day starts.',
    companion_approach: 'Asks open-ended questions, gives you room to share, doesn\'t rush.',
    preferences: {
      support_style: 'listener',
      feedback_type: 'validation',
      questions: 'many',
      message_tone: 'gentle'
    }
  },
  quiet_connector: {
    name: 'Quiet Connector',
    description: 'You crave connection but don\'t always reach out. You feel things deeply but keep them close.',
    companion_approach: 'Checks in warmly, creates safe space, doesn\'t push.',
    preferences: {
      support_style: 'friendly_checkin',
      feedback_type: 'validation',
      questions: 'moderate',
      message_tone: 'warm'
    }
  },
  momentum_seeker: {
    name: 'Momentum Seeker',
    description: 'You need activation energy. A nudge in the right direction gets you moving.',
    companion_approach: 'Brings energy, accountability, forward motion.',
    preferences: {
      support_style: 'accountability',
      feedback_type: 'challenge',
      questions: 'few',
      message_tone: 'energetic'
    }
  },
  steady_anchor: {
    name: 'Steady Anchor',
    description: 'You\'re grounded but sometimes feel unseen. You want someone who notices the small things.',
    companion_approach: 'Pays attention, remembers details, validates.',
    preferences: {
      support_style: 'motivational',
      feedback_type: 'balanced',
      questions: 'moderate',
      message_tone: 'affirming'
    }
  }
};
```

#### Type Scoring Algorithm

```typescript
function calculateType(answers: Record<string, string>): PersonalityType {
  const scores = {
    morning_reflector: 0,
    quiet_connector: 0,
    momentum_seeker: 0,
    steady_anchor: 0
  };

  // Scoring matrix (simplified)
  const scoring = {
    morning_first: {
      linger: { morning_reflector: 2 },
      messages: { quiet_connector: 1 },
      coffee: { steady_anchor: 1 },
      scroll: { momentum_seeker: 1 }
    },
    good_news: {
      private: { quiet_connector: 2, morning_reflector: 1 },
      wait: { steady_anchor: 2 },
      text: { momentum_seeker: 1 },
      post: { momentum_seeker: 1 }
    },
    ideal_message: {
      reflection: { morning_reflector: 2 },
      warmth: { quiet_connector: 2 },
      action: { momentum_seeker: 2 },
      motivation: { steady_anchor: 2 }
    },
    stressed: {
      listen: { quiet_connector: 2, morning_reflector: 1 },
      advice: { momentum_seeker: 1 },
      space: { morning_reflector: 2 },
      distraction: { steady_anchor: 1 }
    },
    hardest: {
      loneliness: { quiet_connector: 2 },
      motivation: { momentum_seeker: 2 },
      structure: { momentum_seeker: 1, morning_reflector: 1 },
      unseen: { steady_anchor: 2 }
    }
  };

  // Calculate scores
  for (const [questionId, answer] of Object.entries(answers)) {
    const questionScoring = scoring[questionId];
    if (questionScoring && questionScoring[answer]) {
      for (const [type, points] of Object.entries(questionScoring[answer])) {
        scores[type] += points;
      }
    }
  }

  // Return highest scoring type
  return Object.entries(scores)
    .sort(([, a], [, b]) => b - a)[0][0] as PersonalityType;
}
```

### Chat Path Details

Companion conducts conversational onboarding. Not a form - the first interaction.

```typescript
const chatOnboardingFlow = [
  {
    step: 'intro',
    companion_message: "Hey! I'm going to text you every morning - but I want it to actually matter to you, not just generic 'have a great day' stuff. Can I ask you a few things?",
    expects: 'acknowledgment',
    fallback_after: 30 // seconds
  },
  {
    step: 'name',
    companion_message: "What should I call you?",
    expects: 'name',
    saves_to: 'display_name'
  },
  {
    step: 'situation',
    companion_message: "Nice to meet you, {name}! What's going on in your life right now? New job, new city, just getting through the days - whatever it is.",
    expects: 'free_text',
    saves_to: 'user_context.thread.current_situation',
    importance: 'high'
  },
  {
    step: 'support_style',
    companion_message: "Got it. And when you wake up, what would actually help - a little motivation, someone to help you think through your day, or just a friendly 'hey, I'm thinking of you'?",
    expects: 'choice',
    options: ['motivation', 'reflection', 'friendly'],
    saves_to: 'preferences.support.style'
  },
  {
    step: 'wake_time',
    companion_message: "One more - what time do you usually wake up? I want to catch you at the right moment.",
    expects: 'time',
    saves_to: 'preferred_message_time'
  },
  {
    step: 'companion_name',
    companion_message: "Last thing - what would you like to call me? Pick a name that feels right.",
    expects: 'name',
    saves_to: 'companion_name',
    default: 'Aria'
  },
  {
    step: 'confirmation',
    companion_message: "Okay {name}, I'll text you tomorrow around {time}. Talk soon!",
    expects: null
  }
];
```

### Shared Final Steps

Both paths converge on:

1. **Name companion** (if not already done in chat)
2. **Set timezone** (auto-detect with confirmation)
3. **Set wake time** (if not already captured)
4. **Connect messaging channel** (Telegram primary)

### Data Output

Both paths produce the same user profile structure:

```typescript
interface OnboardingOutput {
  // User identity
  display_name: string;
  companion_name: string;

  // Timing
  timezone: string;
  preferred_message_time: string;  // "07:30"

  // From quiz (if taken)
  personality_type?: PersonalityType;
  quiz_answers?: Record<string, string>;

  // Preferences (explicit)
  preferences: {
    support: {
      style: 'friendly_checkin' | 'motivational' | 'accountability' | 'listener';
      feedback_type: 'validation' | 'challenge' | 'balanced';
      questions: 'few' | 'moderate' | 'many';
    };
    communication: {
      message_tone: 'gentle' | 'warm' | 'energetic' | 'affirming';
    };
  };

  // Initial context (for Core Memory)
  initial_context: {
    current_situation?: string;  // "Building startup, moved recently"
    hard_days?: string;          // From quiz or chat
  };

  // Metadata
  onboarding_path: 'quiz' | 'chat' | 'quiz_then_chat';
  completed_at: string;
}
```

### Integration with Memory (ADR-001)

Onboarding data flows into memory tiers:

| Onboarding Data | Memory Tier | Category |
|-----------------|-------------|----------|
| `display_name` | Core | `identity` |
| `current_situation` | Active | `thread` |
| `hard_days` | Core | `preference` |
| `personality_type` | Core | `identity` |

### Integration with Personalization (ADR-002)

Onboarding data flows into preferences:

| Onboarding Data | Preference Location |
|-----------------|---------------------|
| `support_style` | `users.preferences.support.style` |
| `feedback_type` | `users.preferences.support.feedback_type` |
| `message_tone` | `users.preferences.communication.message_tone` |
| `companion_name` | `users.companion_name` |
| `wake_time` | `users.preferred_message_time` |

### Database Schema

```sql
-- Quiz results storage
ALTER TABLE users ADD COLUMN personality_type TEXT;
ALTER TABLE users ADD COLUMN quiz_answers JSONB DEFAULT '{}';
ALTER TABLE users ADD COLUMN onboarding_path TEXT;  -- 'quiz', 'chat', 'quiz_then_chat'

-- Onboarding table (existing) - track progress
-- onboarding.data stores intermediate state
-- onboarding.current_step tracks position in flow
```

## Consequences

### Positive

- **Solves cold start**: Day 1 messages are personalized
- **Two acquisition channels**: Quiz (viral) + Direct (high-intent)
- **User investment**: Completion = commitment
- **Clean data**: Structured (quiz) + Rich (chat)
- **Shareable**: Quiz results drive organic growth

### Negative

- **Friction**: Some users may drop off during onboarding
- **Complexity**: Two paths to maintain
- **Quiz maintenance**: Questions/types may need tuning

### Neutral

- **A/B testable**: Can measure which path converts better
- **Extensible**: Can add more questions/types later

## Alternatives Considered

### Option A: Minimal Onboarding

Just name + timezone + connect Telegram.

**Rejected because**:
- Day 1 message would be generic
- Misses opportunity to establish relationship
- No data for personalization

### Option B: Quiz Only

No chat path, everyone takes quiz.

**Rejected because**:
- Some users want to meet companion immediately
- Loses rich contextual data from conversation
- Feels less personal

### Option C: Chat Only

No quiz, everyone does chat onboarding.

**Rejected because**:
- Loses viral/shareable component
- Higher friction for low-intent users
- Harder to get structured preference data

## Implementation Plan

### Phase 1: Chat Onboarding (Priority)
- Implement conversational onboarding flow
- Save to user profile + memory
- Connect to Telegram
- **Ship and validate retention**

### Phase 2: Quiz Flow
- Build quiz UI (8-10 questions)
- Implement type calculation
- Create shareable result cards
- Brief companion intro after quiz

### Phase 3: Flow Integration
- Landing page with both paths
- Analytics: track path → retention
- A/B test quiz vs chat conversion

### Phase 4: Optimization
- Tune quiz questions based on data
- Refine type descriptions
- Add more personality nuance

## Success Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Onboarding completion | >70% | Users must finish to get value |
| Day 1 reply rate | >50% | First message felt personal |
| Day 2 activation | >40% | They came back |
| Day 7 retention | >25% | Core experience is working |
| Quiz share rate | >10% | Viral growth potential |

## References

- [ADR-001: Memory Architecture](ADR-001-memory-architecture.md)
- [ADR-002: Personalization System](ADR-002-personalization-system.md)
- [features/MEMORY_SYSTEM.md](../features/MEMORY_SYSTEM.md)
- [features/PERSONALIZATION.md](../features/PERSONALIZATION.md)
