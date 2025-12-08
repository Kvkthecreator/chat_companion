# YARNNN Testing Ecosystem - Canon-Aligned Structure

This testing ecosystem has been systematically refactored to ensure consistency with the consolidated YARNNN canon documentation (v1.4.0 and Governance v3.0.0).

## 🏛️ Test Organization Structure

### `/canon/` - Core Canon Compliance Tests
Foundational tests that validate adherence to YARNNN's four sacred principles and architectural requirements:

- **`sacredPrinciples.test.ts`** - Tests all Four Sacred Principles enforcement
  - Sacred Principle #1: Capture is Sacred (immutable raw_dumps)
  - Sacred Principle #2: All Substrates are Peers (no hierarchy)
  - Sacred Principle #3: Narrative is Deliberate (composed documents)
  - Sacred Principle #4: Agent Intelligence is Mandatory (required processing)

- **`pipelineBoundaries.test.ts`** - Tests P0→P1→P2→P3→P4 boundary enforcement
  - P0: Capture (writes only raw_dumps)
  - P1: Substrate (creates blocks/items, no relationships)
  - P2: Graph (creates relationships, no content modification)
  - P3: Reflection (read-only computation, optional cache)
  - P4: Presentation (composes narrative, never creates substrate)

- **`substrateEquality.test.ts`** - Tests substrate equality principles
  - Equal treatment of all five substrate types
  - Anti-hierarchy enforcement
  - Equal composition capabilities
  - Type-agnostic operations

- **`setup.ts`** - Canon test utilities and environment setup

### `/governance/` - Workspace-Scoped Governance Tests
Tests for the v3.0.0 workspace-scoped governance system:

- **`workspaceFlags.test.ts`** - Tests workspace-scoped governance flags
- **`changeDescriptor.test.ts`** - Tests unified change abstraction
- **`decisionGateway.test.ts`** - Tests single choke-point for mutations
- **`policyDecider.test.ts`** - Tests centralized routing logic
- **`proposals.test.ts`** - Tests proposal lifecycle and execution
- **`governanceUI.test.tsx`** - Tests governance user interface components

### `/integration/` - End-to-End Workflow Tests
Integration tests that validate complete workflows:

- **`governanceWorkflow.test.ts`** - End-to-end governance workflow validation
- **`completeGovernanceFlow.test.ts`** - Complete canon compliance through governance
- **API route integration tests** - Tests for specific API endpoints

### `/contracts/` - API Contract Tests
Tests ensuring API consistency:

- **`onboarding.test.ts`** - Onboarding flow contracts
- **`substrateReferences.test.ts`** - Substrate reference contracts

### `/unit/` - Unit Tests
Focused unit tests for specific components:

- **`components/`** - Component unit tests
- **`hooks/`** - React hooks unit tests
- **`utils/`** - Utility function tests

## 🎯 Key Testing Principles

### 1. Canon Compliance First
All tests validate adherence to YARNNN canon principles:
- Sacred principles enforcement
- Pipeline boundary respect
- Substrate equality maintenance
- Workspace isolation preservation

### 2. ChangeDescriptor Abstraction
Tests use the unified ChangeDescriptor abstraction instead of legacy API patterns:
```typescript
// ✅ Canon-aligned
const changeDescriptor = createManualEditDescriptor(
  'user-123',
  'workspace-456', 
  'basket-789',
  [{ type: 'CreateBlock', data: { content: 'Goal', semantic_type: 'goal' } }]
);

// ❌ Legacy pattern
const workRequest = {
  basket_id: 'basket-789',
  intent: 'create goal',
  request_id: 'req-123'
};
```

### 3. Workspace-Scoped Testing
All tests respect workspace isolation and use workspace-scoped governance:
```typescript
// ✅ Workspace-scoped governance
const flags = await getWorkspaceFlags(supabase, workspaceId);

// ❌ Global feature flags
const flags = getGovernanceFlags();
```

### 4. Agent Intelligence Integration
Tests validate that agent intelligence is mandatory for substrate operations:
- Validator agent calls for all proposals
- Agent processing queues for raw_dump ingestion
- Intelligence-driven substrate creation

### 5. Real Service Integration
Tests use actual governance services instead of simple mocks:
- Decision Gateway routing
- Policy Decider logic
- Workspace Flags evaluation
- Change Descriptor validation

## 🧪 Running Tests

### Run Canon Compliance Tests
```bash
npm run test:all -- __tests__/canon/
```

### Run Governance Tests
```bash
npm run test:all -- __tests__/governance/
```

### Run Integration Tests
```bash
npm run test:integration
```

### Run All Tests
```bash
npm run test:all
```

## 📋 Test Coverage Areas

### Critical Test Files Added
1. **Sacred Principles Enforcement** - Validates core YARNNN philosophy
2. **Pipeline Boundaries** - Ensures strict P0→P1→P2→P3→P4 separation
3. **Substrate Equality** - Prevents substrate type hierarchies
4. **Workspace Flags** - Tests v3.0.0 workspace-scoped governance

### Updated for Canon Consistency
1. **API Client Tests** - Now use ChangeDescriptor abstraction
2. **Governance Tests** - Updated to use workspace-scoped flags
3. **Integration Tests** - Added complete workflow validation

### Redundant Tests Removed
1. **Obsolete Feature Flags** - Replaced with workspace-scoped governance
2. **Legacy API Patterns** - Updated to use canon-aligned abstractions

## 🛡️ Quality Assurance

### Pre-Commit Validation
Tests validate:
- Sacred principles compliance
- Pipeline boundary respect
- Substrate equality maintenance
- Governance workflow integrity
- Workspace isolation preservation

### Canon Version Alignment
- Tests align with YARNNN Canon v1.4.0
- Governance tests align with v3.0.0 specification
- All tests respect workspace-scoped architecture

---

*This testing ecosystem ensures that all code changes maintain strict adherence to YARNNN canon principles while providing comprehensive coverage of the governance system.*