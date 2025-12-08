#!/usr/bin/env ts-node

import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  }
);

interface TestData {
  workspace: any;
  basket: any;
  documents: any[];
  substrates: {
    dump: any;
    block: any;
    context_item: any;
    reflection: any;
    timeline_event: any;
  };
}

async function seedTestData(): Promise<TestData> {
  console.log('🌱 Starting E2E test data seeding...');

  try {
    // Create test user if not exists
    const testEmail = 'e2e.test@yarnnn.com';
    const testPassword = 'e2eTestPassword123!';

    let { data: authData, error: authError } = await supabase.auth.signInWithPassword({
      email: testEmail,
      password: testPassword,
    });

    if (authError) {
      // Try creating user
      const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
        email: testEmail,
        password: testPassword,
      });
      
      if (signUpError && !signUpError.message.includes('already registered')) {
        throw signUpError;
      }

      // Sign in again
      const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
        email: testEmail,
        password: testPassword,
      });

      if (signInError) throw signInError;
      authData = signInData;
    }

    const userId = authData.user?.id;
    if (!userId) throw new Error('Could not get user ID');

    console.log('👤 Test user authenticated');

    // Create workspace
    const { data: workspace, error: workspaceError } = await supabase
      .from('workspaces')
      .upsert({
        id: 'canon-workspace-id',
        name: 'Canon Test Workspace',
        user_id: userId,
        created_at: new Date().toISOString()
      }, { onConflict: 'id' })
      .select()
      .single();

    if (workspaceError) throw workspaceError;
    console.log('🏢 Workspace created');

    // Create basket
    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .upsert({
        id: 'canon-basket-id',
        workspace_id: workspace.id,
        status: 'ACTIVE',
        created_at: new Date().toISOString()
      }, { onConflict: 'id' })
      .select()
      .single();

    if (basketError) throw basketError;
    console.log('🧺 Basket created');

    // Create documents
    const documentsData = [
      {
        id: 'canon-doc-1',
        workspace_id: workspace.id,
        title: 'Canon Test Document 1',
        content: 'This is test content for canon compliance',
        created_at: new Date().toISOString()
      },
      {
        id: 'canon-doc-2', 
        workspace_id: workspace.id,
        title: 'Canon Test Document 2',
        content: 'This is another test document',
        created_at: new Date().toISOString()
      }
    ];

    const { data: documents, error: documentsError } = await supabase
      .from('documents')
      .upsert(documentsData, { onConflict: 'id' })
      .select();

    if (documentsError) throw documentsError;
    console.log('📄 Documents created');

    // Create substrate data
    const substrates = {
      dump: null,
      block: null, 
      context_item: null,
      reflection: null,
      timeline_event: null
    };

    // Create raw_dumps
    const { data: rawDump, error: rawDumpError } = await supabase
      .from('raw_dumps')
      .upsert({
        id: 'canon-dump-id',
        workspace_id: workspace.id,
        basket_id: basket.id,
        content: 'Immutable capture content',
        content_type: 'text/plain',
        source_type: 'manual',
        created_at: new Date().toISOString()
      }, { onConflict: 'id' })
      .select()
      .single();

    if (rawDumpError) throw rawDumpError;
    substrates.dump = rawDump;

    // Create context_items  
    const { data: contextItem, error: contextError } = await supabase
      .from('context_items')
      .upsert({
        id: 'canon-context-id',
        workspace_id: workspace.id,
        type: 'yarnnn_system',
        content: 'System context item',
        created_at: new Date().toISOString()
      }, { onConflict: 'id' })
      .select()
      .single();

    if (contextError) throw contextError;
    substrates.context_item = contextItem;

    // Create reflections
    const { data: reflection, error: reflectionError } = await supabase
      .from('reflections')
      .upsert({
        id: 'canon-reflection-id',
        workspace_id: workspace.id,
        content: 'Computed reflection content',
        computed: true,
        created_at: new Date().toISOString()
      }, { onConflict: 'id' })
      .select()
      .single();

    if (reflectionError) throw reflectionError;
    substrates.reflection = reflection;

    // Create timeline_events
    const { data: timelineEvent, error: timelineError } = await supabase
      .from('timeline_events')
      .upsert({
        id: 'canon-event-id',
        workspace_id: workspace.id,
        kind: 'dump.created',
        payload: { dump_id: rawDump.id },
        created_at: new Date().toISOString()
      }, { onConflict: 'id' })
      .select()
      .single();

    if (timelineError) throw timelineError;
    substrates.timeline_event = timelineEvent;

    console.log('📊 Substrates created');

    const testData: TestData = {
      workspace,
      basket,
      documents: documents || [],
      substrates
    };

    console.log('✅ E2E test data seeding complete');
    return testData;

  } catch (error) {
    console.error('❌ Error seeding test data:', error);
    throw error;
  }
}

