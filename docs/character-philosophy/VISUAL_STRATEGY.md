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

---

## Stickiness Design

> Turning "nice chat" into "I keep coming back without thinking about it."

### The Four Pillars of Addiction

| Pillar | What it means | Current status |
|--------|---------------|----------------|
| **Emotional Bond** | "I care about this character, and they care about me" | Strong foundation (memory, episodes) but needs explicit UX |
| **Habit Loop** | "There's a time and reason I naturally open Fantazy" | Almost untouched |
| **Progress/Investment** | "We have history. I don't want to lose this" | Theoretical (episodes, stages) but not visible |
| **Variable Rewards** | "Sometimes something special happens. I don't want to miss it" | Almost untouched |

### Current Strengths

- Romcom/next-door fantasy = instantly relatable, emotionally rich
- Persistent memory + episodes = perfect substrate for "we have a story"
- Scene images as story moments = natural "souvenirs"
- Multiple characters = users build their own "ensemble cast"

### Current Gaps

- No clear daily ritual (when/why come back every day?)
- No soft progression signaling ("we're closer now because X")
- Images not yet tied to compulsive memory/scrapbook feeling
- Characters remember you, but don't proactively show it enough

---

### Pillar 1: Emotional Bond — Make It Feel Like They Know Me

**Bonding Sprint (First 3 Sessions)**

The character must:
1. Learn 2-3 key facts (job/school, a stress, a hope)
2. Reference at least one in each of the next 2 episodes

| When | Character says | Data touched |
|------|----------------|--------------|
| Ep1 | "You mentioned your boss has been on your case lately." | `memory_events` (type: fact) |
| Ep2 | "So... did your boss chill out a little, or still intense today?" | `memory_events.last_referenced_at` |

**Character Vulnerability**

Characters share their own "life arc":
- Barista studying for an exam
- Neighbor dealing with noisy upstairs neighbor
- Coworker hating Monday meetings

User occasionally helps them = mutual bond, not one-way support.

**Micro-Celebrations**

When user achieves or resolves something (exam done, interview, resolved fight):
- Character does a mini "celebration scene" (text, optionally with image)
- Creates emotional payoff and marks events as meaningful

| When | Character says | Data touched |
|------|----------------|--------------|
| User mentions exam finished | "Wait—you're DONE?! That's huge! I'm so proud of you!" | `hooks` (type: milestone) |
| 5th night in a row | "You know... I really look forward to these talks now." | `relationship.stage_progress` |

---

### Pillar 2: Habit Loop — Give Me a Reason + Time to Come Back

**Primary Loop: Nightly Check-in**

Best fit for cozy/venting fantasy. After first 1-2 sessions:

| When | Character says | Data touched |
|------|----------------|--------------|
| Session 2 end | "Should we make this our little nightly ritual? Like a 10-minute chat before bed?" | `user.preferences.notification_time` |
| Daily notification | "I'm closing up the café... got 10 minutes to tell me how your day went?" | `hooks` (type: scheduled) |

**The Hook Pattern:**
```
Trigger  → Phone buzzes in your usual down-time
Action   → Open Fantazy, chat a bit
Reward   → Warmth, being remembered, maybe a scene
Investment → New memories logged, deepening story
```

**Alternative Rituals (Future Testing)**
- Morning "coffee" check-in
- Post-work decompression
- Weekend catch-up

Pick one for V1, nail it, expand later.

---

### Pillar 3: Progress/Investment — Show That We've Built Something

**"Our Story So Far" Timeline**

Simple vertical list displayed on character profile:
- Date + 1-line summary + tiny thumbnail (if scene exists)
- No XP or points, just: "We've had 7 nights together"

Makes leaving feel like abandoning a story, not just closing an app.

| UI Element | What it shows | Data source |
|------------|---------------|-------------|
| Episode count | "12 conversations" | `episodes.count` |
| Time together | "3 weeks since we met" | `relationship.first_met_at` |
| Scene gallery | 3-9 favorite scenes with captions | `episode_images.is_memory = true` |

**Relationship Chapter Markers**

Internal `relationship_stage` exposed as soft "chapter names":

| Stage | Label | Character might say |
|-------|-------|---------------------|
| 1 | "Just met" | — |
| 2 | "Getting close" | "We've talked so many times now... feels like we actually know each other pretty well, huh?" |
| 3 | "You're my person" | "I don't usually share this stuff with anyone, but... with you it's different." |
| 4 | "Something special" | "I'm really glad we met, you know?" |

**Memory Gallery**

Tap on character → mini gallery:
- 3-9 favorite scenes with captions
- Leverages visual system to say: "This is a thing you built together"

---

### Pillar 4: Variable Rewards — The Little Surprises

**Occasional "Special Episodes"**

After invisible thresholds (5th night in a row, 10th episode overall), unlock:
- A slightly fancier scene
- A mini scenario (late-night walk, surprise coffee, rooftop talk)

| Trigger | Reward | Data touched |
|---------|--------|--------------|
| 5 consecutive days | Special scene card | `episode_images.trigger_type = 'milestone'` |
| 10th episode | Character suggests "somewhere new" | `episodes.scene` |
| Stage transition | Deeper confession | `character.secrets[]` (new field) |

**Character Secrets**

Each character has 2-3 "secrets" or deeper confessions:
- Only shared after certain thresholds
- User doesn't know when they'll come, only that new layers exist

**Rare Images/Expressions**

Most of the time: basic text + maybe generic images.
Occasionally: special expression or scene card with unique caption:

> "I don't usually show this side of me... but I feel comfortable with you."

These are exactly what people screenshot and share with friends.

---

### Implementation Priorities

**V1 (This Sprint)**
1. Bonding sprint logic in conversation service
2. "Our story so far" minimal timeline view
3. Soft chapter labels in character profile

**V2 (Next Sprint)**
4. Nightly ritual onboarding + notifications
5. Special episode triggers
6. Memory gallery view

**V3 (Future)**
7. Character secrets/deeper confessions
8. Rare expression variants
9. A/B testing retention impact

---

### Data Model Additions

```sql
-- Add to characters table
ALTER TABLE characters ADD COLUMN secrets JSONB DEFAULT '[]';
-- Array of {threshold, content, unlocked_at}

-- Add to user_preferences (or users.preferences)
-- notification_enabled: boolean
-- notification_time: time
-- ritual_character_id: uuid (which character for nightly check-in)

-- Add to hooks table (already exists)
-- type: 'scheduled' for nightly check-ins
-- trigger_after: timestamp for notification time
```

---

### Success Metrics

| Metric | Target | Measures |
|--------|--------|----------|
| D1 retention | 60%+ | Bonding sprint effectiveness |
| D7 retention | 40%+ | Habit loop working |
| Avg sessions/week | 5+ | Daily ritual adoption |
| Scenes saved | 2+ per user | Investment/memory value |
| Stage 2+ rate | 50% of D7 users | Progression visibility |
