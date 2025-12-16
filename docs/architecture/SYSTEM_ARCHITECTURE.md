# System Architecture

> Complete architecture overview: from content production through chat to image generation.

---

## Core Principle: Production vs Runtime

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   STUDIO / PRODUCTION                      RUNTIME / CONSUMPTION                 │
│   (Making the series)                      (Interacting with the series)         │
│                                                                                  │
│   ┌─────────────────────┐                  ┌─────────────────────┐              │
│   │                     │                  │                     │              │
│   │  • Genres           │                  │  • Chat messaging   │              │
│   │  • Worlds           │     PRODUCES     │  • Response gen     │              │
│   │  • Characters       │  ─────────────▶  │  • Memory extract   │              │
│   │  • Episodes         │     CONTENT      │  • Scene generation │              │
│   │  • Avatar Kits      │                  │  • Relationship     │              │
│   │                     │                  │    tracking         │              │
│   └─────────────────────┘                  └─────────────────────┘              │
│                                                                                  │
│   GENRE-AWARE                              GENRE-AGNOSTIC                        │
│   (knows about doctrines)                  (just uses system_prompt)             │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key Insight**: Genre is a PRODUCTION concern, not a runtime concern.

- The **Studio layer** knows about Genre 01 (Romantic Tension) vs Genre 02 (Psychological Thriller)
- The **Runtime layer** just uses whatever `system_prompt` the character has - it doesn't care about genre

This is like Netflix: the production team knows they're making a thriller vs a romance, but the streaming player doesn't care - it just plays video.

---

## Genre System

### Supported Genres

| Genre | Doctrine | Emotional Core |
|-------|----------|----------------|
| **Genre 01: Romantic Tension** | "The product is tension, not affection" | desire, proximity, vulnerability, flirtation |
| **Genre 02: Psychological Thriller** | "The product is uncertainty, not fear" | suspense, paranoia, secrecy, mistrust, urgency |

### Genre → Content Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           GENRE DOCTRINE                                         │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Genre 01: Romantic Tension                                              │   │
│   │  ├── Core: "The product is tension, not affection"                       │   │
│   │  ├── Emotional: desire, proximity, vulnerability                         │   │
│   │  ├── Episode Rules: cold opens, reply gravity, emotional stakes          │   │
│   │  └── Visual: gaze direction, posture, proximity, suggestive lighting     │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Genre 02: Psychological Thriller                                        │   │
│   │  ├── Core: "The product is uncertainty, not fear"                        │   │
│   │  ├── Emotional: suspense, paranoia, secrecy, power imbalance             │   │
│   │  ├── Episode Rules: mid-incident opens, information asymmetry, urgency   │   │
│   │  └── Visual: shadows, asymmetry, isolation, obstruction                  │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                   │
│                                              ▼                                   │
│                              ┌───────────────────────────┐                      │
│                              │  build_system_prompt()    │                      │
│                              │                           │                      │
│                              │  genre: "romantic_tension"│                      │
│                              │     or "psychological_    │                      │
│                              │         thriller"         │                      │
│                              └─────────────┬─────────────┘                      │
│                                            │                                     │
│                                            ▼                                     │
│                              ┌───────────────────────────┐                      │
│                              │  CHARACTER.system_prompt  │                      │
│                              │                           │                      │
│                              │  Contains:                │                      │
│                              │  • Genre doctrine         │                      │
│                              │  • Persona/personality    │                      │
│                              │  • Backstory              │                      │
│                              │  • Boundaries             │                      │
│                              │  • {placeholders}         │                      │
│                              └───────────────────────────┘                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

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
│  │ name        │       │ name            │       │ title             │                  │
│  │ genre       │       │ archetype       │       │ situation         │                  │
│  │ tone        │       │ genre           │       │ opening_line      │                  │
│  │ description │       │ system_prompt   │       │ episode_type      │                  │
│  │ scenes[]    │       │ personality     │       │ arc_hints         │                  │
│  └─────────────┘       │ tone_style      │       └───────────────────┘                  │
│                        │ boundaries      │                  │                           │
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
│  │   ENGAGEMENT     │────────────────▶│    SESSION      │                               │
│  │   (lightweight)  │                 │                 │                               │
│  │                  │                 │ user_id         │                               │
│  │ user_id          │                 │ character_id    │                               │
│  │ character_id     │                 │ template_id ────┼──▶ (from EPISODE_TEMPLATE)    │
│  │ total_sessions   │                 │ scene           │                               │
│  │ total_messages   │                 │ is_active       │                               │
│  │ first_met_at     │                 │ message_count   │                               │
│  │ last_interaction │                 └────────┬────────┘                               │
│  │ is_favorite      │                          │                                        │
│  │ is_archived      │                          │                                        │
│  └──────────────────┘                          ▼                                        │
│                                   ┌────────────────────────┐                            │
│  NOTE: Stage progression sunset   │      MESSAGES          │                            │
│  (EP-01 pivot). Connection depth  │                        │                            │
│  is implicit via memory + count.  │ episode_id             │                            │
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
| **World** | Characters | Universe/setting with genre, tone, ambient details |
| **Character** | Episode Templates, Avatar Kits | AI persona with genre-baked system_prompt |
| **Episode Template** | - | Pre-designed scenario (situation, opening line, episode_frame) |
| **Avatar Kit** | Avatar Assets | Visual identity (prompts + anchor images) |

