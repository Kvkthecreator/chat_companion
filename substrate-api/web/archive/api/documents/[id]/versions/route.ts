import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getTestAwareAuth } from '@/lib/auth/testHelpers';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext { params: Promise<{ id: string }> }

// GET /api/documents/[id]/versions?version_hash=...
export async function GET(req: NextRequest, ctx: RouteContext) {
  try {
    const { id } = await ctx.params;
    const supabase = createServerSupabaseClient() as any;
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    // Verify document access
    const { data: doc, error: docErr } = await supabase
      .from('documents')
      .select('id, workspace_id')
      .eq('id', id)
      .maybeSingle();
    if (docErr || !doc) return NextResponse.json({ error: 'document not found' }, { status: 404 });
    if (doc.workspace_id !== workspace.id) return NextResponse.json({ error: 'unauthorized' }, { status: 403 });

    const { searchParams } = new URL(req.url);
    const version_hash = searchParams.get('version_hash');

    let query = supabase.from('document_versions').select('version_hash, created_at, version_message, content').eq('document_id', id).order('created_at', { ascending: false }).limit(20);
    if (version_hash) query = query.eq('version_hash', version_hash).limit(1);
    const { data: items, error: verErr } = await query;
    // If RLS blocks or table absent, gracefully return empty list
    if (verErr) return NextResponse.json({ items: [] }, { status: 200 });
    return NextResponse.json({ items: items || [] }, { status: 200 });
  } catch (e) {
    return NextResponse.json({ error: 'internal server error' }, { status: 500 });
  }
}
