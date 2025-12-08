import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getTestAwareAuth } from '@/lib/auth/testHelpers';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext {
  params: Promise<{ id: string }>;
}

/**
 * Building Blocks API - Substrate Management
 *
 * Canon-compliant substrate retrieval with context-aware quality metrics.
 *
 * Returns:
 * - Blocks with usage tracking (usefulness_score, times_referenced)
 * - Blocks with staleness detection (staleness_days from last_validated_at)
 * - Context items with semantic meaning
 * - Stats for filtering (anchored, stale, unused counts)
 *
 * NOTE: Raw dumps are managed via the timeline uploads tab (not returned here)
 */

interface KnowledgeSummary {
  has_summary: boolean;
  goals: number;
  constraints: number;
  metrics: number;
  entities: number;
  insights: number;
  actions: number;
  facts: number;
}

interface BlockWithMetrics {
  id: string;
  title: string | null;
  content: string | null;
  semantic_type: string | null;
  confidence_score: number | null;
  created_at: string;
  updated_at?: string | null;
  status: string | null;
  state: string | null;
  scope: string | null;
  version: number | null;
  anchor_role: string | null;
  anchor_status: string | null;
  anchor_confidence: number | null;
  metadata?: Record<string, any> | null;
  raw_dump_id?: string | null;

  usefulness_score: number;
  times_referenced: number;
  staleness_days: number | null;
  last_validated_at: string | null;
  knowledge_summary: KnowledgeSummary;
  needs_enrichment: boolean;
}

// V3.0: Removed ContextItemWithMetrics - context items merged into blocks

interface BuildingBlocksStats {
  total_blocks: number;
  knowledge_blocks: number;  // V3.0: fact, metric, entity
  meaning_blocks: number;     // V3.0: intent, objective, rationale, etc.
}

export async function GET(
  request: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id: basketId } = await ctx.params;
    const supabase = createServerSupabaseClient();
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest
      ? { id: '00000000-0000-0000-0000-000000000002' }
      : await ensureWorkspaceForUser(userId, supabase);

    // Canon v2.1: Fetch substrate types with context-aware metrics
    // Fetch blocks first (without block_usage join to avoid RLS issues)
    const { data: blocksData, error: blocksError } = await supabase
      .from('blocks')
      .select(`
        id,
        semantic_type,
        content,
        confidence_score,
        title,
        created_at,
        updated_at,
        metadata,
        status,
        state,
        scope,
        version,
        anchor_role,
        anchor_status,
        anchor_confidence,
        raw_dump_id,
        last_validated_at
      `)
      .eq('basket_id', basketId)
      .eq('workspace_id', workspace.id)
      .neq('status', 'archived')
      .order('created_at', { ascending: false })
      .limit(200);

    if (blocksError) {
      console.error('Blocks query error:', blocksError);
      return NextResponse.json({ error: 'Failed to fetch blocks' }, { status: 500 });
    }

    // Fetch block usage separately and join in application code
    // This avoids RLS issues with nested selects
    const blockIds = (blocksData ?? []).map(b => b.id);
    const { data: usageData } = await supabase
      .from('block_usage')
      .select('block_id, times_referenced, usefulness_score, last_used_at')
      .in('block_id', blockIds);

    // Create usage lookup map
    const usageMap = new Map(
      (usageData ?? []).map(u => [u.block_id, u])
    );

    // V3.0: No separate context_items query - all semantic types in blocks table

    // Transform blocks with quality metrics
    const blocks: BlockWithMetrics[] = (blocksData ?? []).map(block => {
      const usage = usageMap.get(block.id);

      // Calculate staleness_days from last_validated_at
      let staleness_days: number | null = null;
      if (block.last_validated_at) {
        const lastValidated = new Date(block.last_validated_at);
        const now = new Date();
        const diffMs = now.getTime() - lastValidated.getTime();
        staleness_days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      }

      const state = block.state ?? block.status ?? null;
      const scope = block.scope ?? null;
      const version = typeof block.version === 'number' ? block.version : null;

      const knowledge = (block.metadata?.knowledge_ingredients ?? {}) as Record<string, any>;
      const knowledgeSummary: KnowledgeSummary = {
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

      return {
        id: block.id,
        title: block.title || null,
        content: block.content || null,
        semantic_type: block.semantic_type || null,
        confidence_score: block.confidence_score ?? null,
        created_at: block.created_at,
        updated_at: block.updated_at ?? null,
        status: block.status ?? null,
        state,
        scope,
        version,
        anchor_role: block.anchor_role ?? null,
        anchor_status: block.anchor_status ?? null,
        anchor_confidence: block.anchor_confidence ?? null,
        metadata: block.metadata || null,
        raw_dump_id: block.raw_dump_id || null,

        // Context-aware quality metrics
        usefulness_score: usage?.usefulness_score ?? 0.0,
        times_referenced: usage?.times_referenced ?? 0,
        staleness_days,
        last_validated_at: block.last_validated_at,
        knowledge_summary: knowledgeSummary,
        needs_enrichment: needsEnrichment,
      };
    });

    // V3.0: Calculate stats for Knowledge vs Meaning grouping
    const knowledgeTypes = ['fact', 'metric', 'entity'];
    const meaningTypes = ['intent', 'objective', 'rationale', 'principle', 'assumption', 'context', 'constraint'];

    const knowledge_blocks = blocks.filter(b => b.semantic_type && knowledgeTypes.includes(b.semantic_type)).length;
    const meaning_blocks = blocks.filter(b => b.semantic_type && meaningTypes.includes(b.semantic_type)).length;

    const stats: BuildingBlocksStats = {
      total_blocks: blocks.length,
      knowledge_blocks,
      meaning_blocks,
    };

    return NextResponse.json({
      blocks,
      stats,
    }, { status: 200 });

  } catch (error) {
    console.error('Building blocks fetch error:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
