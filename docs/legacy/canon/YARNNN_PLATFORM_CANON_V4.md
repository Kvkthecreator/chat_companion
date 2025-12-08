# YARNNN Platform Canon v4.0 — The AI Work Platform

**The Single Source of Truth for YARNNN Service Philosophy and Implementation**

**Version**: 4.1.0 (Current Implementation - Architecture Corrected)
**Date**: 2025-10-31 (Updated: 2025-11-19)
**Status**: ⚠️ Vision Document with Current Implementation Notes
**Supersedes**: YARNNN_CANON.md (v3.1)

**IMPORTANT**: Sections marked "Vision" describe future goals. See "Current Implementation" notes for actual state.

---

## 🚨 IMPORTANT: Current Implementation Reference (2025-11-15)

**For current Phase 1-4 implementation details, see**:
- [AGENT_SUBSTRATE_ARCHITECTURE.md](./AGENT_SUBSTRATE_ARCHITECTURE.md) - **Current source of truth for agent integration**
- [TERMINOLOGY_GLOSSARY.md](./TERMINOLOGY_GLOSSARY.md) - Prevents terminology confusion across domains

This Canon document describes the **v4.0 VISION and philosophy**. The AGENT_SUBSTRATE_ARCHITECTURE document describes the **actual implementation roadmap** (Phase 1-4 complete, Phase 5+ planned).

**Key Terminology Update**: "Work artifacts" (work-platform) are distinct from "Reflections" (substrate-API P3 outputs). See glossary for complete terminology.

---

## ⚠️ CURRENT IMPLEMENTATION STATUS (As of 2025-11-19)

**This document describes the v4.0 VISION. Implementation Phases 1-4 Complete, Phase 2e Complete.**

**What IS Working** ✅:
- **Substrate Core** (substrate-api): Blocks, documents, insights, timeline, semantic layer
- **Substrate Governance**: P1 pipeline with proposals, semantic deduplication, quality validation
- **Projects**: User-facing work containers (1:1 with baskets currently)
- **Agent Sessions Architecture** (Phase 2e): agent_sessions, work_requests, work_tickets
- **Work Outputs**: Agent deliverables via tool-use pattern (emit_work_output)
- **Work Supervision**: Review workflow (pending_review → approved/rejected)
- **Reference Assets**: Non-text substrate (screenshots, PDFs) in substrate-API
- **Agent Configs**: Dynamic agent_catalog with JSONB configs
- **Knowledge Modules**: Procedural markdown in agent_orchestration/

**What is NOT Yet Implemented** ⏸️:
- **Unified Governance**: Intentionally separated - substrate governance (proposals) vs work supervision (output review)
- **Work→Substrate Auto-Absorption**: Approved outputs do NOT auto-become blocks (deferred)
- **Execution Modes**: Scheduled/autonomous agent runs (Phase 2 next)
- **Thinking Partner**: Meta-agent for insights and recursion decisions (Phase 3)

**Current Architecture**: **TWO-LAYER with SEPARATED governance** (not 4-layer unified)
- **Layer 1 (Substrate Core)**: substrate-API with its own frontend scaffolding (not fully functional)
- **Layer 2 (Work Orchestration)**: work-platform with its own frontend scaffolding (functional)
- **Layer 1 serves as BFF for Layer 2**: work-platform calls substrate-API for context/outputs
- **No Layer 3 "Unified Governance"**: Governance is separated by design
- **No shared Layer 4 Presentation**: Each layer has independent frontends

**See**:
- [`AGENT_SUBSTRATE_ARCHITECTURE.md`](./AGENT_SUBSTRATE_ARCHITECTURE.md) - Current source of truth
- [`PHASE_2E_SESSION_ARCHITECTURE.md`](./PHASE_2E_SESSION_ARCHITECTURE.md) - Latest architecture (Nov 19)
- [`TERMINOLOGY_GLOSSARY.md`](./TERMINOLOGY_GLOSSARY.md) - Domain boundary clarity

---

## 🎯 Core Identity (Vision)

