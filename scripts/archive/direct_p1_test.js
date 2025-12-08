const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL, 
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function directP1Test() {
  try {
    console.log('🎯 Direct P1 Agent Test...\n');
    
    // Use the dump we created earlier
    const dumpId = '8bf0288a-71f5-4559-b311-cd804a05a097';
    const basketId = 'da75cf04-65e5-46ac-940a-74e2ffe077a2';
    const workspaceId = '00000000-0000-0000-0000-000000000002';
    
    console.log(`📦 Testing P1 agent directly with:`);
    console.log(`   Dump: ${dumpId}`);
    console.log(`   Basket: ${basketId}`);
    console.log(`   Workspace: ${workspaceId}\\n`);
    
    // Try to call the P1 agent via the API endpoint
    console.log('🚀 Attempting to trigger P1 processing via API...');
    
    // Use the correct basket work endpoint with proper format
    try {
      const response = await fetch(`https://rightnow-agent-app-backend.onrender.com/api/baskets/${basketId}/work`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer fake-token' // The endpoint requires auth but we'll handle the 401
        },
        body: JSON.stringify({
          mode: 'structured',
          work_type: 'P1_SUBSTRATE',
          dump_ids: [dumpId],
          options: {
            priority: 'high',
            trace_req_id: `test-${Date.now()}`
          }
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ API call successful:', result);
      } else {
        const error = await response.text();
        console.log(`❌ API call failed (${response.status}): ${error}`);
      }
    } catch (fetchError) {
      console.log('❌ API call failed:', fetchError.message);
    }
    
    // Wait and check for results
    console.log('\\n⏳ Waiting 15 seconds for processing...');
    await new Promise(resolve => setTimeout(resolve, 15000));
    
    // Check for new proposals
    const { data: proposals } = await supabase
      .from('proposals')
      .select('*')
      .contains('provenance', [dumpId])
      .order('created_at', { ascending: false });
    
    console.log(`\\n🔍 Results: ${proposals?.length || 0} proposals found`);
    
    if (proposals && proposals.length > 0) {
      const proposal = proposals[0];
      console.log(`\\n📋 Latest Proposal: ${proposal.id}`);
      console.log(`   Status: ${proposal.status}`);
      console.log(`   Created: ${proposal.created_at}`);
      console.log(`   Executed: ${proposal.is_executed || false}`);
      
      if (proposal.validator_report) {
        const confidence = proposal.validator_report.confidence || 0;
        const warnings = proposal.validator_report.warnings || [];
        console.log(`   Confidence: ${confidence.toFixed(3)}`);
        console.log(`   Warnings: ${warnings.length}`);
        
        const shouldAutoApprove = confidence > 0.7 && warnings.length === 0;
        console.log(`   Should Auto-approve: ${shouldAutoApprove ? 'YES' : 'NO'}`);
      }
      
      if (proposal.ops) {
        const opTypes = proposal.ops.map(op => op.type).filter(Boolean);
        const operationCounts = opTypes.reduce((acc, type) => {
          acc[type] = (acc[type] || 0) + 1;
          return acc;
        }, {});
        
        console.log(`   Operations: ${JSON.stringify(operationCounts)}`);
        
        const hasEvolution = opTypes.some(type => 
          ['ReviseBlock', 'UpdateContextItem', 'MergeContextItems'].includes(type)
        );
        console.log(`   Has Evolution Ops: ${hasEvolution ? '✅' : '❌'}`);
      }
      
      if (proposal.execution_log && proposal.execution_log.length > 0) {
        console.log(`\\n📊 Execution Log:`);
        proposal.execution_log.forEach((log, i) => {
          const status = log.success ? '✅' : '❌';
          console.log(`   ${i + 1}. ${log.operation_type}: ${status}`);
          if (!log.success && log.error_message) {
            console.log(`      Error: ${log.error_message}`);
          }
        });
      }
      
      if (proposal.review_notes) {
        console.log(`\\n📝 Review Notes: ${proposal.review_notes}`);
      }
    } else {
      console.log('❌ No proposals created - P1 agent may not be running');
    }
    
  } catch (err) {
    console.error('❌ Direct P1 test failed:', err.message);
  }
}

directP1Test();