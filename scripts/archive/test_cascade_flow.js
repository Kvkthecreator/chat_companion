const { createClient } = require('@supabase/supabase-js');
const { v4: uuidv4 } = require('uuid');

const supabase = createClient(
  process.env.SUPABASE_URL, 
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

// Utility functions
async function sleep(seconds) {
  return new Promise(resolve => setTimeout(resolve, seconds * 1000));
}

async function waitForQueueEntry(condition, timeout = 60) {
  const start = Date.now();
  while (Date.now() - start < timeout * 1000) {
    const { data } = await supabase
      .from('canonical_queue')
      .select('*')
      .match(condition)
      .order('created_at', { ascending: false })
      .limit(1);
      
    if (data && data.length > 0) {
      return data[0];
    }
    
    await sleep(2);
  }
  return null;
}

async function waitForQueueStatus(queueId, targetStatus, timeout = 120) {
  const start = Date.now();
  while (Date.now() - start < timeout * 1000) {
    const { data } = await supabase
      .from('canonical_queue')
      .select('status, updated_at')
      .eq('id', queueId)
      .single();
      
    if (data && data.status === targetStatus) {
      return data;
    }
    
    await sleep(2);
  }
  return null;
}

// Main test function
async function testCascadeFlow() {
  try {
    console.log('🌊 Testing Pipeline Cascade Flow...\n');
    
    // 1. Setup test basket
    const basketId = 'da75cf04-65e5-46ac-940a-74e2ffe077a2'; // Use existing test basket
    const { data: basket } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basketId)
      .single();
      
    if (!basket) {
      console.error('❌ Test basket not found');
      return;
    }
    
    console.log(`📦 Using basket: ${basket.id}`);
    console.log(`🌐 Workspace: ${basket.workspace_id}\n`);
    
    // 2. Create test dump with cascade-triggering content
    console.log('📝 Creating test dump...');
    const testContent = `
Pipeline Cascade Test Document

This document contains test content designed to trigger the full P0→P1→P2→P3 cascade flow.

Key Concepts:
- Cascade triggering mechanism
- Pipeline stage orchestration
- Automatic downstream processing

Technical Components:
- Queue processor health monitoring
- Cascade manager implementation
- Integration point verification

Expected Behavior:
- P0 captures this raw dump
- P1 creates substrate (blocks + context items)
- P2 maps relationships between substrate
- P3 computes reflections on the substrate

Test Verification Points:
- Queue entries created automatically
- Cascade metadata properly propagated
- Each stage completes successfully
- Timeline events emitted correctly
`;

    const dumpRequestId = uuidv4();
    const { data: ingestResult, error: dumpError } = await supabase.rpc(
      'fn_ingest_dumps',
      {
        p_workspace_id: basket.workspace_id,
        p_basket_id: basket.id,
        p_dumps: [{
          dump_request_id: dumpRequestId,
          text_dump: testContent,
          source_meta: { 
            test: 'cascade_flow_test',
            timestamp: new Date().toISOString()
          }
        }]
      }
    );
    
    if (dumpError) {
      console.error('❌ Failed to create dump:', dumpError);
      return;
    }
    
    const dumpId = ingestResult[0].dump_id;
    console.log(`✅ Created test dump: ${dumpId}\n`);
    
    // 3. Monitor P1 processing
    console.log('⏳ Waiting for P1_SUBSTRATE queue entry...');
    const p1Entry = await waitForQueueEntry({
      dump_id: dumpId,
      work_type: 'P1_SUBSTRATE'
    }, 30);
    
    if (!p1Entry) {
      console.error('❌ P1 queue entry not created - check database triggers');
      return;
    }
    
    console.log(`✅ P1 queue entry created: ${p1Entry.id}`);
    console.log(`   Status: ${p1Entry.status}`);
    console.log(`   Worker: ${p1Entry.worker_id || 'not claimed'}\n`);
    
    // 4. Wait for P1 completion
    console.log('⏳ Waiting for P1 processing to complete...');
    const p1Complete = await waitForQueueStatus(p1Entry.id, 'completed', 60);
    
    if (!p1Complete) {
      console.error('❌ P1 processing did not complete - queue processor may not be running');
      return;
    }
    
    console.log(`✅ P1 completed at: ${p1Complete.updated_at}\n`);
    
    // 5. Check for proposals created
    const { data: proposals } = await supabase
      .from('proposals')
      .select('id, status, is_executed, ops')
      .contains('provenance', [dumpId])
      .order('created_at', { ascending: false });
      
    if (!proposals || proposals.length === 0) {
      console.error('❌ No proposals created by P1');
      return;
    }
    
    const proposal = proposals[0];
    console.log(`📋 P1 created proposal: ${proposal.id}`);
    console.log(`   Status: ${proposal.status}`);
    console.log(`   Executed: ${proposal.is_executed || false}`);
    console.log(`   Operations: ${proposal.ops?.length || 0}\n`);
    
    // 6. Monitor P1→P2 cascade
    console.log('🌊 Checking for P1→P2 cascade trigger...');
    const p2Entry = await waitForQueueEntry({
      basket_id: basket.id,
      work_type: 'P2_GRAPH'
    }, 15);
    
    if (!p2Entry) {
      console.error('❌ P2 queue entry not created - cascade trigger failed');
      console.log('   Check if proposal was auto-approved and executed');
      console.log('   Check cascade_manager integration in governance_processor.py');
      return;
    }
    
    // Verify cascade metadata
    const cascadeMeta = p2Entry.metadata?.cascade_trigger;
    if (cascadeMeta) {
      console.log(`✅ P2 cascade triggered from P1`);
      console.log(`   Source: ${cascadeMeta.source_work_type}`);
      console.log(`   Trigger time: ${cascadeMeta.trigger_time}`);
      console.log(`   Rule: ${cascadeMeta.cascade_rule}\n`);
    } else {
      console.log('⚠️ P2 entry created but missing cascade metadata\n');
    }
    
    // 7. Wait for P2 completion
    console.log('⏳ Waiting for P2 processing to complete...');
    const p2Complete = await waitForQueueStatus(p2Entry.id, 'completed', 60);
    
    if (!p2Complete) {
      console.error('❌ P2 processing did not complete');
      return;
    }
    
    console.log(`✅ P2 completed at: ${p2Complete.updated_at}\n`);
    
    // 8. Check relationships created
    const { data: relationships } = await supabase
      .from('substrate_relationships') // Adjust table name as needed
      .select('id')
      .eq('basket_id', basket.id)
      .gte('created_at', new Date(Date.now() - 300000).toISOString()); // Last 5 minutes
      
    console.log(`🔗 Relationships created: ${relationships?.length || 0}\n`);
    
    // 9. Monitor P2→P3 cascade
    console.log('🌊 Checking for P2→P3 cascade trigger...');
    const p3Entry = await waitForQueueEntry({
      basket_id: basket.id,
      work_type: 'P3_REFLECTION'
    }, 15);
    
    if (!p3Entry) {
      console.log('⚠️ P3 queue entry not created');
      console.log('   This is expected if no relationships were created');
      console.log('   Or cascade trigger not implemented in graph_agent.py\n');
    } else {
      console.log(`✅ P3 cascade triggered from P2`);
      console.log(`   Queue entry: ${p3Entry.id}\n`);
      
      // Wait for P3 completion
      const p3Complete = await waitForQueueStatus(p3Entry.id, 'completed', 60);
      if (p3Complete) {
        console.log(`✅ P3 completed at: ${p3Complete.updated_at}\n`);
      }
    }
    
    // 10. Verify cascade timeline events
    console.log('📅 Checking cascade timeline events...');
    const { data: cascadeEvents } = await supabase
      .from('timeline_events')
      .select('event_type, event_data, created_at')
      .eq('basket_id', basket.id)
      .eq('event_type', 'pipeline.cascade')
      .gte('created_at', new Date(Date.now() - 300000).toISOString())
      .order('created_at', { ascending: true });
      
    if (cascadeEvents && cascadeEvents.length > 0) {
      console.log(`✅ Found ${cascadeEvents.length} cascade events:`);
      cascadeEvents.forEach(event => {
        const data = event.event_data;
        console.log(`   ${data.source_stage} → ${data.target_stage} at ${event.created_at}`);
      });
    } else {
      console.log('❌ No cascade timeline events found');
    }
    
    // Summary
    console.log('\n\n🎯 Cascade Flow Test Summary:');
    console.log('═══════════════════════════════');
    console.log(`P0→P1: ${p1Entry ? '✅' : '❌'} Queue entry created`);
    console.log(`P1 Processing: ${p1Complete ? '✅' : '❌'} Completed`);
    console.log(`P1 Proposals: ${proposals?.length > 0 ? '✅' : '❌'} Created`);
    console.log(`P1→P2 Cascade: ${p2Entry ? '✅' : '❌'} Triggered`);
    console.log(`P2 Processing: ${p2Complete ? '✅' : '❌'} Completed`);
    console.log(`P2→P3 Cascade: ${p3Entry ? '✅' : '⚠️'} ${p3Entry ? 'Triggered' : 'Not triggered (check conditions)'}`);
    
    // Cascade health
    const cascadeHealth = p1Entry && p2Entry && cascadeMeta;
    console.log(`\nOverall Cascade Health: ${cascadeHealth ? '✅ WORKING' : '❌ NEEDS ATTENTION'}`);
    
    if (!cascadeHealth) {
      console.log('\n🔧 Troubleshooting Steps:');
      if (!p1Entry) {
        console.log('1. Check database trigger for raw_dumps → canonical_queue');
      }
      if (!p2Entry) {
        console.log('2. Check cascade_manager integration in governance_processor.py');
        console.log('3. Verify proposals are being auto-approved and executed');
      }
      if (!cascadeMeta) {
        console.log('4. Check cascade metadata is being properly set');
      }
    }
    
  } catch (err) {
    console.error('❌ Cascade flow test failed:', err.message);
  }
}

// Run the test
testCascadeFlow();