# Visual Strategy

> How images work in Fantazy—identity anchors and memory artifacts, not constant eye-candy.

---

## Image Roles in Fantazy

Images serve three distinct purposes:

| Role | Purpose | Where it lives | Generation |
|------|---------|----------------|------------|
| **Avatar** | Identity anchor—who you're with | Header, bubbles, cards | Pre-made (Level 0-1) |
| **Scene Card** | Story moment—where you are | Inline in chat | Generated at key beats (Level 2) |
| **Memory Artifact** | What you've been through | Recaps, gallery, timeline | Derived from scene cards |

**Design principle:** Images are anchors to narrative and memory, not decoration.

---

## Technical Levels

### Level 0-1: Avatar / Identity
```
┌─────────────────────┐
│  [Avatar: Maya]     │  ← Static or expression variants
│  "On shift at café" │
├─────────────────────┤
│  Character: Hey!    │
│  You: Hi there      │
└─────────────────────┘
```
- **Level 0:** Single static image per character
- **Level 1:** 5-10 pre-made expression variants (happy, thinking, flustered...)

**Implementation:** Pre-made assets, no generation cost.

### Level 2: Scene Cards
```
┌─────────────────────────────────────┐
│  Character: Let's grab coffee       │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  [Scene: Cozy coffee shop,  │   │
│  │   warm evening light]       │   │
│  │  ─────────────────────────  │   │
│  │  "The café is quieter than  │   │
│  │   usual tonight..."         │   │
│  │                    ⭐ Save   │   │
│  └─────────────────────────────┘   │
│                                     │
│  Character: This is nice...        │
└─────────────────────────────────────┘
```
- Generated at specific story moments (not every message)
- Full-width card with image + caption
- Belongs to an episode, saveable as memory

**Implementation:** Gemini Flash native image generation.

### Level 3: Continuous Presence (Future)
- Animated avatar with real-time reactions
- Only pursue if Phase 1-2 data supports it

---

## Current Implementation Status

### LLM Service (Text) ✅
```python
from app.services.llm import LLMService

client = LLMService.get_client("google", "gemini-2.0-flash")
async for chunk in client.generate_stream(messages):
    print(chunk)
```
- Provider-agnostic, runtime-configurable
- Default: `google/gemini-2.0-flash`
- Env var: `GOOGLE_API_KEY`

### Image Service ✅
```python
from app.services.image import ImageService

client = ImageService.get_client("gemini", "gemini-2.0-flash-exp-image-generation")
response = await client.generate(
    prompt="A cozy coffee shop interior, warm evening light, anime style",
    num_images=1
)
image_bytes = response.images[0]  # PNG, ~1-2MB
```
- Provider-agnostic, runtime-configurable
- Default: `gemini/gemini-2.0-flash-exp-image-generation`
- Env var: `GOOGLE_API_KEY` (same as LLM)
- Latency: ~5 seconds per image

### Available Models

| Provider | Model | Use Case | Cost |
|----------|-------|----------|------|
| Gemini | `gemini-2.0-flash-exp-image-generation` | Scene cards | Free tier: 1500/day |
| Gemini | `gemini-2.5-flash-image` | Higher quality scenes | Free tier available |
| Replicate | FLUX Schnell | Alternative style | $0.003/image |

**Note:** Imagen models (`imagen-3.0-generate-002`) require Vertex AI, not available on free Google AI tier.

---

## Storage Architecture

### Supabase Storage Buckets

Create these buckets in Supabase Dashboard → Storage:

| Bucket | Purpose | Access |
|--------|---------|--------|
| `avatars` | Character avatars & expressions | Public |
| `scenes` | Generated scene cards | Authenticated (RLS) |

**Bucket setup:**
1. Go to https://supabase.com/dashboard/project/lfwhdzwbikyzalpbwfnd/storage/buckets
2. Click "+ New bucket"
3. Create `avatars` (public: ON)
4. Create `scenes` (public: OFF, RLS: ON)

**Path structure:**
```
avatars/
  {character_id}/
    default.png        ← Main avatar
    happy.png          ← Expression variants (future)
    thinking.png

scenes/
  {user_id}/
    {episode_id}/
      {image_id}.png   ← Generated scene cards
```

### URL Construction
```python
# Public avatar URL
f"{SUPABASE_URL}/storage/v1/object/public/avatars/{character_id}/default.png"

# Authenticated scene URL (requires JWT)
f"{SUPABASE_URL}/storage/v1/object/authenticated/scenes/{user_id}/{episode_id}/{image_id}.png"
```

---

## Data Model for Images

### Database Schema

Migration: `supabase/migrations/008_image_storage.sql`

