import { NextRequest } from "next/server";
import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import { checkBasketAccess } from "@/lib/baskets/access";

interface RouteParams {
  id: string;
  blockId: string;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<RouteParams> }
) {
  try {
    const { id: basketId, blockId } = await params;
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check basket access
    await checkBasketAccess(supabase, basketId);
    
    // Fetch block details
    const { data: block, error } = await supabase
      .from('blocks')
      .select(`
        id,
        basket_id,
        title,
        content,
        semantic_type,
        state,
        status,
        scope,
        version,
        anchor_role,
        anchor_status,
        anchor_confidence,
        confidence_score,
        created_at,
        updated_at,
        metadata
      `)
      .eq('id', blockId)
      .eq('basket_id', basketId)
      .single();

    if (error || !block) {
      return Response.json({ error: 'Block not found' }, { status: 404 });
    }

    const { data: usage } = await supabase
      .from('block_usage')
      .select('times_referenced, usefulness_score, last_used_at')
      .eq('block_id', blockId)
      .maybeSingle();

    const { data: referencesData } = await supabase
      .from('substrate_references')
      .select('document_id, document:documents(id,title,doc_type,updated_at)')
      .eq('substrate_type', 'block')
      .eq('substrate_id', blockId)
      .order('created_at', { ascending: false })
      .limit(10);

    const { data: revisionsData } = await supabase
      .from('block_revisions')
      .select('id, summary, diff_json, created_at, actor_id')
      .eq('block_id', blockId)
      .order('created_at', { ascending: false })
      .limit(10);

    // Format title if missing
    if (!block.title) {
      block.title = block.content ? block.content.substring(0, 50) + '...' : 'Untitled Block';
    }

    const knowledge = (block.metadata?.knowledge_ingredients ?? {}) as Record<string, any>;
    const knowledgeSummary = {
      has_summary: Boolean(knowledge?.summary),
      goals: Array.isArray(knowledge?.goals) ? knowledge.goals.length : 0,
      constraints: Array.isArray(knowledge?.constraints) ? knowledge.constraints.length : 0,
      metrics: Array.isArray(knowledge?.metrics) ? knowledge.metrics.length : 0,
      entities: Array.isArray(knowledge?.entities) ? knowledge.entities.length : 0,
      insights: Array.isArray(knowledge?.insights) ? knowledge.insights.length : 0,
      actions: Array.isArray(knowledge?.actions) ? knowledge.actions.length : 0,
      facts: Array.isArray(knowledge?.facts) ? knowledge.facts.length : 0,
    };

    const needsEnrichment =
      !knowledgeSummary.has_summary &&
      knowledgeSummary.goals === 0 &&
      knowledgeSummary.constraints === 0 &&
      knowledgeSummary.metrics === 0 &&
      knowledgeSummary.entities === 0 &&
      knowledgeSummary.insights === 0 &&
      knowledgeSummary.actions === 0 &&
      knowledgeSummary.facts === 0;

    const references = (referencesData ?? []).map((ref) => {
      const document = Array.isArray(ref.document) ? ref.document[0] : ref.document;

      return {
        document_id: ref.document_id,
        title: document?.title ?? 'Untitled document',
        doc_type: document?.doc_type ?? null,
        updated_at: document?.updated_at ?? null,
      };
    });

    const revisions = (revisionsData ?? []).map((rev) => ({
      id: rev.id,
      summary: rev.summary,
      diff: rev.diff_json,
      created_at: rev.created_at,
      actor_id: rev.actor_id,
    }));

    return Response.json({
      ...block,
      state: block.state ?? block.status ?? null,
      scope: block.scope ?? null,
      version: typeof block.version === 'number' ? block.version : null,
      anchor_role: block.anchor_role ?? null,
      anchor_status: block.anchor_status ?? null,
      anchor_confidence: block.anchor_confidence ?? null,
      times_referenced: usage?.times_referenced ?? 0,
      usefulness_score: usage?.usefulness_score ?? 0,
      last_used_at: usage?.last_used_at ?? null,
      knowledge_summary: knowledgeSummary,
      knowledge_ingredients: knowledge,
      needs_enrichment: needsEnrichment,
      provenance: knowledge?.provenance ?? null,
      references,
      revisions,
    });
  } catch (error: any) {
    console.error('Failed to fetch block:', error);
    return Response.json(
      { error: error.message || 'Failed to fetch block' },
      { status: error.status || 500 }
    );
  }
}
