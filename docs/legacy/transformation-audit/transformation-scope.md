# Canon v1.3.1 — docs clarification (no code change)
Aligns reflections (derived + optional cache), sacred write path endpoints, DTO wording (file_url), schema term context_blocks, basket lifecycle, and event tokens.

# Complete Transformation Scope

## Executive Summary

**Narrative Intelligence Transformation requires systematic changes across 3 layers:**
1. **Agent Layer**: Add narrative wrappers to intelligence APIs
2. **Frontend Layer**: Replace technical substrate vocabulary with user-centric language
3. **Layout Layer**: Implement progressive disclosure and narrative navigation

**Impact Scale**: 47 files requiring changes, 23 high-priority, 24 medium-priority
**Risk Level**: Medium - Well-defined component boundaries enable safe incremental transformation
**Timeline Estimate**: 3 phases over 4-6 weeks

---

## Agent Architecture Transformation

### **Immediate Changes Required (High Priority)**

#### **API Narrative Wrappers**
```typescript
// Files requiring narrative layer addition:
- app/api/intelligence/basket/[basketId]/dashboard/route.ts ❌ TECHNICAL
- app/api/intelligence/basket/[basketId]/comprehensive/route.ts ❌ TECHNICAL  
- app/api/intelligence/process-content/route.ts ❌ TECHNICAL
- app/api/intelligence/workspace/new/route.ts ❌ TECHNICAL

// Transform to:
+ app/api/intelligence/narrative/[basketId]/insights/route.ts ✅ NARRATIVE
+ app/api/intelligence/narrative/[basketId]/understanding/route.ts ✅ NARRATIVE
```

#### **Intelligence Hook Transformations**
```typescript
// Current technical hooks:
- lib/intelligence/useBasketIntelligence.ts → Expose raw analysis objects
- lib/intelligence/useContextualAgentResponse.ts → Technical coordination
- lib/intelligence/agentResponseCoordinator.ts → System-centric language

// Transform to narrative hooks:
+ lib/intelligence/narrative/useProjectUnderstanding.ts
+ lib/intelligence/narrative/useAIAssistant.ts  
+ lib/intelligence/narrative/useIntelligentGuidance.ts
```

### **Response Format Transformation**
```typescript
// BEFORE: Technical substrate exposure
interface ThematicAnalysis {
  analysis_id: string;
  confidence: number;
  theme_distribution: Record<string, number>;
}

// AFTER: Narrative intelligence format
interface ProjectUnderstanding {
  insight: string; // "I can see you're working on..."
  themes: string[]; // Human-readable themes
  nextSteps: string[]; // "Consider adding...", "Try exploring..."
  confidence: "learning" | "understanding" | "deep_insight"; // Narrative levels
}
```

---

## Frontend Language Revolution

### **Critical Vocabulary Transformations**

#### **Block (**context_block**) → Knowledge Transformation**
```typescript
// 🔥 HIGH PRIORITY - User-facing CRUD operations
❌ "Create Block" → ✅ "Capture Insight"
❌ "Edit Block" → ✅ "Refine Idea"  
❌ "Delete Block" → ✅ "Remove Knowledge"
❌ "No proposed blocks yet" → ✅ "No insights captured yet"
❌ "Block type" → ✅ "Type of insight"

// Files requiring immediate transformation:
- components/blocks/BlockCreateModal.tsx
- components/blocks/BlocksPane.tsx
- components/blocks/CoreBlockForm.tsx
- components/work/BlocksList.tsx
```

#### **Intelligence → Understanding Transformation**
```typescript
// 🔥 HIGH PRIORITY - User-facing intelligence language
❌ "Confidence: 75%" → ✅ "Strong understanding of your project"
❌ "Analysis ID" → ✅ Remove from UI entirely
❌ "Thematic Analysis" → ✅ "Project Understanding"
❌ "Document Relationships" → ✅ "Content Connections"

// Files requiring immediate transformation:
- components/baskets/MemoryEvolution.tsx (partially done)
- components/ui/IntelligenceIndicators.tsx
- components/intelligence/* (various)
```

#### **Context → Background Transformation**
```typescript
// 🟡 MEDIUM PRIORITY - Supporting vocabulary
❌ "Context Items" → ✅ "Background Information"
❌ "Add Context" → ✅ "Add Reference"
❌ "Context Panel" → ✅ "Project Background"

// Files requiring medium-priority transformation:
- components/context/ContextPanel.tsx
- components/context/ContextItemEditor.tsx
```

### **Component-by-Component Changes**

#### **High Priority (Week 1-2)**
| Component | Current Issue | Transformation Required |
|-----------|---------------|------------------------|
| `BlockCreateModal.tsx` | "Create Block" modal | → "Capture Insight" interface |
| `BlocksPane.tsx` | "No proposed blocks" | → "No insights captured yet" |
| `MemoryEvolution.tsx` | Technical confidence % | → Narrative progress indicators |
| `IntelligenceIndicators.tsx` | System metrics | → Human-readable progress |

