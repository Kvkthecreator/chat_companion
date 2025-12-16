# System Architecture

> Complete architecture overview: from character creation through chat to image generation.

---

## Domain Model Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    CONTENT LAYER                                         │
│                              (Created by Studio/Admin)                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────┐       ┌─────────────────┐       ┌───────────────────┐                  │
│  │   WORLD     │──────▶│   CHARACTER     │──────▶│ EPISODE_TEMPLATE  │                  │
│  │             │       │                 │       │                   │                  │
│  │ tone        │       │ name            │       │ title             │                  │
│  │ description │       │ archetype       │       │ situation         │                  │
│  │ scenes[]    │       │ system_prompt   │       │ opening_line      │                  │
│  └─────────────┘       │ personality     │       │ episode_type      │                  │
│                        │ tone_style      │       │ arc_hints         │                  │
│                        │ boundaries      │       └───────────────────┘                  │
│                        │ world_id ───────┘                  │                           │
│                        │                                    │                           │
│                        │ active_avatar_kit_id ──┐           │                           │
│                        └────────────────────────┼───────────┘                           │
│                                                 │                                        │
│                                                 ▼                                        │
│                                    ┌─────────────────────┐                              │
│                                    │    AVATAR_KIT       │                              │
│                                    │                     │                              │
│                                    │ appearance_prompt   │──── Visual Description       │
│                                    │ style_prompt        │──── Artistic Style           │
│                                    │ negative_prompt     │──── Avoid These              │
│                                    │ primary_anchor_id ──┼──▶ AVATAR_ASSET (reference)  │
│                                    └─────────────────────┘                              │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              │ User starts chatting
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  USER SESSION LAYER                                      │
│                              (Created per User interaction)                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌──────────────────┐                 ┌─────────────────┐                               │
│  │   RELATIONSHIP   │────────────────▶│    EPISODE      │                               │
│  │                  │                 │                 │                               │
│  │ user_id          │                 │ user_id         │                               │
│  │ character_id     │                 │ character_id    │                               │
│  │ stage            │                 │ template_id ────┼──▶ (from EPISODE_TEMPLATE)    │
│  │ stage_progress   │                 │ scene           │                               │
│  │ dynamic {        │                 │ is_active       │                               │
│  │   tension_level  │                 │ message_count   │                               │
│  │   tone           │                 └────────┬────────┘                               │
│  │   recent_beats[] │                          │                                        │
│  │ }                │                          │                                        │
│  │ milestones[]     │                          ▼                                        │
│  └──────────────────┘             ┌────────────────────────┐                            │
│                                   │      MESSAGES          │                            │
│                                   │                        │                            │
│                                   │ episode_id             │                            │
│                                   │ role (user/assistant)  │                            │
│                                   │ content                │                            │
│                                   │ metadata               │                            │
│                                   └────────────────────────┘                            │
│                                              │                                          │
│                                              │ Extracted async                          │
│                                              ▼                                          │
│           ┌────────────────────┐    ┌────────────────────┐                             │
│           │   MEMORY_EVENTS    │    │      HOOKS         │                             │
│           │                    │    │                    │                             │
│           │ type (fact/pref/..)│    │ type (reminder/..) │                             │
│           │ summary            │    │ content            │                             │
│           │ importance_score   │    │ suggested_opener   │                             │
│           │ embedding          │    │ trigger_after      │                             │
│           └────────────────────┘    └────────────────────┘                             │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              │ Scene generation triggered
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  VISUAL OUTPUT LAYER                                     │
│                              (Generated from context)                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌──────────────────┐         ┌─────────────────┐         ┌─────────────────┐          │
│  │   IMAGE_ASSET    │◀────────│  SCENE_IMAGE    │────────▶│   (Storage)     │          │
│  │                  │         │                 │         │                 │          │
│  │ prompt (used)    │         │ episode_id      │         │ scenes/         │          │
│  │ model_used       │         │ image_id        │         │   {user}/       │          │
│  │ latency_ms       │         │ caption         │         │     {episode}/  │          │
│  │ storage_path     │         │ sequence_index  │         │       {id}.webp │          │
│  └──────────────────┘         │ trigger_type    │         └─────────────────┘          │
│                               │ avatar_kit_id   │                                       │
│                               │ is_memory       │                                       │
│                               └─────────────────┘                                       │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Entity Relationships

