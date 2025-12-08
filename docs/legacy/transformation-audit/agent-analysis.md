# Agent Architecture Analysis

## Current Agents Found

### **Pure Technical Agents**
- **agentResponseCoordinator.ts** (`lib/intelligence/agentResponseCoordinator.ts`)
  - Coordinates multiple agent responses
  - Exposes technical substrate: `priority`, `trigger_source`, `recommended_panel`
  - Direct panel targeting: `context`, `suggestions`, `memory`, `anticipation`

### **Mixed Presentation Agents**
- **useBasketIntelligence.ts** (`lib/intelligence/useBasketIntelligence.ts`)
  - Direct substrate vocabulary exposure
  - Raw analysis objects: `ThematicAnalysis`, `DocumentRelationships`, `CoherenceSuggestions`
  - Technical confidence scoring exposed directly to UI

- **useBasketIntelligenceDashboard.ts** (`lib/baskets/useBasketIntelligenceDashboard.ts`)
  - Recently created narrative wrapper (good pattern)
  - Still exposes `confidenceScore`, `memoryGrowth` terminology
  - Needs deeper narrative transformation

### **Missing Narrative Layer**
- **API Intelligence Endpoints**: All direct substrate exposure
  - `/api/intelligence/basket/[basketId]/dashboard/route.ts` - exposes blocks, context_items
  - `/api/intelligence/basket/[basketId]/comprehensive/route.ts` - raw analysis data
  - `/api/intelligence/process-content/route.ts` - technical processing language

## Substrate Vocabulary Exposure

### **Direct Substrate Terms Found**
- **"blocks"** - Found in:
  - `app/api/intelligence/basket/[basketId]/dashboard/route.ts:62`
  - `components/blocks/BlocksPane.tsx:18` - "No proposed blocks yet"
  - `components/blocks/BlockCreateModal.tsx` - Block creation modal

- **"context_items"** - Found in:
  - `app/api/intelligence/basket/[basketId]/dashboard/route.ts:77`
  - Database queries throughout intelligence APIs

- **"confidence_score"** - Found in:
  - `components/baskets/MemoryEvolution.tsx:61` - "confidenceScore: 45%"
  - Intelligence APIs returning raw confidence metrics

### **Technical Response Patterns**
```typescript
// Raw substrate exposure examples:
interface ThematicAnalysis {
  analysis_id: string;
  dominant_themes: string[];
  theme_distribution: Record<string, number>;
  discovered_patterns: {
    pattern_strength: "weak" | "moderate" | "strong";
    confidence: number;
  }[];
}
```

### **Transformation Priority**
- **HIGH**: API endpoints exposing raw substrate vocabulary
- **HIGH**: Block creation/editing interfaces using technical language
- **MEDIUM**: Intelligence hooks exposing confidence/analysis objects
- **LOW**: Internal coordination logic (can remain technical)

## Coordination Patterns

### **Agent Handoffs**
- Minimal coordination found - mostly individual intelligence services
- `agentResponseCoordinator.ts` attempts coordination but underutilized
- Direct API calls from components rather than orchestrated responses

### **Service Dependencies**
- Intelligence services depend directly on database substrate
- No abstraction layer between data models and user-facing intelligence
- Components make direct API calls to intelligence endpoints

### **Response Assembly**
- Intelligence assembled at API level, not agent level
- Missing narrative transformation layer between raw analysis and UI
- Dashboard intelligence recently improved but still technical vocabulary

## Recommendations for Narrative Layer

### **High Priority Transformations**
1. **API Narrative Wrappers**: Create narrative layer for all intelligence APIs
2. **Block Language Revolution**: Transform "blocks" → "insights", "ideas", "knowledge pieces"
3. **Confidence Score Humanization**: Transform technical percentages to narrative indicators
4. **Context Items Narrative**: Transform "context_items" → "background", "reference material"

### **Architectural Changes Needed**
1. **Agent Response Coordinator Enhancement**: Make it the primary orchestrator
2. **Narrative Translation Layer**: Insert between raw intelligence and UI components
3. **Progressive Disclosure**: Transform technical analysis into user-friendly insights
4. **Human-Centric Intelligence**: Replace system-centric language with user-centric narratives