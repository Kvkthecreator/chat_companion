#!/usr/bin/env python3
"""
Apply Universal Work Orchestration Migration (Canon v2.1)
Extends agent_processing_queue with universal work orchestration capabilities.
"""

import sys
import os
import logging
from pathlib import Path

# Add API src to path so we can import supabase client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "src"))

from app.utils.supabase_client import supabase_admin_client as supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The migration SQL from our migration file
MIGRATION_SQL = """
-- YARNNN Canon v2.1: Universal Work Orchestration Extension
-- Extends agent_processing_queue to support all async work types per Canon v2.1

-- Add universal work orchestration columns to existing table
ALTER TABLE agent_processing_queue 
ADD COLUMN IF NOT EXISTS processing_stage text,
ADD COLUMN IF NOT EXISTS work_payload jsonb DEFAULT '{}',
ADD COLUMN IF NOT EXISTS work_result jsonb DEFAULT '{}',
ADD COLUMN IF NOT EXISTS cascade_metadata jsonb DEFAULT '{}',
ADD COLUMN IF NOT EXISTS parent_work_id uuid,
ADD COLUMN IF NOT EXISTS user_id uuid,
ADD COLUMN IF NOT EXISTS work_id text;

-- Add work_type column to support universal work orchestration
ALTER TABLE agent_processing_queue
ADD COLUMN IF NOT EXISTS work_type text DEFAULT 'P1_SUBSTRATE';

-- Update the processing_state enum to align with Canon v2.1
ALTER TYPE processing_state ADD VALUE IF NOT EXISTS 'cascading';

-- Update constraints to support all work types per Canon v2.1
ALTER TABLE agent_processing_queue 
DROP CONSTRAINT IF EXISTS valid_work_type;

ALTER TABLE agent_processing_queue 
ADD CONSTRAINT valid_work_type_v21 CHECK (work_type IN (
    'P0_CAPTURE', 'P1_SUBSTRATE', 'P2_GRAPH', 'P3_REFLECTION', 'P4_COMPOSE',
    'MANUAL_EDIT', 'PROPOSAL_REVIEW', 'TIMELINE_RESTORE'
));

-- Update existing rows to have work_type = 'P1_SUBSTRATE' (current default)
UPDATE agent_processing_queue 
SET work_type = 'P1_SUBSTRATE' 
WHERE work_type IS NULL;
"""

INDEXES_SQL = """
-- Performance indexes for universal work orchestration
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_queue_work_id ON agent_processing_queue (work_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_queue_user_workspace ON agent_processing_queue (user_id, workspace_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_queue_cascade ON agent_processing_queue USING gin (cascade_metadata);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_queue_work_type ON agent_processing_queue (work_type, processing_state);
"""

COMMENTS_SQL = """
-- Add canon compliance comments
COMMENT ON COLUMN agent_processing_queue.work_type IS 'Canon v2.1: Type of work being processed (P0-P4, manual operations)';
COMMENT ON COLUMN agent_processing_queue.processing_stage IS 'Canon v2.1: Stage-specific status within work type';
COMMENT ON COLUMN agent_processing_queue.work_payload IS 'Canon v2.1: Input data for work execution';
COMMENT ON COLUMN agent_processing_queue.work_result IS 'Canon v2.1: Output data from completed work';
COMMENT ON COLUMN agent_processing_queue.cascade_metadata IS 'Canon v2.1: Metadata for P1→P2→P3 cascade flows';
COMMENT ON COLUMN agent_processing_queue.parent_work_id IS 'Canon v2.1: Parent work entry for cascade flows';
COMMENT ON COLUMN agent_processing_queue.user_id IS 'Canon v2.1: User who initiated this work';
COMMENT ON COLUMN agent_processing_queue.work_id IS 'Canon v2.1: Optional external work identifier';
"""

def apply_migration():
    """Apply the universal work orchestration migration."""
    if not supabase:
        logger.error("Supabase admin client not initialized. Check SUPABASE_SERVICE_ROLE_KEY env var.")
        return False
        
    try:
        logger.info("Starting Universal Work Orchestration migration (Canon v2.1)")
        
        # Apply core migration SQL
        logger.info("Applying core schema changes...")
        supabase.rpc('sql', {'query': MIGRATION_SQL}).execute()
        logger.info("✅ Core schema changes applied")
        
        # Apply indexes (non-blocking with CONCURRENTLY)
        logger.info("Creating performance indexes...")
        supabase.rpc('sql', {'query': INDEXES_SQL}).execute()
        logger.info("✅ Performance indexes created")
        
        # Apply comments
        logger.info("Adding documentation comments...")
        supabase.rpc('sql', {'query': COMMENTS_SQL}).execute()
        logger.info("✅ Documentation comments added")
        
        # Verify migration
        logger.info("Verifying migration...")
        result = supabase.rpc('sql', {
            'query': """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'agent_processing_queue' 
            AND column_name IN ('work_type', 'processing_stage', 'work_payload', 'cascade_metadata')
            ORDER BY column_name;
            """
        }).execute()
        
        if result.data and len(result.data) >= 4:
            logger.info("✅ Migration verification successful")
            logger.info("New columns found:")
            for row in result.data:
                logger.info(f"  - {row['column_name']}: {row['data_type']}")
            return True
        else:
            logger.error("❌ Migration verification failed - expected columns not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = apply_migration()
    if success:
        logger.info("🎉 Universal Work Orchestration migration completed successfully!")
        logger.info("agent_processing_queue now supports Canon v2.1 universal work orchestration")
    else:
        logger.error("💥 Migration failed. Check logs above for details.")
        sys.exit(1)