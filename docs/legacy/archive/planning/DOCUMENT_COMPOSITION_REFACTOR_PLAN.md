# Document Composition Refactor Plan
## Revolutionary Document Model Implementation

**Date:** October 4, 2025
**Canon Version:** v3.0 (Substrate-First Document Model)
**Discourse Foundation:** First principles analysis of document editing vs substrate management

---

## Executive Summary

YARNNN is fundamentally different from Notion and traditional note-taking apps. This refactor implements the **revolutionary stance**: documents are read-only composed views of substrate, not editable artifacts. Users manage substrate and direct composition instead of editing prose.

### Core Philosophy Shift

**From:** Documents are edited → substrate extracted (Notion model)
**To:** Substrate governed → documents composed (YARNNN model)

**Key Decision:** No direct document editing. Ever.

---

## Canon Principle #5 (NEW)

### **"Substrate Management Replaces Document Editing"**

**Documents are read-only composed views of substrate state. Users do not edit documents—they manage substrate and direct composition.**

#### What Users Do Instead of Editing:

1. **Curate substrate** (replaces: "editing content")
   - Approve/reject/merge blocks via governance
   - Add/remove substrate references from documents
   - Update context_items, blocks through proposals

2. **Direct composition** (replaces: "formatting and structure")
   - Define composition instructions ("make section 2 more technical")
   - Select which substrate to include/exclude
   - Request regeneration with updated parameters

3. **Govern substrate mutations** (replaces: "revising drafts")
   - Review proposals for block updates
   - Approve substrate merges and refinements
   - Validate agent-extracted substrate

4. **Manage versions** (replaces: "save and track changes")
   - Freeze versions as final snapshots
   - Compare versions to see substrate evolution
   - Accept/reject regenerated compositions

#### The Fundamental Shift

- **Traditional:** User types prose → saves → document updated
- **YARNNN:** User curates substrate → requests composition → document regenerated

**Substrate management IS the primary user activity.** Documents are downstream artifacts of well-managed substrate.

#### Time Allocation Expected

- **80%** substrate curation (governance, building-blocks management)
- **20%** composition refinement (document regeneration, instruction tuning)

---

## Mental Model: Three-Layer Separation

### Layer 1: RAW_DUMPS (Immutable Capture)

**Purpose:** Preserve original input exactly as received

**Examples:**
- Uploaded product-spec.docx (full text)
- Pasted Notion page export
- PDF upload with OCR text

**User Interaction:** View original (read-only reference)
**Location:** `/baskets/[id]/timeline` (Uploads tab)

### Layer 2: SUBSTRATE (Governed Knowledge)

**Purpose:** Structured, validated knowledge atoms

**Examples:**
- Blocks extracted from raw_dumps
- Context items identified in uploads
- Timeline events from activity

**User Interaction:** Curate, approve, merge (governance)
**Location:** `/baskets/[id]/building-blocks` page

### Layer 3: DOCUMENTS (Composed Artifacts)

**Purpose:** Narrative compositions from substrate

**Examples:**
- PRD composed from product blocks
- Spec regenerated after substrate update
- Email composed from campaign substrate

**User Interaction:** Manage substrate, refine composition
**Location:** `/baskets/[id]/documents/[doc-id]` page

### The Flow

```
Upload Wizard:
  product-spec.docx
    ↓
  raw_dump (Layer 1) → P1 extraction → Substrate (Layer 2)
                                            ↓
                                       P4 composition
                                            ↓
                                       Document (Layer 3)
```

---

## Schema Evolution

### Current State (Documents - Editing Enabled)

```sql
CREATE TABLE documents (
  id uuid PRIMARY KEY,
  basket_id uuid NOT NULL,
  title text NOT NULL,
  content_raw text NOT NULL,        -- ❌ Enables direct editing
  content_rendered text,             -- ❌ Cached edited content
  current_version_hash varchar(64),
  status text DEFAULT 'draft',
  document_type text DEFAULT 'general',
  metadata jsonb DEFAULT '{}'
);
```

### Target State (Documents - Composition Definitions)

