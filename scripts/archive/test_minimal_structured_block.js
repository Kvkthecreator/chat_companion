#!/usr/bin/env node

/**
 * Test Minimal Structured Block 
 * Find the minimal valid structured ingredient format
 */

const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://galytxxkrbksilekmhcw.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_SERVICE_KEY) {
  console.error('❌ ERROR: SUPABASE_SERVICE_ROLE_KEY required');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// Minimal structured block that meets validation
const MINIMAL_BLOCK = {
  id: '33333333-3333-3333-3333-333333333333',
  basket_id: 'da75cf04-65e5-46ac-940a-74e2ffe077a2',
  workspace_id: '00000000-0000-0000-0000-000000000002',
  semantic_type: 'test',
  title: 'Minimal Test Block',
  body_md: 'Test content',
  confidence_score: 0.8,
  state: 'ACCEPTED',
  extraction_method: 'llm_structured_v2',
  provenance_validated: true,
  ingredient_version: '1.0',
  metadata: {
    extraction_method: 'P1_substrate_agent_v2_openai',
    provenance_validated: true,
    knowledge_ingredients: {
      semantic_type: 'test',
      title: 'Minimal Test Block', 
      confidence: 0.8,
      entities: [
        {
          name: 'Test Entity',
          type: 'concept',
          confidence: 0.8
        }
      ],
      goals: [
        {
          title: 'Test Goal',
          description: 'A test goal',
          confidence: 0.8
        }
      ],
      constraints: [],
      metrics: [],
      provenance: {
        dump_id: 'test-dump-minimal',
        ranges: [{ start: 0, end: 12, text: 'Test content' }],
        extraction_method: 'llm_structured_extraction',
        confidence: 0.8
      }
    }
  }
};

async function testMinimalBlock() {
  console.log('🧪 Testing Minimal Structured Block');
  console.log('=' .repeat(50));
  
  try {
    // Test validation function directly first
    console.log('1. 🔍 Testing validation function...');
    const { data: validationResult, error: validationError } = await supabase
      .rpc('validate_structured_ingredient_metadata', { metadata_json: MINIMAL_BLOCK.metadata });
      
    if (validationError) {
      console.error('❌ Validation function error:', validationError);
      return;
    }
    
    console.log(`   Validation result: ${validationResult}`);
    
    if (!validationResult) {
      console.log('❌ Metadata does not pass validation');
      console.log('📋 Metadata structure:', JSON.stringify(MINIMAL_BLOCK.metadata, null, 2));
      return;
    }
    
    // Try inserting minimal block
    console.log('2. 📝 Inserting minimal structured block...');
    const { data, error } = await supabase
      .from('blocks')
      .upsert(MINIMAL_BLOCK, { onConflict: 'id' })
      .select()
      .single();
      
    if (error) {
      console.error('❌ Insert failed:', error);
      return;
    }
    
    console.log('✅ Minimal block created successfully!');
    console.log(`   ID: ${data.id}`);
    console.log(`   Title: ${data.title}`);
    
    // Test API retrieval
    console.log('3. 🔍 Testing API retrieval...');
    const { data: apiData, error: apiError } = await supabase
      .from('blocks')
      .select('id, semantic_type, title, metadata')
      .eq('id', MINIMAL_BLOCK.id)
      .single();
      
    if (apiError) {
      console.error('❌ API test failed:', apiError);
      return;
    }
    
    console.log('✅ API retrieval successful');
    console.log(`   Has knowledge_ingredients: ${Boolean(apiData.metadata?.knowledge_ingredients)}`);
    
    if (apiData.metadata?.knowledge_ingredients) {
      const ingredients = apiData.metadata.knowledge_ingredients;
      console.log('🧬 Retrieved Ingredients:');
      console.log(`   🎯 Goals: ${ingredients.goals?.length || 0}`);
      console.log(`   👥 Entities: ${ingredients.entities?.length || 0}`);
    }
    
    console.log('\n🌐 Frontend Test URL:');
    console.log(`   http://localhost:3001/baskets/${MINIMAL_BLOCK.basket_id}/building-blocks`);
    console.log(`   Look for block: "${MINIMAL_BLOCK.title}"`);
    console.log('   Click to see structured ingredients in modal');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

if (require.main === module) {
  testMinimalBlock();
}