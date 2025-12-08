export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));
    const { basket_id, substrate_type, substrate_id } = body || {};

    if (!basket_id || !substrate_type || !substrate_id) {
      return NextResponse.json({ error: 'basket_id, substrate_type, substrate_id required' }, { status: 422 });
    }

    // Validate substrate_type
    const validTypes = new Set(['block','dump','context_item','timeline_event']);
    if (!validTypes.has(String(substrate_type))) {
      return NextResponse.json({ error: 'invalid substrate_type' }, { status: 422 });
    }

    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    // Verify basket access
    const { data: basket, error: bErr } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basket_id)
      .maybeSingle();
    if (bErr) return NextResponse.json({ error: bErr.message }, { status: 400 });
    if (!basket || basket.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'not_found_or_forbidden' }, { status: 404 });
    }

    // Cascade preview via RPC (with robust fallbacks)
    const callPreview = async (): Promise<{ refs_detached_count: number; relationships_pruned_count: number; affected_documents_count: number }> => {
      // 1) Try canonical RPC signature
      let { data, error } = await supabase.rpc('fn_cascade_preview', {
        p_basket_id: basket_id,
        p_substrate_type: substrate_type,
        p_substrate_id: substrate_id,
      });
      if (!error && data) return data as any;

      // 2) Try alternate named-args (some deployments define param order differently)
      const alt = await supabase.rpc('fn_cascade_preview', {
        p_basket_id: basket_id,
        p_substrate_id: substrate_id,
        p_substrate_type: substrate_type,
      } as any);
      if (!alt.error && alt.data) return alt.data as any;

      // 3) Fallback: compute counts directly (no RPC required)
      const refs = await supabase
        .from('substrate_references')
        .select('document_id', { count: 'exact', head: true })
        .in('document_id', (await supabase.from('documents').select('id').eq('basket_id', basket_id)).data?.map((d: any) => d.id) || [])
        .eq('substrate_type', substrate_type)
        .eq('substrate_id', substrate_id);

      // Distinct affected documents
      const docsRes = await supabase
        .from('substrate_references')
        .select('document_id')
        .in('document_id', (await supabase.from('documents').select('id').eq('basket_id', basket_id)).data?.map((d: any) => d.id) || [])
        .eq('substrate_type', substrate_type)
        .eq('substrate_id', substrate_id);

      const relsRes = await supabase
        .from('substrate_relationships')
        .select('id')
        .eq('basket_id', basket_id)
        .or(`and(from_id.eq.${substrate_id},from_type.eq.${substrate_type}),and(to_id.eq.${substrate_id},to_type.eq.${substrate_type})`);

      const affectedDocs = new Set<string>();
      (docsRes.data || []).forEach((r: any) => { if (r.document_id) affectedDocs.add(r.document_id); });

      return {
        refs_detached_count: (refs as any)?.count ?? (docsRes.data || []).length,
        relationships_pruned_count: (relsRes.data || []).length,
        affected_documents_count: affectedDocs.size,
      };
    };

    const preview = await callPreview();
    return NextResponse.json({ preview }, { status: 200 });
  } catch (error) {
    console.error('Cascade preview error:', error);
    return NextResponse.json({ error: 'internal_error' }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}