### Content Layer (Static)

| Entity | Owns | Description |
|--------|------|-------------|
| **World** | Characters | Universe/setting with tone and ambient details |
| **Character** | Episode Templates, Avatar Kits | The AI persona with personality, boundaries, prompts |
| **Episode Template** | - | Pre-designed scenario (situation, opening line, arc hints) |
| **Avatar Kit** | Avatar Assets | Visual identity package (prompts + anchor images) |

### Session Layer (Per User)

| Entity | Owns | Description |
|--------|------|-------------|
| **Relationship** | Episodes | User↔Character bond (stage, progress, dynamics) |
| **Episode** | Messages, Scene Images | Single conversation session within a template |
| **Message** | - | Individual chat exchange |
| **Memory Event** | - | Extracted fact/preference/emotion from conversation |
| **Hook** | - | Follow-up topic trigger |

### Visual Layer (Generated)

| Entity | Description |
|--------|-------------|
| **Image Asset** | Raw image metadata (prompt, model, storage) |
| **Scene Image** | Episode-bound scene with caption and context |

---

## Service Layer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API ROUTES                                      │
│                                                                              │
│   /chat          /scenes/generate       /avatars          /episodes          │
│      │                  │                   │                  │             │
└──────┼──────────────────┼───────────────────┼──────────────────┼─────────────┘
       │                  │                   │                  │
       ▼                  ▼                   ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SERVICE LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐                       │
│  │ ConversationService  │    │ AvatarGenerationSvc  │                       │
│  │                      │    │                      │                       │
│  │ • get_or_create_ep() │    │ • generate_anchor()  │                       │
│  │ • get_context()      │    │ • generate_variant() │                       │
│  │ • send_message()     │    │ • manage_kits()      │                       │
│  │ • stream_response()  │    └──────────────────────┘                       │
│  └──────────┬───────────┘                                                    │
│             │                                                                │
│             │ builds context                                                 │
│             ▼                                                                │
│  ┌──────────────────────┐    ┌──────────────────────┐                       │
│  │    MemoryService     │    │      LLMService      │                       │
│  │                      │    │                      │                       │
│  │ • extract_memories() │    │ • generate()         │                       │
│  │ • extract_hooks()    │    │ • stream()           │                       │
│  │ • get_relevant()     │    │ • (Claude/Gemini)    │                       │
│  │ • update_dynamics()  │    └──────────────────────┘                       │
│  └──────────────────────┘                                                    │
│                                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐                       │
│  │    SceneService      │    │    ImageService      │                       │
│  │                      │    │                      │                       │
│  │ • should_generate()  │    │ • generate() [T2I]   │                       │
│  │ • generate_scene()   │────│ • edit() [Kontext]   │                       │
│  │ • get_context()      │    │ • (FLUX/Replicate)   │                       │
│  └──────────────────────┘    └──────────────────────┘                       │
│                                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐                       │
│  │   StorageService     │    │   CreditsService     │                       │
│  │                      │    │                      │                       │
│  │ • upload_scene()     │    │ • check_balance()    │                       │
│  │ • upload_avatar()    │    │ • spend()            │                       │
│  │ • create_signed_url()│    │ • grant()            │                       │
│  └──────────────────────┘    └──────────────────────┘                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Chat Flow (Detailed)

