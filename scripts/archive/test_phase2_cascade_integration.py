#!/usr/bin/env python3
"""
Test Phase 2: Cascade Integration Implementation

Tests the Canon v2.1 Enhanced Cascade Manager and P1→P2→P3 pipeline flows:
1. Enhanced cascade manager functionality
2. P1→P2 cascade triggering after substrate creation
3. P2→P3 cascade triggering after relationship mapping  
4. Timeline event emission for cascade flows
5. Integration with universal work tracker

This validates Phase 2 Day 3-4 completion per streamlined execution plan.
"""

import sys
import os
import asyncio
import logging
from uuid import uuid4
from datetime import datetime, timezone

# Add API src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "src"))

# Set environment variables for testing
os.environ["SUPABASE_URL"] = "https://galytxxkrbksilekmhcw.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdhbHl0eHhrcmJrc2lsZWttaGN3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NTU3NjMsImV4cCI6MjA2MjMzMTc2M30.n9wrD3a_fep8GfeCRm0iflk-4Y47RYnLA0EeEECU7OY"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdhbHl0eHhrcmJrc2lsZWttaGN3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njc1NTc2MywiZXhwIjoyMDYyMzMxNzYzfQ.0oAdZeTn_k3p-29Hy8z1v5YYGpjBeqML0amz5bcAS6g"

from app.utils.supabase_client import supabase_admin_client as supabase
from services.enhanced_cascade_manager import canonical_cascade_manager, WorkContext
from services.universal_work_tracker import universal_work_tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REAL_WORKSPACE_ID = "31ee30fe-6ae3-4604-ab6d-ac9b9f06dfde"  # From previous tests
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"  # Valid UUID for testing

async def test_enhanced_cascade_manager():
    """Test 1: Enhanced cascade manager basic functionality."""
    logger.info("🧪 Test 1: Enhanced Cascade Manager")
    
    try:
        # Test cascade rule loading
        cascade_rules = canonical_cascade_manager.cascade_rules
        
        expected_rules = ['P1_SUBSTRATE', 'P2_GRAPH', 'P3_REFLECTION']
        found_rules = set(cascade_rules.keys())
        
        if not set(expected_rules).issubset(found_rules):
            logger.error(f"❌ Missing cascade rules: {set(expected_rules) - found_rules}")
            return False
        
        # Test P1 cascade rule
        p1_rule = cascade_rules['P1_SUBSTRATE']
        if p1_rule.triggers_next != 'P2_GRAPH':
            logger.error(f"❌ P1 rule incorrect: triggers {p1_rule.triggers_next}, expected P2_GRAPH")
            return False
        
        # Test P2 cascade rule
        p2_rule = cascade_rules['P2_GRAPH']
        if p2_rule.triggers_next != 'P3_REFLECTION':
            logger.error(f"❌ P2 rule incorrect: triggers {p2_rule.triggers_next}, expected P3_REFLECTION")
            return False
        
        # Test P3 terminal rule
        p3_rule = cascade_rules['P3_REFLECTION']
        if p3_rule.triggers_next is not None:
            logger.error(f"❌ P3 should be terminal: triggers {p3_rule.triggers_next}")
            return False
        
        logger.info("✅ Enhanced cascade manager initialized correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced cascade manager test failed: {e}")
        return False

