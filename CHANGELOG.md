# Changelog

All notable changes to Episode-0 are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

- **User Character Customization (ADR-004)**: Users can create their own characters to play in platform-authored episodes
  - New `/my-characters` page for managing user characters
  - Character detail page at `/my-characters/[id]` for editing
  - Limited customization: name, archetype, flirting level, appearance prompt
  - 1 free character slot per user (expandable with premium)
  - Backend: `GET/POST /characters/mine`, `GET/PATCH/DELETE /characters/mine/{id}`
  - Migration: `048_user_character_and_roles.sql`

- **Role Abstraction**: Conceptual bridge between episodes and characters
  - Decouples episode templates from specific canonical characters
  - Enables any compatible character (canonical or user-created) to fill a role
  - Preserves authored episode quality while enabling user customization
  - See: [ADR-004](docs/decisions/ADR-004-user-character-role-abstraction.md)

### Changed

- Updated [EPISODE-0_CANON.md](docs/EPISODE-0_CANON.md) with Role architecture (Section 9)
- Updated [CHARACTER_DATA_MODEL.md](docs/quality/core/CHARACTER_DATA_MODEL.md) v2.0.0 with user character types

### Fixed

- FastAPI route ordering: `/characters/mine` now correctly matched before `/{character_id}`

---

## [2024-12-23] - Architecture Audit

### Added

- **ADR-001**: Genre belongs to Story, not Character
- **ADR-002**: Theatrical production model for conversation architecture
- **Director Protocol v2.2**: Stage manager model (no pre-LLM call)
- **6-Layer Context Architecture**: Character, Episode, Genre, Engagement, Memory, Director

### Changed

- Simplified character data model (removed unused fields)
- Scene motivation moved from runtime generation to episode template authoring
- Genre doctrine injected by Director at runtime, not baked into character system_prompt

### Removed

- Unused boundary fields (`availability`, `vulnerability_pacing`, etc.)
- Stage progression from Engagement (now implicit via memory)

---

## [2024-12-XX] - EP-01 Episode-First Pivot

### Changed

- Sessions replaced runtime Episode concept
- Engagement replaced Relationship (removed stage labels)
- Episode templates now own opening situation, opening line, starter prompts
- Character system_prompt generation auto-triggered on field changes

---

## Notes

This changelog was established on 2025-01-01 to track significant architectural decisions and feature additions. Earlier history is reconstructed from ADRs and documentation.
