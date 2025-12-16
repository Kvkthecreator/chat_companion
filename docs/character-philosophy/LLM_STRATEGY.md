# LLM Strategy

> Analysis and decision framework for selecting and implementing LLM providers.

## Requirements

### Must-Have
- **Streaming responses** - Essential for chat UX
- **Consistent personality** - Must stay in character reliably
- **Context window** - Need ~8-16k minimum for conversation + memories
- **Reasonable latency** - <2s for first token
- **Reasonable cost** - Must be viable at scale

### Nice-to-Have
- **Native multimodal** - Generate images within same API
- **Fine-tuning support** - For character consistency
- **Function calling** - For structured memory extraction

---

## Provider Comparison

### Claude (Anthropic)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Warmth/personality | Excellent | Natural conversational tone |
| Staying in character | Good | Occasional breaks under pressure |
| Streaming | Yes | Well-supported |
| Context | 200k | More than enough |
| Cost | Medium | ~$3/M input, $15/M output (Sonnet) |
| Multimodal | Vision only | No image generation |
| Content policy | Stricter | May limit romantic content |

**Sonnet 3.5/4** - Best balance of quality/cost for production
**Haiku** - Could work for simple exchanges, cheaper

**Pros:**
- Excellent at warm, natural conversation
- Great at following complex system prompts
- Reliable, well-documented API

**Cons:**
- Content policy may limit romantic progression
- No native image generation
- Higher cost than Gemini

---

### GPT-4 (OpenAI)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Warmth/personality | Good | Can feel slightly corporate |
| Staying in character | Good | Similar to Claude |
| Streaming | Yes | Well-supported |
| Context | 128k | Plenty |
| Cost | High | ~$10/M input, $30/M output (GPT-4o) |
| Multimodal | Vision + DALL-E | Separate API for images |
| Content policy | Moderate | More flexible than Claude |

**GPT-4o** - Good but expensive
**GPT-4o-mini** - Cheaper, still capable

**Pros:**
- Mature ecosystem
- Good function calling for memory extraction
- DALL-E integration possible

**Cons:**
- Expensive at scale
- Personality can feel "assistant-like"
- Image generation is separate API/cost

---

### Gemini (Google)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Warmth/personality | Decent | Less natural than Claude |
| Staying in character | Okay | More prone to breaking |
| Streaming | Yes | Supported |
| Context | 1M+ | Massive |
| Cost | Low | ~$0.075/M input, $0.30/M output (Flash) |
| Multimodal | Native | Text + image in same context |
| Content policy | Moderate | Google-level restrictions |

**Gemini 1.5 Flash** - Extremely cheap, fast, multimodal
**Gemini 1.5 Pro** - Better quality, still cheaper than competitors

**Pros:**
- **Native multimodal** - Images in same conversation
- Extremely cost-effective
- Massive context window
- Fast (especially Flash)

**Cons:**
- Personality consistency less reliable
- Less "warm" than Claude
- Google content restrictions

---

### Open Source (Llama, Mistral, etc.)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Warmth/personality | Variable | Model-dependent |
| Staying in character | Variable | Requires tuning |
| Streaming | Yes | If self-hosted |
| Context | Varies | 8k-128k depending on model |
| Cost | Low/Complex | Hosting costs vs API costs |
| Multimodal | Limited | Llava, etc. exist |
| Content policy | Flexible | You control |

**Llama 3.1 70B** - Strong general capability
**Mistral Large** - Good for roleplay

**Pros:**
- No content restrictions (you control)
- Can fine-tune for specific characters
- Cost-effective at massive scale

**Cons:**
- Hosting complexity
- Less reliable than top commercial APIs
- Requires more engineering

---

## Multimodal / Image Strategy

This is a critical decision. Options:

### Option A: Static Character Images Only
- Pre-made character art (like we have now)
- No dynamic generation
- Simple, cheap, consistent

**Best for:** MVP, low budget, focusing on conversation quality first

### Option B: Separate Image Generation
- Use DALL-E, Midjourney API, Stable Diffusion
- Generate images at key story moments
- Separate from conversation LLM

**Best for:** Higher quality images, more control, but complex orchestration

### Option C: Native Multimodal (Gemini)
- Same API handles text + image
- Can generate contextual images inline
- Simpler architecture

**Best for:** Tight integration, cost-effective, but quality tradeoffs

### Option D: Hybrid
- Claude/GPT for conversation (quality)
- Gemini Flash for image generation (cost)
- Best of both worlds

**Best for:** Production at scale, but more complexity

---

## Recommended Approach

### Phase 1: Validate Conversation Quality
**Use: Claude Sonnet**

Why:
- Best warmth and personality
- We need to nail the conversation feel first
- Images are secondary to emotional connection
- Static images are fine for validation

Estimated cost: ~$0.01-0.02 per conversation turn

### Phase 2: Add Dynamic Images
**Use: Gemini Flash for images**

