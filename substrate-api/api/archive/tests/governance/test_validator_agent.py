"""Tests for P1 Validator Agent."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4, UUID

from src.app.agents.pipeline.validator_agent import (
    P1ValidatorAgent,
    ValidationReport,
    ProposalConflict,
    ProposalOperation,
    ProposalValidationRequest
)


class TestP1ValidatorAgent:
    """Test P1 Validator Agent for governance workflow."""
    
    @pytest.fixture
    def validator(self):
        """Create validator agent."""
        return P1ValidatorAgent()
    
    @pytest.fixture
    def sample_validation_request(self):
        """Sample validation request."""
        return ProposalValidationRequest(
            basket_id=uuid4(),
            workspace_id=uuid4(),
            ops=[
                ProposalOperation(
                    type='CreateBlock',
                    data={
                        'title': 'Strategic Goals',
                        'content': 'Focus on customer satisfaction and market growth',
                        'semantic_type': 'goal',
                        'confidence': 0.7
                    }
                ),
                ProposalOperation(
                    type='CreateContextItem',
                    data={
                        'label': 'Customer Experience',
                        'content': 'Customer-focused initiatives',
                        'confidence': 0.6
                    }
                )
            ],
            origin='human',
            provenance=[uuid4()]
        )
    
    @pytest.fixture
    def substrate_snapshot(self):
        """Mock substrate snapshot."""
        return {
            'blocks': [
                {
                    'id': str(uuid4()),
                    'title': 'Market Analysis',
                    'body_md': 'Analysis of market trends',
                    'semantic_type': 'insight',
                    'confidence_score': 0.8,
                    'state': 'ACCEPTED'
                }
            ],
            'context_items': [
                {
                    'id': str(uuid4()),
                    'title': 'Customer Success',
                    'normalized_label': 'customer success',
                    'content': 'Customer success initiatives',
                    'type': 'theme',
                    'state': 'ACTIVE'
                }
            ]
        }
    
    @patch('src.app.agents.pipeline.validator_agent.supabase')
    @pytest.mark.asyncio
    async def test_validate_proposal_success(self, mock_supabase, validator, sample_validation_request, substrate_snapshot):
        """Test successful proposal validation."""
        # Mock substrate snapshot retrieval
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = substrate_snapshot['blocks']
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = substrate_snapshot['context_items']
        
        # Mock document count for impact analysis
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{'id': str(uuid4())}]
        
        validator._get_substrate_snapshot = AsyncMock(return_value=substrate_snapshot)
        
        report = await validator.validate_proposal(sample_validation_request)
        
        assert isinstance(report, ValidationReport)
        assert 0.0 <= report.confidence <= 1.0
        assert isinstance(report.dupes, list)
        assert isinstance(report.warnings, list)
        assert isinstance(report.impact_summary, str)
        assert len(report.impact_summary) > 0
    
    @pytest.mark.asyncio
    async def test_validate_create_block_duplicate_detection(self, validator, substrate_snapshot):
        """Test duplicate detection for block creation."""
        # Operation that should trigger duplicate detection
        op = ProposalOperation(
            type='CreateBlock',
            data={
                'title': 'Market Analysis',  # Exact match with existing
                'content': 'Detailed market analysis',
                'semantic_type': 'insight'
            }
        )
        
        validation = await validator._validate_create_block(op, substrate_snapshot, uuid4())
        
        assert len(validation['conflicts']) > 0
        conflict = validation['conflicts'][0]
        assert conflict.conflict_type == 'duplicate'
        assert conflict.similarity_score > 0.9
    
    @pytest.mark.asyncio
    async def test_validate_create_context_item_similarity(self, validator, substrate_snapshot):
        """Test similarity detection for context item creation."""
        # Operation with similar but not identical label
        op = ProposalOperation(
            type='CreateContextItem',
            data={
                'label': 'Customer Success Team',  # Similar to 'Customer Success'
                'content': 'Team focused on customer success'
            }
        )
        
        validation = await validator._validate_create_context_item(op, substrate_snapshot, uuid4())
        
        assert len(validation['suggested_merges']) > 0
        assert validation['confidence'] > 0.5
    
    @pytest.mark.asyncio
    async def test_validate_merge_context_items_validation(self, validator, substrate_snapshot):
        """Test validation of context item merge operations."""
        existing_id = substrate_snapshot['context_items'][0]['id']
        non_existent_id = str(uuid4())
        
        # Valid merge operation
        valid_op = ProposalOperation(
            type='MergeContextItems',
            data={
                'from_ids': [existing_id],
                'canonical_id': existing_id
            }
        )
        
        validation = await validator._validate_merge_context_items(valid_op, substrate_snapshot, uuid4())
        assert len(validation['warnings']) == 0
        assert validation['confidence'] > 0.7
        
        # Invalid merge operation
        invalid_op = ProposalOperation(
            type='MergeContextItems',
            data={
                'from_ids': [non_existent_id],
                'canonical_id': existing_id
            }
        )
        
        validation = await validator._validate_merge_context_items(invalid_op, substrate_snapshot, uuid4())
        assert len(validation['warnings']) > 0
        assert validation['confidence'] < 0.5
    
    def test_calculate_similarity(self, validator):
        """Test text similarity calculation."""
        # Identical strings
        assert validator._calculate_similarity('test', 'test') == 1.0
        
        # Empty strings
        assert validator._calculate_similarity('', '') == 0.0
        assert validator._calculate_similarity('test', '') == 0.0
        
        # Similar strings
        similarity = validator._calculate_similarity('customer experience', 'customer success')
        assert 0.0 < similarity < 1.0
        
        # Completely different strings
        similarity = validator._calculate_similarity('apple', 'bicycle')
        assert similarity == 0.0
    
    @patch('src.app.agents.pipeline.validator_agent.supabase')
    @pytest.mark.asyncio
    async def test_generate_impact_summary(self, mock_supabase, validator):
        """Test impact summary generation."""
        operations = [
            ProposalOperation(type='CreateBlock', data={}),
            ProposalOperation(type='CreateBlock', data={}),
            ProposalOperation(type='CreateContextItem', data={})
        ]
        
        # Mock document count
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': str(uuid4())}, {'id': str(uuid4())}
        ]
        
        summary = await validator._generate_impact_summary(operations, uuid4(), uuid4())
        
        assert '2 CreateBlock' in summary
        assert '1 CreateContextItem' in summary
        assert 'affects 2 documents' in summary
    
    @patch('src.app.agents.pipeline.validator_agent.supabase')
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, mock_supabase, validator, sample_validation_request):
        """Test validation error handling."""
        # Mock substrate snapshot failure
        mock_supabase.table.return_value.select.side_effect = Exception("Database error")
        
        report = await validator.validate_proposal(sample_validation_request)
        
        # Should return safe default on error
        assert report.confidence == 0.3
        assert len(report.warnings) > 0
        assert 'Validation failed' in report.warnings[0]
        assert 'validation error' in report.impact_summary
    
    def test_get_agent_info(self, validator):
        """Test agent information retrieval."""
        info = validator.get_agent_info()
        
        assert info['name'] == 'P1ValidatorAgent'
        assert info['pipeline'] == 'P1_SUBSTRATE'
        assert info['type'] == 'validator'
        assert info['status'] == 'active'
        assert 'governance review' in info['sacred_rule']