```sql
image_assets
├── id UUID
├── type: 'avatar' | 'expression' | 'scene'
├── user_id UUID (nullable for system assets)
├── character_id UUID
├── storage_bucket TEXT ('avatars' | 'scenes')
├── storage_path TEXT
├── prompt TEXT (for regeneration)
├── model_used TEXT
├── style_tags TEXT[]
├── mime_type, file_size_bytes, width, height
└── created_at

episode_images (join table)
├── episode_id UUID
├── image_id UUID
├── sequence_index INTEGER
├── caption TEXT
├── trigger_type: 'milestone' | 'user_request' | 'stage_change' | 'episode_start'
├── is_memory BOOLEAN
└── saved_at TIMESTAMPTZ

character_expressions (future: Level 1)
├── character_id UUID
├── image_id UUID
├── expression TEXT ('happy', 'thinking', 'flustered')
└── emotion_tags TEXT[]
```

**Key insight:** Scene images attach to *episodes*, not individual messages. This makes them "story postcards" that work in both chat view and memory gallery.

---

## Scene Generation Triggers

### MVP Trigger Set

1. **Milestone scenes** (system-detected)
   - First meeting
   - First outing/date
   - Big emotional moments ("I finally quit my job")
   - Relationship stage changes (stage 1→2)

2. **User-requested** (cost control + agency)
   - "✨ Visualize" button under certain messages
   - Enabled when recent messages describe a scene

3. **Episode boundaries**
   - Opening scene for significant episodes
   - Limit: max 1-2 scene cards per episode

### Generation Flow
```
Character invites user to café
        ↓
Episode flagged: has_outing = true
        ↓
Engine generates scene prompt from context
        ↓
ImageService.generate(prompt)
        ↓
Scene card inserted in chat with caption
        ↓
User can ⭐ to save as memory
```

---

## MVP Chat UI Layout

### Header
- Avatar circle (Level 0/1)
- Character name
- Status line ("Closing shift at the café")

### Message Stream
- Text bubbles: user right, character left
- Occasionally: full-width scene card
  - Generated image
  - Caption
  - ⭐ Save to Memories icon

### Input Area
- Text input
- Optional "✨ Visualize" button (appears contextually)

### Memory/Profile View (later)
- "Our story so far" → vertical strip of scene cards with dates
- Tap any card → opens episode recap

---

## Cost Analysis (Updated)

### Google AI Free Tier
- **Text (Gemini Flash):** 1,500 requests/day
- **Images:** 1,500 images/day
- **Rate limit:** 15 RPM for images

### At Scale (1000 DAU)

| Scenario | Images/day | Provider | Monthly Cost |
|----------|------------|----------|--------------|
| Conservative (1 img/user/day) | 1,000 | Gemini Free | $0 |
| Moderate (2 img/user/day) | 2,000 | Gemini Paid | ~$600 |
| Heavy (5 img/user/day) | 5,000 | Replicate FLUX | ~$450 |

**Recommendation:** Start with Gemini free tier, monitor usage, upgrade when needed.

---

## Prompt Engineering for Scene Cards

### Template Structure
```
Scene: [description from conversation context]
Setting: [coffee shop / apartment / park / etc]
Time: [morning / afternoon / evening / night]
Mood: [warm / cozy / romantic / playful / melancholic]
Characters: [character description], [implied user presence]
Style: anime, soft lighting, warm colors, slice-of-life aesthetic
```

### Example Prompt
```
A cozy coffee shop in the evening. Warm golden lighting from
pendant lamps. A young woman with shoulder-length dark hair
sits at a small table by the window, two cups of coffee
between her and an empty chair across from her. She's smiling
softly, looking toward the viewer. Rain traces gentle lines
on the fogged window behind her. Anime style, soft focus,
warm color palette.
```

### Character Consistency Challenge
For MVP: Accept some variation. Characters are "impressionistic."

Future options:
1. Detailed prompt engineering (current approach)
2. Reference image guidance (Gemini 3 Pro supports this)
3. Fine-tuned models (LoRA on character)

---

## Next Steps

### Immediate (This Sprint)
1. **Wire up image generation endpoint**
   - Add `/api/generate-scene` endpoint
   - Accept: episode_id, prompt (or auto-generate from context)
   - Return: image URL, caption

2. **Add EpisodeImage to schema**
   - Create migration for `image_assets` and `episode_images` tables
   - Add relationship to Episode model

3. **Build scene card component**
   - React component for inline scene display
   - Image + caption + save button
   - Loading state while generating

### Short-term (Next 2 Weeks)
4. **Implement generation triggers**
   - Start with user-requested only ("✨ Visualize" button)
   - Add milestone detection later

5. **Test prompt quality**
   - Generate 20-30 test scenes
   - Iterate on prompt template
   - Document what works for anime style

### Medium-term (Month 2)
6. **Memory gallery view**
   - Display saved scene cards across episodes
   - "Our story so far" timeline

7. **A/B test retention impact**
   - Compare users with/without scene cards
   - Measure engagement with memory features

---

## Open Questions (Reduced)

1. **Max scenes per episode?** Suggest: 2 (opening + one key moment)
2. **Auto-generate vs user-requested?** Start with user-requested for cost control
3. **Caption source?** LLM-generated from scene context
4. **Image storage?** S3/Cloudflare R2 with CDN
