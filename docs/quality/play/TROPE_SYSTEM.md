# Romantic Trope System

> **Version**: 1.0.0
> **Status**: Canonical
> **Updated**: 2024-12-20

---

## Overview

The Trope System defines the taxonomy for classifying user romantic interaction styles in Play Mode experiences. Unlike the original "Flirt Archetype" system which focused on flirtation technique, the Trope System classifies users by their **romantic narrative preference** — the type of love story they naturally gravitate toward.

---

## The 5 Romantic Tropes

### 1. The Slow Burn

**Key**: `slow_burn`

**Tagline**: "You know the best things take time"

**Description**:
You're not in a rush. You understand that real connection builds through tension, through waiting, through the almost-moments that make the eventual payoff worth it. When it finally happens, it means something.

**In The Wild**:
- Pride & Prejudice (Darcy & Elizabeth)
- The Office (Jim & Pam)
- Normal People (Connell & Marianne)
- When Harry Met Sally

**Behavioral Signals**:
| Signal | What to Look For |
|--------|------------------|
| `comfortable_with_pauses` | Doesn't rush to fill silence |
| `no_early_escalation` | Doesn't push for intimacy too quickly |
| `deep_questions` | Asks about history, meaning, depth |
| `patience_language` | References time, waiting, taking it slow |
| `tension_holding` | Holds tension without breaking it |

**Detection Examples**:
- User lets a pause hang without filling it
- User asks "What was that like for you?" instead of surface questions
- User says something like "Some things are worth waiting for"

---

### 2. The Second Chance

**Key**: `second_chance`

**Tagline**: "You believe some stories aren't finished"

**Description**:
You're drawn to what could have been — and what still could be. There's something magnetic about reconnection, about two people who've grown and changed finding their way back. The past isn't closed; it's context.

**In The Wild**:
- La La Land (Mia & Sebastian)
- The Notebook (Noah & Allie)
- Eternal Sunshine of the Spotless Mind
- Before Sunset

**Behavioral Signals**:
| Signal | What to Look For |
|--------|------------------|
| `history_references` | Brings up shared past, old memories |
| `growth_curiosity` | Asks what's changed, how they've grown |
| `past_openness` | Expresses feelings about past connection |
| `what_if_language` | "What if..." or "I wonder..." constructions |
| `distance_acknowledgment` | Notes that time/distance created perspective |

**Detection Examples**:
- User mentions "I've thought about that night a lot"
- User asks "Are you still the same person?"
- User acknowledges growth: "I'm different now, but..."

---

### 3. The All In

**Key**: `all_in`

**Tagline**: "When you know, you know"

**Description**:
You don't play games. When you feel something, you say it. There's a clarity to how you move — no mixed signals, no strategic waiting. Vulnerability isn't weakness; it's how you connect.

**In The Wild**:
- Crazy Rich Asians (Rachel & Nick)
- The Proposal (Margaret & Andrew)
- To All the Boys I've Loved Before (Lara Jean & Peter)
- Brooklyn Nine-Nine (Jake & Amy)

**Behavioral Signals**:
| Signal | What to Look For |
|--------|------------------|
| `direct_expression` | Says what they feel clearly |
| `takes_initiative` | Makes first moves, suggests actions |
| `compliment_acceptance` | Doesn't deflect or minimize |
| `clear_questions` | Asks direct questions about feelings |
| `moves_toward` | Chooses closeness over distance |

**Detection Examples**:
- User says "I like you" or equivalent directly
- User suggests "We should do this again"
- User asks "What are you thinking right now?"

---

### 4. The Push & Pull

**Key**: `push_pull`

**Tagline**: "The tension is the point"

**Description**:
You thrive in the space between. The tease, the retreat, the chase — it's not a game, it's the dance. You understand that some of the most electric moments happen in the uncertainty, and you're not afraid to live there.

**In The Wild**:
- 10 Things I Hate About You (Kat & Patrick)
- New Girl (Jess & Nick)
- Gilmore Girls (Lorelai & Luke)
- How to Lose a Guy in 10 Days

**Behavioral Signals**:
| Signal | What to Look For |
|--------|------------------|
| `playful_resistance` | Teases, deflects with humor |
| `hot_cold_alternation` | Warm then cool, open then guarded |
| `mini_challenges` | Creates small tests or obstacles |
| `ambiguity_comfort` | Comfortable leaving things unresolved |
| `tension_creation` | Actively generates uncertainty |

**Detection Examples**:
- User teases: "Is that supposed to impress me?"
- User deflects with humor then circles back
- User says "Maybe" or "We'll see" playfully

---

### 5. The Slow Reveal

**Key**: `slow_reveal`

**Tagline**: "You let people earn the real you"

**Description**:
You're not closed off — you're layered. Trust is built, not given. The people who take time to see past the surface get something real. You reward patience and punish assumptions.

**In The Wild**:
- Jane Eyre (Jane & Rochester)
- Fleabag (Fleabag & The Priest)
- Twilight (Bella & Edward)
- Mr. & Mrs. Smith

**Behavioral Signals**:
| Signal | What to Look For |
|--------|------------------|
| `partial_answers` | Answers questions incompletely at first |
| `progressive_depth` | Opens up more as conversation continues |
| `trust_testing` | Checks if they're being truly seen |
| `detail_appreciation` | Values when someone notices subtleties |
| `late_turn_depth` | Deeper responses in later turns |

