-- Core tables for the backend application
-- These are the minimum required tables based on the service analysis

-- Workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    owner_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Baskets table  
CREATE TABLE IF NOT EXISTS baskets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    basket_id UUID NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content_raw TEXT,
    document_type TEXT DEFAULT 'general',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Blocks table
CREATE TABLE IF NOT EXISTS blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    basket_id UUID NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    semantic_type TEXT,
    content TEXT,
    state TEXT DEFAULT 'active',
    parent_block_id UUID REFERENCES blocks(id) ON DELETE SET NULL,
    canonical_value TEXT,
    scope TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Context items table
CREATE TABLE IF NOT EXISTS context_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    basket_id UUID NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    content TEXT,
    scope TEXT DEFAULT 'project',
    status TEXT DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Raw dumps table
CREATE TABLE IF NOT EXISTS raw_dumps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    basket_id UUID NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    body_md TEXT,
    context_blocks TEXT[],
    source TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    basket_id UUID NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    payload JSONB DEFAULT '{}',
    ts TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Block change queue table
CREATE TABLE IF NOT EXISTS block_change_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_id UUID NOT NULL REFERENCES blocks(id) ON DELETE CASCADE,
    change_type TEXT NOT NULL,
    change_data JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_baskets_workspace_id ON baskets(workspace_id);
CREATE INDEX IF NOT EXISTS idx_documents_basket_id ON documents(basket_id);
CREATE INDEX IF NOT EXISTS idx_documents_workspace_id ON documents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_blocks_basket_id ON blocks(basket_id);
CREATE INDEX IF NOT EXISTS idx_blocks_workspace_id ON blocks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_blocks_state ON blocks(state);
CREATE INDEX IF NOT EXISTS idx_context_items_basket_id ON context_items(basket_id);
CREATE INDEX IF NOT EXISTS idx_context_items_status ON context_items(status);
CREATE INDEX IF NOT EXISTS idx_raw_dumps_basket_id ON raw_dumps(basket_id);
CREATE INDEX IF NOT EXISTS idx_raw_dumps_workspace_id ON raw_dumps(workspace_id);
CREATE INDEX IF NOT EXISTS idx_events_basket_id ON events(basket_id);
CREATE INDEX IF NOT EXISTS idx_events_workspace_id ON events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_block_change_queue_block_id ON block_change_queue(block_id);
CREATE INDEX IF NOT EXISTS idx_block_change_queue_status ON block_change_queue(status);

-- Update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON workspaces FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_baskets_updated_at BEFORE UPDATE ON baskets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_blocks_updated_at BEFORE UPDATE ON blocks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_context_items_updated_at BEFORE UPDATE ON context_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_raw_dumps_updated_at BEFORE UPDATE ON raw_dumps FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_block_change_queue_updated_at BEFORE UPDATE ON block_change_queue FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();