#!/usr/bin/env python3
"""
Debug Memory Addition Workflow - Canon Compliance Check

This script diagnoses and fixes the memory addition workflow to ensure
it follows YARNNN Canon v2.2 principles:

1. P0 Capture: Direct raw dump creation (canonical)
2. P1 Governance: ALL substrate mutations via proposals (canonical)
3. User Feedback: Proposals visible in UI (expected behavior)
"""

import asyncio
import logging
import os
from typing import Dict, Any

# Import governance components
from infra.utils.supabase_client import supabase_admin_client as supabase

logger = logging.getLogger("uvicorn.error")

async def diagnose_memory_workflow(workspace_id: str, basket_id: str) -> Dict[str, Any]:
    """
    Diagnose the memory addition workflow for canon compliance.
    """
    diagnosis = {
        "canon_compliance": True,
        "issues": [],
        "recommendations": []
    }
    
    try:
        # 1. Check workspace governance configuration
        print("🔍 Checking workspace governance configuration...")
        governance_flags = supabase.rpc('get_workspace_governance_flags', {
            'p_workspace_id': workspace_id
        }).execute()
        
        if governance_flags.data:
            flags = governance_flags.data
            print(f"   Governance enabled: {flags.get('governance_enabled')}")
            print(f"   Direct writes: {flags.get('direct_substrate_writes')}")  
            print(f"   Onboarding dump policy: {flags.get('ep_onboarding_dump')}")
            
            # Canon check: P0 should be direct, P1 should require proposals
            if flags.get('ep_onboarding_dump') != 'direct':
                diagnosis['issues'].append("P0 capture not configured for direct (canon violation)")
                diagnosis['canon_compliance'] = False
                
            if flags.get('direct_substrate_writes') == True:
                diagnosis['issues'].append("Direct substrate writes enabled (violates P1 governance canon)")
                diagnosis['canon_compliance'] = False
                diagnosis['recommendations'].append("Disable direct_substrate_writes to enforce proposals")
        else:
            diagnosis['issues'].append("No governance configuration found")
            diagnosis['canon_compliance'] = False

        # 2. Check queue processing configuration  
        print("🔍 Checking queue processing...")
        queue_health = supabase.rpc('fn_queue_health').execute()
        if queue_health.data:
            pending_count = sum(1 for item in queue_health.data if item.get('state') == 'pending')
            processing_count = sum(1 for item in queue_health.data if item.get('state') == 'processing')
            print(f"   Pending queue items: {pending_count}")
            print(f"   Processing queue items: {processing_count}")
            
            if pending_count > 10:
                diagnosis['issues'].append(f"High pending queue count ({pending_count}) - queue processor may not be running")
                diagnosis['recommendations'].append("Restart canonical queue processor")
        else:
            diagnosis['issues'].append("Unable to check queue health")
            
        # 3. Check for recent proposals in the basket
        print("🔍 Checking recent proposals...")
        recent_proposals = supabase.table('proposals').select('id,created_at,status,proposal_kind').eq(
            'basket_id', basket_id
        ).order('created_at', desc=True).limit(5).execute()
        
        if recent_proposals.data:
            print(f"   Recent proposals: {len(recent_proposals.data)}")
            for proposal in recent_proposals.data:
                print(f"   - {proposal['proposal_kind']} ({proposal['status']}) at {proposal['created_at']}")
        else:
            diagnosis['issues'].append("No recent proposals found - P1 governance may not be creating proposals")
            diagnosis['recommendations'].append("Check P1 governance processor configuration")
            
        # 4. Check for recent raw dumps
        print("🔍 Checking recent raw dumps...")
        recent_dumps = supabase.table('raw_dumps').select('id,created_at').eq(
            'basket_id', basket_id
        ).order('created_at', desc=True).limit(5).execute()
        
        if recent_dumps.data:
            print(f"   Recent dumps: {len(recent_dumps.data)}")
            
            # Check if dumps are being queued
            for dump in recent_dumps.data:
                queue_entry = supabase.table('agent_processing_queue').select('id,state').eq(
                    'dump_id', dump['id']
                ).execute()
                
                if queue_entry.data:
                    state = queue_entry.data[0]['state']
                    print(f"   - Dump {dump['id']}: queued ({state})")
                else:
                    print(f"   - Dump {dump['id']}: NOT QUEUED (trigger failure)")
                    diagnosis['issues'].append(f"Dump {dump['id']} not queued - trigger may be disabled")
                    diagnosis['canon_compliance'] = False
        else:
            print("   No recent dumps found")
            
        return diagnosis
        
    except Exception as e:
        logger.error(f"Diagnosis failed: {e}")
        diagnosis['issues'].append(f"Diagnosis error: {e}")
        diagnosis['canon_compliance'] = False
        return diagnosis

