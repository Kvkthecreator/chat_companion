# Studio Episode-First Refactor Plan

**Status:** Planned

**Scope:** Studio UI, Studio API, Content Pipeline

**Created:** 2024-12-16

**Related:** EP-01_pivot_CANON.md, SESSION_ENGAGEMENT_REFACTOR.md

---

## 1. Executive Summary

The current Studio is **character-first**: create a character → add opening beat → generate avatar → activate.

The EP-01 pivot demands **episode-first**: episodes are the primary creative unit, characters anchor them.

This document outlines the refactor plan for Studio to support episode-first content creation.

---

## 2. Current State Analysis

### 2.1 Studio UI (`/studio/create`)

**Current Wizard Flow:**
```
Step 1: Character Core (name, archetype)
Step 2: Personality & Boundaries
Step 3: Opening Beat (situation, opening_line)  ← PROBLEM
Step 4: Review & Save
```

**Problem:** Opening beat is stored on the character, but EP-01 says opening beats belong ONLY in `episode_templates`.

### 2.2 Studio API (`/studio` routes)

**Current Endpoints:**
```
POST /studio/characters        → Create character with opening beat
POST /studio/opening-beat      → Generate opening beat (returns to UI, stored on character)
POST /studio/avatar            → Generate avatar for character
```

**Missing Endpoints:**
- Episode template CRUD
- Episode-first creation flow

### 2.3 Database Schema

**Current:**
- `characters.opening_situation` - DEPRECATED (remove)
- `characters.opening_line` - DEPRECATED (remove)
- `episode_templates` has all needed fields including `episode_frame`

**EP-01 Decision:** Opening beat source of truth = `episode_templates` ONLY

---

## 3. Target Architecture

### 3.1 Dual-Mode Studio

Support both episode-first and character-first workflows:

```
┌─────────────────────────────────────────────────────────────┐
│                      STUDIO HOME                             │
│                                                              │
│   ┌─────────────────────┐    ┌─────────────────────┐        │
│   │  Create Episode     │    │  Create Character   │        │
│   │  (Primary Path)     │    │  (Secondary Path)   │        │
│   └─────────────────────┘    └─────────────────────┘        │
│                                                              │
│   Recent Characters          Recent Episodes                 │
│   ─────────────────          ────────────────                │
│   [Char cards...]            [Episode cards...]              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Episode-First Flow (NEW - Primary)

```
/studio/episodes/create
┌────────────────────────────────────────────────────────────────┐
│ Step 1: Episode Concept                                        │
│ ────────────────────────                                       │
│ • Title: [_______________]                                     │
│ • Genre: [Romantic Tension ▼] [Psychological Thriller ▼]       │
│ • Episode Type: [Entry ▼] [Core ▼] [Expansion ▼]              │
│                                                                │
│ Step 2: Episode Frame (Stage Direction)                        │
│ ───────────────────────────────────────                        │
│ • Situation: [Scene description...]                            │
│ • Episode Frame: [Platform stage direction, brief, evocative]  │
│   Example: "late night café, empty except for you, rain..."    │
│                                                                │
│ Step 3: Opening Beat                                           │
│ ────────────────────                                           │
│ • Opening Line: [Character's first message]                    │
│ • Starter Prompts: [Response options for user]                 │
│   [Generate with AI] button                                    │
│                                                                │
│ Step 4: Character Assignment                                   │
│ ────────────────────────────                                   │
│ • [Select Existing Character ▼]                                │
│   OR                                                           │
│ • [+ Create New Character Inline]                              │
│                                                                │
│ Step 5: Visuals                                                │
│ ───────────────                                                │
│ • Background Image: [Generate] [Upload]                        │
│ • Character Avatar: (auto-assigned from character's kit)       │
│                                                                │
│ [Save as Draft] [Publish]                                      │
└────────────────────────────────────────────────────────────────┘
```

### 3.3 Character-First Flow (MODIFIED - Secondary)

```
/studio/characters/create
┌────────────────────────────────────────────────────────────────┐
│ Step 1: Character Core                                         │
│ ──────────────────────                                         │
│ • Name: [_______________]                                      │
│ • Archetype: [Comforting] [Flirty] [Mysterious] ...           │
│ • Genre: [Romantic Tension ▼]                                  │
│                                                                │
│ Step 2: Personality & Boundaries                               │
│ ────────────────────────────────                               │
│ • Personality Preset: [Warm & Supportive ▼]                    │
│ • Flirting Level: [None] [Playful] [Moderate] [Intense]       │
│ • Content Rating: [SFW] [Adult]                                │
│                                                                │
│ Step 3: Review & Save                                          │
│ ─────────────────────                                          │
│ • Summary card                                                 │
│ • NOTE: Episodes created separately                            │
│                                                                │
│ [Save as Draft]                                                │
└────────────────────────────────────────────────────────────────┘

REMOVED: Opening Beat step (moved to episode creation)
```

### 3.4 Character Detail Page (ENHANCED)

```
/studio/characters/[id]
┌────────────────────────────────────────────────────────────────┐
│ [Avatar] Character Name                                        │
│          archetype • genre • status                            │
│                                                                │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│ │ Overview │ │ Episodes │ │ Assets   │ │ Settings │           │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                │
│ ═══════════════════════════════════════════════════════════   │
│                                                                │
│ EPISODES TAB (NEW)                                             │
│ ──────────────────                                             │
│ [+ Create Episode]                                             │
│                                                                │
│ Episode 0: "The Diner"              [Default]                  │
│ ├─ Frame: "3am diner, corner booth..."                         │
│ ├─ Status: Active                                              │
│ └─ [Edit] [Preview]                                            │
│                                                                │
│ Episode 1: "High Score"                                        │
│ ├─ Frame: "dark arcade after hours..."                         │
│ ├─ Status: Draft                                               │
│ └─ [Edit] [Preview] [Set as Default]                           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. API Changes

### 4.1 New Endpoints

```
# Episode Template CRUD
POST   /studio/episode-templates              → Create episode template
GET    /studio/episode-templates              → List all (paginated)
GET    /studio/episode-templates/:id          → Get single
PUT    /studio/episode-templates/:id          → Update
DELETE /studio/episode-templates/:id          → Delete

# Episode Template by Character
GET    /studio/characters/:id/episode-templates   → List episodes for character
POST   /studio/characters/:id/episode-templates   → Create episode for character

# Episode Frame Generation (AI)
POST   /studio/episode-frame/generate         → Generate episode_frame from situation
```

### 4.2 Modified Endpoints

```
# Character Creation (REMOVE opening beat fields)
POST /studio/characters
{
  name: string,
  archetype: string,
  genre: string,
  personality_preset: string,
  boundaries: {...},
  content_rating: string,
  status: "draft" | "active"
  // REMOVED: opening_situation, opening_line
}

# Opening Beat Generation (now returns episode_frame too)
POST /studio/opening-beat
Response: {
  situation: string,
  episode_frame: string,    // NEW
  opening_line: string,
  starter_prompts: string[]
}
```

### 4.3 Request/Response Contracts

```typescript
// Create Episode Template
interface CreateEpisodeTemplateRequest {
  character_id: string;
  title: string;
  slug?: string;  // Auto-generated if not provided
  situation: string;
  episode_frame: string;
  opening_line: string;
  episode_type: "entry" | "core" | "expansion" | "special";
  is_default?: boolean;
  starter_prompts?: string[];
  background_image_url?: string;
  arc_hints?: Record<string, unknown>;
}

interface EpisodeTemplateResponse {
  id: string;
  character_id: string;
  episode_number: number;
  title: string;
  slug: string;
  situation: string;
  episode_frame: string | null;
  opening_line: string;
  episode_type: string;
  is_default: boolean;
  background_image_url: string | null;
  starter_prompts: string[];
  status: string;
  created_at: string;
  updated_at: string;
}
```

---

## 5. Database Changes

### 5.1 Columns to Remove (characters table)

```sql
-- These columns are deprecated per EP-01
-- Source of truth is now episode_templates only
ALTER TABLE characters DROP COLUMN IF EXISTS opening_situation;
ALTER TABLE characters DROP COLUMN IF EXISTS opening_line;
```

### 5.2 Ensure episode_frame Exists

```sql
-- Already exists, but verify
SELECT column_name FROM information_schema.columns
WHERE table_name = 'episode_templates' AND column_name = 'episode_frame';

-- If missing:
ALTER TABLE episode_templates ADD COLUMN episode_frame TEXT;
```

---

## 6. Frontend Changes

### 6.1 New Components

| Component | Purpose |
|-----------|---------|
| `EpisodeCreateWizard` | Episode-first creation flow |
| `EpisodeCard` | Display episode in list |
| `EpisodeFrameInput` | Specialized input for episode_frame with guidance |
| `CharacterEpisodeList` | Episodes tab on character detail |

### 6.2 Modified Components

| Component | Change |
|-----------|--------|
| `CreateCharacterWizard` | Remove Step 3 (Opening Beat) |
| `StudioHome` | Add "Create Episode" primary action |
| `CharacterDetail` | Add Episodes tab |

### 6.3 New Routes

```
/studio/episodes                    → Episode list
/studio/episodes/create             → Episode creation wizard
/studio/episodes/[id]               → Episode detail/edit
/studio/characters/[id]/episodes    → Character's episodes
```

---

## 7. Implementation Phases

### Phase 1: API Foundation (Backend)
- [ ] Add episode template CRUD routes
- [ ] Add episode_frame generation to opening-beat endpoint
- [ ] Update character creation to remove opening beat fields
- [ ] Add tests for new endpoints

### Phase 2: Character Detail Enhancement (Frontend)
- [ ] Add Episodes tab to character detail page
- [ ] Create EpisodeCard component
- [ ] Create CharacterEpisodeList component
- [ ] Wire up to existing episode template APIs

### Phase 3: Episode Creation Flow (Frontend)
- [ ] Create EpisodeCreateWizard component
- [ ] Create EpisodeFrameInput component with guidance
- [ ] Add /studio/episodes routes
- [ ] Integrate AI generation for episode_frame

### Phase 4: Character Creation Simplification (Frontend)
- [ ] Remove Opening Beat step from character creation
- [ ] Update flow to direct to Episodes tab after creation
- [ ] Add inline "Create First Episode" prompt

### Phase 5: Cleanup
- [ ] Remove opening_situation/opening_line from characters table
- [ ] Update any remaining references
- [ ] Documentation updates

---

## 8. Migration Strategy

### 8.1 Existing Characters

Characters created with opening_situation/opening_line need migration:

```sql
-- For each character with opening data but no episode template:
-- Create an "Entry" episode template from their data

INSERT INTO episode_templates (
  id, character_id, episode_number, title, slug,
  situation, opening_line, episode_frame,
  episode_type, is_default, status
)
SELECT
  gen_random_uuid(),
  c.id,
  0,
  'Introduction',
  c.slug || '-intro',
  c.opening_situation,
  c.opening_line,
  '',  -- episode_frame empty for migrated data
  'entry',
  TRUE,
  'active'
FROM characters c
WHERE c.opening_situation IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM episode_templates et
    WHERE et.character_id = c.id AND et.is_default = TRUE
  );
```

### 8.2 Backwards Compatibility

During transition:
- API continues to accept opening_situation/opening_line on character creation
- If provided, auto-create episode template
- Deprecation warning in response
- Remove after 30 days

---

## 9. Success Criteria

1. **Episode-First Path Works:** Can create episode → assign character
2. **Character-First Still Works:** Can create character → add episodes later
3. **Episode Frame Displayed:** episode_frame shows as stage direction in chat
4. **AI Generation Works:** Can generate episode_frame from situation
5. **Migration Complete:** All existing characters have episode templates

---

## 10. Open Questions

1. **Character without episodes?** Allow or require at least one?
   - Recommendation: Allow draft characters without episodes

2. **Episode reuse?** Can same episode be used with different characters?
   - Current: No, episode_templates have FK to character
   - Future: Could support "scenario templates" that cast different characters

3. **Default episode?** What happens if no is_default episode?
   - Use first entry-type episode
   - Or first by episode_number

---

## Related Documents

- `docs/EP-01_pivot_CANON.md` - Episode-first philosophy
- `docs/character-philosophy/Genre 01 — Romantic Tension.md` - Episode frame guidance
- `docs/character-philosophy/Genre 02 — Psychological Thriller- Suspense.md` - Episode frame guidance
- `docs/implementation/SESSION_ENGAGEMENT_REFACTOR.md` - Session/Engagement changes
