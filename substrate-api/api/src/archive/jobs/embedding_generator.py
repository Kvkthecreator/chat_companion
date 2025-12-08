"""
V3.1 Embedding Generation Background Job

Generates vector embeddings for ACCEPTED blocks asynchronously to avoid
blocking P1 agent operations. This job is triggered after governance approval.

Design:
- Runs as background worker (non-blocking)
- Processes blocks in batches for efficiency
- Idempotent (skips blocks that already have embeddings)
- Graceful error handling (logs errors, continues processing)

Usage:
    # Trigger for single block (after governance approval)
    await queue_embedding_generation(supabase, block_id)

    # Batch processing (backfill)
    python -m api.src.jobs.embedding_generator --workspace-id <uuid>

Reference: docs/V3.1_IMPLEMENTATION_SEQUENCING.md Week 1
"""

import asyncio
import logging
import sys
from typing import Optional, List
from uuid import UUID

from infra.utils.supabase_client import supabase_admin_client as supabase
from infra.substrate.services.semantic_primitives import generate_and_store_embedding

logger = logging.getLogger("uvicorn.error")

# ============================================================================
# Configuration
# ============================================================================

BATCH_SIZE = 50  # Process 50 blocks at a time
RATE_LIMIT_DELAY = 0.5  # 500ms between blocks (OpenAI rate limiting)

# ============================================================================
# Queue Management (Simple Implementation)
# ============================================================================

async def queue_embedding_generation(block_id: str) -> bool:
    """
    Queue a block for embedding generation.

    This is a simple implementation that directly generates the embedding.
    In production, this could be replaced with a proper job queue (Celery, BullMQ).

    Args:
        block_id: Block to generate embedding for

    Returns:
        True if queued/generated successfully

    Usage (P1 agent after governance approval):
        if proposal_approved:
            await queue_embedding_generation(new_block_id)
    """
    try:
        # Direct generation (async, non-blocking)
        success = await generate_and_store_embedding(supabase, block_id)
        if success:
            logger.info(f"Generated embedding for block {block_id}")
        else:
            logger.warning(f"Failed to generate embedding for block {block_id}")
        return success
    except Exception as exc:
        logger.error(f"queue_embedding_generation failed for {block_id}: {exc}")
        return False


# ============================================================================
# Batch Processing (Backfill / Catch-up)
# ============================================================================

async def process_basket_embeddings(basket_id: str) -> dict:
    """
    Generate embeddings for all ACCEPTED blocks in a basket that don't have them.

    Args:
        basket_id: Basket to process

    Returns:
        {
            'basket_id': str,
            'blocks_processed': int,
            'blocks_succeeded': int,
            'blocks_failed': int
        }
    """
    try:
        # Fetch ACCEPTED blocks without embeddings
        response = supabase.table('blocks').select('id').eq(
            'basket_id', str(basket_id)
        ).in_(
            'state', ['ACCEPTED', 'LOCKED', 'CONSTANT']
        ).is_(
            'embedding', 'null'
        ).execute()

        if not response.data:
            logger.info(f"No blocks need embeddings in basket {basket_id}")
            return {
                'basket_id': basket_id,
                'blocks_processed': 0,
                'blocks_succeeded': 0,
                'blocks_failed': 0
            }

        block_ids = [row['id'] for row in response.data]
        logger.info(f"Processing {len(block_ids)} blocks in basket {basket_id}")

        succeeded = 0
        failed = 0

        # Process in batches with rate limiting
        for block_id in block_ids:
            try:
                success = await generate_and_store_embedding(supabase, block_id)
                if success:
                    succeeded += 1
                else:
                    failed += 1

                # Rate limiting (avoid OpenAI quota errors)
                await asyncio.sleep(RATE_LIMIT_DELAY)

            except Exception as exc:
                logger.error(f"Failed to process block {block_id}: {exc}")
                failed += 1

        logger.info(
            f"Basket {basket_id} complete: {succeeded} succeeded, {failed} failed"
        )

        return {
            'basket_id': basket_id,
            'blocks_processed': len(block_ids),
            'blocks_succeeded': succeeded,
            'blocks_failed': failed
        }

    except Exception as exc:
        logger.error(f"process_basket_embeddings failed for {basket_id}: {exc}")
        return {
            'basket_id': basket_id,
            'blocks_processed': 0,
            'blocks_succeeded': 0,
            'blocks_failed': 0,
            'error': str(exc)
        }


