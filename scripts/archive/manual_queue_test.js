const { createClient } = require('@supabase/supabase-js');
const { v4: uuidv4 } = require('uuid');

const supabase = createClient(
  process.env.SUPABASE_URL, 
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function manualQueueTest() {
  try {
    console.log('🔧 Manual Queue Processing Test...\n');
    
    const dumpId = '8bf0288a-71f5-4559-b311-cd804a05a097';
    
    // Get dump details
    const { data: dump } = await supabase
      .from('raw_dumps')
      .select('*')
      .eq('id', dumpId)
      .single();
      
    if (!dump) {
      console.error('❌ Test dump not found');
      return;
    }
    
    console.log(`📦 Testing with dump: ${dump.id}`);
    console.log(`🗂️  Basket: ${dump.basket_id}`);
    console.log(`🌐 Workspace: ${dump.workspace_id}`);
    console.log(`📄 Content length: ${dump.text_dump?.length || 0} characters\n`);
    
    // Manually create a canonical queue entry
    console.log('⚙️ Creating manual queue entry...');
    
    const queueEntry = {
      id: uuidv4(),
      dump_id: dump.id,
      basket_id: dump.basket_id,
      workspace_id: dump.workspace_id,
      work_type: 'P1_SUBSTRATE',
      status: 'pending',
      priority: 5,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    const { data: createdEntry, error: queueError } = await supabase
      .from('canonical_queue')
      .insert(queueEntry)
      .select()
      .single();
    
    if (queueError) {
      console.error('❌ Failed to create queue entry:', queueError);
      return;
    }
    
    console.log(`✅ Created queue entry: ${createdEntry.id}`);
    console.log(`   Status: ${createdEntry.status}`);
    console.log(`   Work Type: ${createdEntry.work_type}\n`);
    
    // Now check if the queue processor picks it up
    console.log('⏳ Waiting 30 seconds for queue processor to pick up the work...');
    await new Promise(resolve => setTimeout(resolve, 30000));
    
    // Check queue entry status
    const { data: updatedEntry } = await supabase
      .from('canonical_queue')
      .select('*')
      .eq('id', createdEntry.id)
      .single();
    
    console.log('🔍 Queue entry status after waiting:');
    console.log(`   Status: ${updatedEntry.status}`);
    console.log(`   Updated: ${updatedEntry.updated_at}`);
    console.log(`   Worker ID: ${updatedEntry.worker_id || 'none'}`);
    
    if (updatedEntry.error_details) {
      console.log(`   Error: ${updatedEntry.error_details}`);
    }
    
    // Check if proposals were created
    const { data: proposals } = await supabase
      .from('proposals')
      .select('*')
      .contains('provenance', [dump.id])
      .order('created_at', { ascending: false });
    
    console.log(`\\n📋 Proposals created: ${proposals?.length || 0}`);
    
    if (proposals && proposals.length > 0) {
      const proposal = proposals[0];
      console.log(`\\n✅ Found proposal: ${proposal.id}`);
      console.log(`   Status: ${proposal.status}`);
      console.log(`   Executed: ${proposal.is_executed || false}`);
      console.log(`   Operations: ${proposal.ops?.length || 0}`);
      
      if (proposal.validator_report) {
        console.log(`   Confidence: ${proposal.validator_report.confidence || 'N/A'}`);
      }
    }
    
    // Assessment
    console.log('\\n\\n🎯 Manual Queue Test Assessment:');
    console.log('═════════════════════════════');
    
    if (updatedEntry.status === 'completed' && proposals && proposals.length > 0) {
      console.log('✅ QUEUE PROCESSING WORKS: Entry processed and proposals created');
    } else if (updatedEntry.status === 'pending') {
      console.log('❌ QUEUE PROCESSOR NOT RUNNING: Entry still pending after 30 seconds');
    } else if (updatedEntry.status === 'failed') {
      console.log('❌ QUEUE PROCESSING FAILED: Check error details above');
    } else {
      console.log(`⚠️ UNKNOWN STATE: Queue status is ${updatedEntry.status}`);
    }
    
  } catch (err) {
    console.error('❌ Manual queue test failed:', err.message);
  }
}

manualQueueTest();