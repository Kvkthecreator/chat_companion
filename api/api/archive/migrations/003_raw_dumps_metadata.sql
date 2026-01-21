-- ==========================================
-- RAW_DUMPS: metadata + idempotency (fits your schema)
-- ==========================================
ALTER TABLE public.raw_dumps
  ADD COLUMN IF NOT EXISTS source_meta JSONB DEFAULT '{}'::jsonb,  -- PDF/source metadata
  ADD COLUMN IF NOT EXISTS ingest_trace_id TEXT;                    -- request-level dedupe

-- Fast lookups
CREATE INDEX IF NOT EXISTS idx_raw_dumps_basket
  ON public.raw_dumps (basket_id);

CREATE INDEX IF NOT EXISTS idx_raw_dumps_trace
  ON public.raw_dumps (ingest_trace_id);

-- Partial UNIQUE: dedupe replays by (basket_id, ingest_trace_id)
CREATE UNIQUE INDEX IF NOT EXISTS ux_raw_dumps_basket_trace
  ON public.raw_dumps (basket_id, ingest_trace_id)
  WHERE ingest_trace_id IS NOT NULL;

-- Optional: for audits/debug on metadata
CREATE INDEX IF NOT EXISTS idx_raw_dumps_source_meta_gin
  ON public.raw_dumps
  USING GIN (source_meta);

-- Optional: helps when validating/downloaded-from storage
CREATE INDEX IF NOT EXISTS idx_raw_dumps_file_url
  ON public.raw_dumps (file_url);

-- ==========================================
-- BLOCKS/DOCUMENTS/CONTEXT_ITEMS: common filters
-- (only creates if they don't already exist)
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_blocks_basket
  ON public.blocks (basket_id);

CREATE INDEX IF NOT EXISTS idx_blocks_raw_dump
  ON public.blocks (raw_dump_id);

CREATE INDEX IF NOT EXISTS idx_documents_basket
  ON public.documents (basket_id);

CREATE INDEX IF NOT EXISTS idx_context_items_basket
  ON public.context_items (basket_id);

-- ==========================================
-- EVENTS: common query pattern (by basket/kind/time)
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_events_basket_kind_ts
  ON public.events (basket_id, kind, ts);

-- Add comments for documentation
COMMENT ON COLUMN public.raw_dumps.source_meta IS 'JSON metadata about source files: [{url, mime, size, parsed, parse_error?, chars_extracted?}]';
COMMENT ON COLUMN public.raw_dumps.ingest_trace_id IS 'Request trace ID for idempotency and debugging';