const { createClient } = require('@supabase/supabase-js');
const { v4: uuidv4 } = require('uuid');

const supabase = createClient(
  process.env.SUPABASE_URL, 
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function createTestDump() {
  try {
    console.log('🧪 Creating test dump to trigger evolution-aware P1...\n');
    
    // Find basket with existing substrate for evolution testing
    const basketId = '1c4955b8-da82-453b-afa2-478b38279eae'; // This basket has 3 context items
    
    // Get correct workspace_id from the basket
    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .select('workspace_id')
      .eq('id', basketId)
      .single();
      
    if (basketError || !basket) {
      console.error('❌ Failed to get basket:', basketError);
      return;
    }
    
    const workspaceId = basket.workspace_id;
    console.log(`📦 Checking existing substrate in basket ${basketId} (workspace: ${workspaceId})...`);
    
    const { data: blocks } = await supabase
      .from('blocks')
      .select('id, content, semantic_type')
      .eq('basket_id', basketId);
      
    const { data: items } = await supabase
      .from('context_items')  
      .select('id, normalized_label, type')
      .eq('basket_id', basketId);
      
    console.log(`   Current substrate: ${blocks?.length || 0} blocks, ${items?.length || 0} context items`);
    
    if (blocks && blocks.length > 0) {
      console.log('   📝 Existing blocks:');
      blocks.forEach(block => console.log(`      - ${block.semantic_type}: ${block.content?.substring(0, 50)}...`));
    }
    
    if (items && items.length > 0) {
      console.log('   🏷️ Existing context items:');
      items.forEach(item => console.log(`      - ${item.type}: ${item.normalized_label}`));
    }
    
    // Create new dump with content that should trigger evolution decisions
    const testContent = `
Project Update: Advanced Analytics Initiative

Current Status:
- Machine learning models are performing well with 95% accuracy
- User engagement analytics show strong growth in mobile usage
- Data pipeline optimization reduced processing time by 40%

Key Insights:
- Mobile users prefer shorter content formats
- Peak engagement occurs during lunch hours (12-2pm) 
- Advanced search features are highly valued by power users

Next Steps:
- Implement real-time personalization based on user behavior patterns
- Expand mobile-first design principles across all features
- Deploy advanced recommendation engine by end of quarter

Team Notes:
- Sarah mentioned the need for better error handling in data ingestion
- Consider upgrading infrastructure to handle increased load
- Schedule user research sessions to validate new features
`;

    console.log('\n📝 Creating test dump with content that should trigger evolution...');
    console.log(`Content preview: ${testContent.substring(0, 200)}...\n`);
    
    // Use the proper RPC function for dump ingestion
    const dumps = [{
      dump_request_id: uuidv4(),
      text_dump: testContent,
      source_meta: { test: 'evolution_agent_test' }
    }];
    
    const { data: ingestResult, error: dumpError } = await supabase.rpc(
      'fn_ingest_dumps',
      {
        p_workspace_id: workspaceId,
        p_basket_id: basketId,
        p_dumps: dumps
      }
    );
      
    if (dumpError) {
      console.error('❌ Failed to create dump:', dumpError);
      return;
    }
    
    if (!ingestResult || ingestResult.length === 0) {
      console.error('❌ No dump created from ingestion');
      return;
    }
    
    const newDumpId = ingestResult[0].dump_id;
    console.log(`✅ Created test dump: ${newDumpId}`);
    
    // Wait a moment then check for new proposals
    console.log('\n⏳ Waiting 10 seconds for P1 agent processing...');
    await new Promise(resolve => setTimeout(resolve, 10000));
    
    // Check for new proposals
    console.log('\n🔍 Checking for new proposals...');
    const { data: recentProposals } = await supabase
      .from('proposals')
      .select('id, ops, status, validator_report, created_at, provenance')
      .gte('created_at', new Date(Date.now() - 60000).toISOString()) // Last minute
      .order('created_at', { ascending: false });
      
    if (recentProposals && recentProposals.length > 0) {
      console.log(`📋 Found ${recentProposals.length} recent proposals:`);
      
      recentProposals.forEach((proposal, i) => {
        console.log(`\n  Proposal ${i + 1}: ${proposal.id}`);
        console.log(`    Status: ${proposal.status}`);
        console.log(`    Created: ${proposal.created_at}`);
        console.log(`    Provenance: ${proposal.provenance?.includes(newDumpId) ? '✅ From our test dump' : 'Different source'}`);
        
        if (proposal.ops) {
          const opTypes = proposal.ops.map(op => op.type).filter(Boolean);
          const operationCounts = opTypes.reduce((acc, type) => {
            acc[type] = (acc[type] || 0) + 1;
            return acc;
          }, {});
          
          console.log(`    Operations: ${JSON.stringify(operationCounts)}`);
          
          const hasEvolution = opTypes.some(type => 
            ['ReviseBlock', 'UpdateContextItem', 'MergeContextItems'].includes(type)
          );
          console.log(`    Has Evolution Ops: ${hasEvolution ? '✅ YES' : '❌ NO'}`);
        }
        
        if (proposal.validator_report) {
          console.log(`    Confidence: ${proposal.validator_report.confidence || 'N/A'}`);
          const autoApprovalEligible = proposal.validator_report.confidence > 0.7 && 
                                      (!proposal.validator_report.warnings || proposal.validator_report.warnings.length === 0);
          console.log(`    Auto-approval eligible: ${autoApprovalEligible ? '✅ YES' : '❌ NO'}`);
        }
      });
    } else {
      console.log('❌ No recent proposals found - P1 agent may not be running or failed');
    }
    
  } catch (err) {
    console.error('❌ Test failed:', err.message);
  }
}

createTestDump();