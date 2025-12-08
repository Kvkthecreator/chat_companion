# YARNNN Documentation Archive

This directory contains historical documentation from previous versions and completed projects.

## Directory Structure

### `/v3.1/` - Version 3.1 Implementation Docs
Documents related to v3.1 semantic layer integration and neural map architecture.

**Contents**:
- V3.1 implementation sequencing
- Week completion reports
- Relationship ontology
- Neural map architecture

**Period**: Oct 2025
**Status**: Completed, superseded by v4.0

---

### `/v3.0/` - Version 3.0 Migration Docs
Documents related to v3.0 substrate unification (context_items → blocks).

**Contents**:
- Frontend migration plans
- Testing plans
- Substrate migration guides

**Period**: Sep 2025
**Status**: Completed, foundational to v4.0

---

### `/features/` - Completed Feature Specifications
Feature specs that have been fully implemented and are now part of core platform.

**Contents**:
- P3/P4 phase completion reports
- Substrate quality refactor summaries
- Document composition refactor plans

**Status**: Implemented, documentation kept for historical reference

---

### `/migrations/` - Completed Database Migrations
Schema change documentation and migration summaries.

**Contents**:
- Schema cleanup summaries
- Substrate v3 migration docs

**Status**: Applied to production, kept for migration history

---

### `/mcp/` - MCP Integration Archives
Completed MCP (Model Context Protocol) integration projects.

**Contents**:
- OAuth refactor summaries
- Launch checklists
- Observability plans

**Status**: Integrated into platform, kept for reference

---

### `/deprecated/` - Obsolete Concepts
Documents describing features or concepts that are no longer part of YARNNN.

**Contents**:
- Graph canon (replaced by Neural Map in v3.1)
- Pre-v3.0 implementation notes
- Old notification canon (superseded by V2)

**Status**: No longer applicable, kept for historical context

---

## Finding What You Need

### "I want to understand how we got here"
→ Read documents in chronological order: v3.0 → v3.1 → v4.0

### "I want to know why feature X works this way"
→ Check `/features/` for original specification

### "I want to see the migration that added table X"
→ Check `/migrations/` for schema change docs

### "I want to understand deprecated concept Y"
→ Check `/deprecated/` with understanding it's no longer used

---

## Active Documentation

For current, canonical documentation, see:

- `/docs/canon/` - Core philosophy and principles (v4.0)
- `/docs/architecture/` - System architecture and design
- `/docs/features/` - Active feature specifications
- `/docs/implementation/` - Technical implementation guides

---

## Archive Policy

**What gets archived**:
- Version-specific implementation docs (after next major version)
- Completed feature specs (after 6 months in production)
- Migration docs (immediately after application)
- Deprecated concepts (as soon as superseded)

**What doesn't get archived**:
- Canon documents (updated in place with version markers)
- Architecture documents (living references)
- Active feature specs (until deprecated)
- Implementation guides (until feature removed)

**Retention**: Archives kept indefinitely for institutional knowledge.

---

**Last Updated**: 2025-10-31 (v4.0 documentation refactor)
