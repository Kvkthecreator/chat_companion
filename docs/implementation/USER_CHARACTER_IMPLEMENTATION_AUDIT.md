# User Character Customization - Implementation Audit

> **Status**: Ready for Implementation
> **Created**: 2025-01-01
> **Related**: [USER_CHARACTER_CUSTOMIZATION.md](./USER_CHARACTER_CUSTOMIZATION.md)

---

## Codebase Audit Summary

This document provides the specific file locations, line numbers, and changes required to implement user character customization.

---

## 1. Character Model

**File**: `substrate-api/api/src/app/models/character.py`

### Current State

| Field | Line | Status |
|-------|------|--------|
| `created_by: Optional[UUID]` | ~159 | EXISTS - creator user ID |
| `is_user_created` | - | MISSING - need to add |
| `is_public` | - | MISSING - for future sharing |

### System Prompt Generation

| Function | Line Range | Notes |
|----------|------------|-------|
| `build_system_prompt()` | 558-705 | Main generation function |
| `generate_system_prompt()` | (in routes/studio.py) | Wrapper called by routes |
| `PERSONALITY_PRESETS` | ~200-300 | Archetype preset definitions |
| `FLIRTING_LEVEL_DESCRIPTIONS` | (in boundaries) | Energy level text |

### Changes Required

```python
# Add to Character model (around line 160)
is_user_created: bool = False
is_public: bool = False  # Future: shareable characters

# Add validation constraint
# If is_user_created=True, created_by must be set
```

### User Character System Prompt

