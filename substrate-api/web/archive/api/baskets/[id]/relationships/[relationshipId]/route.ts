import { NextRequest, NextResponse } from "next/server";
import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import { checkBasketAccess } from "@/lib/baskets/access";

interface RouteParams {
  id: string;
  relationshipId: string;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<RouteParams> }
) {
  try {
    const { id: basketId, relationshipId } = await params;
    const supabase = createRouteHandlerClient({ cookies });

    await checkBasketAccess(supabase, basketId);

    const { data: relationship, error: relationshipError } = await supabase
      .from('substrate_relationships')
      .select('id, from_block_id, to_block_id, relationship_type, confidence_score, inference_method, state, metadata, created_at, updated_at')
      .eq('id', relationshipId)
      .maybeSingle();

    if (relationshipError || !relationship) {
      return NextResponse.json({ error: 'Relationship not found' }, { status: 404 });
    }

    const blockIds = [relationship.from_block_id, relationship.to_block_id].filter(Boolean);
    if (blockIds.length === 0) {
      return NextResponse.json({ error: 'Relationship not found' }, { status: 404 });
    }
    const { data: blocks, error: blockError } = await supabase
      .from('blocks')
      .select('id, basket_id, workspace_id, title, semantic_type, created_at')
      .in('id', blockIds);

    if (blockError) {
      console.error('Relationship block fetch failed:', blockError);
      return NextResponse.json({ error: 'Failed to load related blocks' }, { status: 500 });
    }

    const blockMap = new Map<string, { id: string; title?: string | null; semantic_type?: string | null; created_at?: string }>();
    (blocks || []).forEach((block) => {
      if (block.basket_id === basketId) {
        blockMap.set(block.id, {
          id: block.id,
          title: block.title,
          semantic_type: block.semantic_type,
          created_at: block.created_at,
        });
      }
    });

    const fromBlock = relationship.from_block_id ? blockMap.get(relationship.from_block_id) : undefined;
    const toBlock = relationship.to_block_id ? blockMap.get(relationship.to_block_id) : undefined;

    if (!fromBlock || !toBlock) {
      return NextResponse.json({ error: 'Relationship does not belong to this basket' }, { status: 404 });
    }

    const result = {
      id: relationship.id,
      relationship_type: relationship.relationship_type,
      confidence_score: relationship.confidence_score,
      inference_method: relationship.inference_method,
      state: relationship.state,
      metadata: relationship.metadata,
      created_at: relationship.created_at,
      updated_at: relationship.updated_at,
      from_block: fromBlock,
      to_block: toBlock,
    };

    return NextResponse.json(result, { status: 200 });
  } catch (error: any) {
    console.error('Failed to fetch relationship:', error);
    return NextResponse.json(
      { error: error?.message || 'Failed to fetch relationship' },
      { status: error?.status || 500 }
    );
  }
}
