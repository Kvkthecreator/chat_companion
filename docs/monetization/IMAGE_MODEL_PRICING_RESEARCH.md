# Image Generation Model Pricing Research

> **Status**: IMPLEMENTED (ADR-007)
> **Last Updated**: 2025-01-07
> **Related**: [ADR-007-prompt-first-image-generation.md](../decisions/ADR-007-prompt-first-image-generation.md)

## Recommended Stack: 3 Models

**Decision**: Use exactly 3 models to balance cost, quality, and operational simplicity.

| Model | Cost | Use Case | Why |
|-------|------|----------|-----|
| **FLUX 1.1 Pro** | $0.05 | Avatars | Identity-defining, one-time per character |
| **FLUX Kontext Pro** | $0.04 | Character scenes with reference | Irreplaceable for consistency |
| **FLUX Schnell** | $0.003 | Everything else | 94% cheaper, style-first handles quality |

### Cost Impact

```
Before ADR-007: $3.00/user/month (all FLUX Dev/Pro)
After ADR-007:  $1.01/user/month (3-model stack)
Savings:        66% reduction
```

### Why Not More Models?

We researched alternatives but chose simplicity:
- **SDXL Lightning** ($0.0017): 43% cheaper than Schnell, but adds operational complexity for ~$1.30/month savings at 1000 images
- **Seedream 4** ($0.03): 25% cheaper than Kontext, but newer/less tested
- **p-image-edit** ($0.01, <1s): Cool for real-time editing, but no current use case

### When to Revisit

| Trigger | Action |
|---------|--------|
| 50K+ images/month | Evaluate dedicated hosting |
| Need sub-second editing | Evaluate p-image-edit |
| Kontext quality issues | Evaluate Seedream 4 as backup |

---

## Current Implementation

| Use Case | Model | Cost | Code Location |
|----------|-------|------|---------------|
| **T2I Default** | `flux-schnell` | $0.003 | `image.py:DEFAULT_MODEL` |
| **Avatars** | `flux-1.1-pro` | $0.05 | `avatar_generation.py` |
| **Kontext Scenes** | `flux-kontext-pro` | $0.04 | `scene.py` |
| **Backgrounds** | `flux-schnell` | $0.003 | `studio.py`, scripts |
| **Props** | `flux-schnell` | $0.003 | Scripts |

---

## Provider Pricing Comparison

### Google AI (Direct API)

| Model | Free Tier | Paid Price/Image |
|-------|-----------|------------------|
| Imagen 4 Fast | **None** | $0.02 |
| Imagen 4 Standard | **None** | $0.04 |
| Imagen 4 Ultra | **None** | $0.06 |
| Imagen 3 | **None** | $0.03 |
| Gemini 2.5 Flash Image | **None** | $0.039 (batch: $0.0195) |

**Key Finding**: Google Gemini image generation has NO free tier. All image output is paid.

### Replicate (Serverless API)

| Model | Pricing Model | Cost |
|-------|---------------|------|
| **FLUX.1 Kontext Pro** | Per image | $0.04 (25 images/$1) |
| **FLUX.1 Schnell** | Per image | $0.003 (333 images/$1) |
| **FLUX.1 Dev** | Time-based | ~$0.05 median |
| **FLUX.1.1 Pro** | Per image | ~$0.05 |
| **Google Imagen 4 Fast** | Per image | $0.02 (50 images/$1) |
| **Google Imagen 4** | Per image | $0.04 |

**Key Finding**: Replicate offers Google Imagen at the same price as direct API, plus FLUX alternatives.

### Replicate Hardware Pricing (Time-Based)

| Hardware | Per-Second | Per-Hour |
|----------|-----------|----------|
| CPU (Small) | $0.000025 | $0.09 |
| CPU | $0.0001 | $0.36 |
| Nvidia T4 GPU | $0.000225 | $0.81 |
| Nvidia L40S GPU | $0.000975 | $3.51 |
| Nvidia A100 (80GB) | $0.0014 | $5.04 |
| Nvidia H100 GPU | $0.001525 | $5.49 |

---

## Model Selection Matrix

### By Use Case

