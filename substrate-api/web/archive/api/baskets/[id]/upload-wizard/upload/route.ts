import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

/**
 * Upload Wizard - File Upload API
 * Canon v3.0 compliant
 *
 * Flow:
 * 1. Receive uploaded document content
 * 2. Create raw_dump (P0)
 * 3. Queue P1 extraction work
 * 4. Return raw_dump ID for status tracking
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

    // Load mode config
    const body = await req.json();
    const { fileName, content } = body as { fileName: string; content: string };

    if (!fileName || !content?.trim()) {
      return NextResponse.json(
        { error: 'Invalid file data' },
        { status: 400 }
      );
    }

    // P0: Create raw_dump for uploaded document
    const { data: raw_dump, error: dumpError } = await supabase
      .from('raw_dumps')
      .insert({
        basket_id: basketId,
        workspace_id: workspace.id,
        body_md: content.trim(),
        source_meta: {
          wizard_type: 'upload',
          original_filename: fileName,
          upload_timestamp: new Date().toISOString(),
        },
        created_by: userId,
      })
      .select('id')
      .single();

    if (dumpError || !raw_dump) {
      console.error('[upload-wizard] Failed to create raw_dump:', dumpError);
      return NextResponse.json(
        { error: 'Failed to create raw dump' },
        { status: 500 }
      );
    }

    // P1: Create work item for substrate extraction
    const { data: work_item, error: workError } = await supabase
      .from('universal_work_queue')
      .insert({
        work_type: 'p1_extract_substrate',
        status: 'queued',
        basket_id: basketId,
        workspace_id: workspace.id,
        input_refs: { raw_dump_id: raw_dump.id },
        metadata: {
          source: 'upload_wizard',
          original_filename: fileName,
        },
      })
      .select('id')
      .single();

    if (workError) {
      console.error('[upload-wizard] Failed to queue work:', workError);
      // Continue anyway - work might be picked up by other mechanisms
    }

    return NextResponse.json({
      success: true,
      raw_dump_id: raw_dump.id,
      work_id: work_item?.id,
      message: 'Document uploaded. Substrate extraction queued.',
    });
  } catch (error) {
    console.error('[upload-wizard] Unexpected error:', error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : 'Internal server error',
      },
      { status: 500 }
    );
  }
}