#### **Medium Priority (Week 3-4)**  
| Component | Current Issue | Transformation Required |
|-----------|---------------|------------------------|
| `ContextPanel.tsx` | "Context Items" | → "Background Information" |
| `BasketWorkLayout.tsx` | Technical tab names | → Narrative navigation |
| `LiveThinkingPartner.tsx` | Mixed technical language | → Pure narrative |
| `DocumentIntelligenceLayer.tsx` | Technical overlays | → Contextual assistance |

---

## Layout Progressive Disclosure

### **Layout Evolution Phases**

#### **Phase 1: Focus Mode (Default for New Users)**
```tsx
// Single-panel layout with progressive intelligence discovery
<Layout mode="focus">
  <MainContent width="100%" />
  <AIAssistant 
    trigger="contextual" 
    appearance="bottom-sheet" 
    disclosure="progressive"
  />
</Layout>
```

#### **Phase 2: Enhanced Mode (Progressive Users)**
```tsx
// Two-panel with contextual intelligence
<Layout mode="enhanced">
  <MainContent width="75%" />
  <IntelligencePanel 
    width="25%" 
    mode="contextual"
    showWhen="user_engaged"
  />
</Layout>
```

#### **Phase 3: Advanced Mode (Power Users)**
```tsx  
// Full three-panel for users who discovered all features
<Layout mode="advanced">
  <Navigation width="20%" />
  <MainContent width="60%" />
  <IntelligencePanel width="20%" mode="always_visible" />
</Layout>
```

### **Navigation Narrative Transformation**
```typescript
// Current technical navigation:
❌ "Dashboard" → ✅ "Project Overview"
❌ "Insights" → ✅ "AI Understanding" 
❌ "Brain Sidebar" → ✅ "AI Assistant"
❌ "Context Panel" → ✅ "Background"
❌ "Memory Evolution" → ✅ "Learning Progress"
```

---

## Implementation Roadmap

### **Week 1-2: Agent Narrative Layer**
- [ ] Create narrative API wrappers for intelligence endpoints
- [ ] Transform response formats from technical to narrative
- [ ] Update intelligence hooks to use narrative APIs
- [ ] Test backward compatibility with existing components

### **Week 3-4: Frontend Language Revolution**  
- [ ] Transform all block-related components and language
- [ ] Update intelligence display components to narrative format
- [ ] Replace technical confidence scoring with narrative indicators
- [ ] Update CRUD operations to narrative actions

### **Week 5-6: Layout Progressive Disclosure**
- [ ] Implement focus mode as default layout
- [ ] Create progressive intelligence discovery patterns  
- [ ] Add contextual AI assistant with bottom-sheet mobile behavior
- [ ] Update navigation to narrative language

---

## Risk Assessment & Mitigation

### **High Risk Areas**
1. **API Response Breaking Changes**: Narrative wrappers might break existing integrations
   - **Mitigation**: Maintain both technical and narrative APIs during transition
2. **User Flow Disruption**: Block terminology deeply embedded in user mental models
   - **Mitigation**: Progressive rollout with user feedback collection
3. **Component Dependencies**: Shared utilities between technical and narrative components
   - **Mitigation**: Create adapter patterns and gradual migration

### **Medium Risk Areas**  
1. **Performance Impact**: Additional narrative transformation layer
   - **Mitigation**: Cache narrative transformations, optimize API responses
2. **Mobile Layout Changes**: Progressive disclosure might confuse existing mobile users
   - **Mitigation**: A/B testing and opt-in advanced modes

### **Low Risk Areas**
1. **Internal Technical Language**: Backend services and internal APIs
   - **Strategy**: Keep technical for developers, transform only user-facing language
2. **Database Schema**: Underlying data models
   - **Strategy**: No schema changes required, only presentation layer transformation

---

## Success Metrics

### **User Experience Metrics**
- **Language Clarity**: User comprehension testing of new vocabulary
- **Feature Discovery**: Progressive disclosure effectiveness measurement  
- **Task Completion**: CRUD operations with narrative language
- **AI Understanding**: User comfort with narrative intelligence presentation

### **Technical Metrics**
- **API Response Time**: Ensure narrative wrappers don't slow performance
- **Component Reusability**: Maintain or improve component modularity
- **Backward Compatibility**: Zero breaking changes during transition
- **Code Coverage**: Maintain test coverage through transformation

### **Business Metrics**
- **User Engagement**: Increased usage of intelligence features
- **Feature Adoption**: Progressive disclosure improves feature discovery
- **User Retention**: Narrative interface reduces confusion and abandonment
- **Support Requests**: Decreased confusion-related support tickets

---

## Next Steps

1. **Approve transformation scope and timeline**
2. **Begin Phase 1: Agent narrative layer implementation**
3. **Create user testing plan for vocabulary changes**
4. **Set up metrics collection for transformation impact**
5. **Plan progressive rollout strategy with feature flags**