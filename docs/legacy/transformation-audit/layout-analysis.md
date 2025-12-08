# Layout Structure Analysis

## Current Panel Architecture

### **Three-Panel Layout System**
- **components/responsive/ResponsiveThreePanelLayout.tsx**:
  - Panels with priority system: 1 = main content, 2 = secondary navigation, 3 = tertiary intelligence
  - Responsive collapse behavior: desktop → tablet → mobile
  - Panel switching on mobile/tablet

- **components/basket/StandardizedBasketLayout.tsx**:
  - Left panel: Navigation/documents
  - Main content: Primary work area  
  - Right panel: Intelligence/brain sidebar
  - Context types: `dashboard`, `document`, `settings`, `insights`

### **Current Panel Distribution**
```tsx
interface Panel {
  id: string;
  priority: number; // Attention hierarchy
  content: ReactNode;
  title: string;
  icon: string;
}
```

## Attention Distribution Patterns

### **Desktop Layout (Current)**
```
┌─────────────┬──────────────────────┬─────────────┐
│   Left      │    Main Content      │   Right     │
│   Panel     │    (Priority 1)      │   Panel     │
│ (Priority 2)│        60%           │(Priority 3) │
│    20%      │                      │    20%      │
└─────────────┴──────────────────────┴─────────────┘
```

### **Current Responsive Behavior**
- **Desktop**: Three panels visible, equal distribution
- **Tablet**: Main + one secondary panel (collapsible)
- **Mobile**: Single panel with tab switching

### **Attention Problems Identified**
1. **Intelligence panel competes with main content**
2. **Equal visual weight given to all panels**
3. **No progressive disclosure - everything visible at once**
4. **Technical brain sidebar exposed by default**

## Layout Components Analysis

### **StandardizedBasketLayout.tsx**
- **Good**: Contextual intelligence modes (`ambient`, `active`, `detailed`)
- **Problem**: Intelligence always visible in right panel
- **Need**: Progressive disclosure pattern
- **Status**: Core layout that needs transformation

### **BasketWorkLayout.tsx**
- **Good**: Tab-based content switching (`dashboard`, `insights`, `history`)
- **Problem**: Technical tab names
- **Need**: Narrative tab labeling
- **Status**: Secondary layout, moderate priority

### **ResponsiveThreePanelLayout.tsx**
- **Good**: Responsive design patterns
- **Problem**: Fixed three-panel assumption
- **Need**: Dynamic panel system based on user progression
- **Status**: Utility component, needs enhancement

## Navigation Patterns

### **Current Navigation Structure**
- Tab-based switching in main layout
- Sidebar navigation for documents/baskets
- Brain sidebar for intelligence features
- Mobile hamburger menu for panel switching

### **Navigation Language Issues**
- "Dashboard" → Technical terminology
- "Insights" → Good narrative term
- "Brain Sidebar" → Technical system language
- "Context Panel" → Technical substrate language

## Responsive Layout Issues

### **Mobile Experience Problems**
1. **Panel switching confusion**: Users don't understand panel hierarchy
2. **Intelligence hidden**: Brain sidebar not discoverable on mobile
3. **Context switching cost**: Too much navigation between panels

### **Tablet Experience Problems**
1. **Awkward two-panel distribution**: Either 50/50 or collapsing
2. **Intelligence competes**: Right panel gets equal visual weight
3. **No progressive disclosure**: All features visible immediately

## Layout Transformation Requirements

### **High Priority Changes**

#### **1. Progressive Disclosure Layout**
```tsx
// Instead of fixed three panels:
Layout Modes:
- "Focus": Main content only (new users)
- "Enhanced": Main + contextual intelligence (progressive)
- "Advanced": Full three-panel (power users)
```

#### **2. Narrative Navigation**
```tsx
// Current technical navigation:
"Dashboard" → "Project Overview"
"Insights" → "Intelligence" 
"Brain Sidebar" → "AI Assistant"
"Context Panel" → "Project Background"
```

#### **3. Attention Hierarchy**
```
┌─────────────────────────────────────────┬─────────────┐
│           Main Content                  │   AI        │
│           (Priority 1)                  │  Assistant  │
│              80%                        │ (Priority 2)│
│                                         │    20%      │
│                                         │ (Contextual)│
└─────────────────────────────────────────┴─────────────┘
```

### **Medium Priority Changes**

#### **1. Contextual Intelligence Panels**
- Intelligence appears based on user actions
- Progressive disclosure of AI capabilities
- Contextual intelligence suggestions

#### **2. Mobile-First Intelligence**
- Bottom sheet intelligence on mobile
- Swipe gestures for intelligence access
- Floating action button for AI assistant

#### **3. Smart Panel Management**
- Automatic panel showing/hiding based on context
- User preference learning for panel usage
- Adaptive layout based on screen size and usage patterns

### **Low Priority Changes**

#### **1. Animation Enhancements**
- Smooth panel transitions
- Intelligence fade-in/fade-out
- Progressive disclosure animations

#### **2. Accessibility Improvements**
- Keyboard navigation between panels
- Screen reader optimization
- Focus management improvements

## Recommended Layout Evolution

### **Phase 1: Single-Panel Focus Mode**
- Default to main content only
- Progressive intelligence discovery
- Contextual AI assistant appearance

### **Phase 2: Adaptive Panel System**
- Dynamic panel showing based on user progression
- Smart contextual intelligence
- Narrative navigation labels

### **Phase 3: Advanced Layout Modes**
- User-customizable layouts
- Panel preferences and learning
- Advanced responsive behaviors

## Technical Implementation Notes

### **Components Requiring Changes**
1. **StandardizedBasketLayout.tsx** - Core layout transformation
2. **ResponsiveThreePanelLayout.tsx** - Dynamic panel system
3. **BasketWorkLayout.tsx** - Narrative navigation
4. **ContextualBrainSidebar.tsx** - Progressive intelligence

### **New Components Needed**
1. **ProgressiveDisclosureLayout.tsx** - New primary layout
2. **ContextualIntelligencePanel.tsx** - Smart AI assistant panel
3. **NarrativeNavigation.tsx** - User-friendly navigation
4. **AdaptiveLayoutManager.tsx** - Smart layout decisions

### **Backward Compatibility Considerations**
- Maintain existing layout component APIs
- Progressive migration path for existing layouts
- Fallback to current layout for unsupported features