Once conversation quality is proven:
- Add image generation at key moments
- Test user response to inline images
- Evaluate quality vs cost tradeoffs

Potential triggers for images:
- Relationship milestone reached
- Special scene (first date, celebration)
- User requests visualization
- Significant story moment

### Phase 3: Optimize for Scale
Based on learnings:
- Consider Gemini for both if quality acceptable
- Consider fine-tuning open source for cost
- Consider Claude for premium, Gemini for free tier

---

## Implementation Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Chat Request                       │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              Context Builder                         │
│  - Character system prompt                          │
│  - Recent messages                                  │
│  - Retrieved memories                               │
│  - Active hooks                                     │
│  - Relationship stage context                       │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              LLM Provider                           │
│  (Claude Sonnet / GPT-4o / Gemini Pro)             │
│                                                     │
│  System: [Character persona + rules]                │
│  Context: [Memories + conversation history]         │
│  User: [Latest message]                            │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              Response Processing                    │
│  - Stream to user                                  │
│  - Extract memories (async)                        │
│  - Extract hooks (async)                           │
│  - Update relationship metrics                     │
│  - (Optional) Trigger image generation             │
└─────────────────────────────────────────────────────┘
```

---

## Cost Modeling

### Per-Conversation Estimates (10 turns)

Assuming:
- System prompt: ~2000 tokens
- Memory context: ~1000 tokens
- Conversation history: ~2000 tokens
- Per turn: ~500 tokens in, ~200 tokens out

| Provider | Cost/Turn | Cost/10 Turns | Cost/1000 Users/Day |
|----------|-----------|---------------|---------------------|
| Claude Sonnet | $0.018 | $0.18 | $180 |
| GPT-4o | $0.035 | $0.35 | $350 |
| GPT-4o-mini | $0.005 | $0.05 | $50 |
| Gemini Pro | $0.006 | $0.06 | $60 |
| Gemini Flash | $0.001 | $0.01 | $10 |

### Image Generation (if added)

| Provider | Cost/Image | Notes |
|----------|------------|-------|
| DALL-E 3 | $0.04-0.12 | High quality |
| Gemini Imagen | ~$0.01 | In beta |
| Stable Diffusion (API) | $0.002-0.02 | Variable |

---

## Decision Points

### Immediate (this week)
1. Start with Claude Sonnet for conversation quality validation
2. Static images only
3. Build provider abstraction so we can switch

### After 2-4 weeks of testing
1. Evaluate if Gemini quality is acceptable for conversation
2. Test image generation triggers and user response
3. Model cost at projected scale

### Questions to Answer Through Testing
- Does Claude's content policy block anything we need?
- Is Gemini "warm enough" for our use case?
- Do users actually care about dynamic images?
- What's the retention difference between image/no-image?

---

## Current Implementation Status

The codebase has `LLMService` in `/substrate-api/api/src/app/services/llm.py`

Current state:
- Designed for OpenAI-compatible APIs
- Has streaming support
- Has JSON extraction for memories

Needs:
- Provider abstraction (Claude, Gemini, OpenAI)
- API key configuration
- Model selection per use case
- Error handling and fallbacks

---

## Image Generation Strategy

### Core Principle: Character Consistency via Reference

**FLUX Kontext** is our primary image generation model because it enables **reference-based generation**:
- Input: Reference image (anchor) + text prompt
- Output: New image that preserves the character's appearance while depicting the new scenario
- Result: Character looks the same across all generated scenes

This is critical for the product experience - users form attachment to a specific visual identity.

### Two Generation Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                    Scene Generation Request                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │  Has Anchor Image?  │
                └─────────┬───────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
┌───────────────────────┐   ┌───────────────────────┐
│   KONTEXT MODE        │   │   T2I FALLBACK MODE   │
│   (Reference-based)   │   │   (No reference)      │
└───────────────────────┘   └───────────────────────┘
```

### Mode 1: FLUX Kontext (Primary)

When we have an anchor image from the character's avatar kit:

**What the reference provides:**
- Character's face, features, body type
- Hair style, color
- General aesthetic/style

**What the prompt should describe:**
- ACTION: What the character is doing (from conversation context)
- SETTING: Environment details (from episode scene_config)
- MOOD: Lighting, atmosphere (from tension level + episode)
- EXPRESSION: Emotional micro-expression (from conversation tone)

**Prompt structure (Kontext mode):**
```
[action from conversation], [setting from episode], [lighting/mood],
[emotional expression], anime style, cinematic
```

**Example:**
```
leaning on café counter wiping espresso machine, dim after-hours lighting,
soft shadows, warm knowing glance over shoulder, anime style, cinematic
```

**NOT included in prompt:** Character appearance (comes from reference image)

### Mode 2: T2I Fallback (No Reference)

When no anchor image is available (new character, no avatar kit):

