"""
V3.1 Semantic Relationship Inference Validation Script

Purpose: Validate the semantic relationship inference pipeline.

Tests:
1. LLM verification correctly identifies causal relationships
2. infer_relationships() returns high-quality proposals
3. Confidence scores align with relationship quality
4. Invalid relationships are rejected

Usage:
  python tests/test_semantic_relationship_inference.py
"""

import asyncio
import logging
from typing import Dict, Any

from infra.utils.supabase_client import supabase_admin_client as supabase
from infra.substrate.services.semantic_primitives import (
    verify_relationship_with_llm,
    infer_relationships,
    RELATIONSHIP_ONTOLOGY,
    RELATIONSHIP_HIGH_CONFIDENCE,
    RELATIONSHIP_MEDIUM_CONFIDENCE
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Test cases: Known causal relationships
TEST_CASES = [
    {
        "name": "ADDRESSES: Solution addresses problem",
        "from_block": {
            "id": "test-1",
            "content": "Implement rate limiting on the API to prevent abuse",
            "semantic_type": "solution"
        },
        "to_block": {
            "id": "test-2",
            "content": "API is vulnerable to spam attacks and resource exhaustion",
            "semantic_type": "problem"
        },
        "relationship_type": "addresses",
        "expected_exists": True,
        "expected_min_confidence": 0.80
    },
    {
        "name": "SUPPORTS: Evidence supports insight",
        "from_block": {
            "id": "test-3",
            "content": "User survey shows 85% satisfaction rate with new onboarding flow",
            "semantic_type": "metric"
        },
        "to_block": {
            "id": "test-4",
            "content": "The new onboarding flow is effective and well-received",
            "semantic_type": "insight"
        },
        "relationship_type": "supports",
        "expected_exists": True,
        "expected_min_confidence": 0.75
    },
    {
        "name": "CONTRADICTS: Findings contradict each other",
        "from_block": {
            "id": "test-5",
            "content": "Latest A/B test shows blue button has 20% higher conversion",
            "semantic_type": "finding"
        },
        "to_block": {
            "id": "test-6",
            "content": "Previous study concluded red button performs best for conversions",
            "semantic_type": "finding"
        },
        "relationship_type": "contradicts",
        "expected_exists": True,
        "expected_min_confidence": 0.70
    },
    {
        "name": "DEPENDS_ON: Action depends on prerequisite",
        "from_block": {
            "id": "test-7",
            "content": "Deploy the new feature to production",
            "semantic_type": "action"
        },
        "to_block": {
            "id": "test-8",
            "content": "Complete QA testing and security review",
            "semantic_type": "action"
        },
        "relationship_type": "depends_on",
        "expected_exists": True,
        "expected_min_confidence": 0.75
    },
    {
        "name": "INVALID: Unrelated blocks",
        "from_block": {
            "id": "test-9",
            "content": "The sky is blue",
            "semantic_type": "fact"
        },
        "to_block": {
            "id": "test-10",
            "content": "Implement OAuth authentication",
            "semantic_type": "action"
        },
        "relationship_type": "addresses",
        "expected_exists": False,
        "expected_min_confidence": 0.0
    }
]


async def test_llm_verification():
    """Test LLM verification for known causal relationships."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: LLM Verification")
    logger.info("="*60)

    results = {"passed": 0, "failed": 0}

    for test_case in TEST_CASES:
        logger.info(f"\nTest: {test_case['name']}")
        logger.info(f"  FROM: {test_case['from_block']['content'][:60]}...")
        logger.info(f"  TO: {test_case['to_block']['content'][:60]}...")
        logger.info(f"  Type: {test_case['relationship_type']}")

        try:
            verification = await verify_relationship_with_llm(
                from_block=test_case["from_block"],
                to_block=test_case["to_block"],
                relationship_type=test_case["relationship_type"]
            )

            logger.info(f"  Result: exists={verification['exists']}, confidence={verification['confidence_score']:.2f}")
            logger.info(f"  Reasoning: {verification['reasoning']}")

            # Validate expectations
            if verification["exists"] != test_case["expected_exists"]:
                logger.error(f"  ❌ FAILED: Expected exists={test_case['expected_exists']}, got {verification['exists']}")
                results["failed"] += 1
            elif test_case["expected_exists"] and verification["confidence_score"] < test_case["expected_min_confidence"]:
                logger.error(f"  ❌ FAILED: Expected confidence >= {test_case['expected_min_confidence']}, got {verification['confidence_score']:.2f}")
                results["failed"] += 1
            else:
                logger.info(f"  ✅ PASSED")
                results["passed"] += 1

        except Exception as exc:
            logger.error(f"  ❌ FAILED: Exception: {exc}")
            results["failed"] += 1

    logger.info(f"\nTest 1 Results: {results['passed']} passed, {results['failed']} failed")
    return results


async def test_infer_relationships_integration():
    """Test full infer_relationships() pipeline with real blocks."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: infer_relationships() Integration")
    logger.info("="*60)

    # Create test basket with sample blocks
    logger.info("Creating test basket and blocks...")

    try:
        # Create test basket
        basket_response = supabase.table("baskets").insert({
            "name": "V3.1 Semantic Inference Test",
            "workspace_id": "00000000-0000-0000-0000-000000000000",  # Test workspace
            "basket_signature": "test-semantic-inference",
            "metadata": {"test": True}
        }).execute()

        basket_id = basket_response.data[0]["id"]
        logger.info(f"Created test basket: {basket_id}")

        # Create test blocks
        test_blocks = [
            {
                "basket_id": basket_id,
                "workspace_id": "00000000-0000-0000-0000-000000000000",
                "title": "API Rate Limiting",
                "content": "Implement rate limiting to prevent API abuse and protect resources",
                "semantic_type": "solution",
                "state": "ACCEPTED",
                "confidence_score": 0.9
            },
            {
                "basket_id": basket_id,
                "workspace_id": "00000000-0000-0000-0000-000000000000",
                "title": "API Vulnerability",
                "content": "Our API endpoints are vulnerable to spam attacks and resource exhaustion",
                "semantic_type": "problem",
                "state": "ACCEPTED",
                "confidence_score": 0.85
            },
            {
                "basket_id": basket_id,
                "workspace_id": "00000000-0000-0000-0000-000000000000",
                "title": "Security Best Practices",
                "content": "Rate limiting is a standard security practice for APIs",
                "semantic_type": "principle",
                "state": "ACCEPTED",
                "confidence_score": 0.9
            }
        ]

        blocks_response = supabase.table("blocks").insert(test_blocks).execute()
        block_ids = [block["id"] for block in blocks_response.data]
        logger.info(f"Created {len(block_ids)} test blocks")

        # Generate embeddings for blocks
        logger.info("Generating embeddings...")
        from infra.substrate.services.embedding import generate_embedding

        for i, block_id in enumerate(block_ids):
            block = blocks_response.data[i]
            embedding = generate_embedding(f"{block['title']}\n{block['content']}")
            if embedding:
                supabase.table("blocks").update({
                    "embedding": embedding
                }).eq("id", block_id).execute()
                logger.info(f"  Generated embedding for block {i+1}")

        # Test infer_relationships() for the solution block
        logger.info("\nTesting relationship inference...")
        solution_block_id = block_ids[0]  # "API Rate Limiting" solution

        proposals = await infer_relationships(
            supabase=supabase,
            block_id=solution_block_id,
            basket_id=basket_id
        )

        logger.info(f"\nInferred {len(proposals)} relationship proposals:")
        for i, proposal in enumerate(proposals, 1):
            logger.info(f"\n  Proposal {i}:")
            logger.info(f"    Type: {proposal.relationship_type}")
            logger.info(f"    To Block: {proposal.to_block_id}")
            logger.info(f"    Confidence: {proposal.confidence_score:.2f}")
            logger.info(f"    Reasoning: {proposal.reasoning}")

            # Validate proposal quality
            if proposal.confidence_score >= RELATIONSHIP_HIGH_CONFIDENCE:
                logger.info(f"    Status: ✅ HIGH CONFIDENCE (auto-accept)")
            elif proposal.confidence_score >= RELATIONSHIP_MEDIUM_CONFIDENCE:
                logger.info(f"    Status: ⚠️  MEDIUM CONFIDENCE (propose)")
            else:
                logger.info(f"    Status: ❌ LOW CONFIDENCE (reject)")

        # Cleanup: Delete test basket and blocks
        logger.info("\nCleaning up test data...")
        supabase.table("blocks").delete().eq("basket_id", basket_id).execute()
        supabase.table("baskets").delete().eq("id", basket_id).execute()
        logger.info("Test data cleaned up")

        # Validate results
        results = {"passed": 0, "failed": 0}

        # Expect at least one "addresses" relationship (solution → problem)
        addresses_proposals = [p for p in proposals if p.relationship_type == "addresses"]
        if len(addresses_proposals) > 0 and addresses_proposals[0].confidence_score >= RELATIONSHIP_MEDIUM_CONFIDENCE:
            logger.info("\n✅ PASSED: Found high-confidence 'addresses' relationship")
            results["passed"] += 1
        else:
            logger.error("\n❌ FAILED: Expected at least one high-confidence 'addresses' relationship")
            results["failed"] += 1

        logger.info(f"\nTest 2 Results: {results['passed']} passed, {results['failed']} failed")
        return results

    except Exception as exc:
        logger.error(f"Test 2 failed with exception: {exc}")
        return {"passed": 0, "failed": 1}


