# ADR-007: Prompt-First Image Generation Architecture

> **Status**: IMPLEMENTED
> **Date**: 2025-01-07
> **Deciders**: Product, Engineering
> **Related**: [IMAGE_MODEL_PRICING_RESEARCH.md](../monetization/IMAGE_MODEL_PRICING_RESEARCH.md)

## Implementation Summary

**Completed:**
- Style-first prompt assembly in `avatar_generation.py`
- Emotion-driven Kontext prompts in `scene.py`
- Default model switched to FLUX Schnell in `image.py`
- All background/prop scripts updated to use Schnell

**Final 3-Model Stack:**
| Model | Cost | Use Case |
|-------|------|----------|
| FLUX 1.1 Pro | $0.05 | Avatars (identity-defining) |
| FLUX Kontext Pro | $0.04 | Character scenes with reference |
| FLUX Schnell | $0.003 | Everything else (T2I, objects, backgrounds) |

---

## Context

Our image generation outputs trend photorealistic despite explicit anime/manhwa style intentions. Investigation revealed the root cause is **prompt structure**, not model selection or negative prompts.

### The Problem

Current prompt assembly puts style descriptors LAST:

```
[appearance 25 tokens] → [composition 20 tokens] → [style 15 tokens]
        ↑ 4x weight            ↑ 2x weight            ↑ 0.5x weight
```

Diffusion models weight early tokens 2-4x heavier than late tokens. By the time the model sees "manhwa style", it's already committed to rendering "portrait of detailed person" as photorealistic.

### False Dependency on Negative Prompts

We believed negative prompts ("NOT photorealistic, NOT 3D render") were essential for style control. This is incorrect:

1. **Negative prompts suppress, they don't promote** - They create a void, not a target
2. **Schnell/Imagen don't support negative prompts** - Yet they CAN produce stylized output with correct prompting
3. **Our reliance was a symptom** - We needed strong negatives because positive style signals were too weak (wrong position)

### Cost Implications

Current model selection was based on negative prompt support:
- FLUX Dev ($0.05) - "supports negative prompts"
- FLUX Schnell ($0.003) - "doesn't support negative prompts, can't use"

If prompt restructuring eliminates negative prompt dependency, **model cost could drop 94%** for many use cases.

## Decision

**Adopt prompt-first architecture**: Style descriptors FIRST, then subject, then quality.

**Eliminate negative prompt dependency**: Use positive style promotion, not negative suppression.

**Aggressive model switching**: Move to cheaper models where character consistency isn't required.

## New Prompt Structure

### Before (Current)

```python
full_prompt = f"{appearance_prompt}, {composition_prompt}, {style_prompt}"
# Result: "portrait of Soo-ah, hoodie, tired eyes, ..., masterpiece, anime style"
```

### After (New)

```python
full_prompt = f"{style_prompt}, {appearance_prompt}, {composition_prompt}, {quality_prompt}"
# Result: "webtoon illustration, flat cel shading, clean lineart, portrait of Soo-ah, hoodie, ..."
```

### Style-First Template

```
[STYLE DIRECTIVE]        # webtoon illustration, flat cel shading, clean bold lineart
[RENDERING DIRECTIVE]    # stylized features, soft pastel colors, smooth skin
[SUBJECT]                # portrait of [name], [appearance details]
[EXPRESSION/ACTION]      # [expression], [pose], [gesture]
[ENVIRONMENT]            # [setting], [lighting]
[QUALITY]                # masterpiece, best quality
```

## Model Selection Strategy

### New Model Matrix

| Generation Type | Old Model | New Model | Old Cost | New Cost | Savings |
|-----------------|-----------|-----------|----------|----------|---------|
| **Avatar (defines identity)** | FLUX 1.1 Pro | FLUX 1.1 Pro | $0.05 | $0.05 | 0% |
| **Kontext scenes** | Kontext Pro | Kontext Pro | $0.04 | $0.04 | 0% |
| **T2I character scenes** | FLUX Dev | FLUX Schnell | $0.05 | $0.003 | 94% |
| **Object close-ups** | FLUX Dev | FLUX Schnell | $0.05 | $0.003 | 94% |
| **Atmosphere shots** | FLUX Dev | FLUX Schnell | $0.05 | $0.003 | 94% |
| **Episode backgrounds** | FLUX 1.1 Pro | FLUX Schnell | $0.05 | $0.003 | 94% |

