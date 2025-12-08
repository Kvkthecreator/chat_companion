#!/usr/bin/env node

/**
 * Debug P2 Work Flow Issues
 */

console.log(`
🔍 P2 GRAPH WORK DEBUGGING GUIDE

1. **Frontend Work Creation Check**:
   - Open browser console (F12)
   - Click "Map Connections" button
   - Look for: "P2 Graph mapping initiated:"
   - Should see work_id in response
   
2. **Backend Processing Check**:
   - Check server logs for:
     "Starting P2 graph work: work_id=..."
     "Successfully claimed X work items"
     "P2 Graph completed successfully"
   
3. **Common Issues**:
   
   ❌ No Console Logs = Work not created
   - Check network tab for /api/work POST request
   - Should return 201/202 with work_id
   
   ❌ Work Created but Not Processed
   - Canonical queue processor not running
   - Work stuck in 'pending' state
   - Check agent_processing_queue table
   
   ❌ Relationships Created but Not Showing
   - UI filters hiding nodes (enable all types)
   - State filtering (PROPOSED blocks won't show)
   - Both nodes must exist for edge to render
   
4. **Manual Database Queries** (if you have access):
   
   -- Check if work was created
   SELECT id, work_type, processing_state, error_message, created_at 
   FROM agent_processing_queue 
   WHERE work_type = 'P2_GRAPH' 
   AND basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1'
   ORDER BY created_at DESC;
   
   -- Check if relationships exist
   SELECT COUNT(*) 
   FROM substrate_relationships 
   WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1';
   
   -- Check substrate counts
   SELECT 
     (SELECT COUNT(*) FROM blocks WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1' AND state IN ('ACCEPTED','LOCKED','CONSTANT')) as blocks,
     (SELECT COUNT(*) FROM context_items WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1' AND state = 'ACTIVE') as context_items;

5. **Quick Fixes**:
   ✅ Enable ALL node type filters in graph view
   ✅ Wait for backend deployment with canon fix
   ✅ Try creating new blocks/context items first
   ✅ Check if basket has mature substrate (5+ items)
   
6. **What Should Happen**:
   1. Click "Map Connections" → Creates P2_GRAPH work
   2. Backend claims work from queue
   3. P2GraphAgent analyzes blocks + context_items
   4. Creates substrate_relationships 
   5. Graph page shows connections on refresh
   
7. **Canon Compliance Notes**:
   - Raw dumps are NOT included (just fixed this!)
   - Only connects blocks + context_items
   - Relationships: semantic_similarity, causal_relationship, etc.
`);

console.log('\n📊 Expected Flow:');
console.log('Frontend → /api/work → agent_processing_queue → P2GraphAgent → substrate_relationships → Graph UI');