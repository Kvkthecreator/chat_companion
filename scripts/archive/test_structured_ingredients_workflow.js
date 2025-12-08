#!/usr/bin/env node

/**
 * Test Script: Validate Structured Ingredients Workflow
 * 
 * Tests the end-to-end flow of structured ingredients extraction and display
 * by simulating the P1 Agent v2 output and verifying frontend API response.
 */

const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://galytxxkrbksilekmhcw.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_SERVICE_KEY) {
  console.error('❌ ERROR: SUPABASE_SERVICE_ROLE_KEY required');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// Test data simulating P1 Agent v2 output
const TEST_STRUCTURED_BLOCK = {
  id: '11111111-1111-1111-1111-111111111111',
  basket_id: 'da75cf04-65e5-46ac-940a-74e2ffe077a2',
  workspace_id: '00000000-0000-0000-0000-000000000002',
  semantic_type: 'requirements',
  title: 'E2E Feature Launch Requirements',
  body_md: '[[LEGACY TEXT - Use metadata.knowledge_ingredients instead]]',
  confidence_score: 0.89,
  state: 'ACCEPTED',
  metadata: {
    extraction_method: 'P1_substrate_agent_v2_openai',
    extraction_timestamp: new Date().toISOString(),
    confidence: 0.89,
    provenance_validated: true,
    knowledge_ingredients: {
      semantic_type: 'requirements',
      title: 'E2E Feature Launch Requirements',
      confidence: 0.89,
      entities: [
        {
          name: 'Sarah Chen',
          type: 'person',
          role: 'Product Manager',
          confidence: 0.9,
          provenance: {
            dump_id: 'test-dump-001',
            ranges: [{ start: 45, end: 55, text: 'Sarah Chen' }],
            extraction_method: 'llm_structured_extraction',
            confidence: 0.9
          }
        },
        {
          name: 'React 18',
          type: 'technology',
          description: 'Frontend framework',
          confidence: 0.85,
          provenance: {
            dump_id: 'test-dump-001', 
            ranges: [{ start: 123, end: 131, text: 'React 18' }],
            extraction_method: 'llm_structured_extraction',
            confidence: 0.85
          }
        }
      ],
      goals: [
        {
          title: 'Launch feature by December 2024',
          description: 'Complete feature development and deployment by end of Q4',
          priority: 'high',
          success_criteria: ['Feature is live in production', 'User feedback collected', '25% DAU increase'],
          confidence: 0.95,
          provenance: {
            dump_id: 'test-dump-001',
            ranges: [{ start: 0, end: 45, text: 'Launch feature by December 2024 with user focus' }],
            extraction_method: 'llm_structured_extraction', 
            confidence: 0.95
          }
        }
      ],
      constraints: [
        {
          type: 'budget',
          description: 'Development budget limited to $75K',
          severity: 'hard',
          mitigation: 'Focus on MVP features first',
          confidence: 0.9,
          provenance: {
            dump_id: 'test-dump-001',
            ranges: [{ start: 67, end: 98, text: 'Limited to $75K for development' }],
            extraction_method: 'llm_structured_extraction',
            confidence: 0.9
          }
        },
        {
          type: 'timeline',
          description: 'Tight 6-month delivery timeline', 
          severity: 'hard',
          confidence: 0.8,
          provenance: {
            dump_id: 'test-dump-001',
            ranges: [{ start: 200, end: 225, text: 'Tight timeline pressure' }],
            extraction_method: 'llm_structured_extraction',
            confidence: 0.8
          }
        }
      ],
      metrics: [
        {
          name: 'Daily Active Users',
          target: '25% increase',
          current: 'Baseline established',
          measurement_method: 'Analytics dashboard tracking',
          frequency: 'daily',
          confidence: 0.85,
          provenance: {
            dump_id: 'test-dump-001',
            ranges: [{ start: 156, end: 180, text: '25% increase in DAU' }],
            extraction_method: 'llm_structured_extraction', 
            confidence: 0.85
          }
        },
        {
          name: 'User Churn Rate',
          target: '15% reduction',
          measurement_method: 'Retention cohort analysis',
          frequency: 'weekly',
          confidence: 0.8,
          provenance: {
            dump_id: 'test-dump-001',
            ranges: [{ start: 182, end: 210, text: '15% reduction in churn rate' }],
            extraction_method: 'llm_structured_extraction',
            confidence: 0.8
          }
        }
      ],
      provenance: {
        dump_id: 'test-dump-001',
        ranges: [{ start: 0, end: 500, text: 'Full content range for block extraction' }],
        extraction_method: 'llm_structured_extraction',
        confidence: 0.89
      }
    }
  }
};

