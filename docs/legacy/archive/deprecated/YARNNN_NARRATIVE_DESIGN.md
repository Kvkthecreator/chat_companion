# Narrative Design System

## Overview

The Narrative Design System transforms technical substrate language into conversational, AI-partnership language throughout the application. This system eliminates technical vocabulary and creates a natural, supportive user experience that feels like working with an intelligent strategic partner.

## Core Principles

### 1. Substrate Vocabulary Elimination

**Prohibited Terms:**
- Technical: `blocks`, `context items`, `metadata`, `CRUD operations`
- System: `algorithm`, `processing`, `execution`, `functions`
- Data: `confidence scores`, `datasets`, `analytics`, `calculations`
- UI: `components`, `widgets`, `forms`, `dropdowns`

**Narrative Replacements:**
- `blocks` → `insights` or `ideas`
- `context items` → `project knowledge`
- `confidence score` → `understanding level`
- `create/edit/delete` → `capture/refine/remove`
- `analysis` → `discoveries` or `understanding`

### 2. AI Voice Consistency

**Required Patterns:**
- First-person AI perspective: "I can see...", "I understand...", "I know..."
- Collaborative language: "we can...", "let's...", "together we..."
- Human-centered focus: "your project", "your goals", "your work"
- Supportive tone: "help you", "support your", "guide you"

**Avoid:**
- Third-person system language: "the system", "the algorithm", "the AI"
- Technical process language: "execute", "process", "compute"
- Transactional language: "operation", "transaction", "function"

### 3. Progressive Disclosure

**Three Levels:**
1. **Story**: Natural, conversational narrative (default)
2. **Reasoning**: "How I know this" - methodology explanation
3. **Substrate**: Technical details and raw data (power users only)

## Component Patterns

### StrategicActions Component

**Purpose:** Transform technical CRUD actions into narrative partnership actions.

**Language Patterns:**
```typescript
// Technical (Avoid)
const technicalActions = [
  { type: 'create_block', label: 'Create Block' },
  { type: 'edit_context', label: 'Edit Context Item' },
  { type: 'run_analysis', label: 'Execute Analysis' }
];

// Narrative (Use)
const narrativeActions = [
  { type: 'capture_insight', label: 'Capture New Insight' },
  { type: 'share_knowledge', label: 'Share Your Knowledge' },
  { type: 'explore_discoveries', label: 'Explore My Discoveries' }
];
```

**Implementation:**
```typescript
<ProgressiveDisclosure
  story="I can see some clear next steps that would help move your project forward"
  reasoning="Based on what you've shared so far, these actions align with your goals..."
  substrate={{ actions, actionTypes, enabledCount }}
>
  <ActionButtons />
</ProgressiveDisclosure>
```

### StrategicUnderstanding Component

**Purpose:** Present AI understanding in conversational, confidence-building language.

**Language Transformation:**
```typescript
// Technical confidence (Avoid)
"Confidence: 87% | Themes Found: 5 | Analysis Complete"

// Narrative understanding (Use)  
"I have a strong understanding of your project direction and goals"
```

**Key Features:**
- Transforms confidence scores to narrative levels
- Converts technical themes to human-readable insights
- Uses encouraging, supportive language
- Progressive disclosure of technical details

### ProjectContext Component

**Purpose:** Transform "context items" into "project knowledge" with collaborative language.

**Language Patterns:**
```typescript
// Technical (Avoid)
"Context Items (12)" 
"Metadata: Updated 2 hours ago"
"Semantic Type: Document"

// Narrative (Use)
"What I Know About Your Project"
"Knowledge: Updated 2 hours ago" 
"Type: Document"
```

### InsightRefinement Component

**Purpose:** Replace technical "block creation" with conversational insight capture.

**Design Elements:**
- Natural language form labels
- Conversational placeholders
- Insight type badges with emojis
- Narrative confirmation messaging

## Navigation Transformation

### Navigation Labels

```typescript
const NARRATIVE_NAVIGATION = {
  'Dashboard': 'Strategic Intelligence',
  'Blocks': 'Insights & Ideas',
  'Context': 'My Understanding',
  'Memory': 'Project Knowledge', 
  'Analysis': 'Strategic Planning',
  'History': 'Evolution'
};
```

### Usage Example

```typescript
<NarrativeNavigation 
  basketId={basketId}
  useNarrativeLabels={true}
  showDescriptions={true}
  variant="tabs"
/>
```

## Progressive Disclosure Implementation

### Basic Pattern

