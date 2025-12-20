# Quality System Changelog

All notable changes to the Quality System documentation.

Format: `[Document] vX.Y.Z - YYYY-MM-DD`

---

## [Unreleased]

### Proposed
- Interactive instruction cards (clickable choices)
- Pacing visualization in ChatHeader

---

## 2024-12-20 (Evening)

### Added
- **[DIRECTOR_UI_TOOLKIT.md]** v1.0.0 - Director UI responsibilities
  - Complete stream event catalog
  - Visual type taxonomy with cost model
  - Auto-scene mode configuration
  - Component mapping (SceneCard, InstructionCard, etc.)
  - Frontend hook interface
  - Data flow diagram

### Implemented
- Director pre-guidance (Phase 1) in conversation flow
- Turn-aware pacing in conversation service
- Genre beat injection via GENRE_BEATS lookup
- Pacing field in StreamDirectorState

---

## 2024-12-20

### Added
- **[QUALITY_FRAMEWORK.md]** v1.0.0 - Initial quality framework
  - Three quality dimensions: Contextual Coherence, Emotional Resonance, Narrative Momentum
  - Quality levels (1-5) with definitions
  - Quality anti-patterns catalog
  - Success signals by genre
  - Measurement protocol

- **[CONTEXT_LAYERS.md]** v1.0.0 - Context layer specification
  - 6-layer architecture documented
  - Layer 6 (Director Guidance) proposed
  - Token budget estimates
  - Layer composition order

- **[DIRECTOR_PROTOCOL.md]** v2.0.0 - Director behavior specification
  - Two-phase model: pre-guidance + post-evaluation
  - Pacing algorithm defined
  - Visual type taxonomy
  - Genre-specific director behavior
  - Auto-scene modes

- **[README.md]** - Quality system overview
  - Document structure
  - Usage guide for engineers/creators
  - Version policy
  - Migration notes

---

## Migration from Previous Docs

| Old Location | New Location | Status |
|--------------|--------------|--------|
| `docs/prompting/PROMPTING_STRATEGY.md` | Remains (implementation) | Reference |
| `docs/character-philosophy/Genre 01 — Romantic Tension.md` | `docs/quality/genres/ROMANTIC_TENSION.md` | Planned |
| `docs/character-philosophy/Genre 02 — Psychological Thriller.md` | `docs/quality/genres/PSYCHOLOGICAL_THRILLER.md` | Planned |
| `docs/character-philosophy/PHILOSOPHY.md` | Absorbed into QUALITY_FRAMEWORK | Archived |

---

## Version Numbering

- **Major (X.0.0)**: Breaking changes to quality expectations or behavior
- **Minor (0.X.0)**: New guidance, features, or enhanced clarity
- **Patch (0.0.X)**: Typos, clarifications, examples

---

## How to Add Entries

1. Add entry under `[Unreleased]` section during development
2. Move to dated section when deployed
3. Include document name, version, and brief description
4. Link to relevant PRs or issues if applicable
