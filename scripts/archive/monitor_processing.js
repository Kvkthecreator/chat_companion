#!/usr/bin/env node

const { execSync } = require('child_process');

async function monitorProcessing() {
  console.log('🔍 Monitoring substrate processing over time...\n');
  
  // Create a test dump
  console.log('📥 Creating raw_dump...');
  const createResult = execSync(`
    source .env && psql "$DATABASE_URL" -t -A -c "
    INSERT INTO raw_dumps (body_md, workspace_id, basket_id) 
    VALUES (
      'Advanced test content for substrate scaffolding: project management strategies, team dynamics, technical architecture, user experience design, data analytics, marketing campaigns, competitive analysis, financial planning, risk management, and strategic roadmapping.',
      'fa622620-824e-4734-b4f1-d47a733a0ec1',
      'fa622620-824e-4734-b4f1-d47a733a0ec1'
    ) 
    RETURNING id;"
  `, { encoding: 'utf8' });
  
  const dumpId = createResult.trim();
  console.log(`✅ Raw dump created: ${dumpId}`);
  console.log('📊 Content length: 341 characters\n');
  
  // Monitor processing state changes every 30 seconds for up to 5 minutes
  const maxChecks = 10;
  const checkInterval = 30000; // 30 seconds
  
  for (let i = 0; i < maxChecks; i++) {
    const timeElapsed = (i * 30);
    console.log(`⏱️  ${timeElapsed}s: Checking processing state...`);
    
    try {
      // Check queue status
      const queueResult = execSync(`
        source .env && psql "$DATABASE_URL" -t -A -c "
        SELECT processing_state FROM agent_queue WHERE dump_id = '${dumpId}';
        "
      `, { encoding: 'utf8' }).trim();
      
      console.log(`   Queue State: ${queueResult || 'not_in_queue'}`);
      
      // Check for created substrate
      const substateResults = execSync(`
        source .env && psql "$DATABASE_URL" -c "
        -- Check blocks
        SELECT 'Blocks:' as type, COUNT(*) as count FROM blocks 
        WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1';
        
        -- Check context items  
        SELECT 'Context Items:' as type, COUNT(*) as count FROM context_items 
        WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1';
        
        -- Check proposals
        SELECT 'Proposals:' as type, COUNT(*) as count FROM proposals 
        WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1';
        
        -- Check relationships
        SELECT 'Relationships:' as type, COUNT(*) as count FROM context_item_relationships 
        WHERE workspace_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1';
        "
      `, { encoding: 'utf8' });
      
      console.log('   Substrate counts:');
      console.log(substateResults.split('\n').filter(line => line.includes('|')).slice(1, -1).map(line => `     ${line}`).join('\n'));
      
      // If processing completed, check for success
      if (queueResult === 'completed') {
        console.log('\n🎉 Processing completed! Analyzing results...');
        break;
      } else if (queueResult === 'failed') {
        console.log('\n❌ Processing failed. Checking for error details...');
        
        const errorResult = execSync(`
          source .env && psql "$DATABASE_URL" -t -A -c "
          SELECT error_message FROM agent_queue WHERE dump_id = '${dumpId}';
          "
        `, { encoding: 'utf8' }).trim();
        
        console.log(`   Error: ${errorResult || 'No error message'}`);
        break;
      }
      
      console.log('');
      
      // Wait before next check (except on last iteration)
      if (i < maxChecks - 1) {
        await new Promise(resolve => setTimeout(resolve, checkInterval));
      }
      
    } catch (error) {
      console.error(`   Error checking status: ${error.message}`);
    }
  }
  
  // Final comprehensive check
  console.log('\n📊 Final Substrate Scaffolding Results:');
  console.log('──────────────────────────────────────');
  
  try {
    const finalResults = execSync(`
      source .env && psql "$DATABASE_URL" -c "
      SELECT 
        'P0 (Raw Dumps)' as component,
        COUNT(*) as count,
        CASE WHEN COUNT(*) > 0 THEN '✅' ELSE '❌' END as status
      FROM raw_dumps 
      WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1'
      
      UNION ALL
      
      SELECT 
        'P1 (Blocks)' as component,
        COUNT(*) as count,
        CASE WHEN COUNT(*) > 0 THEN '✅' ELSE '❌' END as status
      FROM blocks 
      WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1'
      
      UNION ALL
      
      SELECT 
        'P1 (Context Items)' as component,
        COUNT(*) as count,
        CASE WHEN COUNT(*) > 0 THEN '✅' ELSE '❌' END as status
      FROM context_items 
      WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1'
      
      UNION ALL
      
      SELECT 
        'P1 (Proposals)' as component,
        COUNT(*) as count,
        CASE WHEN COUNT(*) > 0 THEN '✅' ELSE '❌' END as status
      FROM proposals 
      WHERE basket_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1'
      
      UNION ALL
      
      SELECT 
        'P2 (Relationships)' as component,
        COUNT(*) as count,
        CASE WHEN COUNT(*) > 0 THEN '✅' ELSE '❌' END as status
      FROM context_item_relationships 
      WHERE workspace_id = 'fa622620-824e-4734-b4f1-d47a733a0ec1';
      "
    `, { encoding: 'utf8' });
    
    console.log(finalResults);
    
  } catch (error) {
    console.error(`Error getting final results: ${error.message}`);
  }
}

monitorProcessing().catch(console.error);