```sql
CREATE TABLE documents (
  id uuid PRIMARY KEY,
  basket_id uuid NOT NULL,
  workspace_id uuid NOT NULL,
  title text NOT NULL,

  -- Composition definition (not content)
  composition_instructions jsonb DEFAULT '{}',
  substrate_filter jsonb DEFAULT '{}',

  -- Linking
  source_raw_dump_id uuid REFERENCES raw_dumps(id),  -- NEW
  current_version_hash varchar(64),

  -- Metadata
  created_at timestamptz DEFAULT now(),
  created_by uuid,
  updated_at timestamptz DEFAULT now()

  -- REMOVED: content_raw, content_rendered (content lives in versions only)
  -- REMOVED: status 'draft' (documents are always computed)
);

COMMENT ON TABLE documents IS
  'Composition definitions that generate versioned artifacts from substrate. Content lives in versions only.';
```

### Document Versions (Immutable Snapshots)

```sql
CREATE TABLE document_versions (
  version_hash varchar(64) PRIMARY KEY,
  document_id uuid NOT NULL,

  -- Frozen content (read-only)
  content text NOT NULL,
  content_rendered text,

  -- Frozen substrate references
  substrate_refs_snapshot jsonb NOT NULL,

  -- Composition provenance
  composition_instructions jsonb,
  composition_signature varchar(64),

  -- Version metadata
  created_at timestamptz DEFAULT now(),
  created_by uuid,
  version_trigger text CHECK (version_trigger IN (
    'initial',            -- First composition
    'substrate_update',   -- Substrate changed
    'user_requested',     -- User clicked "regenerate"
    'instruction_change', -- User modified composition instructions
    'upload_composition'  -- Composed from uploaded document
  )),
  version_message text,
  parent_version_hash varchar(64)
);

COMMENT ON TABLE document_versions IS
  'Immutable snapshots of composed documents. Content is frozen and read-only.';
```

### Raw Dumps (Link to Composed Documents)

```sql
ALTER TABLE raw_dumps
  ADD COLUMN document_id uuid REFERENCES documents(id);

COMMENT ON COLUMN raw_dumps.document_id IS
  'If raw_dump was uploaded as document import, links to composed YARNNN document';
```

---

## Upload Wizard Transformation Flow

### Current Behavior (Wrong)

```
User uploads document.docx
  ↓
Create document with content_raw = original text
  ↓
User can edit document directly
  ❌ Violates substrate-first principle
```

### Target Behavior (Pure Substrate Model)

```
1. User uploads product-spec.docx
   ↓
2. P0: Create raw_dump with full original text
   ↓
3. P1: Substrate extraction → Creates proposals
   ↓
4. User reviews proposals (governance) → Approves
   ↓
5. Substrate committed to basket
   ↓
6. P4: Compose NEW document from extracted substrate
   ↓
7. Show side-by-side:
   [Original upload] ←→ [YARNNN version]
   ↓
8. User: Accept YARNNN version | Cancel upload
   ↓
9. If accepted:
   - Document created (substrate-backed)
   - raw_dump.document_id = document.id
   - documents.source_raw_dump_id = raw_dump.id
```

### Trust Model

**Key Insight:** We don't "migrate" their document. We **transform** it into substrate-backed knowledge.

**Transparency:**
- Show what substrate was extracted (block by block)
- Show regenerated document side-by-side with original
- User explicitly accepts transformation

**If prose changes:**
→ This is a **feature**, proving substrate extraction works

**If user wants exact preservation:**
→ YARNNN is not for them (fundamentally different)

---

## UX Design: Single Panel + FAB

### Document View Layout

```
┌────────────────────────────────────────────────────────────┐
│  Left Nav  │  Main Panel (Document + Substrate Overlay)    │
├────────────┼────────────────────────────────────────────────┤
│            │                                                │
│ 📁 Baskets │  # Product Requirements Document              │
│            │  v2.1 (Latest) · Generated 2 hours ago         │
│ 📄 Docs    │  📎 From uploaded document [View Original]    │
│            │  ─────────────────────────────────────────────│
│ 🔧 Memory  │                                                │
│            │  ## Problem Statement                         │
│            │                                                │
│            │  Lorem ipsum dolor sit amet...                │
│            │                                                │
│            │  ┌─────────────────────────────────────┐      │
│            │  │ 📦 Substrate: [Problem Block #42]   │      │
│            │  │ "Users struggle with X because..."  │      │
│            │  │ Confidence: 0.85 · Updated: 1d ago  │      │
│            │  └─────────────────────────────────────┘      │
│            │                                                │
│            │  More prose continues...                      │
│            │                                                │
└────────────┴────────────────────────────────────────────────┘

                                                    ┌──────────┐
                                                    │    ⚙️    │ ← FAB
                                                    └──────────┘
```