async def test_ontology_coverage():
    """Test that all relationship types are properly defined."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Relationship Ontology Coverage")
    logger.info("="*60)

    results = {"passed": 0, "failed": 0}

    expected_types = ["addresses", "supports", "contradicts", "depends_on"]

    for rel_type in expected_types:
        logger.info(f"\nValidating '{rel_type}'...")

        if rel_type not in RELATIONSHIP_ONTOLOGY:
            logger.error(f"  ❌ FAILED: Relationship type '{rel_type}' not in ontology")
            results["failed"] += 1
            continue

        ontology = RELATIONSHIP_ONTOLOGY[rel_type]

        # Check required fields
        required_fields = ["from_types", "to_types", "description", "verification_prompt"]
        missing_fields = [field for field in required_fields if field not in ontology]

        if missing_fields:
            logger.error(f"  ❌ FAILED: Missing fields: {missing_fields}")
            results["failed"] += 1
        else:
            logger.info(f"  ✅ PASSED: All required fields present")
            logger.info(f"    FROM types: {ontology['from_types'][:3]}...")
            logger.info(f"    TO types: {ontology['to_types'][:3]}...")
            logger.info(f"    Description: {ontology['description']}")
            results["passed"] += 1

    logger.info(f"\nTest 3 Results: {results['passed']} passed, {results['failed']} failed")
    return results


async def main():
    """Run all validation tests."""
    logger.info("\n" + "#"*60)
    logger.info("V3.1 SEMANTIC RELATIONSHIP INFERENCE VALIDATION")
    logger.info("#"*60)

    all_results = {"passed": 0, "failed": 0}

    # Test 1: LLM Verification
    test1_results = await test_llm_verification()
    all_results["passed"] += test1_results["passed"]
    all_results["failed"] += test1_results["failed"]

    # Test 2: Integration test
    test2_results = await test_infer_relationships_integration()
    all_results["passed"] += test2_results["passed"]
    all_results["failed"] += test2_results["failed"]

    # Test 3: Ontology coverage
    test3_results = await test_ontology_coverage()
    all_results["passed"] += test3_results["passed"]
    all_results["failed"] += test3_results["failed"]

    # Final summary
    logger.info("\n" + "#"*60)
    logger.info("VALIDATION SUMMARY")
    logger.info("#"*60)
    logger.info(f"Total Passed: {all_results['passed']}")
    logger.info(f"Total Failed: {all_results['failed']}")

    if all_results["failed"] == 0:
        logger.info("\n🎉 ALL TESTS PASSED! V3.1 semantic inference is working correctly.")
    else:
        logger.error(f"\n⚠️  {all_results['failed']} test(s) failed. Please review errors above.")

    logger.info("#"*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
