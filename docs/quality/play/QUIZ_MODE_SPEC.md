# Quiz Mode Specification

> **Version**: 1.1.0
> **Status**: Implemented
> **Updated**: 2025-12-21

---

## Overview

Quiz Mode is a static, quiz-based experience where users answer 5 multiple choice questions and receive a romantic trope result. This approach prioritizes:

1. **Consistent quality** - No LLM variance in the experience
2. **Proven viral format** - MBTI/BuzzFeed-style quizzes have established shareability
3. **Fast iteration** - Questions can be A/B tested easily
4. **Same payoff** - Trope identity result remains the viral hook

---

## Quiz Theme

### "What's Your Red Flag?"
- Self-deprecating, funny framing
- High shareability - people love roasting themselves
- Maps cleanly to existing tropes

---

## User Flow

```
/play
  └── Quiz Landing Page
        ├── Title: "What's Your Red Flag?"
        ├── Subtitle: "5 questions. brutal honesty. no judgment (ok maybe a little)"
        └── CTA: "Find Out"
              │
              ▼
        Question Flow (5 questions)
        ├── Q1 → Q2 → Q3 → Q4 → Q5
        ├── Progress indicator (bar)
        └── Each question: scenario + 5 answer options (one per trope)
              │
              ▼
        Result Page (Elaborate)
        ├── Hero: emoji + "your red flag is..." + title + tagline
        ├── Description card
        ├── "In Relationships" section
        ├── Strengths & Challenges (2-column grid)
        ├── Advice card (highlighted)
        ├── Compatibility ("you vibe with")
        ├── Share button (primary CTA)
        ├── Try again button
        └── "Try Episode 0" section
              ├── Hometown Crush card
              └── Coffee Shop Crush card
```

---

## Question Design

### Format
Each question presents a scenario with 5 answer options. Each option maps to one trope.

### Scoring
- Each answer adds 1 point to its corresponding trope
- After all questions, highest score = result trope
- Ties broken by: last answered trope wins (recency = stronger signal)

### Question Style
Scenario-based with a casual, slightly unhinged tone.

---

## The 5 Questions

### Q1: The Text Back
**"They finally text back after 6 hours. You:"**

| Option | Trope |
|--------|-------|
| Wait exactly 6 hours and 1 minute to respond. Balance. | push_pull |
| Already drafted 4 versions of your reply in Notes | slow_burn |
| "Finally! I was starting to spiral" (send immediately) | all_in |
| Check if they've been active elsewhere first | slow_reveal |
| Wonder if this is the universe giving you a second chance | second_chance |

### Q2: The Ex Situation
**"Your ex likes your Instagram story. You:"**

| Option | Trope |
|--------|-------|
| Screenshot it and send to the group chat for analysis | slow_burn |
| Already know what it means. Time to have The Talk. | all_in |
| Like something of theirs back. The game is on. | push_pull |
| Ignore it but check their profile 3 times that day | slow_reveal |
| Feel a flutter. Maybe the timing is finally right? | second_chance |

### Q3: The First Date Energy
**"On a first date, you're most likely to:"**

| Option | Trope |
|--------|-------|
| Ask about their last relationship (for research purposes) | second_chance |
| Tell them you're having a great time. Out loud. With words. | all_in |
| Tease them until they're slightly confused but intrigued | push_pull |
| Give them just enough to want a second date | slow_reveal |
| Enjoy the tension of not knowing where this is going | slow_burn |

### Q4: The Feelings Check
**"When you catch feelings, you:"**

| Option | Trope |
|--------|-------|
| Tell them. Life's too short for games. | all_in |
| Create situations to see if they feel it too | push_pull |
| Sit with it for weeks before doing anything | slow_burn |
| Drop hints and see if they're paying attention | slow_reveal |
| Wonder if this is fate correcting a past mistake | second_chance |

### Q5: The Dealbreaker
**"Your biggest dating dealbreaker is someone who:"**

