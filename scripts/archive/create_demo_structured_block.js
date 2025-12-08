#!/usr/bin/env node

/**
 * Create Demo Block with Structured Ingredients
 * 
 * Creates a persistent demo block for manual frontend testing
 */

const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://galytxxkrbksilekmhcw.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_SERVICE_KEY) {
  console.error('❌ ERROR: SUPABASE_SERVICE_ROLE_KEY required');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// Demo block for manual testing
const DEMO_BLOCK = {
  id: '22222222-2222-2222-2222-222222222222',
  basket_id: 'da75cf04-65e5-46ac-940a-74e2ffe077a2',
  workspace_id: '00000000-0000-0000-0000-000000000002',
  semantic_type: 'specification',
  title: 'API Performance Specification',
  body_md: '[[LEGACY: Use structured ingredients instead]]',
  confidence_score: 0.92,
  state: 'ACCEPTED',
  version: 1,
  extraction_method: 'llm_structured_v2',
  provenance_validated: true,
  ingredient_version: '1.0',
  metadata: {
    extraction_method: 'P1_substrate_agent_v2_openai',
    extraction_timestamp: new Date().toISOString(),
    confidence: 0.92,
    provenance_validated: true,
    knowledge_ingredients: {
      semantic_type: 'specification',
      title: 'API Performance Specification',
      confidence: 0.92,
      entities: [
        { name: 'Authentication Service', type: 'system', description: 'Handles user login and security' },
        { name: 'PostgreSQL Database', type: 'infrastructure', description: 'Primary data storage' },
        { name: 'Redis Cache', type: 'infrastructure', description: 'Caching layer for performance' }
      ],
      goals: [
        { 
          title: 'Achieve 99.9% API uptime',
          description: 'Maintain high availability for production services',
          priority: 'high',
          success_criteria: ['< 8.76 hours downtime per year', 'Automated failover working']
        },
        {
          title: 'Optimize API response times',
          description: 'Ensure fast user experience across all endpoints', 
          priority: 'high',
          success_criteria: ['< 100ms average response', '< 2s page load times']
        }
      ],
      constraints: [
        { 
          type: 'performance', 
          description: 'API responses must be under 100ms average',
          severity: 'hard',
          mitigation: 'Implement Redis caching and query optimization'
        },
        { 
          type: 'infrastructure',
          description: 'AWS-only deployment requirement', 
          severity: 'hard',
          mitigation: 'Use AWS services for all components'
        },
        {
          type: 'scalability',
          description: 'Must handle 10K concurrent connections',
          severity: 'soft', 
          mitigation: 'Load balancing and connection pooling'
        }
      ],
      metrics: [
        { 
          name: 'API Response Time',
          target: '< 100ms average', 
          measurement_method: 'Application monitoring (New Relic)',
          frequency: 'real-time'
        },
        { 
          name: 'System Uptime',
          target: '99.9%',
          measurement_method: 'Health check monitoring',
          frequency: 'continuous'  
        },
        {
          name: 'Concurrent User Capacity',
          target: '10,000 users',
          measurement_method: 'Load testing reports',
          frequency: 'monthly'
        }
      ]
    }
  }
};

async function createDemoBlock() {
  console.log('🎨 Creating Demo Block with Rich Structured Ingredients');
  console.log('=' .repeat(60));
  
  try {
    const { data, error } = await supabase
      .from('blocks')
      .upsert(DEMO_BLOCK, { onConflict: 'id' })
      .select()
      .single();
      
    if (error) {
      console.error('❌ Failed to create demo block:', error);
      return;
    }
    
    console.log('✅ Demo block created successfully!');
    console.log('');
    console.log('📋 Block Details:');
    console.log(`   ID: ${data.id}`);
    console.log(`   Title: ${data.title}`);
    console.log(`   Type: ${data.semantic_type}`);
    console.log(`   Confidence: ${data.confidence_score}`);
    console.log('');
    console.log('🧬 Structured Ingredients Summary:');
    const ingredients = data.metadata.knowledge_ingredients;
    console.log(`   🎯 Goals: ${ingredients.goals?.length || 0}`);
    console.log(`   ⚠️ Constraints: ${ingredients.constraints?.length || 0}`);
    console.log(`   📊 Metrics: ${ingredients.metrics?.length || 0}`);
    console.log(`   👥 Entities: ${ingredients.entities?.length || 0}`);
    console.log('');
    console.log('🌐 Test URLs:');
    console.log(`   Building Blocks: http://localhost:3001/baskets/${DEMO_BLOCK.basket_id}/building-blocks`);
    console.log(`   (Look for "${data.title}" with ingredient badges)`);
    console.log('');
    console.log('💡 Expected Frontend Display:');
    console.log('   - Block should show ingredient counts with color badges');
    console.log('   - Modal should display structured data sections');
    console.log('   - Goals in blue, Constraints in red, Metrics in green, Entities in purple');
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

if (require.main === module) {
  createDemoBlock();
}