"""
V3.1 Batch Relationship Inference Job

Purpose: Backfill semantic relationships for existing substrate blocks.
This is useful for:
- Initial onboarding of existing workspaces
- Re-processing after ontology updates
- Periodic relationship refresh

Usage:
  python -m jobs.batch_relationship_inference --workspace-id <uuid>
  python -m jobs.batch_relationship_inference --basket-id <uuid>
"""

import argparse
import asyncio
import logging
from typing import List, Optional
from uuid import UUID

from infra.utils.supabase_client import supabase_admin_client as supabase
from infra.substrate.services.semantic_primitives import (
    infer_relationships,
    RELATIONSHIP_HIGH_CONFIDENCE,
    RELATIONSHIP_MEDIUM_CONFIDENCE,
    RelationshipProposal
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def batch_infer_relationships(
    basket_id: str,
    batch_size: int = 10,
    dry_run: bool = False
) -> dict:
    """
    Infer relationships for all blocks in a basket.

    Args:
        basket_id: Basket UUID
        batch_size: Number of blocks to process concurrently
        dry_run: If True, only log proposals without creating relationships

    Returns:
        Statistics dict with counts
    """
    logger.info(f"Starting batch relationship inference for basket {basket_id}")

    # Get all blocks in basket that need relationship inference
    blocks_response = supabase.table("blocks").select("id, title, semantic_type").eq(
        "basket_id", basket_id
    ).in_("state", ["ACCEPTED", "LOCKED", "CONSTANT"]).execute()

    block_ids = [block["id"] for block in blocks_response.data]

    if not block_ids:
        logger.info(f"No blocks found in basket {basket_id}")
        return {
            "blocks_processed": 0,
            "proposals_generated": 0,
            "relationships_created": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "errors": 0
        }

    logger.info(f"Processing {len(block_ids)} blocks in batches of {batch_size}")

    stats = {
        "blocks_processed": 0,
        "proposals_generated": 0,
        "relationships_created": 0,
        "high_confidence": 0,
        "medium_confidence": 0,
        "errors": 0
    }

    # Process blocks in batches
    for i in range(0, len(block_ids), batch_size):
        batch = block_ids[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(block_ids) + batch_size - 1)//batch_size}")

        # Infer relationships for each block in batch
        batch_proposals = []
        for block_id in batch:
            try:
                proposals = await infer_relationships(
                    supabase=supabase,
                    block_id=block_id,
                    basket_id=basket_id
                )
                batch_proposals.extend(proposals)
                stats["blocks_processed"] += 1

                logger.info(
                    f"Block {block_id}: Found {len(proposals)} relationship proposals"
                )

            except Exception as exc:
                logger.error(f"Failed to infer relationships for block {block_id}: {exc}")
                stats["errors"] += 1
                continue

        stats["proposals_generated"] += len(batch_proposals)

        # Create relationships (unless dry run)
        if not dry_run and batch_proposals:
            created = await _create_relationships_batch(basket_id, batch_proposals)
            stats["relationships_created"] += len(created)

            # Count by confidence
            for proposal in batch_proposals:
                if proposal.confidence_score >= RELATIONSHIP_HIGH_CONFIDENCE:
                    stats["high_confidence"] += 1
                elif proposal.confidence_score >= RELATIONSHIP_MEDIUM_CONFIDENCE:
                    stats["medium_confidence"] += 1

        elif dry_run:
            logger.info(f"[DRY RUN] Would create {len(batch_proposals)} relationships")

        # Rate limiting: brief pause between batches
        if i + batch_size < len(block_ids):
            await asyncio.sleep(0.5)

    logger.info(f"Batch inference complete: {stats}")
    return stats


async def _create_relationships_batch(
    basket_id: str,
    proposals: List[RelationshipProposal]
) -> List[dict]:
    """
    Create relationships from proposals with confidence-based governance.

    Args:
        basket_id: Basket UUID (not used but kept for consistency)
        proposals: List of relationship proposals

    Returns:
        List of created relationship records
    """
    if not proposals:
        return []

    try:
        # Prepare relationship data
        relationship_data = []
        for proposal in proposals:
            # Determine state based on confidence
            if proposal.confidence_score >= RELATIONSHIP_HIGH_CONFIDENCE:
                state = "ACCEPTED"
            elif proposal.confidence_score >= RELATIONSHIP_MEDIUM_CONFIDENCE:
                state = "PROPOSED"
            else:
                # Skip low confidence
                continue

            relationship_data.append({
                "from_block_id": str(proposal.from_block_id),
                "to_block_id": str(proposal.to_block_id),
                "relationship_type": proposal.relationship_type,
                "confidence_score": proposal.confidence_score,
                "inference_method": proposal.inference_method,
                "state": state,
                "metadata": {
                    "reasoning": proposal.reasoning,
                    "inferred_by": "batch_relationship_inference_job"
                }
            })

        if not relationship_data:
            logger.warning("No valid relationships to create (all below confidence threshold)")
            return []

        # Upsert to avoid duplicates
        response = supabase.table("substrate_relationships").upsert(
            relationship_data,
            on_conflict="from_block_id,to_block_id,relationship_type"
        ).execute()

        logger.info(
            f"Created {len(response.data or [])} relationships "
            f"(accepted: {len([r for r in relationship_data if r['state'] == 'ACCEPTED'])}, "
            f"proposed: {len([r for r in relationship_data if r['state'] == 'PROPOSED'])})"
        )

        return response.data or []

    except Exception as exc:
        logger.error(f"Failed to create relationships batch: {exc}")
        return []


async def batch_infer_for_workspace(
    workspace_id: str,
    batch_size: int = 10,
    dry_run: bool = False
) -> dict:
    """
    Infer relationships for all baskets in a workspace.

    Args:
        workspace_id: Workspace UUID
        batch_size: Number of blocks to process concurrently per basket
        dry_run: If True, only log proposals without creating relationships

    Returns:
        Aggregated statistics dict
    """
    logger.info(f"Starting batch relationship inference for workspace {workspace_id}")

    # Get all baskets in workspace
    baskets_response = supabase.table("baskets").select("id, name").eq(
        "workspace_id", workspace_id
    ).execute()

    basket_ids = [basket["id"] for basket in baskets_response.data]

    if not basket_ids:
        logger.info(f"No baskets found in workspace {workspace_id}")
        return {
            "baskets_processed": 0,
            "blocks_processed": 0,
            "proposals_generated": 0,
            "relationships_created": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "errors": 0
        }

    logger.info(f"Processing {len(basket_ids)} baskets")

    total_stats = {
        "baskets_processed": 0,
        "blocks_processed": 0,
        "proposals_generated": 0,
        "relationships_created": 0,
        "high_confidence": 0,
        "medium_confidence": 0,
        "errors": 0
    }

    # Process each basket
    for basket_id in basket_ids:
        logger.info(f"Processing basket {basket_id}")
        try:
            basket_stats = await batch_infer_relationships(
                basket_id=basket_id,
                batch_size=batch_size,
                dry_run=dry_run
            )

            total_stats["baskets_processed"] += 1
            total_stats["blocks_processed"] += basket_stats["blocks_processed"]
            total_stats["proposals_generated"] += basket_stats["proposals_generated"]
            total_stats["relationships_created"] += basket_stats["relationships_created"]
            total_stats["high_confidence"] += basket_stats["high_confidence"]
            total_stats["medium_confidence"] += basket_stats["medium_confidence"]
            total_stats["errors"] += basket_stats["errors"]

        except Exception as exc:
            logger.error(f"Failed to process basket {basket_id}: {exc}")
            total_stats["errors"] += 1
            continue

    logger.info(f"Workspace inference complete: {total_stats}")
    return total_stats


async def main():
    """CLI entry point for batch relationship inference."""
    parser = argparse.ArgumentParser(description="Batch infer semantic relationships")
    parser.add_argument("--workspace-id", type=str, help="Workspace UUID (process all baskets)")
    parser.add_argument("--basket-id", type=str, help="Basket UUID (process single basket)")
    parser.add_argument("--batch-size", type=int, default=10, help="Concurrent blocks per batch")
    parser.add_argument("--dry-run", action="store_true", help="Log proposals without creating relationships")

    args = parser.parse_args()

    if not args.workspace_id and not args.basket_id:
        print("Error: Must specify either --workspace-id or --basket-id")
        return

    if args.workspace_id:
        stats = await batch_infer_for_workspace(
            workspace_id=args.workspace_id,
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )
    else:
        stats = await batch_infer_relationships(
            basket_id=args.basket_id,
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )

    print("\n" + "="*60)
    print("BATCH RELATIONSHIP INFERENCE COMPLETE")
    print("="*60)
    for key, value in stats.items():
        print(f"{key:30s}: {value}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
