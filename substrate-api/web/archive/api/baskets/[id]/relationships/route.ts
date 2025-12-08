import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getTestAwareAuth } from '@/lib/auth/testHelpers';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext {
  params: Promise<{ id: string }>;
}

type RelationshipRecord = {
  id: string;
  from_block_id: string;
  to_block_id: string;
  relationship_type: string;
  confidence_score: number | null;
  inference_method: string | null;
  state: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string | null;
};

export async function GET(
  request: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id: basketId } = await ctx.params;
    const supabase = createServerSupabaseClient();
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    // Load blocks for this basket to enforce access and gather metadata
    const { data: blockRows, error: blockError } = await supabase
      .from('blocks')
      .select('id, title, semantic_type, basket_id, workspace_id, created_at')
      .eq('basket_id', basketId)
      .eq('workspace_id', workspace.id)
      .in('state', ['ACCEPTED', 'LOCKED', 'CONSTANT'])
      .neq('status', 'archived');

    if (blockError) {
      console.error('Relationship block lookup failed:', blockError);
      return NextResponse.json({ error: 'Failed to load basket blocks' }, { status: 500 });
    }

    const blockMap = new Map<string, { id: string; title?: string | null; semantic_type?: string | null; created_at?: string }>();
    (blockRows || []).forEach((block) => {
      blockMap.set(block.id, {
        id: block.id,
        title: block.title,
        semantic_type: block.semantic_type,
        created_at: block.created_at,
      });
    });

    const blockIds = Array.from(blockMap.keys());
    if (blockIds.length === 0) {
      return NextResponse.json([], { status: 200 });
    }

    const selectColumns = 'id, from_block_id, to_block_id, relationship_type, confidence_score, inference_method, state, metadata, created_at, updated_at';

    const [outbound, inbound] = await Promise.all([
      supabase
        .from('substrate_relationships')
        .select(selectColumns)
        .in('from_block_id', blockIds),
      supabase
        .from('substrate_relationships')
        .select(selectColumns)
        .in('to_block_id', blockIds),
    ]);

    if (outbound.error || inbound.error) {
      console.error('Relationship query failed:', outbound.error || inbound.error);
      return NextResponse.json({ error: 'Failed to fetch relationships' }, { status: 500 });
    }

    const relationshipMap = new Map<string, RelationshipRecord>();
    [...(outbound.data || []), ...(inbound.data || [])].forEach((rel) => {
      if (!rel) return;
      // Ensure both ends belong to this basket
      if (!blockMap.has(rel.from_block_id) || !blockMap.has(rel.to_block_id)) return;
      relationshipMap.set(rel.id, rel as RelationshipRecord);
    });

    const relationships = Array.from(relationshipMap.values())
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .map((rel) => ({
        id: rel.id,
        relationship_type: rel.relationship_type,
        confidence_score: rel.confidence_score,
        inference_method: rel.inference_method,
        state: rel.state,
        metadata: rel.metadata,
        created_at: rel.created_at,
        updated_at: rel.updated_at,
        from_block: blockMap.get(rel.from_block_id),
        to_block: blockMap.get(rel.to_block_id),
      }));

    return NextResponse.json(relationships, { status: 200 });

  } catch (error) {
    console.error('Relationships fetch error:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}