| Use Case | Recommended Model | Reasoning |
|----------|-------------------|-----------|
| **Quick T2I** | FLUX Schnell | Fastest, cheapest ($0.003) |
| **Quality T2I** | FLUX Dev / FLUX 1.1 Pro | Better negative prompt support |
| **Character Consistency** | FLUX Kontext Pro | Purpose-built for reference images |
| **Budget T2I** | Imagen 4 Fast | $0.02, good quality |
| **Batch Generation** | Gemini 2.5 Flash Batch | $0.0195, bulk discount |

### Quality vs Cost Trade-off

```
Cost/Image:   $0.003 -------- $0.02 -------- $0.04 -------- $0.06
              Schnell        Imagen Fast    Kontext/Dev    Imagen Ultra
              (low)          (good)         (excellent)    (best)
```

---

## Serverless vs Dedicated Hosting Analysis

### When Does Dedicated Make Sense?

Replicate offers "Deployments" - dedicated GPU instances for high-volume usage.

**Serverless Pricing** (pay per use):
- Kontext Pro: $0.04/image
- Monthly at 1000 images: $40
- Monthly at 5000 images: $200
- Monthly at 10000 images: $400

**Dedicated Pricing** (pay for uptime):
- H100 GPU: $5.49/hour = ~$3,950/month (always on)
- A100 GPU: $5.04/hour = ~$3,629/month (always on)
- L40S GPU: $3.51/hour = ~$2,527/month (always on)

### Break-Even Analysis

Assuming dedicated H100 can generate ~1 image/second (Kontext Pro average):

| Monthly Volume | Serverless Cost | Dedicated H100 | Winner |
|----------------|-----------------|----------------|--------|
| 1,000 images | $40 | $3,950 | Serverless |
| 10,000 images | $400 | $3,950 | Serverless |
| 50,000 images | $2,000 | $3,950 | Serverless |
| 100,000 images | $4,000 | $3,950 | ~Breakeven |
| 200,000 images | $8,000 | $3,950 | Dedicated |
| 500,000 images | $20,000 | $3,950 | Dedicated |

**Break-Even Point**: ~100,000 images/month ($0.04 model)

For FLUX Schnell ($0.003/image):
- Break-even at ~1.3M images/month

### Dedicated Hosting Considerations

**Pros:**
- Predictable costs at high volume
- Lower latency (no cold starts)
- Private endpoint
- Auto-scaling with always-on option

**Cons:**
- Pay for idle time
- Requires volume commitment
- Operational overhead
- Minimum ~$2,500/month even at low usage

**Recommendation**: Stay serverless until consistently generating 50,000+ images/month with growth trajectory.

---

## Cost Optimization Strategies

### 1. Model Tiering (Implemented Partially)

```
Use Case Routing:
├── Auto-gen scenes → FLUX Schnell ($0.003) or Imagen Fast ($0.02)
├── User-triggered moments → FLUX Dev ($0.05)
├── Character consistency → FLUX Kontext Pro ($0.04)
└── Avatar generation → FLUX 1.1 Pro ($0.05)
```

**Potential Savings**: Switch auto-gen from FLUX Dev to Schnell/Imagen Fast
- Current: 60 auto-gen × $0.05 = $3.00/user/month
- Optimized: 60 auto-gen × $0.003 = $0.18/user/month
- **Savings: ~$2.82/user/month (94%)**

### 2. Batch Processing

Google Gemini 2.5 Flash offers 50% batch discount ($0.0195 vs $0.039).
- Good for pre-generated library scenes
- Not suitable for real-time generation

### 3. Pre-Generation Strategy

Already documented in [IMAGE_GENERATION_COSTS.md]:
- Pre-generate 20-30 images per character
- Cost: ~$1.00-1.50 per character (one-time)
- Amortized across all users

---

## Implementation Recommendations

### Immediate (No Code Changes)

1. **Continue current model selection** - FLUX Kontext Pro for character consistency is correct choice
2. **Monitor usage** via `usage_events` table to track actual volumes

### Short-Term Optimization

| Change | Effort | Savings | Status |
|--------|--------|---------|--------|
| Switch auto-gen T2I to Schnell | Low | ~$2.80/user/mo | NOT IMPLEMENTED |
| Add Imagen 4 Fast option | Medium | ~$0.03/image | NOT IMPLEMENTED |
| Batch pre-gen with Gemini | Medium | 50% on batch | NOT IMPLEMENTED |

