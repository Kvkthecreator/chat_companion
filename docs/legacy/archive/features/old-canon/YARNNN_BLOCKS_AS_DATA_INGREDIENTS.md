# YARNNN Blocks as Data Ingredients Architecture

**Version**: 1.0  
**Status**: Canon Definition  
**Purpose**: Define the canonical architecture where blocks are structured knowledge ingredients, not text chunks

## 🎯 Core Philosophy

**Blocks are data ingredients, not text overlays.**

Traditional systems treat blocks as formatted text. YARNNN treats blocks as structured knowledge that can be:
- Transformed and composed programmatically
- Queried by specific attributes (find all blocks with budget constraints)
- Combined to generate different document formats
- Validated for completeness and consistency

## 📊 Block Structure Definition

Each block created by the P1 Substrate Agent contains:

```typescript
interface KnowledgeBlock {
  // Core identification
  semantic_type: string;        // "requirements", "strategy", "specification", etc.
  title: string;               // Human-readable summary
  confidence: number;          // 0.0 to 1.0 extraction confidence
  
  // Structured knowledge ingredients
  entities: Entity[];          // Key actors, systems, components
  goals: Goal[];              // Objectives and desired outcomes
  constraints: Constraint[];   // Limitations, requirements, boundaries
  metrics: Metric[];          // Measurable criteria and success indicators
  relationships: Relationship[]; // Connections between entities
  
  // Traceability
  provenance: Provenance;      // Source text spans for each extracted item
}
```

### Detailed Field Definitions

#### Entities
Key actors, systems, or components mentioned in the source:
```typescript
interface Entity {
  name: string;               // "Sarah Chen", "React 18", "Authentication Service"
  type: string;               // "person", "technology", "system"
  role?: string;              // "Product Manager", "Frontend Framework", "Security Layer"
  properties: Record<string, any>; // Additional structured data
  provenance: Provenance;     // Where this was found in source
}
```

#### Goals
Objectives and desired outcomes:
```typescript
interface Goal {
  description: string;        // "Launch feature by December 2024"
  priority?: "high" | "medium" | "low";
  timeframe?: string;         // "Q4 2024", "6 months"
  success_criteria?: string[]; // Specific achievement markers
  provenance: Provenance;
}
```

#### Constraints
Limitations, requirements, and boundaries:
```typescript
interface Constraint {
  type: string;               // "budget", "technical", "regulatory", "resource"
  description: string;        // "Limited to $75K budget"
  severity?: "hard" | "soft"; // Hard = must satisfy, Soft = preferred
  mitigation?: string;        // How to work within this constraint
  provenance: Provenance;
}
```

#### Metrics
Measurable criteria and success indicators:
```typescript
interface Metric {
  name: string;               // "Daily Active Users"
  target: string;             // "25% increase"
  current?: string;           // Current baseline if known
  measurement_method?: string; // How to measure
  frequency?: string;         // "daily", "weekly", "monthly"
  provenance: Provenance;
}
```

## 🔄 Processing Pipeline

### 1. P0 Capture Agent
- Receives raw text or file uploads
- Creates immutable `raw_dumps`
- No interpretation or structuring

### 2. P1 Substrate Agent v2 (Comprehensive Batch Mode)
- Processes multiple raw dumps in unified batch operation for Share Updates
- Performs cross-content analysis to identify relationships spanning inputs
- Uses OpenAI Structured Outputs with JSON Schema for consistency
- Extracts unified structured knowledge ingredients from comprehensive analysis
- Validates provenance with UTF-8 span tracking across all source dumps
- Generates single coherent proposal with cross-dump relationships
- Stores comprehensive ingredients in `blocks.metadata.knowledge_ingredients`

### 3. P2-P3 Agents
- Work with structured data, not text
- Can query blocks by specific attributes
- Build relationships between ingredients

### 4. P4 Presentation Agent
- Composes documents from structured ingredients
- Can generate different formats from same data
- Documents reference ingredients, not duplicate text

## 💡 Benefits of Data Ingredients

### 1. Queryability
```sql
-- Find all blocks with budget constraints over $100K
SELECT * FROM blocks 
WHERE metadata->'knowledge_ingredients'->'constraints' @> 
  '[{"type": "budget", "description": ~* "\\$[0-9]{3,}K"}]';

-- Find all blocks mentioning specific person
SELECT * FROM blocks
WHERE metadata->'knowledge_ingredients'->'entities' @> 
  '[{"name": "Sarah Chen"}]';
```

