# Image Strategy - Fantazy Visual System

> Defining what each image type conveys, where it appears, and how it should be generated.

## Overview

The Fantazy visual system has **4 distinct image layers**, each serving a specific narrative purpose:

```
┌─────────────────────────────────────────────────────────────┐
│  DISCOVERY LAYER (Browse/Marketing)                         │
│  ├─ Series Cover    → "What world am I entering?"          │
│  └─ Episode Card    → "What situation awaits?"             │
├─────────────────────────────────────────────────────────────┤
│  IDENTITY LAYER (Character Recognition)                     │
│  └─ Character Avatar → "Who am I talking to?"              │
├─────────────────────────────────────────────────────────────┤
│  ATMOSPHERE LAYER (Immersion)                               │
│  └─ Episode Background → "Where am I right now?"           │
├─────────────────────────────────────────────────────────────┤
│  MOMENT LAYER (User-Generated)                              │
│  └─ Scene Cards → "What just happened between us?"         │
└─────────────────────────────────────────────────────────────┘
```

## Visual Identity Cascade

**IMPLEMENTED** - All content images inherit visual identity through a cascade:

```
World visual_style (K-World base aesthetic)
    ↓ inheritance
Series visual_style (genre-specific overrides)
    ↓ merge
Episode-specific context (location, time of day)
    ↓ generation
Final Image Prompt
```

### Database Schema
- `worlds.visual_style` - JSONB with base aesthetic (color palette, rendering style)
- `series.visual_style` - JSONB with series-level overrides (mood, motifs)
- Both use the `VisualStyle` schema defined in `app/models/world.py`

### VisualStyle Fields
```python
base_style: str       # Core art direction (e.g., "anime-influenced illustration")
color_palette: str    # Color themes (e.g., "warm neon, cool shadows")
rendering: str        # Technical rendering (e.g., "soft cel shading")
character_framing: str # How characters are presented
negative_prompt: str  # What to avoid
mood: str            # Emotional atmosphere (series-level)
recurring_motifs: list # Visual themes (series-level)
genre_markers: str   # Genre-specific visual cues (series-level)
atmosphere: str      # Environmental feel (series-level)
```

### Service Files
- `app/services/content_image_generation.py` - Visual cascade logic + prompt builders
- `app/scripts/generate_series_images.py` - CLI script for batch generation

---

## 1. Series Cover Image

### Purpose
Marketing/discovery image that conveys the **emotional promise** of the series.

### Where It Appears
- Discover page (featured hero card)
- Series listing cards
- Series detail page header

### Visual Requirements
- **Aspect Ratio**: 16:9 (landscape) or 1:1 (square for cards)
- **Style**: Atmospheric, mood-focused, may include character silhouette
- **Content**: Setting + mood + genre hint (NOT a portrait)
- **Text**: None (title overlaid by UI)

### Generation Approach
- **Input**: Series title, tagline, genre, world tone
- **Prompt Focus**: Environment, lighting, color palette, emotional tone
- **Example**: "Stolen Moments" → Neon-lit Seoul street at night, rain reflections, sense of mystery and longing

### Priority
**Medium** - Enhances discovery but not critical for core experience

---

## 2. Episode Background Image

### Purpose
Atmospheric backdrop that establishes **where the conversation takes place**.

### Where It Appears
- Chat page (full-height background behind messages)
- Applied with gradient overlay for readability

### Visual Requirements
- **Aspect Ratio**: 9:16 (portrait) or 16:9 (will be cropped/covered)
- **Style**: Soft focus, atmospheric, NOT busy
- **Content**: Location/setting only (NO characters)
- **Overlay Compatibility**: Must work with `from-black/40 via-black/20 to-black/60` gradient

### Generation Approach
- **Input**: Episode situation, dramatic_question, time of day hints
- **Prompt Focus**: Empty environment, ambient lighting, mood
- **Negative Prompt**: people, characters, faces, text

### Episode-Specific Examples (Stolen Moments)

| Episode | Title | Setting | Background Concept |
|---------|-------|---------|-------------------|
| EP-00 | 3AM | Convenience store | Fluorescent-lit konbini interior, empty aisles, 3am quiet |
| EP-01 | Rain Check | Café awning | Rain outside café window, warm interior light, blurred street |
| EP-02 | Missed Connection | Train platform | Empty subway platform, last train announcement ambiance |
| EP-03 | Borrowed Time | Rooftop | Seoul rooftop at dusk, city lights below, golden hour fading |
| EP-04 | Paper Walls | Apartment hallway | Dim apartment corridor, soft light under doors |
| EP-05 | Last Call | Bar closing | Bar interior, chairs on tables, neon signs dimming |

### Priority
**High** - Directly impacts immersion during conversation

---

## 3. Character Avatar