async def test_p1_substrate_cascade():
    """Test 2: P1→P2 cascade triggering after substrate creation."""
    logger.info("🧪 Test 2: P1→P2 Substrate Cascade")
    
    try:
        # Create test context
        test_proposal_id = str(uuid4())
        test_basket_id = str(uuid4())
        test_user_id = TEST_USER_ID
        
        substrate_created = {
            'blocks': 2,
            'context_items': 1,
            'updates': 0
        }
        
        # Trigger P1→P2 cascade
        cascade_work_id = await canonical_cascade_manager.trigger_p1_substrate_cascade(
            proposal_id=test_proposal_id,
            basket_id=test_basket_id,
            workspace_id=REAL_WORKSPACE_ID,
            user_id=test_user_id,
            substrate_created=substrate_created
        )
        
        if not cascade_work_id:
            logger.error("❌ P1→P2 cascade failed - no work_id returned")
            return False
        
        logger.info(f"✅ P1→P2 cascade triggered successfully: {cascade_work_id}")
        
        # Verify work was created in queue
        work_response = supabase.table("agent_processing_queue").select(
            "work_id, work_type, work_payload, cascade_metadata"
        ).eq("work_id", cascade_work_id).single().execute()
        
        if not work_response.data:
            logger.error("❌ Cascade work not found in queue")
            return False
        
        work = work_response.data
        
        if work['work_type'] != 'P2_GRAPH':
            logger.error(f"❌ Wrong work type: {work['work_type']}, expected P2_GRAPH")
            return False
        
        # Check cascade metadata
        payload = work['work_payload'] or {}
        cascade_source = payload.get('cascade_source', {})
        
        if cascade_source.get('work_type') != 'P1_SUBSTRATE':
            logger.error("❌ Cascade source metadata missing or incorrect")
            return False
        
        logger.info("✅ P1→P2 cascade work created with correct metadata")
        
        # Cleanup
        supabase.table("agent_processing_queue").delete().eq("work_id", cascade_work_id).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ P1→P2 cascade test failed: {e}")
        return False

async def test_p2_graph_cascade():
    """Test 3: P2→P3 cascade triggering after relationship mapping."""
    logger.info("🧪 Test 3: P2→P3 Graph Cascade")
    
    try:
        # Create test context
        test_work_id = f"p2-test-{uuid4()}"
        relationships_created = 3
        
        context = WorkContext(
            user_id=TEST_USER_ID,
            workspace_id=REAL_WORKSPACE_ID,
            basket_id=str(uuid4())
        )
        
        # Trigger P2→P3 cascade
        cascade_work_id = await canonical_cascade_manager.trigger_p2_graph_cascade(
            work_id=test_work_id,
            relationships_created=relationships_created,
            context=context
        )
        
        if not cascade_work_id:
            logger.error("❌ P2→P3 cascade failed - no work_id returned")
            return False
        
        logger.info(f"✅ P2→P3 cascade triggered successfully: {cascade_work_id}")
        
        # Verify work was created in queue
        work_response = supabase.table("agent_processing_queue").select(
            "work_id, work_type, work_payload, parent_work_id"
        ).eq("work_id", cascade_work_id).single().execute()
        
        if not work_response.data:
            logger.error("❌ P2→P3 cascade work not found in queue")
            return False
        
        work = work_response.data
        
        if work['work_type'] != 'P3_REFLECTION':
            logger.error(f"❌ Wrong work type: {work['work_type']}, expected P3_REFLECTION")
            return False
        
        # Check parent work relationship
        parent_work_id = work['parent_work_id']
        if not parent_work_id or parent_work_id != test_work_id:
            logger.error(f"❌ Parent work ID incorrect: {parent_work_id}")
            return False
        
        logger.info("✅ P2→P3 cascade work created with correct parent relationship")
        
        # Cleanup
        supabase.table("agent_processing_queue").delete().eq("work_id", cascade_work_id).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ P2→P3 cascade test failed: {e}")
        return False

async def test_cascade_conditions():
    """Test 4: Cascade conditional triggering."""
    logger.info("🧪 Test 4: Cascade Conditional Triggering")
    
    try:
        # Test P1 cascade with no substrate created (should not trigger)
        empty_substrate = {'blocks': 0, 'context_items': 0, 'updates': 0}
        
        cascade_work_id = await canonical_cascade_manager.trigger_p1_substrate_cascade(
            proposal_id=str(uuid4()),
            basket_id=str(uuid4()),
            workspace_id=REAL_WORKSPACE_ID,
            user_id=TEST_USER_ID,
            substrate_created=empty_substrate
        )
        
        if cascade_work_id:
            logger.error("❌ Empty substrate should not trigger cascade")
            return False
        
        logger.info("✅ Empty substrate correctly skipped cascade")
        
        # Test P2 cascade with no relationships created (should not trigger)
        context = WorkContext(
            user_id=TEST_USER_ID,
            workspace_id=REAL_WORKSPACE_ID,
            basket_id=str(uuid4())
        )
        
        cascade_work_id = await canonical_cascade_manager.trigger_p2_graph_cascade(
            work_id="test-work",
            relationships_created=0,
            context=context
        )
        
        if cascade_work_id:
            logger.error("❌ No relationships should not trigger cascade")
            return False
        
        logger.info("✅ Zero relationships correctly skipped cascade")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cascade conditions test failed: {e}")
        return False