### 2. Composability
```python
# Combine goals from multiple blocks into project roadmap
all_goals = []
for block in blocks:
    all_goals.extend(block.metadata.knowledge_ingredients.goals)

# Generate timeline from goals with timeframes
timeline = generate_timeline(
    [g for g in all_goals if g.timeframe]
)
```

### 3. Validation
```python
# Check if all constraints have mitigation strategies
incomplete_constraints = [
    c for c in block.constraints 
    if c.severity == "hard" and not c.mitigation
]

# Verify all metrics have measurement methods
unmeasurable_metrics = [
    m for m in block.metrics
    if not m.measurement_method
]
```

### 4. Transformation
```python
# Transform technical spec into business summary
business_summary = {
    "objectives": [g.description for g in block.goals],
    "budget": next(
        (c.description for c in block.constraints if c.type == "budget"), 
        "Not specified"
    ),
    "success_metrics": [
        f"{m.name}: {m.target}" for m in block.metrics
    ],
    "key_stakeholders": [
        e.name for e in block.entities if e.type == "person"
    ]
}
```

## 🏗️ Implementation Details

### Database Storage
Blocks store structured data in JSONB `metadata` field:
```sql
-- Example block record
{
  "id": "uuid",
  "semantic_type": "requirements",
  "title": "Q4 Feature Launch Requirements",
  "body_md": "[[LEGACY TEXT - Use metadata.knowledge_ingredients instead]]",
  "metadata": {
    "knowledge_ingredients": {
      "entities": [...],
      "goals": [...],
      "constraints": [...],
      "metrics": [...],
      "provenance": {...}
    },
    "extraction_method": "P1_substrate_agent_v2_openai",
    "extraction_timestamp": "2024-01-25T10:30:00Z",
    "confidence": 0.89
  }
}
```

### Feature Flag
```python
# Enable structured ingredients extraction
YARNNN_STRUCTURED_INGREDIENTS = True
```

### API Contract
```typescript
// Frontend should use this structure
interface BlockResponse {
  id: string;
  semantic_type: string;
  title: string;
  metadata: {
    knowledge_ingredients: KnowledgeBlock;
    extraction_method: string;
    confidence: number;
  };
  created_at: string;
  updated_at: string;
}
```

## 🚫 Anti-Patterns to Avoid

### ❌ Text-First Thinking
```javascript
// BAD: Treating blocks as text with some metadata
const blockContent = block.body_md;
const summary = extractSummary(blockContent);
```

### ✅ Data-First Thinking  
```javascript
// GOOD: Working with structured data
const goals = block.metadata.knowledge_ingredients.goals;
const constraints = block.metadata.knowledge_ingredients.constraints;
const summary = generateSummaryFromIngredients(goals, constraints);
```

### ❌ Document-Centric Storage
```javascript
// BAD: Copying text into documents
const document = {
  content: blocks.map(b => b.body_md).join('\n')
};
```

### ✅ Reference-Based Composition
```javascript
// GOOD: Documents reference ingredients
const document = {
  block_references: blocks.map(b => b.id),
  custom_prose: "Additional authored content",
  composition_metadata: {
    primary_goals: extractPrimaryGoals(blocks),
    critical_constraints: extractCriticalConstraints(blocks)
  }
};
```

## 🎯 Vision Alignment

This architecture aligns with YARNNN's core vision:
1. **Intelligence Substrate**: Blocks form structured knowledge base
2. **Transformation Ready**: Data can be reshaped for any purpose
3. **Provenance Tracked**: Every fact traceable to source
4. **Composition Over Duplication**: Reference and transform, don't copy
5. **Machine-Readable First**: Structured for AI/automation, renderable for humans

## 📋 Migration Path

1. **Backend**: ✅ P1 Substrate Agent v2 implemented
2. **Database**: ✅ Migration adds structured fields
3. **Frontend**: ❌ Still displaying body_md instead of ingredients
4. **API**: ❌ Not fetching metadata field

### Next Steps
1. Update frontend API to fetch metadata
2. Create UI components for ingredient display
3. Build query/filter capabilities
4. Implement composition workflows
5. Deprecate body_md display

## 🔮 Future Capabilities

With blocks as data ingredients, we can:
- Auto-generate documentation in multiple formats
- Build knowledge graphs from entity relationships  
- Track requirement → implementation → metric chains
- Identify gaps (goals without metrics, constraints without mitigation)
- Generate project templates from successful patterns
- Enable semantic search across structured attributes

The key insight: **When blocks are data, not text, they become infinitely more useful.**