### Long-Term (High Volume)

| Trigger | Action |
|---------|--------|
| 50K images/month | Evaluate dedicated hosting ROI |
| 100K images/month | Likely migrate to dedicated |
| Quality complaints with Schnell | Consider Imagen 4 Fast |

---

## False Assumption Correction

**Original Assumption**: "Google Gemini image generation is free like their text API"

**Reality**:
- Google Gemini **text** has a generous free tier (1M tokens/min)
- Google Gemini **image** has **NO free tier**
- All image output (Imagen, Gemini Flash Image) requires paid API access
- Pricing ranges from $0.02-$0.06 per image

This means our current Replicate-based approach is not more expensive than Google - it's comparable or cheaper with better model options.

---

## Summary Table

| Provider | Model | Cost/Image | Quality | Use Case |
|----------|-------|------------|---------|----------|
| Replicate | FLUX Schnell | $0.003 | Good | Budget T2I |
| Google | Imagen 4 Fast | $0.02 | Good | Quality T2I |
| Google | Gemini Flash Batch | $0.0195 | Good | Bulk pre-gen |
| Replicate | FLUX Dev | ~$0.05 | Excellent | Quality T2I |
| Replicate | FLUX Kontext Pro | $0.04 | Excellent | Character consistency |
| Replicate | FLUX 1.1 Pro | ~$0.05 | Excellent | Avatars |
| Google | Imagen 4 Ultra | $0.06 | Best | Premium features |

---

## SUPERSEDED: Prompt-First Architecture

> **This section is superseded by [ADR-007-prompt-first-image-generation.md](../decisions/ADR-007-prompt-first-image-generation.md)**
>
> The analysis below identified negative prompt support as a blocker for cheaper models.
> Further investigation revealed the ROOT CAUSE is **prompt structure**, not negative prompts.
> With style-first prompting, negative prompts become optional, unlocking 94% cost savings.

### Key Insight

The "negative prompt blocker" was a false constraint. Our prompts put style descriptors LAST,
causing diffusion models to weight appearance 4x heavier than style. This produced photorealistic
outputs regardless of negative prompt usage.

**Fix**: Put style descriptors FIRST → cheaper models become viable → 66% cost reduction.

See ADR-007 for the full implementation plan.

---

## Deep Dive: Model Capability Analysis for Cost Optimization (Historical)

### Generation Path Audit

Current codebase has **4 distinct generation contexts**:

| Context | Current Model | Cost | Triggers | Character Consistency Needed? |
|---------|---------------|------|----------|------------------------------|
| **Avatar Generation** | FLUX 1.1 Pro | $0.05 | User-initiated in Studio | YES - defines character identity |
| **Scene w/ Reference** | FLUX Kontext Pro | $0.04 | Has anchor image | YES - must match avatar |
| **Scene T2I (no ref)** | FLUX Dev (default) | $0.05 | No anchor, auto-gen | PARTIAL - appearance in prompt |
| **Director Auto-Gen** | FLUX Dev (default) | $0.05 | Director visual events | PARTIAL - depends on visual_type |
| **Scripts (pre-gen)** | FLUX 1.1 Pro | $0.05 | Batch character assets | YES - establishing character |

### Model Capability Matrix

| Capability | Schnell | Imagen 4 Fast | FLUX Dev | FLUX 1.1 Pro | Kontext Pro |
|------------|---------|---------------|----------|--------------|-------------|
| **Negative Prompts** | No | No | Yes | Yes | No |
| **Reference Images** | No | No | No | No | **Yes** |
| **Character Consistency** | Via prompt only | Via prompt only | Via prompt | Via prompt | **Native** |
| **Speed** | ~1-2s | ~3s | ~10-15s | ~8-12s | ~15-20s |
| **Cost** | $0.003 | $0.02 | ~$0.05 | ~$0.05 | $0.04 |
| **Quality** | Good | Good | Excellent | Excellent | Excellent |

### Critical Finding: Negative Prompt Support

Your T2I templates heavily rely on negative prompts:

```python
# From scene.py - T2I mode
base_negative = "multiple people, two people, twins, couple, pair, duo, 2girls, 2boys, group, crowd"
final_negative = f"{base_negative}, photorealistic, 3D render, harsh shadows, text, watermark"
```

