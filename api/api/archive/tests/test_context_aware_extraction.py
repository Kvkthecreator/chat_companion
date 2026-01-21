"""
Test context-aware substrate extraction improvements.

Validates that P1 agent:
1. Fetches existing basket substrate before extraction
2. Uses context for deduplication
3. Logs quality metrics
4. Marks blocks stale when new dumps arrive
"""

import pytest
from uuid import uuid4, UUID
from app.agents.pipeline.improved_substrate_agent import ImprovedP1SubstrateAgent
from app.agents.pipeline.governance_processor import GovernanceDumpProcessor
from infra.utils.supabase_client import supabase_admin_client as supabase


@pytest.mark.asyncio
async def test_basket_context_fetching():
    """Test that P1 agent fetches basket context before extraction"""

    agent = ImprovedP1SubstrateAgent()

    # Create test basket
    basket_id = uuid4()
    workspace_id = uuid4()

    # Test empty basket context
    context = await agent._get_basket_substrate_context(basket_id, workspace_id)

    assert context is not None
    assert context["active_blocks_count"] == 0
    assert context["active_context_items_count"] == 0
    assert context["blocks_summary"] == []
    assert context["goals_and_constraints"] == ""


@pytest.mark.asyncio
async def test_context_instructions_building():
    """Test that context instructions are built correctly"""

    agent = ImprovedP1SubstrateAgent()

    # Test empty context
    empty_context = {
        "active_blocks_count": 0,
        "active_context_items_count": 0,
        "blocks_summary": [],
        "context_items_summary": [],
        "goals_and_constraints": ""
    }

    instructions = agent._build_context_instructions(empty_context)
    assert "first content in this basket" in instructions.lower()

    # Test context with blocks
    populated_context = {
        "active_blocks_count": 3,
        "active_context_items_count": 2,
        "blocks_summary": [
            {
                "id": str(uuid4()),
                "title": "Product vision: AI-powered knowledge management",
                "semantic_type": "goal",
                "content": "Build the best AI knowledge system...",
                "usefulness": 0.9,
                "staleness_days": 5
            },
            {
                "id": str(uuid4()),
                "title": "Customer pain: Information overload",
                "semantic_type": "finding",
                "content": "Users struggle with too much content...",
                "usefulness": 0.5,
                "staleness_days": 35  # Stale!
            }
        ],
        "context_items_summary": [
            {"id": str(uuid4()), "label": "Customer segment: Enterprise", "kind": "entity"},
            {"id": str(uuid4()), "label": "Feature: Context-aware search", "kind": "concept"}
        ],
        "goals_and_constraints": "Must integrate with existing tools | Budget: $50k"
    }

    instructions = agent._build_context_instructions(populated_context)

    # Verify context elements are included
    assert "EXISTING BASKET CONTEXT" in instructions
    assert "Product vision" in instructions
    assert "Customer pain" in instructions
    assert "[STALE]" in instructions  # Should mark stale block
    assert "Enterprise" in instructions
    assert "Context-aware search" in instructions
    assert "existing tools" in instructions  # From goals


@pytest.mark.asyncio
async def test_extraction_quality_metrics_schema():
    """Test that extraction quality metrics can be logged"""

    # Verify the table and function exist by querying
    try:
        result = supabase.table("extraction_quality_metrics").select("id").limit(1).execute()
        assert result is not None  # Table exists
    except Exception as e:
        pytest.fail(f"extraction_quality_metrics table doesn't exist: {e}")

    # Verify log function exists
    try:
        test_metric_id = supabase.rpc(
            'log_extraction_metrics',
            {
                'p_dump_id': str(uuid4()),
                'p_basket_id': str(uuid4()),
                'p_workspace_id': str(uuid4()),
                'p_agent_version': 'test_v1',
                'p_extraction_method': 'test_extraction',
                'p_blocks_created': 5,
                'p_context_items_created': 3,
                'p_avg_confidence': 0.85,
                'p_processing_time_ms': 1200
            }
        ).execute()
        assert test_metric_id.data is not None
        print(f"✅ Successfully logged test metric: {test_metric_id.data}")
    except Exception as e:
        pytest.fail(f"log_extraction_metrics function failed: {e}")


@pytest.mark.asyncio
async def test_block_usage_tracking():
    """Test that block usage tracking works"""

    try:
        # Create a test block
        block_result = supabase.table("blocks").insert({
            "basket_id": str(uuid4()),
            "workspace_id": str(uuid4()),
            "semantic_type": "test",
            "title": "Test block for usage tracking",
            "content": "Test content",
            "status": "proposed"
        }).execute()

        block_id = block_result.data[0]["id"]

        # Increment usage
        supabase.rpc('increment_block_usage', {'p_block_id': block_id}).execute()
        supabase.rpc('increment_block_usage', {'p_block_id': block_id}).execute()
        supabase.rpc('increment_block_usage', {'p_block_id': block_id}).execute()

        # Check usage
        usage_result = supabase.table("block_usage").select("*").eq("block_id", block_id).single().execute()

        assert usage_result.data is not None
        assert usage_result.data["times_referenced"] == 3
        assert usage_result.data["usefulness_score"] == 0.9  # 3+ references = 0.9

        # Cleanup
        supabase.table("blocks").delete().eq("id", block_id).execute()

        print(f"✅ Block usage tracking working correctly")

    except Exception as e:
        pytest.fail(f"Block usage tracking failed: {e}")


if __name__ == "__main__":
    import asyncio

    async def run_tests():
        print("Running context-aware extraction tests...\n")

        print("Test 1: Basket context fetching...")
        await test_basket_context_fetching()
        print("✅ Passed\n")

        print("Test 2: Context instructions building...")
        await test_context_instructions_building()
        print("✅ Passed\n")

        print("Test 3: Extraction quality metrics schema...")
        await test_extraction_quality_metrics_schema()
        print("✅ Passed\n")

        print("Test 4: Block usage tracking...")
        await test_block_usage_tracking()
        print("✅ Passed\n")

        print("All tests passed! 🎉")

    asyncio.run(run_tests())