async def test_timeline_events():
    """Test 5: Timeline event emission for cascades."""
    logger.info("🧪 Test 5: Timeline Event Emission")
    
    try:
        # Count timeline events before cascade
        before_response = supabase.table("timeline_events").select("id").eq(
            "kind", "pipeline.cascade_triggered"
        ).execute()
        
        events_before = len(before_response.data or [])
        
        # Trigger a cascade that should emit timeline event
        substrate_created = {'blocks': 1, 'context_items': 1, 'updates': 0}
        
        cascade_work_id = await canonical_cascade_manager.trigger_p1_substrate_cascade(
            proposal_id=str(uuid4()),
            basket_id=str(uuid4()),
            workspace_id=REAL_WORKSPACE_ID,
            user_id=TEST_USER_ID,
            substrate_created=substrate_created
        )
        
        if not cascade_work_id:
            logger.error("❌ Cascade failed - can't test timeline events")
            return False
        
        # Wait a moment for timeline event to be created
        await asyncio.sleep(1)
        
        # Count timeline events after cascade
        after_response = supabase.table("timeline_events").select("id").eq(
            "kind", "pipeline.cascade_triggered"
        ).execute()
        
        events_after = len(after_response.data or [])
        
        if events_after <= events_before:
            logger.error(f"❌ Timeline event not created: before={events_before}, after={events_after}")
            return False
        
        logger.info(f"✅ Timeline event created: {events_after - events_before} new events")
        
        # Cleanup
        supabase.table("agent_processing_queue").delete().eq("work_id", cascade_work_id).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Timeline events test failed: {e}")
        return False

async def test_cascade_status():
    """Test 6: Cascade status tracking."""
    logger.info("🧪 Test 6: Cascade Status Tracking")
    
    try:
        # Create a test cascade work
        substrate_created = {'blocks': 1, 'context_items': 0, 'updates': 0}
        
        cascade_work_id = await canonical_cascade_manager.trigger_p1_substrate_cascade(
            proposal_id=str(uuid4()),
            basket_id=str(uuid4()),
            workspace_id=REAL_WORKSPACE_ID,
            user_id=TEST_USER_ID,
            substrate_created=substrate_created
        )
        
        if not cascade_work_id:
            logger.error("❌ Failed to create test cascade work")
            return False
        
        # Get cascade status
        status = await canonical_cascade_manager.get_cascade_status(cascade_work_id)
        
        if not status:
            logger.error("❌ Failed to get cascade status")
            return False
        
        # Check status structure
        expected_keys = ['cascade_active', 'work_type', 'processing_state']
        if not all(key in status for key in expected_keys):
            logger.error(f"❌ Cascade status missing keys: {set(expected_keys) - set(status.keys())}")
            return False
        
        if status['work_type'] != 'P2_GRAPH':
            logger.error(f"❌ Wrong cascade work type: {status['work_type']}")
            return False
        
        logger.info("✅ Cascade status tracking working correctly")
        
        # Cleanup
        supabase.table("agent_processing_queue").delete().eq("work_id", cascade_work_id).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cascade status test failed: {e}")
        return False

async def run_all_tests():
    """Run all Phase 2 cascade integration tests."""
    logger.info("🚀 Starting Phase 2 Cascade Integration Tests")
    logger.info("Testing Canon v2.1 enhanced cascade manager implementation")
    
    tests = [
        ("Enhanced Cascade Manager", test_enhanced_cascade_manager),
        ("P1→P2 Substrate Cascade", test_p1_substrate_cascade),
        ("P2→P3 Graph Cascade", test_p2_graph_cascade),
        ("Cascade Conditions", test_cascade_conditions),
        ("Timeline Events", test_timeline_events),
        ("Cascade Status", test_cascade_status)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Report results
    logger.info(f"\n{'='*50}")
    logger.info("📊 PHASE 2 TEST RESULTS")
    logger.info(f"{'='*50}")
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n📈 SUMMARY: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED! Phase 2 cascade integration complete.")
        logger.info("Canon v2.1 Enhanced Cascade Manager fully operational.")
        return True
    else:
        logger.error("💥 Some tests failed. Phase 2 needs fixes before proceeding.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)