| Option | Trope |
|--------|-------|
| Rushes things before the tension has time to build | slow_burn |
| Plays too hard to get (that's YOUR move) | push_pull |
| Can't handle emotional honesty | all_in |
| Asks too many questions too soon | slow_reveal |
| Refuses to believe people can change | second_chance |

---

## Result Page Structure (Implemented)

```
┌─────────────────────────────────────────────────────────────────┐
│                          [emoji]                                │
│                   your red flag is...                           │
│                       SLOW BURN                                 │
│        the tension is the whole point and you know it           │
├─────────────────────────────────────────────────────────────────┤
│  You'd rather wait three seasons for a kiss than rush it...    │
├─────────────────────────────────────────────────────────────────┤
│  💕 In Relationships                                            │
│  You're the person who makes every glance feel loaded...       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐ ┌─────────────────────┐               │
│  │ ✨ Strengths        │ │ ⚠️ Challenges       │               │
│  │ • Point 1           │ │ • Point 1           │               │
│  │ • Point 2           │ │ • Point 2           │               │
│  │ • Point 3           │ │ • Point 3           │               │
│  └─────────────────────┘ └─────────────────────┘               │
├─────────────────────────────────────────────────────────────────┤
│  "Not everything needs to marinate..."  (advice, highlighted)  │
├─────────────────────────────────────────────────────────────────┤
│                      you vibe with                              │
│                  SLOW REVEAL & PUSH & PULL                      │
└─────────────────────────────────────────────────────────────────┘

                    [ share result ]  ← Primary CTA
                      [ try again ]

┌─────────────────────────────────────────────────────────────────┐
│                  ready for the real thing?                      │
│    try episode 0 — free interactive romance stories            │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  Hometown       │    │  Coffee Shop    │                    │
│  │  Crush          │    │  Crush          │                    │
│  └─────────────────┘    └─────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘

                      ep-0.com/play
```

---

## Technical Implementation

### File Locations

| Component | File |
|-----------|------|
| Quiz data & scoring | `web/src/lib/quiz-data.ts` |
| Quiz types | `web/src/types/index.ts` |
| Progress component | `web/src/components/quiz/QuizProgress.tsx` |
| Question component | `web/src/components/quiz/QuizQuestion.tsx` |
| Result component | `web/src/components/quiz/QuizResult.tsx` |
| Main page | `web/src/app/play/page.tsx` |

### No Backend Required

Quiz mode is **entirely frontend**:
- Questions stored in `quiz-data.ts`
- Scoring calculated client-side
- No API calls during quiz flow
- Share via native share API or clipboard copy

### Scoring Logic

```typescript
function calculateTrope(answers: Record<number, RomanticTrope>): RomanticTrope {
  const scores: Record<RomanticTrope, number> = {
    slow_burn: 0,
    second_chance: 0,
    all_in: 0,
    push_pull: 0,
    slow_reveal: 0,
  };

  let lastAnswered: RomanticTrope = 'slow_burn';

  for (const trope of Object.values(answers)) {
    scores[trope]++;
    lastAnswered = trope;
  }

  const maxScore = Math.max(...Object.values(scores));
  const winners = Object.entries(scores)
    .filter(([_, score]) => score === maxScore)
    .map(([trope]) => trope as RomanticTrope);

  // Tie-breaker: last answered wins
  if (winners.length > 1 && winners.includes(lastAnswered)) {
    return lastAnswered;
  }

  return winners[0];
}
```

---

## Success Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Completion rate | 90%+ | Quiz is short (<60 seconds) |
| Share rate | 35%+ | Primary viral mechanism |
| Episode 0 click-through | 15%+ | Conversion to full stories |
| Time to complete | <60s | Quick, snackable experience |

---

## Future Considerations

- Multiple quiz themes (same tropes, different questions)
- Randomize question order
- A/B test question variations
- Add "your match" feature (compare with friends)
- OG image generation for share links

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2025-12-21 | Updated with elaborate result page structure (strengths, challenges, advice, compatibility) |
| 1.0.0 | 2025-12-21 | Initial quiz mode spec |