```
User sends message: "I'll have the usual"
                │
                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│  1. GET OR CREATE EPISODE                                                      │
│                                                                                │
│  ConversationService.get_or_create_episode()                                   │
│  ├── Find active episode for (user, character)                                 │
│  ├── OR create new from episode_template                                       │
│  │   └── Inject template.opening_line as first assistant message               │
│  └── Ensure relationship record exists                                         │
└───────────────────────────────────────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│  2. BUILD CONTEXT                                                              │
│                                                                                │
│  ConversationService.get_context() → ConversationContext                       │
│  ├── character: system_prompt, name, personality, boundaries                   │
│  ├── relationship: stage, progress, dynamic (tension, tone, beats)             │
│  ├── episode: scene, title, template context                                   │
│  ├── messages: last 20 messages                                                │
│  ├── memories: 10 relevant (by importance + recency)                           │
│  └── hooks: 5 active (untriggered, past trigger_after)                         │
└───────────────────────────────────────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│  3. FORMAT SYSTEM PROMPT                                                       │
│                                                                                │
│  ConversationContext.to_messages()                                             │
│  ├── Base: character.system_prompt (with Genre 01 doctrine)                    │
│  ├── Inject: {memories} → formatted memory text                                │
│  ├── Inject: {hooks} → formatted hook suggestions                              │
│  ├── Inject: {relationship_stage} → stage label                                │
│  ├── Append: Stage-specific behavior guidelines                                │
│  ├── Append: Bonding goals (tension-focused per Genre 01)                      │
│  └── Append: Life arc context if exists                                        │
└───────────────────────────────────────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│  4. LLM CALL                                                                   │
│                                                                                │
│  LLMService.stream()                                                           │
│  ├── Messages: [system_prompt, ...history, user_message]                       │
│  ├── Model: gemini-2.0-flash (default)                                         │
│  ├── Temperature: 0.8                                                          │
│  └── Stream response to client                                                 │
└───────────────────────────────────────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│  5. SAVE MESSAGES                                                              │
│                                                                                │
│  ├── Insert user message → messages table                                      │
│  └── Insert assistant response → messages table (with model, tokens, latency)  │
└───────────────────────────────────────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│  6. POST-PROCESSING (Background, non-blocking)                                 │
│                                                                                │
│  MemoryService.process_exchange()                                              │
│  ├── Extract memories (facts, preferences, emotions, events)                   │
│  ├── Extract hooks (reminders, follow-ups)                                     │
│  ├── Update relationship.dynamic (tension_level, tone, recent_beats)           │
│  └── Mark triggered hooks as used                                              │
└───────────────────────────────────────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│  7. SCENE TRIGGER CHECK (Optional)                                             │
│                                                                                │
│  SceneService.should_generate()                                                │
│  ├── episode_start: First message of new episode                               │
│  ├── milestone: Message count hits [10, 25, 50]                                │
│  └── stage_change: Relationship stage advanced                                 │
│                                                                                │
│  If triggered → Queue scene generation                                         │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Image Generation Architecture

### The Core Principle

**FLUX Kontext** maintains character consistency by using a **reference image** (the anchor from avatar_kit). The prompt describes the scenario, NOT the character's appearance.

### Generation Mode Decision

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        SCENE GENERATION REQUEST                             │
│                                                                             │
│  Input:                                                                     │
│  ├── episode_id (context: scene, messages, relationship)                    │
│  ├── character_id (context: avatar_kit, visual identity)                    │
│  └── trigger_type (episode_start, milestone, manual)                        │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Fetch Avatar Kit Data        │
                    │                               │
                    │  • primary_anchor_id          │
                    │  • appearance_prompt          │
                    │  • style_prompt               │
                    │  • negative_prompt            │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Has Primary Anchor Image?    │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────────┐     ┌───────────────────────┐
        │   KONTEXT MODE        │     │   T2I FALLBACK MODE   │
        │   (Reference-based)   │     │   (No reference)      │
        │                       │     │                       │
        │   Character appearance│     │   Character appearance│
        │   FROM anchor image   │     │   FROM appearance_    │
        │                       │     │   prompt text         │
        └───────────────────────┘     └───────────────────────┘
```

