# YARNNN Documentation Archive

**Historical Documentation and Deprecated Specifications**

**Last Updated**: 2025-10-31

---

## 📦 Archive Structure

This directory contains historical documentation from previous YARNNN versions. Documents here are **no longer canonical** but are preserved for reference and understanding the platform's evolution.

---

## 📂 Directories

### `v3.1/` - Context OS (v3.1)

**Date Range**: 2025-01-15 → 2025-10-31

**Key Features**:
- Semantic intelligence layer (vector embeddings + causal relationships)
- Substrate-only governance (blocks, documents)
- Emergent memory architecture
- No work orchestration layer

**Archived Documents**:
- `V3.1_IMPLEMENTATION_SEQUENCING.md` - Implementation roadmap for v3.1
- `V3.1_WEEK1_COMPLETION_REPORT.md` - Week 1 progress report
- `V3.1_WEEK2_COMPLETION_SUMMARY.md` - Week 2 completion
- `V3.1_RELATIONSHIP_ONTOLOGY.md` - Relationship types specification

**Why Archived**: YARNNN v4.0 evolved from pure "Context OS" to "AI Work Platform" integrating work orchestration + context management with unified governance.

---

### `v3.0/` - Unified Substrate (v3.0)

**Date Range**: 2024-12 → 2025-01-15

**Key Features**:
- Unified substrate table (context_items → blocks)
- Emergent anchors (no predefined categories)
- Universal versioning (parent_block_id chains)
- Workspace/basket scopes

**Archived Documents**:
- `V3_TESTING_PLAN.md` - Testing strategy for v3.0
- `V3_FRONTEND_MIGRATION.md` - Frontend migration guide

**Why Archived**: v3.1 enhanced v3.0 with semantic layer. v4.0 further evolved with work orchestration.

---

### `features/` - Completed Feature Specs

**Historical feature specifications** that were implemented and superseded by newer versions.

**Subdirectories**:
- `old-canon/` - Pre-v4.0 canonical documents (governance, substrate, timeline, etc.)
- `specialized/` - Specialized features (basket inference, neural map, document modes, onboarding)

**Why Archived**: Features evolved significantly in v4.0. Refer to `docs/features/` for current specifications.

---

### `migrations/` - Migration Guides

**Database and API migration guides** between versions.

**Contents**:
- `YARNNN_SUBSTRATE_V3_MIGRATION.md` - v3.0 substrate migration
- `SCHEMA_SNAPSHOT.sql` - Historical schema snapshot (2025-10-23)
- Migration scripts and breaking change documentation

---

### `mcp/` - MCP Server Documentation

**Model Context Protocol (MCP)** server specifications and implementation guides.

**Contents**:
- `MCP_INTEGRATION_ARCHITECTURE.md` - MCP integration architecture
- `MCP_LAUNCH_CHECKLIST.md` - Launch checklist
- `MCP_OBSERVABILITY_PLAN.md` - Observability planning
- `MCP_OPENAI_APPS_TODO.md` - OpenAI apps integration
- `MCP_TOOL_CATALOG.md` - Tool catalog
- `CHATGPT_MCP_PREVIEW.md` - ChatGPT MCP preview
- `CLAUDE_REMOTE_MCP.md` - Claude remote MCP

**Status**: May still be relevant for MCP server implementation.

---

### `deprecated/` - Obsolete Documentation

**Completely obsolete documentation** that no longer applies to any version of YARNNN.

**Contents**:
- `YARNNN_ASYNC_INTELLIGENCE.md` - Async intelligence (superseded)
- `YARNNN_BACKEND_AGENTSETUP.md` - Old agent setup
- `YARNNN_BATCH_INGESTION_SPEC.md` - Batch ingestion
- `YARNNN_CONTRACT_ALIGNMENT.md` - Contract alignment
- `YARNNN_DELETION_RETENTION_CANON_v1.0.md` - Old retention policy
- `YARNNN_EXTERNAL_SHARING_AND_INTEGRATIONS.md` - External sharing
- `YARNNN_INTERFACE_SPEC_v0.1.0.md` - Interface spec v0.1
- `YARNNN_MEMORY_MODEL.md` - Old memory model
- `YARNNN_NARRATIVE_DESIGN.md` - Narrative design
- `YARNNN_PRESENTATION_LAYERS.md` - Presentation layers
- `YARNNN_SUBSTRATE_DELTA_ENGINE.md` - Delta engine
- `YARNNN_TESTING_HARNESS.md` - Testing harness
- `YARNNN_UNIFIED_FLOW.md` - Unified flow

**Why Archived**: Abandoned features, incorrect designs, or superseded approaches.

---

### `planning/` - Historical Planning Documents

**Implementation plans, refactoring plans, and strategic decision documents.**

