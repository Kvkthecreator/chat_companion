"""
Simple test for context-aware substrate improvements - no pytest required.
"""

import asyncio
import sys
import os
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app.agents.pipeline.improved_substrate_agent import ImprovedP1SubstrateAgent
from infra.utils.supabase_client import supabase_admin_client as supabase


async def test_basket_context_view():
    """Test that the basket_substrate_context view works"""
    print("Test 1: Basket substrate context view...")

    try:
        # Query the view with a random basket (should return empty but not error)
        result = supabase.from_("basket_substrate_context")\
            .select("*")\
            .limit(1)\
            .execute()

        print(f"  ✅ View exists and is queryable")
        if result.data:
            print(f"  ✅ Sample data: {result.data[0].keys()}")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def test_extraction_metrics_logging():
    """Test extraction quality metrics logging"""
    print("\nTest 2: Extraction quality metrics logging...")

    try:
        test_metric_id = supabase.rpc(
            'log_extraction_metrics',
            {
                'p_dump_id': str(uuid4()),
                'p_basket_id': str(uuid4()),
                'p_workspace_id': str(uuid4()),
                'p_agent_version': 'test_context_aware_v1',
                'p_extraction_method': 'context_aware_extraction',
                'p_blocks_created': 7,
                'p_context_items_created': 4,
                'p_avg_confidence': 0.82,
                'p_processing_time_ms': 1500
            }
        ).execute()

        print(f"  ✅ Successfully logged metric: {test_metric_id.data}")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def test_block_usage_increment():
    """Test block usage tracking"""
    print("\nTest 3: Block usage tracking...")

    try:
        # Create test block
        block = supabase.table("blocks").insert({
            "basket_id": str(uuid4()),
            "workspace_id": str(uuid4()),
            "semantic_type": "test",
            "title": "Test usage tracking",
            "content": "Test content for usage",
            "status": "proposed"
        }).execute()

        block_id = block.data[0]["id"]
        print(f"  ✅ Created test block: {block_id}")

        # Increment usage 3 times
        for i in range(3):
            supabase.rpc('increment_block_usage', {'p_block_id': block_id}).execute()

        # Check usage score
        usage = supabase.table("block_usage")\
            .select("*")\
            .eq("block_id", block_id)\
            .single()\
            .execute()

        print(f"  ✅ Usage recorded: {usage.data['times_referenced']} references")
        print(f"  ✅ Usefulness score: {usage.data['usefulness_score']}")

        # Cleanup
        supabase.table("blocks").delete().eq("id", block_id).execute()

        return usage.data['times_referenced'] == 3 and usage.data['usefulness_score'] == 0.9

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def test_staleness_column():
    """Test staleness tracking column"""
    print("\nTest 4: Staleness tracking...")

    try:
        # Create test block
        block = supabase.table("blocks").insert({
            "basket_id": str(uuid4()),
            "workspace_id": str(uuid4()),
            "semantic_type": "test",
            "title": "Test staleness",
            "content": "Test staleness tracking",
            "status": "proposed"
        }).execute()

        block_id = block.data[0]["id"]

        # Check it has last_validated_at
        block_data = supabase.table("blocks")\
            .select("last_validated_at")\
            .eq("id", block_id)\
            .single()\
            .execute()

        print(f"  ✅ Block has last_validated_at: {block_data.data['last_validated_at']}")

        # Cleanup
        supabase.table("blocks").delete().eq("id", block_id).execute()

        return block_data.data['last_validated_at'] is not None

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def test_p1_agent_context_method():
    """Test P1 agent context fetching method"""
    print("\nTest 5: P1 Agent context-aware method...")

    try:
        agent = ImprovedP1SubstrateAgent()

        # Test with random IDs (should return empty context)
        context = await agent._get_basket_substrate_context(
            basket_id=uuid4(),
            workspace_id=uuid4()
        )

        print(f"  ✅ Context fetched: {context.keys()}")
        print(f"  ✅ Active blocks: {context['active_blocks_count']}")
        print(f"  ✅ Active context items: {context['active_context_items_count']}")

        # Test context instructions building
        instructions = agent._build_context_instructions(context)
        print(f"  ✅ Context instructions built: {len(instructions)} chars")

        return True

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("SUBSTRATE QUALITY IMPROVEMENTS - TEST SUITE")
    print("=" * 60)

    results = []

    results.append(await test_basket_context_view())
    results.append(await test_extraction_metrics_logging())
    results.append(await test_block_usage_increment())
    results.append(await test_staleness_column())
    results.append(await test_p1_agent_context_method())

    print("\n" + "=" * 60)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")

    if all(results):
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