### Prompt Composition Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROMPT COMPOSER SERVICE                               │
│                        (To be implemented)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LAYER 1: Character Visual Identity                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Source: avatar_kit + character.visual_identity (proposed)          │    │
│  │                                                                      │    │
│  │  Kontext Mode:  (not needed - from reference)                        │    │
│  │  T2I Mode:      appearance_prompt + gender_tag → "solo, 1girl, ..."  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                       │                                      │
│                                       ▼                                      │
│  LAYER 2: Episode Scene Config                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Source: episode_template.scene_config (proposed) + episode.scene    │    │
│  │                                                                      │    │
│  │  Provides:                                                           │    │
│  │  • lighting_preset: "dim_intimate" | "bright" | "dramatic"           │    │
│  │  • environment_style: "indoor_cafe" | "outdoor_park"                 │    │
│  │  • time_of_day: "evening" | "night" | "afternoon"                    │    │
│  │  • mood_keywords: ["cozy", "intimate", "tense"]                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                       │                                      │
│                                       ▼                                      │
│  LAYER 3: Relationship Context                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Source: relationship.stage + relationship.dynamic                   │    │
│  │                                                                      │    │
│  │  Tension Level → Visual Intensity:                                   │    │
│  │  ├── 0-30:   Casual pose, soft gaze                                  │    │
│  │  ├── 30-60:  Open posture, lingering look                            │    │
│  │  ├── 60-80:  Direct eye contact, leaning in                          │    │
│  │  └── 80-100: Intense gaze, intimate proximity                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                       │                                      │
│                                       ▼                                      │
│  LAYER 4: Conversation Context (Dynamic)                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Source: Last N messages from messages table                         │    │
│  │                                                                      │    │
│  │  LLM extracts:                                                       │    │
│  │  • Current ACTION: "wiping espresso machine"                         │    │
│  │  • Visible PROPS: "coffee cup", "counter"                            │    │
│  │  • EXPRESSION: "soft knowing smile"                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                       │                                      │
│                                       ▼                                      │
│  OUTPUT                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Kontext Mode:                                                       │    │
│  │  prompt: "[action], [setting], [lighting], [expression], anime"      │    │
│  │  reference_image: anchor bytes                                       │    │
│  │  negative_prompt: (not used by Kontext)                              │    │
│  │                                                                      │    │
│  │  T2I Mode:                                                           │    │
│  │  prompt: "[appearance], [action], [setting], [lighting], anime"      │    │
│  │  negative_prompt: "multiple people, ..." + avatar_kit.negative       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Image Generation Call

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          IMAGE GENERATION                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KONTEXT MODE (primary):                                                    │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  ImageService.edit()                                                │    │
│  │  ├── model: black-forest-labs/flux-kontext-pro                      │    │
│  │  ├── prompt: "[action], [setting], [lighting], [expression]"        │    │
│  │  ├── reference_images: [anchor_bytes]                               │    │
│  │  └── aspect_ratio: "1:1"                                            │    │
│  │                                                                      │    │
│  │  Character consistency: Maintained by reference image                │    │
│  │  Scenario specificity: From prompt                                   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  T2I FALLBACK (no anchor):                                                  │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  ImageService.generate()                                            │    │
│  │  ├── model: FLUX.1 schnell or similar                               │    │
│  │  ├── prompt: "[appearance], [action], [setting], [lighting]"        │    │
│  │  ├── negative_prompt: "multiple people, twins, ..."                 │    │
│  │  └── size: 1024x1024                                                │    │
│  │                                                                      │    │
│  │  Character consistency: Best-effort via appearance_prompt            │    │
│  │  Scenario specificity: From prompt                                   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   STUDIO CREATES                     USER INTERACTS                          │
│   ═══════════════                    ══════════════                          │
│                                                                              │
│   World ──▶ Character ──▶ Episode    User selects    Chat with              │
│                │          Template   Character   ──▶ Character              │
│                │             │                           │                   │
│                ▼             │                           │                   │
│           Avatar Kit         │                           │                   │
│           (anchor image)     │                           ▼                   │
│                │             │                    ┌─────────────┐            │
│                │             └───────────────────▶│  EPISODE    │            │
│                │                                  │  (session)  │            │
│                │                                  └──────┬──────┘            │
│                │                                         │                   │
│                │                         ┌───────────────┼───────────────┐   │
│                │                         │               │               │   │
│                │                         ▼               ▼               ▼   │
│                │                    Messages      Memories/Hooks    Relationship
│                │                         │               │          Dynamic  │
│                │                         │               │               │   │
│                │                         └───────────────┴───────────────┘   │
│                │                                         │                   │
│                │                                         │                   │
│                │                                         ▼                   │
│                │                              ┌─────────────────────┐        │
│                │                              │  PROMPT COMPOSER    │        │
│                │                              │  (builds prompt     │        │
│                └─────────────────────────────▶│   from all sources) │        │
│                  (reference image)            └──────────┬──────────┘        │
│                                                          │                   │
│                                                          ▼                   │
│                                               ┌─────────────────────┐        │
│                                               │   FLUX KONTEXT      │        │
│                                               │   (generates scene) │        │
│                                               └──────────┬──────────┘        │
│                                                          │                   │
│                                                          ▼                   │
│                                               ┌─────────────────────┐        │
│                                               │    SCENE_IMAGE      │        │
│                                               │  (shown in chat)    │        │
│                                               └─────────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Schema Additions Needed

