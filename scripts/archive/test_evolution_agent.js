const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL, 
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function testEvolutionAgent() {
  try {
    console.log('🔄 Testing Evolution-Aware P1 Agent...\n');
    
    // Check connection
    const { data: test, error: testError } = await supabase.from('baskets').select('id').limit(1);
    if (testError) {
      console.error('❌ Connection failed:', testError);
      return;
    }
    console.log('✅ Connected to Supabase\n');
    
    // Find baskets with existing substrate for testing evolution
    const { data: baskets, error: basketError } = await supabase
      .from('baskets')
      .select('id')
      .limit(5);
      
    if (basketError) {
      console.error('❌ Error fetching baskets:', basketError);
      return;
    }
    
    console.log(`📋 Found ${baskets?.length || 0} baskets\n`);
    
    for (const basket of (baskets || [])) {
      console.log(`🗂️  Basket: ${basket.id}`);
      
      // Check existing substrate
      const { data: blocks } = await supabase
        .from('blocks')
        .select('id, content, semantic_type, confidence_score')
        .eq('basket_id', basket.id);
        
      const { data: items } = await supabase
        .from('context_items')
        .select('id, normalized_label, type, confidence_score')
        .eq('basket_id', basket.id);
        
      console.log(`   📦 Substrate: ${blocks?.length || 0} blocks, ${items?.length || 0} context items`);
      
      // Show some sample substrate
      if (blocks && blocks.length > 0) {
        console.log('   🧱 Sample blocks:');
        blocks.slice(0, 3).forEach(block => {
          console.log(`      - ${block.semantic_type}: ${block.content?.substring(0, 60)}...`);
        });
      }
      
      if (items && items.length > 0) {
        console.log('   🏷️  Sample context items:');
        items.slice(0, 3).forEach(item => {
          console.log(`      - ${item.type}: ${item.normalized_label}`);
        });
      }
      
      // Check recent raw_dumps to see what might trigger evolution
      const { data: dumps } = await supabase
        .from('raw_dumps')
        .select('id, text_dump, created_at')
        .eq('basket_id', basket.id)
        .order('created_at', { ascending: false })
        .limit(3);
        
      if (dumps && dumps.length > 0) {
        console.log(`   📄 Recent dumps: ${dumps.length}`);
        dumps.forEach(dump => {
          console.log(`      - ${dump.created_at}: ${dump.text_dump?.substring(0, 50)}...`);
        });
      }
      
      console.log('');
    }
    
    // Check queue processing status
    const { data: queue } = await supabase
      .from('canonical_queue')
      .select('id, work_type, status, basket_id')
      .order('created_at', { ascending: false })
      .limit(10);
      
    console.log(`⚙️  Queue status: ${queue?.length || 0} recent entries`);
    if (queue) {
      const statusCounts = queue.reduce((acc, entry) => {
        acc[entry.status] = (acc[entry.status] || 0) + 1;
        return acc;
      }, {});
      console.log('   Status breakdown:', statusCounts);
    }
    
    // Check recent proposals for evolution operations
    console.log('\n🔍 Recent Proposals Analysis:');
    const { data: proposals } = await supabase
      .from('proposals')
      .select('id, ops, status, validator_report, created_at')
      .eq('origin', 'agent')
      .order('created_at', { ascending: false })
      .limit(5);
      
    if (proposals) {
      proposals.forEach((proposal, i) => {
        console.log(`\n  Proposal ${i + 1}: ${proposal.id}`);
        console.log(`    Status: ${proposal.status}`);
        console.log(`    Created: ${proposal.created_at}`);
        
        if (proposal.ops && proposal.ops.length > 0) {
          const opTypes = proposal.ops.map(op => op.type || op.operation_type).filter(Boolean);
          const operationCounts = opTypes.reduce((acc, type) => {
            acc[type] = (acc[type] || 0) + 1;
            return acc;
          }, {});
          
          console.log(`    Operations: ${JSON.stringify(operationCounts)}`);
          
          // Check if it has evolution operations (not just CREATE)
          const hasEvolution = opTypes.some(type => 
            ['ReviseBlock', 'UpdateContextItem', 'MergeContextItems'].includes(type)
          );
          console.log(`    Has Evolution Ops: ${hasEvolution ? '✅' : '❌'}`);
        }
        
        if (proposal.validator_report) {
          console.log(`    Confidence: ${proposal.validator_report.confidence || 'N/A'}`);
        }
      });
    }
    
  } catch (err) {
    console.error('❌ Test failed:', err.message);
  }
}

testEvolutionAgent();