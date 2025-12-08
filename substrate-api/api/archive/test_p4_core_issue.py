#!/usr/bin/env python3
"""
Test P4 Core Issue - Simple test to diagnose substrate attachment

This test focuses on the core issue: why fn_document_attach_substrate is failing
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

async def test_fn_document_attach_substrate():
    """Test the fn_document_attach_substrate function directly"""
    logger.info("🧪 Testing fn_document_attach_substrate function")
    
    try:
        # Create a test document first
        doc_id = str(uuid4())
        test_doc = {
            "id": doc_id,
            "title": "Test Document",
            "content_raw": "Test content",
            "document_type": "narrative",
            "workspace_id": str(uuid4()),
            "basket_id": str(uuid4())
        }
        
        doc_result = supabase.table("documents").insert(test_doc).execute()
        
        if not doc_result.data:
            logger.error("❌ Failed to create test document")
            return False
            
        logger.info(f"✅ Created test document: {doc_id}")
        
        # Test the function call with different parameter formats
        test_substrate_id = str(uuid4())
        
        # Test 1: Array format for snippets
        logger.info("Testing with array format for snippets...")
        try:
            result1 = supabase.rpc("fn_document_attach_substrate", {
                "p_document_id": doc_id,
                "p_substrate_type": "block",
                "p_substrate_id": test_substrate_id,
                "p_role": "test",
                "p_weight": 0.5,
                "p_snippets": ["test snippet"],  # Array format
                "p_metadata": {"test": True}     # Object format
            }).execute()
            logger.info(f"✅ Array format succeeded: {result1.data}")
        except Exception as e:
            logger.error(f"❌ Array format failed: {e}")
        
        # Test 2: JSON string format for snippets (current agent format)
        logger.info("Testing with JSON string format for snippets...")
        try:
            import json
            result2 = supabase.rpc("fn_document_attach_substrate", {
                "p_document_id": doc_id,
                "p_substrate_type": "block",
                "p_substrate_id": str(uuid4()),
                "p_role": "test",
                "p_weight": 0.5,
                "p_snippets": json.dumps(["test snippet"]),  # JSON string format (current agent)
                "p_metadata": json.dumps({"test": True})     # JSON string format (current agent)
            }).execute()
            logger.error(f"❌ JSON string format should have failed but didn't: {result2.data}")
        except Exception as e:
            logger.info(f"✅ JSON string format correctly failed: {e}")
            logger.info("   This confirms the double JSON serialization bug!")
        
        # Check if substrate references were created
        refs_result = supabase.table("substrate_references").select("*").eq("document_id", doc_id).execute()
        ref_count = len(refs_result.data) if refs_result.data else 0
        logger.info(f"📊 Total substrate references created: {ref_count}")
        
        # Cleanup
        supabase.table("substrate_references").delete().eq("document_id", doc_id).execute()
        supabase.table("documents").delete().eq("id", doc_id).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ fn_document_attach_substrate test failed: {e}")
        return False

async def test_queue_processor_startup():
    """Test if canonical queue processor can start"""
    logger.info("🧪 Testing canonical queue processor startup")
    
    try:
        from infra.substrate.services.canonical_queue_processor import CanonicalQueueProcessor
        
        processor = CanonicalQueueProcessor(worker_id="test-startup", poll_interval=60)
        logger.info(f"✅ Queue processor created: {processor.worker_id}")
        
        # Test processor info
        info = processor.get_processor_info()
        logger.info(f"✅ Processor info: {info['processor_name']} v{info['canon_version']}")
        logger.info(f"   Status: {info['status']}")
        logger.info(f"   Pipeline agents: {list(info['pipeline_agents'].keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Queue processor startup test failed: {e}")
        return False

async def test_p4_agent_creation():
    """Test P4 composition agent creation"""
    logger.info("🧪 Testing P4 composition agent creation")
    
    try:
        from app.agents.pipeline.composition_agent import P4CompositionAgent
        
        agent = P4CompositionAgent()
        logger.info("✅ P4 composition agent created successfully")
        
        # Test agent info if available
        if hasattr(agent, 'get_agent_info'):
            info = agent.get_agent_info()
            logger.info(f"   Agent info: {info}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ P4 composition agent creation failed: {e}")
        return False

async def run_core_tests():
    """Run core diagnostic tests"""
    logger.info("🚀 Starting P4 Core Issue Diagnostic Tests")
    logger.info("=" * 50)
    
    tests = [
        ("fn_document_attach_substrate", test_fn_document_attach_substrate),
        ("Canonical Queue Processor", test_queue_processor_startup),
        ("P4 Composition Agent", test_p4_agent_creation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*30}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Report results
    logger.info(f"\n{'='*50}")
    logger.info("📊 CORE ISSUE DIAGNOSTIC RESULTS")
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
        logger.info("🎉 All core components working!")
    else:
        logger.error("💥 Core issues found that explain the blank document bug.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_core_tests())
    sys.exit(0 if success else 1)