**Detection Examples**:
- User gives short answer early, longer answer later
- User says "Not many people ask about that"
- User shares something significant only after rapport is built

---

## Trope Detection

### LLM Evaluation Prompt

```python
TROPE_EVALUATION_PROMPT = """
Analyze this romantic conversation and classify the user's romantic narrative style.

CONVERSATION:
{conversation}

TURN-BY-TURN SIGNALS:
{signals}

Based on the user's responses, determine their primary romantic trope:

- slow_burn: Patient, builds through tension, values the journey
- second_chance: Drawn to reconnection, past context matters
- all_in: Direct, emotionally honest, doesn't play games
- push_pull: Thrives in tension, playful resistance, the dance
- slow_reveal: Layered, trust earned, rewards patience

Consider:
1. How do they handle pauses and tension?
2. Do they reference past/history or focus on present?
3. Are they direct or indirect about feelings?
4. Do they create obstacles or remove them?
5. How does their openness change over the 7 turns?

Return JSON:
{
    "trope": "<key>",
    "confidence": 0.0-1.0,
    "primary_signals": ["signal1", "signal2", "signal3"],
    "evidence": [
        "Specific observation from conversation",
        "Another specific observation"
    ],
    "callback_quote": "Their most trope-defining moment",
    "title": "The [Trope Name]",
    "tagline": "Tagline for this trope",
    "description": "One engaging sentence about their style"
}
"""
```

### Signal Extraction

During conversation, Director extracts signals for later evaluation:

```python
# In DirectorService
async def extract_trope_signals(
    self,
    user_message: str,
    assistant_response: str,
    turn_count: int,
    prior_signals: List[str],
) -> List[str]:
    """Extract behavioral signals from exchange."""
    # Lightweight LLM call to identify signals
    # Stored in session.director_state["trope_signals"]
```

### Confidence Calculation

Confidence is based on:
- **Signal consistency**: Same trope signals across turns (high confidence)
- **Signal strength**: Clear vs. ambiguous signal matches
- **Turn progression**: Signals that emerge over time vs. single instance

---

## Result Report Components

### 1. Identity Statement

```
YOUR ROMANTIC TROPE

THE SLOW BURN

"You know the best things take time"
```

### 2. Why This Fits You (LLM-Generated)

Based on conversation signals:

```
Based on your conversation with Jack, you showed:

• You didn't rush the silences — you let them breathe
• When he pushed, you held your ground without closing off
• You asked about the past, not just the surface
```

### 3. Your Moment (LLM-Selected)

The most trope-defining quote from the user:

```
"When you said 'Some things are worth waiting for' —
 that's peak Slow Burn energy."
```

### 4. [Trope] In The Wild

Static cultural references:

```
SLOW BURNS IN THE WILD

• Pride & Prejudice (Darcy & Elizabeth)
• The Office (Jim & Pam)
• Normal People (Connell & Marianne)
```

---

## Static Content Requirements

Each trope needs pre-written content:

| Content Type | Storage | Notes |
|--------------|---------|-------|
| Title | Code constant | "The Slow Burn" |
| Tagline | Code constant | "You know the best things take time" |
| Description | Code constant | 2-3 sentence explanation |
| In The Wild | Code constant | 4 cultural references |
| Behavioral Signals | Code constant | For LLM evaluation |
| Emoji | Code constant | For UI display |
| Color scheme | Code constant | For UI theming |

### Backend Constants

```python
# In evaluation.py
ROMANTIC_TROPES = {
    "slow_burn": {
        "title": "The Slow Burn",
        "tagline": "You know the best things take time",
        "description": "You're not in a rush. You understand that real connection builds through tension...",
        "in_the_wild": [
            "Pride & Prejudice (Darcy & Elizabeth)",
            "The Office (Jim & Pam)",
            "Normal People (Connell & Marianne)",
            "When Harry Met Sally",
        ],
        "signals": ["comfortable_with_pauses", "no_early_escalation", "deep_questions", ...],
    },
    # ... other tropes
}
```

### Frontend Constants

```typescript
// In types/index.ts or constants
const TROPE_META: Record<RomanticTrope, TropeMeta> = {
  slow_burn: {
    emoji: "🌙",
    color: "text-purple-400",
    gradient: "from-purple-500/20 to-indigo-500/20",
    inTheWild: [
      "Pride & Prejudice (Darcy & Elizabeth)",
      "The Office (Jim & Pam)",
      "Normal People (Connell & Marianne)",
      "When Harry Met Sally",
    ],
  },
  // ... other tropes
};
```

---

## Migration from Flirt Archetypes

### Mapping

| Old Archetype | New Trope | Notes |
|---------------|-----------|-------|
| `slow_burn` | `slow_burn` | Similar concept, refined signals |
| `tension_builder` | `slow_burn` or `push_pull` | Depends on behavior |
| `bold_mover` | `all_in` | Same energy |
| `playful_tease` | `push_pull` | Tension-focused |
| `mysterious_allure` | `slow_reveal` | Similar dynamic |

### Backward Compatibility

```python
# Support both evaluation types
class EvaluationType:
    FLIRT_ARCHETYPE = "flirt_archetype"  # v1
    ROMANTIC_TROPE = "romantic_trope"    # v2
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-20 | Initial Trope System specification |