### FAB (Floating Action Button) - Phase 1

```
Click FAB (⚙️) → Expands to action menu:

┌─────────────────────────────────┐
│  📦 Manage Substrate            │
│  🔄 Regenerate Document         │
│  🎨 Refine Composition          │
│  📜 Version History             │
│  📊 View Substrate Graph        │
│  💾 Freeze Current Version      │
└─────────────────────────────────┘
```

### FAB Evolution - Phase 2 (Future)

```
FAB becomes conversational agent interface:

┌─────────────────────────────────┐
│  💬 Chat with Document Agent    │
└─────────────────────────────────┘

User: "Add competitive analysis section"
  ↓
Agent: "Found 3 blocks about competitors.
        Adding as supporting substrate..."
  ↓
Document: Auto-regenerated with new section
```

---

## User Workflows

### Workflow 1: Create New Document

```
1. User: Click "New Document" → Select template "PRD"
   ↓
2. System: Create document with composition_instructions
   ↓
3. User: Select substrate to include:
   - ✅ [Block] Customer research
   - ✅ [Block] Problem statement
   - ✅ [Context] Target audience
   ↓
4. User: Click "Generate Document"
   ↓
5. P4: Compose from substrate + template instructions
   ↓
6. System: Create document_version (immutable)
   ↓
7. User: Views generated document (read-only)
```

### Workflow 2: Update Document (Substrate Changed)

```
1. Substrate changes: New block approved
   ↓
2. System: Detects documents referencing this substrate
   ↓
3. Notification: "Document 'PRD v1' has stale substrate"
   ↓
4. User: Reviews changes → Click "Regenerate"
   ↓
5. P4: Recompose with updated substrate
   ↓
6. System: Create new document_version
   ↓
7. User: Views diff [Old] ←→ [New]
   ↓
8. User: Accept (update current_version_hash) | Reject
```

### Workflow 3: Refine Composition

```
1. User: Views document → "Too technical"
   ↓
2. User: Click FAB → "Refine Composition"
   ↓
3. Modal: Edit composition instructions
   - Section 2: "Make less technical, business-focused"
   ↓
4. User: Click "Regenerate"
   ↓
5. P4: Recompose with new instructions
   ↓
6. User: Views diff → Accept/Reject
```

### Workflow 4: Upload Existing Document

```
1. User: Upload product-spec.docx
   ↓
2. System: Analysis shown
   - "Detected: 12 blocks, 5 context items"
   ↓
3. User: Click "Extract Substrate"
   ↓
4. P1: Substrate proposals created
   ↓
5. User: Reviews proposals (governance) → Approves
   ↓
6. P4: Generate YARNNN document from substrate
   ↓
7. System: Show side-by-side
   [Original] ←→ [YARNNN version]
   ↓
8. User: "Use YARNNN Version"
   ↓
9. Document created, raw_dump preserved
```

---

## Implementation Phases

### Phase 1: Schema Migration (Foundation)

**Goal:** Remove editing capability, establish composition model

**Tasks:**
1. Create migration: Add `composition_instructions`, `substrate_filter`, `source_raw_dump_id` to documents
2. Create migration: Remove `content_raw`, `content_rendered` from documents
3. Create migration: Add `version_trigger` to document_versions
4. Create migration: Add `document_id` to raw_dumps
5. Update database schema snapshot

**Acceptance:**
- Documents table has no content fields
- All document content lives in versions table
- Clear linking: raw_dump ←→ document

### Phase 2: Upload Wizard (Transformation Flow)

**Goal:** Transform uploaded documents via substrate extraction

**Tasks:**
1. Create upload analysis UI (show detected substrate)
2. Implement substrate extraction flow (P0 → P1 → governance)
3. Implement P4 composition from extracted substrate
4. Create side-by-side diff view (original vs YARNNN)
5. Link raw_dump to created document

