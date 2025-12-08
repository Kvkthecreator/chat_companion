# Legacy Unified Governance Documents

**Date Archived**: 2025-11-09
**Status**: ⚠️ DEPRECATED - DO NOT IMPLEMENT

## Why These Documents Are Archived

These documents describe a **"unified governance"** approach that was designed **before the architectural split** between work-platform and substrate-api services was finalized.

### The Problem

The unified governance model proposed that:
- User approves work quality ONCE
- System automatically creates blocks in substrate (bypassing proposals)
- Single approval → dual effect (work quality + substrate integrity)

This approach **bypassed substrate governance** (P1 proposals, semantic dedup, quality validation) and created architectural conflicts.

### The Solution (Nov 2025-11-05)

YARNNN now uses **SPLIT GOVERNANCE**:

1. **Work-Platform Governance**: Reviews agent work quality only
2. **Substrate Governance**: Independently validates memory integrity via proposals
3. **Bridge Layer**: Converts approved work artifacts → substrate proposals

**See**:
- [Governance Cleanup Summary](../../architecture/GOVERNANCE_CLEANUP_SUMMARY_2025_11_05.md)
- [Governance Separation Refactor Plan](../../architecture/GOVERNANCE_SEPARATION_REFACTOR_PLAN.md)
- [YARNNN Architecture Canon](../../YARNNN_ARCHITECTURE_CANON.md) - Section on Split Governance

## What's in This Archive

- `YARNNN_UNIFIED_GOVERNANCE.md` - Legacy spec for unified governance (DO NOT IMPLEMENT)

## Current Canon

**Canonical Governance Architecture** (as of 2025-11-05):
- Work-platform has its OWN governance (work quality)
- Substrate-api has its OWN governance (memory integrity via proposals)
- These are INDEPENDENT systems with a bridge layer between them

---

**Status**: Archived for historical reference only
**Next Steps**: Implement WorkToSubstrateBridge as specified in Governance Separation Refactor Plan
