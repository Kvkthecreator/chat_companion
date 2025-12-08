# YARNNN Unified Flow: From Input to Intelligence

**Version**: 1.0  
**Status**: Authoritative  
**Purpose**: Single source of truth for the complete YARNNN flow including async agent processing

## 🎯 Core Architecture (Governance-First Evolution)

```
User Input → Immediate Capture → Agent Processing → Proposal Creation → Governance → Substrate → UI Display
    ↓              ↓                    ↓                   ↓            ↓         ↓         ↓
  Frontend    Raw Dumps DB        Async Queue         Proposals    Review     Smart Data  Real-time
```

## 📐 The Two-Path Model

### Path 1: Immediate Response (Synchronous)
```
User → Frontend → Vercel API → fn_ingest_dumps → raw_dumps → Success Response
```
**Time**: <500ms  
**Purpose**: User confirmation, continuity, trust

### Path 2: Intelligence Creation (Governance-Gated)
```
raw_dumps → Queue → Agent Backend → Proposals → Governance Review → Substrate Commitment → Timeline Events → UI Updates
```
**Time**: Agent processing (2-30s) + governance review (variable)  
**Purpose**: Extract meaning, validate quality, govern substrate evolution

## 🔄 Detailed Flow

### Step 1: User Input Capture

**Endpoint**: `POST /api/dumps/new` or `POST /api/baskets/ingest`

**What Happens**:
1. User uploads file or enters text
2. Frontend calls Next.js API route (Vercel)
3. API route validates auth and workspace access
4. Calls `fn_ingest_dumps` RPC with:
   - `basket_id` 
   - `dump_request_id` (for idempotency)
   - `text_dump` or `file_url`
5. Returns immediately with `dump_id`

**Key Point**: No agent processing happens here - just storage

### Step 2: Queue Entry Creation

**Trigger**: Database trigger on `raw_dumps` insert

```sql
CREATE TRIGGER after_dump_insert
AFTER INSERT ON raw_dumps
FOR EACH ROW 
EXECUTE FUNCTION queue_agent_processing();
```

**Queue Entry**:
- `dump_id`: Reference to raw dump
- `basket_id`: Container context
- `processing_state`: 'pending'
- `created_at`: Timestamp

### Step 3: Agent Processing

**Agent Backend** (FastAPI on Render):

1. **Poll Queue** (every 10 seconds):
   ```python
   dumps_to_process = await claim_next_dumps(limit=10)
   ```

2. **Process Each Dump**:
   - Download content from `raw_dumps`
   - Extract blocks (themes, insights, questions)
   - Identify context items (entities, concepts)
   - Map relationships between elements

3. **Create Proposals**:
   ```python
   # Agents create governed proposals instead of direct substrate writes
   validation_report = await validate_operations(ops)
   proposal_id = await supabase.rpc('fn_proposal_create', {
     'ops': ops, 
     'validation_report': validation_report,
     'origin': 'agent'
   })
   ```

4. **Update Queue**:
   - Mark as 'completed'
   - Record processing metadata

### Step 4: Governance Review

**Proposal Queue**:
- Agents submit proposals to governance queue
- Human reviewers see impact analysis and validation reports
- Decisions: APPROVE → commits to substrate | REJECT → proposal archived

### Step 5: Timeline Events

**Governance Event Emission**:
- Proposal approval triggers substrate commitment
- Each committed operation calls `fn_timeline_emit`
- Events flow: `timeline_events` → `events` → subscriptions

**Event Types**:
- `dump.created` - Raw capture complete
- `proposal.submitted` - Agent proposes substrate changes
- `proposal.approved` - Human approves proposal
- `block.created` - Insight committed to substrate
- `context.bulk_tagged` - Entities committed to substrate
- `rel.bulk_upserted` - Connections committed to substrate

### Step 6: UI Updates

**Frontend Subscription**:
```typescript
// Polls every 3 seconds (WebSocket auth issues)
useBasketEvents(basketId) → Updates UI progressively
```

