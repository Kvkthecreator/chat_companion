# YARNNN Contract Alignment Guide

**Version**: 1.0  
**Status**: Implementation Guide  
**Purpose**: Align shared contracts with RPC function expectations

## 🎯 The Problem

During the Supabase RPC migration, contracts diverged:
- `/shared/contracts` - Original TypeScript interfaces
- RPC functions - Expect different field names (snake_case, different naming)
- API routes - Mix of both conventions

## 📐 The Solution

**Update shared contracts to match RPC reality** (one-time alignment)

## 🔄 Contract Mappings

### Context Items

**Current Mismatch**:
```typescript
// shared/contracts expects:
{ context_type, content_text }

// RPC expects:
{ kind, label }

// Frontend sends:
{ type, content }
```

**Alignment**:
```typescript
// Update shared/contracts/context.ts
export interface ContextItem {
  kind: 'theme' | 'question' | 'entity' | 'cue';  // was: context_type/type
  label: string;                                   // was: content_text/content
  metadata?: Record<string, unknown>;
}
```

### Blocks

**Current Mismatch**:
```typescript
// Various names used:
{ context_blocks, blocks, substrate_blocks }
```

**Alignment**:
```typescript
// Update shared/contracts/blocks.ts
export interface Block {
  id: string;
  basket_id: string;
  title: string;
  content?: string;
  semantic_type: 'insight' | 'theme' | 'question';
  state: 'proposed' | 'accepted' | 'rejected';
  confidence_score?: number;
}
```

### Raw Dumps

**Current Mismatch**:
```typescript
// Frontend sends:
{ body_md, file_refs }

// RPC expects:
{ text_dump, file_url }
```

**Alignment**:
```typescript
// Update shared/contracts/dumps.ts
export interface CreateDumpPayload {
  basket_id: string;
  dump_request_id: string;
  text_dump?: string;      // was: body_md
  file_url?: string;       // was: file_refs
  metadata?: Record<string, unknown>;
}
```

## 📋 Implementation Checklist

### Phase 1: Contract Updates (30 min)
- [ ] Update `/shared/contracts/context.ts` - Match RPC field names
- [ ] Update `/shared/contracts/blocks.ts` - Consistent naming
- [ ] Update `/shared/contracts/dumps.ts` - Align with RPCs
- [ ] Update `/shared/contracts/relationships.ts` - Graph terminology

### Phase 2: Frontend Updates (1 hour)
- [ ] Find/replace old field names in components
- [ ] Update API client calls to use new contracts
- [ ] Test onboarding flow with aligned fields

### Phase 3: Agent Updates (30 min)
- [ ] Update agent services to use aligned contracts
- [ ] Ensure agents call RPCs with correct field names
- [ ] Test agent processing with new contracts

## 🚨 Critical Fields to Update

### In API Routes
```typescript
// Before
const { context_type, content_text } = req.body;

// After
const { kind, label } = req.body;
```

### In Frontend Components
```typescript
// Before
<div>{item.context_type}: {item.content_text}</div>

// After
<div>{item.kind}: {item.label}</div>
```

### In Agent Processing
```typescript
// Before
await supabase.from('context_items').insert({
  context_type: 'theme',
  content_text: 'Product roadmap'
});

// After
await supabase
  .from('context_items')
  .insert({
    type: 'theme',
    title: 'Product roadmap',
    content: 'Product roadmap',
    normalized_label: 'product roadmap',
    state: 'ACTIVE',
    status: 'active',
  });
```

## ✅ Validation

After alignment, these should all match:
1. TypeScript interfaces in `/shared/contracts`
2. Insert payloads used by backend services
3. Frontend component prop usage
4. Agent/service calls

## 🎯 End Goal

One source of truth where:
- Frontend uses contracts directly
- Agents use contracts to build RPC parameters
- No field name translation needed
- Type safety throughout the stack

---

**This one-time alignment eliminates ongoing confusion and makes the codebase maintainable.**