**FLUX Schnell does NOT support negative prompts** - the parameter is ignored.
**Imagen 4 Fast does NOT support negative prompts** either.

This is a **blocker** for switching T2I auto-gen to cheaper models without prompt engineering changes.

### Safe Optimization Paths

#### Path A: Object/Atmosphere Visuals (Low Risk)

Director's `object` and `atmosphere` visual types don't need character consistency:

```python
# From scene.py - OBJECT_PROMPT_TEMPLATE
# "close-up of significant object" - NO character in frame

# From scene.py - ATMOSPHERE_PROMPT_TEMPLATE
# "NO characters in frame" - environment only
```

**These CAN safely use Schnell or Imagen 4 Fast** without quality loss.

Estimated savings:
- If 30% of auto-gen are object/atmosphere: 18 images × $0.047 savings = $0.85/user/month

#### Path B: Pre-Generated Library (Low Risk)

Batch script generation (props, backgrounds) could use cheaper models:
- Props: Close-up items, no character → Schnell OK
- Backgrounds: No character → Schnell OK
- Avatars: MUST stay FLUX 1.1 Pro (defines identity)
- Character scenes: MUST stay FLUX Dev/Pro (needs negative prompts)

#### Path C: Tiered Quality System (Medium Risk)

Introduce quality tiers based on moment importance:

```
High-Impact Moments (keep current):
├── Avatar generation → FLUX 1.1 Pro ($0.05)
├── User-triggered "Capture Moment" → FLUX Dev ($0.05)
├── Kontext scenes (has reference) → Kontext Pro ($0.04)
└── Stage change scenes → FLUX Dev ($0.05)

Standard Moments (optimize):
├── Object close-ups → Imagen 4 Fast ($0.02)
├── Atmosphere shots → FLUX Schnell ($0.003)
└── Generic milestone scenes → Imagen 4 Fast ($0.02)
```

### Recommended Implementation Strategy

**Phase 1: Safe Wins (No Quality Risk)**
1. Add model selection to Director's `generate_director_visual`:
   - `visual_type == "object"` → Use Imagen 4 Fast ($0.02)
   - `visual_type == "atmosphere"` → Use FLUX Schnell ($0.003)
   - `visual_type == "character"` → Keep FLUX Dev ($0.05)

2. Update batch scripts for props/backgrounds to use Schnell

**Phase 2: Monitor & Expand**
1. Track image quality feedback by model
2. A/B test Imagen 4 Fast for `milestone` T2I scenes
3. If quality acceptable, expand usage

**Phase 3: Advanced (If Volume Justifies)**
1. Consider dedicated hosting at 50K+ images/month
2. Evaluate fine-tuned models for specific art styles

### Cost Impact Analysis

**Current State** (all FLUX Dev/Pro):
- 60 images/user/month × $0.05 = $3.00

**Phase 1 Optimization** (object/atmosphere to cheap models):
- 42 character images × $0.05 = $2.10
- 12 object images × $0.02 = $0.24
- 6 atmosphere images × $0.003 = $0.018
- **Total: $2.36/user/month (-21%)**

**Aggressive Optimization** (milestone T2I to Imagen Fast):
- 30 high-impact images × $0.05 = $1.50
- 18 standard T2I × $0.02 = $0.36
- 12 object/atmosphere × $0.01 avg = $0.12
- **Total: $1.98/user/month (-34%)**

### Kontext Pro: The Character Consistency Anchor

FLUX Kontext Pro is **irreplaceable** for scenes with reference images:

> "The model maintains subject identity through explicit prompting... Users preserve faces and features by instructing it to keep the same facial features"

No other model in our price range offers this capability. **Keep Kontext Pro for all reference-based generation.**

---

## Detailed Model Deep-Dives (Research Notes)

This section contains detailed research on alternative models discovered during our exploration.

### FLUX Kontext Family (Character Consistency)

#### FLUX Kontext Pro
- **Model**: `black-forest-labs/flux-kontext-pro`
- **Price**: $0.04/image (25 images/$1)
- **Runs**: 42.4M (high adoption)
- **Key Features**:
  - State-of-the-art text-based image editing
  - Style transfer (watercolor, oil painting, sketches)
  - Object/clothing modifications
  - Text replacement in images
  - Background changes while preserving subjects
  - Character consistency across multiple edits