**Contents**:
- `OPTION_B_IMPLEMENTATION_PLAN.md` - Option B implementation
- `P3_P4_PHASE_4_COMPLETE.md` - Phase completion report
- `SEMANTIC_LAYER_INTEGRATION_DESIGN.md` - Semantic layer design
- `STRATEGIC_DECISION_REQUEST.md` - Strategic decisions
- `YARNNN_P3_P4_IMPLEMENTATION.md` - P3/P4 implementation
- `UI_REFACTOR_PLAN_BUILDING_BLOCKS_GOVERNANCE.md` - UI refactor plan
- `DOCUMENT_COMPOSITION_REFACTOR_PLAN.md` - Document composition refactor
- `BASKET_BUILDING_BLOCKS_AUDIT.md` - Building blocks audit
- `SUBSTRATE_QUALITY_REFACTOR_SUMMARY.md` - Quality refactor summary
- `SCHEMA_CLEANUP_SUMMARY.md` - Schema cleanup
- `MCP_OAUTH_REFACTOR_SUMMARY.md` - MCP OAuth refactor
- `MCP_SERVER_AUDIT_AND_REFACTORING_PLAN.md` - MCP server audit
- `OAUTH_REDIRECT_FIX.md` - OAuth redirect fix

**Why Archived**: Completed implementation plans no longer needed for reference.

---

## 🔍 Finding Historical Context

### By Version

**Looking for v3.1 docs?** → `archive/v3.1/`

**Looking for v3.0 docs?** → `archive/v3.0/`

**Looking for older versions?** → `archive/deprecated/`

**Looking for planning documents?** → `archive/planning/`

### By Feature

**Looking for old governance specs?** → Current: [docs/features/governance/](../features/governance/)

**Looking for old substrate specs?** → Current: [YARNNN_SUBSTRATE_CANON_V3.md](../YARNNN_SUBSTRATE_CANON_V3.md) (updated for v4.0)

**Looking for old architecture docs?** → Current: [docs/architecture/](../architecture/)

---

## 📖 Reading Archived Documentation

**Important Notes**:

1. **Not Canonical**: Archived docs are **historical references only**, not authoritative.
2. **May Be Outdated**: Code examples, API endpoints, and schemas may no longer work.
3. **Context Required**: Understand which version the doc applies to before using.
4. **Current Docs First**: Always check current documentation before consulting archives.

---

## 🔗 Current Documentation

**For current YARNNN v4.0 documentation**, see:

### Canon (Philosophy)
- [YARNNN_PLATFORM_CANON_V4.md](../canon/YARNNN_PLATFORM_CANON_V4.md) - Core identity
- [YARNNN_WORK_PLATFORM_THESIS.md](../canon/YARNNN_WORK_PLATFORM_THESIS.md) - Value proposition
- [YARNNN_GOVERNANCE_PHILOSOPHY_V4.md](../canon/YARNNN_GOVERNANCE_PHILOSOPHY_V4.md) - Governance principles

### Architecture
- [YARNNN_LAYERED_ARCHITECTURE_V4.md](../architecture/YARNNN_LAYERED_ARCHITECTURE_V4.md) - System design
- [YARNNN_UNIFIED_GOVERNANCE.md](../architecture/YARNNN_UNIFIED_GOVERNANCE.md) - Governance layer
- [YARNNN_DATA_FLOW_V4.md](../architecture/YARNNN_DATA_FLOW_V4.md) - Request flows
- [YARNNN_API_SURFACE.md](../architecture/YARNNN_API_SURFACE.md) - API reference
- [YARNNN_ARCHITECTURE_CANON.md](../YARNNN_ARCHITECTURE_CANON.md) - Deployment architecture

### Features
- [Work Management](../features/work-management/) - Work sessions, artifacts, checkpoints
- [Governance](../features/governance/) - Policies, workflows, risk, audit
- [Integrations](../features/integrations/) - Agent providers, timeline, notifications

---

## 📊 Version Comparison

| Feature | v3.0 | v3.1 | v4.0 |
|---------|------|------|------|
| **Substrate** | Unified blocks | + Semantic layer | + Work orchestration provenance |
| **Governance** | Basic proposal workflow | Substrate-only | **Unified (work + substrate)** |
| **Work Orchestration** | ❌ None | ❌ None | ✅ **Full layer** |
| **Agent SDK** | ❌ None | ❌ None | ✅ **Integrated** |
| **Risk Assessment** | ❌ Manual | ❌ Manual | ✅ **Multi-factor automated** |
| **Auto-Approval** | ❌ None | ❌ None | ✅ **Trust-based** |
| **Provenance** | Basic | Basic | ✅ **Complete lineage** |

---

## 🗑️ Deletion Policy

**Retention**: Archive documents are retained indefinitely by default.

**Deletion Criteria**: Documents may be deleted if:
- Completely obsolete (no historical value)
- Duplicate of other archived docs
- Contains sensitive/incorrect information

**Before Deletion**: Document title and reason added to this index.

---

## 📎 See Also

- [DOCUMENTATION_REFACTOR_PLAN_V4.md](../DOCUMENTATION_REFACTOR_PLAN_V4.md) - Refactoring plan that created this archive
- [README.md](../../README.md) - Main repository README
- [docs/canon/](../canon/) - Current canon documentation

---

**Archive Principle**: Preserve history, prioritize present. When in doubt, check current docs first.
