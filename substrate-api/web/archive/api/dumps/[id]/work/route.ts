import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getTestAwareAuth } from '@/lib/auth/testHelpers';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext {
  params: Promise<{ id: string }>;
}

/**
 * GET /api/dumps/[id]/work - Get work items associated with a dump
 * 
 * Returns all work entries in the universal work orchestration system
 * that are related to processing this dump through the P0→P1→P2→P3 pipeline.
 * 
 * Canon v2.1 Compliant:
 * - Uses universal work tracker (agent_processing_queue)
 * - Respects workspace isolation
 * - Provides real-time pipeline visibility
 */
export async function GET(
  request: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id: dumpId } = await ctx.params;
    const supabase = createServerSupabaseClient();
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    // First verify the dump exists and user has access
    const { data: dump, error: dumpError } = await supabase
      .from('raw_dumps')
      .select('id, workspace_id, basket_id')
      .eq('id', dumpId)
      .eq('workspace_id', workspace.id)
      .maybeSingle();

    if (dumpError) {
      console.error('Error fetching dump:', dumpError);
      return NextResponse.json({ error: 'Failed to fetch dump' }, { status: 500 });
    }

    if (!dump) {
      return NextResponse.json({ error: 'Dump not found' }, { status: 404 });
    }

    // Query work items related to this dump
    // Work items are linked via dump_id in the work_payload or by basket_id context
    const { data: workItems, error: workError } = await supabase
      .from('agent_processing_queue')
      .select(`
        work_id,
        work_type,
        processing_state,
        created_at,
        work_payload,
        basket_id,
        dump_id
      `)
      .eq('workspace_id', workspace.id)
      .or(`dump_id.eq.${dumpId},basket_id.eq.${dump.basket_id}`)
      .order('created_at', { ascending: true });

    if (workError) {
      console.error('Error fetching work items:', workError);
      return NextResponse.json({ error: 'Failed to fetch work items' }, { status: 500 });
    }

    // Filter work items that are actually related to this dump
    const dumpRelatedWork = (workItems || []).filter(work => {
      // Direct dump_id match
      if (work.dump_id === dumpId) return true;
      
      // Check work_payload for dump reference
      if (work.work_payload) {
        const payload = work.work_payload;
        if (payload.dump_id === dumpId) return true;
        if (payload.source_dump_id === dumpId) return true;
        if (payload.raw_dump_id === dumpId) return true;
      }
      
      // For P1+ work in the same basket, check if it's part of the same processing flow
      if (work.basket_id === dump.basket_id && 
          ['P1_SUBSTRATE', 'P2_GRAPH', 'P3_REFLECTION'].includes(work.work_type)) {
        // This is a heuristic - in a more advanced system, we'd track the work chain explicitly
        return true;
      }
      
      return false;
    });

    // Format response for frontend
    const workMappings = dumpRelatedWork.map(work => ({
      dump_id: dumpId,
      work_id: work.work_id,
      work_type: work.work_type,
      status: work.processing_state,
      created_at: work.created_at
    }));

    return NextResponse.json({
      dump_id: dumpId,
      basket_id: dump.basket_id,
      work_mappings: workMappings,
      pipeline_stages: workMappings.map(w => w.work_type).filter(type => 
        ['P0_CAPTURE', 'P1_SUBSTRATE', 'P2_GRAPH', 'P3_REFLECTION'].includes(type)
      )
    }, { status: 200 });

  } catch (error) {
    console.error('Dump work mapping error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}