async function cleanupTestData(): Promise<void> {
  console.log('🧹 Cleaning up test data...');
  
  try {
    // Delete in reverse order to avoid foreign key constraints
    await supabase.from('timeline_events').delete().eq('workspace_id', 'canon-workspace-id');
    await supabase.from('reflections').delete().eq('workspace_id', 'canon-workspace-id');
    await supabase.from('context_items').delete().eq('workspace_id', 'canon-workspace-id');
    await supabase.from('raw_dumps').delete().eq('workspace_id', 'canon-workspace-id');
    await supabase.from('documents').delete().eq('workspace_id', 'canon-workspace-id');
    await supabase.from('baskets').delete().eq('workspace_id', 'canon-workspace-id');
    await supabase.from('workspaces').delete().eq('id', 'canon-workspace-id');
    
    console.log('✅ Test data cleanup complete');
  } catch (error) {
    console.error('❌ Error cleaning up test data:', error);
    throw error;
  }
}

// Exported cleanup function for agent orchestration
export async function cleanup(basketId?: string): Promise<void> {
  try {
    if (basketId) {
      console.log(`🧹 Cleaning up test data for basket: ${basketId}`);
      // Clean specific basket data
      await supabase.from('timeline_events').delete().eq('payload->basket_id', basketId);
      await supabase.from('raw_dumps').delete().eq('basket_id', basketId);
      await supabase.from('baskets').delete().eq('id', basketId);
    } else {
      // Clean all test data
      await cleanupTestData();
    }
  } catch (error) {
    console.warn('Cleanup failed (non-fatal):', error);
  }
}

// Make seeding idempotent
export async function ensureTestData(): Promise<TestData> {
  try {
    // Check if test data already exists
    const { data: existingWorkspace } = await supabase
      .from('workspaces')
      .select('*')
      .eq('id', 'canon-workspace-id')
      .single();

    if (existingWorkspace) {
      console.log('✅ Test data already exists, using existing data');
      
      // Return existing data structure
      const { data: basket } = await supabase
        .from('baskets')
        .select('*')
        .eq('id', 'canon-basket-id')
        .single();

      const { data: documents } = await supabase
        .from('documents')
        .select('*')
        .eq('workspace_id', 'canon-workspace-id');

      return {
        workspace: existingWorkspace,
        basket: basket || null,
        documents: documents || [],
        substrates: {
          dump: null,
          block: null,
          context_item: null,
          reflection: null,
          timeline_event: null
        }
      };
    }

    // Create new test data if it doesn't exist
    return await seedTestData();
  } catch (error) {
    console.log('🌱 Creating fresh test data...');
    return await seedTestData();
  }
}

// CLI interface
async function main() {
  const command = process.argv[2];
  
  try {
    switch (command) {
      case 'seed':
        await seedTestData();
        break;
      case 'cleanup':
        await cleanupTestData();
        break;
      case 'reset':
        await cleanupTestData();
        await seedTestData();
        break;
      case 'ensure':
        await ensureTestData();
        break;
      default:
        console.log(`
Usage: tsx scripts/seed-e2e.ts <command>

Commands:
  seed    - Create test data
  cleanup - Remove test data  
  reset   - Cleanup and then seed fresh data
  ensure  - Create data only if it doesn't exist (idempotent)
        `);
        process.exit(1);
    }
  } catch (error) {
    console.error('Script failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { seedTestData, cleanupTestData };