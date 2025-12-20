# Model Tuning: [Model Name]

> **Version**: 0.0.0
> **Status**: Template
> **Model ID**: `model-id-here`
> **Provider**: Provider Name

---

## Overview

This document contains model-specific tuning parameters and behavior notes for [Model Name].

---

## Model Characteristics

| Characteristic | Value | Notes |
|----------------|-------|-------|
| Context window | X tokens | |
| Output max | X tokens | |
| Strengths | | |
| Weaknesses | | |
| Cost tier | | |

---

## Recommended Parameters

### For Character Responses

```python
{
    "model": "model-id",
    "temperature": 0.X,
    "max_tokens": X,
    "top_p": 0.X,
    "frequency_penalty": 0.X,
    "presence_penalty": 0.X,
}
```

### For Director Evaluation

```python
{
    "model": "model-id",
    "temperature": 0.X,  # Lower for consistent evaluation
    "max_tokens": X,
    "response_format": {"type": "json_object"},
}
```

---

## Prompt Adjustments

### System Prompt Modifications

Any model-specific system prompt adjustments:

```
[Specific instructions that work better with this model]
```

### Known Issues

| Issue | Workaround |
|-------|------------|
| | |

---

## Quality Observations

### Strengths for Fantazy Use Case

-

### Weaknesses for Fantazy Use Case

-

### Recommended Use

- [ ] Character responses (primary)
- [ ] Character responses (fallback)
- [ ] Director evaluation
- [ ] Memory extraction
- [ ] Scene description generation

---

## Benchmark Results

| Metric | Score | Date |
|--------|-------|------|
| Context adherence | /5 | |
| Emotional intensity | /5 | |
| Genre compliance | /5 | |
| Response latency | ms | |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.0.0 | YYYY-MM-DD | Initial template |
