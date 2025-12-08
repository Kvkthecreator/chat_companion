# YARNNN Async Intelligence Framework

**Version**: 2.0  
**Status**: Canon Extension  
**Purpose**: Define the pure Supabase async processing model that bridges user experience with agent intelligence

## 🎯 First Principle

**User experience is immediate. Intelligence arrives when ready.**

This principle resolves the tension between:
- Users need instant feedback (human psychology)
- Agents need time to think (computational reality)

## 🏗️ Architecture Overview

### The Queue Model

```sql
-- The bridge between capture and intelligence
CREATE TABLE agent_processing_queue (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  dump_id uuid REFERENCES raw_dumps(id) NOT NULL,
  basket_id uuid REFERENCES baskets(id) NOT NULL,
  workspace_id uuid REFERENCES workspaces(id) NOT NULL,
  processing_state processing_state DEFAULT 'pending',
  claimed_at timestamp,
  claimed_by text,
  completed_at timestamp,
  attempts int DEFAULT 0,
  error_message text,
  created_at timestamp DEFAULT now(),
  
  -- Indexes for efficient polling
  INDEX idx_queue_state_created (processing_state, created_at),
  INDEX idx_queue_workspace (workspace_id, processing_state)
);

-- Processing states
CREATE TYPE processing_state AS ENUM (
  'pending',      -- Waiting for agent
  'claimed',      -- Agent has claimed
  'processing',   -- Actively processing
  'completed',    -- Successfully processed
  'failed'        -- Failed (will retry)
);
```

### The Trigger

```sql
-- Automatic queue entry on dump creation
CREATE OR REPLACE FUNCTION queue_agent_processing() 
RETURNS trigger AS $$
BEGIN
  INSERT INTO agent_processing_queue (
    dump_id, 
    basket_id, 
    workspace_id
  )
  SELECT 
    NEW.id,
    NEW.basket_id,
    b.workspace_id
  FROM baskets b
  WHERE b.id = NEW.basket_id;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_dump_insert
AFTER INSERT ON raw_dumps
FOR EACH ROW 
EXECUTE FUNCTION queue_agent_processing();
```

## 🤖 Agent Backend Integration

### Queue Claim Mechanism

```sql
-- Atomic claim to prevent duplicate processing
CREATE OR REPLACE FUNCTION fn_claim_next_dumps(
  p_worker_id text,
  p_limit int DEFAULT 10,
  p_stale_after_minutes int DEFAULT 5
) RETURNS SETOF agent_processing_queue AS $$
BEGIN
  RETURN QUERY
  UPDATE agent_processing_queue
  SET 
    processing_state = 'claimed',
    claimed_at = now(),
    claimed_by = p_worker_id
  WHERE id IN (
    SELECT id 
    FROM agent_processing_queue
    WHERE processing_state = 'pending'
       OR (processing_state = 'claimed' 
           AND claimed_at < now() - interval '1 minute' * p_stale_after_minutes)
    ORDER BY created_at
    LIMIT p_limit
    FOR UPDATE SKIP LOCKED  -- Critical: prevents race conditions
  )
  RETURNING *;
END;
$$ LANGUAGE plpgsql;
```

### Agent Processing Loop

```python
# Agent backend service (FastAPI) - Pure Supabase Architecture
class AgentProcessor:
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        # Uses SUPABASE_SERVICE_ROLE_KEY for backend operations
        self.supabase = create_service_role_client()  # No DATABASE_URL needed
    
    async def run_forever(self):
        """Main processing loop"""
        while True:
            try:
                # Claim work
                dumps = await self.claim_dumps()
                
                # Process each dump
                for dump_entry in dumps:
                    await self.process_dump(dump_entry)
                    
            except Exception as e:
                logger.error(f"Processing error: {e}")
                
            # Wait before next poll
            await asyncio.sleep(10)
    
    async def claim_dumps(self):
        """Atomically claim dumps from queue"""
        result = await self.supabase.rpc(
            'fn_claim_next_dumps',
            {
                'p_worker_id': self.worker_id,
                'p_limit': 10
            }
        ).execute()
        return result.data or []
    
    async def process_dump(self, queue_entry):
        """Process a single dump through all pipelines"""
        dump_id = queue_entry['dump_id']
        
        try:
            # Mark as processing
            await self.update_queue_state(queue_entry['id'], 'processing')
            
            # Get dump content
            dump = await self.fetch_dump(dump_id)
            
            # P1: Extract substrate
            blocks = await self.extract_blocks(dump)
            context_items = await self.extract_context_items(dump)
            
            # P2: Map relationships
            relationships = await self.map_relationships(
                dump_id, blocks, context_items
            )
            
            # P3: Reflections computed on-read (not stored)
            # Skip as per canon - reflections are derived
            
            # Mark complete
            await self.update_queue_state(queue_entry['id'], 'completed')
            
        except Exception as e:
            # Mark failed for retry
            await self.update_queue_failed(
                queue_entry['id'], 
                str(e),
                queue_entry['attempts'] + 1
            )
```

### Pipeline Integration

```python
async def extract_blocks(self, dump):
    """P1: Extract structured insights"""
    # Use DumpInterpreterService
    insights = await self.interpreter.extract_insights(dump['body_md'])
    
    # Create blocks via RPC
    for insight in insights:
        await self.supabase.rpc('fn_block_create', {
            'p_basket_id': dump['basket_id'],
            'p_title': insight.title,
            'p_content': insight.content,
            'p_semantic_type': insight.type,
            'p_confidence_score': insight.confidence
        }).execute()
    
    return insights

async def extract_context_items(self, dump):
    """P1: Extract entities and concepts"""
    # Entity recognition
    entities = await self.extractor.extract_entities(dump['body_md'])
    
    # Bulk create via direct insert (service role)
    if entities:
        payload = [
            {
                'basket_id': dump['basket_id'],
                'type': e.type,
                'title': e.name,
                'content': e.name,
                'metadata': e.metadata,
                'normalized_label': e.name.lower(),
                'state': 'ACTIVE',
                'status': 'active'
            }
            for e in entities
        ]
        await self.supabase.table('context_items').insert(payload).execute()
    
    return entities
```

