-- Migration: Add structured ingredients support to blocks table
-- Canon v1.4.0 - Blocks as Data Ingredients
-- Created: 2025-09-03

BEGIN;

-- Add structured metadata columns to blocks table
ALTER TABLE blocks 
ADD COLUMN IF NOT EXISTS extraction_method text DEFAULT 'legacy_text_chunks',
ADD COLUMN IF NOT EXISTS provenance_validated boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS ingredient_version text DEFAULT '1.0';

-- Create index for efficient querying of extraction methods
CREATE INDEX IF NOT EXISTS idx_blocks_extraction_method ON blocks(extraction_method);
CREATE INDEX IF NOT EXISTS idx_blocks_provenance_validated ON blocks(provenance_validated);

-- Update metadata JSONB to support structured ingredients
-- The metadata column already exists, we're documenting expected structure:
COMMENT ON COLUMN blocks.metadata IS 
'JSONB metadata supporting both legacy and structured ingredients.
For extraction_method=llm_structured_v2:
{
  "knowledge_ingredients": KnowledgeBlock schema with provenance,
  "extraction_method": "llm_structured_v2", 
  "provenance_validated": true,
  "transformation_hints": {...}
}
For extraction_method=legacy_text_chunks: 
{
  "keywords": [...], 
  "generated_by": "agent_name"
}';

-- Add structured ingredient validation function
CREATE OR REPLACE FUNCTION validate_structured_ingredient_metadata(metadata_json jsonb)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    -- Validate that structured ingredients have required fields
    IF metadata_json ? 'knowledge_ingredients' THEN
        -- Must have provenance validation
        IF NOT (metadata_json -> 'provenance_validated')::boolean THEN
            RETURN false;
        END IF;
        
        -- Must have extraction method marker
        IF NOT (metadata_json ? 'extraction_method') THEN
            RETURN false;
        END IF;
        
        -- Knowledge ingredients must have provenance
        IF NOT (metadata_json -> 'knowledge_ingredients' ? 'provenance') THEN
            RETURN false;
        END IF;
        
        RETURN true;
    END IF;
    
    -- Legacy blocks are always valid
    RETURN true;
END;
$$;

-- Add check constraint for structured ingredient validation
ALTER TABLE blocks 
ADD CONSTRAINT check_structured_ingredient_metadata 
CHECK (validate_structured_ingredient_metadata(metadata));

-- Create view for structured ingredient blocks
CREATE OR REPLACE VIEW structured_ingredient_blocks AS
SELECT 
    id,
    basket_id,
    title,
    semantic_type,
    confidence_score,
    extraction_method,
    provenance_validated,
    ingredient_version,
    metadata -> 'knowledge_ingredients' as ingredients,
    metadata -> 'transformation_hints' as transformation_hints,
    created_at
FROM blocks
WHERE extraction_method = 'llm_structured_v2'
  AND provenance_validated = true;

COMMENT ON VIEW structured_ingredient_blocks IS
'View of blocks created using P1SubstrateAgentV2 with structured knowledge ingredients.
Provides clean access to ingredient data for P4 synthesis operations.';

-- Create migration tracking entry (optional - depends on schema_migrations table existence)
-- INSERT INTO schema_migrations (version, description, applied_at) 
-- VALUES (
--     '20250903_structured_ingredients',
--     'Add structured ingredients support - Canon v1.4.0 Blocks as Data Ingredients',
--     NOW()
-- ) ON CONFLICT (version) DO NOTHING;

-- Grant appropriate permissions
GRANT SELECT ON structured_ingredient_blocks TO authenticated;
GRANT SELECT ON structured_ingredient_blocks TO service_role;

COMMIT;

-- Migration verification queries:
-- SELECT COUNT(*) FROM blocks WHERE extraction_method = 'llm_structured_v2';
-- SELECT COUNT(*) FROM structured_ingredient_blocks;
-- SELECT metadata -> 'knowledge_ingredients' -> 'entities' FROM structured_ingredient_blocks LIMIT 1;