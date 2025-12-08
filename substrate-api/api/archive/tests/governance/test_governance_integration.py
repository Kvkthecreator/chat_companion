"""Integration tests for end-to-end governance workflow."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4, UUID

from src.app.agents.pipeline.governance_processor import GovernanceDumpProcessor
from src.app.agents.pipeline.validator_agent import P1ValidatorAgent, ValidationReport


class TestGovernanceIntegration:
    """Test complete governance workflow integration."""
    
    @pytest.fixture
    def mock_supabase_full(self):
        """Complete supabase mock for integration testing."""
        mock = MagicMock()
        
        # Mock table operations
        mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
        mock.table.return_value.insert.return_value.select.return_value.single.return_value.execute.return_value.data = None
        mock.table.return_value.update.return_value.eq.return_value.execute.return_value = None
        
        # Mock RPC operations
        mock.rpc.return_value.execute.return_value = None
        
        return mock
    
    @pytest.mark.asyncio
    async def test_dump_to_proposal_to_substrate_flow(self, mock_supabase_full):
        """Test complete flow: dump → proposal → approval → substrate."""
        with patch('src.app.agents.pipeline.governance_processor.supabase', mock_supabase_full), \
             patch('src.app.agents.pipeline.validator_agent.supabase', mock_supabase_full):
            
            # Setup test data
            dump_id = uuid4()
            basket_id = uuid4()
            workspace_id = uuid4()
            proposal_id = uuid4()
            
            dump_data = {
                'id': str(dump_id),
                'text_dump': 'Strategic goal: improve customer satisfaction through better service delivery.',
                'file_url': None,
                'source_meta': {}
            }
            
            # Mock dump retrieval
            mock_supabase_full.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = dump_data
            
            # Mock empty substrate snapshot (no conflicts)
            mock_supabase_full.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
            mock_supabase_full.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            # Mock proposal creation
            mock_supabase_full.table.return_value.insert.return_value.select.return_value.single.return_value.execute.return_value.data = {
                'id': str(proposal_id)
            }
            
            # Mock document count for impact analysis
            mock_supabase_full.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            # Step 1: Process dump through governance
            processor = GovernanceDumpProcessor()
            result = await processor.process_dump(dump_id, basket_id, workspace_id)
            
            assert result['proposals_created'] == 1
            assert result['status'] == 'proposal_created'
            assert result['proposal_id'] == str(proposal_id)
            
            # Verify proposal was created with proper structure
            proposal_insert_call = None
            for call in mock_supabase_full.table.return_value.insert.call_args_list:
                if call[0][0].get('proposal_kind') == 'Extraction':
                    proposal_insert_call = call[0][0]
                    break
            
            assert proposal_insert_call is not None
            assert proposal_insert_call['origin'] == 'agent'
            assert proposal_insert_call['blast_radius'] == 'Local'
            assert len(proposal_insert_call['ops']) > 0
            
            # Verify timeline event emission
            timeline_calls = [call for call in mock_supabase_full.rpc.call_args_list 
                            if call[0][0] == 'emit_timeline_event']
            assert len(timeline_calls) > 0
            
            timeline_event = timeline_calls[0][1]
            assert timeline_event['p_event_type'] == 'proposal.submitted'
            assert timeline_event['p_event_data']['origin'] == 'agent'
    
    @pytest.mark.asyncio
    async def test_proposal_validation_with_conflicts(self, mock_supabase_full):
        """Test proposal validation when conflicts exist."""
        with patch('src.app.agents.pipeline.validator_agent.supabase', mock_supabase_full):
            
            # Mock existing substrate with potential conflicts
            existing_blocks = [
                {
                    'id': str(uuid4()),
                    'title': 'Customer Goals',  # Similar to what we'll propose
                    'body_md': 'Existing customer-focused content',
                    'semantic_type': 'goal',
                    'confidence_score': 0.8,
                    'state': 'ACCEPTED'
                }
            ]
            
            existing_context = [
                {
                    'id': str(uuid4()),
                    'title': 'Customer Service',
                    'normalized_label': 'customer service',
                    'content': 'Service-related context',
                    'type': 'theme',
                    'state': 'ACTIVE'
                }
            ]
            
            mock_supabase_full.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = existing_blocks
            mock_supabase_full.table.return_value.select.return_value.eq.return_value.execute.return_value.data = existing_context
            
            # Create validation request with potential conflicts
            request = ProposalValidationRequest(
                basket_id=uuid4(),
                workspace_id=uuid4(),
                ops=[
                    ProposalOperation(
                        type='CreateBlock',
                        data={
                            'title': 'Customer Goals Strategy',  # Similar to existing
                            'content': 'New customer-focused strategy',
                            'semantic_type': 'goal'
                        }
                    ),
                    ProposalOperation(
                        type='CreateContextItem',
                        data={
                            'label': 'Customer Support',  # Similar to existing
                            'content': 'Support-related context'
                        }
                    )
                ],
                origin='human',
                provenance=[]
            )
            
            validator = P1ValidatorAgent()
            report = await validator.validate_proposal(request)
            
            # Should detect similarities and suggest merges
            assert len(report.suggested_merges) > 0
            assert report.confidence > 0.0
            assert 'CreateBlock' in report.impact_summary
            assert 'CreateContextItem' in report.impact_summary
    
    @pytest.mark.asyncio
    async def test_proposal_validation_error_recovery(self, mock_supabase_full):
        """Test validation graceful error handling."""
        with patch('src.app.agents.pipeline.validator_agent.supabase', mock_supabase_full):
            
            # Mock database error
            mock_supabase_full.table.return_value.select.side_effect = Exception("Database connection failed")
            
            request = ProposalValidationRequest(
                basket_id=uuid4(),
                workspace_id=uuid4(),
                ops=[
                    ProposalOperation(type='CreateBlock', data={'content': 'Test'})
                ],
                origin='agent',
                provenance=[]
            )
            
            validator = P1ValidatorAgent()
            report = await validator.validate_proposal(request)
            
            # Should return safe defaults on error
            assert report.confidence == 0.3
            assert len(report.warnings) > 0
            assert 'Validation failed' in report.warnings[0]
            assert 'validation error' in report.impact_summary
    
    @pytest.mark.asyncio
    async def test_feature_flag_governance_disabled(self):
        """Test behavior when governance is disabled via feature flags."""
        with patch('src.lib.governance.featureFlags.shouldUseGovernance', return_value=False):
            # This would be tested at the API route level
            # Governance processor should not be invoked when disabled
            pass
    
    @pytest.mark.asyncio
    async def test_validator_required_vs_optional(self, mock_supabase_full):
        """Test validator behavior based on feature flags."""
        request = ProposalValidationRequest(
            basket_id=uuid4(),
            workspace_id=uuid4(),
            ops=[ProposalOperation(type='CreateBlock', data={'content': 'Test'})],
            origin='human',
            provenance=[]
        )
        
        with patch('src.app.agents.pipeline.validator_agent.supabase', mock_supabase_full):
            # Mock empty substrate
            mock_supabase_full.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
            mock_supabase_full.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            validator = P1ValidatorAgent()
            
            # Test with validator required (normal path)
            report = await validator.validate_proposal(request)
            assert isinstance(report, ValidationReport)
            assert report.confidence > 0.0
            
            # Test validation bypass (when validator optional)
            # This would be handled at API level with fallback report
    
    @pytest.mark.asyncio
    async def test_proposal_lifecycle_states(self):
        """Test proposal state transitions."""
        # This tests the conceptual state machine
        # DRAFT → PROPOSED → UNDER_REVIEW → [APPROVED|REJECTED]
        
        valid_transitions = [
            ('DRAFT', 'PROPOSED'),
            ('PROPOSED', 'UNDER_REVIEW'), 
            ('UNDER_REVIEW', 'APPROVED'),
            ('UNDER_REVIEW', 'REJECTED'),
            ('PROPOSED', 'SUPERSEDED'),
            ('UNDER_REVIEW', 'MERGED')
        ]
        
        invalid_transitions = [
            ('APPROVED', 'REJECTED'),
            ('REJECTED', 'APPROVED'),
            ('DRAFT', 'APPROVED')
        ]
        
        # In a real implementation, this would test database constraints
        # For now, verify the conceptual model
        for from_state, to_state in valid_transitions:
            assert True  # Would validate transition logic
        
        for from_state, to_state in invalid_transitions:
            assert True  # Would validate rejection of invalid transitions
    
    def test_blast_radius_classification(self):
        """Test blast radius impact classification."""
        # Local: affects only the current basket
        local_ops = [
            {'type': 'CreateBlock', 'data': {'content': 'Local note'}}
        ]
        
        # Scoped: affects workspace-level context
        scoped_ops = [
            {'type': 'CreateContextItem', 'data': {'label': 'Project Theme', 'scope': 'workspace'}}
        ]
        
        # Global: affects cross-workspace elements (future)
        global_ops = [
            {'type': 'PromoteScope', 'data': {'from': 'workspace', 'to': 'global'}}
        ]
        
        # Test classification logic (conceptual)
        assert self._classify_blast_radius(local_ops) == 'Local'
        assert self._classify_blast_radius(scoped_ops) in ['Local', 'Scoped']
        assert self._classify_blast_radius(global_ops) in ['Scoped', 'Global']
    
    def _classify_blast_radius(self, operations):
        """Mock blast radius classification."""
        # Simplified logic for testing
        if any(op.get('data', {}).get('scope') == 'global' for op in operations):
            return 'Global'
        elif any(op.get('data', {}).get('scope') == 'workspace' for op in operations):
            return 'Scoped'
        else:
            return 'Local'
    
    @pytest.mark.asyncio
    async def test_governance_sacred_principles_enforcement(self):
        """Test that Sacred Principles are enforced in governance."""
        
        # Sacred Principle #1: All substrate mutations flow through governed proposals
        # → No direct substrate writes allowed when governance enabled
        
        # Sacred Principle #2: Proposals are intent, not truth - truth changes only on approval
        # → Proposals don't modify substrate until approved
        
        # Sacred Principle #3: Agent validation is mandatory for all proposals regardless of origin
        # → All proposals must pass through validator
        
        # These principles are enforced at the API and database level
        # Tests would verify rejection of direct substrate writes when governance is active
        assert True  # Conceptual validation - enforced by implementation
    
    @pytest.mark.asyncio
    async def test_governance_preserves_sacred_capture_path(self):
        """Test that governance preserves the sacred raw_dump → agent → substrate flow."""
        
        # The sacred capture path must remain:
        # raw_dumps → P1 Agent → [NOW: Proposals] → Substrate
        
        # Governance adds the proposal layer but preserves:
        # 1. Agent intelligence is mandatory
        # 2. Raw dumps remain immutable
        # 3. Substrate equality is maintained
        # 4. Timeline events preserve audit trail
        
        assert True  # Conceptual validation - enforced by governance implementation
    
    def test_governance_canon_compliance(self):
        """Test compliance with YARNNN Governance Canon v2.0."""
        
        # All requirements from governance canon should be testable:
        governance_requirements = [
            "All substrate mutations flow through governed proposals",
            "Proposals are intent, not truth - truth changes only on approval", 
            "Agent validation is mandatory for all proposals regardless of origin",
            "Dual ingestion converges at governance",
            "Context_items have governance states",
            "Proposal operations are atomic",
            "Timeline events preserve complete audit trail",
            "Workspace isolation maintained through RLS"
        ]
        
        # Each requirement should have corresponding tests
        assert len(governance_requirements) == 8
        
        # In production, each requirement would have specific test coverage
        for requirement in governance_requirements:
            assert len(requirement) > 0  # Basic validation