## 📊 Monitoring & Operations

### Key Metrics

```sql
-- Queue health view
CREATE VIEW queue_health AS
SELECT 
  processing_state,
  COUNT(*) as count,
  AVG(EXTRACT(epoch FROM (now() - created_at))) as avg_age_seconds,
  MAX(EXTRACT(epoch FROM (now() - created_at))) as max_age_seconds
FROM agent_processing_queue
GROUP BY processing_state;

-- Processing performance
CREATE VIEW processing_performance AS
SELECT 
  DATE_TRUNC('hour', completed_at) as hour,
  COUNT(*) as completed,
  AVG(EXTRACT(epoch FROM (completed_at - created_at))) as avg_duration_seconds,
  MAX(attempts) as max_attempts
FROM agent_processing_queue
WHERE processing_state = 'completed'
  AND completed_at > now() - interval '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

### Operational Queries

```sql
-- Stuck jobs
SELECT * FROM agent_processing_queue
WHERE processing_state = 'claimed' 
  AND claimed_at < now() - interval '10 minutes';

-- Failed jobs needing attention
SELECT * FROM agent_processing_queue
WHERE processing_state = 'failed'
  AND attempts >= 3;

-- Queue depth by workspace
SELECT 
  w.name as workspace,
  COUNT(*) as pending_dumps
FROM agent_processing_queue q
JOIN workspaces w ON q.workspace_id = w.id
WHERE q.processing_state = 'pending'
GROUP BY w.name
ORDER BY pending_dumps DESC;
```

## 🎭 User Experience Patterns

### Progressive Enhancement

1. **Immediate State**: 
   ```
   ✓ Upload complete
   📄 research_paper.pdf (2.3 MB)
   ⏳ Analyzing content...
   ```

2. **Early Results** (5-10s):
   ```
   ✓ Upload complete
   📄 research_paper.pdf (2.3 MB)
   📊 Found 3 key themes
   🔄 Extracting relationships...
   ```

3. **Complete Intelligence** (20-30s):
   ```
   ✓ Upload complete
   📄 research_paper.pdf (2.3 MB)
   ✅ Analysis complete
   📊 12 insights | 8 entities | 15 connections
   ```

### Frontend Implementation

```typescript
// Show processing state
export function DumpStatus({ dump }: { dump: RawDump }) {
  const { data: queueStatus } = useQueueStatus(dump.id);
  
  return (
    <div className="dump-status">
      {queueStatus?.processing_state === 'pending' && (
        <span className="processing">
          <Spinner /> Waiting for analysis...
        </span>
      )}
      
      {queueStatus?.processing_state === 'processing' && (
        <span className="processing">
          <Spinner /> Analyzing content...
        </span>
      )}
      
      {queueStatus?.processing_state === 'completed' && (
        <span className="complete">
          ✅ Analysis complete
        </span>
      )}
      
      {queueStatus?.processing_state === 'failed' && (
        <span className="error">
          ⚠️ Analysis failed - will retry
        </span>
      )}
    </div>
  );
}
```

## 🚀 Pure Supabase Deployment Architecture

### Single Connection Type - Multi-Worker Scaling

```
                    ┌─────────────┐
                    │  Supabase   │
                    │   Database  │
                    │   + Queue   │
                    │   + RPCs    │
                    └──────┬──────┘
                           │ Pure Supabase Client
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼─────┐      ┌────▼─────┐      ┌────▼─────┐
   │ Worker 1 │      │ Worker 2 │      │ Worker N │
   │  Render  │      │  Render  │      │  Render  │
   │(Service) │      │(Service) │      │(Service) │
   └──────────┘      └──────────┘      └──────────┘
```

**Architecture Benefits:**
- **No DATABASE_URL required** - eliminates connection string complexity
- **Service role authentication** for backend operations
- **Anon role authentication** for user operations  
- **Single connection type** - more reliable and maintainable
- **Leverages Supabase scaling** - connection pooling built-in
- Each worker has unique ID
- `FOR UPDATE SKIP LOCKED` prevents conflicts
- Horizontal scaling by adding workers
- Graceful shutdown support

## 🔧 Implementation Steps

### Phase 1: Queue Infrastructure
1. Create queue table and triggers
2. Deploy queue management RPCs
3. Add monitoring views

### Phase 2: Agent Integration
1. Update agent backend to poll queue
2. Implement claim/process/complete flow
3. Add error handling and retries

### Phase 3: UI Enhancement
1. Add processing status indicators
2. Implement progressive result display
3. Add queue status to admin panel

### Phase 4: Operations
1. Set up monitoring dashboards
2. Configure alerts for stuck jobs
3. Document runbooks for common issues

## 📋 Success Metrics

- **Queue Latency**: 95% processed within 30s
- **Success Rate**: >99% eventual success (with retries)
- **Worker Efficiency**: <20% idle time
- **User Satisfaction**: Clear progress indicators

## 🚨 Failure Modes & Recovery

### Automatic Recovery
- Stale claims released after 5 minutes
- Failed jobs retry up to 3 times
- Exponential backoff on retries

### Manual Intervention
- Admin UI to requeue failed jobs
- Ability to skip poisoned dumps
- Worker restart without data loss

---

**This async framework ensures intelligence processing scales independently while maintaining excellent user experience.**
