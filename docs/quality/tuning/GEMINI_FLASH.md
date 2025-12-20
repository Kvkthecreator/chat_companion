# Model Tuning: Gemini 2.0 Flash

> **Version**: 1.0.0
> **Status**: Production
> **Model ID**: `gemini-2.0-flash`
> **Provider**: Google

---

## Overview

Gemini 2.0 Flash is the current production model for Fantazy character responses. This document captures tuning parameters and behavior observations.

---

## Model Characteristics

| Characteristic | Value | Notes |
|----------------|-------|-------|
| Context window | 1M tokens | Effectively unlimited for our use |
| Output max | 8192 tokens | We cap at 1024 |
| Strengths | Fast, good instruction following, handles complex prompts |
| Weaknesses | Can be verbose, sometimes breaks character in long contexts |
| Cost tier | Low | Good for streaming responses |

---

## Recommended Parameters

### For Character Responses

```python
{
    "model": "gemini-2.0-flash",
    "temperature": 0.8,
    "max_tokens": 1024,
    # Gemini uses different param names
    "top_p": 0.95,
}
```

**Notes**:
- Temperature 0.8 balances creativity with coherence
- Higher temperatures (0.9+) can cause character voice drift
- Lower temperatures (0.6-) feel robotic

### For Director Evaluation

```python
{
    "model": "gemini-2.0-flash",
    "temperature": 0.3,
    "max_tokens": 256,
    "response_format": "json",  # Gemini JSON mode
}
```

**Notes**:
- Lower temperature for consistent evaluation
- JSON mode helps with structured output
- Small token limit forces concise responses

---

## Prompt Adjustments

### System Prompt Best Practices

Gemini Flash responds well to:
- Clear section headers (using caps or markdown)
- Explicit "NEVER" and "ALWAYS" instructions
- Examples with "Good:" and "Bad:" labels
- Numbered priority lists

```
CRITICAL RULES:
1. ALWAYS ground responses in the physical situation
2. NEVER break character to explain or apologize
3. Keep responses under 3 paragraphs

Good: "I glance up from my sketchbook, pencil still in hand..."
Bad: "I look at you mysteriously..."
```

### Known Issues

| Issue | Workaround |
|-------|------------|
| Tends toward verbosity | Add "Keep responses concise (2-3 paragraphs max)" |
| Can drop physical grounding | Repeat situation in moment layer |
| Sometimes adds emoji unprompted | Explicit "no emoji unless character uses them" |
| May over-explain emotions | "Show, don't tell" instruction |

---

## Quality Observations

### Strengths for Fantazy Use Case

- Excellent at maintaining character voice within session
- Good emotional range and nuance
- Follows complex multi-part prompts well
- Fast streaming (good UX)
- Handles romantic tension appropriately
- Respects boundaries when instructed

### Weaknesses for Fantazy Use Case

- Can become generic in long conversations (context drift)
- Sometimes prioritizes helpfulness over character authenticity
- May lose physical grounding if not reinforced
- Occasional "assistant mode" breaks when user asks questions

### Recommended Use

- [x] Character responses (primary)
- [ ] Character responses (fallback)
- [x] Director evaluation
- [x] Memory extraction
- [x] Scene description generation

---

## Benchmark Results

| Metric | Score | Date | Notes |
|--------|-------|------|-------|
| Context adherence | 3.8/5 | 2024-12-20 | Good but can drift |
| Emotional intensity | 4.0/5 | 2024-12-20 | Strong range |
| Genre compliance | 3.5/5 | 2024-12-20 | Needs reinforcement |
| Response latency | ~800ms | 2024-12-20 | First token |

---

## Comparison Notes

### vs GPT-4

- Flash is faster and cheaper
- GPT-4 has slightly better character consistency
- Flash handles our prompt format well

### vs Claude

- Similar quality for character work
- Claude slightly better at emotional nuance
- Flash better cost/speed ratio for production

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-20 | Initial production documentation |