**YARNNN is an AI Work Platform where deep context understanding enables superior agent supervision and work quality.**

We are **not** just a context OS. We are **not** just agent orchestration. We are the **integration** of both—where context and work create emergent value that neither achieves alone.

### The Strategic Positioning

```
┌─────────────────────────────────────────────────────────────┐
│ Traditional Memory Systems (Mem0, Zep, Pinecone)            │
│ - Focus: Store and retrieve context                          │
│ - Missing: Work supervision, governance, agent quality       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Agent Orchestration Platforms (LangGraph, n8n, Temporal)   │
│ - Focus: Run agents and workflows                            │
│ - Missing: Deep context, lineage, unified governance        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ YARNNN: Integrated AI Work Platform                         │
│ ✅ Deep context substrate (blocks, semantic layer, timeline) │
│ ✅ Work orchestration (sessions, tickets, outputs)           │
│ ✅ Separated governance (substrate proposals + work review)  │
│ ✅ Complete provenance (work → reasoning → substrate)        │
└─────────────────────────────────────────────────────────────┘
```

**The Thesis**: Context understanding + Work supervision = Superior AI outcomes

**Note**: "Unified governance" was the v4.0 vision but is intentionally separated in current implementation.

---

## 🌟 The Five Sacred Principles (v4.0)

### 1. **Work Quality is Sacred**

Agent work requires human review before updating context. We supervise AI workers, not just store their outputs.

**Why**: Agents make mistakes. Context pollution is permanent. Human judgment remains essential for quality assurance.

**Manifestation**:
- All agent work flows through `work_tickets` (execution tracking)
- Work outputs await approval via work supervision (not substrate governance)
- Multi-checkpoint supervision for iterative feedback (work_checkpoints)
- Risk assessment guides review attention

### 2. **Context Enables Intelligence**

Deep substrate understanding improves agent reasoning quality. Context is not just storage—it's the foundation for better work.

**Why**: Agents with access to rich, structured context produce higher-quality outputs than those with raw retrieval.

**Manifestation**:
- Task documents (P4) provide narrative context envelopes
- Blocks provide granular facts
- Semantic layer enables intelligent relationship discovery
- Timeline provides temporal context

### 3. **Governance Independence (Current Implementation)**

**Current State**: Work supervision and substrate governance are **intentionally separated**

**Why**: Work quality review and substrate integrity validation have different concerns
- Work supervision: "Did the agent complete the task well?" (work_outputs review)
- Substrate governance: "Should this become memory?" (proposals → deduplication → quality validation)

**Manifestation**:
- Substrate governance via P1 proposals pipeline (working)
- Work supervision via work_outputs review (pending_review → approved/rejected)
- **No automatic bridge**: Approved work outputs do NOT auto-absorb into substrate blocks (intentionally deferred)
- Avoids terminology conflict: "governance" only used for substrate, "supervision" for work outputs

**Original Vision (v4.0 - Deprecated)**: Unified approval orchestrator
- Single review for work quality → automatic substrate application
- Eliminated Nov 2025 because it bypassed substrate proposals and semantic deduplication
- Separated approach maintains substrate integrity guarantees

### 4. **Provenance is Mandatory**

Every work output traces back to work ticket, agent reasoning, and source context. Complete accountability.

**Why**: Without provenance, debugging is impossible, trust erodes, and quality improvement stalls.

**Manifestation**:
- `work_outputs` link to `work_tickets` via work_ticket_id
- `work_outputs.source_context_ids` track which blocks were used for reasoning
- Timeline events capture agent decisions
- `agent_sessions.sdk_session_id` enables Claude SDK conversation history resume
- `work_requests` capture user's original ask (what they wanted done)

### 5. **Supervision is Iterative**

Multi-checkpoint feedback loops improve work quality through conversation, not binary approve/reject.

**Why**: Complex work requires course correction. Iteration beats single-shot judgment.

**Manifestation**:
- Checkpoint types: plan approval, mid-work review, final approval
- `work_iterations` capture feedback loops
- Agent revises based on user feedback
- Configurable approval strategies per user/agent

