#!/usr/bin/env node

/**
 * Test Substrate Scaffolding Pipeline
 * 
 * Tests the complete pipeline: P0 → P1 → P2 → P3
 * - P0: raw_dump creation ✓ (we know this works)
 * - P1: context_items/context_blocks extraction
 * - P2: substrate_relationships creation  
 * - P3: reflections generation
 */

const { exec } = require('child_process');
const { randomUUID } = require('crypto');

// Use the same connection string as dump_schema.sh
const PG_URL = "postgresql://postgres.galytxxkrbksilekmhcw:4ogIUdwWzVyPH0nU@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require";

function runQuery(sql) {
  return new Promise((resolve, reject) => {
    exec(`psql "${PG_URL}" -c "${sql.replace(/"/g, '\\"')}"`, (error, stdout, stderr) => {
      if (error) {
        reject({ error, stderr });
        return;
      }
      resolve(stdout);
    });
  });
}

// Test basket and workspace IDs from our debugging
const TEST_BASKET_ID = 'fa622620-824e-4734-b4f1-d47a733a0ec1';
const TEST_WORKSPACE_ID = '99e6bf7d-513c-45ff-9b96-9362bd914d12';

// Rich test content that should trigger semantic extraction
const TEST_CONTENT = `
Project Update: Q4 Website Redesign

Goals:
- Improve user conversion rate by 25%
- Reduce page load time to under 2s
- Implement mobile-first design

Team:
- Sarah Johnson (PM) - project lead
- Mike Chen (Frontend Dev) - React components
- Lisa Rodriguez (UX Designer) - user research

Timeline:
- Phase 1: User research - Complete by Oct 15
- Phase 2: Design mockups - Complete by Nov 1  
- Phase 3: Development - Complete by Dec 15
- Phase 4: Testing & Launch - Complete by Dec 31

Budget: $150,000 allocated
Current spend: $45,000 (30% utilized)

Risks:
- Mobile framework compatibility issues
- Third-party API rate limiting
- Holiday season deployment freeze

Next Actions:
- Schedule user interviews with Sarah
- Review design system with Lisa
- Set up staging environment with Mike
`;

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testSubstrateScaffolding() {
  console.log('🧪 Testing Substrate Scaffolding Pipeline\n');
  
  try {
    // Step 1: Create raw_dump (P0)
    console.log('📥 Step 1: Creating raw_dump (P0)...');
    const dumpId = randomUUID();
    const timestamp = new Date().toISOString();
    
    // Escape the test content for SQL
    const escapedContent = TEST_CONTENT.replace(/'/g, "''").replace(/\n/g, '\\n');
    
    const requestId = randomUUID();
    const insertSql = `
      INSERT INTO raw_dumps (id, basket_id, workspace_id, dump_request_id, text_dump, created_at) 
      VALUES ('${dumpId}', '${TEST_BASKET_ID}', '${TEST_WORKSPACE_ID}', '${requestId}', '${escapedContent}', '${timestamp}')
      RETURNING id;
    `;
    
    try {
      const result = await runQuery(insertSql);
      console.log('✅ Raw dump created:', dumpId);
      console.log('📊 Content length:', TEST_CONTENT.length, 'characters\n');
    } catch (insertError) {
      console.error('❌ Failed to create raw_dump:', insertError);
      return;
    }
    
    // Step 1.5: Check queue processing
    console.log('🔄 Step 1.5: Checking agent queue processing...');
    await sleep(2000);
    
    try {
      const queueSql = `
        SELECT processing_state, COUNT(*) as count
        FROM agent_processing_queue 
        WHERE dump_id = '${dumpId}'
        GROUP BY processing_state;
      `;
      const queueResult = await runQuery(queueSql);
      console.log('📊 Queue status for this dump:');
      console.log(queueResult.trim());
    } catch (queueError) {
      console.error('⚠️  Error checking queue:', queueError);
    }
    
    // Step 2: Wait and check for P1 processing (context_items, blocks)
    console.log('\n🔄 Step 2: Checking P1 processing (context extraction)...');
    
    // Wait longer for async processing
    console.log('   Waiting 15 seconds for async processing...');
    await sleep(15000);
    
    // Check context_items
    let contextItemsCount = 0;
    try {
      const contextItemsSql = `
        SELECT COUNT(*) as count, array_agg(DISTINCT type) as types 
        FROM context_items 
        WHERE basket_id = '${TEST_BASKET_ID}' 
        AND created_at >= '${timestamp}';
      `;
      const contextItemsResult = await runQuery(contextItemsSql);
      const contextItemsMatch = contextItemsResult.match(/\s+(\d+)\s+\|\s+(\{.*?\}|\{NULL\})/);
      contextItemsCount = contextItemsMatch ? parseInt(contextItemsMatch[1]) : 0;
      const contextItemsTypes = contextItemsMatch ? contextItemsMatch[2] : '{}';
      
      console.log(`📋 Context items found: ${contextItemsCount}`);
      if (contextItemsCount > 0) {
        console.log('   Types:', contextItemsTypes);
      }
    } catch (contextError) {
      console.error('⚠️  Error checking context_items:', contextError);
    }
    
    // Check blocks (FIXED: was checking non-existent context_blocks table)
    let blocksCount = 0;
    try {
      const blocksSql = `
        SELECT COUNT(*) as count, array_agg(DISTINCT semantic_type) as types,
               array_agg(DISTINCT CASE WHEN body_md IS NOT NULL THEN 'has_body_md' ELSE 'no_body_md' END) as content_status
        FROM blocks 
        WHERE workspace_id = '${TEST_WORKSPACE_ID}' 
        AND created_at >= '${timestamp}';
      `;
      const blocksResult = await runQuery(blocksSql);
      const blocksMatch = blocksResult.match(/\s+(\d+)\s+\|\s+(\{.*?\}|\{NULL\})/);
      blocksCount = blocksMatch ? parseInt(blocksMatch[1]) : 0;
      const blocksTypes = blocksMatch ? blocksMatch[2] : '{}';
      
      console.log(`🧱 Blocks found: ${blocksCount}`);
      if (blocksCount > 0) {
        console.log('   Types:', blocksTypes);
      }
    } catch (blocksError) {
      console.error('⚠️  Error checking blocks:', blocksError);
    }
    
    // Step 3: Check P2 processing (relationships)
    console.log('\n🔄 Step 3: Checking P2 processing (relationships)...');
    await sleep(3000);
    
    let relationshipsCount = 0;
    try {
      const relationshipsSql = `
        SELECT COUNT(*) as count, array_agg(DISTINCT relationship_type) as types 
        FROM substrate_relationships 
        WHERE basket_id = '${TEST_BASKET_ID}' 
        AND created_at >= '${timestamp}';
      `;
      const relationshipsResult = await runQuery(relationshipsSql);
      const relationshipsMatch = relationshipsResult.match(/\s+(\d+)\s+\|\s+(\{.*?\}|\{NULL\})/);
      relationshipsCount = relationshipsMatch ? parseInt(relationshipsMatch[1]) : 0;
      const relationshipsTypes = relationshipsMatch ? relationshipsMatch[2] : '{}';
      
      console.log(`🔗 Relationships found: ${relationshipsCount}`);
      if (relationshipsCount > 0) {
        console.log('   Types:', relationshipsTypes);
      }
    } catch (relError) {
      console.error('⚠️  Error checking relationships:', relError);
    }
    
    // Step 4: Check P3 processing (reflections)
    console.log('\n🔄 Step 4: Checking P3 processing (reflections)...');
    await sleep(2000);
    
    let reflectionsCount = 0;
    try {
      const reflectionsSql = `
        SELECT COUNT(*) as count 
        FROM reflections_artifact 
        WHERE basket_id = '${TEST_BASKET_ID}' 
        AND computation_timestamp >= '${timestamp}';
      `;
      const reflectionsResult = await runQuery(reflectionsSql);
      const reflectionsMatch = reflectionsResult.match(/\s+(\d+)/);
      reflectionsCount = reflectionsMatch ? parseInt(reflectionsMatch[1]) : 0;
      
      console.log(`💭 Reflections found: ${reflectionsCount}`);
    } catch (reflError) {
      console.error('⚠️  Error checking reflections:', reflError);
    }
    
    // Summary
    console.log('\n📊 Substrate Scaffolding Test Results:');
    console.log('─'.repeat(50));
    console.log(`✅ P0 (Raw Dump):     1 created`);
    console.log(`${contextItemsCount > 0 ? '✅' : '❌'} P1a (Context Items): ${contextItemsCount} created`);
    console.log(`${blocksCount > 0 ? '✅' : '❌'} P1b (Blocks): ${blocksCount} created`);
    console.log(`${relationshipsCount > 0 ? '✅' : '❌'} P2 (Relationships):  ${relationshipsCount} created`);
    console.log(`${reflectionsCount > 0 ? '✅' : '❌'} P3 (Reflections):    ${reflectionsCount} created`);
    
    if (contextItemsCount === 0 && blocksCount === 0) {
      console.log('\n⚠️  WARNING: No semantic extraction occurred (P1 not working)');
      console.log('   This suggests the substrate scaffolding pipeline is not processing raw_dumps');
    }
    
    if (relationshipsCount === 0) {
      console.log('\n⚠️  WARNING: No relationships created (P2 not working)');
    }
    
    if (reflectionsCount === 0) {
      console.log('\n⚠️  WARNING: No reflections generated (P3 not working)');
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test
testSubstrateScaffolding();