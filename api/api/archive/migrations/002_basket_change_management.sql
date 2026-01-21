-- Basket Change Management System Tables
-- For Manager Agent system with idempotency support

-- Idempotency tracking table
CREATE TABLE IF NOT EXISTS idempotency_keys (
    request_id TEXT PRIMARY KEY,
    delta_id TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Basket deltas table (stores BasketDelta payloads)
CREATE TABLE IF NOT EXISTS basket_deltas (
    delta_id TEXT PRIMARY KEY,
    basket_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NULL
);

-- Basket events table (for realtime notifications via Supabase)
CREATE TABLE IF NOT EXISTS basket_events (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_delta_id ON idempotency_keys(delta_id);
CREATE INDEX IF NOT EXISTS idx_basket_deltas_basket_id ON basket_deltas(basket_id);
CREATE INDEX IF NOT EXISTS idx_basket_deltas_created_at ON basket_deltas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_basket_deltas_applied_at ON basket_deltas(applied_at);
CREATE INDEX IF NOT EXISTS idx_basket_events_event_type ON basket_events(event_type);
CREATE INDEX IF NOT EXISTS idx_basket_events_created_at ON basket_events(created_at DESC);

-- Partial index for unapplied deltas
CREATE INDEX IF NOT EXISTS idx_basket_deltas_unapplied ON basket_deltas(basket_id, created_at DESC) 
WHERE applied_at IS NULL;

COMMENT ON TABLE idempotency_keys IS 'Tracks processed requests to prevent duplicate operations';
COMMENT ON TABLE basket_deltas IS 'Stores BasketDelta payloads from Manager Agent analysis';  
COMMENT ON TABLE basket_events IS 'Events for Supabase Realtime notifications to frontend';

COMMENT ON COLUMN basket_deltas.payload IS 'Complete BasketDelta JSON including changes, explanations, confidence';
COMMENT ON COLUMN basket_deltas.applied_at IS 'When delta was successfully applied to basket (NULL = proposed only)';
COMMENT ON COLUMN basket_events.event_type IS 'Event types: basket.delta.proposed, basket.delta.applied, etc.';