- **Best Practices**:
  - Use clear, detailed language with exact colors
  - Specify what should remain unchanged
  - Use quotation marks for text replacements
  - Reference specific artistic styles
- **Use Case Fit**: PRIMARY for character-consistent scene generation

#### FLUX Kontext Max
- **Model**: `black-forest-labs/flux-kontext-max`
- **Price**: $0.08/image (12 images/$1) - 2x Pro cost
- **Key Difference**: Maximum performance, improved typography
- **When to Use**: Premium tier only, text-heavy scenes
- **Use Case Fit**: PREMIUM TIER for highest quality moments

#### FLUX 2 Pro
- **Model**: `black-forest-labs/flux-2-pro`
- **Price**: $0.015/run + $0.015/input MP + $0.015/output MP
- **Runs**: 1.1M
- **Key Features**:
  - Up to 8 reference images (API)
  - Legible text rendering (typography, infographics, UI mockups)
  - Sharp textures and photorealism
  - JSON-based structured prompting for precise composition
  - Up to 4MP output for editing
- **Limitations**: Doesn't understand negative prompts
- **Use Case Fit**: EXPERIMENTAL - Multi-reference scenarios only

### Fast/Cheap T2I Alternatives

#### FLUX Schnell (Current Budget Choice)
- **Model**: `black-forest-labs/flux-schnell`
- **Price**: $0.003/image (333 images/$1)
- **Speed**: ~1-2s
- **Limitations**: No negative prompt support
- **Use Case Fit**: Object/atmosphere shots, style-first generation

#### SDXL Lightning (Cheapest Option)
- **Model**: `bytedance/sdxl-lightning-4step`
- **Price**: $0.0017/image (588 images/$1) - **43% cheaper than Schnell**
- **Speed**: ~2s
- **Hardware**: A100 80GB
- **Key Features**:
  - 4-step generation (vs 20+ for standard SDXL)
  - 1024x1280 max resolution
  - Multiple scheduler options
- **Limitations**: Older SDXL architecture, less refined than FLUX
- **Use Case Fit**: CONSIDER for ultra-budget background generation

#### Imagen 4 Fast
- **Model**: `google/imagen-4-fast`
- **Price**: $0.02/image (50 images/$1)
- **Speed**: ~2-3s
- **Runs**: 3.4M
- **Key Features**:
  - Fine detail rendering
  - Enhanced text rendering (graphics, posters)
  - Flexible aspect ratios up to 2K
  - Three safety filter levels
- **Use Case Fit**: CONSIDER for scenes requiring text elements

#### Ideogram v3 Turbo
- **Model**: `ideogram-ai/ideogram-v3-turbo`
- **Price**: $0.03/image (33 images/$1)
- **Speed**: ~5s
- **Runs**: 5.9M
- **Key Features**:
  - Excellent text rendering in images
  - Stunning photorealism
  - Style reference support (up to 3 images)
  - Layout precision for complex compositions
- **Use Case Fit**: CONSIDER for marketing materials, text-heavy scenes

### Image Edit/Reference Models

#### Pruna AI p-image-edit
- **Model**: `prunaai/p-image-edit`
- **Price**: $0.01/image (100 images/$1)
- **Speed**: <1 second (!!)
- **Runs**: 5.3M
- **Hardware**: H100
- **Key Features**:
  - State-of-the-art AI image editing
  - Multi-image editing support
  - Turbo mode for extra speed
  - Exact prompt adherence
- **Inputs**: Prompt + images + aspect ratio + seed
- **Use Case Fit**: INVESTIGATE for quick edits, props modification

#### ByteDance Seedream 4
- **Model**: `bytedance/seedream-4`
- **Price**: $0.03/image (33 images/$1)
- **Runs**: 21.1M
- **Key Features**:
  - Unified text-to-image AND editing in one model
  - Up to 4K resolution
  - Batch processing (multiple refs, multiple outputs)
  - Natural language editing ("Remove the boy in this picture")
  - Multi-reference workflows
  - Diverse style application
- **Styles**: Watercolor, cyberpunk, architectural, etc.
- **Use Case Fit**: INVESTIGATE as Kontext Pro alternative for editing

