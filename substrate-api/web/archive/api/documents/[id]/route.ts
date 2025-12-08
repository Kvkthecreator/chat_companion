import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getTestAwareAuth } from '@/lib/auth/testHelpers';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext { params: Promise<{ id: string }> }

// GET /api/documents/[id] - Get document with current version content
// Canon v3.0: Uses document_heads view to join document + current version
export async function GET(req: NextRequest, ctx: RouteContext) {
  try {
    const { id } = await ctx.params;
    const supabase = createServerSupabaseClient() as any;
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    // Use document_heads view for easy access to document + current version
    const { data: row, error } = await supabase
      .from('document_heads')
      .select('*')
      .eq('document_id', id)
      .maybeSingle();

    if (error || !row) {
      console.error('Document GET error:', error);
      return NextResponse.json({ error: 'not found' }, { status: 404 });
    }

    if (row.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'unauthorized' }, { status: 403 });
    }

    return NextResponse.json({
      id: row.document_id,
      basket_id: row.basket_id,
      title: row.title,
      document_type: row.document_type,
      composition_instructions: row.composition_instructions || {},
      substrate_filter: row.substrate_filter || {},
      source_raw_dump_id: row.source_raw_dump_id,
      current_version_hash: row.current_version_hash,
      created_at: row.document_created_at,
      updated_at: row.document_updated_at,
      metadata: row.document_metadata || {},

      // Current version content (read-only)
      content: row.content,
      version_metadata: row.version_metadata || {},
      substrate_refs_snapshot: row.substrate_refs_snapshot || [],
      version_created_at: row.version_created_at,
      version_trigger: row.version_trigger,
      version_message: row.version_message,
    }, { status: 200 });
  } catch (e) {
    console.error('Document GET error:', e);
    return NextResponse.json({ error: 'internal server error' }, { status: 500 });
  }
}

// PATCH /api/documents/[id] - Update document composition definition
// Canon v3.0: Updates composition instructions, NOT content
export async function PATCH(req: NextRequest, ctx: RouteContext) {
  try {
    const { id } = await ctx.params;
    const body = await req.json();
    const supabase = createServerSupabaseClient() as any;
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    // Verify ownership
    const { data: doc, error: docErr } = await supabase
      .from('documents')
      .select('id, workspace_id')
      .eq('id', id)
      .maybeSingle();

    if (docErr || !doc) {
      return NextResponse.json({ error: 'not found' }, { status: 404 });
    }

    if (doc.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'unauthorized' }, { status: 403 });
    }

    // Allow updating composition definition fields only (no content_raw)
    const patch: any = { updated_at: new Date().toISOString() };

    if (typeof body.title === 'string') {
      patch.title = body.title;
    }

    if (body.composition_instructions !== undefined) {
      patch.composition_instructions = body.composition_instructions;
    }

    if (body.substrate_filter !== undefined) {
      patch.substrate_filter = body.substrate_filter;
    }

    if (body.metadata !== undefined) {
      patch.metadata = body.metadata;
    }

    const { data: updated, error } = await supabase
      .from('documents')
      .update(patch)
      .eq('id', id)
      .select('id, title, composition_instructions, substrate_filter, updated_at, metadata')
      .single();

    if (error) {
      console.error('Document PATCH error:', error);
      return NextResponse.json({ error: 'update failed' }, { status: 400 });
    }

    return NextResponse.json({
      document: updated,
      message: 'Composition definition updated. Regenerate document to see changes.'
    }, { status: 200 });
  } catch (e) {
    console.error('Document PATCH error:', e);
    return NextResponse.json({ error: 'internal server error' }, { status: 500 });
  }
}
