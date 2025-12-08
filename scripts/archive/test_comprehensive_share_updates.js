#!/usr/bin/env node

/**
 * Test Script: Comprehensive Share Updates Workflow
 * 
 * Tests the new batch processing pipeline:
 * Multiple inputs → unified analysis → single proposal → comprehensive review
 */

const { createClient } = require('@supabase/supabase-js');
const { randomUUID } = require('crypto');

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://galytxxkrbksilekmhcw.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_SERVICE_KEY) {
  console.error('❌ ERROR: SUPABASE_SERVICE_ROLE_KEY required');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// Test data for comprehensive Share Updates
const BATCH_ID = randomUUID();
const TEST_BASKET_ID = 'da75cf04-65e5-46ac-940a-74e2ffe077a2';
const TEST_WORKSPACE_ID = '00000000-0000-0000-0000-000000000002';

const SHARE_UPDATES_BATCH = [
  {
    dump_request_id: randomUUID(),
    text_dump: "Product roadmap Q4: Launch social features, improve performance metrics, target 25% DAU growth. Budget constraints: $150K max. Key stakeholder: Sarah Chen (PM).",
    source_meta: {
      batch_id: BATCH_ID,
      comprehensive_review: true,
      content_type: "strategic_planning"
    }
  },
  {
    dump_request_id: randomUUID(), 
    text_dump: "Technical requirements: React 18 migration, API response time under 100ms, implement Redis caching. Security constraints: OAuth 2.0 compliance required.",
    source_meta: {
      batch_id: BATCH_ID,
      comprehensive_review: true,
      content_type: "technical_specification"
    }
  },
  {
    dump_request_id: randomUUID(),
    text_dump: "User research insights: 78% want better mobile experience, 65% request dark mode, performance is top complaint. Retention goal: reduce churn by 15%.",
    source_meta: {
      batch_id: BATCH_ID,
      comprehensive_review: true,
      content_type: "user_research"
    }
  }
];

async function testComprehensiveShareUpdates() {
  console.log('🚀 Testing Comprehensive Share Updates Workflow');
  console.log('=' .repeat(70));
  console.log(`📦 Batch ID: ${BATCH_ID}`);
  console.log(`🧺 Basket: ${TEST_BASKET_ID}`);
  console.log(`📊 Sources: ${SHARE_UPDATES_BATCH.length} content pieces`);
  console.log('');
  
  try {
    // Step 1: Create comprehensive ingest request
    console.log('1. 📥 Creating comprehensive ingest request...');
    
    const ingestPayload = {
      idempotency_key: randomUUID(),
      basket: { name: "Comprehensive Test Basket" },
      dumps: SHARE_UPDATES_BATCH,
      batch_id: BATCH_ID,
      comprehensive_review: true
    };
    
    // Step 2: Submit to ingest API  
    console.log('2. 🔄 Submitting batch to ingest pipeline...');
    const { data: ingestResult, error: ingestError } = await supabase.rpc('fn_ingest_dumps', {
      p_workspace_id: TEST_WORKSPACE_ID,
      p_basket_id: TEST_BASKET_ID,
      p_dumps: SHARE_UPDATES_BATCH
    });
    
    if (ingestError) {
      console.error('❌ Ingest failed:', ingestError);
      return;
    }
    
    console.log('   ✅ Ingest successful');
    console.log(`   📋 Dumps created: ${ingestResult ? ingestResult.length : 'unknown'}`);
    
    // Step 3: Verify batch metadata was stored  
    console.log('3. 🔍 Verifying batch metadata...');
    const { data: dumpCheck, error: dumpError } = await supabase
      .from('raw_dumps')
      .select('id, source_meta')
      .contains('source_meta', { batch_id: BATCH_ID });
      
    if (dumpError) {
      console.error('❌ Dump verification failed:', dumpError);
      return;
    }
    
    console.log(`   ✅ Found ${dumpCheck.length} dumps with batch metadata`);
    dumpCheck.forEach((dump, i) => {
      console.log(`   📄 Dump ${i+1}: ${dump.id}`);
    });
    
    // Step 4: Check canonical queue for batch processing
    console.log('4. ⚡ Checking canonical queue processing...');
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait for async processing
    
    // Step 5: Verify unified proposal was created
    console.log('5. 🏛️ Checking for comprehensive governance proposal...');
    const { data: proposals, error: proposalError } = await supabase
      .from('proposals') 
      .select('id, proposal_kind, ops, status, metadata')
      .eq('basket_id', TEST_BASKET_ID)
      .eq('metadata->>processing_method', 'share_updates_batch')
      .order('created_at', { ascending: false })
      .limit(1);
      
    if (proposalError) {
      console.error('❌ Proposal check failed:', proposalError);
      return;
    }
    
    if (proposals && proposals.length > 0) {
      const proposal = proposals[0];
      console.log('   ✅ Comprehensive proposal found!');
      console.log(`   🆔 Proposal ID: ${proposal.id}`);
      console.log(`   🏷️ Kind: ${proposal.proposal_kind}`);
      console.log(`   📋 Summary: ${proposal.ops.summary}`);
      console.log(`   📊 Status: ${proposal.status}`);
      
      // Check ops for batch processing indicators
      const ops = proposal.ops;
      if (ops && ops.source_dumps) {
        console.log(`   🔗 Source dumps: ${ops.source_dumps.length}`);
        console.log(`   🧬 Comprehensive analysis: ${ops.comprehensive_analysis}`);
        console.log(`   📦 Blocks created: ${ops.blocks ? ops.blocks.length : 0}`);
      }
    } else {
      console.log('   ⚠️ No comprehensive proposal found yet (may still be processing)');
    }
    
    console.log('');
    console.log('🎯 Test Summary:');
    console.log('=' .repeat(40));
    console.log('✅ Batch ingest with metadata support');
    console.log('✅ Raw dumps created with batch tracking');
    console.log(`${proposals && proposals.length > 0 ? '✅' : '⚠️'} Comprehensive governance proposal`);
    console.log('');
    console.log('🌐 Review URLs:');
    console.log(`   Governance: http://localhost:3001/baskets/${TEST_BASKET_ID}/governance`);
    console.log(`   (Look for "comprehensive_share_updates" proposal)`);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    // Cleanup test data
    console.log('');
    console.log('🧹 Cleaning up test data...');
    
    try {
      // Remove test dumps
      await supabase
        .from('raw_dumps')
        .delete()
        .eq('source_meta->>batch_id', BATCH_ID);
      console.log('   ✅ Test dumps removed');
    } catch (cleanupError) {
      console.log('   ⚠️ Cleanup failed:', cleanupError.message);
    }
  }
}

if (require.main === module) {
  testComprehensiveShareUpdates();
}