"""Tests for block lifecycle enforcement."""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.app.memory.blocks import (
    BlockLifecycleService, 
    BlockProposalService,
    StateTransitionError
)


class TestBlockLifecycleService:
    """Test block state transitions and validation."""
    
    def test_valid_transitions(self):
        """Test that valid state transitions are allowed."""
        # PROPOSED can go to ACCEPTED or REJECTED
        BlockLifecycleService.validate_transition("PROPOSED", "ACCEPTED", "user")
        BlockLifecycleService.validate_transition("PROPOSED", "REJECTED", "user")
        
        # ACCEPTED can go to LOCKED or SUPERSEDED
        BlockLifecycleService.validate_transition("ACCEPTED", "LOCKED", "user")
        BlockLifecycleService.validate_transition("ACCEPTED", "SUPERSEDED", "user")
        
        # LOCKED can go to CONSTANT or SUPERSEDED
        BlockLifecycleService.validate_transition("LOCKED", "CONSTANT", "user")
        BlockLifecycleService.validate_transition("LOCKED", "SUPERSEDED", "user")
    
    def test_invalid_transitions(self):
        """Test that invalid state transitions are rejected."""
        with pytest.raises(StateTransitionError, match="Cannot transition from PROPOSED to LOCKED"):
            BlockLifecycleService.validate_transition("PROPOSED", "LOCKED", "user")
            
        with pytest.raises(StateTransitionError, match="Cannot transition from CONSTANT"):
            BlockLifecycleService.validate_transition("CONSTANT", "ACCEPTED", "user")
            
        with pytest.raises(StateTransitionError, match="Cannot transition from REJECTED"):
            BlockLifecycleService.validate_transition("REJECTED", "ACCEPTED", "user")
    
    def test_agent_restrictions(self):
        """Test that agents cannot set user-only states."""
        with pytest.raises(StateTransitionError, match="Agents cannot set state to ACCEPTED"):
            BlockLifecycleService.validate_transition("PROPOSED", "ACCEPTED", "agent")
            
        with pytest.raises(StateTransitionError, match="Agents cannot set state to LOCKED"):
            BlockLifecycleService.validate_transition("ACCEPTED", "LOCKED", "agent")
        
        # But agents CAN propose SUPERSEDED
        BlockLifecycleService.validate_transition("ACCEPTED", "SUPERSEDED", "agent")
    
    def test_content_modification_rules(self):
        """Test content modification permissions by state."""
        # Users can modify in most states
        assert BlockLifecycleService.can_modify_content("PROPOSED", "user") == True
        assert BlockLifecycleService.can_modify_content("ACCEPTED", "user") == True
        
        # But not in locked/final states
        assert BlockLifecycleService.can_modify_content("LOCKED", "user") == False
        assert BlockLifecycleService.can_modify_content("CONSTANT", "user") == False
        assert BlockLifecycleService.can_modify_content("REJECTED", "user") == False
        
        # Agents can only modify PROPOSED blocks
        assert BlockLifecycleService.can_modify_content("PROPOSED", "agent") == True
        assert BlockLifecycleService.can_modify_content("ACCEPTED", "agent") == False
        assert BlockLifecycleService.can_modify_content("LOCKED", "agent") == False


class TestBlockProposalService:
    """Test agent block proposal workflow."""
    
    @patch('src.app.memory.blocks.lifecycle.supabase')
    @pytest.mark.asyncio
    async def test_propose_block(self, mock_supabase):
        """Test creating a new block proposal."""
        basket_id = uuid4()
        agent_id = "test-agent"
        
        # Mock supabase responses
        mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
            "workspace_id": "test-workspace"
        }
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "new-block-id"}]
        
        result = await BlockProposalService.propose_block(
            basket_id=basket_id,
            semantic_type="insight",
            content="Test insight content",
            agent_id=agent_id,
            scope="basket"
        )
        
        # Verify block was created with PROPOSED state
        block_insert_call = mock_supabase.table.return_value.insert.call_args_list[0]
        block_data = block_insert_call[0][0]
        
        assert block_data["state"] == "PROPOSED"
        assert block_data["semantic_type"] == "insight"
        assert block_data["content"] == "Test insight content"
        assert block_data["basket_id"] == str(basket_id)
        
        # Verify event was created
        event_insert_call = mock_supabase.table.return_value.insert.call_args_list[1]
        event_data = event_insert_call[0][0]
        
        assert event_data["kind"] == "block.proposed"
        assert event_data["payload"]["agent_id"] == agent_id


@pytest.fixture
def sample_block_data():
    """Sample block data for testing."""
    return {
        "id": str(uuid4()),
        "basket_id": str(uuid4()),
        "semantic_type": "insight",
        "content": "Test content",
        "state": "PROPOSED",
        "version": 1,
        "workspace_id": "test-workspace"
    }


class TestBlockLifecycleIntegration:
    """Integration tests for the complete lifecycle workflow."""
    
    def test_complete_proposal_acceptance_flow(self, sample_block_data):
        """Test the full flow from proposal to acceptance."""
        # This would test:
        # 1. Agent proposes block (PROPOSED state)
        # 2. User reviews proposal 
        # 3. User accepts proposal (ACCEPTED state)
        # 4. Revision and event records are created
        
        # Implementation would use test database or mocked supabase
        pass
    
    def test_block_update_with_lifecycle_check(self, sample_block_data):
        """Test that block updates respect lifecycle state."""
        # This would test:
        # 1. User can update ACCEPTED block content
        # 2. User cannot update LOCKED block content
        # 3. Agent cannot update ACCEPTED block content
        
        pass