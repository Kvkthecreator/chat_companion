#!/usr/bin/env node

/**
 * Seed Script: Create TEST_BASKET_ID for E2E Testing
 * 
 * This script ensures that the TEST_BASKET_ID exists with proper test data
 * for running E2E tests in CI environments.
 * 
 * Usage: node scripts/seed-test-basket.js
 */

const { createClient } = require('@supabase/supabase-js');

// Configuration from environment variables
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://galytxxkrbksilekmhcw.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const TEST_BASKET_ID = process.env.TEST_BASKET_ID || 'da75cf04-65e5-46ac-940a-74e2ffe077a2';
let TEST_USER_ID = process.env.TEST_USER_ID || '00000000-0000-0000-0000-000000000001';
const TEST_WORKSPACE_ID = process.env.TEST_WORKSPACE_ID || '00000000-0000-0000-0000-000000000002';

if (!SUPABASE_SERVICE_KEY) {
  console.error('❌ ERROR: SUPABASE_SERVICE_ROLE_KEY environment variable is required');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

async function seedTestBasket() {
  console.log('🌱 Seeding TEST_BASKET_ID for E2E testing...');
  console.log(`📊 Supabase URL: ${SUPABASE_URL}`);
  console.log(`📦 Test Basket ID: ${TEST_BASKET_ID}`);
  console.log(`👤 Test User ID: ${TEST_USER_ID}`);
  console.log(`🏢 Test Workspace ID: ${TEST_WORKSPACE_ID}`);
  console.log('');

  try {
    // 1. Ensure test user exists in auth.users
    console.log('1. Ensuring test user exists...');
    const { data: existingUser, error: userCheckError } = await supabase.auth.admin.getUserById(TEST_USER_ID);
    
    if (userCheckError && userCheckError.message.includes('User not found')) {
      console.log('   Creating test user...');
      const { data: newUser, error: createUserError } = await supabase.auth.admin.createUser({
        user_id: TEST_USER_ID,
        email: 'test@example.com',
        password: 'test-password-123',
        email_confirm: true,
        user_metadata: {
          name: 'E2E Test User',
          role: 'test'
        }
      });
      
      if (createUserError) {
        if (createUserError.code === 'email_exists') {
          console.log('   ⚠️ User with email already exists, continuing with existing user');
          // Get the existing user ID
          const { data: users } = await supabase.auth.admin.listUsers();
          const existingUser = users.users?.find(u => u.email === 'test@example.com');
          if (existingUser) {
            console.log(`   📝 Using existing user ID: ${existingUser.id}`);
            // Update our TEST_USER_ID to match the existing user
            TEST_USER_ID = existingUser.id;
          }
        } else {
          console.error('   ❌ Failed to create test user:', createUserError);
        }
      } else {
        console.log('   ✅ Test user created successfully');
      }
    } else if (userCheckError) {
      console.error('   ❌ Error checking test user:', userCheckError);
    } else {
      console.log('   ✅ Test user already exists');
    }

    // 2. Ensure test workspace exists
    console.log('2. Ensuring test workspace exists...');
    const { data: workspace, error: workspaceError } = await supabase
      .from('workspaces')
      .upsert({
        id: TEST_WORKSPACE_ID,
        name: 'E2E Test Workspace',
        owner_id: TEST_USER_ID,
        is_demo: true
      }, { onConflict: 'id' })
      .select()
      .single();

    if (workspaceError) {
      console.error('   ❌ Failed to create/update test workspace:', workspaceError);
    } else {
      console.log('   ✅ Test workspace ready');
    }

    // 3. Ensure test basket exists
    console.log('3. Ensuring test basket exists...');
    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .upsert({
        id: TEST_BASKET_ID,
        name: 'E2E Test Basket - Substrate Composition',
        user_id: TEST_USER_ID,
        workspace_id: TEST_WORKSPACE_ID,
        status: 'ACTIVE',
        origin_template: 'e2e_testing',
        tags: ['e2e', 'substrate_canon_v1.3.1']
      }, { onConflict: 'id' })
      .select()
      .single();

    if (basketError) {
      console.error('   ❌ Failed to create/update test basket:', basketError);
      return;
    } else {
      console.log('   ✅ Test basket ready');
    }

    // 4. Create sample documents for testing
    console.log('4. Creating sample documents...');
    const sampleDocuments = [
      {
        id: '11111111-1111-1111-1111-111111111111',
        basket_id: TEST_BASKET_ID,
        title: 'E2E Test Document - Multi-Substrate',
        metadata: { test_purpose: 'substrate_composition', seed_created: true }
      },
      {
        id: '22222222-2222-2222-2222-222222222222',
        basket_id: TEST_BASKET_ID,
        title: 'E2E Test Document - Graph Visualization',
        metadata: { test_purpose: 'graph_view', seed_created: true }
      }
    ];

    const { data: documents, error: docsError } = await supabase
      .from('documents')
      .upsert(sampleDocuments, { onConflict: 'id' })
      .select();

    if (docsError) {
      console.error('   ❌ Failed to create sample documents:', docsError);
    } else {
      console.log(`   ✅ Created ${documents.length} sample documents`);
    }

    // 5. Create sample blocks
    console.log('5. Creating sample blocks...');
    const sampleBlocks = [
      {
        id: '33333333-3333-3333-3333-333333333333',
        basket_id: TEST_BASKET_ID,
        title: 'E2E Test Block - Primary Content',
        body_md: 'This is a test block created for E2E testing of substrate composition. It contains meaningful content for document references.',
        state: 'active',
        version: 1,
        metadata: { test_purpose: 'reference_testing', seed_created: true }
      },
      {
        id: '44444444-4444-4444-4444-444444444444',
        basket_id: TEST_BASKET_ID,
        title: 'E2E Test Block - Supporting Material',
        body_md: 'This is supporting content for testing multi-substrate document composition workflows.',
        state: 'active',
        version: 1,
        metadata: { test_purpose: 'supporting_reference', seed_created: true }
      }
    ];

    const { data: blocks, error: blocksError } = await supabase
      .from('context_blocks')
      .upsert(sampleBlocks, { onConflict: 'id' })
      .select();

    if (blocksError) {
      console.error('   ❌ Failed to create sample blocks:', blocksError);
    } else {
      console.log(`   ✅ Created ${blocks.length} sample blocks`);
    }

    // 6. Create sample dumps
    console.log('6. Creating sample dumps...');
    const sampleDumps = [
      {
        id: '55555555-5555-5555-5555-555555555555',
        basket_id: TEST_BASKET_ID,
        source_type: 'e2e_test',
        char_count: 250,
        preview: 'E2E test dump for substrate composition testing',
        metadata: { test_purpose: 'dump_reference', seed_created: true }
      }
    ];

    const { data: dumps, error: dumpsError } = await supabase
      .from('raw_dumps')
      .upsert(sampleDumps, { onConflict: 'id' })
      .select();

    if (dumpsError) {
      console.error('   ❌ Failed to create sample dumps:', dumpsError);
    } else {
      console.log(`   ✅ Created ${dumps.length} sample dumps`);
    }

    // 7. Create sample context items
    console.log('7. Creating sample context items...');
    const sampleContextItems = [
      {
        id: '66666666-6666-6666-6666-666666666666',
        basket_id: TEST_BASKET_ID,
        content_text: 'E2E testing requirement for substrate composition workflows',
        context_type: 'requirement',
        is_validated: true,
        metadata: { test_purpose: 'context_reference', seed_created: true }
      }
    ];

    const { data: contextItems, error: contextError } = await supabase
      .from('context_items')
      .upsert(sampleContextItems, { onConflict: 'id' })
      .select();

    if (contextError) {
      console.error('   ❌ Failed to create sample context items:', contextError);
    } else {
      console.log(`   ✅ Created ${contextItems.length} sample context items`);
    }

    // 8. Create substrate references to test composition
    console.log('8. Creating substrate references...');
    const sampleReferences = [
      {
        id: '77777777-7777-7777-7777-777777777777',
        document_id: '11111111-1111-1111-1111-111111111111',
        substrate_type: 'block',
        substrate_id: '33333333-3333-3333-3333-333333333333',
        role: 'primary',
        weight: 0.8,
        snippets: ['meaningful content for document references'],
        metadata: { seed_created: true }
      },
      {
        id: '88888888-8888-8888-8888-888888888888',
        document_id: '11111111-1111-1111-1111-111111111111',
        substrate_type: 'dump',
        substrate_id: '55555555-5555-5555-5555-555555555555',
        role: 'source',
        weight: 0.6,
        snippets: [],
        metadata: { seed_created: true }
      },
      {
        id: '99999999-9999-9999-9999-999999999999',
        document_id: '22222222-2222-2222-2222-222222222222',
        substrate_type: 'context_item',
        substrate_id: '66666666-6666-6666-6666-666666666666',
        role: 'constraint',
        weight: 0.9,
        snippets: ['substrate composition workflows'],
        metadata: { seed_created: true }
      }
    ];

    const { data: references, error: refsError } = await supabase
      .from('substrate_references')
      .upsert(sampleReferences, { onConflict: 'id' })
      .select();

    if (refsError) {
      console.error('   ❌ Failed to create substrate references:', refsError);
    } else {
      console.log(`   ✅ Created ${references.length} substrate references`);
    }

    // 9. Create timeline events for testing
    console.log('9. Creating timeline events...');
    const timelineEvents = [
      {
        id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        basket_id: TEST_BASKET_ID,
        kind: 'document.created',
        payload: {
          document_id: '11111111-1111-1111-1111-111111111111',
          title: 'E2E Test Document - Multi-Substrate'
        },
        preview: 'Created test document for E2E testing',
        ref_id: '11111111-1111-1111-1111-111111111111'
      },
      {
        id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
        basket_id: TEST_BASKET_ID,
        kind: 'document.block.attached',
        payload: {
          document_id: '11111111-1111-1111-1111-111111111111',
          substrate_type: 'block',
          substrate_id: '33333333-3333-3333-3333-333333333333',
          reference_id: '77777777-7777-7777-7777-777777777777'
        },
        preview: 'Attached block to test document',
        ref_id: '11111111-1111-1111-1111-111111111111'
      }
    ];

    const { data: events, error: eventsError } = await supabase
      .from('timeline_events')
      .upsert(timelineEvents, { onConflict: 'id' })
      .select();

    if (eventsError) {
      console.error('   ❌ Failed to create timeline events:', eventsError);
    } else {
      console.log(`   ✅ Created ${events.length} timeline events`);
    }

    // 10. Verify the setup
    console.log('10. Verifying test data setup...');
    
    const verificationQueries = [
      { name: 'Documents', table: 'documents', column: 'basket_id' },
      { name: 'Blocks', table: 'context_blocks', column: 'basket_id' },
      { name: 'Dumps', table: 'raw_dumps', column: 'basket_id' },
      { name: 'Context Items', table: 'context_items', column: 'basket_id' },
      { name: 'Substrate References', table: 'substrate_references', column: 'document_id', 
        join: 'documents', joinColumn: 'basket_id' },
      { name: 'Timeline Events', table: 'timeline_events', column: 'basket_id' }
    ];

    for (const query of verificationQueries) {
      try {
        let supabaseQuery;
        if (query.join) {
          supabaseQuery = supabase
            .from(query.table)
            .select(`*, ${query.join}(${query.joinColumn})`)
            .eq(`${query.join}.${query.joinColumn}`, TEST_BASKET_ID);
        } else {
          supabaseQuery = supabase
            .from(query.table)
            .select('*')
            .eq(query.column, TEST_BASKET_ID);
        }

        const { data, error } = await supabaseQuery;
        
        if (error) {
          console.error(`   ❌ ${query.name} verification failed:`, error);
        } else {
          console.log(`   ✅ ${query.name}: ${data.length} records`);
        }
      } catch (err) {
        console.error(`   ❌ ${query.name} verification error:`, err);
      }
    }

    console.log('');
    console.log('🎉 TEST_BASKET_ID seeding completed successfully!');
    console.log('');
    console.log('📋 Summary:');
    console.log(`   - Test Basket ID: ${TEST_BASKET_ID}`);
    console.log(`   - Test User ID: ${TEST_USER_ID}`);
    console.log(`   - Test Workspace ID: ${TEST_WORKSPACE_ID}`);
    console.log('   - Sample documents, blocks, dumps, and context items created');
    console.log('   - Substrate references configured for composition testing');
    console.log('   - Timeline events seeded for event testing');
    console.log('');
    console.log('🚀 Ready for E2E testing! Run: npm run test:e2e');

  } catch (error) {
    console.error('❌ Seeding failed:', error);
    process.exit(1);
  }
}

// Run the seeding script
if (require.main === module) {
  seedTestBasket()
    .then(() => process.exit(0))
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}

module.exports = { seedTestBasket };