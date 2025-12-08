# YARNNN Architecture Canon — Unified System Architecture

**The Single Source of Truth for YARNNN System Architecture, Deployment, and Implementation**

**Version**: 4.0 (Updated for AI Work Platform)
**Date**: 2025-10-31
**Status**: ✅ Canonical

This document consolidates current implementation status, actual production architecture, and monorepo structure into a comprehensive architectural reference.

---

## 🆕 v4.0 Architecture Update (2025-10)

YARNNN has evolved from a **context-first memory OS** to an **AI Work Platform** where deep context understanding enables superior agent supervision.

### Key v4.0 Changes

**New Four-Layer Architecture**:
1. **Layer 4: Presentation** - Work review UI, substrate management (Next.js)
2. **Layer 3: Unified Governance** - Work quality + substrate integrity approval (Python orchestrator)
3. **Layer 2: Work Orchestration** - Agent sessions, artifacts, checkpoints (PostgreSQL + FastAPI)
4. **Layer 1: Substrate Core** - Blocks, documents, timeline, semantic layer (Supabase + FastAPI)

**New Governance Model**:
- **Single Approval → Dual Effect**: User reviews work quality once → Substrate automatically updated
- **Multi-Checkpoint Supervision**: Plan approval, mid-work review, artifact review, final approval
- **Risk-Informed Review**: High-risk artifacts get human attention, low-risk auto-approved
- **Complete Provenance**: Every substrate change traces to work session → artifact → reasoning

**New Work Orchestration Layer**:
- `work_sessions` - Track agent execution lifecycle
- `work_artifacts` - Agent outputs awaiting approval
- `work_checkpoints` - Multi-stage approval workflow
- `work_iterations` - Feedback loops for work refinement
- `work_context_mutations` - Audit trail of substrate changes

**See**:
- [YARNNN Platform Canon v4.0](canon/YARNNN_PLATFORM_CANON_V4.md) - Core philosophy
- [Layered Architecture v4.0](architecture/YARNNN_LAYERED_ARCHITECTURE_V4.md) - Complete system design
- [Unified Governance](architecture/YARNNN_UNIFIED_GOVERNANCE.md) - Governance layer spec
- [Data Flow v4.0](architecture/YARNNN_DATA_FLOW_V4.md) - End-to-end request flows
- [API Surface](architecture/YARNNN_API_SURFACE.md) - Complete API reference

---

## ✅ What's Implemented and Working

### Frontend Architecture
- **Centralized API Client**: `web/lib/api/client.ts` ✅
  - Single source of truth for ALL API calls
  - Unified error handling and request formatting
  - Type-safe basket operations
  
- **Operational Hook**: `web/hooks/useBasketOperations.ts` ✅
  - Combines API calls with React state management
  - Loading states, error handling, and success callbacks
  - Ready for component adoption
  
- **Realtime Integration**: Supabase-based realtime updates ✅
  - `web/lib/hooks/useBasketEvents.ts` for event subscriptions
  - Database triggers sync basket_deltas → baskets table

### Backend Architecture
- **BFF Data Access Pattern**: Direct SQL with workspace filtering ✅
  - All routes use `db=Depends(get_db)` for database access
  - JWT auth via `verify_jwt` dependency, authorization via workspace_id in SQL
  - Pgbouncer compatible: `statement_cache_size=0` prevents prepared statement errors
  - **See**: [BFF_DATA_ACCESS_PATTERN.md](BFF_DATA_ACCESS_PATTERN.md)

- **Canonical Queue Processor**: `api/src/services/canonical_queue_processor.py` ✅
  - Orchestrates P0-P4 pipeline agents in strict sequence
  - Processes dumps via queue system with atomic claiming
  - Real P1 agent with OpenAI structured extraction (not full SDK)

- **Repository Pattern**: `api/src/repositories/` ✅
  - `BasketRepository` - CRUD operations for baskets
  - `DeltaRepository` - Delta persistence and retrieval
  - `EventRepository` - Event publishing for realtime

- **API Integration**: `web/app/api/baskets/[id]/work/route.ts` ✅
  - Bridge between Next.js frontend and FastAPI backend
  - Proper request forwarding and error handling