### Purpose
Visual identity that answers **"Who am I talking to?"**

### Where It Appears
- Chat header (small)
- Message bubbles (tiny thumbnail)
- Character cards in discovery
- Profile page (large)
- Scene card generation (as reference anchor)

### Visual Requirements
- **Aspect Ratio**: 1:1 (square)
- **Style**: Fantazy house style (anime-influenced illustration)
- **Content**: Character portrait, face clearly visible
- **Expression**: Neutral-warm (versatile for any conversation context)

### Generation Approach
- **Source**: Avatar Kit system with primary anchor
- **Prompt**: Full appearance description + Fantazy style lock
- **Consistency**: Same anchor used for all scene card generations

### Current Status
- Soo-ah: **Has avatar** (generated via Avatar Kit)
- Managed via Studio character gallery

### Priority
**Critical** - Required for character activation

---

## 4. Scene Cards (User-Generated Moments)

### Purpose
Capture **specific moments** during conversation as visual memories.

### Where It Appears
- Inline in chat message flow
- User's "Memories" gallery (if saved)
- Triggered at milestones or user request

### Visual Requirements
- **Aspect Ratio**: 16:9 (cinematic)
- **Style**: Fantazy style, character-consistent
- **Content**: Character + action + setting
- **Caption**: AI-generated poetic 1-2 sentence description

### Generation Approach
- **KONTEXT Mode** (preferred): Uses avatar anchor as reference
- **T2I Mode** (fallback): Full appearance in prompt
- **Trigger Points**: Episode start, milestones, user "Visualize it" click

### Priority
**Medium** - Enhances engagement but generated on-demand

---

## Generation Pipeline

### Immediate Needs (Stolen Moments Series)

1. **Series Cover** (1 image)
   - Prompt: "Seoul night cityscape, neon reflections on wet pavement, mysterious atmosphere, sense of fleeting moments, K-drama aesthetic, cinematic lighting, no people"

2. **Episode Backgrounds** (6 images)
   - Generate per-episode atmospheric backgrounds
   - Use existing `generate_episode_backgrounds` script
   - Prompts derived from episode situations

### Not Needed Now
- Character Avatar: Already exists for Soo-ah
- Scene Cards: Generated during gameplay

---

## Prompt Templates

### Series Cover Template
```
{world_tone} {setting_type}, {time_of_day} lighting, {mood_keywords},
cinematic composition, no people, no text, atmospheric depth,
{genre_visual_cues}, masterpiece quality illustration
```

### Episode Background Template
```
{location} interior/exterior, {time_of_day}, empty scene,
{mood_adjectives}, {lighting_style}, no people, no characters,
soft atmospheric blur, suitable for text overlay,
{world_aesthetic} style, ambient and immersive
```

### Style Lock (All Images)
```
Positive: masterpiece, best quality, highly detailed illustration,
cinematic lighting, soft dramatic shadows, warm color palette,
anime-influenced art style, professional quality

Negative: photorealistic, 3D render, multiple people, text,
watermark, signature, blurry, low quality, deformed
```

---

## Implementation Checklist

### Phase 1: Stolen Moments Launch ✅ COMPLETED
- [x] Generate series cover image
- [x] Generate 6 episode background images
- [x] Store URLs in database (Replicate delivery URLs)
- [x] Update database records (series.cover_image_url, episode_templates.background_image_url)

### Phase 2: Pipeline Automation
- [ ] Add cover generation to series creation flow
- [ ] Add background generation to episode template creation
- [ ] Studio UI for image preview/regeneration

### Phase 3: Quality & Iteration
- [ ] A/B test different background styles
- [ ] User feedback on immersion
- [ ] Refine prompt templates based on results

---

## Generation Script Usage

```bash
# Generate all images for a series (cover + backgrounds)
cd substrate-api/api/src
export FANTAZY_DB_PASSWORD='...'
export REPLICATE_API_TOKEN='...'
python -m app.scripts.generate_series_images --series-slug stolen-moments

# Options
--dry-run          # Show prompts without generating
--cover-only       # Only generate series cover
--backgrounds-only # Only generate episode backgrounds
--skip-existing    # Skip if image already exists
```

### Current Provider
- **Replicate + FLUX 1.1 Pro** (`black-forest-labs/flux-1.1-pro`)
- Handles rate limiting with retry + exponential backoff

---

## Decisions Made

1. **Series Cover Aspect Ratio**: 16:9 (1024x576) - cropped by UI for cards
2. **Episode Background Aspect Ratio**: 9:16 (576x1024) - portrait for mobile chat
3. **Image Storage**: Replicate delivery URLs stored directly in DB
4. **Fallback**: Gradient overlay applied via CSS if no background_image_url

---

*Last Updated: 2024-12-17*
*Status: Implemented - Phase 1 complete for Stolen Moments*
