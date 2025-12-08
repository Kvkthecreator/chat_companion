import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

/**
 * Upload Wizard - Extraction Status API
 * Polls P1 extraction work status for uploaded documents
 *
 * Query params:
 * - raw_dump_id: The raw_dump ID to check status for
 *
 * Returns:
 * - status: 'queued' | 'processing' | 'completed' | 'error'
 * - substrate_count: Number of substrate proposals extracted (if completed)
 */
export async function GET(
  req: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const { id: basketId } = await context.params;
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    // Validate basket access
    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basketId)
      .maybeSingle();

    if (basketError || !basket || basket.workspace_id !== workspace.id) {
      return NextResponse.json(
        { error: 'Basket not found' },
        { status: 404 }
      );
    }

    const searchParams = req.nextUrl.searchParams;
    const rawDumpId = searchParams.get('raw_dump_id');

    if (!rawDumpId) {
      return NextResponse.json(
        { error: 'raw_dump_id required' },
        { status: 400 }
      );
    }

    // Check work queue status
    const { data: workItem, error: workError } = await supabase
      .from('universal_work_queue')
      .select('id, status, output_refs, error_log')
      .eq('basket_id', basketId)
      .eq('work_type', 'p1_extract_substrate')
      .contains('input_refs', { raw_dump_id: rawDumpId })
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (workError) {
      console.error('[upload-wizard-status] Work query error:', workError);
      return NextResponse.json(
        { error: 'Failed to query work status' },
        { status: 500 }
      );
    }

    if (!workItem) {
      // No work item found - might not have been queued yet
      return NextResponse.json({
        status: 'queued',
        substrate_count: 0,
      });
    }

    // Map work status to response status
    let status: 'queued' | 'processing' | 'completed' | 'error';
    if (workItem.status === 'completed') {
      status = 'completed';
    } else if (workItem.status === 'failed') {
      status = 'error';
    } else if (workItem.status === 'processing') {
      status = 'processing';
    } else {
      status = 'queued';
    }

    // If completed, count substrate proposals
    let substrateCount = 0;
    if (status === 'completed' && workItem.output_refs) {
      const proposalIds = workItem.output_refs.substrate_proposal_ids || [];
      substrateCount = proposalIds.length;
    }

    return NextResponse.json({
      status,
      substrate_count: substrateCount,
      error_message: workItem.error_log || undefined,
    });
  } catch (error) {
    console.error('[upload-wizard-status] Unexpected error:', error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : 'Internal server error',
      },
      { status: 500 }
    );
  }
}