```typescript
<ProgressiveDisclosure
  story={conversationalContent}
  reasoning={methodologyExplanation}
  substrate={technicalData}
>
  {childComponents}
</ProgressiveDisclosure>
```

### Level Guidelines

**Story Level (Default):**
- Conversational, encouraging language
- Focus on outcomes and benefits
- Hide technical complexity
- Use first-person AI voice

**Reasoning Level:**
- Explain methodology and approach
- Show thinking process
- Maintain conversational tone
- Bridge story and technical

**Substrate Level:**
- Raw data and technical details
- Preserve full information
- For power users and debugging
- Clearly separated from narrative

## Theme Transformation

### Technical to Narrative Themes

```typescript
const themeTransformations = {
  'api_development': 'Technical Architecture',
  'user_interface': 'User Experience Design',
  'data_processing': 'Data Strategy',
  'business_logic': 'Business Strategy',
  'authentication': 'Security & Access',
  'performance_optimization': 'System Performance'
};
```

### Visual Representation

```typescript
<Badge variant="secondary" className="bg-primary/10 text-primary">
  <span className="text-xs mr-1">💡</span>
  {narrativeTheme}
</Badge>
```

## Language Validation

### Validation Rules

1. **Zero Substrate Vocabulary**: No technical terms in user-facing text
2. **Consistent AI Voice**: First-person perspective throughout
3. **Collaborative Language**: Partnership-focused actions
4. **Progressive Complexity**: Appropriate detail level for context

### Validation Tools

```typescript
import { narrativeValidator } from '@/lib/narrative/validation/narrativeValidation';

// Validate component props
const result = narrativeValidator.validateComponentProps(props, 'StrategicActions');

// Validate text content
const textResult = narrativeValidator.validateText(content, 'button.label');

// Check compliance
const isCompliant = result.isValid && result.score > 80;
```

## Accessibility Considerations

### Screen Reader Experience

- Use semantic HTML structure
- Provide clear heading hierarchy
- Include ARIA labels for disclosure states
- Ensure logical reading order

### Keyboard Navigation

- All interactive elements accessible via keyboard
- Proper focus management in progressive disclosure
- Tab order follows logical flow

### Visual Design

- Sufficient color contrast for all themes
- Clear visual hierarchy between disclosure levels
- Responsive design maintains accessibility

## Testing Guidelines

### Language Transformation Tests

```typescript
describe('Narrative Language', () => {
  test('eliminates all substrate vocabulary', () => {
    expect(screen.queryByText(/blocks?/i)).toBeNull();
    expect(screen.queryByText(/confidence.*score/i)).toBeNull();
  });

  test('uses consistent AI voice', () => {
    expect(screen.getByText(/I can see/i)).toBeInTheDocument();
    expect(screen.getByText(/we can do/i)).toBeInTheDocument();
  });
});
```

### Progressive Disclosure Tests

```typescript
test('reveals reasoning on user request', async () => {
  fireEvent.click(screen.getByRole('button', { name: /how I know/i }));
  await waitFor(() => {
    expect(screen.getByText(mockReasoning)).toBeInTheDocument();
  });
});
```

### User Experience Tests

```typescript
test('creates strategic partnership feeling', () => {
  expect(screen.getByText(/what we can do next/i)).toBeInTheDocument();
  expect(screen.queryByText(/execute.*operation/i)).toBeNull();
});
```

## Implementation Checklist

### Component Development

- [ ] Use ProgressiveDisclosure for complex components
- [ ] Transform all technical language to narrative
- [ ] Include appropriate AI voice patterns
- [ ] Provide encouraging, supportive messaging
- [ ] Implement proper accessibility features

### Language Review

- [ ] Zero substrate vocabulary violations
- [ ] Consistent first-person AI voice
- [ ] Collaborative partnership language
- [ ] Natural, conversational tone
- [ ] Progressive complexity appropriate to context

### Testing Coverage

- [ ] Language transformation validation
- [ ] Progressive disclosure functionality
- [ ] Accessibility compliance
- [ ] User experience flow testing
- [ ] API integration with narrative formatting

## Future Enhancements

### Adaptive Language

- Personalize AI voice based on user preferences
- Adjust complexity level based on user expertise
- Context-aware language adaptation

### Intelligent Assistance

- Proactive narrative guidance
- Smart action suggestions
- Contextual help integration

### Advanced Progressive Disclosure

- Animated transitions between levels
- Personalized default levels
- Smart level recommendations

This design system ensures consistent narrative transformation throughout the application, creating a natural, supportive AI partnership experience while maintaining full functionality for power users through progressive disclosure.