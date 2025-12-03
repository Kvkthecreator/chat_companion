# Substrate Data Types

**Version**: 2.0
**Date**: 2025-12-03
**Status**: Canonical
**Purpose**: Define the foundational data taxonomy for YARNNN's substrate layer
**Changelog**: v2.0 introduces Context Entries as primary context management system

---

## Overview

YARNNN's substrate is a **source-agnostic knowledge layer** where both humans and AI agents contribute, access, and build upon shared context. This document defines the core data types that comprise the substrate.

### Design Principles

1. **Source Agnostic**: All data types can be created and accessed by both users AND agents
2. **Structured Context**: Work recipe context uses schema-driven Context Entries (not freeform blocks)
3. **Multi-Modal Unity**: Context Entries embed asset references directly, unifying text and media
4. **Token Efficiency**: Field-level context selection enables minimal, focused agent prompts
5. **Interoperability Vision**: Substrate should be shareable with any AI system (Claude, ChatGPT, Gemini)

---

## Data Type Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                     SUBSTRATE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          CONTEXT ENTRIES (Primary for Work Recipes)       │   │
│  │                                                           │   │
│  │  Structured, schema-driven, multi-modal context per role  │   │
│  │  Tables: context_entry_schemas, context_entries           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              │ embeds references to              │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              REFERENCE ASSETS (Storage Layer)             │   │
│  │                                                           │   │
│  │  Blob storage for files (images, PDFs, documents)         │   │
│  │  Table: reference_assets                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           BLOCKS (Knowledge Extraction Layer)             │   │
│  │                                                           │   │
│  │  Semantic knowledge units for RAG, search, provenance     │   │
│  │  Table: blocks                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Type 1: Context Entries (NEW - Primary for Work Recipes)

**Definition**: Schema-driven, multi-modal context organized by anchor role.

**Characteristics**:
- One entry per anchor role per basket (singleton) or multiple (arrays like competitors)
- Structured JSONB data following role-specific field schemas
- Embedded asset references via `asset://uuid` pattern
- Completeness scoring for UX guidance
- Field-level access for token-efficient agent prompting

**Backend Tables**:
- `context_entry_schemas` - Defines available fields per anchor role
- `context_entries` - Actual context data per basket

**Schema**:
```sql
-- Schema definitions
CREATE TABLE context_entry_schemas (
    anchor_role TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    category TEXT CHECK (category IN ('foundation', 'market', 'insight')),
    is_singleton BOOLEAN DEFAULT true,
    field_schema JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Context data
CREATE TABLE context_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    basket_id UUID NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,
    anchor_role TEXT NOT NULL REFERENCES context_entry_schemas(anchor_role),
    entry_key TEXT,
    display_name TEXT,
    data JSONB NOT NULL DEFAULT '{}',
    completeness_score FLOAT,
    state TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID,
    UNIQUE(basket_id, anchor_role, entry_key)
);
```

**Example Entry**:
```json
{
  "anchor_role": "brand",
  "data": {
    "name": "Acme Corp",
    "tagline": "Building tomorrow, today.",
    "voice": "Professional yet approachable. Use active voice.",
    "logo": "asset://550e8400-e29b-41d4-a716-446655440000",
    "colors": ["#FF5733", "#3498DB", "#2ECC71"],
    "guidelines_doc": "asset://6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  },
  "completeness_score": 1.0
}
```

**Use Case**: Work recipe context injection. Recipes declare which roles and fields they need.

**See**: [ADR_CONTEXT_ENTRIES.md](../architecture/ADR_CONTEXT_ENTRIES.md) for full architecture.

---

## Type 2: Reference Assets (Storage Layer)

**Definition**: Blob storage for file-based content with classification metadata.

**Characteristics**:
- Files stored in Supabase Storage
- LLM-powered automatic classification
- Referenced from Context Entries via `asset://uuid` pattern
- Permanence rules (permanent vs temporary)

**Backend Table**: `reference_assets`

**Key Fields**:
```sql
id, basket_id, storage_path, file_name, mime_type,
asset_type, asset_category, classification_status,
classification_confidence, work_session_id, created_by_user_id
```

**MIME Type Categories**:

| Category | MIME Types | Examples |
|----------|------------|----------|
| Images | `image/*` | PNG, JPEG, GIF, WebP, SVG |
| Documents | `application/pdf`, `application/vnd.openxmlformats-*` | PDF, DOCX, XLSX, PPTX |
| Data | `text/csv`, `application/json` | CSV, JSON |

**Source Identification**:
- `created_by_user_id` set → User upload
- `work_session_id` set → Agent-generated file

**Relationship to Context Entries**:
- Assets are **storage units** (blobs + metadata)
- Context Entries **reference** assets via `asset://uuid`
- Assets gain semantic meaning through their context entry field

---

## Type 3: Blocks (Knowledge Extraction Layer)

**Definition**: Propositional knowledge units with semantic types and vector embeddings.

**Characteristics**:
- Smallest unit of extractable meaning
- Has semantic type (fact, decision, constraint, assumption, etc.)
- State-based lifecycle (PROPOSED → ACCEPTED → LOCKED)
- Vector embeddings for semantic retrieval
- Governance workflow for mutations
- Optional anchor_role for legacy compatibility

**Backend Table**: `blocks`

**Key Fields**:
```sql
id, basket_id, title, content, semantic_type, state,
embedding, anchor_role, anchor_status,
derived_from_asset_id, origin_ref, created_at
```