- **Idempotency System**: Request deduplication working ✅
  - Prevents duplicate processing of basket work requests
  - Cached results for repeated requests

### Governance Architecture ✅ (v4.0: SPLIT GOVERNANCE - Updated 2025-11-05)

**CRITICAL: YARNNN has TWO INDEPENDENT GOVERNANCE SYSTEMS**

#### 1. Work-Platform Governance (work-platform service)
**Concern**: Work quality, task completion, agent deliverables
**Question**: "Did the agent do good work?"

- **Work Session Lifecycle**: `initialized` → `in_progress` → `pending_review` → `approved` / `rejected`
- **Work Artifacts**: Agent outputs awaiting quality review
- **Approval Decision**: User reviews agent work quality only
- **Output**: Approved artifacts (ready for substrate submission)

#### 2. Substrate Governance (substrate-api service)
**Concern**: Memory integrity, semantic deduplication, quality validation
**Question**: "Should this become persistent memory?"

- **Proposal System**: ALL substrate mutations via `proposals` table
- **P1 Validation**: Semantic dedup, quality checks, merge detection
- **Block Creation**: Only through approved proposals (ENFORCED)
- **Provenance**: Links back to source (raw_dump or work_artifact)

#### Critical Separation (as of 2025-11-05):
- ✅ **Substrate governance**: WORKING & ENFORCED (P1 proposals only)
- ⚠️ **Work-platform governance**: SCHEMA READY, integration NOT YET IMPLEMENTED
- ❌ **"Unified Approval Orchestrator"**: DISABLED (bypassed proposals - see GOVERNANCE_CLEANUP_SUMMARY_2025_11_05.md)

**See**:
- [Governance Cleanup Summary (2025-11-05)](architecture/GOVERNANCE_CLEANUP_SUMMARY_2025_11_05.md) - Current state
- [Governance Separation Refactor Plan](architecture/GOVERNANCE_SEPARATION_REFACTOR_PLAN.md) - Future implementation plan

### Data Flow (v4.0: Split Governance - TO BE IMPLEMENTED)
1. **Frontend** → Create work session via `/api/work/sessions`
2. **Agent** → Executes task, creates work_artifacts
3. **Work Governance** → User reviews work quality, approves/rejects
4. **Bridge** (TODO) → Submit approved artifacts as substrate proposals
5. **Substrate Governance** → P1 validates proposals (semantic dedup, quality)
6. **Substrate** → Approved proposals create blocks (or merge with existing)
7. **Notification** → Work-platform notified of substrate mutations
8. **Timeline Events** → Both work approval + substrate changes logged

## 🧹 Recent Cleanup (Completed)

### Centralization Achieved
- ✅ **All services use ApiClient** - No more scattered fetch() calls
- ✅ **6+ services migrated** - UniversalChangeService, SubstrateService, etc.
- ✅ **Legacy API wrappers deprecated** - Clear migration path marked
- ✅ **Components updated** - YarnnnThinkingPartner uses centralized API

### Code Quality
- ✅ **TypeScript build passes** - No type errors
- ✅ **Tests added** - Basic coverage for API client and hooks
- ✅ **Unused code documented** - Performance system marked experimental
- ✅ **Architecture documented** - This file matches reality

## 📋 What's NOT Implemented (By Conscious Choice)

### Not Needed at Current Scale
- **Redis caching** - PostgreSQL + proper indexes are fast enough
- **Message queues** - Database events + Supabase Realtime sufficient
- **Complex state management** - Hooks + Context + Supabase work well
- **Microservices** - Monolith is appropriate for team size

### Experimental/Future Features
- **Performance monitoring system** (`web/lib/performance/`) - Not yet integrated
- **Advanced caching** (`CacheManager`) - Will add when performance requires
- **Bundle optimization tools** - Current build times acceptable

## 🔧 How It All Works Together

### v4.0: Creating an Agent Work Task

