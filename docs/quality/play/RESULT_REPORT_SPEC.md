# Result Report Specification

> **Version**: 1.0.0
> **Status**: Canonical
> **Updated**: 2024-12-20

---

## Purpose

This document specifies the result report structure for Play Mode experiences. The report is designed for **maximum shareability** — it should feel like discovery, not diagnosis.

---

## Report Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ✨ YOUR ROMANTIC TROPE                                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │            THE SLOW BURN                                │   │
│  │                                                         │   │
│  │     "You know the best things take time"                │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  WHY THIS FITS YOU                                              │
│                                                                 │
│  Based on your conversation with Jack, you showed:             │
│                                                                 │
│  • You didn't rush the silences — you let them breathe         │
│  • When he pushed, you held your ground without closing off    │
│  • You asked about the past, not just the surface              │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  YOUR MOMENT                                                    │
│                                                                 │
│  "When you said 'Some things are worth waiting for' —          │
│   that's peak Slow Burn energy."                               │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  SLOW BURNS IN THE WILD                                        │
│                                                                 │
│  • Pride & Prejudice (Darcy & Elizabeth)                       │
│  • The Office (Jim & Pam)                                      │
│  • Normal People (Connell & Marianne)                          │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  [ Share Result ]              [ Continue with Jack → ]        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section Specifications

### 1. Identity Statement

**Purpose**: Give users language to describe themselves.

**Components**:
| Element | Source | Notes |
|---------|--------|-------|
| Section header | Static | "YOUR ROMANTIC TROPE" |
| Trope name | Static per trope | "THE SLOW BURN" |
| Tagline | Static per trope | "You know the best things take time" |

**Styling**:
- Trope name: Large, bold, trope-colored
- Tagline: Italic, subtle, quotation marks

### 2. Why This Fits You

**Purpose**: Personalization — proves the AI "saw" them.

**Source**: LLM-generated from conversation signals.

**Format**:
```
Based on your conversation with [Character], you showed:

• [Observation 1]
• [Observation 2]
• [Observation 3]
```

**Generation Requirements**:
- Exactly 3 observations
- Each observation references specific behavior
- Uses second person ("you")
- Active voice
- Max 15 words per observation

**LLM Prompt Section**:
```
Generate 3 specific observations about the user's romantic style based on their conversation. Each should:
- Reference a specific moment or pattern
- Use active, engaging language
- Be 10-15 words
- Avoid generic statements

Example observations:
- "You didn't rush the silences — you let them breathe"
- "When he pushed, you held your ground without closing off"
- "You asked about the past, not just the surface"
```

### 3. Your Moment

**Purpose**: The "whoa" reaction — they remember saying that.

**Source**: LLM-selected from user's actual messages.

**Format**:
```
"When you said '[actual quote]' — that's peak [Trope] energy."
```

**Requirements**:
- Must be an actual quote from user
- Max 10 words from their message
- Framing should explain why it's trope-aligned
- Can paraphrase if quote is too long

**LLM Prompt Section**:
```
Select the user's most trope-defining moment from the conversation.

Requirements:
- Quote directly from their message (or paraphrase if >10 words)
- Explain why this is peak [trope] energy
- Format: "When you said '[quote]' — [explanation]"
```

### 4. [Trope] In The Wild

**Purpose**: Cultural anchoring — associates them with beloved stories.

**Source**: Static per trope (curated examples).

**Format**:
```
[TROPE NAME] IN THE WILD

• [Reference 1] ([Characters])
• [Reference 2] ([Characters])
• [Reference 3] ([Characters])
```

**Requirements**:
- Exactly 3-4 references per trope
- Mix of classic and contemporary
- Recognizable to broad audience
- Include character names

**Static Content by Trope**:

| Trope | References |
|-------|------------|
| slow_burn | Pride & Prejudice (Darcy & Elizabeth), The Office (Jim & Pam), Normal People (Connell & Marianne), When Harry Met Sally |
| second_chance | La La Land (Mia & Sebastian), The Notebook (Noah & Allie), Eternal Sunshine of the Spotless Mind, Before Sunset |
| all_in | Crazy Rich Asians (Rachel & Nick), The Proposal (Margaret & Andrew), To All the Boys I've Loved Before (Lara Jean & Peter), Brooklyn Nine-Nine (Jake & Amy) |
| push_pull | 10 Things I Hate About You (Kat & Patrick), New Girl (Jess & Nick), Gilmore Girls (Lorelai & Luke), How to Lose a Guy in 10 Days |
| slow_reveal | Jane Eyre (Jane & Rochester), Fleabag (Fleabag & The Priest), Twilight (Bella & Edward), Mr. & Mrs. Smith |

### 5. Actions

**Purpose**: Clear next steps.

**Primary CTA**: Share Result
- Large, prominent button
- Triggers native share or clipboard copy
- Share text: "I'm [Trope Name]! What's your romantic trope? [URL]"

**Secondary CTAs** (Auth-gated):
- "Continue with [Character] →"
- "Save to profile"
- "Try another story"

---

## Share Card (OG Image)

**Purpose**: Visual for social sharing.

**Design**:
```
┌─────────────────────────────────────┐
│                                     │
│  I'm a SLOW BURN                    │
│                                     │
│  "You know the best things          │
│   take time"                        │
│                                     │
│  What's your romantic trope?        │
│  ep-0.com/play                      │
│                                     │
└─────────────────────────────────────┘
```

**Requirements**:
- 1200x630px (Facebook/LinkedIn) or 1200x1200px (Instagram)
- Trope name prominent
- Tagline included
- CTA: "What's your romantic trope?"
- ep-0 branding subtle

**Dynamic vs. Static**:
- **Option A**: Pre-rendered per trope (5 images)
- **Option B**: Dynamic generation via Vercel OG

**Recommendation**: Start with static (faster), add dynamic for personalization later.

---

## Data Model

### Evaluation Result Schema

```python
class RomanticTropeResult(BaseModel):
    trope: str  # slow_burn, second_chance, etc.
    confidence: float  # 0.0-1.0
    primary_signals: List[str]  # Signal keys detected
    evidence: List[str]  # 3 observations for "Why This Fits You"
    callback_quote: str  # User quote for "Your Moment"
    title: str  # "The Slow Burn"
    tagline: str  # "You know the best things take time"
    description: str  # Full description
```

### API Response

```typescript
interface PlayResultResponse {
  evaluation_type: "romantic_trope";
  result: {
    trope: RomanticTrope;
    confidence: number;
    primary_signals: string[];
    evidence: string[];  // NEW: Personalized observations
    callback_quote: string;  // NEW: User's defining moment
    title: string;
    tagline: string;
    description: string;
  };
  share_id: string;
  share_url: string;
  character_id: string;
  character_name: string;
  series_id: string | null;
}
```

---

## Frontend Components

### TropeResultCard

**Props**:
```typescript
interface TropeResultCardProps {
  trope: RomanticTrope;
  title: string;
  tagline: string;
  description: string;
  confidence: number;
  evidence: string[];
  callbackQuote: string;
  characterName: string;
}
```

**Structure**:
```tsx
<TropeResultCard>
  <IdentitySection trope={trope} title={title} tagline={tagline} />
  <EvidenceSection evidence={evidence} characterName={characterName} />
  <CallbackSection quote={callbackQuote} trope={trope} />
  <InTheWildSection trope={trope} />
</TropeResultCard>
```

### ActionButtons

```tsx
<ActionButtons>
  <ShareButton result={result} />
  <ContinueButton characterId={characterId} characterName={characterName} />
</ActionButtons>
```

---

## Why This Structure Works

| Section | Psychological Hook |
|---------|-------------------|
| Identity Statement | Gives language to describe self — shareable identity |
| Evidence | Proves it's not random — creates "they saw me" feeling |
| Callback Quote | Creates "whoa" moment — they remember saying that |
| In The Wild | Aspirational association with beloved stories |
| Share CTA | Low friction to spread |

---

## Implementation Priority

1. **Core card** with identity statement (works with current data)
2. **Evidence section** (requires LLM enhancement)
3. **Callback quote** (requires transcript analysis)
4. **Cultural references** (static content addition)
5. **OG image** (can start static)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-20 | Initial result report specification |