---

## 🚀 User Mental Model

### The Core Journey

```
[1. Create Task]
      ↓
   User defines intent: "Research AI memory competitors"
      ↓
[2. Agent Works]
      ↓
   Agent queries context (using YARNNN substrate)
   Agent reasons with Claude
   Agent creates artifacts (blocks, documents, insights)
   Agent shows reasoning trail
      ↓
[3. User Reviews]
      ↓
   User sees: artifacts + agent reasoning + confidence
   User decides: approve all / approve some / request changes
   Optionally: Mid-work checkpoints for course correction
      ↓
[4. Context Updates]
      ↓
   Approved artifacts → substrate (blocks created/updated)
   Timeline event emitted
   Substrate hash updated
   Documents marked stale (if needed)
      ↓
[5. Continuous Improvement]
      ↓
   Agent track record improves
   Trust calibration enables auto-approve for low-risk work
   User focuses on high-value supervision
```

### Key User Questions Answered

**"How do I use YARNNN?"**
Create tasks for agents. Review their work. Approved work becomes your knowledge base.

**"What makes YARNNN different?"**
Your agents have access to all your context, not just what fits in a prompt. You supervise work quality once, not context changes separately.

**"Why not just use ChatGPT with RAG?"**
ChatGPT doesn't track work sessions, doesn't require approval, doesn't maintain lineage, and doesn't update your knowledge base. YARNNN is a platform, not a chat interface.

**"What about agent autonomy?"**
Agents work autonomously but outputs require approval. Think "employee with autonomy" not "automation without oversight."

---

## 🏗️ Architecture Overview (Current: 2-Layer with BFF Pattern)

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: WORK ORCHESTRATION (work-platform)                 │
│                                                               │
│ Backend (FastAPI on Render):                                 │
│ - agent_sessions (persistent Claude SDK sessions)            │
│ - work_requests (user asks: what they want done)             │
│ - work_tickets (execution tracking)                          │
│ - work_checkpoints (approval stages)                         │
│ - work_iterations (revision loops)                           │
│ - project_agents (agent instances + configs)                 │
│ - knowledge_modules (procedural markdown)                    │
│                                                               │
│ Frontend (Next.js on Vercel):                                │
│ - Work review UI (work supervision)                          │
│ - Agent dashboards                                           │
│ - Project management                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓ BFF calls (HTTP)
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: SUBSTRATE CORE (substrate-API)                     │
│                                                               │
│ Backend (FastAPI - serves as BFF for Layer 2):              │
│ - blocks (knowledge substrate)                               │
│ - reference_assets (non-text substrate: screenshots, PDFs)  │
│ - work_outputs (agent deliverables - basket-scoped RLS)     │
│ - documents (P4 compositions)                                │
│ - insights (P3 reflections)                                  │
│ - timeline events (activity stream)                          │
│ - proposals (P1 governance pipeline)                         │
│ - semantic layer (embeddings, relationships)                 │
│                                                               │
│ Frontend (Next.js - scaffolding exists, not fully functional)│
│ - Substrate management UI (view blocks, documents)           │
└─────────────────────────────────────────────────────────────┘

                    SEPARATED GOVERNANCE
