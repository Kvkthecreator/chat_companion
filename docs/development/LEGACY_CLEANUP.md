# Legacy Code Cleanup

> **Status**: Pre-execution analysis
> **Created**: 2026-01-26
> **Purpose**: Document legacy code from Episode-0 that can be safely removed

---

## Executive Summary

The companion app was built on top of a previous product (Episode-0/fantazy). Several legacy files and patterns remain that are no longer used by the companion system. This document identifies what can be cleaned up.

---

## Safe to Remove

### 1. Legacy Memory Service

**Files**:
- `api/api/src/app/services/memory.py` - Episode-0 memory system
- `api/api/src/app/models/memory.py` - Legacy memory models

**Why safe**:
- `MemoryService` is defined but never instantiated
- The companion uses `ContextService` and `ThreadService` instead
- References to `memory_events` table (Episode-0) vs `user_context` table (companion)

**Action**: Remove files and update `api/api/src/app/services/__init__.py` exports

### 2. Legacy Memory Routes (Partial)

**File**: `api/api/src/app/routes/memory.py`

**What's legacy** (lines 415-578):
- Routes that reference `memory_events` table
- `MemoryEvent`, `MemoryEventCreate`, `MemoryType` models
- `/memory` POST endpoint (uses Episode-0 memory_events)
- `/memory/relevant` GET endpoint
- `/memory/{memory_id}` DELETE endpoint
- `/memory/{memory_id}/reference` POST endpoint

**What's current** (lines 1-413):
- Memory summary/full endpoints (use `user_context`)
- Thread management endpoints
- Context CRUD endpoints

**Action**: Remove lines 415-578, remove legacy imports

### 3. Legacy Models

**File**: `api/api/src/app/models/hook.py` (if exists)

**Why safe**: Episode-0 used "hooks" for story triggers. Not used in companion.

### 4. Legacy Migrations (Reference Only)

**Files** in `supabase/migrations/`:
- `001_users.sql` through `066_props_for_refactored_series.sql` - Episode-0 schema
- `fantazy_combined.sql` - Combined legacy schema

**Why NOT removed**:
- Migrations are historical records
- Tables may exist in production database
- Removing migrations doesn't remove tables

**Action**: Keep for reference, but document in SCHEMA.md that 100+ are companion schema

---

## Dual Approaches to Consolidate

### 1. Memory Storage: user_context vs memory_events

**Current state**:
- Episode-0 uses `memory_events` table
- Companion uses `user_context` table
- Both exist in database

**Companion approach** (keep):
- `user_context` with categories (fact, thread, follow_up, pattern)
- `ContextService` for extraction
- `ThreadService` for thread tracking

**Action**: Remove all code referencing `memory_events`

### 2. Messages Table: messages vs companion_messages

**Current state**:
- Episode-0 uses `messages` table
- Companion uses `companion_messages` table
- Both exist in database

**Companion approach** (keep):
- `companion_messages` table
- Clear naming to avoid confusion

**Action**: Update any documentation referencing `messages` to `companion_messages`

---

## Code Cleanup Checklist

### High Priority (Before Domain Layer Implementation)

- [ ] Remove `api/api/src/app/services/memory.py`
- [ ] Remove legacy imports from `api/api/src/app/services/__init__.py`
- [ ] Clean up `api/api/src/app/routes/memory.py` (remove Episode-0 routes)
- [ ] Remove `api/api/src/app/models/memory.py` (if separate from hook.py)

### Medium Priority (Can Do Anytime)

- [ ] Remove `HAS_LEGACY_MEMORY` import checks in routes/memory.py
- [ ] Clean up legacy Episode-0 references in LLM prompts
- [ ] Remove any `memory_events` table references

### Low Priority (Reference/Documentation)

- [ ] Add note to migrations README about legacy 001-066
- [ ] Archive Episode-0 documentation if any exists

---

## Verification Before Cleanup

Before removing any code, verify:

1. **No runtime usage**:
   ```bash
   grep -r "MemoryService(" api/  # Should return 0 results
   grep -r "memory_events" api/   # Check each reference is legacy
   ```

2. **Tests pass** (if any):
   ```bash
   cd api && python -m pytest
   ```

3. **No import errors after removal**:
   ```bash
   cd api && python -c "from app.routes import router"
   ```

---

## Post-Cleanup State

After cleanup, the codebase will have:

**Memory System** (single approach):
- `ContextService` - Extract facts from conversations
- `ThreadService` - Track ongoing situations
- `PatternService` - Detect behavioral patterns
- All stored in `user_context` table

**API Routes**:
- `/memory/summary` - Dashboard card
- `/memory/full` - Management page
- `/memory/context/*` - CRUD operations
- `/memory/threads/*` - Thread management

**No References To**:
- `memory_events` table
- `MemoryService` class
- Episode-0 memory models
- Legacy hook system
