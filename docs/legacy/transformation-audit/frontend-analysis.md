# Frontend Language Analysis

## Substrate Vocabulary in UI Components

### **Block Language Patterns**
- **components/blocks/BlocksPane.tsx**:
  - Line 18: `"No proposed blocks yet."` → Should be narrative
  - Block state filtering: `state === "PROPOSED"` → Technical substrate exposure
  - Block history tracking exposed to users

- **components/blocks/BlockCreateModal.tsx**:
  - Modal for creating "blocks" - needs complete language transformation
  - Form fields: `type`, `label`, `content` → Technical vocabulary
  - Should become "Add Insight", "Capture Idea", "Document Knowledge"

- **components/blocks/CoreBlockForm.tsx**:
  - Labels like "Label", "Type" → Generic technical language
  - Needs transformation to narrative prompts

### **Intelligence Language Patterns**
- **components/baskets/MemoryEvolution.tsx**:
  - `"Project Memory"` → Good narrative start
  - `"Intelligence: 75%"` → Technical confidence display
  - `"Ready to learn"`, `"Early understanding"` → Good narrative labels
  - **STATUS**: Partially transformed, needs completion

- **components/baskets/IntelligenceUnderstanding.tsx**:
  - `"Your Project Intelligence"` → Good narrative heading
  - Uses conversational understanding text → Good pattern
  - Theme badges → Good progressive disclosure

### **Analysis Component Patterns**
- **components/intelligence/LiveThinkingPartner.tsx**:
  - Narrative approach already implemented
  - Good example of human-centric intelligence presentation

- **components/ui/IntelligenceIndicators.tsx**:
  - Technical indicators, needs narrative transformation
  - Should show progress narratively, not technically

## Technical vs User Language Mapping

### **GOOD Narrative Patterns Found**
```tsx
// IntelligenceUnderstanding.tsx - Good conversational pattern
understanding: "From your documents and context, I can see early themes..."

// MemoryEvolution.tsx - Good confidence labels
getConfidenceLabel(score):
  - "Ready to learn"
  - "Early understanding" 
  - "Growing intelligence"
  - "Strong insights"
  - "Deep understanding"
```

### **BAD Technical Patterns Found**
```tsx
// BlocksPane.tsx - Raw technical language
"No proposed blocks yet."
blocks.filter(b => b.state === "PROPOSED")

// Block creation - Technical CRUD language
"Create Block", "Edit Block", "Delete Block"

// Raw confidence scoring
"Confidence: 75%"
"Analysis ID: abc123"
```

### **Transformation Requirements**

#### **High Priority Language Changes**
1. **Block → Knowledge Piece/Insight/Idea**
   - "Create Block" → "Capture Insight"
   - "Edit Block" → "Refine Idea"
   - "No blocks yet" → "No insights captured yet"

2. **Technical Confidence → Narrative Indicators**
   - "Confidence: 75%" → "Strong understanding of your project"
   - Progress bars with narrative context
   - Remove percentage displays

3. **Analysis → Understanding**
   - "Thematic Analysis" → "Project Understanding"
   - "Document Relationships" → "Content Connections"
   - "Coherence Suggestions" → "Next Steps"

#### **Medium Priority Changes**
1. **Context Items → Reference Material**
   - "Add Context Item" → "Add Reference"
   - "Context Guidelines" → "Project Guidelines"

2. **Technical States → Human States**
   - "PROPOSED" → "Draft"
   - "ACTIVE" → "Live"
   - "ARCHIVED" → "Saved"

## CRUD Operations Analysis

### **Current Technical CRUD Patterns**
- Block creation: Technical modal with type/label fields
- Document creation: Generic "Create Document" language
- Context item management: Technical administrative language

### **Narrative CRUD Transformation**
```tsx
// Instead of technical CRUD:
"Create Block" → "Capture New Insight"
"Edit Context" → "Update Project Background"
"Delete Analysis" → "Remove Understanding"

// Progressive disclosure CRUD:
"+" button → "Add to your project"
Settings gear → "Refine understanding"
Trash icon → "Remove from workspace"
```

## Component Transformation Priorities

### **High Priority Components (Complete Overhaul)**
1. **components/blocks/*** - All block-related components
2. **components/blocks/BlockCreateModal.tsx** - Primary creation interface
3. **components/blocks/BlocksPane.tsx** - Main display component

### **Medium Priority Components (Language Updates)**
1. **components/baskets/MemoryEvolution.tsx** - Remove technical confidence display
2. **components/ui/IntelligenceIndicators.tsx** - Narrative indicators
3. **components/intelligence/*** - Various intelligence components

### **Low Priority Components (Minor Updates)**
1. Navigation and layout components - Mostly structural
2. Form components - Update labels and placeholders
3. Utility components - Internal technical language acceptable

## Recommended Transformation Approach

### **Phase 1: Core Vocabulary Revolution**
- Replace all "block" references with "insight"/"idea"/"knowledge piece"
- Transform confidence percentages to narrative indicators
- Update all user-facing technical language

### **Phase 2: Narrative Flow Enhancement**
- Convert CRUD operations to narrative actions
- Implement progressive disclosure patterns
- Add contextual help with narrative explanations

### **Phase 3: Deep Integration**
- Ensure narrative consistency across all user flows
- Remove any remaining technical substrate exposure
- Implement user testing and refinement