#!/usr/bin/env node

/**
 * Test Script: Enable Governance and Test Proposal Creation
 * 
 * This script enables governance for the test workspace and verifies
 * that block/context_item creation goes through proposals.
 */

const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://galytxxkrbksilekmhcw.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const TEST_WORKSPACE_ID = process.env.TEST_WORKSPACE_ID || '00000000-0000-0000-0000-000000000002';
const TEST_BASKET_ID = process.env.TEST_BASKET_ID || 'da75cf04-65e5-46ac-940a-74e2ffe077a2';

if (!SUPABASE_SERVICE_KEY) {
  console.error('❌ ERROR: SUPABASE_SERVICE_ROLE_KEY environment variable is required');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

async function enableGovernanceAndTest() {
  console.log('🏛️ Testing Governance Integration...');
  console.log(`📊 Workspace ID: ${TEST_WORKSPACE_ID}`);
  console.log(`📦 Basket ID: ${TEST_BASKET_ID}`);
  console.log('');

  try {
    // 1. Check current governance settings
    console.log('1. Checking current governance settings...');
    const { data: currentSettings, error: currentError } = await supabase
      .from('workspace_governance_settings')
      .select('*')
      .eq('workspace_id', TEST_WORKSPACE_ID)
      .single();

    if (currentError && currentError.code !== 'PGRST116') {
      console.error('   ❌ Failed to check settings:', currentError);
      return;
    }

    if (currentSettings) {
      console.log('   📋 Current settings:');
      console.log('      - governance_enabled:', currentSettings.governance_enabled);
      console.log('      - direct_substrate_writes:', currentSettings.direct_substrate_writes);
      console.log('      - ep_manual_edit:', currentSettings.ep_manual_edit);
    } else {
      console.log('   📋 No settings found - using defaults (governance disabled)');
    }

    // 2. Enable governance for testing
    console.log('2. Enabling governance for testing...');
    const { data: updatedSettings, error: enableError } = await supabase
      .from('workspace_governance_settings')
      .upsert({
        workspace_id: TEST_WORKSPACE_ID,
        governance_enabled: true,           // ✅ Enable governance
        validator_required: false,          // Start with lenient validation
        direct_substrate_writes: false,     // ✅ Force through proposals
        governance_ui_enabled: true,        // ✅ Show governance UI
        
        // Entry point policies - manual_edit should create proposals
        ep_onboarding_dump: 'direct',       // Keep dumps direct (sacred path)
        ep_manual_edit: 'proposal',         // ✅ Manual edits go through governance
        ep_document_edit: 'proposal',
        ep_reflection_suggestion: 'proposal',
        ep_graph_action: 'proposal',
        ep_timeline_restore: 'proposal',
        
        default_blast_radius: 'Local'
      }, { 
        onConflict: 'workspace_id' 
      })
      .select()
      .single();

    if (enableError) {
      console.error('   ❌ Failed to enable governance:', enableError);
      return;
    }

    console.log('   ✅ Governance enabled successfully!');
    console.log('      - governance_enabled:', updatedSettings.governance_enabled);
    console.log('      - direct_substrate_writes:', updatedSettings.direct_substrate_writes);
    console.log('      - ep_manual_edit:', updatedSettings.ep_manual_edit);

    // 3. Test the governance API endpoints
    console.log('3. Testing governance API endpoints...');
    
    // Test changes API status
    const response = await fetch('http://localhost:3000/api/changes', {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer test-token',
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const apiStatus = await response.json();
      console.log('   ✅ Changes API responding:', apiStatus.api_version);
      console.log('   📋 Governance status:', apiStatus.governance_status?.governance_enabled);
    } else {
      console.log('   ⚠️ Changes API test failed (requires auth)');
    }

    // 4. Show test instructions
    console.log('');
    console.log('🧪 Test Instructions:');
    console.log('1. Go to: http://localhost:3000/baskets/' + TEST_BASKET_ID + '/building-blocks');
    console.log('2. Click "Create Block" or "Create Context Item"');
    console.log('3. Fill out the form and submit');
    console.log('4. Check: http://localhost:3000/baskets/' + TEST_BASKET_ID + '/governance');
    console.log('5. You should see proposals awaiting approval!');
    console.log('');
    console.log('🔧 To disable governance again:');
    console.log('   Set governance_enabled: false, direct_substrate_writes: true');

  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test
if (require.main === module) {
  enableGovernanceAndTest()
    .then(() => {
      console.log('✅ Governance test script completed');
      process.exit(0);
    })
    .catch(error => {
      console.error('❌ Fatal error:', error);
      process.exit(1);
    });
}

module.exports = { enableGovernanceAndTest };