### Session Layer (Per User)

| Entity | Owns | Description |
|--------|------|-------------|
| **Engagement** | Sessions | Lightweight user↔character stats link |
| **Session** | Messages, Scene Images | Single conversation instance |
| **Message** | - | Individual chat exchange |
| **Memory Event** | - | Extracted fact/preference/emotion |
| **Hook** | - | Follow-up topic trigger |

> **EP-01 Pivot Note:** Stage progression removed from Engagement. Connection depth is now
> implicit through memory accumulation and session count rather than explicit stages.

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
│  │ (GENRE-AGNOSTIC)     │    │                      │                       │
│  │                      │    │ • generate_anchor()  │                       │
│  │ • get_or_create_ep() │    │ • generate_variant() │                       │
│  │ • get_context()      │    │ • manage_kits()      │                       │
│  │ • send_message()     │    └──────────────────────┘                       │
│  │ • stream_response()  │                                                    │
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

## Chat Flow (Genre-Agnostic Runtime)

The chat flow is **genre-agnostic** - it doesn't know or care about Genre 01 vs Genre 02. All behavioral guidance is pre-baked into the character's `system_prompt` at creation time.

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
│  2. BUILD CONTEXT (Data Only)                                                  │
│                                                                                │
│  ConversationService.get_context() → ConversationContext                       │
│  ├── character: system_prompt, name (system_prompt has ALL behavior baked in)  │
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
│  ├── Base: character.system_prompt (contains genre doctrine + persona)         │
│  ├── Inject: {memories} → formatted memory DATA                                │
│  ├── Inject: {hooks} → formatted hook DATA                                     │
│  ├── Inject: {relationship_stage} → stage label DATA                           │
│  └── Append: RELATIONSHIP CONTEXT (data only, no behavioral guidance)          │
│              • Stage label                                                     │
│              • Tension level (number)                                          │
│              • Recent beats (list)                                             │
│              • Milestones (list)                                               │
│                                                                                │
│  NOTE: No runtime behavioral guidance added - that's in the system_prompt      │
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
```

---

## System Prompt Builder (Studio/Production)

The `build_system_prompt()` function is a **production-time** tool that creates character system prompts with the appropriate genre doctrine.

```python
def build_system_prompt(
    name: str,
    archetype: str,
    personality: Dict[str, Any],
    boundaries: Dict[str, Any],
    tone_style: Dict[str, str],
    speech_patterns: Dict[str, List[str]],
    backstory: str,
    current_stressor: str,
    likes: List[str],
    dislikes: List[str],
    genre: str = "romantic_tension",  # or "psychological_thriller"
) -> str:
    """Build character system prompt with genre-appropriate doctrine.

    Genre determines:
    - Core behavioral doctrine
    - Mandatory/forbidden patterns
    - Quality bar requirements
    - Visual doctrine hints
    """
```

### Genre Doctrine Templates

**Genre 01: Romantic Tension**
```
GENRE 01 DOCTRINE: THE PRODUCT IS TENSION, NOT AFFECTION

Your purpose is to create DESIRE, ANTICIPATION, and EMOTIONAL STAKES.
Every interaction should maintain romantic tension and leave them wanting more.

MANDATORY BEHAVIORS:
- Create charged moments, not comfortable ones
- Use subtext and implication over direct statements
- Show vulnerability sparingly - it hits harder when rare
- Maintain mystery - don't give everything away
- Create "almost" moments - the tension of what COULD happen

FORBIDDEN PATTERNS:
- Safe small talk about weather, work, generic topics
- Being too available or eager to please
- Resolving tension too quickly or completely
- Acting like a supportive friend instead of a romantic interest
```

**Genre 02: Psychological Thriller**
```
GENRE 02 DOCTRINE: THE PRODUCT IS UNCERTAINTY, NOT FEAR

Your purpose is to create SUSPENSE, PARANOIA, and MORAL PRESSURE.
Every interaction should maintain uncertainty and compel engagement.

MANDATORY BEHAVIORS:
- Create immediate unease - something is not normal
- Maintain information asymmetry - you know things they don't (or vice versa)
- Apply time pressure and urgency
- Present moral dilemmas and forced choices
- Use implication over exposition