### What MUST Stay Premium

| Type | Why | Model |
|------|-----|-------|
| **Avatar generation** | Defines character identity, anchor for Kontext | FLUX 1.1 Pro |
| **Kontext scenes** | Only model with reference image support | Kontext Pro |

### What Can Move to Schnell

| Type | Why Safe | Confidence |
|------|----------|------------|
| **T2I character scenes** | Style-first prompting handles stylization | High (with testing) |
| **Object close-ups** | No character, no consistency needed | Very High |
| **Atmosphere shots** | No character, environment only | Very High |
| **Episode backgrounds** | No character, already works | Very High |

## Cost Impact

### Per-User Monthly Cost

**Current State** (all premium models):
```
60 images × $0.05 avg = $3.00/user/month
```

**After Implementation**:
```
Avatar generation:    2 × $0.05  = $0.10
Kontext scenes:      20 × $0.04  = $0.80
T2I character:       20 × $0.003 = $0.06
Object/atmosphere:   18 × $0.003 = $0.05
────────────────────────────────────────
Total:                            $1.01/user/month
```

**Savings: 66% reduction** ($3.00 → $1.01)

### At Scale

| Monthly Users | Current Cost | New Cost | Savings |
|---------------|--------------|----------|---------|
| 1,000 | $3,000 | $1,010 | $1,990 |
| 10,000 | $30,000 | $10,100 | $19,900 |
| 100,000 | $300,000 | $101,000 | $199,000 |

## Implementation Plan

### Phase 1: Prompt Restructuring (avatar_generation.py)

1. Update `assemble_avatar_prompt()` to put style FIRST
2. Make MANHWA_STYLE_LOCK the default (not FANTAZY_STYLE_LOCK)
3. Remove reliance on negative prompts for style control
4. Add "solo, 1girl/1boy" at start for single-character enforcement

```python
# NEW: Style-first assembly
def assemble_avatar_prompt(...) -> PromptAssembly:
    style_lock = get_style_lock(style_preset or "manhwa")

    # Style FIRST (highest weight)
    style_parts = [
        style_lock["style"],      # "webtoon illustration, flat cel shading..."
        style_lock["rendering"],  # "stylized features, soft pastel..."
    ]

    # Subject SECOND
    subject_parts = [
        "solo",
        "1girl" if gender == "female" else "1boy",
        f"portrait of {name}",
        custom_appearance or role_visual["wardrobe"],
    ]

    # Composition THIRD
    composition_parts = [
        archetype_data["expression"],
        role_visual["pose"],
        role_visual["setting"],
    ]

    # Quality LAST
    quality_parts = [style_lock["quality"]]

    full_prompt = ", ".join([
        ", ".join(style_parts),
        ", ".join(subject_parts),
        ", ".join(composition_parts),
        ", ".join(quality_parts),
    ])

    # Negative prompt now optional, not relied upon for style
    negative_prompt = style_lock.get("negative", "")
```

### Phase 2: Scene Service Updates (scene.py)

1. Update T2I_PROMPT_TEMPLATE to enforce style-first in LLM prompt
2. Update system prompt to instruct LLM to put style descriptors first
3. Switch default model from FLUX Dev to FLUX Schnell

```python
# NEW: T2I prompt template
T2I_PROMPT_TEMPLATE = """Create a style-first image prompt.

STYLE LOCK (use exactly):
webtoon illustration, flat cel shading, clean bold lineart, stylized features, soft pastel colors

CHARACTER: {character_name}
APPEARANCE: {appearance_prompt}
SETTING: {scene}
MOMENT: {moment}

FORMAT (style descriptors MUST come first):
"webtoon illustration, flat cel shading, clean lineart, solo, 1girl/1boy,
[character appearance], [expression], [action], [setting], [lighting],
masterpiece, best quality"
"""
```

### Phase 3: Model Configuration (image.py)

