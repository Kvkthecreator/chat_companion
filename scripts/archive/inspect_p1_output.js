const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL, 
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function inspectP1Output() {
  try {
    console.log('🔍 Inspecting P1 Agent Output Quality...\n');
    
    // Get recent proposals to inspect operations
    const { data: proposals, error } = await supabase
      .from('proposals')
      .select('*')
      .eq('origin', 'agent')
      .eq('proposal_kind', 'Extraction')
      .order('created_at', { ascending: false })
      .limit(3);
      
    if (error) {
      console.error('❌ Error fetching proposals:', error);
      return;
    }
    
    console.log(`📋 Found ${proposals?.length || 0} agent proposals to inspect\n`);
    
    proposals?.forEach((proposal, idx) => {
      console.log(`\n🔍 Proposal ${idx + 1}: ${proposal.id}`);
      console.log(`📅 Created: ${proposal.created_at}`);
      console.log(`📊 Operations count: ${proposal.ops?.length || 0}`);
      
      // Inspect the operations in detail
      if (proposal.ops && proposal.ops.length > 0) {
        console.log('\n📝 Operations Detail:');
        proposal.ops.slice(0, 3).forEach((op, opIdx) => {
          console.log(`\n  Operation ${opIdx + 1}:`);
          console.log(`    Type: ${op.operation_type || op.type || 'MISSING TYPE'}`);
          console.log(`    Target: ${op.target_type || op.target || 'N/A'}`);
          
          // Check for block creation operations
          if (op.operation_type === 'CreateBlock' || op.type === 'create_block') {
            console.log(`    Content: ${op.content?.substring(0, 100) || 'NO CONTENT'}...`);
            console.log(`    Semantic Type: ${op.semantic_type || 'MISSING'}`);
            console.log(`    Title: ${op.title || 'MISSING'}`);
          }
          
          // Check for context item creation
          if (op.operation_type === 'CreateContextItem' || op.type === 'create_context_item') {
            console.log(`    Label: ${op.label || 'MISSING'}`);
            console.log(`    Item Type: ${op.item_type || 'MISSING'}`);
            console.log(`    Confidence: ${op.confidence || 'MISSING'}`);
          }
          
          // Raw operation dump for debugging
          console.log(`    Raw: ${JSON.stringify(op).substring(0, 200)}...`);
        });
        
        if (proposal.ops.length > 3) {
          console.log(`\n  ... and ${proposal.ops.length - 3} more operations`);
        }
      } else {
        console.log('\n  ❌ No operations found or operations array is empty!');
      }
      
      // Check validator report
      console.log('\n📊 Validator Report:');
      if (proposal.validator_report) {
        console.log(`  Confidence: ${proposal.validator_report.confidence || 'MISSING'}`);
        console.log(`  Impact Summary: ${proposal.validator_report.impact_summary || 'MISSING'}`);
        console.log(`  Warnings: ${proposal.validator_report.warnings?.length || 0}`);
      } else {
        console.log('  ❌ No validator report found!');
      }
      
      // Check provenance (what raw dumps it came from)
      console.log('\n🔗 Provenance (source dumps):');
      if (proposal.provenance && proposal.provenance.length > 0) {
        proposal.provenance.forEach((prov, i) => {
          console.log(`  ${i + 1}. ${prov}`);
        });
      } else {
        console.log('  ❌ No provenance found!');
      }
    });
    
    // Summary assessment
    console.log('\n\n📊 P1 Agent Health Assessment:');
    console.log('────────────────────────────');
    
    const hasOperations = proposals?.some(p => p.ops && p.ops.length > 0);
    const hasValidOperations = proposals?.some(p => 
      p.ops?.some(op => op.operation_type || op.type)
    );
    const hasContent = proposals?.some(p =>
      p.ops?.some(op => op.content || op.label)
    );
    
    console.log(`✅ Creating proposals: ${proposals?.length > 0 ? 'YES' : 'NO'}`);
    console.log(`${hasOperations ? '✅' : '❌'} Proposals have operations: ${hasOperations ? 'YES' : 'NO'}`);
    console.log(`${hasValidOperations ? '✅' : '❌'} Operations have types: ${hasValidOperations ? 'YES' : 'NO'}`);
    console.log(`${hasContent ? '✅' : '❌'} Operations have content: ${hasContent ? 'YES' : 'NO'}`);
    
  } catch (err) {
    console.error('❌ Inspection failed:', err.message);
  }
}

inspectP1Output();