The existing `build_system_prompt()` can be reused with modifications:
- Skip backstory section if empty (user-created won't have detailed backstory)
- Use archetype preset for personality if user didn't customize
- Genre doctrine is already injected at runtime by Director (ADR-001)

---

## 2. Episode Template Model

**File**: `substrate-api/api/src/app/models/episode_template.py`

### Current State

| Field | Line | Notes |
|-------|------|-------|
| `character_id: Optional[UUID]` | 65-66 | References specific character |
| `series_id: Optional[UUID]` | 66 | Series grouping |
| `scene_objective` | 88 | ADR-002 theatrical model |
| `scene_obstacle` | 89 | ADR-002 theatrical model |
| `scene_tactic` | 90 | ADR-002 theatrical model |

### For Role Abstraction

**Decision**: Create `roles` table now (not deferred).

**Rationale**:
- The conceptual work is done — Role is a real abstraction
- Avoids "implicit magic" where role is inferred from canonical character
- Makes the architecture explicit and queryable
- Lower migration cost now vs. retrofitting later

### Schema Changes

```sql
-- Create roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    archetype TEXT NOT NULL,
    compatible_archetypes TEXT[],
    required_traits JSONB DEFAULT '{}',
    scene_objective TEXT,
    scene_obstacle TEXT,
    scene_tactic TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add role_id to episode_templates
ALTER TABLE episode_templates ADD COLUMN role_id UUID REFERENCES roles(id);
```

**Backward compatibility**: Existing episodes with NULL `role_id` derive role implicitly from canonical character.

---

## 3. Session Model

**File**: `substrate-api/api/src/app/models/session.py`

### Current State

| Field | Line | Notes |
|-------|------|-------|
| `character_id: UUID` | 88 | Required, who user is chatting with |
| `episode_template_id: Optional[UUID]` | 90 | Which episode template |
| `series_id: Optional[UUID]` | 91 | For memory scoping |

### Changes Required

```python
# Session already supports any character_id
# No changes needed for Phase 1

# Future (Phase 2): Add role_id for explicit role tracking
# role_id: Optional[UUID] = None
```

### Memory Scoping Confirmation

Current memory query pattern (verified in `services/memory.py`):
```sql
SELECT * FROM memory_events
WHERE user_id = ? AND character_id = ? AND series_id = ?
```

This already supports user-created characters. Same character in different series = isolated memories.

---

## 4. Routes

### Existing Character Routes

**File**: `substrate-api/api/src/app/routes/studio.py`

| Endpoint | Lines | Notes |
|----------|-------|-------|
| `POST /studio/characters` | 153-270 | Create character |
| `GET /studio/characters` | 98-150 | List all (no ownership filter) |
| `PATCH /studio/characters/{id}` | 313-449 | Update character |
| `POST /studio/characters/{id}/activate` | 529-575 | Activate for chat |

### New Endpoints Needed

```python
# User character management (new routes file or extend studio.py)

# List user's own characters
GET /api/characters/mine
-> Filter by created_by = current_user_id AND is_user_created = true

# Create user character (simplified flow)
POST /api/characters
Body: { name, appearance_prompt, archetype, flirting_level }
-> Auto-generate system_prompt, avatar
-> Set is_user_created = true, created_by = current_user_id

# Update user character
PATCH /api/characters/{id}
-> Only allow if created_by = current_user_id
-> Regenerate system_prompt if personality fields change

# Regenerate avatar
POST /api/characters/{id}/regenerate-avatar
Body: { appearance_prompt? }

# Delete user character
DELETE /api/characters/{id}
-> Only allow if created_by = current_user_id
-> Cascade delete related avatar_kits
```

### Episode Character Selection

**File**: `substrate-api/api/src/app/routes/sessions.py`

| Endpoint | Lines | Notes |
|----------|-------|-------|
| `POST /sessions` | 183-236 | Create session with character_id |

### New/Modified Endpoints

```python
# Get available characters for an episode
GET /api/episodes/{episode_id}/characters
Response: {
    canonical: Character,           # The episode's original character
    compatible: [Character, ...]    # User's characters with matching archetype
}

# Session creation already accepts any character_id
# Just need frontend to pass user's character_id if selected
POST /sessions
Body: { character_id, episode_template_id? }
```

---

## 5. Services

### ConversationService

**File**: `substrate-api/api/src/app/services/conversation.py`

| Method | Lines | Notes |
|--------|-------|-------|
| `get_context()` | 308-488 | Builds conversation context |
| `send_message()` | ~500+ | Main message handler |
| Episode template fetch | 447-481 | Gets scene motivation |

### Changes Required

```python
# In get_context() - currently at line 316
character = await self.get_character(session.character_id)

# This already works for any character_id (canonical or user-created)
# No changes needed for basic functionality

# ENHANCEMENT: If user character is playing canonical's role,
# inject scene motivation from episode_template (already happening)
# The system_prompt comes from the user's character
# The scene_objective/obstacle/tactic comes from episode_template
```

### AvatarGenerationService

**File**: `substrate-api/api/src/app/services/avatar_generation.py`

| Method | Lines | Notes |
|--------|-------|-------|
| Role frame visuals | 59-103 | Maps context to visual descriptions |
| `generate_anchor()` | ~200+ | Creates primary avatar image |
| `generate_variant()` | ~300+ | Creates variant expressions |

### Usage for User Characters

```python
# User character creation flow:
1. User provides appearance_prompt (e.g., "young woman with short blue hair")
2. Call generate_anchor() with:
   - appearance_description = user's appearance_prompt
   - expression = default neutral or friendly
   - pose = default portrait
3. Create avatar_kit linked to character
4. Set character.avatar_url = primary anchor URL

# Existing service supports this - just need route to call it
```

---

## 6. Database Migrations

**Location**: `supabase/migrations/`

### Next Migration Number

Based on existing files, next should be `048_` or higher (check latest).

### Required Migration: User Character Support

```sql
-- Migration: 048_user_character_support.sql

-- Add is_user_created flag to characters
ALTER TABLE characters
ADD COLUMN IF NOT EXISTS is_user_created BOOLEAN DEFAULT FALSE;

-- Add is_public flag for future sharing
ALTER TABLE characters
ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;

-- Ensure created_by is set for user-created characters
ALTER TABLE characters
ADD CONSTRAINT chk_user_created_has_owner
CHECK (is_user_created = FALSE OR created_by IS NOT NULL);

-- Index for listing user's characters
CREATE INDEX IF NOT EXISTS idx_characters_user_created
ON characters(created_by, status)
WHERE is_user_created = TRUE;

-- Mark existing characters as platform-created
UPDATE characters SET is_user_created = FALSE WHERE is_user_created IS NULL;

-- Verification
DO $$
BEGIN
    ASSERT (SELECT COUNT(*) FROM characters WHERE is_user_created IS NULL) = 0,
        'All characters should have is_user_created set';
END $$;
```

### Future Migration: Explicit Roles (Phase 2)

```sql
-- Migration: XXX_roles_table.sql (FUTURE - not Phase 1)

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    archetype TEXT NOT NULL,
    compatible_archetypes TEXT[],
    required_traits JSONB DEFAULT '{}',
    scene_objective TEXT,
    scene_obstacle TEXT,
    scene_tactic TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE episode_templates
ADD COLUMN role_id UUID REFERENCES roles(id);

ALTER TABLE sessions
ADD COLUMN role_id UUID REFERENCES roles(id);
```

---

## 7. Content Moderation

### Required Functions

**File**: New file `substrate-api/api/src/app/services/moderation.py` or extend existing

```python
async def validate_character_name(name: str) -> tuple[bool, str]:
    """Validate character name for content policy."""
    # Length: 2-30 chars
    # Blocklist: slurs, banned terms
    # Real person detection (optional)

async def validate_appearance_prompt(prompt: str) -> tuple[bool, str]:
    """Validate appearance prompt for content policy."""
    # Length: max 500 chars
    # NSFW content detection
    # Real person/celebrity detection
    # IP/copyright detection

# Can use existing moderation patterns from image generation
# or integrate with external moderation API
```

---

## 8. Implementation Phases

### Phase 1a: Database & Model (2-3 days)

- [ ] Create migration `048_user_character_support.sql`
- [ ] Update Character model with `is_user_created`, `is_public`
- [ ] Add validation constraint for `created_by`
- [ ] Run migration on dev/staging

### Phase 1b: Character CRUD Routes (3-4 days)

- [ ] Create `/api/characters/mine` endpoint
- [ ] Create `POST /api/characters` for user character creation
- [ ] Create `PATCH /api/characters/{id}` with ownership check
- [ ] Create `DELETE /api/characters/{id}` with ownership check
- [ ] Create `POST /api/characters/{id}/regenerate-avatar`
- [ ] Add moderation validation to creation flow

### Phase 1c: Avatar Generation Flow (2-3 days)

- [ ] Create user character avatar generation flow
- [ ] Wire appearance_prompt → AvatarGenerationService
- [ ] Handle avatar regeneration
- [ ] Ensure signed URLs work correctly

### Phase 1d: Episode Integration (3-4 days)

- [ ] Create `GET /api/episodes/{id}/characters` endpoint
- [ ] Implement archetype compatibility checking
- [ ] Update session creation to validate character compatibility
- [ ] Test full flow: create character → select for episode → chat

### Phase 1e: Frontend (Parallel with backend)

- [ ] Character creation form UI
- [ ] My Characters list page
- [ ] Character selection pre-episode screen
- [ ] Edit/delete character flows

---

## 9. Key File Locations Summary

| Component | File Path | Key Lines |
|-----------|-----------|-----------|
| Character Model | `models/character.py` | 113-167 (fields), 558-705 (system prompt) |
| Episode Template | `models/episode_template.py` | 65-66 (character_id), 88-92 (scene motivation) |
| Session Model | `models/session.py` | 87-91 (user/character/episode refs) |
| Studio Routes | `routes/studio.py` | 153-270 (create), 313-449 (update) |
| Session Routes | `routes/sessions.py` | 183-236 (create session) |
| ConversationService | `services/conversation.py` | 308-488 (context building) |
| AvatarGeneration | `services/avatar_generation.py` | 59-103 (role frames), ~200+ (generate) |
| Migrations | `supabase/migrations/` | Next: 048+ |

---

## 10. Testing Checklist

### Unit Tests

- [ ] Character creation with all required fields
- [ ] Character creation fails without name
- [ ] Character update regenerates system_prompt
- [ ] Archetype compatibility checking
- [ ] Content moderation validation

### Integration Tests

- [ ] Create user character → verify in database
- [ ] Create character → generate avatar → verify URLs
- [ ] Select user character for episode → create session → chat works
- [ ] User character in episode uses episode's scene motivation
- [ ] Memories scoped correctly (user, character, series)

### E2E Tests

- [ ] Full character creation flow
- [ ] Character selection in episode
- [ ] Multi-episode with same character, memories persist
- [ ] Character deletion cascades properly

---

## Related Documents

- [USER_CHARACTER_CUSTOMIZATION.md](./USER_CHARACTER_CUSTOMIZATION.md) — Architecture and design
- [GLOSSARY.md](../GLOSSARY.md) — Terminology (needs Role addition)
- [CHARACTER_DATA_MODEL.md](../quality/core/CHARACTER_DATA_MODEL.md) — Character schema reference