```typescript
// Component level (Layer 4)
const createTask = async () => {
  const response = await fetch('/api/work/sessions', {
    method: 'POST',
    body: JSON.stringify({
      workspace_id: currentWorkspace.id,
      basket_id: currentBasket.id,
      task_intent: "Research competitors in AI memory space",
      task_type: "research",
      approval_strategy: "final_only"
    })
  })

  const session = await response.json()
  router.push(`/work/${session.id}`)
}

// Under the hood (v4.0 flow):
// 1. Frontend → Next.js API route → FastAPI backend
// 2. Work session created (Layer 2) → status: 'initialized'
// 3. Agent executes task, retrieves context from substrate (Layer 1)
// 4. Agent creates artifacts (Layer 2) → status: 'pending_review'
// 5. User reviews work (Layer 4) → Unified orchestrator (Layer 3)
// 6. Approved artifacts → Substrate blocks (Layer 1) in ACCEPTED state
// 7. Timeline event created → Notifications sent
// 8. Realtime → Frontend updates with completion + substrate changes
```

### v4.0: Reviewing Agent Work

```typescript
// User reviews work session
const handleApprove = async () => {
  const decision = {
    workQuality: 'approved',
    artifactDecisions: {
      'artifact-1': 'apply_to_substrate',  // Create block
      'artifact-2': 'apply_to_substrate',  // Create block
      'artifact-3': 'approve_only'         // Good work, no substrate impact
    }
  }

  const result = await fetch(`/api/governance/sessions/${sessionId}/review`, {
    method: 'POST',
    body: JSON.stringify({ decision })
  })

  // Result includes substrate changes applied
  const { substrateChanges } = await result.json()
  // substrateChanges.blocksCreated = [block-id-1, block-id-2]
}

// Under the hood (v4.0 unified governance):
// 1. Unified orchestrator validates authorization (Layer 3)
// 2. For each artifact with 'apply_to_substrate':
//    - Create block in ACCEPTED state (Layer 1)
//    - Generate embedding for semantic search
//    - Extract relationships
//    - Link artifact → block (provenance)
// 3. Update work session → status: 'completed_approved'
// 4. Update agent track record (approval rate)
// 5. Emit timeline event (work_approved)
// 6. Send notifications to workspace members
```

### Real-time Updates (v4.0)
```typescript
// Frontend automatically gets updates via:
// 1. Timeline events → Database trigger → Notifications table
// 2. Supabase Realtime subscription (postgres_changes)
// 3. useWorkspaceNotifications hook
// 4. Toast notification + UI update
```

## 🎯 Current System Strengths (v4.0)

1. **Simple & Reliable** - No over-engineering, everything has a clear purpose
2. **Real Agent Integration** - Actually calls worker agents, no fake data
3. **Type Safety** - Full TypeScript coverage with proper contracts
4. **Centralized APIs** - Single source of truth, easy to debug
5. **Realtime Updates** - Immediate UI feedback on backend changes
6. **Proper Error Handling** - Graceful degradation and user feedback
7. **Testable** - Clean architecture makes testing straightforward
8. **Single Approval → Dual Effect** - Users review once, both work + substrate handled
9. **Risk-Informed Governance** - High-risk gets scrutiny, low-risk auto-approved
10. **Complete Provenance** - Every block traces to work session + reasoning
11. **Iterative Supervision** - Feedback loops improve agent outputs
12. **Trust Calibration** - Agent performance enables progressive automation

## 📊 Performance Characteristics

- **API Response Times**: ~200-500ms for basket work (depends on agent complexity)
- **Build Time**: ~6-8s (acceptable for development)
- **Bundle Size**: ~200KB compressed (well within limits)
- **Memory Usage**: Stable, no significant leaks detected
- **Database Performance**: Sub-10ms queries with proper indexing

## 🚀 Next Steps (When Needed)

### If Performance Becomes an Issue
1. Enable `CacheManager` integration with `ApiClient`
2. Add performance monitoring dashboard
3. Implement bundle optimization for large components

### If Scale Increases
1. Consider worker queues for long-running agent tasks
2. Add Redis for session/request caching
3. Implement more sophisticated error recovery

### If Team Grows
1. Add more comprehensive test coverage
2. Implement integration test suite
3. Add development tooling for debugging

---

**Status**: ✅ **Production Ready**
**Last Updated**: December 2024
**Confidence Level**: High - all major features tested and working

