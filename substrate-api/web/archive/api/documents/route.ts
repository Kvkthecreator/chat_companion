import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getTestAwareAuth } from '@/lib/auth/testHelpers';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

// POST /api/documents - create a document (composition definition)
// Canon v3.0: Documents are composition definitions, not editable content
export async function POST(req: NextRequest) {
  try {
    const supabase = createServerSupabaseClient() as any;
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    const body = await req.json();
    const { basket_id, title, composition_instructions, substrate_filter, metadata } = body || {};
    if (!basket_id || !title) {
      return NextResponse.json({ error: 'basket_id and title required' }, { status: 400 });
    }

    // Create document as composition definition (no content_raw)
    const { data: inserted, error } = await supabase
      .from('documents')
      .insert({
        basket_id,
        workspace_id: workspace.id,
        title: String(title),
        composition_instructions: composition_instructions || {},
        substrate_filter: substrate_filter || {},
        document_type: 'narrative',
        metadata: {
          created_via: 'api',
          ...(metadata || {})
        }
      })
      .select('id, basket_id, title, composition_instructions, substrate_filter, created_at, metadata')
      .single();

    if (error || !inserted) {
      console.error('Document creation failed:', error);
      return NextResponse.json({ error: error?.message || 'create failed' }, { status: 400 });
    }

    return NextResponse.json({
      document: inserted,
      message: 'Document created. Use composition API to generate content from substrate.'
    }, { status: 201 });
  } catch (e) {
    console.error('Document POST error:', e);
    return NextResponse.json({ error: 'internal server error' }, { status: 500 });
  }
}

// GET /api/documents?basketId=uuid&limit=20
export async function GET(req: NextRequest) {
  try {
    const supabase = createServerSupabaseClient() as any;
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    const { searchParams } = new URL(req.url);
    const basketId = searchParams.get('basketId');
    const limit = Math.min(parseInt(searchParams.get('limit') || '20', 10) || 20, 100);

    let query = supabase
      .from('documents')
      .select('id, basket_id, title, current_version_hash, created_at, updated_at, metadata, workspace_id, composition_instructions, substrate_filter')
      .eq('workspace_id', workspace.id)
      .order('updated_at', { ascending: false })
      .limit(limit);

    if (basketId) {
      query = query.eq('basket_id', basketId);
    }

    const { data, error } = await query;
    if (error) {
      console.error('Documents GET error:', error);
      return NextResponse.json({ documents: [] }, { status: 200 });
    }

    const documents = (data || []).map((d: any) => ({
      id: d.id,
      basket_id: d.basket_id,
      title: d.title,
      current_version_hash: d.current_version_hash,
      has_content: !!d.current_version_hash,
      created_at: d.created_at,
      updated_at: d.updated_at,
      metadata: d.metadata || {},
      composition_instructions: d.composition_instructions || {},
      substrate_filter: d.substrate_filter || {},
    }));

    return NextResponse.json({ documents }, { status: 200 });
  } catch (e) {
    console.error('Documents GET error:', e);
    return NextResponse.json({ error: 'internal server error' }, { status: 500 });
  }
}