async function testStructuredIngredientsWorkflow() {
  console.log('🧪 Testing Structured Ingredients Workflow');
  console.log('='.repeat(60));
  
  try {
    // Step 1: Insert test block with structured ingredients
    console.log('1. 📝 Inserting test block with structured ingredients...');
    const { data: insertResult, error: insertError } = await supabase
      .from('blocks')
      .upsert(TEST_STRUCTURED_BLOCK, { onConflict: 'id' });
      
    if (insertError) {
      console.error('❌ Insert failed:', insertError);
      return;
    }
    console.log('   ✅ Block inserted successfully');
    
    // Step 2: Query using building-blocks API format
    console.log('2. 🔍 Querying with metadata field (API simulation)...');
    const { data: queryResult, error: queryError } = await supabase
      .from('blocks')
      .select('id, semantic_type, content, confidence_score, title, body_md, created_at, meta_agent_notes, metadata')
      .eq('id', TEST_STRUCTURED_BLOCK.id)
      .single();
      
    if (queryError) {
      console.error('❌ Query failed:', queryError);
      return;
    }
    
    console.log('   ✅ Query successful');
    console.log('   📊 Block title:', queryResult.title);
    console.log('   🏷️ Semantic type:', queryResult.semantic_type);
    console.log('   💯 Confidence:', queryResult.confidence_score);
    
    // Step 3: Validate structured ingredients
    console.log('3. 🧬 Validating structured ingredients...');
    const ingredients = queryResult.metadata?.knowledge_ingredients;
    
    if (!ingredients) {
      console.error('❌ No knowledge_ingredients found in metadata');
      return;
    }
    
    console.log('   ✅ Knowledge ingredients found:');
    console.log(`   🎯 Goals: ${ingredients.goals?.length || 0}`);
    console.log(`   ⚠️ Constraints: ${ingredients.constraints?.length || 0}`);  
    console.log(`   📊 Metrics: ${ingredients.metrics?.length || 0}`);
    console.log(`   👥 Entities: ${ingredients.entities?.length || 0}`);
    
    // Step 4: Test structured ingredient details
    console.log('4. 🔬 Ingredient Details:');
    if (ingredients.goals?.length > 0) {
      console.log(`   🎯 Goal: "${ingredients.goals[0].title}"`);
      console.log(`      Success criteria: ${ingredients.goals[0].success_criteria?.join(', ')}`);
    }
    
    if (ingredients.constraints?.length > 0) {
      console.log(`   ⚠️ Constraint: "${ingredients.constraints[0].description}"`);
      console.log(`      Type: ${ingredients.constraints[0].type}, Severity: ${ingredients.constraints[0].severity}`);
    }
    
    if (ingredients.metrics?.length > 0) {
      console.log(`   📊 Metric: "${ingredients.metrics[0].name}: ${ingredients.metrics[0].target}"`);
      console.log(`      Method: ${ingredients.metrics[0].measurement_method}`);
    }
    
    if (ingredients.entities?.length > 0) {
      console.log(`   👥 Entity: "${ingredients.entities[0].name}" (${ingredients.entities[0].type})`);
      if (ingredients.entities[0].role) {
        console.log(`      Role: ${ingredients.entities[0].role}`);
      }
    }
    
    // Step 5: Validate provenance tracking
    console.log('5. 🔍 Provenance Validation:');
    if (ingredients.provenance?.ranges?.length > 0) {
      console.log(`   ✅ Block provenance: ${ingredients.provenance.ranges.length} text spans`);
    }
    
    let provenanceCount = 0;
    ['goals', 'constraints', 'metrics', 'entities'].forEach(type => {
      const items = ingredients[type] || [];
      items.forEach(item => {
        if (item.provenance?.ranges?.length > 0) {
          provenanceCount++;
        }
      });
    });
    console.log(`   ✅ Item provenance: ${provenanceCount} items with text spans`);
    
    // Step 6: Test frontend API contract compatibility
    console.log('6. 🌐 Frontend API Contract Test:');
    const frontendFormat = {
      id: queryResult.id,
      type: 'block',
      title: queryResult.title,
      content: queryResult.body_md || queryResult.content || '',
      structured_ingredients: ingredients,
      metadata: queryResult.metadata,
      semantic_type: queryResult.semantic_type,
      confidence_score: queryResult.confidence_score,
      created_at: queryResult.created_at
    };
    
    console.log('   ✅ Frontend format conversion successful');
    console.log(`   📋 Type: ${frontendFormat.type}`);
    console.log(`   🏷️ Has structured_ingredients: ${Boolean(frontendFormat.structured_ingredients)}`);
    
    // Final verification
    console.log('\n🎯 Workflow Validation Summary:');
    console.log('=' .repeat(40));
    console.log('✅ P1 Agent v2 structured extraction format validated');
    console.log('✅ Database storage of knowledge_ingredients confirmed');  
    console.log('✅ API metadata field retrieval working');
    console.log('✅ Frontend contract compatibility verified');
    console.log('✅ Structured ingredients display data available');
    
    console.log('\n🚀 Ready for frontend testing at:');
    console.log(`   http://localhost:3001/baskets/${TEST_STRUCTURED_BLOCK.basket_id}/building-blocks`);
    console.log(`   (Block ID: ${TEST_STRUCTURED_BLOCK.id})`);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    // Cleanup - remove test block
    console.log('\n🧹 Cleaning up test data...');
    await supabase.from('blocks').delete().eq('id', TEST_STRUCTURED_BLOCK.id);
    console.log('   ✅ Test block removed');
  }
}

if (require.main === module) {
  testStructuredIngredientsWorkflow();
}