---

## 📊 Production Architecture Implementation

### Current Real-time System: Polling-Based

**Technical Decision: Pragmatic over Perfect**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Hook    │────│   Polling Loop   │────│   Supabase DB   │
│ useBasketEvents │    │   (3s interval)  │    │  basket_events  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                        │
        ▼                       ▼                        ▼
   Same Interface        Reliable Updates       Standard API Calls
```

**Problem**: Supabase WebSocket authentication SDK issues  
**Solution**: 3-second polling with identical interface  
**Trade-off**: Slight delay vs shipping working product  

### Implementation Details

```typescript
// Current: Polling (Production)
export function useBasketPolling(basketId: string) {
  useEffect(() => {
    const pollEvents = async () => {
      const { data } = await supabase
        .from('basket_events')
        .select('*')
        .eq('payload->>basket_id', basketId)
        .order('created_at', { ascending: false });
      // Process new events...
    };
    
    const interval = setInterval(pollEvents, 3000);
    return () => clearInterval(interval);
  }, [basketId]);
}

// Future: WebSocket (Ready when needed)
export function useBasketWebSocket(basketId: string) {
  // Identical interface, different transport
}
```

---

## 🏗️ Monorepo Architecture & Deployment

### Overview: AI Work Platform Implementation (v4.0)

This monorepo implements the **AI Work Platform** with a Python FastAPI backend (`api.yarnnn.com`), a Next.js frontend (`yarnnn.com`), and a Supabase database. All services run in production; development mirrors the same topology.

**v4.0 Evolution**: From pure context management to integrated work orchestration + context management, with unified governance spanning both.

### Deployment Architecture (Async Intelligence Model)

```
┌──────────────┐ Direct  ┌──────────────┐ Queue  ┌────────────────────┐ SQL ┌──────────────┐
│ yarnnn.com   │◄────────►│  Supabase    │◄──────►│ api.yarnnn.com     │◄───►│  Supabase    │
│ (Next.js)    │  Read    │  Database    │ Poll   │ (FastAPI, Render)  │     │  Database    │
│ Vercel       │          │              │        │                    │     │              │
└──────────────┘          └──────────────┘        └────────────────────┘     └──────────────┘
       │                                                     │
       └─────────────────────────────────────────────────────┘
                          Immediate writes (dumps only)