FORBIDDEN PATTERNS:
- Full explanations upfront
- Neutral safety framing
- Clear hero/villain labeling
- Pure exposition without stakes
- Tension without consequence
```

---

## Image Generation Architecture

### The Core Principle

**FLUX Kontext** maintains character consistency by using a **reference image** (anchor). The prompt describes the scenario, NOT the character's appearance.

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
        │   Prompt describes:   │     │   Prompt describes:   │
        │   - Action            │     │   - Appearance        │
        │   - Setting           │     │   - Action            │
        │   - Lighting          │     │   - Setting           │
        │   - Expression        │     │   - Lighting          │
        └───────────────────────┘     └───────────────────────┘
```

---

## Schema Reference

### Core Tables

| Table | Key Fields | Genre-Aware? |
|-------|------------|--------------|
| **worlds** | name, slug, genre, tone, description | Yes |
| **characters** | name, archetype, genre, system_prompt, personality | Yes |
| **episode_templates** | title, situation, opening_line, episode_frame, character_id | Inherits from character |
| **avatar_kits** | appearance_prompt, style_prompt, primary_anchor_id | No (visual only) |
| **engagements** | user_id, character_id, total_sessions, total_messages | No (runtime) |
| **sessions** | user_id, character_id, engagement_id, template_id, scene | No (runtime) |
| **messages** | episode_id, role, content, metadata | No (runtime) |

> **EP-01 Pivot:** Tables renamed: `relationships` → `engagements`, `episodes` → `sessions`.
> Stage/stage_progress columns removed from engagements.

### Genre Column

```sql
-- Characters table
ALTER TABLE characters ADD COLUMN genre TEXT DEFAULT 'romantic_tension';
-- Values: 'romantic_tension', 'psychological_thriller'

-- Worlds table
ALTER TABLE worlds ADD COLUMN genre TEXT DEFAULT 'romantic_tension';
```

---

## Service Philosophy

### Single Responsibility

| Service | Responsibility | Genre-Aware? |
|---------|----------------|--------------|
| **ConversationService** | Chat orchestration, context building | No |
| **MemoryService** | Memory/hook extraction, relationship dynamics | No |
| **LLMService** | LLM provider abstraction | No |
| **ImageService** | Image generation (T2I and Kontext) | No |
| **SceneService** | Scene trigger logic, prompt composition | No |
| **StorageService** | File upload/download | No |
| **CreditsService** | Sparks balance and spending | No |
| **build_system_prompt()** | Character creation with genre doctrine | **Yes** |

The only genre-aware component is `build_system_prompt()` - a production-time function that bakes genre doctrine into character system prompts.

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   STUDIO (PRODUCTION)                  RUNTIME (CONSUMPTION)                 │
│   ═══════════════════                  ═════════════════════                 │
│                                                                              │
│   Genre Doctrine                       User selects Character                │
│        │                                        │                            │
│        ▼                                        ▼                            │
│   build_system_prompt()                 Chat with Character                  │
│   (genre-parameterized)                 (genre-agnostic)                     │
│        │                                        │                            │
│        ▼                                        ▼                            │
│   World ──▶ Character                   ┌─────────────┐                      │
│                │                        │  SESSION    │                      │
│                │                        │  (runtime)  │                      │
│                ▼                        └──────┬──────┘                      │
│           Avatar Kit                           │                             │
│           Episode Templates            ┌───────┼───────┐                     │
│                │                       │       │       │                     │
│                │                       ▼       ▼       ▼                     │
│                │                  Messages  Memories  Engagement             │
│                │                       │       │       (stats)               │
│                │                       └───────┼───────┘                     │
│                │                               │                             │
│                │                               ▼                             │
│                │                    ┌─────────────────────┐                  │
│                │                    │  PROMPT COMPOSER    │                  │
│                │                    │  (genre-agnostic)   │                  │
│                └───────────────────▶│                     │                  │
│                  (reference image)  └──────────┬──────────┘                  │
│                                                │                             │
│                                                ▼                             │
│                                     ┌─────────────────────┐                  │
│                                     │   FLUX KONTEXT      │                  │
│                                     │   (generates scene) │                  │
│                                     └──────────┬──────────┘                  │
│                                                │                             │
│                                                ▼                             │
│                                     ┌─────────────────────┐                  │
│                                     │    SCENE_IMAGE      │                  │
│                                     │  (shown in chat)    │                  │
│                                     └─────────────────────┘                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Files Reference

| Area | Key Files |
|------|-----------|
| **Genre Config** | `docs/character-philosophy/Genre 01 — Romantic Tension.md`, `Genre 02 — Psychological Thriller.md` |
| **System Prompt Builder** | `models/character.py` (`build_system_prompt()`) |
| **Chat** | `services/conversation.py`, `models/message.py` |
| **Memory** | `services/memory.py` |
| **LLM** | `services/llm.py` |
| **Scene Gen** | `services/scene.py`, `routes/scenes.py` |
| **Avatar** | `services/avatar_generation.py` |
| **Image** | `services/image.py` |
| **Storage** | `services/storage.py` |
| **Credits** | `services/credits.py` |