#### Qwen Image Edit
- **Model**: `qwen/qwen-image-edit`
- **Price**: $0.03/image (33 images/$1)
- **Speed**: ~2.6s
- **Hardware**: H100
- **Key Features**:
  - **Semantic Editing**: Style transfer, rotation, character creation
  - **Appearance Editing**: Add/remove elements, detail work
  - **Text Editing**: Bilingual (Chinese/English), preserves font/size/style
  - Full 180-degree object rotation capability
  - Fine detail work ("remove fine hair strands")
- **License**: Apache 2.0 (commercial OK)
- **Use Case Fit**: INVESTIGATE for text-in-image editing, semantic transforms

#### FLUX Fill Pro
- **Model**: `black-forest-labs/flux-fill-pro`
- **Price**: $0.05/image (20 images/$1)
- **Runs**: 3.6M
- **Key Features**:
  - Professional inpainting
  - Outpainting (extend images beyond boundaries)
  - Complex scene understanding
  - Text preservation during edits
- **Inputs**: Image + mask + text prompt
- **Use Case Fit**: FUTURE - Extending scenes, background expansion

### Avatar/Portrait Generation Models

#### PhotoMaker
- **Model**: `tencentarc/photomaker`
- **Price**: $0.005/image (200 images/$1)
- **Speed**: ~6s
- **Key Features**:
  - 11 style presets: Cinematic, Digital Art, Fantasy, Neonpunk, Comic Book, Line Art, etc.
  - Multi-image input (up to 4 refs for better identity)
  - Adjustable style strength (15-50%)
  - "Stacked ID embedding" for identity preservation
- **Best Practices**:
  - Include "img" trigger word in prompts
  - Prefix "asian" for Asian faces
  - Ensure faces occupy most of frame
- **License**: Open source, self-hostable
- **Use Case Fit**: LOW PRIORITY - Already have avatar generation pipeline

#### PuLID
- **Model**: `zsxkib/pulid`
- **Price**: $0.004/image (250 images/$1)
- **Speed**: ~5s
- **Hardware**: L40S
- **Key Features**:
  - Tuning-free identity preservation
  - Works with SDXL
  - Contrastive alignment for consistency
  - Up to 3 auxiliary face inputs for blending
  - Adjustable identity scale (0-5)
- **Limitations**: SDXL-based (older), best with front-facing faces
- **Use Case Fit**: LOW PRIORITY - Consider for user-uploaded face stylization

#### face-to-sticker
- **Model**: `fofr/face-to-sticker`
- **Price**: $0.021/image (48 images/$1)
- **Speed**: ~22s
- **Key Features**:
  - InstantID technology for facial recognition
  - IP adapter controls
  - Optional 2x upscaling
  - Built-in background removal
- **License**: **NON-COMMERCIAL ONLY**
- **Use Case Fit**: NOT RECOMMENDED - License restriction

#### face-to-many
- **Model**: `fofr/face-to-many`
- **Price**: $0.008/image (125 images/$1)
- **Speed**: ~9s
- **Runs**: 14.9M
- **Key Features**:
  - 6 style presets: 3D, Emoji, Video Game, Pixels, Clay, Toy
  - InstantID-based
  - Custom LoRA support
- **License**: **NON-COMMERCIAL** (InsightFace weights)
- **Use Case Fit**: NOT RECOMMENDED - License restriction

#### sticker-maker (Text-Only)
- **Model**: `fofr/sticker-maker`
- **Price**: $0.004/image (250 images/$1)
- **Speed**: ~5s
- **Runs**: 1.9M
- **Key Features**:
  - Text prompt only (no face input)
  - Transparent backgrounds (LayerDiffuse)
  - Batch generation (up to 10)
- **Use Case Fit**: CONSIDER for prop stickers, item graphics

#### Recraft V3
- **Model**: `recraft-ai/recraft-v3`
- **Price**: $0.04/image (25 images/$1)
- **Key Features**:
  - Design-focused generation
  - Long text generation in images
  - Raster AND vector outputs
  - Brand style customization via reference
  - Multiple style categories (realistic, illustration, vector)
- **Use Case Fit**: CONSIDER for UI mockups, branded content

### Bonus: Video Generation