async def process_workspace_embeddings(workspace_id: str) -> dict:
    """
    Generate embeddings for all ACCEPTED blocks in a workspace.

    Args:
        workspace_id: Workspace to process

    Returns:
        {
            'workspace_id': str,
            'baskets_processed': int,
            'total_blocks_succeeded': int,
            'total_blocks_failed': int,
            'basket_results': [...]
        }
    """
    try:
        # Fetch all baskets in workspace
        response = supabase.table('baskets').select('id').eq(
            'workspace_id', str(workspace_id)
        ).execute()

        if not response.data:
            logger.warning(f"No baskets found in workspace {workspace_id}")
            return {
                'workspace_id': workspace_id,
                'baskets_processed': 0,
                'total_blocks_succeeded': 0,
                'total_blocks_failed': 0,
                'basket_results': []
            }

        basket_ids = [row['id'] for row in response.data]
        logger.info(f"Processing {len(basket_ids)} baskets in workspace {workspace_id}")

        basket_results = []
        total_succeeded = 0
        total_failed = 0

        for basket_id in basket_ids:
            result = await process_basket_embeddings(basket_id)
            basket_results.append(result)
            total_succeeded += result['blocks_succeeded']
            total_failed += result['blocks_failed']

        logger.info(
            f"Workspace {workspace_id} complete: {total_succeeded} succeeded, {total_failed} failed"
        )

        return {
            'workspace_id': workspace_id,
            'baskets_processed': len(basket_ids),
            'total_blocks_succeeded': total_succeeded,
            'total_blocks_failed': total_failed,
            'basket_results': basket_results
        }

    except Exception as exc:
        logger.error(f"process_workspace_embeddings failed for {workspace_id}: {exc}")
        return {
            'workspace_id': workspace_id,
            'baskets_processed': 0,
            'total_blocks_succeeded': 0,
            'total_blocks_failed': 0,
            'error': str(exc)
        }


# ============================================================================
# CLI Entry Point (for backfill script)
# ============================================================================

async def main():
    """
    CLI entry point for embedding generation job.

    Usage:
        # Process specific workspace
        python -m api.src.jobs.embedding_generator --workspace-id <uuid>

        # Process specific basket
        python -m api.src.jobs.embedding_generator --basket-id <uuid>
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='V3.1 Embedding Generation Background Job'
    )
    parser.add_argument(
        '--workspace-id',
        type=str,
        help='Process all baskets in workspace'
    )
    parser.add_argument(
        '--basket-id',
        type=str,
        help='Process specific basket'
    )

    args = parser.parse_args()

    if not args.workspace_id and not args.basket_id:
        parser.error("Must specify either --workspace-id or --basket-id")

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    try:
        if args.workspace_id:
            logger.info(f"Starting workspace embedding generation: {args.workspace_id}")
            result = await process_workspace_embeddings(args.workspace_id)
            print("\n" + "="*60)
            print("WORKSPACE EMBEDDING GENERATION COMPLETE")
            print("="*60)
            print(f"Workspace ID: {result['workspace_id']}")
            print(f"Baskets Processed: {result['baskets_processed']}")
            print(f"Total Blocks Succeeded: {result['total_blocks_succeeded']}")
            print(f"Total Blocks Failed: {result['total_blocks_failed']}")
            print("="*60 + "\n")

            if result['total_blocks_failed'] > 0:
                sys.exit(1)

        elif args.basket_id:
            logger.info(f"Starting basket embedding generation: {args.basket_id}")
            result = await process_basket_embeddings(args.basket_id)
            print("\n" + "="*60)
            print("BASKET EMBEDDING GENERATION COMPLETE")
            print("="*60)
            print(f"Basket ID: {result['basket_id']}")
            print(f"Blocks Processed: {result['blocks_processed']}")
            print(f"Blocks Succeeded: {result['blocks_succeeded']}")
            print(f"Blocks Failed: {result['blocks_failed']}")
            print("="*60 + "\n")

            if result['blocks_failed'] > 0:
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Embedding generation interrupted by user")
        sys.exit(0)
    except Exception as exc:
        logger.error(f"Embedding generation failed: {exc}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