┌──────────────────────────────┬──────────────────────────────┐
│ Work Supervision             │ Substrate Governance         │
│ (Layer 2: work-platform)     │ (Layer 1: substrate-API)     │
├──────────────────────────────┼──────────────────────────────┤
│ - work_outputs review        │ - P1 proposals pipeline      │
│ - pending_review → approved  │ - Semantic deduplication     │
│ - User reviews agent outputs │ - Quality validation         │
│ - NO auto-substrate update   │ - Block state transitions    │
└──────────────────────────────┴──────────────────────────────┘
```

**Key Points**:
- **NO Layer 3 "Unified Governance"** - Governance is intentionally separated
- **NO shared Layer 4 Presentation** - Each layer has independent frontends
- **Layer 1 serves as BFF** - work-platform calls substrate-API for context/outputs
- **Dual auth support** - Service-to-service + User JWT
- **work_outputs live in Layer 1** - For basket-scoped RLS, but referenced by Layer 2

**See**: [AGENT_SUBSTRATE_ARCHITECTURE.md](./AGENT_SUBSTRATE_ARCHITECTURE.md) for complete implementation details.

---

## 🎯 Key Differentiators (Competitive Moat)

### 1. Separated but Coordinated Review (Current Implementation)

**The Problem**: Traditional systems either have no review workflow OR require confusing double-approval

**YARNNN Current Approach**: Separated governance with clear boundaries
- **Work Supervision**: "Is this agent output good quality?" (work_outputs review)
- **Substrate Governance**: "Should this become permanent memory?" (proposals pipeline)
- **Intentionally separated**: Maintains substrate integrity while allowing work quality review
- **Future bridge**: Approved outputs MAY feed into substrate (deferred, not automatic)

**Result**: Clear separation of concerns, no governance bypass, substrate quality maintained

### 2. Multi-Checkpoint Iterative Supervision

**The Problem**: Binary approve/reject loses nuance
- Agent does 2 hours of work
- User rejects because step 1 was wrong
- Agent must redo everything

**YARNNN Solution**: Checkpoints
- Plan approval: "Is this approach right?"
- Mid-work review: "Course correct before continuing"
- Final approval: "Apply to context"
- Result: Efficient iteration, less wasted work

### 3. Complete Work Provenance

**The Problem**: Agent outputs are black boxes
- "Why did the agent say this?"
- "What context did it use?"
- "Can I trust this?"

**YARNNN Solution**: Full lineage
- Every work output links to work ticket
- `work_outputs.source_context_ids` shows which blocks were used
- `agent_sessions.sdk_session_id` enables conversation history resume
- `work_requests` capture original user intent
- Timeline events capture all agent decisions
- Result: Trust through transparency

### 4. Context-Powered Agent Reasoning

**The Problem**: RAG is not enough
- Simple retrieval misses relationships
- No semantic understanding
- No temporal context
- No narrative composition

**YARNNN Solution**: Substrate + Semantic Layer
- Blocks provide structured knowledge
- Semantic layer discovers relationships
- Timeline provides temporal context
- P4 documents compose narratives
- Result: Agents reason better, produce better work

---

## 📊 What Stays from v3.1

### Substrate Architecture (Layer 1) — Unchanged

**We're not throwing away our foundation.** The substrate model from v3.1 is solid:

- ✅ **Blocks** - Universal substrate (all semantic types)
- ✅ **Raw Dumps** - Immutable capture
- ✅ **Timeline Events** - Activity stream
- ✅ **Semantic Layer** - Embeddings + relationships
- ✅ **Documents (P4)** - Immutable compositions
- ✅ **Insights (P3)** - Reflections and synthesis

**See**: [YARNNN_SUBSTRATE_CANON_V3.md](../../YARNNN_SUBSTRATE_CANON_V3.md) for complete substrate reference.

### Core Principles That Evolved

| v3.1 Principle | v4.0 Evolution |
|----------------|----------------|
| "Capture is Sacred" | → "Work Quality is Sacred" (broader scope) |
| "All Substrates are Peers" | ✅ Unchanged (still true) |
| "Narrative is Deliberate" | ✅ Unchanged (P4 documents still composed) |
| "Agent Intelligence is Mandatory" | → "Context Enables Intelligence" (reframed) |
| "Substrate Management Replaces Document Editing" | → "Supervision Replaces Manual Work" (evolved) |

---

## 🔄 What's New in v4.0 (Phase 1 - In Progress)

### Projects (User-Facing Containers)

**Concept**: User-facing work containers separate from substrate storage.

**Status**: ✅ Implemented (Phase 6, Nov 2025)

**Components**:
- `projects` table - Work containers with 1:1 basket relationship
- Project creation flow - Orchestrates basket + dump + work request creation
- BFF pattern - work-platform orchestrates, substrate-api stores

**Why**: Clear domain separation. Users see "projects", infrastructure uses "baskets".

### Layer 2: Work Orchestration (Schema Only)

**Concept**: Agent work is a first-class entity requiring lifecycle management.

**Status**: ⏸️ Schema created (Phase 1, Nov 2025), governance deferred to Phase 2

**Components Created**:
- `work_sessions` - Track task execution with JSONB parameters
- `work_artifacts` - Agent outputs with review status
- `work_checkpoints` - User review pause points
- RLS policies for workspace isolation

**Components Deferred**:
- `work_iterations` - Feedback loops (not yet implemented)
- `work_context_mutations` - Audit trail (not yet implemented)
- Substrate application logic (disabled Nov 2025)

**Why**: Rapid iteration with clear separation. Substrate integration comes in Phase 2.

### Layer 3: Separated Governance (Current State)

**Concept**: Work governance and substrate governance operate independently.

**Status**: ⚠️ Substrate governance working, work governance not yet defined

**Pattern**: Separated Review (Current)
- **Substrate governance**: P1 proposals → semantic dedup → quality validation → blocks
- **Work governance**: Not yet implemented (deferred to Phase 2)
- **Bridge**: Architecture pending (approved work artifacts → substrate proposals)

**Pattern**: Unified Review (Future Vision - Disabled Nov 2025)
- ~~Single approval handles both work quality and substrate mutation~~
- ~~Blocks created in `ACCEPTED` state (no separate proposal)~~
- Eliminated because it bypassed substrate proposals and semantic deduplication

**Why Separated**: Maintains substrate integrity guarantees while work-platform design matures.

### Agent SDK Integration

**Concept**: Clean integration with external agent execution frameworks.

**Pattern**: Session Linking
- Agent SDK manages execution (Claude conversations, tool use)
- YARNNN manages work lifecycle (outputs, approval, substrate)
- Linked via `agent_sessions.sdk_session_id` (Phase 2e architecture)
- Enables cross-system tracing and debugging

**Why**: In v3.1, agents were internal-only. Now we support external agent frameworks.

### Agent Skills & File Generation

**Concept**: Agents can generate professional deliverables beyond text outputs.

**Capabilities** (via Claude Agent SDK Skills):
- **PDF**: Professional reports, formatted documents
- **XLSX**: Spreadsheets with formulas, data tables
- **DOCX**: Word documents with rich formatting
- **PPTX**: Presentation slides with layouts

**Architecture**:
```
Agent generates file (via Skill)
  ↓ file_id returned