#### MiniMax Video-01 (Hailuo)
- **Model**: `minimax/video-01`
- **Price**: $0.50/video (2 videos/$1)
- **Duration**: Up to 6 seconds (10s coming soon)
- **Resolution**: 720p @ 25fps
- **Modes**:
  - Text-to-Video (T2V)
  - Image-to-Video (S2V) with reference
- **Key Features**:
  - Cinematic camera movements
  - Prompt optimizer
  - First-frame image for aspect ratio control
- **Use Case Fit**: FUTURE - Premium tier animated moments

---

## Fantazy Use Case Mapping

### Current Implementation (What We Use)

| Use Case | Model | Cost | Status |
|----------|-------|------|--------|
| Avatar Generation | FLUX 1.1 Pro | $0.05 | KEEP |
| Kontext Scenes | FLUX Kontext Pro | $0.04 | KEEP |
| T2I Scenes | FLUX Dev → Schnell | $0.05 → $0.003 | MIGRATING (ADR-007) |
| Object Shots | FLUX Dev → Schnell | $0.05 → $0.003 | MIGRATING |
| Atmosphere | FLUX Dev → Schnell | $0.05 → $0.003 | MIGRATING |

### Potential Alternatives to Investigate

| Use Case | Current | Alternative | Potential Benefit |
|----------|---------|-------------|-------------------|
| **Ultra-cheap T2I** | Schnell ($0.003) | SDXL Lightning ($0.0017) | 43% cheaper |
| **Character Edit** | Kontext Pro ($0.04) | Seedream 4 ($0.03) | 25% cheaper, unified model |
| **Quick Edits** | N/A | p-image-edit ($0.01) | <1s processing |
| **Text in Images** | N/A | Ideogram v3 Turbo ($0.03) | Superior text rendering |
| **Prop Stickers** | N/A | sticker-maker ($0.004) | Transparent backgrounds |
| **Premium Moments** | Kontext Pro ($0.04) | Kontext Max ($0.08) | Best quality tier |

### NOT Recommended (License/Quality Issues)

| Model | Reason |
|-------|--------|
| face-to-sticker | Non-commercial license |
| face-to-many | Non-commercial license |
| FLUX Dev LoRA | Deprecated, use official |
| PuLID | SDXL-based, older quality |

---

## Future Exploration Roadmap

### Phase 1: Validate Current ADR-007 Migration
- [ ] Complete style-first prompting migration
- [ ] Validate Schnell quality with new prompts
- [ ] Track user feedback on image quality

### Phase 2: Cost Optimization Experiments
- [ ] A/B test SDXL Lightning vs Schnell for backgrounds
- [ ] Evaluate Seedream 4 for character editing
- [ ] Test p-image-edit for quick prop modifications

### Phase 3: Premium Tier Enhancements
- [ ] Evaluate Kontext Max for premium users
- [ ] Investigate video generation (MiniMax) for special moments
- [ ] Consider Ideogram for text-heavy marketing assets

---

## References

- [Replicate Text-to-Image Collection](https://replicate.com/collections/text-to-image)
- [Google AI Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Replicate Pricing](https://replicate.com/pricing)
- [Replicate Deployments Docs](https://replicate.com/docs/deployments)
- [FLUX Kontext Pro](https://replicate.com/black-forest-labs/flux-kontext-pro)
- [FLUX Kontext Max](https://replicate.com/black-forest-labs/flux-kontext-max)
- [FLUX 2 Pro](https://replicate.com/black-forest-labs/flux-2-pro)
- [Seedream 4](https://replicate.com/bytedance/seedream-4)
- [Qwen Image Edit](https://replicate.com/qwen/qwen-image-edit)
- [p-image-edit](https://replicate.com/prunaai/p-image-edit)
- [PhotoMaker](https://replicate.com/tencentarc/photomaker)
- [PuLID](https://replicate.com/zsxkib/pulid)
- [SDXL Lightning](https://replicate.com/bytedance/sdxl-lightning-4step)
- [Ideogram v3 Turbo](https://replicate.com/ideogram-ai/ideogram-v3-turbo)
- [Imagen 4 Fast](https://replicate.com/google/imagen-4-fast)
- [MiniMax Video-01](https://replicate.com/minimax/video-01)
