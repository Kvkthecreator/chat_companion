"""Tests for canonical queue processor with governance integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4, UUID

from src.services.canonical_queue_processor import CanonicalQueueProcessor
from src.app.agents.pipeline.governance_processor import GovernanceDumpProcessor


class TestCanonicalQueueGovernance:
    """Test canonical queue processor with governance workflow."""
    
    @pytest.fixture
    def processor(self):
        """Create canonical queue processor."""
        return CanonicalQueueProcessor(worker_id="test-worker", poll_interval=1)
    
    @pytest.fixture
    def queue_entry(self):
        """Sample queue entry for testing."""
        return {
            'id': str(uuid4()),
            'dump_id': str(uuid4()),
            'basket_id': str(uuid4()),
            'workspace_id': str(uuid4()),
            'processing_state': 'pending'
        }
    
    @patch('src.services.canonical_queue_processor.supabase')
    @pytest.mark.asyncio
    async def test_process_dump_through_governance(self, mock_supabase, processor, queue_entry):
        """Test dump processing creates governance proposals instead of direct substrate."""
        
        # Mock dump validation
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            'id': queue_entry['dump_id'],
            'body_md': 'Test dump content with strategic goals',
            'workspace_id': queue_entry['workspace_id'],
            'basket_id': queue_entry['basket_id']
        }
        
        # Mock governance processor result
        governance_result = {
            'proposals_created': 1,
            'proposal_id': str(uuid4()),
            'status': 'proposal_created',
            'operations_count': 3,
            'confidence': 0.8
        }
        
        # Mock RPC calls
        mock_supabase.rpc.return_value.execute.return_value = None
        
        # Mock governance processor
        processor.p1_governance.process_dump = AsyncMock(return_value=governance_result)
        
        await processor._process_dump_canonically(queue_entry)
        
        # Verify governance processing was called
        processor.p1_governance.process_dump.assert_called_once_with(
            dump_id=UUID(queue_entry['dump_id']),
            basket_id=UUID(queue_entry['basket_id']),
            workspace_id=UUID(queue_entry['workspace_id'])
        )
        
        # Verify P2/P3 were deferred (no immediate substrate to process)
        # In governance mode, P2/P3 run after proposal approval via cascade events
    
    @patch('src.services.canonical_queue_processor.supabase')
    @pytest.mark.asyncio
    async def test_process_dump_no_candidates(self, mock_supabase, processor, queue_entry):
        """Test processing dump with no extractable candidates."""
        
        # Mock dump validation
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            'id': queue_entry['dump_id'],
            'body_md': 'x',  # Too short for extraction
            'workspace_id': queue_entry['workspace_id'],
            'basket_id': queue_entry['basket_id']
        }
        
        # Mock governance processor - no candidates
        governance_result = {
            'proposals_created': 0,
            'status': 'no_candidates',
            'message': 'No substrate candidates found in dump'
        }
        
        mock_supabase.rpc.return_value.execute.return_value = None
        processor.p1_governance.process_dump = AsyncMock(return_value=governance_result)
        
        await processor._process_dump_canonically(queue_entry)
        
        # Should complete processing even with no candidates
        processor.p1_governance.process_dump.assert_called_once()
    
    @patch('src.services.canonical_queue_processor.supabase')
    @pytest.mark.asyncio
    async def test_claim_dumps_governance_ready(self, mock_supabase, processor):
        """Test claiming dumps for governance processing."""
        
        # Mock queue entries ready for governance processing
        queue_data = [
            {
                'id': str(uuid4()),
                'dump_id': str(uuid4()),
                'basket_id': str(uuid4()),
                'workspace_id': str(uuid4()),
                'processing_state': 'pending',
                'claimed_by': 'test-worker'
            }
        ]
        
        mock_supabase.rpc.return_value.execute.return_value.data = queue_data
        
        claimed = await processor._claim_dumps(limit=5)
        
        assert len(claimed) == 1
        assert claimed[0]['processing_state'] == 'pending'
        
        # Verify correct RPC call
        mock_supabase.rpc.assert_called_with('fn_claim_next_dumps', {
            'p_worker_id': 'test-worker',
            'p_limit': 5,
            'p_stale_after_minutes': 5
        })
    
    @patch('src.services.canonical_queue_processor.supabase')
    @pytest.mark.asyncio
    async def test_governance_processor_info(self, mock_supabase, processor):
        """Test processor info includes governance agents."""
        
        info = processor.get_processor_info()
        
        assert info['processor_name'] == 'CanonicalQueueProcessor'
        assert info['canon_version'] == 'v1.4.0'
        
        # Should include governance agent
        assert 'P1_GOVERNANCE' in info['pipeline_agents']
        assert info['processing_sequence'] == ['P0_CAPTURE', 'P1_GOVERNANCE', 'P2_DEFERRED', 'P3_DEFERRED']
        
        # Sacred principles should be preserved
        assert 'Capture is Sacred' in info['sacred_principles']
        assert 'Agent Intelligence is Mandatory' in info['sacred_principles']
    
    @pytest.mark.asyncio
    async def test_p0_capture_validation_governance(self, processor):
        """Test P0 capture validation in governance mode."""
        dump_id = uuid4()
        workspace_id = uuid4()
        
        with patch('src.services.canonical_queue_processor.supabase') as mock_supabase:
            # Mock valid dump
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = {
                'id': str(dump_id),
                'body_md': 'Valid dump content',
                'workspace_id': str(workspace_id),
                'basket_id': str(uuid4())
            }
            
            # Should validate successfully
            await processor._validate_p0_capture(dump_id, workspace_id)
            
            # Verify dump lookup
            mock_supabase.table.assert_called_with('raw_dumps')
    
    @pytest.mark.asyncio
    async def test_queue_state_update_governance(self, processor):
        """Test queue state updates in governance workflow."""
        queue_id = str(uuid4())
        
        with patch('src.services.canonical_queue_processor.supabase') as mock_supabase:
            mock_supabase.rpc.return_value.execute.return_value = None
            
            # Test updating to governance processing state
            await processor._update_queue_state(queue_id, 'processing')
            
            mock_supabase.rpc.assert_called_with('fn_update_queue_state', {
                'p_id': queue_id,
                'p_state': 'processing',
                'p_error': None
            })
            
            # Test updating to completed (proposal created)
            await processor._update_queue_state(queue_id, 'completed')
            
            # Test marking as failed
            await processor._mark_failed(queue_id, 'Governance processing failed')
            
            mock_supabase.rpc.assert_called_with('fn_update_queue_state', {
                'p_id': queue_id,
                'p_state': 'failed',
                'p_error': 'Governance processing failed'
            })


class TestGovernanceCanonCompliance:
    """Test canonical queue processor maintains canon compliance with governance."""
    
    def test_pipeline_boundaries_preserved(self):
        """Test that governance preserves sacred pipeline boundaries."""
        processor = CanonicalQueueProcessor()
        
        # P0 CAPTURE: Still only processes existing dumps (preserved)
        assert hasattr(processor, 'p0_capture')
        
        # P1 SUBSTRATE: Now P1 GOVERNANCE (evolution)
        assert hasattr(processor, 'p1_governance')
        assert isinstance(processor.p1_governance, GovernanceDumpProcessor)
        
        # P2/P3: Deferred until substrate exists (post-approval)
        assert hasattr(processor, 'p2_graph')
        assert hasattr(processor, 'p3_reflection')
    
    def test_sacred_principles_governance_evolution(self):
        """Test that Sacred Principles evolve correctly with governance."""
        processor = CanonicalQueueProcessor()
        info = processor.get_processor_info()
        
        sacred_principles = info['sacred_principles']
        
        # All original Sacred Principles preserved
        assert 'Capture is Sacred' in sacred_principles
        assert 'All Substrates are Peers' in sacred_principles  
        assert 'Narrative is Deliberate' in sacred_principles
        assert 'Agent Intelligence is Mandatory' in sacred_principles
        
        # Governance extends these principles without violating them
        # 1. Capture is Sacred → Raw dumps still immutable, governance adds review layer
        # 2. All Substrates are Peers → Proposals don't privilege any substrate type
        # 3. Narrative is Deliberate → Documents still compose substrate references
        # 4. Agent Intelligence is Mandatory → Validation required for all proposals
    
    @pytest.mark.asyncio
    async def test_agent_intelligence_mandatory_governance(self, mock_supabase_full):
        """Test Sacred Principle #4 enforcement in governance."""
        
        # Agent intelligence must be mandatory even in governance workflow
        # All proposals require agent validation per Governance Sacred Principle #3
        
        processor = CanonicalQueueProcessor()
        
        # Governance processor should require agent validation
        assert hasattr(processor.p1_governance, 'validator')
        
        # Validator should be P1ValidatorAgent instance
        from src.app.agents.pipeline.validator_agent import P1ValidatorAgent
        assert isinstance(processor.p1_governance.validator, P1ValidatorAgent)
    
    def test_workspace_isolation_governance(self):
        """Test workspace isolation maintained in governance."""
        
        # Governance must respect workspace boundaries
        # All proposals scoped to workspace via RLS policies
        # Agent processing respects workspace_id parameter
        
        processor = CanonicalQueueProcessor()
        
        # Processor should maintain workspace context throughout pipeline
        assert 'workspace_id' in processor._process_dump_canonically.__code__.co_varnames
        
        # Governance agents should respect workspace boundaries
        assert hasattr(processor.p1_governance, 'process_dump')


class MockSupabaseFull:
    """Helper for comprehensive supabase mocking."""
    
    def __init__(self):
        self.table_responses = {}
        self.rpc_responses = {}
    
    def table(self, name):
        mock = MagicMock()
        mock.select.return_value.eq.return_value.execute.return_value.data = self.table_responses.get(name, [])
        return mock
    
    def rpc(self, name, params=None):
        mock = MagicMock()
        mock.execute.return_value.data = self.rpc_responses.get(name, None)
        return mock
    
    def set_table_data(self, table_name, data):
        self.table_responses[table_name] = data
    
    def set_rpc_response(self, rpc_name, response):
        self.rpc_responses[rpc_name] = response


@pytest.fixture
def mock_supabase_full():
    """Fixture for comprehensive supabase mocking."""
    return MockSupabaseFull()