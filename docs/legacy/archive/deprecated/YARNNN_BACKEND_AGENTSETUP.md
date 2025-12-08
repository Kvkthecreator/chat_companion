# YARNNN Backend Agent Setup - Canon v1.4.0 Specification

**Version**: 1.0  
**Status**: Canon Extension  
**Purpose**: Define the canonical agent architecture that implements YARNNN pipeline boundaries and Sacred Principle #4

## 🎯 First Principle: Pipeline-Aligned Agent Architecture

**Each agent maps to exactly one pipeline. No exceptions.**

This eliminates boundary violations and ensures canonical substrate processing.

## 🏗️ Canonical Agent Architecture

### The Five Pipeline Agents (P0-P4)

```
P0: CaptureAgent        → Only writes raw_dumps
P1: SubstrateAgent      → Creates blocks, context_items  
P2: GraphAgent          → Creates relationships
P3: ReflectionAgent     → Computes derived patterns
P4: PresentationAgent   → Composes documents, narratives
```

### Agent Hierarchy

```
QueueProcessor (orchestrates)
├── P0: CaptureAgent (dump ingestion)
├── P1: SubstrateAgent (block/context creation) 
├── P2: GraphAgent (relationship mapping)
├── P3: ReflectionAgent (pattern computation)
└── P4: PresentationAgent (narrative composition)
```

## 📋 Canonical Agent Definitions

### 1. P0 Capture Agent
**File**: `agents/pipeline/capture_agent.py`
**Purpose**: Process dump ingestion requests only
**Sacred Rule**: Only writes raw_dumps, never interprets content
**Operations**:
- File content extraction from Supabase Storage
- Text normalization and validation
- Metadata capture
- Dump persistence via `fn_ingest_dumps` RPC

```python
class P0CaptureAgent:
    """Canonical P0 Capture pipeline agent."""
    pipeline = "P0_CAPTURE"
    
    async def process_dump_ingestion(self, request: DumpIngestionRequest) -> DumpResult:
        # ONLY file extraction, text normalization, dump persistence
        # NO interpretation, NO block creation, NO analysis
```

### 2. P1 Substrate Agent  
**File**: `agents/pipeline/substrate_agent_v2.py`
**Purpose**: Extract structured knowledge ingredients from raw dumps
**Sacred Rule**: Creates blocks/context_items, never relationships or reflections
**Operations**:
- Extract goals, constraints, metrics, entities, and relationships from dump content
- Create blocks with structured knowledge data and provenance tracking  
- Use OpenAI Structured Outputs with JSON Schema enforcement
- Context item extraction with semantic classification
- Substrate persistence via proper RPCs with knowledge_ingredients metadata

```python
class P1SubstrateAgent:
    """Canonical P1 Substrate pipeline agent."""
    pipeline = "P1_SUBSTRATE"
    
    async def create_substrate(self, dump_id: str) -> SubstrateResult:
        # Extract structured knowledge (goals, constraints, metrics, entities)
        # Create blocks with knowledge_ingredients via BlockProposalService
        # Extract context_items with semantic types
        # Track provenance for all extracted data
        # NO relationship creation, NO pattern analysis
```

### 3. P2 Graph Agent
**File**: `agents/pipeline/graph_agent.py`  
**Purpose**: Connect existing substrate elements
**Sacred Rule**: Creates relationships, never modifies substrate content
**Operations**:
- Relationship discovery between substrates
- Connection strength analysis
- Graph structure optimization
- Relationship persistence

```python
class P2GraphAgent:
    """Canonical P2 Graph pipeline agent."""
    pipeline = "P2_GRAPH"
    
    async def map_relationships(self, substrate_ids: List[str]) -> RelationshipResult:
        # Analyze existing substrate for connections
        # Create relationships between blocks, context_items
        # NO substrate modification, NO content changes
```

### 4. P3 Reflection Agent
**File**: `agents/pipeline/reflection_agent.py`
**Purpose**: Compute derived patterns and insights  
**Sacred Rule**: Read-only computation, optionally cached
**Operations**:
- Pattern recognition across substrates
- Insight derivation
- Trend analysis
- Reflection caching (optional)

```python
class P3ReflectionAgent:
    """Canonical P3 Reflection pipeline agent."""
    pipeline = "P3_REFLECTION"
    
    async def compute_reflections(self, workspace_id: str) -> ReflectionResult:
        # Read-only analysis of existing substrate
        # Pattern computation, insight derivation
        # NO substrate creation, NO modifications
```

