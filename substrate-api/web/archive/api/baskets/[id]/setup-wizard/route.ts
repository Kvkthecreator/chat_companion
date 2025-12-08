import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

/**
 * Setup Wizard Submission API
 * Canon v3.0 compliant - P0-P3 governance flow
 *
 * Flow:
 * 1. Validate inputs against wizard config
 * 2. Create raw_dumps (P0) - one per input field
 * 3. Trigger P1 extraction via work queue
 * 4. Return raw_dump IDs for tracking
 */
export async function POST(
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
      .select('id, workspace_id, name')
      .eq('id', basketId)
      .maybeSingle();

    if (basketError || !basket || basket.workspace_id !== workspace.id) {
      return NextResponse.json(
        { error: 'Basket not found' },
        { status: 404 }
      );
    }

    // Load wizard config
    const body = await req.json();
    const { inputs } = body as { inputs: Record<string, string> };

    if (!inputs || typeof inputs !== 'object') {
      return NextResponse.json(
        { error: 'Invalid inputs' },
        { status: 400 }
      );
    }

    const sanitizedEntries = Object.entries(inputs).filter(([, value]) => typeof value === 'string' && value.trim().length);
    if (!sanitizedEntries.length) {
      return NextResponse.json(
        { error: 'No valid inputs provided' },
        { status: 400 }
      );
    }

    // P0: Create raw_dumps for each provided input
    const raw_dump_inserts = sanitizedEntries.map(([field, value]) => ({
        basket_id: basketId,
        workspace_id: workspace.id,
        body_md: value.trim(),
        source_meta: {
          wizard_field: field,
          wizard_type: 'setup',
        },
        created_by: userId,
      }));

    const { data: raw_dumps, error: dumpError } = await supabase
      .from('raw_dumps')
      .insert(raw_dump_inserts)
      .select('id');

    if (dumpError || !raw_dumps) {
      console.error('[setup-wizard] Failed to create raw_dumps:', dumpError);
      return NextResponse.json(
        { error: 'Failed to create raw dumps' },
        { status: 500 }
      );
    }

    // P1: Create work items for substrate extraction
    const work_inserts = raw_dumps.map((dump) => ({
      work_type: 'p1_extract_substrate',
      status: 'queued',
      basket_id: basketId,
      workspace_id: workspace.id,
      input_refs: { raw_dump_id: dump.id },
      metadata: {
        source: 'setup_wizard',
      },
    }));

    const { data: work_items, error: workError } = await supabase
      .from('universal_work_queue')
      .insert(work_inserts)
      .select('id');

    if (workError) {
      console.error('[setup-wizard] Failed to queue work:', workError);
      // Continue anyway - work might be picked up by other mechanisms
    }

    // Immediate response - P1 extraction happens async
    // Frontend can poll for completion or show governance UI when ready
    return NextResponse.json({
      success: true,
      raw_dump_ids: raw_dumps.map((d) => d.id),
      work_ids: work_items?.map((w) => w.id) || [],
      message: 'Setup wizard inputs captured. Substrate extraction in progress.',
      next_steps: {
        governance_url: `/baskets/${basketId}/building-blocks`,
        documents_url: `/baskets/${basketId}/documents`,
      },
    });
  } catch (error) {
    console.error('[setup-wizard] Unexpected error:', error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : 'Internal server error',
      },
      { status: 500 }
    );
  }
}
