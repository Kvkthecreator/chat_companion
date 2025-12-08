#!/usr/bin/env node

/**
 * Debug script to check graph relationship issues
 */

console.log(`
🔍 GRAPH RELATIONSHIP DEBUG CHECKLIST

1. Check Browser Console:
   - Open developer tools (F12)
   - Look for the log: "P2 Graph mapping initiated:" 
   - Check if there are any error messages

2. Enable All Node Types:
   - ✅ Knowledge Block
   - ✅ Meaning 
   - ✅ Source Note (currently disabled by default!)

3. Check Graph Statistics:
   - Look at "Relationships: X" count in the Statistics panel
   - If it shows 0, relationships aren't being fetched
   - If it shows > 0, they exist but aren't rendering

4. Verify Node Existence:
   - Relationships only show if BOTH nodes are loaded
   - With limits (100 blocks, 50 dumps), some nodes might be excluded
   - Try reducing the amount of data in your basket

5. Manual Database Check (if you have access):
   SELECT COUNT(*) FROM substrate_relationships WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1';
   
   SELECT 
     sr.*,
     b1.state as from_state,
     b2.state as to_state
   FROM substrate_relationships sr
   LEFT JOIN blocks b1 ON sr.from_id = b1.id AND sr.from_type = 'block'
   LEFT JOIN blocks b2 ON sr.to_id = b2.id AND sr.to_type = 'block'
   WHERE sr.basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1'
   LIMIT 10;

6. Common Issues:
   - Relationships to PROPOSED/REJECTED blocks won't show
   - Relationships to archived/deprecated items won't show  
   - Dump relationships hidden by default toggle
   - P2 work might be failing silently

7. Quick Fix to Try:
   - Enable all node type filters
   - Click "Refresh Connections" button
   - Wait 30 seconds
   - Refresh the page (Cmd+R)

8. Check Work Execution:
   - The "Map Connections" button creates P2_GRAPH work
   - Check if work_result shows success
   - Look for error_message in agent_processing_queue
`);

console.log('\n📊 Expected P2 Relationship Types:');
console.log('- semantic_similarity');
console.log('- related_content'); 
console.log('- thematic_connection');
console.log('- causal_relationship');
console.log('- temporal_sequence');
console.log('- enablement_chain');
console.log('- impact_relationship');
console.log('- conditional_logic');