**Acceptance:**
- User uploads document → raw_dump created
- Substrate extracted and governed
- YARNNN document composed from substrate
- Original preserved in raw_dump

### Phase 3: Document View UX (Single Panel + FAB)

**Goal:** Replace editing interface with substrate management

**Tasks:**
1. Create single-panel document view with substrate overlays
2. Implement FAB component with action menu
3. Create "View Original" affordance (links to raw_dump)
4. Show substrate references inline with document prose
5. Remove all text editing UI (no contenteditable)

**Acceptance:**
- Document view is read-only
- Substrate overlays show which blocks used
- FAB provides all management actions
- No editing affordances visible

### Phase 4: Substrate Management Actions (Manual Operations)

**Goal:** Enable substrate curation and composition refinement

**Tasks:**
1. Implement "Manage Substrate" modal (add/remove references)
2. Implement "Regenerate Document" flow (P4 composition)
3. Implement "Refine Composition" modal (edit instructions)
4. Implement version comparison (diff view)
5. Implement "Freeze Version" (snapshot current state)

**Acceptance:**
- Users can add/remove substrate from documents
- Users can request regeneration with updated substrate
- Users can modify composition instructions
- All changes create new immutable versions

### Phase 5: Page Refactoring (Clean Separation)

**Goal:** Clear mental model across timeline uploads, building blocks, documents

**Tasks:**
1. Update timeline uploads tab to show raw_dump → document links
2. Add "Composed into document" indicators on raw_dumps
3. Add "View Original" links on documents from uploads
4. Ensure /building-blocks shows substrate governance
5. Remove any document editing UI remnants

**Acceptance:**
- Timeline uploads tab shows immutable captures with document links
- /building-blocks shows substrate management (governance)
- /documents shows composition management (regeneration)
- Clear three-layer mental model maintained

---

## Success Metrics

### User Behavior Shift

- **Time in substrate curation** > **Time in document view**
- **Governance approvals** > **Document regenerations** (substrate drives changes)
- **Substrate quality improvements** correlate with **document quality**

### Technical Validation

- Zero direct document edits (enforced by schema)
- All document changes traceable to substrate or instruction changes
- Version history shows clear provenance (substrate_update vs user_requested)

### User Feedback

- "I understand why my document regenerated" (substrate change transparency)
- "I trust the upload wizard" (side-by-side diff builds confidence)
- "Managing substrate is more powerful than editing prose"

---

## Risks & Mitigations

### Risk 1: Users Expect Direct Editing

**Mitigation:**
- Clear onboarding: "YARNNN is fundamentally different"
- Upload wizard builds trust through transparency
- Side-by-side diffs show transformation value

### Risk 2: Upload Wizard Rejects (Poor Substrate Extraction)

**Mitigation:**
- Allow manual substrate refinement before composition
- Show confidence scores on extracted substrate
- Provide "Skip extraction, use as reference only" option

### Risk 3: Composition Quality Below Original

**Mitigation:**
- Start with high-quality P4 composition prompts
- Allow detailed composition instruction tuning
- Preserve original in raw_dump for reference

### Risk 4: Learning Curve Too Steep

**Mitigation:**
- Gradual introduction via guided capture wizards
- Interactive tutorials on substrate management
- FAB evolution path (buttons → conversational agent)

---

## Future Enhancements (Post-Phase 5)

### Agentic Document Management

- Research agents propose new substrate
- Monitoring agents detect staleness
- Composition agents suggest regeneration

### Multi-Document Substrate Reuse

- Same substrate → PRD, spec, email, blog
- Substrate changes propagate to all documents
- Unified substrate curation benefits all artifacts

### Advanced Composition

- Section-level composition instructions
- Template marketplace for document types
- Style transfer (same substrate, different tone)

---

## Conclusion

This refactor implements the **revolutionary stance**: YARNNN is fundamentally different from Notion. Documents are not edited—they're composed from curated substrate.

**The shift:**
- From **prose authoring** to **substrate curation**
- From **document editing** to **composition direction**
- From **typist** to **supervisor**

This is the service philosophy that differentiates YARNNN and creates defensible value through substrate intelligence.

---

**Document Version:** 1.0
**Approved By:** Discourse alignment, October 4, 2025
**Next Step:** Execute Phase 1 (Schema Migration)