### 1. `characters.visual_identity` (JSONB)

Structured visual metadata for prompt generation:

```json
{
  "gender_tag": "female",      // → "1girl" in T2I mode
  "body_type": "slender",
  "age_range": "young_adult",
  "key_features": ["warm eyes", "beauty mark"]
}
```

### 2. `episode_templates.scene_config` (JSONB)

Visual configuration per episode template:

```json
{
  "composition": "solo",               // solo | duo | flexible
  "lighting_preset": "dim_intimate",   // bright | warm | dim_intimate | dramatic
  "environment_style": "indoor_cafe",  // indoor_cafe | outdoor_park | apartment
  "time_of_day": "evening",            // morning | afternoon | evening | night
  "mood_keywords": ["cozy", "intimate"],
  "negative_additions": []             // episode-specific negatives
}
```

---

## Service Philosophy

### Single Responsibility

| Service | Responsibility |
|---------|----------------|
| **ConversationService** | Chat flow orchestration, context building |
| **MemoryService** | Memory/hook extraction, relationship dynamics |
| **LLMService** | LLM provider abstraction |
| **ImageService** | Image generation (T2I and Kontext) |
| **SceneService** | Scene trigger logic, composition (uses PromptComposer) |
| **PromptComposerService** | Build prompts from all context layers |
| **StorageService** | File upload/download |
| **CreditsService** | Sparks balance and spending |

### New Service: PromptComposerService

```python
class PromptComposerService:
    """Compose image generation prompts from all context layers."""

    async def compose(
        self,
        character_id: UUID,
        episode_id: UUID,
        conversation_summary: str,
    ) -> PromptComposition:
        """
        Returns:
            PromptComposition(
                mode: "kontext" | "t2i",
                prompt: str,
                negative_prompt: str | None,
                reference_image: bytes | None,
            )
        """
        # 1. Fetch avatar kit → determine mode
        # 2. Fetch episode scene_config → lighting, environment
        # 3. Fetch relationship dynamic → tension level
        # 4. Use LLM to extract action/props/expression from conversation
        # 5. Compose final prompt based on mode
```

---

## Current Bug: Duplicate Prompting in Kontext Mode

### The Problem

Current scene generation uses FLUX Kontext correctly (verified by `model_used: black-forest-labs/flux-kontext-pro`), BUT sends prompts that include character appearance:

```
# CURRENT (WRONG):
prompt: "Mira with warm attentive eyes meeting viewer's gaze, long wavy brown hair..."
reference_image: [Mira's anchor image]

# CORRECT:
prompt: "leaning on café counter, dim after-hours lighting, soft knowing glance..."
reference_image: [Mira's anchor image]
```

### Why This Causes Issues

1. **Redundant description**: Reference image already defines appearance
2. **Conflicting signals**: Prompt says "Mira" + reference shows Mira = FLUX may interpret as "two Miras"
3. **Generic outputs**: When prompt re-describes character, the action/setting becomes secondary

### The Fix

Implement mode-aware prompt generation:

```python
# In PromptComposerService:

if mode == "kontext":
    # Prompt describes ONLY the scene/action
    prompt = f"{action}, {setting}, {lighting}, {expression}, anime style"
    # Character appearance comes from reference_image
else:
    # T2I fallback needs full description
    prompt = f"{appearance_prompt}, {action}, {setting}, {lighting}, anime style"
```

### Implementation Priority

1. **Immediate**: Split prompt generation by mode in `routes/scenes.py`
2. **Short-term**: Create `PromptComposerService` for proper separation
3. **Medium-term**: Add `visual_identity` and `scene_config` schema for richer prompts

---

## Files Reference

| Area | Key Files |
|------|-----------|
| **Chat** | `services/conversation.py`, `models/message.py` |
| **Memory** | `services/memory.py` |
| **LLM** | `services/llm.py` |
| **Scene Gen** | `services/scene.py`, `routes/scenes.py` |
| **Avatar** | `services/avatar_generation.py` |
| **Image** | `services/image.py` |
| **Storage** | `services/storage.py` |
| **Credits** | `services/credits.py` |