**Use Cases**:
- RAG (Retrieval Augmented Generation)
- Semantic search across project knowledge
- Knowledge extraction from documents
- Audit trail of extracted/approved knowledge

**NOT Used For** (as of v2.0):
- Primary work recipe context (use Context Entries instead)
- Asset organization (use Context Entries with embedded refs)

---

## Type 4: Entries (Legacy - Raw Content)

**Definition**: Raw text content from various sources.

**Status**: Legacy pattern. New projects should use Context Entries for structured content.

**Backend Tables**:
- `raw_dumps` - User-pasted text (capture layer)
- `work_outputs` - Agent-generated text (supervision layer)

**Future**: May be deprecated as Context Entries handle structured input.

---

## Source Metadata Pattern

All substrate types support source identification:

| Field | Meaning |
|-------|---------|
| `created_by_user_id` | UUID of user who created (user source) |
| `work_session_id` | UUID of agent session that created (agent source) |
| `created_by` | Generic creator reference (Context Entries) |

**UI Source Badge Logic**:
```typescript
function getSourceBadge(item: SubstrateItem) {
  if (item.work_session_id || item.agent_type) {
    return { label: 'Agent', variant: 'secondary' };
  }
  if (item.created_by_user_id || item.created_by) {
    return { label: 'User', variant: 'outline' };
  }
  return { label: 'System', variant: 'ghost' };
}
```

---

## Architectural Diagram (v2.0)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INPUT LAYER                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   User fills Context Forms ──────────────► context_entries (structured)  │
│           │                                      │                       │
│           │ uploads files                        │ references            │
│           ▼                                      ▼                       │
│   reference_assets ◄──────────────────── asset://uuid patterns          │
│   (blob storage)                                                         │
│                                                                          │
│   User pastes raw text ──────────────────► raw_dumps (legacy capture)   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROCESSING LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   reference_assets ──► LLM Classification ──► asset_type, description   │
│                                                                          │
│   raw_dumps ──► P0 Capture ──► P1 Extraction ──► blocks (proposed)      │
│                                                                          │
│   Document Upload ──► Context Extraction ──► context_entries (fields)   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     WORK RECIPE CONTEXT ASSEMBLY                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Recipe declares:                                                       │
│     context_requirements:                                                │
│       entries:                                                           │
│         - role: "brand"                                                  │
│           fields: ["name", "voice"]  ◄─── Only these fields loaded      │
│         - role: "customer"                                               │
│           fields: ["description", "pain_points"]                         │
│                                                                          │
│   Context Assembly:                                                      │
│     1. Query context_entries by role                                     │
│     2. Project only required fields                                      │
│     3. Resolve asset:// references                                       │
│     4. Inject structured XML/JSON into prompt                            │
│                                                                          │
│   Result: 500-1,500 tokens (vs 3,000-15,000 with blocks)                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            UI LAYER                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  Context Page (Role-Based Cards)                                 │  │
│   │                                                                  │  │
│   │  [🎯 Problem 100%] [👥 Customer 80%] [🔮 Vision 40%]            │  │
│   │  [🏷️ Brand 100%] [📊 Competitors 3]                             │  │
│   │                                                                  │  │
│   │  Click card → Form-based editor per schema                       │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   Legacy Views (if needed):                                              │
│   [ Blocks ] [ Raw Entries ] [ Assets ]                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Anchor Role Vocabulary

Context Entries are organized by **anchor role** - the semantic function the context serves:

### Foundation Roles (Human-Established, Stable)

| Role | Description | Singleton |
|------|-------------|-----------|
| `problem` | The pain point being solved | Yes |
| `customer` | Who this is for (persona) | Yes |
| `vision` | Where this is going | Yes |
| `brand` | Brand identity and voice | Yes |

### Market Roles (Human or Agent, Multiple Allowed)

| Role | Description | Singleton |
|------|-------------|-----------|
| `competitor` | Competitive intelligence | No (array) |
| `market_segment` | Market segment details | No (array) |

### Insight Roles (Agent-Produced, Refreshable)

| Role | Description | Singleton |
|------|-------------|-----------|
| `trend_digest` | Synthesized market trends | Yes |
| `competitor_snapshot` | Competitive analysis summary | Yes |
| `content_calendar` | Generated content schedule | Yes |

---

## Migration from v1.0

### What Changed

| v1.0 | v2.0 |
|------|------|
| Blocks as primary context | Context Entries as primary context |
| Assets disconnected from roles | Assets embedded in entries via `asset://` |
| Full block content in prompts | Field-level projection |
| Flat text, unstructured | Schema-driven, typed fields |

### Coexistence Strategy

- **Context Entries**: New context management (work recipes)
- **Blocks**: Knowledge extraction, RAG, search (unchanged)
- **Reference Assets**: Storage layer (now referenced from entries)
- **raw_dumps**: Legacy capture (may be deprecated)

No data migration required for existing blocks. New context goes to entries.

---

## Related Documents

- [ADR_CONTEXT_ENTRIES.md](../architecture/ADR_CONTEXT_ENTRIES.md) - Architectural decision record
- [CONTEXT_ROLES_ARCHITECTURE.md](CONTEXT_ROLES_ARCHITECTURE.md) - Legacy anchor role architecture
- [TERMINOLOGY_GLOSSARY.md](TERMINOLOGY_GLOSSARY.md) - Terminology standards
- [AGENT_SUBSTRATE_ARCHITECTURE.md](AGENT_SUBSTRATE_ARCHITECTURE.md) - Agent integration patterns

---

**End of Document**