### 5. P4 Presentation Agent
**File**: `agents/pipeline/presentation_agent.py`
**Purpose**: Compose narratives from substrate
**Sacred Rule**: Consumes substrate for documents/narratives, never creates substrate
**Operations**:
- Document composition
- Narrative generation
- User-facing content creation
- Presentation formatting

```python
class P4PresentationAgent:
    """Canonical P4 Presentation pipeline agent."""
    pipeline = "P4_PRESENTATION"  
    
    async def compose_document(self, composition_request: CompositionRequest) -> DocumentResult:
        # Consume existing substrate for narrative
        # Generate user-facing documents
        # NO substrate creation, only consumption
```

## 🔄 Queue Processing Model

### Canonical Queue Processor
**File**: `services/canonical_queue_processor.py`
**Purpose**: Orchestrate pipeline agents in sequence
**Operations**:
```python
async def process_dump(self, queue_entry):
    # Sequential pipeline processing
    dump_result = await self.p0_capture.process_dump_ingestion(request)
    substrate_result = await self.p1_substrate.create_substrate(dump_result.dump_id)  
    relationship_result = await self.p2_graph.map_relationships(substrate_result.substrate_ids)
    reflection_result = await self.p3_reflection.compute_reflections(workspace_id)
    # P4 triggered on-demand, not in queue processing
```

### Processing Sequence
```
Queue Entry → P0 Capture → P1 Substrate → P2 Graph → P3 Reflection
                                                              ↓
User Request → P4 Presentation ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

## 🗂️ File Structure Reorganization

### New Canonical Structure
```
api/src/app/agents/
├── pipeline/                    # Canon pipeline agents
│   ├── __init__.py
│   ├── capture_agent.py        # P0 Capture
│   ├── substrate_agent.py      # P1 Substrate  
│   ├── graph_agent.py          # P2 Graph
│   ├── reflection_agent.py     # P3 Reflection
│   └── presentation_agent.py   # P4 Presentation
├── services/
│   ├── canonical_queue_processor.py  # Orchestrator
│   └── pipeline_boundaries.py        # Boundary enforcement
└── [SUNSET ALL OTHER AGENT DIRS]
```

### Files to Sunset
```
agents/runtime/                 # Multiple boundary violations
agents/narrative/              # Mix P3/P4 responsibilities  
agents/integration/            # Unclear canon alignment
agents/tasks/                  # Pipeline boundary mixing
agents/tools/                  # Should be in services/
agents/utils/                  # Should be in services/
services/dump_interpreter.py   # Replaced by P1SubstrateAgent
services/substrate_ops.py      # Boundary violations
services/document_composition.py # Replaced by P4PresentationAgent
services/context_tagger.py     # P1/P2 boundary mixing
```

## 🎯 Implementation Strategy

### Phase 1.5 Day 2: Create Canonical Agents
1. **Create pipeline agent directory structure**
2. **Implement P0CaptureAgent** (migrate from dump_interpreter)  
3. **Implement P1SubstrateAgent** (clean substrate creation)
4. **Implement P2GraphAgent** (relationship mapping only)
5. **Implement P3ReflectionAgent** (read-only computation)
6. **Implement P4PresentationAgent** (document composition)

### Phase 1.5 Day 3: Integration & Cleanup
1. **Create CanonicalQueueProcessor** (orchestrate P0-P3 sequence)
2. **Update API routes** to use canonical agents  
3. **Sunset legacy agent code** (remove non-canon agents)
4. **Update tests** to validate pipeline boundaries
5. **Verify canon compliance** via boundary tests

## ✅ Success Criteria

1. **Single Pipeline Responsibility**: Each agent maps to exactly one pipeline
2. **No Boundary Violations**: Agents respect sacred rules strictly
3. **Clean Architecture**: No duplicate/overlapping agent functionality  
4. **Canon Compliance**: All Sacred Principles enforced in code
5. **Documentation Clarity**: Agent responsibilities clearly defined

## 🚫 Anti-Patterns Eliminated

- ❌ Agents doing multiple pipeline work
- ❌ Infrastructure vs Runtime vs Narrative confusion  
- ❌ Services mixing pipeline boundaries
- ❌ Duplicate agent functionality
- ❌ Unclear agent responsibilities

## 🎯 Result: Clean Canon-Compliant Backend

This specification eliminates agent drift and establishes the single canonical way to implement YARNNN's async intelligence framework while respecting all pipeline boundaries and Sacred Principles.

---

**Next**: Execute this specification to create the canonical agent system.