**User Experience**:
1. Immediate: "Upload complete ✓"
2. Processing: "Analyzing content..."
3. Governance: "Proposals ready for review" (with notification)
4. Progressive: Approved blocks/entities appear in substrate
5. Complete: Full graph and relationships visible

## 🏗️ System Components

### Frontend (Vercel)
- **Role**: Fast user interactions, display
- **Does**: Raw dump creation, UI rendering
- **Doesn't**: Agent processing, substrate creation

### Agent Backend (Render)
- **Role**: Intelligence extraction
- **Does**: Process dumps into substrate
- **Doesn't**: Handle user requests directly

### Database (Supabase)
- **Role**: Source of truth, queue, events
- **Does**: Store everything, enforce security
- **Doesn't**: Process or interpret

## 🔐 Security Model

### Workspace Isolation
- Every operation scoped by `workspace_id`
- RLS policies enforce boundaries
- Agents respect workspace context

### RPC Security
```sql
-- Only authenticated users can call
GRANT EXECUTE ON FUNCTION fn_ingest_dumps TO authenticated;

-- Agents use service_role for substrate writes
GRANT EXECUTE ON FUNCTION fn_block_create TO service_role;
```

## 📊 Data Flow Examples

### Example 1: Text Note
```
1. User types "Meeting notes about product roadmap"
2. Frontend → POST /api/dumps/new
3. Stored in raw_dumps
4. Queue entry created
5. Agent extracts:
   - Block: "Product Roadmap Discussion"
   - Context items: "Q2 Planning", "Feature X"
   - Relationships: Roadmap → Features
6. UI shows extracted insights
```

### Example 2: PDF Upload
```
1. User uploads "research_paper.pdf"
2. File → Supabase Storage
3. raw_dumps entry with file_url
4. Agent downloads and processes:
   - Extracts text via PyMuPDF
   - Creates blocks for key findings
   - Maps citation relationships
5. UI displays structured knowledge
```

## ⚡ Performance Characteristics

### Latency
- **Capture**: <500ms (immediate)
- **Agent Processing**: 2-30s (depends on content)
- **UI Update**: 0-3s after processing (polling)

### Throughput
- **Queue Processing**: 10 dumps/batch
- **Agent Instances**: Horizontally scalable
- **Database**: ~1000 ops/second capacity

## 🚨 Critical Rules

### What Frontend CANNOT Do
- Call substrate-writing RPCs directly
- Create blocks, context_items, or relationships
- Synthesize intelligence client-side

### What Agents MUST Do
- Process every raw dump
- Use RPCs for all writes
- Emit proper timeline events
- Respect workspace boundaries

### What the Queue ENSURES
- No dumps are missed
- Failed processing can retry
- Multiple agents can work in parallel
- Processing state is trackable

## 🔧 Implementation Checklist

1. **Database Schema**:
   - [ ] Create `agent_processing_queue` table
   - [ ] Add trigger on `raw_dumps`
   - [ ] Create queue management RPCs

2. **Agent Backend**:
   - [ ] Implement queue polling
   - [ ] Connect to substrate RPCs
   - [ ] Add error handling/retry

3. **Monitoring**:
   - [ ] Queue depth metrics
   - [ ] Processing latency tracking
   - [ ] Failed job alerts

4. **Documentation**:
   - [ ] Update contracts to match RPCs
   - [ ] Document queue states
   - [ ] Create troubleshooting guide

## 📋 Common Issues & Solutions

### "Why don't I see extracted insights?"
- Check if agent backend is running
- Verify queue entries are created
- Look for failed processing states

### "Uploads work but nothing happens"
- Ensure database trigger exists
- Check agent polling is active
- Verify RPC permissions

### "Some content processes, some doesn't"
- Check for specific file type support
- Look for processing errors in queue
- Verify content size limits

## 🎯 Success Criteria

The system is working correctly when:
1. Every raw dump gets a queue entry
2. Agents process queue within 30 seconds
3. Substrate appears in UI progressively
4. No manual intervention required
5. Failed jobs retry automatically

---

**This flow ensures agent intelligence remains mandatory while keeping user experience fast and reliable.**