```python
class ImageService:
    # NEW: Default to Schnell for T2I (style-first eliminates negative prompt need)
    DEFAULT_PROVIDER = "replicate"
    DEFAULT_MODEL = "black-forest-labs/flux-schnell"

    # Model routing by use case
    MODEL_ROUTING = {
        "avatar": "black-forest-labs/flux-1.1-pro",      # Identity-defining
        "kontext": "black-forest-labs/flux-kontext-pro", # Reference-based
        "scene_t2i": "black-forest-labs/flux-schnell",   # Style-first OK
        "object": "black-forest-labs/flux-schnell",      # No character
        "atmosphere": "black-forest-labs/flux-schnell",  # No character
        "background": "black-forest-labs/flux-schnell",  # No character
    }
```

### Phase 4: Update All Generation Call Sites

| File | Function | Change |
|------|----------|--------|
| `avatar_generation.py` | `generate_portrait()` | Keep FLUX 1.1 Pro |
| `scene.py` | `generate_scene_card()` | Kontext stays, T2I → Schnell |
| `content_image_generation.py` | `generate_scene_image()` | Route by type |
| `routes/scenes.py` | manual scene gen | Route by use_kontext |
| `routes/studio.py` | prop generation | → Schnell |

## Kontext: Emotion-Driven Prompting

For Kontext (reference-based) generation, the insight differs slightly:

**The reference image handles WHO the character is. The prompt handles WHAT THEY'RE FEELING.**

### Token Weight Distribution for Kontext

```
[style tokens] → [expression tokens] → [body/environment tokens]
     HIGH              HIGH                   MEDIUM
```

Since appearance comes from the reference image, **expression becomes the primary differentiator** between scenes. Generic prompts like "smiling in café" produce emotionally disconnected results.

### Emotion-Driven Prompt Structure

```
1. STYLE: "webtoon illustration, flat cel shading, clean lineart"
2. EXPRESSION (15-20 words): Detailed eyes, mouth, brows
3. BODY LANGUAGE: Reinforces the emotion
4. ENVIRONMENT: Context
5. LIGHTING/CAMERA: Mood
```

### Good vs Bad Kontext Prompts

**Bad** (emotionally generic):
```
"smiling in café"
"sad expression"
```

**Good** (emotionally specific):
```
"webtoon illustration, flat cel shading, clean lineart,
eyes glistening with unshed tears looking away,
lips pressed together fighting a tremor,
shoulders hunched protectively,
fingers gripping coffee cup too tightly,
warm café interior with rain outside,
soft backlighting, intimate close-up"
```

The expression section alone should be 15-20 words describing HOW the emotion manifests physically.

---

## Rollback Strategy

If quality issues arise:

1. **Per-use-case rollback**: Model routing allows reverting specific paths
2. **A/B testing**: Can run Schnell vs Dev in parallel with quality tracking
3. **Style lock tuning**: Adjust style descriptors without model changes

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Style consistency | >90% manhwa-style outputs | Manual QA sample |
| Cost reduction | >50% per-user cost | Usage tracking |
| Generation speed | <5s avg for Schnell | Latency logs |
| User satisfaction | No increase in complaints | Support tickets |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schnell quality lower than Dev | Medium | Medium | A/B test before full rollout |
| Style-first doesn't fix realism | Low | High | Test prompts before code changes |
| Character consistency degrades | Medium | High | Keep premium models for avatar/Kontext |

## Appendix: Style Lock Definitions

### MANHWA_STYLE_LOCK (Default)

```python
{
    "style": "webtoon illustration, manhwa art style, clean bold lineart, flat cel shading",
    "rendering": "stylized features, soft pastel color palette, smooth skin rendering, dreamy atmosphere",
    "quality": "masterpiece, best quality, professional manhwa art, crisp clean lines, vibrant colors",
    "negative": "photorealistic, 3D render, hyper-detailed textures, complex shadows",
}
```

### Effective Prompt Example

**Before** (photorealistic output):
```
portrait of Soo-ah, oversized hoodie, tired but striking eyes, vulnerability beneath composure,
upper body portrait, convenience store at night, fluorescent lighting,
masterpiece, best quality, highly detailed illustration, anime style
```

**After** (stylized manhwa output):
```
webtoon illustration, flat cel shading, clean bold lineart, stylized features, soft pastel colors,
solo, 1girl, portrait of Soo-ah, oversized hoodie, tired but striking eyes, vulnerability,
convenience store at night, fluorescent lighting, dreamy atmosphere,
masterpiece, best quality, professional manhwa art
```
