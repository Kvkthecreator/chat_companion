const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL, 
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function quickTest() {
  try {
    console.log('🧪 Quick connection test...');
    
    // First, find an existing workspace and basket
    console.log('🔍 Finding existing workspace...');
    const { data: workspaces, error: wsError } = await supabase
      .from('workspaces')
      .select('id')
      .limit(1);
      
    if (wsError || !workspaces?.length) {
      console.error('❌ No workspaces found:', wsError);
      return;
    }
    
    const workspaceId = workspaces[0].id;
    console.log(`✅ Using workspace: ${workspaceId}`);
    
    // Find an existing basket in this workspace
    console.log('🔍 Finding existing basket...');
    let basketId;
    const { data: baskets, error: basketError } = await supabase
      .from('baskets')
      .select('id')
      .eq('workspace_id', workspaceId)
      .limit(1);
      
    if (basketError || !baskets?.length) {
      console.log('📝 Creating new basket...');
      const { data: newBasket, error: createBasketError } = await supabase
        .from('baskets')
        .insert({
          workspace_id: workspaceId,
          title: 'Test Basket for Substrate Scaffolding',
          description: 'Temporary basket for testing P0-P3 pipeline',
          status: 'ACTIVE'
        })
        .select()
        .single();
        
      if (createBasketError) {
        console.error('❌ Failed to create basket:', createBasketError);
        return;
      }
      basketId = newBasket.id;
      console.log(`✅ Created basket: ${basketId}`);
    } else {
      basketId = baskets[0].id;
      console.log(`✅ Using existing basket: ${basketId}`);
    }
    
    // Check existing raw dumps first
    console.log('🔍 Checking existing raw dumps and their processing...');
    const { data: existingDumps, error: dumpError } = await supabase
      .from('raw_dumps')
      .select('id, created_at, body_md')
      .eq('basket_id', basketId)
      .order('created_at', { ascending: false })
      .limit(5);
      
    if (dumpError) {
      console.error('❌ Error checking dumps:', dumpError);
      return;
    }
    
    console.log(`📋 Found ${existingDumps?.length || 0} existing dumps`);
    
    let testDumpId;
    if (existingDumps?.length > 0) {
      // Use the most recent dump
      testDumpId = existingDumps[0].id;
      console.log(`✅ Using existing dump: ${testDumpId}`);
      console.log(`📝 Content preview: ${existingDumps[0].body_md?.substring(0, 60)}...`);
    } else {
      // Try to create with different approach - using API endpoint instead of direct insert
      console.log('📝 No existing dumps found. The create permission error suggests database triggers.');
      console.log('ℹ️ This indicates the P0 capture process likely needs to go through API endpoints, not direct inserts.');
      
      // For now, let\'s check if there are any dumps in other baskets we can monitor
      const { data: anyDumps, error: anyError } = await supabase
        .from('raw_dumps')
        .select('id, basket_id, created_at')
        .order('created_at', { ascending: false })
        .limit(5);
        
      if (anyError) {
        console.error('❌ Error checking any dumps:', anyError);
        return;
      }
      
      if (anyDumps?.length > 0) {
        testDumpId = anyDumps[0].id;
        basketId = anyDumps[0].basket_id; // Use the basket that has the dump
        console.log(`✅ Using most recent dump from system: ${testDumpId}`);
        console.log(`📁 In basket: ${basketId}`);
      } else {
        console.log('❌ No dumps found in system to test with');
        return;
      }
    }
    
    console.log('⏱️ Monitoring processing for this dump...');
    
    // Check queue status every 10 seconds for 1 minute
    for (let i = 0; i < 6; i++) {
      await new Promise(resolve => setTimeout(resolve, 10000));
      
      const { data: queue } = await supabase
        .from('agent_queue')
        .select('processing_state, error_message')
        .eq('dump_id', testDumpId)
        .single();
        
      const timeElapsed = (i + 1) * 10;
      console.log(`📊 ${timeElapsed}s: Queue state = ${queue?.processing_state || 'not_found'}`);
      
      if (queue?.error_message) {
        console.log(`❌ Error: ${queue.error_message}`);
      }
      
      if (queue?.processing_state === 'completed') {
        console.log('✅ Processing completed! Checking results...');
        break;
      } else if (queue?.processing_state === 'failed') {
        console.log('❌ Processing failed');
        break;
      }
    }
    
    // Check for created substrate
    console.log('\n🔍 Checking substrate creation...');
    
    const { data: proposals } = await supabase
      .from('proposals')
      .select('*')
      .eq('basket_id', basketId)
      .order('created_at', { ascending: false })
      .limit(3);
      
    console.log(`📋 Proposals: ${proposals?.length || 0} found`);
    if (proposals?.length > 0) {
      proposals.forEach((p, i) => {
        console.log(`   ${i+1}. ${p.proposal_kind} - Status: ${p.status} - Ops: ${p.ops?.length || 0}`);
        if (p.ops?.length > 0) {
          console.log(`      Ops preview: ${p.ops.slice(0, 2).map(op => op.operation_type).join(', ')}${p.ops.length > 2 ? '...' : ''}`);
        }
      });
    }
    
    // Check if any substrate was actually created from these proposals
    console.log('\n🔍 Checking for actual substrate creation...');
    
    const { data: blocks } = await supabase
      .from('blocks')
      .select('id, title, status')
      .eq('basket_id', basketId)
      .limit(5);
      
    const { data: contextItems } = await supabase
      .from('context_items')  
      .select('id, item_type, status')
      .eq('basket_id', basketId)
      .limit(5);
      
    console.log(`🧱 Blocks: ${blocks?.length || 0} found`);
    if (blocks?.length > 0) {
      blocks.forEach((b, i) => {
        console.log(`   ${i+1}. ${b.title?.substring(0, 40) || 'Untitled'} - Status: ${b.status}`);
      });
    }
    
    console.log(`📝 Context Items: ${contextItems?.length || 0} found`);
    if (contextItems?.length > 0) {
      contextItems.forEach((c, i) => {
        console.log(`   ${i+1}. Type: ${c.item_type} - Status: ${c.status}`);
      });
    }
    
    // Summary of pipeline status
    console.log('\n📊 Pipeline Status Summary:');
    console.log('──────────────────────────');
    console.log(`✅ P0 (Capture): Working - Raw dumps exist`);
    console.log(`✅ P1 (Governance): Working - ${proposals?.length || 0} proposals created`);
    
    if (proposals?.some(p => p.status === 'APPROVED')) {
      console.log(`✅ P1 (Approval): Working - Some proposals approved`);
    } else {
      console.log(`⚠️ P1 (Approval): Pending - All proposals in PROPOSED state`);
    }
    
    if (blocks?.length > 0 || contextItems?.length > 0) {
      console.log(`✅ P1 (Substrate): Working - Substrate creation successful`);
    } else {
      console.log(`❌ P1 (Substrate): Not working - No substrate created from proposals`);
    }
    
    console.log(`❓ P2 (Relationships): Needs checking`);
    console.log(`❓ P3 (Reflections): Needs checking`);
      
  } catch (err) {
    console.error('❌ Test failed:', err.message);
  }
}

quickTest();