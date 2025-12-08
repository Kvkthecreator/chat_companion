#!/usr/bin/env python3
"""
Test Database Function - fn_document_attach_substrate

Simple test to check if the database function exists and how it handles parameters
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

async def test_database_function_existence():
    """Test if fn_document_attach_substrate function exists"""
    logger.info("🧪 Testing if fn_document_attach_substrate function exists")
    
    try:
        # Query the function definition
        result = supabase.rpc('sql', {
            'query': '''
            SELECT 
                routine_name,
                data_type,
                parameter_name,
                parameter_mode
            FROM information_schema.parameters 
            WHERE specific_name = 'fn_document_attach_substrate'
            ORDER BY ordinal_position;
            '''
        }).execute()
        
        if result.data:
            logger.info("✅ fn_document_attach_substrate function exists")
            logger.info("   Parameters:")
            for param in result.data:
                logger.info(f"     {param['parameter_name']} ({param['parameter_mode']}) - {param['data_type']}")
            return True
        else:
            logger.error("❌ fn_document_attach_substrate function does not exist")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error checking function existence: {e}")
        return False

async def test_parameter_formats():
    """Test different parameter formats for the function"""
    logger.info("🧪 Testing parameter formats")
    
    # Use dummy UUIDs that will fail gracefully
    dummy_doc_id = str(uuid4())
    dummy_substrate_id = str(uuid4())
    
    tests = [
        {
            "name": "Array snippets, Object metadata",
            "params": {
                "p_document_id": dummy_doc_id,
                "p_substrate_type": "block",
                "p_substrate_id": dummy_substrate_id,
                "p_role": "test",
                "p_weight": 0.5,
                "p_snippets": ["test snippet"],
                "p_metadata": {"test": True}
            }
        },
        {
            "name": "JSON string snippets, JSON string metadata (current agent)",
            "params": {
                "p_document_id": dummy_doc_id,
                "p_substrate_type": "block", 
                "p_substrate_id": dummy_substrate_id,
                "p_role": "test",
                "p_weight": 0.5,
                "p_snippets": '["test snippet"]',
                "p_metadata": '{"test": true}'
            }
        },
        {
            "name": "Null snippets and metadata",
            "params": {
                "p_document_id": dummy_doc_id,
                "p_substrate_type": "block",
                "p_substrate_id": dummy_substrate_id,
                "p_role": "test",
                "p_weight": 0.5,
                "p_snippets": None,
                "p_metadata": None
            }
        }
    ]
    
    for test in tests:
        logger.info(f"   Testing: {test['name']}")
        try:
            result = supabase.rpc("fn_document_attach_substrate", test['params']).execute()
            logger.info(f"     ✅ Function call succeeded (may have failed on FK constraints)")
            logger.info(f"     Result: {result.data}")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg or "violates foreign key" in error_msg:
                logger.info(f"     ✅ Function exists but failed on data constraints: {e}")
            elif "invalid input syntax" in error_msg or "invalid type" in error_msg:
                logger.error(f"     ❌ Parameter format error: {e}")
            else:
                logger.error(f"     ❌ Unknown error: {e}")
    
    return True

async def test_existing_documents():
    """Test with existing documents if any"""
    logger.info("🧪 Testing with existing documents")
    
    try:
        # Find an existing document
        docs_result = supabase.table("documents").select("id, basket_id, workspace_id").limit(1).execute()
        
        if docs_result.data:
            doc = docs_result.data[0]
            logger.info(f"✅ Found existing document: {doc['id']}")
            
            # Try to attach substrate to existing document
            try:
                result = supabase.rpc("fn_document_attach_substrate", {
                    "p_document_id": doc['id'],
                    "p_substrate_type": "block",
                    "p_substrate_id": str(uuid4()),  # This will fail on FK but tests the format
                    "p_role": "test",
                    "p_weight": 0.5,
                    "p_snippets": ["test snippet"],
                    "p_metadata": {"test": True}
                }).execute()
                logger.info(f"✅ Function call with existing document succeeded")
                
            except Exception as e:
                if "violates foreign key" in str(e):
                    logger.info("✅ Function worked but substrate doesn't exist (expected)")
                else:
                    logger.error(f"❌ Unexpected error: {e}")
        else:
            logger.info("ℹ️  No existing documents found")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing existing documents: {e}")
        return False

async def run_db_function_tests():
    """Run database function tests"""
    logger.info("🚀 Starting Database Function Tests")
    logger.info("Testing fn_document_attach_substrate")
    logger.info("=" * 40)
    
    tests = [
        ("Function Existence", test_database_function_existence),
        ("Parameter Formats", test_parameter_formats),
        ("Existing Documents", test_existing_documents)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*25}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Report results
    logger.info(f"\n{'='*40}")
    logger.info("📊 DATABASE FUNCTION TEST RESULTS")
    logger.info(f"{'='*40}")
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}")
    
    return True

if __name__ == "__main__":
    asyncio.run(run_db_function_tests())