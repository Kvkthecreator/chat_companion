import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

/**
 * Upload Wizard - Document Composition API (P4)
 * Canon v3.0 compliant
 *
 * Flow:
 * 1. Receive raw_dump_id for uploaded document
 * 2. Query approved substrate for this raw_dump
 * 3. Compose document from substrate (P4)
 * 4. Link document ↔ raw_dump (bidirectional)
 * 5. Return composed document for comparison
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
      .select('id, workspace_id, name, mode')
      .eq('id', basketId)
      .maybeSingle();

    if (basketError || !basket || basket.workspace_id !== workspace.id) {
      return NextResponse.json(
        { error: 'Basket not found' },
        { status: 404 }
      );
    }

    const body = await req.json();
    const { raw_dump_id } = body as { raw_dump_id: string };

    if (!raw_dump_id) {
      return NextResponse.json(
        { error: 'raw_dump_id required' },
        { status: 400 }
      );
    }

    // Verify raw_dump belongs to this basket
    const { data: rawDump, error: dumpError } = await supabase
      .from('raw_dumps')
      .select('id, body_md, source_meta')
      .eq('id', raw_dump_id)
      .eq('basket_id', basketId)
      .maybeSingle();

    if (dumpError || !rawDump) {
      return NextResponse.json(
        { error: 'Raw dump not found' },
        { status: 404 }
      );
    }

    // Query approved substrate extracted from this raw_dump
    const { data: substrate, error: substrateError } = await supabase
      .from('substrate')
      .select('id, anchor_id, content_md, metadata')
      .eq('basket_id', basketId)
      .contains('source_refs', { raw_dump_id })
      .eq('status', 'approved');

    if (substrateError) {
      console.error('[compose] Substrate query error:', substrateError);
      return NextResponse.json(
        { error: 'Failed to query substrate' },
        { status: 500 }
      );
    }

    // P4: Compose document from substrate
    // Group substrate by anchor for structured composition
    const substrateByAnchor = (substrate || []).reduce((acc, sub) => {
      if (!acc[sub.anchor_id]) {
        acc[sub.anchor_id] = [];
      }
      acc[sub.anchor_id].push(sub);
      return acc;
    }, {} as Record<string, typeof substrate>);

    // Build composed markdown
    const sections: string[] = [];
    const originalFilename = rawDump.source_meta?.original_filename || 'Uploaded Document';

    sections.push(`# ${originalFilename} (YARNNN Composed)\n`);
    sections.push(`> This document is composed from renewable substrate extracted from your upload.\n`);

    // Add sections based on substrate anchors
    for (const [anchorId, items] of Object.entries(substrateByAnchor)) {
      const anchorLabel = anchorId.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
      sections.push(`\n## ${anchorLabel}\n`);

      items.forEach((item) => {
        sections.push(item.content_md);
      });
    }

    const composedBody = sections.join('\n');

    // Create document with bidirectional link
    const { data: document, error: docError } = await supabase
      .from('documents')
      .insert({
        basket_id: basketId,
        workspace_id: workspace.id,
        title: `${originalFilename} (Transformed)`,
        body_md: composedBody,
        source_raw_dump_id: raw_dump_id, // Link to raw_dump
        version_trigger: 'upload_composition',
        created_by: userId,
      })
      .select('id, title, body_md, created_at')
      .single();

    if (docError || !document) {
      console.error('[compose] Document creation error:', docError);
      return NextResponse.json(
        { error: 'Failed to create document' },
        { status: 500 }
      );
    }

    // Update raw_dump with document_id (reverse link)
    await supabase
      .from('raw_dumps')
      .update({
        document_id: document.id,
      })
      .eq('id', raw_dump_id);

    return NextResponse.json({
      success: true,
      document: {
        id: document.id,
        title: document.title,
        body_md: document.body_md,
        created_at: document.created_at,
      },
      original: {
        body_md: rawDump.body_md,
        filename: originalFilename,
      },
      substrate_count: substrate?.length || 0,
      message: 'Document composed from extracted substrate',
    });
  } catch (error) {
    console.error('[compose] Unexpected error:', error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : 'Internal server error',
      },
      { status: 500 }
    );
  }
}