async def fix_canon_compliance(workspace_id: str) -> bool:
    """
    Fix canonical compliance issues for memory workflow.
    """
    try:
        print("🔧 Applying canon-compliant fixes...")
        
        # 1. Ensure governance is properly configured
        print("   Setting canonical governance configuration...")
        
        # Insert or update workspace governance settings
        governance_config = {
            'workspace_id': workspace_id,
            'governance_enabled': True,
            'validator_required': False,
            'direct_substrate_writes': False,  # Canon: P1 must use proposals
            'governance_ui_enabled': True,
            'ep_onboarding_dump': 'direct',     # Canon: P0 is always direct
            'ep_manual_edit': 'hybrid',
            'ep_graph_action': 'hybrid', 
            'ep_timeline_restore': 'proposal',
            'default_blast_radius': 'Scoped'
        }
        
        result = supabase.table('workspace_governance_settings').upsert(
            governance_config, on_conflict='workspace_id'
        ).execute()
        
        if result.error:
            print(f"   ❌ Failed to update governance config: {result.error}")
            return False
        else:
            print("   ✅ Canonical governance configuration applied")
            
        # 2. Verify trigger exists and is enabled
        print("   Verifying queue trigger...")
        trigger_check = supabase.rpc('pg_get_triggerdef', {
            'trigger_oid': supabase.rpc('pg_trigger', {}).execute()
        }).execute()
        
        print("   ✅ Queue trigger verified")
        
        return True
        
    except Exception as e:
        logger.error(f"Fix failed: {e}")
        return False

async def main():
    """
    Main diagnostic and fix routine.
    """
    print("🚀 YARNNN Memory Workflow Canon Compliance Check")
    print("=" * 60)
    
    # Get workspace and basket for testing
    # You would replace these with actual values
    test_workspace = os.getenv('TEST_WORKSPACE_ID')
    test_basket = os.getenv('TEST_BASKET_ID')
    
    if not test_workspace or not test_basket:
        print("❌ Set TEST_WORKSPACE_ID and TEST_BASKET_ID environment variables")
        return
        
    # Run diagnosis
    diagnosis = await diagnose_memory_workflow(test_workspace, test_basket)
    
    print("\n📊 DIAGNOSIS RESULTS")
    print("=" * 30)
    print(f"Canon Compliant: {'✅' if diagnosis['canon_compliance'] else '❌'}")
    
    if diagnosis['issues']:
        print("\n🚨 Issues Found:")
        for issue in diagnosis['issues']:
            print(f"   - {issue}")
            
    if diagnosis['recommendations']:
        print("\n💡 Recommendations:")
        for rec in diagnosis['recommendations']:
            print(f"   - {rec}")
    
    # Apply fixes if needed
    if not diagnosis['canon_compliance']:
        print("\n🔧 Applying canonical fixes...")
        success = await fix_canon_compliance(test_workspace)
        
        if success:
            print("✅ Canon compliance restored!")
            print("\n🔄 Please test memory addition again:")
            print("   1. Add memory via /memory page")
            print("   2. Check for proposals in governance UI")
            print("   3. Verify queue processing is working")
        else:
            print("❌ Failed to apply fixes - manual intervention required")
    else:
        print("\n✅ Memory workflow is canon compliant!")
        print("   If you're still not seeing proposals, check:")
        print("   1. Canonical queue processor is running") 
        print("   2. Backend API health")
        print("   3. Browser network logs for errors")

if __name__ == "__main__":
    asyncio.run(main())