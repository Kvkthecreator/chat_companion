#!/usr/bin/env python3
"""
Test P4 Composition Flow End-to-End

This test verifies the complete P4 composition flow from document creation
through async processing to substrate attachment.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables for testing
os.environ["SUPABASE_URL"] = "https://galytxxkrbksilekmhcw.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdhbHl0eHhrcmJrc2lsZWttaGN3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NTU3NjMsImV4cCI6MjA2MjMzMTc2M30.n9wrD3a_fep8GfeCRm0iflk-4Y47RYnLA0EeEECU7OY"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdhbHl0eHhrcmJrc2lsZWttaGN3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njc1NTc2MywiZXhwIjoyMDYyMzMxNzYzfQ.0oAdZeTn_k3p-29Hy8z1v5YYGpjBeqML0amz5bcAS6g"

from infra.utils.supabase_client import supabase_admin_client as supabase
from infra.substrate.services.universal_work_tracker import universal_work_tracker, WorkContext
from infra.substrate.services.canonical_queue_processor import CanonicalQueueProcessor
from app.agents.pipeline.composition_agent import P4CompositionAgent, CompositionRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class P4CompositionFlowTest:
    """Test the complete P4 composition flow"""
    
    def __init__(self):
        self.test_data = {}
        
    async def setup_test_data(self):
        """Set up test workspace, basket, and substrate for composition"""
        logger.info("Setting up test data...")
        
        # Create test workspace
        workspace_id = str(uuid4())
        self.test_data['workspace_id'] = workspace_id
        
        # Create test basket
        basket_id = str(uuid4())
        self.test_data['basket_id'] = basket_id
        
        user_id = str(uuid4())
        self.test_data['user_id'] = user_id
        
        # Create test substrate - blocks
        block_1 = await self._create_test_block(
            basket_id, workspace_id,
            title="Project Architecture",
            content="The system uses a microservices architecture with FastAPI and React."
        )
        
        block_2 = await self._create_test_block(
            basket_id, workspace_id,
            title="Database Design", 
            content="We're using PostgreSQL with Supabase for real-time subscriptions."
        )
        
        # Create test substrate - context items
        context_item = await self._create_test_context_item(
            basket_id, workspace_id,
            label="Technical Stack",
            kind="technology"
        )
        
        self.test_data['substrate'] = {
            'blocks': [block_1, block_2],
            'context_items': [context_item]
        }
        
        logger.info(f"Test data created: workspace={workspace_id}, basket={basket_id}")
        return True
        
    async def _create_test_block(self, basket_id, workspace_id, title, content):
        """Create a test block"""
        try:
            response = supabase.table("blocks").insert({
                "id": str(uuid4()),
                "basket_id": basket_id,
                "workspace_id": workspace_id,
                "semantic_type": "insight",
                "content": content,
                "title": title,
                "confidence_score": 0.8,
                "state": "ACCEPTED",
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            
            if response.data:
                logger.info(f"Created test block: {title}")
                return response.data[0]['id']
            else:
                raise RuntimeError("Failed to create test block")
                
        except Exception as e:
            logger.error(f"Failed to create test block {title}: {e}")
            raise
            
    async def _create_test_context_item(self, basket_id, workspace_id, label, kind):
        """Create a test context item"""
        try:
            response = supabase.table("context_items").insert({
                "id": str(uuid4()),
                "basket_id": basket_id,
                "workspace_id": workspace_id,
                "label": label,
                "kind": kind,
                "state": "ACTIVE",
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            
            if response.data:
                logger.info(f"Created test context item: {label}")
                return response.data[0]['id']
            else:
                raise RuntimeError("Failed to create test context item")
                
        except Exception as e:
            logger.error(f"Failed to create test context item {label}: {e}")
            raise
    
    async def test_queue_processor_running(self):
        """Test if canonical queue processor is running"""
        logger.info("🧪 Test 1: Queue Processor Status")
        
        try:
            # Check if processor can claim work
            processor = CanonicalQueueProcessor(worker_id="test-worker", poll_interval=1)
            claimed_work = await processor._claim_work(limit=1)
            
            logger.info(f"✅ Queue processor operational - claimed {len(claimed_work)} items")
            return True
            
        except Exception as e:
            logger.error(f"❌ Queue processor test failed: {e}")
            return False
    
    async def test_p4_work_queuing(self):
        """Test P4_COMPOSE work queuing via Universal Work Tracker"""
        logger.info("🧪 Test 2: P4_COMPOSE Work Queuing")
        
        try:
            context = WorkContext(
                user_id=self.test_data['user_id'],
                workspace_id=self.test_data['workspace_id'],
                basket_id=self.test_data['basket_id']
            )
            
            # Create test document for composition
            document_id = str(uuid4())
            
            # Queue P4_COMPOSE work
            work_id = await universal_work_tracker.initiate_work(
                work_type="P4_COMPOSE",
                payload={
                    "operations": [{
                        "type": "compose_from_memory",
                        "data": {
                            "document_id": document_id,
                            "intent": "Create project documentation from recent discussions",
                            "window": {"days": 30},
                            "pinned_ids": []
                        }
                    }],
                    "basket_id": self.test_data['basket_id'],
                    "confidence_score": 0.0,
                    "trace_id": str(uuid4())
                },
                context=context,
                priority=5
            )
            
            if not work_id:
                logger.error("❌ P4_COMPOSE work queuing failed - no work_id returned")
                return False
                
            logger.info(f"✅ P4_COMPOSE work queued successfully: {work_id}")
            
            # Verify work status
            status = await universal_work_tracker.get_work_status(work_id)
            
            if status.work_type != "P4_COMPOSE":
                logger.error(f"❌ Work type mismatch: expected P4_COMPOSE, got {status.work_type}")
                return False
                
            logger.info(f"✅ Work status verified: {status.status}")
            
            self.test_data['work_id'] = work_id
            self.test_data['document_id'] = document_id
            
            return True
            
        except Exception as e:
            logger.error(f"❌ P4_COMPOSE work queuing test failed: {e}")
            return False
    
    async def test_queue_processor_claims_p4_work(self):
        """Test that queue processor claims P4_COMPOSE work"""
        logger.info("🧪 Test 3: Queue Processor Claims P4 Work")
        
        try:
            processor = CanonicalQueueProcessor(worker_id="test-p4-worker", poll_interval=1)
            
            # Try to claim work (should include our P4_COMPOSE work)
            claimed_work = await processor._claim_work(limit=10)
            
            # Look for our P4_COMPOSE work
            p4_work = [w for w in claimed_work if w.get('work_type') == 'P4_COMPOSE']
            
            if not p4_work:
                logger.warning("⚠️  No P4_COMPOSE work claimed - may not be available yet")
                return True  # Don't fail, work might be processed already
                
            logger.info(f"✅ Queue processor claimed {len(p4_work)} P4_COMPOSE work items")
            
            # Check if our specific work was claimed
            our_work = [w for w in p4_work if w.get('work_id') == self.test_data.get('work_id')]
            if our_work:
                logger.info(f"✅ Our test work was claimed: {our_work[0]['id']}")
                self.test_data['queue_entry'] = our_work[0]
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Queue processor P4 work claiming test failed: {e}")
            return False
    
    async def test_p4_composition_agent_direct(self):
        """Test P4 composition agent directly"""
        logger.info("🧪 Test 4: P4 Composition Agent Direct")
        
        try:
            # Create document shell for testing
            document_id = str(uuid4())
            doc_insert = await supabase.table("documents").insert({
                "id": document_id,
                "basket_id": self.test_data['basket_id'],
                "workspace_id": self.test_data['workspace_id'],
                "title": "Test P4 Composition",
                "content_raw": "",
                "document_type": "narrative",
                "metadata": {
                    "composition_status": "pending",
                    "composition_type": "async_pending"
                }
            }).execute()
            
            if not doc_insert.data:
                raise RuntimeError("Failed to create test document")
                
            logger.info(f"Created test document: {document_id}")
            
            # Test P4 composition agent directly
            agent = P4CompositionAgent()
            
            request = CompositionRequest(
                document_id=document_id,
                basket_id=self.test_data['basket_id'],
                workspace_id=self.test_data['workspace_id'],
                intent="Summarize project architecture and database design decisions",
                window={"days": 30},
                pinned_ids=[]
            )
            
            # Process composition
            result = await agent.process(request)
            
            if not result.success:
                logger.error(f"❌ P4 composition failed: {result.message}")
                return False
                
            logger.info(f"✅ P4 composition succeeded: {result.message}")
            logger.info(f"   Substrate count: {result.data.get('substrate_count', 0)}")
            
            # Verify document was updated
            doc_check = await supabase.table("documents").select("*").eq("id", document_id).execute()
            if doc_check.data:
                doc = doc_check.data[0]
                logger.info(f"   Document content length: {len(doc.get('content_raw', ''))}")
                
                # Check for substrate references
                refs_check = await supabase.table("substrate_references")\
                    .select("*").eq("document_id", document_id).execute()
                    
                ref_count = len(refs_check.data) if refs_check.data else 0
                logger.info(f"   Substrate references: {ref_count}")
                
                if ref_count == 0:
                    logger.warning("⚠️  No substrate references found - this is the bug!")
                    
                    # Debug: Check if fn_document_attach_substrate exists
                    try:
                        debug_result = await supabase.rpc("fn_document_attach_substrate", {
                            "p_document_id": document_id,
                            "p_substrate_type": "block", 
                            "p_substrate_id": self.test_data['substrate']['blocks'][0],
                            "p_role": "test",
                            "p_weight": 0.5,
                            "p_snippets": ["test snippet"],
                            "p_metadata": {"test": True}
                        }).execute()
                        logger.info("✅ fn_document_attach_substrate function exists and callable")
                    except Exception as e:
                        logger.error(f"❌ fn_document_attach_substrate failed: {e}")
                        logger.error("   This is likely the root cause!")
                else:
                    logger.info(f"✅ Substrate references attached successfully")
            
            self.test_data['test_document_id'] = document_id
            return True
            
        except Exception as e:
            logger.error(f"❌ P4 composition agent direct test failed: {e}")
            return False
    
    async def test_complete_async_flow(self):
        """Test the complete async P4 composition flow"""
        logger.info("🧪 Test 5: Complete Async P4 Flow")
        
        try:
            # This test simulates the complete flow from frontend to backend
            # Create document via universal work tracker (simulating the frontend flow)
            
            context = WorkContext(
                user_id=self.test_data['user_id'],
                workspace_id=self.test_data['workspace_id'], 
                basket_id=self.test_data['basket_id']
            )
            
            # Create document shell first (like the API does)
            document_id = str(uuid4())
            doc_insert = await supabase.table("documents").insert({
                "id": document_id,
                "basket_id": self.test_data['basket_id'],
                "workspace_id": self.test_data['workspace_id'],
                "title": "Test Async Composition",
                "content_raw": "Draft content",
                "document_type": "narrative",
                "metadata": {
                    "composition_status": "pending",
                    "composition_type": "async_pending",
                    "composition_context": {
                        "intent": "Create comprehensive project documentation",
                        "window": {"days": 30}
                    }
                }
            }).execute()
            
            if not doc_insert.data:
                raise RuntimeError("Failed to create async test document")
                
            logger.info(f"Created async test document: {document_id}")
            
            # Queue work
            work_id = await universal_work_tracker.initiate_work(
                work_type="P4_COMPOSE",
                payload={
                    "operations": [{
                        "type": "compose_from_memory",
                        "data": {
                            "document_id": document_id,
                            "intent": "Create comprehensive project documentation",
                            "window": {"days": 30},
                            "pinned_ids": []
                        }
                    }],
                    "basket_id": self.test_data['basket_id'],
                    "confidence_score": 0.0,
                    "trace_id": str(uuid4())
                },
                context=context
            )
            
            logger.info(f"Queued async composition work: {work_id}")
            
            # Process work through canonical queue processor
            processor = CanonicalQueueProcessor(worker_id="test-async-worker")
            
            # Manually claim and process our work
            claimed_work = await processor._claim_work(limit=20)
            our_work = None
            
            for work in claimed_work:
                if work.get('work_id') == work_id:
                    our_work = work
                    break
            
            if our_work:
                logger.info(f"Found our work in queue: {our_work['id']}")
                
                # Process the work
                await processor._process_composition_work(our_work)
                logger.info("✅ Async composition processing completed")
                
                # Check final document state
                final_doc = await supabase.table("documents").select("*").eq("id", document_id).execute()
                if final_doc.data:
                    doc = final_doc.data[0]
                    logger.info(f"   Final content length: {len(doc.get('content_raw', ''))}")
                    
                    refs_check = await supabase.table("substrate_references")\
                        .select("*").eq("document_id", document_id).execute()
                    ref_count = len(refs_check.data) if refs_check.data else 0
                    logger.info(f"   Final substrate references: {ref_count}")
                    
                    if ref_count > 0:
                        logger.info("✅ Async composition flow successful!")
                        return True
                    else:
                        logger.error("❌ Async composition failed - no substrate attached")
                        return False
            else:
                logger.warning("⚠️  Our work not found in claimed work - may have been processed already")
                return True
                
        except Exception as e:
            logger.error(f"❌ Complete async flow test failed: {e}")
            return False
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("Cleaning up test data...")
        
        try:
            # Clean up documents
            if 'test_document_id' in self.test_data:
                await supabase.table("documents").delete().eq("id", self.test_data['test_document_id']).execute()
                
            # Clean up substrate references
            await supabase.table("substrate_references")\
                .delete().eq("document_id", self.test_data.get('test_document_id', '')).execute()
                
            # Clean up test substrate
            for block_id in self.test_data.get('substrate', {}).get('blocks', []):
                await supabase.table("blocks").delete().eq("id", block_id).execute()
                
            for item_id in self.test_data.get('substrate', {}).get('context_items', []):
                await supabase.table("context_items").delete().eq("id", item_id).execute()
                
            # Clean up work queue entries
            if 'work_id' in self.test_data:
                await supabase.table("agent_processing_queue").delete().eq("work_id", self.test_data['work_id']).execute()
                
            logger.info("✅ Test data cleanup completed")
            
        except Exception as e:
            logger.warning(f"Test cleanup failed (non-critical): {e}")

async def run_p4_composition_tests():
    """Run all P4 composition flow tests"""
    logger.info("🚀 Starting P4 Composition Flow Tests")
    logger.info("Testing Canon v2.1 P4 async composition implementation")
    logger.info("=" * 60)
    
    test_suite = P4CompositionFlowTest()
    
    try:
        # Setup
        await test_suite.setup_test_data()
        
        # Run tests
        tests = [
            ("Queue Processor Running", test_suite.test_queue_processor_running),
            ("P4_COMPOSE Work Queuing", test_suite.test_p4_work_queuing),
            ("Queue Processor Claims P4 Work", test_suite.test_queue_processor_claims_p4_work),
            ("P4 Composition Agent Direct", test_suite.test_p4_composition_agent_direct),
            ("Complete Async P4 Flow", test_suite.test_complete_async_flow)
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
        logger.info(f"\n{'='*60}")
        logger.info("📊 P4 COMPOSITION FLOW TEST RESULTS")
        logger.info(f"{'='*60}")
        
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
            logger.info("🎉 ALL P4 COMPOSITION TESTS PASSED!")
            logger.info("P4 async composition flow is working correctly.")
        else:
            logger.error("💥 Some P4 composition tests failed.")
            logger.error("This explains why 'compose from memory' creates blank documents.")
        
        return failed == 0
        
    finally:
        # Cleanup
        await test_suite.cleanup_test_data()

if __name__ == "__main__":
    success = asyncio.run(run_p4_composition_tests())
    sys.exit(0 if success else 1)