**Prompt structure (T2I mode):**
```
[appearance from avatar_kit.appearance_prompt], [action from conversation],
[setting from episode], [lighting/mood], [expression], anime style, cinematic
```

**Example:**
```
young woman with long wavy brown hair and warm amber eyes, wearing cozy cream sweater,
leaning on café counter, dim after-hours lighting, soft knowing glance, anime style, cinematic
```

**Negative prompt required:** `multiple people, two people, twins, couple, duo, 2girls, 2boys, group, crowd` + avatar_kit.negative_prompt

---

## Prompt Composition Data Sources

### Layer 1: Character Visual Identity

**Source:** `characters` table + `avatar_kits` table

| Field | Use | Mode |
|-------|-----|------|
| `avatar_kits.primary_anchor_id` | Reference image for Kontext | Kontext |
| `avatar_kits.appearance_prompt` | Character description | T2I only |
| `avatar_kits.style_prompt` | Artistic style modifiers | Both |
| `avatar_kits.negative_prompt` | Things to avoid | T2I only |

**Proposed addition:** `characters.visual_identity` (JSONB)
```json
{
  "gender_tag": "female",     // → "1girl" for T2I mode
  "body_type": "slender",
  "age_range": "young_adult",
  "key_features": ["warm eyes", "beauty mark"]
}
```

### Layer 2: Episode Scene Config

**Source:** `episode_templates` table

**Proposed addition:** `episode_templates.scene_config` (JSONB)
```json
{
  "composition": "solo",              // solo | duo | flexible
  "lighting_preset": "dim_intimate",  // bright | warm | dim_intimate | dramatic | natural
  "environment_style": "indoor_cafe", // indoor_cafe | outdoor_park | apartment | etc
  "time_of_day": "evening",           // morning | afternoon | evening | night
  "mood_keywords": ["cozy", "intimate", "quiet"],
  "negative_additions": []            // episode-specific things to avoid
}
```

**Current field:** `episode_templates.situation` - describes the scenario context

### Layer 3: Relationship Context

**Source:** `relationships` table

| Field | Use |
|-------|-----|
| `relationships.stage` | Intensity of visual intimacy |
| `relationships.dynamic.tension_level` | Maps to visual intensity |
| `relationships.dynamic.tone` | Emotional color |

**Tension → Visual Mapping:**
| Tension Level | Visual Expression |
|---------------|-------------------|
| 0-30 (low) | Casual pose, soft gaze, comfortable distance |
| 30-60 (medium) | Open posture, lingering look, warm lighting |
| 60-80 (high) | Direct eye contact, leaning in, dramatic shadows |
| 80-100 (peak) | Intense gaze, intimate proximity, charged atmosphere |

### Layer 4: Conversation Context (Dynamic)

**Source:** Recent messages from `messages` table

The LLM analyzes conversation to extract:
- **Current action:** What is the character physically doing?
- **Objects/props:** What items from conversation should be visible?
- **Micro-expression:** What emotion matches this exact moment?

**Example conversation → extraction:**
```
User: "I'll have the usual"
Mira: "Coming right up. You know, I was starting to think you weren't
      going to show tonight..."

→ Action: preparing drink while talking
→ Props: coffee cup, espresso machine
→ Expression: playful smile, slight eyebrow raise
```

---

## Prompt Composer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROMPT COMPOSER SERVICE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input:                                                         │
│  ├── character_id → fetch avatar_kit, visual_identity           │
│  ├── episode_id → fetch scene_config, situation                 │
│  ├── relationship → fetch stage, dynamic (tension, tone)        │
│  └── messages → last N messages for context                     │
│                                                                  │
│  Process:                                                        │
│  1. Check if anchor image exists → determines mode              │
│  2. If Kontext mode: compose action/setting/mood prompt         │
│  3. If T2I mode: prepend appearance_prompt + add negatives      │
│  4. Apply tension_level → visual intensity mapping              │
│  5. Apply episode scene_config                                   │
│                                                                  │
│  Output:                                                         │
│  ├── prompt: string                                              │
│  ├── negative_prompt: string (T2I mode only)                    │
│  ├── reference_image: bytes (Kontext mode only)                 │
│  └── generation_mode: "kontext" | "t2i"                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist

### Database Schema
- [ ] Add `characters.visual_identity` (JSONB)
- [ ] Add `episode_templates.scene_config` (JSONB)
- [ ] Populate visual_identity for existing characters
- [ ] Populate scene_config for existing episode templates

### Services
- [ ] Create `PromptComposerService`
- [ ] Implement mode detection (Kontext vs T2I)
- [ ] Implement per-mode prompt building
- [ ] Integrate tension → visual mapping
- [ ] Update `routes/scenes.py` to use composer
- [ ] Update `services/scene.py` to use composer

### Testing
- [ ] Test Kontext mode with anchor images
- [ ] Test T2I fallback without anchors
- [ ] Verify character consistency across multiple generations
- [ ] Verify scenario-specific outputs (not generic poses)