Download from Claude Files API
  ↓ (bytes, metadata)
Upload to Supabase Storage (yarnnn-assets bucket)
  ↓ storage_path
work_outputs table (file_id, file_format, storage_path, skill_metadata)
```

**Implementation** (Phase 2e+):
- `work_outputs.file_id`: Claude Files API reference
- `work_outputs.storage_path`: Supabase Storage location (persistent)
- `work_outputs.generation_method`: `skill` | `code_execution` | `text`
- `work_outputs.skill_metadata`: Provenance tracking

**Storage Pattern**: `baskets/{basket_id}/work_outputs/{work_ticket_id}/{filename}`

**Why File Support**: Agents produce real business deliverables (reports, spreadsheets, presentations), not just text. Users expect downloadable artifacts.

**Reference**: See [`SKILLS_IMPLEMENTATION_GUIDE.md`](./SKILLS_IMPLEMENTATION_GUIDE.md) for technical details.

---

## 🚧 Migration from v3.1

### For Existing Users

**What Changes**:
- Mental model: "Context management" → "Work supervision"
- UI: New work review interface (alongside substrate view)
- Workflow: Create tasks → review work (instead of just managing substrate)

**What Stays**:
- All your substrate data (blocks, documents, timeline)
- Basket structure and workspace memberships
- Authentication and authorization model
- P3/P4 composition system

**Migration Path**:
- v3.1 users can continue substrate management workflows
- v4.0 features are additive, not breaking
- Work management is optional (can use YARNNN as pure context OS)

### For Developers

**What Changes**:
- API: New `/api/work/*` endpoints for work orchestration
- Database: New tables (`work_sessions`, `work_artifacts`, etc.)
- Governance: Unified approval replaces substrate-only governance

**What Stays**:
- Substrate API (`/api/baskets`, `/api/blocks`, etc.)
- RLS policies and workspace isolation
- Timeline event system

**Migration Path**:
- Old APIs remain functional (backward compatible)
- New work orchestration features opt-in
- Agent SDK integration is separate package

---

## 📖 Conceptual Glossary

### Core Concepts

**Work Session**: Agent execution lifecycle (task → artifacts → review → completion)

**Work Artifact**: Agent output awaiting approval (block proposal, document, insight, external file)

**Checkpoint**: Approval point during work session (plan approval, mid-work review, final approval)

**Iteration**: Feedback loop where user requests changes and agent revises

**Context Mutation**: Substrate change resulting from approved work (tracked in audit trail)

**Unified Governance**: Single approval process handling both work quality and substrate integrity

**Substrate**: Layer 1 entities (blocks, documents, insights, timeline) — the knowledge base

**Provenance**: Complete lineage from task → work session → reasoning → artifacts → substrate

### Relationships

```
Work Session (1) → Work Artifacts (N)
Work Session (1) → Checkpoints (N)
Work Session (1) → Iterations (N)
Work Session (1) → Context Mutations (N)

Work Artifact → Block (substrate application)
Work Artifact → Document (substrate application)
Work Artifact → External File (no substrate impact)

Work Session → Agent SDK Session (cross-system tracing)
```

---

## 🎭 Narrative Guidelines (Brand Voice)

### Core Messaging

**Primary**: "Supervise your AI workforce with confidence"

**Secondary**: "Deep context understanding enables better agent work"

**Tertiary**: "One review, dual effect—work quality and knowledge base updates"

### What We Say

✅ "YARNNN supervises AI workers"
✅ "Review work quality, not just outputs"
✅ "Context-powered agent reasoning"
✅ "Single approval for work and knowledge"
✅ "Complete provenance and accountability"

### What We Don't Say

❌ "YARNNN is a vector database" (too narrow)
❌ "YARNNN is agent orchestration" (misses context value)
❌ "YARNNN stores memories" (passive, not platform)
❌ "YARNNN manages context" (v3.1 framing, too limited)

### Audience Framing

**For Developers**: "YARNNN is the missing governance layer between agent frameworks and production."

**For Product Teams**: "YARNNN lets you deploy AI agents with confidence, not fear."

**For Enterprises**: "YARNNN provides the audit trails, quality controls, and accountability required for agent adoption at scale."

---

## 🔮 Future Evolution (Beyond v4.0)

### Near-Term (v4.1-4.3)

- **Agent Track Record**: Trust calibration based on approval history
- **Risk Assessment**: Automated risk scoring for artifacts
- **Context Mutation Limits**: Safety thresholds per agent/session
- **Advanced Checkpoints**: Custom checkpoint strategies per user
- **Workspace Policies**: Per-workspace governance configuration

### Medium-Term (v4.5-5.0)

- **Multi-Agent Collaboration**: Work sessions spanning multiple agents
- **External Approvers**: Delegate work review to team members
- **Integration Marketplace**: Third-party work artifact handlers
- **Agent Marketplace**: Pre-configured agents for common tasks
- **Work Templates**: Reusable task patterns

### Long-Term (v5.0+)

- **Autonomous Work Chains**: Agent-to-agent work delegation
- **Cross-Workspace Context**: Org-level substrate federation
- **External Work Sources**: Ingest work from GitHub, Jira, etc.
- **Predictive Risk Assessment**: ML-based artifact risk scoring
- **Context Intelligence**: Proactive substrate optimization

---

## ✅ Canonical Status

This document is **the single source of truth** for YARNNN's philosophy, identity, and core principles as of v4.0.

**When in doubt**:
- This document defines "what YARNNN is"
- Architecture documents define "how YARNNN works"
- Feature documents define "what YARNNN does"

**Conflicts**:
- If other documents conflict with this canon, **this document wins**
- Report conflicts as documentation bugs to be fixed

**Updates**:
- This document evolves via major version bumps (v4.0 → v5.0)
- Minor clarifications don't require version change
- Breaking philosophy changes require team-wide review

---

## 📎 See Also

### Current Implementation (Priority)
- [AGENT_SUBSTRATE_ARCHITECTURE.md](./AGENT_SUBSTRATE_ARCHITECTURE.md) - **Current source of truth for Phase 1-4 implementation**
- [TERMINOLOGY_GLOSSARY.md](./TERMINOLOGY_GLOSSARY.md) - **Prevents terminology confusion between domains**
- [WORK_OUTPUT_TYPES.md](../features/work-management/WORK_OUTPUT_TYPES.md) - Work output types and handling

### Foundation Documents
- [YARNNN_WORK_PLATFORM_THESIS.md](./YARNNN_WORK_PLATFORM_THESIS.md) - Why context + work integration matters
- [YARNNN_GOVERNANCE_PHILOSOPHY_V4.md](./YARNNN_GOVERNANCE_PHILOSOPHY_V4.md) - Unified governance model
- [YARNNN_USER_MENTAL_MODEL_V4.md](./YARNNN_USER_MENTAL_MODEL_V4.md) - Detailed user journey

### Architecture Documents
- [PHASE_2E_SESSION_ARCHITECTURE.md](./PHASE_2E_SESSION_ARCHITECTURE.md) - Latest architecture (agent sessions, Nov 19)
- [YARNNN_LAYERED_ARCHITECTURE_V4.md](../architecture/YARNNN_LAYERED_ARCHITECTURE_V4.md) - ⚠️ Vision: 4-layer (current: 2-layer)
- [YARNNN_WORK_LAYER.md](../architecture/YARNNN_WORK_LAYER.md) - Layer 2 specification
- [YARNNN_SUBSTRATE_LAYER.md](../architecture/YARNNN_SUBSTRATE_LAYER.md) - Layer 1 specification
- ~~[YARNNN_UNIFIED_GOVERNANCE.md](../architecture/YARNNN_UNIFIED_GOVERNANCE.md)~~ - Deprecated (governance separated)

### Legacy Documents
- [YARNNN_CANON.md](../../YARNNN_CANON.md) - v3.1 canon (superseded)
- [YARNNN_SUBSTRATE_CANON_V3.md](../../YARNNN_SUBSTRATE_CANON_V3.md) - Substrate reference (still valid)

---

## 📝 Document Version History

### v4.1.0 (2025-11-19) - Architecture Correction
**Major corrections to reflect actual implementation:**
- ❌ Removed "4-layer unified model" - Current: 2-layer with BFF pattern
- ❌ Removed "Layer 3 Unified Governance" - Governance is intentionally separated
- ❌ Removed "Layer 4 shared Presentation" - Each layer has independent frontends
- ✅ Added correct architecture: substrate-API (Layer 1) serves as BFF for work-platform (Layer 2)
- ✅ Updated terminology: work_sessions → work_tickets, work_artifacts → work_outputs
- ✅ Clarified governance separation: substrate governance vs work supervision
- ✅ Added Phase 2e architecture: agent_sessions, work_requests, work_tickets
- ✅ Updated provenance: work_outputs.source_context_ids, agent_sessions.sdk_session_id
- ✅ Marked deprecated sections as "Vision" with current implementation notes

**Key Reality Checks:**
- "Unified governance" was v4.0 vision, eliminated Nov 2025 to maintain substrate integrity
- No automatic work output → substrate block absorption (intentionally deferred)
- substrate-API frontend exists but not fully functional
- work-platform frontend is functional
- Layer 1 serves as BFF for Layer 2 (not peer services)

### v4.0.1 (2025-11-15) - Initial Phase 1-4 status
- Added implementation status notes
- Marked governance as separated

### v4.0 (2025-10-31) - Original vision
- 4-layer model described (vision, not implementation)
- Unified governance concept introduced

---

**This is YARNNN v4.1. We are the AI Work Platform.**
