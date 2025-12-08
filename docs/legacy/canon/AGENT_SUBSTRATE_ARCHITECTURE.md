# yarnnn Agent Substrate Architecture
## Comprehensive Design Document

**Version:** 2.0
**Date:** 2025-11-17
**Status:** Phase 1-4 ✅ DEPLOYED | Work Output Lifecycle Complete | Tool-Use Pattern Validated

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement & Strategic Moat](#problem-statement--strategic-moat)
3. [Design Principles](#design-principles)
4. [Substrate Primitives](#substrate-primitives)
5. [Data Model Specifications](#data-model-specifications)
6. [Implementation Phases](#implementation-phases)
7. [Deferred Capabilities](#deferred-capabilities)
8. [Technical Implementation Guide](#technical-implementation-guide)
9. [Appendix: Decision Rationale](#appendix-decision-rationale)

---

## Executive Summary

### Vision
yarnnn is an AI work platform for solo founders where **agents run autonomously**, **context accumulates continuously**, and **knowledge never needs to be repeated**. Unlike ChatGPT or one-off agent tools, yarnnn's differentiation lies in **persistent shared substrate** that grows richer with every agent run.

### Core Architecture Thesis
The current substrate architecture (`raw_dumps → context_blocks`) is necessary but **insufficient** for sophisticated multi-agent work. This document defines the evolution to support:

1. **Reference Assets**: Non-text substrate (screenshots, documents, brand samples) preserving fidelity
2. **Agent Configurations**: Persistent operational parameters (watchlists, tone preferences, schedules)
3. **Execution Modes**: Scheduled/autonomous runs vs. manual requests
4. **Thinking Partner**: Meta-agent for recursion decisions, insights, and user interaction

### Technology Stack Decision
- **Primary Store**: PostgreSQL + pgvector (existing Supabase setup)
- **Blob Storage**: Supabase Storage (S3-backed, region: ap-northeast-2)
- **Future Extensions**: TimescaleDB (if high-frequency time-series needed), Graph DB (if deep provenance needed)
- **Not Migrating To**: Vector-first databases (Pinecone/Weaviate) - insufficient benefit vs. loss of RLS/governance

### Critical Architecture Decision: Database Placement

**Reference Assets location:** substrate-API database (NOT work-platform database)

**Rationale:**
1. **Assets ARE substrate** - Second branch of context (files) alongside blocks (text)
2. **Enterprise B2B enablement** - Standalone substrate service needs file context for "context service with files" product
3. **Service boundary clarity** - substrate-api owns basket-scoped context provisioning (blocks + assets + TP memory)
4. **Consistent access patterns** - work-platform queries both blocks and assets via HTTP (uniform substrate client interface)
5. **Provenance validation** - Same-DB colocation enables local asset existence check for block derivation

**Database Topology:**
- **work-platform DB**: Projects, project_agents, agent_catalog, user-facing tables
- **substrate-API DB**: Baskets, blocks, reference_assets, **work_outputs** (agent deliverables), proposals, substrate_references (all substrate primitives)

> **Note (2025-11-17)**: work_outputs table is in substrate-API for basket-scoped RLS access. work_sessions remains in work-platform DB but references work_outputs via BFF pattern.

---

## Problem Statement & Strategic Moat

### What Solo Founders Don't Want
- ❌ Manually trigger "monitor the market" every day
- ❌ Re-explain brand voice every time they request content
- ❌ Treat agents like chatbots they must constantly prompt
- ❌ Lose context when switching between research, content, and reporting

### What yarnnn Provides (The Moat)

#### 1. **Shared Substrate That Never Drifts**
- All agents (Research, Content, Reporting) query the same basket
- User drops context once → all agents have access
- Context accumulates over time (blocks, assets, work outputs)

#### 2. **Agents That Work Without Constant Prompting**
- Research agent runs **daily autonomous sweeps** (no user action)
- Content agent operates on **scheduled pipelines** (weekly posts)
- Reporting agent is **on-call** for manual requests (board meeting decks)

#### 3. **Context That Gets Richer as Agents Run**
- Week 1: Research agent finds "Competitor has 10 employees"
- Week 2: Research agent detects "Competitor now has 15 employees" → **signals growth**
- Context includes temporal provenance, not just latest snapshots

#### 4. **Governance Makes Approved Work Canonical**
- User reviews work once → becomes part of substrate
- Future agents query past approved outputs
- No re-writing the same context for every run

### Competitive Differentiation

| Capability | ChatGPT | AutoGPT | yarnnn |
|------------|---------|---------|--------|
| Persistent workspace context | ❌ | ⚠️ (vector DB only) | ✅ (governed substrate) |
| Multi-agent coordination | ❌ | ✅ | ✅ (shared basket) |
| Scheduled autonomous execution | ❌ | ❌ | ✅ |
| Governance & review workflow | ❌ | ❌ | ✅ |
| Non-text substrate (screenshots) | ❌ | ❌ | ✅ (reference assets) |
| Temporal provenance tracking | ❌ | ⚠️ (basic) | ✅ (full lineage) |

**Conclusion:** yarnnn's moat is not "better AI" but **better substrate architecture** that enables true autonomous teamwork.

---

## Design Principles

### Principle 1: Substrate Equality
All substrate primitives (blocks, assets, configs) are first-class citizens with:
- RLS policies (workspace-scoped access)
- Audit trails (who created, when, why)
- Lifecycle management (creation, mutation, archival)

### Principle 2: Separation of Concerns
Each substrate primitive has a distinct purpose:

| Primitive | Purpose | Mutability | Storage |
|-----------|---------|------------|---------|
| **Context Blocks** | Propositional knowledge ("X is Y") | Mutable (governance) | PostgreSQL + pgvector |
| **Reference Assets** | Fidelity-preserving inputs (screenshots, docs) | Immutable (append-only) | Blob storage + metadata in SQL |
| **Agent Configs** | Operational parameters (how agents behave) | Mutable (direct update) | JSONB in SQL |
| **Work Outputs** | Agent execution outputs (findings, insights) | Immutable (historical record) | PostgreSQL (substrate-API) |

### Principle 3: Polyglot Persistence (Incremental)
Use the right storage for each data type:
- Text with semantic search → Postgres + pgvector ✅
- Files/blobs → S3/Supabase Storage ✅
- Time-series metrics → TimescaleDB extension (future)
- Deep provenance graphs → Neo4j (future, only if needed)

**Critical:** Don't prematurely optimize. Add storage systems **only when existing stack proves insufficient**.

### Principle 4: Recursion is Governed
Agent outputs feeding back into substrate must:
1. Go through governance flow (proposals, not direct writes)
2. Preserve provenance (what derived from what)
3. Prevent circular reasoning (metadata recursion, not full-text)

**Exception:** Thinking Partner can create raw_dumps from synthesized insights (still governed via P0→P1 pipeline).

### Principle 5: Agent-Centric Architecture
Agents are not ephemeral request handlers. They are **persistent team members** with:
- Identity (project_agents table)
- Configuration (watchlists, tone preferences)
- Execution mode (manual, scheduled, autonomous)
- Memory (access to past work outputs)

---

## Substrate Primitives

### 1. Context Blocks (Existing - Enhanced)

**What They Are:**
Discrete units of propositional knowledge extracted from raw dumps or created through governance.

**Current Schema (No Changes):**
```sql
CREATE TABLE blocks (
  id uuid PRIMARY KEY,
  basket_id uuid REFERENCES baskets(id),
  content text NOT NULL,
  semantic_type text, -- 'fact', 'insight', 'principle', etc.
  state text, -- 'PROPOSED', 'ACCEPTED', 'LOCKED'
  confidence numeric,
  embedding vector(1536), -- pgvector for semantic search
  created_at timestamptz,
  ...
);
```

**Enhancement (Phase 1 Migration Required):**
```sql
-- Add provenance for blocks derived from reference assets:
ALTER TABLE blocks
ADD COLUMN derived_from_asset_id uuid REFERENCES reference_assets(id) ON DELETE SET NULL;

-- Index for provenance queries:
CREATE INDEX idx_blocks_derived_asset ON blocks(derived_from_asset_id)
  WHERE derived_from_asset_id IS NOT NULL;
```

**Query Patterns:**
- Semantic search: `ORDER BY embedding <-> $query_embedding`
- Type filtering: `WHERE semantic_type = 'fact'`
- Governance: `WHERE state = 'ACCEPTED'`

---

### 2. Reference Assets (New)

**What They Are:**
Non-text substrate that preserves fidelity of inputs agents need but can't be reduced to text blocks.

**Examples:**
- Brand voice samples (screenshots of tweets/posts)
- Competitor screenshots (landing pages, pricing)
- Tone reference documents (full PDFs showing desired style)
- Watchlists (JSON files of entities to monitor)
- Report templates (PowerPoint masters, Excel templates)

**Why Separate from Context Blocks:**
1. **Storage location differs**: Files in blob storage, blocks in SQL
2. **Mutability differs**: Assets are immutable (replace, not edit), blocks are mutable
3. **Retrieval differs**: Metadata filtering vs. semantic search
4. **Type system differs**: Functional types (brand_voice_sample) vs. semantic types (fact, insight)
5. **Consumption differs**: File download vs. text prompt inclusion

**Database Location:** substrate-API database (colocated with blocks table)

**Schema:**
```sql
-- Deploy to substrate-API database:
CREATE TABLE reference_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  basket_id uuid NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,

  -- Storage
  storage_path text NOT NULL, -- Supabase Storage: baskets/{basket_id}/assets/{filename}
  file_name text NOT NULL,
  file_size_bytes bigint,
  mime_type text,

  -- Classification
  asset_type text NOT NULL CHECK (asset_type IN (
    'brand_voice_sample',
    'competitor_screenshot',
    'tone_reference_doc',
    'watchlist_json',
    'template_file',
    'data_source',
    'other'
  )),
  asset_category text NOT NULL, -- 'brand_identity', 'competitive_intel', 'template', 'other'

  -- Lifecycle
  permanence text NOT NULL DEFAULT 'permanent' CHECK (permanence IN ('permanent', 'temporary')),
  expires_at timestamptz, -- For temporary assets scoped to specific work
  work_session_id uuid REFERENCES work_sessions(id), -- If scoped to specific work

  -- Agent scoping
  agent_scope text[], -- ['research', 'content', 'thinking_partner']

  -- Semantic metadata
  metadata jsonb DEFAULT '{}',
  tags text[], -- User-defined tags for filtering

  -- Embeddings (for semantic search over descriptions)
  description text, -- User or AI-generated description
  description_embedding vector(1536), -- pgvector

  -- Audit
  created_at timestamptz DEFAULT now() NOT NULL,
  created_by_user_id uuid REFERENCES auth.users(id),
  last_accessed_at timestamptz,
  access_count integer DEFAULT 0,

  -- Constraints
  CONSTRAINT temporary_must_expire CHECK (
    (permanence = 'temporary' AND expires_at IS NOT NULL) OR
    (permanence = 'permanent')
  )
);

-- Indexes
CREATE INDEX idx_ref_assets_basket ON reference_assets(basket_id);
CREATE INDEX idx_ref_assets_scope ON reference_assets USING gin(agent_scope);
CREATE INDEX idx_ref_assets_category ON reference_assets(asset_category);
CREATE INDEX idx_ref_assets_tags ON reference_assets USING gin(tags);
CREATE INDEX idx_ref_assets_embedding ON reference_assets
  USING ivfflat (description_embedding vector_cosine_ops);
```

**RLS Policy:**
```sql
ALTER TABLE reference_assets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access assets in their workspace baskets"
  ON reference_assets FOR ALL
  USING (
    basket_id IN (
      SELECT b.id FROM baskets b
      JOIN workspaces w ON w.id = b.workspace_id
      JOIN workspace_memberships wm ON wm.workspace_id = w.id
      WHERE wm.user_id = auth.uid()
    )
  );
```

**Query Patterns:**
```sql
-- Permanent brand voice samples for Content Agent:
SELECT * FROM reference_assets
WHERE basket_id = $basket_id
  AND 'content' = ANY(agent_scope)
  AND asset_category = 'brand_identity'
  AND permanence = 'permanent'
ORDER BY created_at DESC;

-- Temporary assets for current work session:
SELECT * FROM reference_assets
WHERE work_session_id = $current_work_session;

-- Semantic search over asset descriptions:
SELECT * FROM reference_assets
WHERE basket_id = $basket_id
ORDER BY description_embedding <-> $query_embedding
LIMIT 10;
```

**Lifecycle Management:**
```sql
-- Cron job to delete expired temporary assets:
DELETE FROM reference_assets
WHERE permanence = 'temporary'
  AND expires_at < now();
```

---

### 3. Agent Configurations (New)

**What They Are:**
Persistent operational parameters that define **WHAT** agents do - what they monitor, what rules they follow, what preferences they have.

**The Agent Execution Triad:**

Agents receive three complementary inputs at execution time:

| Input | Purpose | Storage | Example |
|-------|---------|---------|---------|
| **Agent Config** | WHAT to do | `project_agents.config` (JSONB) | Watchlists, alert rules, output preferences |
| **Knowledge Modules** | HOW to do it | `agent_orchestration/knowledge_modules/` (markdown) | Research methodology, quality standards |
| **Reference Assets** | EXAMPLES to learn from | `reference_assets` table + blob storage | Brand voice screenshots, tone samples |

**Why Separate from Context Blocks:**
- Configs are **operational** (how to run), blocks are **informational** (what is known)
- Configs are **agent-specific**, blocks are **shared across agents**
- Configs are **directly mutable**, blocks require governance

**Database Location:** work-platform database (part of project_agents table)

**Schema Enhancement (Phase 1 Migration Required):**
```sql
-- Existing table in work-platform DB:
CREATE TABLE project_agents (
  id uuid PRIMARY KEY,
  project_id uuid REFERENCES projects(id),
  agent_type text REFERENCES agent_catalog(agent_type), -- FK to agent_catalog
  display_name text,
  is_active boolean,
  created_at timestamptz,
  created_by_user_id uuid,
  ...
);

-- Phase 1 Migration - Add config columns:
ALTER TABLE project_agents
ADD COLUMN config jsonb DEFAULT '{}' NOT NULL,
ADD COLUMN config_version integer DEFAULT 1 NOT NULL,
ADD COLUMN last_config_updated_at timestamptz DEFAULT now(),
ADD COLUMN last_config_updated_by uuid REFERENCES auth.users(id);

-- Create index for config queries:
CREATE INDEX idx_project_agents_config ON project_agents USING gin(config);

-- Agent Catalog (dynamic, admin-managed - NO hardcoded enums):
CREATE TABLE IF NOT EXISTS agent_catalog (
  agent_type text PRIMARY KEY,
  display_name text NOT NULL,
  description text,
  icon text,

  -- Dynamic config schema (JSON Schema format for runtime validation)
  config_schema jsonb DEFAULT '{}',

  -- Lifecycle management
  is_active boolean DEFAULT true,
  is_beta boolean DEFAULT false,
  deprecated_at timestamptz,

  -- Schema versioning
  schema_version integer DEFAULT 1,

  -- Admin metadata
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  created_by_user_id uuid,
  notes text
);

CREATE INDEX idx_agent_catalog_active ON agent_catalog(is_active, is_beta);

-- Seed initial agent types (can be updated via admin UI without migration):
INSERT INTO agent_catalog (agent_type, display_name, description, icon, config_schema) VALUES
(
  'research',
  'Research Agent',
  'Monitors markets, competitors, and signals with autonomous sweeps.',
  'Brain',
  '{
    "type": "object",
    "properties": {
      "watchlist": {
        "type": "object",
        "properties": {
          "competitors": {"type": "array", "items": {"type": "string"}},
          "topics": {"type": "array", "items": {"type": "string"}},
          "data_sources": {"type": "array"}
        }
      },
      "alert_rules": {"type": "object"},
      "output_preferences": {"type": "object"}
    }
  }'::jsonb
),
(
  'content',
  'Content Agent',
  'Plans and drafts recurring content across channels.',
  'PenSquare',
  '{
    "type": "object",
    "properties": {
      "brand_voice": {"type": "object"},
      "platforms": {"type": "object"},
      "content_rules": {"type": "object"}
    }
  }'::jsonb
),
(
  'reporting',
  'Reporting Agent',
  'Transforms context and work history into structured reports.',
  'BarChart3',
  '{
    "type": "object",
    "properties": {
      "report_preferences": {"type": "object"},
      "data_sources": {"type": "object"},
      "formatting": {"type": "object"}
    }
  }'::jsonb
)
ON CONFLICT (agent_type) DO NOTHING;

-- Optional: Config audit trail
CREATE TABLE agent_config_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_agent_id uuid NOT NULL REFERENCES project_agents(id) ON DELETE CASCADE,
  config_snapshot jsonb NOT NULL,
  config_version integer NOT NULL,
  changed_by_user_id uuid REFERENCES auth.users(id),
  changed_at timestamptz DEFAULT now() NOT NULL,
  change_reason text
);
```

**Config Schemas by Agent Type:**

#### Research Agent Config
```typescript
interface ResearchAgentConfig {
  watchlist: {
    competitors: string[]; // ["CompanyA", "CompanyB"]
    topics: string[]; // ["AI agents", "knowledge management"]
    data_sources: {
      url: string;
      source_type: 'rss' | 'api' | 'website';
      check_frequency: 'hourly' | 'daily' | 'weekly';
    }[];
  };
  alert_rules: {
    funding_threshold_usd?: number; // Alert if competitor raises > $X
    headcount_change_percent?: number; // Alert if headcount changes > X%
    news_sentiment_threshold?: number; // -1 to 1
    keywords_trigger?: string[]; // Alert if these keywords appear
  };
  output_preferences: {
    format: 'structured_blocks' | 'narrative_report' | 'both';
    max_findings_per_run: number;
    include_analysis: boolean; // Or just facts
  };
}
```

#### Content Agent Config
```typescript
interface ContentAgentConfig {
  brand_voice: {
    tone: string; // "casual but authoritative"
    avoid_topics: string[]; // ["politics", "religion"]
    reference_asset_ids: string[]; // Links to brand voice samples
    style_notes: string; // Free-text guidance
  };
  platforms: {
    twitter: {
      max_length: number;
      use_threads: boolean;
      max_hashtags: number;
      avoid_emojis: boolean;
    };
    linkedin: {
      max_length: number;
      use_hashtags: boolean;
      include_media: boolean;
    };
  };
  content_rules: {
    always_include_cta: boolean;
    always_cite_sources: boolean;
    max_drafts_per_request: number;
  };
}
```

#### Reporting Agent Config
```typescript
interface ReportingAgentConfig {
  report_preferences: {
    default_format: 'ppt' | 'pdf' | 'excel' | 'markdown';
    template_asset_id?: string; // Links to template file in reference_assets
    sections: string[]; // ["Overview", "Key Metrics", "Recommendations"]
    stakeholder_level: 'executive' | 'manager' | 'analyst';
  };
  data_sources: {
    include_timeline_events: boolean;
    include_work_sessions: boolean;
    include_context_blocks: boolean;
    time_window_days: number; // Default lookback period
  };
  formatting: {
    chart_style: 'minimal' | 'detailed';
    include_appendix: boolean;
    page_limit?: number;
  };
}
```

---

### 4. Agent Knowledge Modules (New - Phase 2d)

**What They Are:**
Procedural knowledge modules that teach agents **HOW** to work. These are markdown files containing methodology, standards, and patterns that augment agent system prompts at execution time.

**Why Separate from Agent Config:**
- Knowledge modules are **procedural** (methodology, processes), configs are **declarative** (settings, preferences)
- Knowledge modules are **reusable** (shared across agent instances), configs are **instance-specific**
- Knowledge modules are **version-controlled** (in git), configs are **database-persisted**

**Storage Location:** work-platform codebase (`src/agent_orchestration/knowledge_modules/`)

**File Structure:**
```
work-platform/api/src/agent_orchestration/knowledge_modules/
├── research_methodology.md      # Research agent: 5-step research process
├── quality_standards.md         # All agents: Confidence scoring, evidence requirements
├── substrate_patterns.md        # All agents: Tool usage, provenance tracking
├── content_creation_guide.md    # Content agent: Platform-specific guidelines
└── report_formatting_guide.md   # Reporting agent: Report structure, formatting
```

**Module Naming Convention:**
```
{domain}_{module_name}.md

Examples:
- research_methodology.md (agent-specific)
- quality_standards.md (cross-agent)
- substrate_patterns.md (cross-agent)
```

**Loading Pattern:**
```python
# Orchestration layer loads modules for agent
from agent_orchestration.knowledge_modules import KnowledgeModuleLoader

loader = KnowledgeModuleLoader()
knowledge = loader.load_for_agent(agent_type="research")

# Agent receives knowledge via payload
agent = ResearchAgentSDK(
    basket_id=basket_id,
    workspace_id=workspace_id,
    knowledge_modules=knowledge,  # Augments system prompt
    agent_config=project_agent.config,  # Runtime settings
)
```

**Relationship to Official Claude SDK Skills:**

**Current State**: We use static prompt templates (knowledge modules)
- ❌ NOT official Claude SDK Skills (which require `Skill` tool + `setting_sources`)
- ✅ Prompt-level procedural knowledge injection
- ✅ Works well for our BFF pattern

**Future State** (if needed): Could add official Skills support to yarnnn_agents
- Knowledge modules would coexist with Skills
- Knowledge = static prompt augmentation
- Skills = autonomous tool invocation

**Key Insight**: Knowledge modules are the **"agent config receiving side"** - they complement `agent_config` (user's settings) with procedural knowledge (how to apply those settings).

---

### 5. Execution Modes (New - Phase 2)

**What They Enable:**
Differentiation between autonomous/scheduled agents (Research, Content) vs. on-demand agents (Reporting).

**Database Location:** work-platform database (extends project_agents and work_sessions)

**Schema Cleanup (Phase 1 - Before Adding Execution Modes):**
```sql
-- Remove redundant column from work_sessions:
-- (executed_by_agent_id is legacy string; project_agent_id is the proper FK)
ALTER TABLE work_sessions
DROP COLUMN IF EXISTS executed_by_agent_id;
```

**Schema Enhancement (Phase 2):**
```sql
-- Add execution mode to project_agents:
ALTER TABLE project_agents
ADD COLUMN execution_mode text DEFAULT 'manual'
  CHECK (execution_mode IN ('manual', 'scheduled', 'autonomous')),
ADD COLUMN schedule_config jsonb DEFAULT '{}';

-- Example schedule_config:
{
  "enabled": true,
  "frequency": "daily", // 'hourly', 'daily', 'weekly', 'monthly'
  "time_of_day": "06:00",
  "timezone": "America/New_York",
  "days_of_week": [1, 2, 3, 4, 5], // Mon-Fri
  "task_template": {
    "task_intent": "Daily market monitoring sweep",
    "config_override": {} // Override agent config for scheduled runs
  }
}

-- Add execution trigger to work_sessions:
ALTER TABLE work_sessions
ADD COLUMN execution_trigger text DEFAULT 'manual'
  CHECK (execution_trigger IN ('manual', 'scheduled', 'autonomous', 'cascade'));
```

**Scheduler Service (Future Implementation):**
```typescript
// Cron job runs every hour:
const dueAgents = await supabase
  .from('project_agents')
  .select('*')
  .eq('execution_mode', 'scheduled')
  .lte('schedule_config->next_run_at', new Date().toISOString());

for (const agent of dueAgents) {
  await triggerWorkSession({
    project_agent_id: agent.id,
    task_intent: agent.schedule_config.task_template.task_intent,
    execution_trigger: 'scheduled',
  });

  // Update next_run_at:
  await updateNextRun(agent);
}
```

---

### 5. Thinking Partner (New - Phase 3)

**What It Is:**
A meta-agent that orchestrates other agents, provides insights to users, makes recursion decisions, and manages system-level intelligence.

**Capabilities:**
1. **Chat Interface**: User asks questions, TP queries all substrate + work history
2. **Pattern Recognition**: "I notice you reject emoji-heavy posts"
3. **Recursion Judgment**: "Should this report insight become a context block?"
4. **Trigger Work**: "Run a competitor analysis for me"
5. **Systemic Updates**: "Update Research agent's watchlist to include Competitor X"
6. **Synthesize Insights**: Create raw_dumps from derived intelligence

**Database Location:** substrate-API database (memory and chats colocated with substrate)

**Rationale for substrate-API Placement:**
- Thinking Partner memory IS substrate (meta-intelligence layer)
- Enables direct queries alongside blocks and assets (no cross-DB joins)
- Chat history needs access to all substrate primitives
- Agent execution context requires TP memory without BFF round-trip

**Schema (Deploy to substrate-API Database):**
```sql
-- Thinking Partner Memory (substrate-API DB):
CREATE TABLE thinking_partner_memory (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  basket_id uuid NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,

  -- Memory type
  memory_type text NOT NULL CHECK (memory_type IN (
    'user_preference', -- "User prefers threads over single tweets"
    'pattern', -- "Engagement is 3x higher on data-driven posts"
    'insight', -- "Competitor A is scaling aggressively"
    'recommendation' -- "Should add Competitor X to watchlist"
  )),

  -- Content
  content jsonb NOT NULL,
  -- Example: {
  --   "pattern": "User rejects emoji posts",
  --   "confidence": 0.85,
  --   "evidence": ["work_session_id_1", "work_session_id_2"],
  --   "sample_size": 15
  -- }

  -- Provenance
  derived_from_sessions uuid[], -- Work sessions this insight came from
  derived_from_chat uuid, -- If from chat interaction (references chat_messages table)

  -- Lifecycle
  created_at timestamptz DEFAULT now(),
  expires_at timestamptz, -- Some insights are ephemeral
  confidence numeric CHECK (confidence BETWEEN 0 AND 1),

  -- User feedback
  user_validated boolean DEFAULT null, -- User confirmed or rejected
  validated_at timestamptz
);

CREATE INDEX idx_tp_memory_basket ON thinking_partner_memory(basket_id);
CREATE INDEX idx_tp_memory_type ON thinking_partner_memory(memory_type);
CREATE INDEX idx_tp_memory_confidence ON thinking_partner_memory(confidence DESC);

-- Chat History (substrate-API DB):
CREATE TABLE thinking_partner_chats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  basket_id uuid NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id),

  -- Chat thread
  thread_id uuid DEFAULT gen_random_uuid(),

  -- Message
  role text NOT NULL CHECK (role IN ('user', 'assistant')),
  content text NOT NULL,

  -- Context used (for citations)
  context_blocks_queried uuid[],
  reference_assets_queried uuid[],
  work_sessions_queried uuid[],

  -- Timestamps
  created_at timestamptz DEFAULT now()
);

CREATE INDEX idx_tp_chats_basket ON thinking_partner_chats(basket_id);
CREATE INDEX idx_tp_chats_thread ON thinking_partner_chats(thread_id, created_at);
```

**Thinking Partner as Project Agent:**
```sql
-- Auto-provision Thinking Partner for all projects:
INSERT INTO project_agents (project_id, agent_type, display_name, is_active)
SELECT
  p.id as project_id,
  'thinking_partner' as agent_type,
  'Thinking Partner' as display_name,
  true as is_active
FROM projects p
ON CONFLICT (project_id, agent_type) DO NOTHING;
```

---

## Data Model Specifications

### Complete Entity Relationship Diagram

```
Workspaces
  ↓ 1:N
Projects
  ↓ 1:1
Baskets (context container)
  ├─ 1:N → Context Blocks (text substrate)
  ├─ 1:N → Reference Assets (file substrate)
  └─ 1:N → Thinking Partner Memory (meta-intelligence)

Projects
  ↓ 1:N
Project Agents (Research, Content, Reporting, Thinking Partner)
  ├─ config (JSONB) → Agent Configurations
  ├─ schedule_config (JSONB) → Execution Modes
  └─ 1:N → Work Sessions
         ├─ execution_trigger (manual, scheduled, autonomous)
         └─ 1:N → Work Artifacts (outputs)

Reference Assets
  ↓ N:1
Work Sessions (for temporary assets)

Context Blocks
  ↓ N:1
Reference Assets (derived_from_asset_id for provenance)

Thinking Partner Memory
  ↓ N:N
Work Sessions (derived_from_sessions for provenance)
```

### Table Size Estimates (Year 1 - 100 Active Projects)

| Table | Row Count | Growth Rate | Storage |
|-------|-----------|-------------|---------|
| `blocks` | ~500K | +10K/week | ~500MB (text + embeddings) |
| `reference_assets` | ~5K | +100/week | Metadata: ~5MB, Blobs: ~50GB |
| `project_agents` | ~400 | +4/project | <1MB |
| `work_sessions` | ~50K | +1K/week | ~50MB |
| `work_artifacts` | ~100K | +2K/week | ~100MB |
| `thinking_partner_memory` | ~10K | +200/week | ~10MB |
| `thinking_partner_chats` | ~100K | +2K/week | ~50MB |

**Total SQL:** ~1GB (well within Postgres limits)
**Total Blob Storage:** ~50GB (S3/Supabase Storage)

### Key Relationships & Foreign Keys

```sql
-- Context Blocks provenance:
ALTER TABLE blocks
ADD CONSTRAINT fk_blocks_derived_asset
  FOREIGN KEY (derived_from_asset_id) REFERENCES reference_assets(id) ON DELETE SET NULL;

-- Reference Assets scoping:
ALTER TABLE reference_assets
ADD CONSTRAINT fk_ref_assets_work_session
  FOREIGN KEY (work_session_id) REFERENCES work_sessions(id) ON DELETE CASCADE;

-- Agent linkage:
ALTER TABLE work_sessions
ADD CONSTRAINT fk_work_sessions_agent
  FOREIGN KEY (project_agent_id) REFERENCES project_agents(id) ON DELETE SET NULL;

-- Thinking Partner memory provenance:
ALTER TABLE thinking_partner_memory
ADD CONSTRAINT fk_tp_memory_basket
  FOREIGN KEY (basket_id) REFERENCES baskets(id) ON DELETE CASCADE;
```

---

## Implementation Phases

### Phase 1: Storage Foundation (P0-P1) ✅ **DEPLOYED**

**Status:** Backend infrastructure deployed to Render | Frontend BFF deployed to Vercel
**Deployed:** 2025-11-13
**Next:** Testing & Refinement

**Goal:** Enable agents to access non-text substrate and persistent configurations.

**Prerequisites:** Schema stress test completed (ARCHITECTURE_STRESS_TEST.md) - all conflicts resolved.

**Deliverables:**

1. **Database Migrations:**

   **Migration 1: work-platform DB (project_agents enhancement + cleanup)**
   ```sql
   -- File: /supabase/migrations/YYYYMMDD_phase1_agent_configs.sql

   -- 1. Create agent_catalog table (dynamic, admin-managed):
   CREATE TABLE IF NOT EXISTS agent_catalog (
     agent_type text PRIMARY KEY,
     display_name text NOT NULL,
     description text,
     icon text,
     config_schema jsonb DEFAULT '{}',
     is_active boolean DEFAULT true,
     is_beta boolean DEFAULT false,
     deprecated_at timestamptz,
     schema_version integer DEFAULT 1,
     created_at timestamptz DEFAULT now(),
     updated_at timestamptz DEFAULT now(),
     created_by_user_id uuid,
     notes text
   );

   CREATE INDEX idx_agent_catalog_active ON agent_catalog(is_active, is_beta);

   -- Seed initial agent types (can be updated via admin UI without migration):
   INSERT INTO agent_catalog (agent_type, display_name, description, icon, config_schema) VALUES
   (
     'research',
     'Research Agent',
     'Monitors markets, competitors, and signals with autonomous sweeps.',
     'Brain',
     '{
       "type": "object",
       "properties": {
         "watchlist": {"type": "object"},
         "alert_rules": {"type": "object"},
         "output_preferences": {"type": "object"}
       }
     }'::jsonb
   ),
   (
     'content',
     'Content Agent',
     'Plans and drafts recurring content across channels.',
     'PenSquare',
     '{
       "type": "object",
       "properties": {
         "brand_voice": {"type": "object"},
         "platforms": {"type": "object"},
         "content_rules": {"type": "object"}
       }
     }'::jsonb
   ),
   (
     'reporting',
     'Reporting Agent',
     'Transforms context and work history into structured reports.',
     'BarChart3',
     '{
       "type": "object",
       "properties": {
         "report_preferences": {"type": "object"},
         "data_sources": {"type": "object"},
         "formatting": {"type": "object"}
       }
     }'::jsonb
   )
   ON CONFLICT (agent_type) DO NOTHING;

   -- 2. Add config columns to project_agents:
   ALTER TABLE project_agents
   ADD COLUMN IF NOT EXISTS config jsonb DEFAULT '{}' NOT NULL,
   ADD COLUMN IF NOT EXISTS config_version integer DEFAULT 1 NOT NULL,
   ADD COLUMN IF NOT EXISTS last_config_updated_at timestamptz DEFAULT now(),
   ADD COLUMN IF NOT EXISTS last_config_updated_by uuid REFERENCES auth.users(id);

   -- Create index for config queries:
   CREATE INDEX IF NOT EXISTS idx_project_agents_config
     ON project_agents USING gin(config);

   -- 3. Create config audit trail:
   CREATE TABLE IF NOT EXISTS agent_config_history (
     id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
     project_agent_id uuid NOT NULL REFERENCES project_agents(id) ON DELETE CASCADE,
     config_snapshot jsonb NOT NULL,
     config_version integer NOT NULL,
     changed_by_user_id uuid REFERENCES auth.users(id),
     changed_at timestamptz DEFAULT now() NOT NULL,
     change_reason text
   );

   CREATE INDEX IF NOT EXISTS idx_agent_config_history_agent
     ON agent_config_history(project_agent_id, changed_at DESC);

   -- 4. Remove redundant column from work_sessions:
   -- (executed_by_agent_id is legacy; project_agent_id is proper FK)
   ALTER TABLE work_sessions
   DROP COLUMN IF EXISTS executed_by_agent_id;
   ```

   **Migration 2: substrate-API DB (reference_assets + blocks enhancement)**
   ```sql
   -- File: /substrate-api/migrations/YYYYMMDD_phase1_reference_assets.sql

   -- 1. Create asset_type_catalog (dynamic, admin-managed):
   CREATE TABLE IF NOT EXISTS asset_type_catalog (
     asset_type text PRIMARY KEY,
     display_name text NOT NULL,
     description text,
     category text,
     allowed_mime_types text[],
     is_active boolean DEFAULT true,
     deprecated_at timestamptz,
     created_at timestamptz DEFAULT now(),
     notes text
   );

   CREATE INDEX idx_asset_type_catalog_active ON asset_type_catalog(is_active);
   CREATE INDEX idx_asset_type_catalog_category ON asset_type_catalog(category);

   -- Seed initial asset types (can be updated via admin UI without migration):
   INSERT INTO asset_type_catalog (asset_type, display_name, category, allowed_mime_types) VALUES
     ('brand_voice_sample', 'Brand Voice Sample', 'brand_identity', ARRAY['image/*', 'application/pdf']),
     ('competitor_screenshot', 'Competitor Screenshot', 'competitive_intel', ARRAY['image/*']),
     ('tone_reference_doc', 'Tone Reference Document', 'brand_identity', ARRAY['application/pdf', 'text/*']),
     ('watchlist_json', 'Watchlist JSON', 'configuration', ARRAY['application/json']),
     ('template_file', 'Template File', 'template', ARRAY['application/*']),
     ('data_source', 'Data Source', 'integration', ARRAY['*/*']),
     ('other', 'Other', 'uncategorized', ARRAY['*/*'])
   ON CONFLICT (asset_type) DO NOTHING;

   -- 2. Create reference_assets table:
   CREATE TABLE reference_assets (
     id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
     basket_id uuid NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,

     -- Storage
     storage_path text NOT NULL,
     file_name text NOT NULL,
     file_size_bytes bigint,
     mime_type text,

     -- Classification (validated via FK to catalog, not hardcoded enum)
     asset_type text NOT NULL REFERENCES asset_type_catalog(asset_type),
     asset_category text NOT NULL,

     -- Lifecycle
     permanence text NOT NULL DEFAULT 'permanent' CHECK (permanence IN ('permanent', 'temporary')),
     expires_at timestamptz,
     work_session_id uuid, -- Note: Cross-DB FK not enforced, handled in app code

     -- Agent scoping
     agent_scope text[],

     -- Semantic metadata
     metadata jsonb DEFAULT '{}',
     tags text[],
     description text,
     description_embedding vector(1536),

     -- Audit
     created_at timestamptz DEFAULT now() NOT NULL,
     created_by_user_id uuid REFERENCES auth.users(id),
     last_accessed_at timestamptz,
     access_count integer DEFAULT 0,

     -- Constraints
     CONSTRAINT temporary_must_expire CHECK (
       (permanence = 'temporary' AND expires_at IS NOT NULL) OR
       (permanence = 'permanent')
     )
   );

   -- Indexes:
   CREATE INDEX idx_ref_assets_basket ON reference_assets(basket_id);
   CREATE INDEX idx_ref_assets_type ON reference_assets(asset_type);
   CREATE INDEX idx_ref_assets_scope ON reference_assets USING gin(agent_scope);
   CREATE INDEX idx_ref_assets_category ON reference_assets(asset_category);
   CREATE INDEX idx_ref_assets_tags ON reference_assets USING gin(tags);
   CREATE INDEX idx_ref_assets_embedding ON reference_assets
     USING ivfflat (description_embedding vector_cosine_ops)
     WITH (lists = 100); -- Tune based on dataset size

   -- RLS:
   ALTER TABLE reference_assets ENABLE ROW LEVEL SECURITY;

   CREATE POLICY "Users can access assets in their workspace baskets"
     ON reference_assets FOR ALL
     USING (
       basket_id IN (
         SELECT b.id FROM baskets b
         JOIN workspaces w ON w.id = b.workspace_id
         JOIN workspace_memberships wm ON wm.workspace_id = w.id
         WHERE wm.user_id = auth.uid()
       )
     );

   -- 2. Add provenance column to blocks:
   ALTER TABLE blocks
   ADD COLUMN IF NOT EXISTS derived_from_asset_id uuid REFERENCES reference_assets(id) ON DELETE SET NULL;

   CREATE INDEX IF NOT EXISTS idx_blocks_derived_asset
     ON blocks(derived_from_asset_id)
     WHERE derived_from_asset_id IS NOT NULL;
   ```

2. **Supabase Storage Setup:**

   **Storage Bucket Configuration:**
   ```sql
   -- Run in Supabase Dashboard → Storage
   -- Bucket: yarnnn-assets
   -- Public: false
   -- File size limit: 50MB
   -- Allowed MIME types: image/*, application/pdf, application/json, text/*
   ```

   **Storage RLS Policies:**
   ```sql
   -- Policy: Users can upload to their workspace baskets
   CREATE POLICY "Users can upload assets to their baskets"
   ON storage.objects FOR INSERT
   WITH CHECK (
     bucket_id = 'yarnnn-assets'
     AND (storage.foldername(name))[1] = 'baskets'
     AND (storage.foldername(name))[2]::uuid IN (
       SELECT b.id FROM baskets b
       JOIN workspaces w ON w.id = b.workspace_id
       JOIN workspace_memberships wm ON wm.workspace_id = w.id
       WHERE wm.user_id = auth.uid()
     )
   );

   -- Policy: Users can read assets from their baskets
   CREATE POLICY "Users can read assets from their baskets"
   ON storage.objects FOR SELECT
   USING (
     bucket_id = 'yarnnn-assets'
     AND (storage.foldername(name))[1] = 'baskets'
     AND (storage.foldername(name))[2]::uuid IN (
       SELECT b.id FROM baskets b
       JOIN workspaces w ON w.id = b.workspace_id
       JOIN workspace_memberships wm ON wm.workspace_id = w.id
       WHERE wm.user_id = auth.uid()
     )
   );

   -- Policy: Users can delete assets from their baskets
   CREATE POLICY "Users can delete assets from their baskets"
   ON storage.objects FOR DELETE
   USING (
     bucket_id = 'yarnnn-assets'
     AND (storage.foldername(name))[1] = 'baskets'
     AND (storage.foldername(name))[2]::uuid IN (
       SELECT b.id FROM baskets b
       JOIN workspaces w ON w.id = b.workspace_id
       JOIN workspace_memberships wm ON wm.workspace_id = w.id
       WHERE wm.user_id = auth.uid()
     )
   );
   ```

   **Implementation Notes:**
   - Storage path format: `baskets/{basket_id}/assets/{asset_id}/{filename}`
   - Region: ap-northeast-2 (matches Supabase setup)
   - Access keys: Generated via Supabase Dashboard → Project Settings → API

3. **substrate-API Endpoints (New - Required):**

   **Critical:** substrate-API must implement file upload endpoints since reference_assets table lives in substrate-API DB.

   ```
   POST   /substrate/baskets/{basketId}/assets           - Upload reference asset
   GET    /substrate/baskets/{basketId}/assets           - List assets (with filters)
   GET    /substrate/baskets/{basketId}/assets/{assetId} - Get asset metadata
   DELETE /substrate/baskets/{basketId}/assets/{assetId} - Delete asset
   POST   /substrate/baskets/{basketId}/assets/{assetId}/signed-url - Get signed download URL
   ```

   **Implementation Notes:**
   - substrate-API handles both SQL metadata AND blob storage operations
   - Uses Supabase Storage client with service role key
   - Enforces workspace-scoped access via RLS
   - Returns signed URLs for secure file downloads

4. **work-platform BFF Routes (Proxies to substrate-API):**
   ```
   POST   /api/baskets/{basketId}/assets           - Proxy to substrate-API
   GET    /api/baskets/{basketId}/assets           - Proxy to substrate-API
   GET    /api/baskets/{basketId}/assets/{assetId} - Proxy to substrate-API
   DELETE /api/baskets/{basketId}/assets/{assetId} - Proxy to substrate-API

   GET    /api/projects/{projectId}/agents/{agentId}/config - Get agent config (work-platform DB)
   PUT    /api/projects/{projectId}/agents/{agentId}/config - Update agent config (work-platform DB)
   ```

5. **UI Components:**
   - ✅ Context page: "Assets" tab with upload interface
   - ✅ Asset type selector (brand voice, screenshot, etc.)
   - ✅ Agent scope selector (which agents can use this asset)
   - ✅ Asset preview/thumbnail display
   - ✅ Agent dashboards: Config forms per agent type
     - Research: Watchlist, data sources, alert rules
     - Content: Brand voice, platform specs, tone preferences
     - Reporting: Template selector, report preferences

6. **Agent Execution Enhancement:**
   ```typescript
   // When agent runs, payload includes:
   interface AgentExecutionPayload {
     context_blocks: Block[];
     reference_assets: Asset[]; // NEW
     agent_config: AgentConfig; // NEW
   }
   ```

**Success Criteria:**
- ✅ Migrations run successfully on both DBs (work-platform & substrate-API)
- ✅ Supabase Storage bucket created with correct RLS policies
- ✅ substrate-API file upload endpoints deployed to Render
- ✅ work-platform BFF routes deployed to Vercel
- ✅ Context page Assets tab UI deployed
- ✅ Agent Config forms UI deployed
- 🔄 **IN TESTING:** User can upload brand voice screenshot via UI
- 🔄 **IN TESTING:** User can configure agent settings via Config forms
- ⏳ **PENDING (Phase 3):** Content Agent receives screenshot in execution payload
- ⏳ **PENDING (Phase 3):** Agent config persists across work sessions

**Deployment Validation:**
- ✅ reference_assets table exists in substrate-API DB
- ✅ asset_type_catalog table exists in substrate-API DB with initial seed data
- ✅ blocks.derived_from_asset_id column exists
- ✅ project_agents.config column exists in work-platform DB
- ✅ agent_catalog table exists in work-platform DB with dynamic schema support
- ✅ agent_catalog seeded with 3 agent types (research, content, reporting)
- ✅ work_sessions.executed_by_agent_id column removed
- ✅ RLS policies enforce workspace-scoping for assets
- ✅ Cross-DB work_session_id reference handled in app code (not FK)
- ✅ No hardcoded CHECK constraints on agent_type or asset_type (FK to catalogs instead)
- ✅ substrate-API: Deployed to Render (commit 91314c3f)
- ✅ work-platform: Deployed to Vercel (commit 68265d22)

---

### Phase 4: Work Output Lifecycle (NEW - 2025-11-17) ✅ **DEPLOYED**

**Status:** Backend infrastructure deployed | Tool-use pattern validated | BFF integration complete
**Deployed:** 2025-11-17
**Note:** Phase 4 completes the agent output supervision loop before execution modes.

**Goal:** Complete work supervision lifecycle with structured agent outputs.

**Key Deliverables:**

1. **Tool-Use Pattern (emit_work_output)**:
   ```python
   # Agents emit structured outputs via Claude tool-use
   emit_work_output_tool = {
       "name": "emit_work_output",
       "input_schema": {
           "properties": {
               "output_type": {"enum": ["finding", "recommendation", "insight", "draft_content"]},
               "title": {"type": "string"},
               "body": {"type": "object"},  # summary, details, evidence, recommendations
               "confidence": {"type": "number"},
               "source_block_ids": {"type": "array"}  # Provenance
           }
       }
   }
   ```

2. **Work Outputs Table (substrate-API)**:
   - Lives in substrate-API for basket-scoped RLS
   - supervision_status: pending_review → approved/rejected/revision_requested
   - Provenance: source_context_ids links to source blocks
   - Cross-DB reference: work_session_id (no FK, validated in app code)

3. **BFF Pattern Enforcement**:
   - work-platform orchestrates agent execution
   - substrate-API owns work_outputs table
   - Dual auth: Service-to-service + User JWT supported
   - Service auth bypasses workspace membership check (trusted)

4. **Agent Orchestration Flow**:
   ```python
   # work-platform/api/src/app/routes/agent_orchestration.py
   async def execute_agent_work():
       work_session_id = await _create_work_session(...)  # Track execution
       result = await _run_research_agent(request, user_id, work_session_id)
       work_outputs = result.get("work_outputs", [])  # Parsed from tool_use blocks
       await write_agent_outputs(basket_id, work_session_id, outputs)  # BFF to substrate-API
   ```

5. **Supervision Endpoints** (substrate-API):
   - `POST /baskets/{id}/outputs` - Write outputs (service auth)
   - `GET /baskets/{id}/outputs` - List pending review
   - `PUT /baskets/{id}/outputs/{id}/status` - Approve/reject

**Validation Results:**
- ✅ Tool-use pattern tested with real Claude API
- ✅ 3 structured outputs with provenance tracking
- ✅ Dual auth working (service + user)
- ✅ RLS policies enforce basket-scoped access

**Current Scope:**
- Work outputs are supervised (user reviews)
- Approved outputs do NOT automatically become blocks (intentionally deferred)
- Future: block_proposal type for direct substrate absorption

---

### Phase 2: Execution Modes & Scheduling (FUTURE)

**Status:** Not started
**Priority:** Next after frontend work management UI

**Goal:** Enable scheduled/autonomous agent runs (the real moat).

**Deliverables:**

1. **Database Schema:**
   - [ ] Add `execution_mode` + `schedule_config` to `project_agents`
   - [ ] Add `execution_trigger` to `work_sessions`

2. **Scheduler Service:**
   - [ ] Background job (cron) that checks for due scheduled runs
   - [ ] Triggers work sessions via platform-API
   - [ ] Updates `next_run_at` after execution

3. **UI Components:**
   - [ ] Agent dashboard: Schedule configuration UI
     - Frequency selector (daily, weekly, etc.)
     - Time picker
     - Timezone selector
     - Enable/disable toggle
   - [ ] Work sessions list: Badge showing execution trigger
     - 🔁 Scheduled
     - 👆 Manual
     - 🤖 Autonomous

4. **Work Metadata Recursion:**
   ```typescript
   // Agent receives lightweight metadata from previous runs:
   interface AgentExecutionPayload {
     context_blocks: Block[];
     reference_assets: Asset[];
     agent_config: AgentConfig;
     previous_run_metadata: { // NEW
       last_5_runs: [
         {
           date: string,
           task: string,
           findings_count: number,
           entities_analyzed: string[]
         },
         ...
       ]
     };
   }
   ```

5. **Content Agent Exception:**
   ```typescript
   // Content Agent ALSO receives approved posts for style consistency:
   interface ContentAgentPayload extends AgentExecutionPayload {
     approved_posts: [ // NEW
       {content: string, platform: string, created_at: string},
       ... // Last 3 approved
     ];
   }
   ```

**Success Criteria:**
- [ ] User can schedule Research agent to run daily at 6am
- [ ] Scheduled run executes without user intervention
- [ ] Work sessions list shows "Scheduled" badge
- [ ] Research agent Week 2 knows what it analyzed Week 1 (metadata)
- [ ] Content agent maintains style consistency across runs

---

### Phase 3: Thinking Partner (FUTURE)

**Status:** Not started
**Priority:** After execution modes

**Goal:** Meta-agent for insights, recursion decisions, and chat interface.

**Deliverables:**

1. **Database Schema:**
   - [ ] Create `thinking_partner_memory` table
   - [ ] Create `thinking_partner_chats` table
   - [ ] Auto-provision Thinking Partner agent for all projects

2. **Chat Interface:**
   - [ ] Chat UI component (sidebar or dedicated page)
   - [ ] Message history display
   - [ ] Citation rendering (links to context blocks, assets, work sessions)

3. **Thinking Partner Capabilities:**
   - [ ] **Phase 3.1 (Chat + Insights):**
     - User asks questions
     - TP queries context blocks, assets, work sessions
     - TP answers with citations
   - [ ] **Phase 3.2 (Recommendations + Triggers):**
     - TP suggests actions ("Add Competitor X to watchlist")
     - User approves → TP updates agent configs
     - TP can trigger work sessions
   - [ ] **Phase 3.3 (Pattern Recognition + Auto-Recursion):**
     - TP detects patterns ("User rejects emoji posts")
     - TP creates raw_dumps from synthesized insights
     - TP manages its own memory (stores learnings)

4. **API Routes:**
   ```
   POST /api/projects/{projectId}/thinking-partner/chat - Send message
   GET  /api/projects/{projectId}/thinking-partner/insights - Get insights
   POST /api/projects/{projectId}/thinking-partner/trigger-work - Trigger work session
   PUT  /api/projects/{projectId}/thinking-partner/update-config - Update agent config
   ```

**Success Criteria:**
- [ ] User can chat with Thinking Partner
- [ ] TP provides insights with citations
- [ ] TP can trigger Research agent run via chat
- [ ] TP detects user preference patterns
- [ ] TP creates raw_dump from synthesized insight

---

## Recent Implementation Summary (2025-11-17)

### What's Deployed
1. **SDK Internalization**: claude_agent_sdk → yarnnn_agents (work-platform owns orchestration)
2. **Tool-Use Pattern**: emit_work_output forces Claude to emit structured outputs
3. **BFF Pattern**: work-platform orchestrates, substrate-API owns data
4. **Dual Auth**: Service-to-service + User JWT supported
5. **Work Output Lifecycle**: Complete supervision flow (pending_review → approved/rejected)

### Architectural Decisions Made
- work_outputs table in substrate-API (not work-platform) for basket-scoped RLS
- work_session_id cross-DB reference (no FK enforcement, validated in app code)
- Deferred: Approved outputs do NOT auto-absorb into substrate blocks
- Service auth bypasses workspace membership (trusted backend-to-backend)

### Next Priorities
1. Frontend work management UI (supervision dashboard)
2. Agent quality experiments (output quality validation)
3. Execution modes (Phase 2)

---

## Deferred Capabilities

### Why Deferred & When to Revisit

#### 1. **Derived Intelligence as Separate Concern** (Deferred to Phase 4+)

**What it is:** Automated pattern recognition, trend detection, and insight synthesis stored in a dedicated table.

**Why deferred:**
- Phase 3 Thinking Partner absorbs this scope (handles patterns, insights, recommendations)
- Don't know yet if intelligence should be:
  - High-frequency metrics → TimescaleDB
  - Text-based insights → Postgres with embeddings
  - Graph provenance → Neo4j
- Need real usage data to inform storage decision

**When to revisit:** After Phase 3 Thinking Partner is live and we see:
- Volume of insights generated
- Query patterns (time-series? graph traversal?)
- Performance bottlenecks

**Placeholder schema (for reference):**
```sql
-- Only implement if Thinking Partner memory proves insufficient:
CREATE TABLE derived_intelligence (
  id uuid PRIMARY KEY,
  basket_id uuid REFERENCES baskets(id),
  intelligence_type text, -- 'trend', 'pattern', 'anomaly'
  content jsonb,
  provenance jsonb, -- {source_blocks: [...], confidence: 0.8}
  temporal_window tstzrange,
  created_at timestamptz
);
```

---

#### 2. **Time-Series Database for Metrics** (Deferred to Phase 4+)

**What it is:** TimescaleDB extension for storing high-frequency temporal data (daily competitor headcount, sentiment scores, traffic metrics).

**Why deferred:**
- Current use cases don't have high-frequency data
- JSONB in Postgres can handle low-frequency temporal data
- Don't want to add DB complexity prematurely

**When to revisit:** When Research agent is:
- Monitoring 50+ competitors daily
- Tracking 10+ metrics per competitor
- Querying trends frequently ("Show me headcount growth over 6 months")

**Migration path (when needed):**
```sql
-- Install TimescaleDB extension:
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert thinking_partner_memory to hypertable:
SELECT create_hypertable('thinking_partner_memory', 'created_at');
```

---

#### 3. **Graph Database for Provenance** (Deferred to Phase 5+)

**What it is:** Neo4j or Dgraph for deep provenance tracking (what derived from what, multi-level chains).

**Why deferred:**
- JSONB provenance (1-2 levels deep) sufficient for now
- Postgres JSONB with GIN indexes handles shallow graphs well
- Graph DB adds operational complexity

**When to revisit:** When queries need:
- Multi-hop traversal ("Show me all insights derived from this competitor's funding announcement, 5 levels deep")
- Complex graph algorithms (PageRank for block importance)

**Migration path (when needed):**
```cypher
// Neo4j example:
(block:ContextBlock {id: 'uuid1'})
(asset:ReferenceAsset {id: 'uuid2'})
(insight:ThinkingPartnerMemory {id: 'uuid3'})

(block)-[:DERIVED_FROM]->(asset)
(insight)-[:DERIVED_FROM]->(block)
(insight)-[:CREATED_BY_SESSION]->(work_session)
```

---

#### 4. **Full Work Artifact Recursion** (Deferred - Absorbed by Metadata Approach)

**What it was:** Agents reading full text of previous reports/posts.

**Why deferred:**
- Risk of circular reasoning (agent cites its own analysis)
- Metadata recursion (what was analyzed, not conclusions) is safer
- Exception: Content Agent reads approved posts (specific use case)

**Current approach:**
```sql
-- Lightweight metadata query:
SELECT
  ws.task_intent,
  ws.created_at,
  ws.metadata->>'findings_count' as findings_count
FROM work_sessions ws
WHERE ws.project_agent_id = $agent_id
  AND ws.status = 'completed'
ORDER BY ws.created_at DESC
LIMIT 5;
```

**When to revisit:** If agents demonstrate need for full-text recursion with clear use case that avoids circular reasoning.

---

## Technical Implementation Guide

### BFF Route Specifications

#### Reference Assets Routes

**POST /api/baskets/{basketId}/assets**
```typescript
// Request:
{
  file: File, // multipart/form-data
  asset_type: 'brand_voice_sample' | 'competitor_screenshot' | ...,
  asset_category: 'brand_identity' | 'competitive_intel' | ...,
  agent_scope: ['content', 'research'],
  permanence: 'permanent' | 'temporary',
  expires_at?: string, // ISO 8601, required if temporary
  work_session_id?: string, // required if temporary
  description?: string,
  tags?: string[]
}

// Response:
{
  asset: {
    id: string,
    storage_path: string,
    file_name: string,
    asset_type: string,
    created_at: string,
    ...
  }
}

// Implementation:
1. Validate user owns basket (RLS)
2. Upload file to Supabase Storage: baskets/{basketId}/assets/{uuid}/{filename}
3. Generate description embedding (if description provided)
4. Insert metadata row in reference_assets
5. Return asset object
```

**GET /api/baskets/{basketId}/assets**
```typescript
// Query params:
{
  asset_type?: string,
  asset_category?: string,
  agent_scope?: string, // Filter by agent
  permanence?: 'permanent' | 'temporary',
  tags?: string[], // Filter by tags
}

// Response:
{
  assets: Asset[],
  total: number
}

// Implementation:
1. Build WHERE clause from filters
2. Query reference_assets with RLS
3. Return paginated results
```

---

#### Agent Config Routes

**GET /api/projects/{projectId}/agents/{agentId}/config**
```typescript
// Response:
{
  agent_id: string,
  agent_type: 'research' | 'content' | 'reporting',
  config: AgentConfig, // Type depends on agent_type
  config_version: number,
  last_updated_at: string
}

// Implementation:
1. Validate user owns project
2. Query project_agents
3. Return config with version
```

**PUT /api/projects/{projectId}/agents/{agentId}/config**
```typescript
// Request:
{
  config: AgentConfig, // Validated against agent_type schema
  change_reason?: string
}

// Response:
{
  agent_id: string,
  config: AgentConfig,
  config_version: number, // Incremented
  last_updated_at: string
}

// Implementation:
1. Validate user owns project
2. Validate config schema (per agent_type)
3. Insert snapshot into agent_config_history
4. Update project_agents.config
5. Increment config_version
6. Return updated config
```

---

### UI Component Specifications

#### Context Page - Assets Tab

**Location:** `/app/projects/[id]/context/page.tsx`

**Components:**
```tsx
// New tab component:
<Tabs defaultValue="blocks">
  <TabsList>
    <TabsTrigger value="blocks">Blocks</TabsTrigger>
    <TabsTrigger value="assets">Assets</TabsTrigger> {/* NEW */}
  </TabsList>

  <TabsContent value="blocks">
    <ContextBlocksClient />
  </TabsContent>

  <TabsContent value="assets">
    <ReferenceAssetsClient /> {/* NEW */}
  </TabsContent>
</Tabs>

// ReferenceAssetsClient.tsx:
interface ReferenceAssetsClientProps {
  basketId: string;
}

export function ReferenceAssetsClient({ basketId }: ReferenceAssetsClientProps) {
  // State: assets, loading, filters
  // Actions: upload, delete, filter

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <Card>
        <UploadAssetForm basketId={basketId} onSuccess={refetch} />
      </Card>

      {/* Filters */}
      <AssetFilters
        filters={filters}
        onChange={setFilters}
      />

      {/* Assets Grid */}
      <AssetsGrid
        assets={assets}
        onDelete={handleDelete}
      />
    </div>
  );
}
```

---

#### Agent Dashboard - Config Section

**Location:** `/app/projects/[id]/agents/[agentType]/page.tsx`

**Components:**
```tsx
// AgentDashboardClient.tsx enhancement:
<Card className="p-6">
  <h2 className="text-lg font-semibold mb-4">Configuration</h2>

  {agentType === 'research' && (
    <ResearchAgentConfigForm
      agentId={agent.id}
      config={agent.config}
      onSave={handleConfigSave}
    />
  )}

  {agentType === 'content' && (
    <ContentAgentConfigForm
      agentId={agent.id}
      config={agent.config}
      onSave={handleConfigSave}
    />
  )}

  {agentType === 'reporting' && (
    <ReportingAgentConfigForm
      agentId={agent.id}
      config={agent.config}
      onSave={handleConfigSave}
    />
  )}
</Card>

// ResearchAgentConfigForm.tsx:
export function ResearchAgentConfigForm({ agentId, config, onSave }) {
  return (
    <form onSubmit={handleSubmit}>
      {/* Watchlist Section */}
      <div className="space-y-2">
        <Label>Competitor Watchlist</Label>
        <TagInput
          value={config.watchlist.competitors}
          onChange={(val) => setConfig({...config, watchlist: {...config.watchlist, competitors: val}})}
          placeholder="Add competitor..."
        />
      </div>

      {/* Data Sources Section */}
      <div className="space-y-2">
        <Label>Data Sources</Label>
        {config.watchlist.data_sources.map((source, idx) => (
          <DataSourceInput
            key={idx}
            value={source}
            onChange={(val) => updateDataSource(idx, val)}
          />
        ))}
        <Button type="button" onClick={addDataSource}>+ Add Source</Button>
      </div>

      {/* Alert Rules Section */}
      <div className="space-y-2">
        <Label>Alert Rules</Label>
        <Input
          type="number"
          label="Funding Threshold (USD)"
          value={config.alert_rules.funding_threshold_usd}
          onChange={(e) => setConfig({...config, alert_rules: {...config.alert_rules, funding_threshold_usd: +e.target.value}})}
        />
      </div>

      <Button type="submit">Save Configuration</Button>
    </form>
  );
}
```

---

### Agent Execution Flow Enhancement

**Current Flow:**
```typescript
// platform-api/src/routes/work.ts
async function createWorkSession(req, res) {
  // 1. Validate request
  // 2. Create work_session row
  // 3. Call substrate-api to execute work
  // 4. Return work_session object
}
```

**Enhanced Flow (Phase 1):**
```typescript
async function createWorkSession(req, res) {
  // 1. Validate request

  // 2. Create work_session row
  const workSession = await createWorkSessionRow(...);

  // 3. Fetch agent execution payload:
  const payload = await buildAgentPayload(workSession);

  // 4. Call substrate-api with enhanced payload
  const result = await substrateClient.executeWork({
    work_session_id: workSession.id,
    ...payload
  });

  // 5. Return work_session
  return res.json({ work_session: workSession });
}

async function buildAgentPayload(workSession) {
  const agent = await getProjectAgent(workSession.project_agent_id);

  // Fetch context blocks (existing):
  const contextBlocks = await getContextBlocks(workSession.basket_id);

  // Fetch reference assets (NEW):
  const referenceAssets = await getReferenceAssets({
    basket_id: workSession.basket_id,
    agent_scope: agent.agent_type,
    permanence: 'permanent', // Only permanent assets by default
  });

  // Get agent config (NEW):
  const agentConfig = agent.config;

  return {
    context_blocks: contextBlocks,
    reference_assets: referenceAssets,
    agent_config: agentConfig,
  };
}
```

---

## Appendix: Decision Rationale

### A1. Why Reference Assets are Separate from Context Blocks

**Five Axiom-Level Differences:**

1. **Storage Location:**
   - Blocks: Content stored in SQL (queryable text)
   - Assets: Files in blob storage (SQL has pointer only)

2. **Mutability Model:**
   - Blocks: Mutable via governance (edit → proposal → approval)
   - Assets: Immutable (replace, not edit)

3. **Retrieval Pattern:**
   - Blocks: Semantic search (vector similarity) + full-text
   - Assets: Metadata filtering (tags, type, scope)

4. **Type System:**
   - Blocks: Semantic types (fact, insight, principle)
   - Assets: Functional types (brand_voice_sample, competitor_screenshot)

5. **Agent Consumption:**
   - Blocks: Text included in prompt
   - Assets: File downloaded + encoded (vision model for images)

**Conclusion:** Attempting to unify creates sparse columns, complex queries, and leaky abstractions. Separation is justified.

---

### A2. Why Not Vector-First Database (Pinecone/Weaviate)

**What Vector-First Solves:**
- ✅ Semantic search at massive scale (100M+ vectors)
- ✅ Low-latency similarity queries
- ✅ Horizontal scaling for ML workloads

**What Vector-First Doesn't Solve:**
- ❌ RLS/Governance (must rebuild in app code)
- ❌ Relational queries ("Show work sessions for this project")
- ❌ Time-series data (trends, metrics)
- ❌ Provenance tracking (graph relationships)

**yarnnn's Current Scale:**
- 1000s of blocks per project (not millions)
- Postgres + pgvector handles this easily
- RLS is critical for multi-tenancy
- Relational joins are common

**When to Reconsider:** If pgvector performance degrades at 10M+ blocks. Unlikely in next 12-24 months.

---

### A3. Why Postgres + Extensions (Not Polyglot from Day 1)

**Pragmatic Incrementalism:**
- Start with Postgres for everything (blocks, assets metadata, configs, work sessions)
- Add Supabase Storage for blobs (S3-backed, already integrated)
- Defer TimescaleDB until high-frequency metrics exist
- Defer Graph DB until provenance queries hit JSONB limits

**Rationale:**
- ✅ Operational simplicity (one primary DB)
- ✅ Proven stack (Supabase handles millions of users)
- ✅ Can add extensions without data migration (TimescaleDB is Postgres extension)
- ✅ Clear inflection points for when to add complexity

**Not Premature Optimization:** We add new storage systems when existing stack proves insufficient, not speculatively.

---

### A4. Why Thinking Partner Absorbs Intelligence & Recursion

**Original Plan:**
- Separate derived_intelligence table
- Separate recursion decision logic
- Separate chat interface

**Unified Approach:**
- Thinking Partner IS the meta-agent that:
  - Stores intelligence (thinking_partner_memory)
  - Makes recursion decisions (creates raw_dumps)
  - Provides chat interface (thinking_partner_chats)

**Benefits:**
- ✅ Single mental model ("talk to the Thinking Partner")
- ✅ Avoid table sprawl (one memory table vs. separate intelligence table)
- ✅ Clear ownership (TP owns all meta-operations)

**Trade-off:** Thinking Partner is more complex. But complexity is concentrated in one place, not spread across multiple systems.

---

## Document Control

**Version History:**
- v1.0 (2024-11-13): Initial comprehensive architecture
- v1.1 (2024-11-13): Schema stress tested - Critical updates:
  - **Database Placement Decision**: reference_assets moved to substrate-API DB (colocated with blocks)
  - **Migration Scripts**: Complete Phase 1 migrations for both DBs
  - **Schema Cleanup**: Remove redundant executed_by_agent_id column
  - **Agent Catalog**: Added agent_catalog table definition
  - **Thinking Partner Location**: Clarified substrate-API DB placement
  - **Storage Setup**: Complete Supabase Storage configuration with RLS
  - **API Endpoints**: substrate-API must implement file upload (not just BFF proxy)
  - **Validation**: Cross-DB FK constraints handled in app code
- v1.2 (2024-11-13): Config flexibility & enterprise B2B rationale:
  - **Rationale refined**: Added enterprise B2B standalone substrate service as primary driver
  - **Agent catalog flexibility**: Removed hardcoded CHECK constraints, added JSON Schema validation
  - **Asset type catalog**: Dynamic admin-managed catalog instead of hardcoded enums
  - **Lifecycle management**: Added is_active, is_beta, deprecated_at to both catalogs
  - **Schema versioning**: Added schema_version for config migration support
  - **Admin UI foundation**: Catalogs can be updated via admin routes without migrations
- **v2.0 (2025-11-17): Work Output Lifecycle Deployed - Major updates:**
  - **Phase 4 Complete**: Work Output Lifecycle Management deployed
  - **SDK Internalization**: claude_agent_sdk → yarnnn_agents (work-platform owns orchestration)
  - **Tool-Use Pattern**: emit_work_output forces structured agent outputs
  - **BFF Pattern Enforced**: work-platform orchestrates, substrate-API owns data
  - **Dual Auth Support**: Service-to-service + User JWT in substrate-API
  - **work_outputs table**: Lives in substrate-API for basket-scoped RLS
  - **Supervision Status**: pending_review → approved/rejected/revision_requested
  - **Provenance Tracking**: source_context_ids maps outputs to source blocks
  - **Marked Future**: Phases 2-3 clearly marked as not started
  - **Updated Primitives**: Work Artifacts → Work Outputs (terminology clarity)
- **v2.1 (2025-11-19): Agent Knowledge Modules Architecture - Refinements:**
  - **Phase 2d Added**: Agent Knowledge Modules (procedural knowledge layer)
  - **The Agent Execution Triad**: Config (WHAT) + Knowledge (HOW) + Assets (EXAMPLES)
  - **Terminology Clarity**: "Skills" → "Knowledge Modules" (not official Claude SDK Skills)
  - **Orchestration Layer**: Centralized payload building with knowledge module loading
  - **Architecture Alignment**: Knowledge modules complement agent_config (receiving side)
  - **File-based Storage**: Markdown modules in `agent_orchestration/knowledge_modules/`
  - **Reusability**: Core modules (quality_standards, substrate_patterns) + agent-specific
  - **Future Path**: Clear separation allowing official Skills integration later

**Approvals:**
- Architecture: ✅ Approved
- Schema Stress Test: ✅ Completed (see ARCHITECTURE_STRESS_TEST.md)
- Implementation: ✅ Ready for Phase 1 kickoff

**Critical Implementation Notes:**

1. **Two Separate Migrations Required:**
   - `/supabase/migrations/YYYYMMDD_phase1_agent_configs.sql` (work-platform DB)
   - `/substrate-api/migrations/YYYYMMDD_phase1_reference_assets.sql` (substrate-API DB)

2. **substrate-API Must Handle File Uploads:**
   - Cannot proxy from work-platform BFF (reference_assets table in substrate-API DB)
   - Implement multipart/form-data handling
   - Use Supabase Storage client with service role key

3. **Cross-DB Reference Handling:**
   - `reference_assets.work_session_id` is NOT a FK (cross-DB)
   - Enforce referential integrity in application code
   - Validate work_session existence before creating temporary asset

4. **Compatibility Validated:**
   - ✅ P0-P4 pipeline unchanged
   - ✅ Governance flow unchanged
   - ✅ Work execution backward compatible
   - ✅ Existing queries continue working

**Next Steps:**
1. ✅ Architecture document updated with stress test findings
2. Create Phase 1 implementation tickets:
   - Ticket 1: Run migrations on both DBs
   - Ticket 2: Configure Supabase Storage bucket
   - Ticket 3: Implement substrate-API file upload endpoints
   - Ticket 4: Implement work-platform BFF proxy routes
   - Ticket 5: Build UI components (Assets tab, Config forms)
   - Ticket 6: Enhance agent execution payload
3. Begin Phase 1 development

**Related Documents:**
- `/ARCHITECTURE_STRESS_TEST.md` - Schema validation against production
- `/YARNNN_ALERTS_NOTIFICATIONS_CANON.md` - Event system for agent notifications
- `/docs/governance-hierarchy.md` - Governance flow for substrate mutations

---

**End of Document**
