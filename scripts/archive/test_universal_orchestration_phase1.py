#!/usr/bin/env python3
"""
Test Universal Work Orchestration Phase 1 Implementation

Tests the Canon v2.1 Universal Work Orchestration implementation:
1. Schema migration verification
2. Universal Work Tracker functionality
3. Work Status API endpoints
4. Integration with canonical queue processor

This validates Phase 1 Day 1-2 completion per streamlined execution plan.
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
from services.universal_work_tracker import universal_work_tracker, WorkContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_schema_migration():
    """Test 1: Verify schema migration was applied correctly."""
    logger.info("🧪 Test 1: Schema Migration Verification")
    
    try:
        # Check that all new columns exist
        result = supabase.rpc('sql', {
            'query': """
            SELECT column_name, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'agent_processing_queue' 
            AND column_name IN ('work_type', 'processing_stage', 'work_payload', 'cascade_metadata', 'parent_work_id', 'user_id', 'work_id')
            ORDER BY column_name;
            """
        }).execute()
        
        columns = result.data or []
        expected_columns = {'work_type', 'processing_stage', 'work_payload', 'cascade_metadata', 'parent_work_id', 'user_id', 'work_id'}
        found_columns = {col['column_name'] for col in columns}
        
        if expected_columns.issubset(found_columns):
            logger.info("✅ Schema migration verified - all columns present")
            return True
        else:
            missing = expected_columns - found_columns
            logger.error(f"❌ Schema migration incomplete - missing columns: {missing}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False

async def test_universal_work_tracker():
    """Test 2: Universal Work Tracker functionality."""
    logger.info("🧪 Test 2: Universal Work Tracker")
    
    try:
        # Create test work context
        test_user_id = str(uuid4())
        test_workspace_id = str(uuid4())
        
        context = WorkContext(
            user_id=test_user_id,
            workspace_id=test_workspace_id,
            basket_id=str(uuid4())
        )
        
        # Test work initiation (without dump_id for universal work type)
        work_id = await universal_work_tracker.initiate_work(
            work_type="MANUAL_EDIT",
            payload={"test": True, "content": "Test manual edit work"},
            context=context,
            priority=5
        )
        
        if not work_id:
            logger.error("❌ Work initiation failed - no work_id returned")
            return False
        
        logger.info(f"✅ Work initiated successfully: {work_id}")
        
        # Test work status retrieval
        status = await universal_work_tracker.get_work_status(work_id)
        
        if status.work_id != work_id:
            logger.error("❌ Work status retrieval failed - wrong work_id")
            return False
        
        if status.work_type != "MANUAL_EDIT":
            logger.error("❌ Work status retrieval failed - wrong work_type")
            return False
        
        logger.info(f"✅ Work status retrieved: {status.status} at {status.progress_percentage}%")
        
        # Test work completion
        test_result = {
            "proposals_created": 2,
            "confidence": 0.85,
            "blocks_created": 3,
            "context_items_created": 1
        }
        
        await universal_work_tracker.complete_work(work_id, test_result)
        
        # Verify completion
        completed_status = await universal_work_tracker.get_work_status(work_id)
        
        if completed_status.status != "completed":
            logger.error(f"❌ Work completion failed - status: {completed_status.status}")
            return False
        
        if completed_status.substrate_impact.proposals_created != 2:
            logger.error("❌ Work completion failed - substrate impact not recorded")
            return False
        
        logger.info("✅ Work completion verified with substrate impact")
        
        # Cleanup test work entry
        supabase.table("agent_processing_queue").delete().eq("work_id", work_id).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Universal Work Tracker test failed: {e}")
        return False

async def test_queue_health_endpoint():
    """Test 3: Queue health endpoint functionality."""
    logger.info("🧪 Test 3: Queue Health Endpoint")
    
    try:
        # Test queue health RPC function
        result = supabase.rpc('fn_queue_health').execute()
        
        if not result.data:
            logger.warning("⚠️  Queue health returned no data (empty queue)")
        else:
            logger.info(f"✅ Queue health data retrieved: {len(result.data)} status groups")
        
        # Test that the function executes without error
        logger.info("✅ Queue health endpoint functional")
        return True
        
    except Exception as e:
        logger.error(f"❌ Queue health endpoint test failed: {e}")
        return False

async def test_work_type_constraints():
    """Test 4: Work type constraints per Canon v2.1."""
    logger.info("🧪 Test 4: Work Type Constraints")
    
    try:
        # Test valid work types
        valid_types = [
            'P0_CAPTURE', 'P1_SUBSTRATE', 'P2_GRAPH', 'P3_REFLECTION', 'P4_COMPOSE',
            'MANUAL_EDIT', 'PROPOSAL_REVIEW', 'TIMELINE_RESTORE'
        ]
        
        # Try to insert a valid work type
        test_entry = {
            'id': str(uuid4()),
            'work_type': 'MANUAL_EDIT',
            'workspace_id': str(uuid4()),
            'user_id': str(uuid4()),
            'processing_state': 'pending',
            'work_payload': {},
            'priority': 5
        }
        
        insert_result = supabase.table("agent_processing_queue").insert(test_entry).execute()
        
        if not insert_result.data:
            logger.error("❌ Valid work type insertion failed")
            return False
        
        logger.info("✅ Valid work type constraint passed")
        
        # Cleanup
        supabase.table("agent_processing_queue").delete().eq("id", test_entry['id']).execute()
        
        # Test invalid work type (should fail)
        try:
            invalid_entry = test_entry.copy()
            invalid_entry['id'] = str(uuid4())
            invalid_entry['work_type'] = 'INVALID_TYPE'
            
            supabase.table("agent_processing_queue").insert(invalid_entry).execute()
            logger.error("❌ Invalid work type constraint failed - insertion should have been rejected")
            return False
            
        except Exception:
            logger.info("✅ Invalid work type correctly rejected by constraint")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Work type constraints test failed: {e}")
        return False

async def test_processing_state_enum():
    """Test 5: Processing state enum includes 'cascading' value."""
    logger.info("🧪 Test 5: Processing State Enum")
    
    try:
        # Check enum values
        result = supabase.rpc('sql', {
            'query': """
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'processing_state')
            ORDER BY enumlabel;
            """
        }).execute()
        
        enum_values = {row['enumlabel'] for row in (result.data or [])}
        expected_values = {'pending', 'claimed', 'processing', 'cascading', 'completed', 'failed'}
        
        if expected_values.issubset(enum_values):
            logger.info(f"✅ Processing state enum complete: {enum_values}")
            return True
        else:
            missing = expected_values - enum_values
            logger.error(f"❌ Processing state enum incomplete - missing: {missing}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Processing state enum test failed: {e}")
        return False

async def run_all_tests():
    """Run all Phase 1 tests and report results."""
    logger.info("🚀 Starting Universal Work Orchestration Phase 1 Tests")
    logger.info("Testing Canon v2.1 implementation per streamlined execution plan")
    
    tests = [
        ("Schema Migration", test_schema_migration),
        ("Universal Work Tracker", test_universal_work_tracker),
        ("Queue Health Endpoint", test_queue_health_endpoint),
        ("Work Type Constraints", test_work_type_constraints),
        ("Processing State Enum", test_processing_state_enum)
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
    logger.info("📊 PHASE 1 TEST RESULTS")
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
        logger.info("🎉 ALL TESTS PASSED! Phase 1 implementation complete.")
        logger.info("Canon v2.1 Universal Work Orchestration foundation ready.")
        return True
    else:
        logger.error("💥 Some tests failed. Phase 1 needs fixes before proceeding.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)