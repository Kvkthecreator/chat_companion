# Quality System

> **Purpose**: Modular, versioned documentation for conversation quality across all modalities.
> **Maintainer**: Engineering + Content
> **Last Updated**: 2024-12-20

---

## Overview

This folder contains the **Quality System** — the technical and creative specifications that govern how Fantazy conversations feel, progress, and respond to context.

The system is designed to:
- **Evolve independently** as LLM providers improve
- **Support multiple modalities** (text, image, future: audio, video)
- **Version control** quality standards separately from implementation
- **Enable A/B testing** of different quality configurations

---

## Document Structure

```
docs/quality/
├── README.md                    ← You are here
├── CHANGELOG.md                 ← Version history across all specs
│
├── core/                        ← Foundational specifications
│   ├── QUALITY_FRAMEWORK.md     ← Philosophy and measurement
│   ├── CONTEXT_LAYERS.md        ← 6-layer prompt architecture
│   ├── DIRECTOR_PROTOCOL.md     ← Director evaluation logic (two-phase)
│   └── DIRECTOR_UI_TOOLKIT.md   ← Director UI/UX outputs (events, components)
│
├── genres/                      ← Genre-specific quality rules
│   ├── ROMANTIC_TENSION.md      ← Romance genre doctrine (planned)
│   ├── PSYCHOLOGICAL_THRILLER.md← Thriller genre doctrine (planned)
│   └── _TEMPLATE.md             ← Template for new genres
│
├── modalities/                  ← Output-specific quality rules
│   ├── TEXT_RESPONSES.md        ← Character message quality (planned)
│   ├── VISUAL_GENERATION.md     ← Scene/image generation (planned)
│   └── _FUTURE.md               ← Placeholder for audio/video
│
├── tuning/                      ← Model-specific adjustments
│   ├── GEMINI_FLASH.md          ← Current production model
│   └── _MODEL_TEMPLATE.md       ← Template for new models
│
└── play/                        ← Play Mode (viral experiences)
    ├── README.md                ← Play Mode overview
    ├── PLAY_MODE_ARCHITECTURE.md← Routing, auth, flow
    ├── TROPE_SYSTEM.md          ← Romantic Trope taxonomy
    ├── RESULT_REPORT_SPEC.md    ← Share card and result design
    └── IMPLEMENTATION_STATUS.md ← Current vs. target state
```

---

## How to Use This System

### For Engineers
1. Read [QUALITY_FRAMEWORK.md](core/QUALITY_FRAMEWORK.md) for philosophy
2. Read [CONTEXT_LAYERS.md](core/CONTEXT_LAYERS.md) for prompt architecture
3. Check [DIRECTOR_PROTOCOL.md](core/DIRECTOR_PROTOCOL.md) for Director evaluation logic
4. Check [DIRECTOR_UI_TOOLKIT.md](core/DIRECTOR_UI_TOOLKIT.md) for Director UI outputs
5. Reference model-specific tuning in `/tuning/`

### For Content Creators
1. Read [QUALITY_FRAMEWORK.md](core/QUALITY_FRAMEWORK.md) for quality bar
2. Check relevant genre doc in `/genres/`
3. Use checklists before publishing episodes

### For Quality Testing
1. Use evaluation criteria from [QUALITY_FRAMEWORK.md](core/QUALITY_FRAMEWORK.md)
2. Cross-reference genre-specific success signals
3. Log issues in CHANGELOG.md

---

## Version Policy

Each document has its own version number following semver:
- **Major**: Breaking changes to quality expectations
- **Minor**: New features or enhanced guidance
- **Patch**: Clarifications and typo fixes

Example: `DIRECTOR_PROTOCOL.md v2.1.0`

The CHANGELOG.md tracks all changes across the system.

---

## Related Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| Prompting Strategy | `/docs/prompting/` | How prompts are composed (implementation) |
| Episode System | `/docs/content/` | Episode lifecycle and structure |
| Character Philosophy | `/docs/character-philosophy/` | Character design principles |

---

## Migration Notes

This quality system consolidates and versions concepts previously scattered across:
- `docs/prompting/PROMPTING_STRATEGY.md` (context layers)
- `docs/character-philosophy/Genre *.md` (genre doctrines)
- `docs/character-philosophy/PHILOSOPHY.md` (quality principles)

Those documents remain as implementation references. This system defines the **what** and **why**; those define the **how**.
