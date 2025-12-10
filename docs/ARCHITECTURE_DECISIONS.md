# Clearinghouse Architecture Decisions

> **Document Purpose**: Canonical record of key architectural decisions, trade-offs, and rationale.

---

## ADR-001: Permission Registry vs. Semantic Search

**Date**: 2025-12-10
**Status**: Decided
**Context**: Clarifying what technical capabilities are required for the core value proposition.

### Decision

**Structured filtering on permissions is the core requirement. Semantic search (embeddings) is a nice-to-have.**

### Rationale

#### What AI Platforms Actually Query

When an AI platform (Suno, ElevenLabs, etc.) queries a rights clearinghouse, they ask structured questions:

```sql
-- "What can I legally use for training in this genre?"
SELECT * FROM rights_entities
WHERE ai_permissions->>'training_allowed' = 'true'
  AND ai_permissions->>'commercial_use' = 'true'
  AND content->>'genre' IN ('K-pop', 'Pop')
```

This is **structured filtering on JSONB fields**—no embeddings required.

#### What Embeddings Enable

Semantic/fuzzy search like:
> "Find something that feels like a sunny road trip"

This is useful for **human discovery UX**, not for programmatic API queries from AI platforms.

#### Priority Matrix

| Capability | Required for Path A? | Current Status |
|------------|---------------------|----------------|
| AI permissions schema | Yes | Done |
| Structured metadata in `content` | Yes | Done |
| Filter API by permissions | Yes | Partial |
| Text embeddings | No (nice-to-have) | Done |
| Semantic search UI | No (nice-to-have) | Not connected |

### Implications

1. **Keep existing embeddings infrastructure**—it works, don't remove it
2. **Don't invest more time** improving embeddings for now
3. **Focus on** making structured filtering + permissions API solid
4. **Demo should emphasize** "queryable permissions" not "semantic search"

---

## ADR-002: Two-Path Product Strategy

**Date**: 2025-12-10
**Status**: Decided
**Context**: Defining the product roadmap in terms of capability layers.

### Decision

The product has two complementary paths that build on each other:

```
┌─────────────────────────────────────────────────────┐
│  Path B: Licensed Source Material Pipeline          │
│  "Generate with Thriller, pay $0.02 per use"        │
│  - Asset delivery (stems, audio files)              │
│  - Per-use tracking & billing                       │
│  - Real-time API for generation platforms           │
│  STATUS: Future (requires Path A foundation)        │
├─────────────────────────────────────────────────────┤
│  Path A: Permission Registry                        │
│  "This catalog allows training, no voice cloning"   │
│  - Structured permissions schema                    │
│  - Bulk licensing for model training                │
│  - Query API for compliance checks                  │
│  STATUS: Current focus (MVP)                        │
├─────────────────────────────────────────────────────┤
│  Foundation: Catalog + Rights Data                  │
│  - Entity metadata                                  │
│  - Ownership chains                                 │
│  - AI permissions schema                            │
│  STATUS: Done                                       │
└─────────────────────────────────────────────────────┘
```

### Path A: Permission Registry (Now)

**Value proposition to suppliers**: "Make your catalog queryable by AI platforms with clear, structured permissions."

**What it enables**:
- AI platforms can query: "Show me all tracks that allow training + commercial use"
- Bulk licensing deals for model training datasets
- Compliance checking before AI platforms use content

**Technical requirements**:
- Structured `ai_permissions` schema (done)
- Filter/query API on permissions (partial)
- Catalog management UI (done)
- Bulk import pipeline (done)

### Path B: Licensed Source Material (Later)

**Value proposition**: "Generate using specific licensed tracks, pay per use."

**What it enables**:
- Explicit, licensed usage of specific catalog items
- Real-time asset delivery for generation
- Per-generation usage tracking and billing
- Audio fingerprinting to verify what was used

**Technical requirements** (not yet built):
- Asset storage and delivery infrastructure
- Usage metering at generation level
- Billing/settlement system
- Possibly audio fingerprinting (Chromaprint/AcoustID)

### Why Path A First

1. **Path A is the foundation Path B requires**—you can't do per-track licensing without the permission registry
2. **Path A is simpler to build and sell**—it's catalog management + permissions, not real-time asset delivery
3. **Path A generates supply**—once catalogs are onboarded, Path B has content to license
4. **Path A is the demo story**—"your catalog, AI-ready" is compelling to rights holders

---

## ADR-003: Current Generative AI vs. Licensed Generation

**Date**: 2025-12-10
**Status**: Informational
**Context**: Understanding how Clearinghouse relates to existing music AI platforms.

### Current State: Keyword-Based Generation

Platforms like Suno and Udio use text prompts:

> "Make something that sounds like Michael Jackson"

The model was trained on music (possibly including MJ) and generates **new audio** in that style. No specific track is referenced. The rights question is murky.

### Future State: Licensed Source Material

What Clearinghouse could enable:

> "Generate using Michael Jackson's 'Thriller' as licensed source material"

This is **explicit, licensed usage** where:
- The AI platform has permission to use actual stems/audio as input
- The specific recording is referenced and tracked
- The rights holder is paid per use
- Provenance is recorded

### Implications for Clearinghouse

| Approach | What Clearinghouse Provides | Technical Needs |
|----------|----------------------------|-----------------|
| **Current gen AI** (keyword-based) | Permission to train on catalog | Permissions registry (Path A) |
| **Future gen AI** (licensed source) | Specific tracks as generation inputs | Asset delivery + metering (Path B) |

**Key insight**: Path A (permission registry) serves current keyword-based AI. Path B (licensed source material) enables a new generation paradigm where specific content is explicitly licensed and tracked.

---

## ADR-004: Supplier Data Reality

**Date**: 2025-12-10
**Status**: Informational
**Context**: Understanding what data suppliers actually have when they onboard.

### What Suppliers Typically Have

Most catalogs exist as:
- Spreadsheets with basic info (title, artist, ISRC, release date)
- PRO registrations (ASCAP/BMI) with songwriter/publisher splits
- Maybe some genre tags, maybe not

### What They Don't Have

- AI-specific permissions (training, voice synthesis, likeness)
- Rich semantic metadata (mood, energy, instrumentation)
- Structured ownership chains

### Onboarding Opportunity

This gap is actually the value-add:

1. **Import what they have** (CSV, API sync with distributors)
2. **Enrich with AI-assisted tagging** (auto-detect mood, genre from audio)—future
3. **Define AI permissions** (guided workflow)

### Implications

- Bulk import must handle minimal data (title, artist, ISRC)
- Permissions setting is a key onboarding workflow
- Metadata enrichment is a future feature, not MVP requirement

---

## Summary: What to Build Next

Based on these decisions:

| Priority | What | Why |
|----------|------|-----|
| **High** | Filter API by `ai_permissions` fields | Core Path A capability |
| **High** | Demo polish (permissions display, filtering) | Sales tool |
| **Medium** | Bulk import with permissions workflow | Onboarding |
| **Low** | Semantic search UI | Nice-to-have, not core |
| **Future** | Asset delivery + metering | Path B |
| **Future** | Audio fingerprinting | Path B |

---

*Document created: 2025-12-10*
*Source: Architecture discussion during Phase 2 implementation*