```

**Service Distribution:**
- **Frontend:** Next.js (Vercel) - Immediate user responses, raw dump creation
- **Agent Backend:** FastAPI (Render) - Async intelligence processing via queue
- **Database:** Supabase (Postgres + RLS) - Single source of truth + queue
- **Flow:** User → Immediate → Queue → Async Intelligence → Progressive UI

### Substrate Layer (v4.0 Enhanced)

**Layer 1: Substrate Core (Peer Entities):**
- **Baskets** – container scope
- **Dumps** – raw captures (files/text)
- **Blocks** – structured interpretations (state: ACCEPTED | PROPOSED | REJECTED | SUPERSEDED)
- **Documents** – composed outputs (P4 task documents, research reports, etc.)
- **Context Items** – semantic connectors
- **Timeline Events** – append-only activity stream (work events + substrate events)
- **Substrate Relationships** – causal, temporal, semantic, contradiction links

**Layer 2: Work Orchestration (New in v4.0):**
- **Work Sessions** – agent execution lifecycle tracking
- **Work Artifacts** – agent outputs awaiting approval
- **Work Checkpoints** – multi-stage approval workflow
- **Work Iterations** – feedback loop records
- **Work Context Mutations** – audit trail of substrate changes

**Layer 3: Unified Governance (New in v4.0):**
- **Agent Track Record** – performance metrics per agent
- **Workspace Approval Policies** – governance configuration per workspace
- **Governance Audit Log** – all governance decisions (append-only)

These layers compose the complete AI Work Platform; agents operate across all layers with governance oversight.

### API Endpoint Distribution (v4.0)

#### Frontend APIs (Vercel - Next.js)
- **Work Sessions:** `POST /api/work/sessions` - Create agent task
- **Work Review:** `GET /api/work/sessions/{id}` - Fetch work for review
- **Governance:** `POST /api/governance/sessions/{id}/review` - Approve/reject work
- **Substrate Read:** `GET /api/substrate/blocks`, `GET /api/substrate/documents`
- **Notifications:** `GET /api/notifications` - User notifications
- **Dashboard:** `GET /api/dashboard/workspaces/{id}` - Aggregated metrics

#### Backend APIs (Render - FastAPI)
- **Work Orchestration:** `/work/*` - Session lifecycle, artifact submission
- **Governance Orchestration:** `/governance/*` - Review processing, risk assessment
- **Substrate Core:** `/substrate/*` - Block/document CRUD, semantic search
- **Agent Providers:** YARNNN Memory, Governance, Tasks (for Agent SDK integration)
- **Timeline:** `/timeline/*` - Event stream access
- **Agent Metrics:** `/governance/agents/{id}/metrics` - Performance tracking

#### Legacy APIs (Being Phased Out)
- **Dumps:** `POST /api/dumps/new` - Raw capture (pre-v4.0)
- **Baskets:** `POST /api/baskets/ingest` - Onboarding (pre-v4.0)
- **Queue:** Agent polling (replaced by work sessions in v4.0)

### Architecture Flow (v4.0)
```
User → Work Session Creation → Agent Execution → Artifact Creation →
User Review (Layer 3 Governance) → Substrate Mutation (Layer 1) →
Timeline Event → Notifications → UI Update
```

### Frontend Configuration
- Connects to backend via `NEXT_PUBLIC_API_BASE_URL`
- Environment-specific configuration for development/production
- Direct Supabase connection for immediate operations

### Development vs Production Topology

**Development:**
- Local Next.js dev server
- Local FastAPI via Docker/direct execution
- Same Supabase instance (development database)

**Production:**
- Vercel deployment for frontend
- Render deployment for backend agents
- Production Supabase instance

---

## 🎯 Architectural Decision Summary (v4.0)

### Why This Architecture Works

1. **Immediate User Feedback**: Frontend provides instant responses for user actions
2. **Asynchronous Intelligence**: Agent processing happens without blocking UI
3. **Single Source of Truth**: Supabase database maintains consistency
4. **Progressive Enhancement**: UI updates as intelligence processing completes
5. **Pragmatic Real-time**: Polling delivers reliable updates without WebSocket complexity
6. **Scalable Services**: Clear separation allows independent scaling of frontend/backend
7. **Single Approval → Dual Effect**: Users review work quality once, substrate automatically updated
8. **Risk-Informed Governance**: Attention focused where it matters (high-risk artifacts)
9. **Complete Provenance**: Every substrate change traces to work session + reasoning
10. **Trust Calibration**: Agent performance enables progressive automation

### Key Trade-offs

1. **Polling vs WebSocket**: Chose reliability over perfect real-time performance
2. **Monolith vs Microservices**: Appropriate for current team size and complexity
3. **Direct DB vs API**: Frontend uses Supabase directly for reads, API for complex operations
4. **Queue vs Immediate**: Agent processing is queued for reliability and scalability
5. **Unified Governance vs Separate**: Single approval flow reduces friction vs separate work/substrate reviews
6. **Four Layers vs Three**: Added work orchestration layer for explicit agent work management
7. **Auto-Approval vs Always Manual**: Trust-based automation for proven agents vs always requiring human review

### Future Evolution Path

1. **WebSocket Migration**: Drop-in replacement when Supabase SDK issues resolve
2. **Service Scaling**: Independent scaling of frontend (Vercel) and backend (Render)
3. **Agent Distribution**: Queue system ready for multiple agent workers
4. **Progressive Enhancement**: Architecture supports adding complexity incrementally
5. **Agent SDK Integration**: Full integration with claude-agentsdk-yarnnn for generic agent framework
6. **Multi-Agent Orchestration**: Complex tasks decomposed across multiple specialized agents
7. **Advanced Risk Models**: ML-based risk prediction using historical governance data

This architecture successfully delivers a production-ready YARNNN v4.0 system that balances immediate user experience with sophisticated agent work management, unified governance, and deep context integration.