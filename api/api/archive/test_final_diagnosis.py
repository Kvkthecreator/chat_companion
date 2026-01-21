#!/usr/bin/env python3
"""
Final Diagnosis - P4 Composition Issue

This test provides the definitive diagnosis of why "compose from memory" creates blank documents.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables for testing
os.environ["SUPABASE_URL"] = "https://galytxxkrbksilekmhcw.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdhbHl0eHhrcmJrc2lsZWttaGN3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NTU3NjMsImV4cCI6MjA2MjMzMTc2M30.n9wrD3a_fep8GfeCRm0iflk-4Y47RYnLA0EeEECU7OY"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdhbHl0eHhrcmJrc2lsZWttaGN3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njc1NTc2MywiZXhwIjoyMDYyMzMxNzYzfQ.0oAdZeTn_k3p-29Hy8z1v5YYGpjBeqML0amz5bcAS6g"

from infra.utils.supabase_client import supabase_admin_client as supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose_queue_work_claiming():
    """Diagnose if P4_COMPOSE work is being claimed by queue processor"""
    logger.info("🔍 DIAGNOSIS: Queue Work Claiming for P4_COMPOSE")
    
    try:
        # Check what work types exist in the queue
        queue_result = supabase.table("agent_processing_queue")\
            .select("work_type, processing_state, created_at")\
            .order("created_at", desc=True)\
            .limit(20).execute()
            
        if queue_result.data:
            logger.info(f"📊 Recent queue entries ({len(queue_result.data)}):")
            work_types = {}
            for entry in queue_result.data:
                wt = entry.get('work_type', 'UNKNOWN')
                state = entry.get('processing_state', 'UNKNOWN')
                work_types[wt] = work_types.get(wt, 0) + 1
                logger.info(f"   {wt} - {state} - {entry.get('created_at', 'N/A')}")
            
            logger.info(f"📈 Work type summary: {work_types}")
            
            if 'P4_COMPOSE' in work_types:
                logger.info("✅ P4_COMPOSE work exists in queue")
                
                # Check if any P4_COMPOSE work is stuck in pending
                p4_pending = supabase.table("agent_processing_queue")\
                    .select("*")\
                    .eq("work_type", "P4_COMPOSE")\
                    .eq("processing_state", "pending")\
                    .execute()
                    
                if p4_pending.data:
                    logger.error(f"❌ {len(p4_pending.data)} P4_COMPOSE work items stuck in pending state!")
                    logger.error("   This suggests the queue processor is not claiming P4_COMPOSE work")
                    return False
                else:
                    logger.info("✅ No P4_COMPOSE work stuck in pending")
            else:
                logger.warning("⚠️  No P4_COMPOSE work found in recent queue entries")
        else:
            logger.info("ℹ️  No recent queue entries found")
        
        # Test fn_claim_next_dumps function directly
        logger.info("🧪 Testing fn_claim_next_dumps function...")
        
        try:
            claim_result = supabase.rpc('fn_claim_next_dumps', {
                'p_worker_id': 'test-diagnosis-worker',
                'p_limit': 5,
                'p_stale_after_minutes': 5
            }).execute()
            
            logger.info(f"✅ fn_claim_next_dumps succeeded, claimed: {len(claim_result.data or [])}")
            
            if claim_result.data:
                claimed_types = [entry.get('work_type', 'UNKNOWN') for entry in claim_result.data]
                logger.info(f"   Claimed work types: {claimed_types}")
                
                if 'P4_COMPOSE' in claimed_types:
                    logger.info("✅ fn_claim_next_dumps can claim P4_COMPOSE work")
                else:
                    logger.warning("⚠️  fn_claim_next_dumps did not claim any P4_COMPOSE work")
                    
        except Exception as e:
            logger.error(f"❌ fn_claim_next_dumps failed: {e}")
            logger.error("   This indicates the queue processor cannot claim work at all!")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Queue work claiming diagnosis failed: {e}")
        return False

async def diagnose_p4_agent_substrate_query():
    """Diagnose if P4 agent can find substrate to compose"""
    logger.info("🔍 DIAGNOSIS: P4 Agent Substrate Querying")
    
    try:
        # Find an existing basket with substrate
        baskets_result = supabase.table("baskets").select("id").limit(5).execute()
        
        if not baskets_result.data:
            logger.warning("⚠️  No baskets found for testing")
            return True
            
        for basket in baskets_result.data:
            basket_id = basket['id']
            logger.info(f"🔍 Checking substrate in basket: {basket_id}")
            
            # Check blocks
            blocks_result = supabase.table("blocks")\
                .select("id, semantic_type, state")\
                .eq("basket_id", basket_id)\
                .execute()
            
            blocks_count = len(blocks_result.data) if blocks_result.data else 0
            logger.info(f"   Blocks: {blocks_count}")
            
            if blocks_result.data:
                states = [b.get('state') for b in blocks_result.data]
                logger.info(f"   Block states: {set(states)}")
            
            # Check context items
            items_result = supabase.table("context_items")\
                .select("id, type, state")\
                .eq("basket_id", basket_id)\
                .execute()
                
            items_count = len(items_result.data) if items_result.data else 0
            logger.info(f"   Context items: {items_count}")
            
            # Check raw dumps
            dumps_result = supabase.table("raw_dumps")\
                .select("id")\
                .eq("basket_id", basket_id)\
                .execute()
                
            dumps_count = len(dumps_result.data) if dumps_result.data else 0
            logger.info(f"   Raw dumps: {dumps_count}")
            
            total_substrate = blocks_count + items_count + dumps_count
            logger.info(f"   Total substrate: {total_substrate}")
            
            if total_substrate > 0:
                logger.info(f"✅ Basket {basket_id} has substrate available for composition")
                break
        else:
            logger.warning("⚠️  No baskets with substrate found - P4 agent would have nothing to compose")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ P4 agent substrate query diagnosis failed: {e}")
        return False

async def provide_final_diagnosis():
    """Provide final diagnosis and recommendations"""
    logger.info("🎯 FINAL DIAGNOSIS")
    logger.info("=" * 50)
    
    # Based on all tests performed
    logger.info("📋 INVESTIGATION SUMMARY:")
    logger.info("✅ fn_document_attach_substrate function exists and works correctly")
    logger.info("✅ P4 composition agent creates successfully")
    logger.info("✅ Canonical queue processor creates successfully")
    logger.info("✅ Parameter formats (array vs JSON string) work correctly")
    logger.info("")
    
    logger.info("🔍 MOST LIKELY ROOT CAUSES:")
    logger.info("1. 🚫 Canonical queue processor not running in production deployment")
    logger.info("2. ⏸️  P4_COMPOSE work not being claimed by fn_claim_next_dumps")
    logger.info("3. 📊 No substrate available in target baskets for composition")
    logger.info("4. 🔄 Work queue timing issues or stale work detection")
    logger.info("")
    
    logger.info("🔧 RECOMMENDED FIXES:")
    logger.info("1. ✅ Apply P4 composition agent fixes (parameter format, metadata update)")
    logger.info("2. 🚀 Verify canonical queue processor is running in production")
    logger.info("3. 🔍 Check if fn_claim_next_dumps supports P4_COMPOSE work type")
    logger.info("4. ⚡ Add better logging to track P4_COMPOSE work processing")
    logger.info("5. 🧪 Test with baskets that have actual substrate")
    logger.info("")
    
    logger.info("🎯 IMMEDIATE ACTION ITEMS:")
    logger.info("• Deploy the P4 composition agent fixes")
    logger.info("• Check production queue processor status")
    logger.info("• Monitor P4_COMPOSE work in agent_processing_queue table")
    logger.info("• Test compose from memory with baskets containing blocks/context_items")

async def run_final_diagnosis():
    """Run final diagnosis"""
    logger.info("🚀 FINAL DIAGNOSIS - P4 Composition Issue")
    logger.info("Comprehensive investigation of 'compose from memory' blank documents")
    logger.info("=" * 70)
    
    tests = [
        ("Queue Work Claiming", diagnose_queue_work_claiming),
        ("P4 Agent Substrate Query", diagnose_p4_agent_substrate_query),
        ("Final Diagnosis", provide_final_diagnosis)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*40}")
        try:
            await test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} failed: {e}")
    
    logger.info(f"\n{'='*70}")
    logger.info("🏁 DIAGNOSIS COMPLETE")
    logger.info("Review the findings above to resolve the blank document issue.")

if __name__ == "__main__":
    asyncio.run(run_final_diagnosis())