#!/usr/bin/env node

/**
 * Test script for building-blocks CRUD operations
 * Run: node test-crud-operations.js
 */

const BASKET_ID = '1c4955b8-da82-453b-afa2-478b38279eae'; // Replace with actual basket ID
const API_BASE = 'http://localhost:3000';

async function testContextItemCreation() {
  console.log('\n🧪 Testing Context Item Creation...');
  
  try {
    const response = await fetch(`${API_BASE}/api/work`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        // Add authentication headers as needed
      },
      body: JSON.stringify({
        work_type: 'MANUAL_EDIT',
        work_payload: {
          basket_id: BASKET_ID,
          operations: [{
            type: 'CreateContextItem',
            data: {
              label: 'Test Context Item',
              content: 'This is a test context item created by the test script',
              synonyms: ['test', 'testing', 'verification'],
              kind: 'concept',
              confidence: 0.9
            }
          }]
        },
        priority: 'normal'
      })
    });

    const result = await response.json();
    
    if (response.ok) {
      console.log('✅ Context Item Creation:', result.execution_mode);
      return { success: true, result };
    } else {
      console.log('❌ Context Item Creation failed:', result);
      return { success: false, error: result };
    }
  } catch (error) {
    console.log('❌ Context Item Creation error:', error.message);
    return { success: false, error: error.message };
  }
}

async function testBlockCreation() {
  console.log('\n🧪 Testing Block Creation...');
  
  try {
    const response = await fetch(`${API_BASE}/api/work`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        // Add authentication headers as needed
      },
      body: JSON.stringify({
        work_type: 'MANUAL_EDIT',
        work_payload: {
          basket_id: BASKET_ID,
          operations: [{
            type: 'CreateBlock',
            data: {
              content: 'This is a test block created by the test script for CRUD verification',
              semantic_type: 'test_insight',
              canonical_value: 'Test insight for CRUD verification',
              confidence: 0.9,
              scope: 'LOCAL'
            }
          }]
        },
        priority: 'normal'
      })
    });

    const result = await response.json();
    
    if (response.ok) {
      console.log('✅ Block Creation:', result.execution_mode);
      return { success: true, result };
    } else {
      console.log('❌ Block Creation failed:', result);
      return { success: false, error: result };
    }
  } catch (error) {
    console.log('❌ Block Creation error:', error.message);
    return { success: false, error: error.message };
  }
}

async function testBuildingBlocksFetch() {
  console.log('\n🧪 Testing Building Blocks Fetch...');
  
  try {
    const response = await fetch(`${API_BASE}/api/baskets/${BASKET_ID}/building-blocks`, {
      headers: {
        // Add authentication headers as needed
      }
    });

    const result = await response.json();
    
    if (response.ok) {
      console.log('✅ Building Blocks Fetch successful:');
      console.log(`   - Raw Dumps: ${result.counts.raw_dumps}`);
      console.log(`   - Context Items: ${result.counts.context_items}`);
      console.log(`   - Blocks: ${result.counts.blocks}`);
      console.log(`   - Total: ${result.counts.total}`);
      
      // Show latest items
      if (result.substrates.length > 0) {
        console.log('\nLatest items:');
        result.substrates.slice(0, 3).forEach((item, i) => {
          console.log(`   ${i + 1}. [${item.type}] ${item.title} (${item.agent_stage})`);
        });
      }
      
      return { success: true, result };
    } else {
      console.log('❌ Building Blocks Fetch failed:', result);
      return { success: false, error: result };
    }
  } catch (error) {
    console.log('❌ Building Blocks Fetch error:', error.message);
    return { success: false, error: error.message };
  }
}

async function runTests() {
  console.log('🚀 Starting CRUD Operations Test');
  console.log(`📍 Basket ID: ${BASKET_ID}`);
  console.log(`🌐 API Base: ${API_BASE}`);
  
  const results = {};
  
  // Test in sequence
  results.contextItem = await testContextItemCreation();
  results.block = await testBlockCreation();
  results.fetch = await testBuildingBlocksFetch();
  
  // Summary
  console.log('\n📊 Test Summary:');
  console.log(`   Context Item: ${results.contextItem.success ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Block Creation: ${results.block.success ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Fetch Display: ${results.fetch.success ? '✅ PASS' : '❌ FAIL'}`);
  
  const allPassed = results.contextItem.success && results.block.success && results.fetch.success;
  console.log(`\n${allPassed ? '🎉 All tests passed!' : '⚠️  Some tests failed - check above for details'}`);
  
  return results;
}

// Run tests if script is called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests().catch(console.error);
}

export { runTests, testContextItemCreation, testBlockCreation, testBuildingBlocksFetch };
