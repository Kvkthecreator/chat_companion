export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createRouteHandlerClient } from '@/lib/supabase/clients';
import { ensureWorkspaceServer } from '@/lib/workspaces/ensureWorkspaceServer';

export async function POST(req: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();
    if (authError || !user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const workspace = await ensureWorkspaceServer(supabase);
    if (!workspace) return NextResponse.json({ error: 'Workspace access required' }, { status: 401 });

    // Admin only
    const { data: membership } = await supabase
      .from('workspace_memberships')
      .select('role')
      .eq('workspace_id', workspace.id)
      .eq('user_id', user.id)
      .single();
    if (!membership || !['admin','owner'].includes(membership.role)) {
      return NextResponse.json({ error: 'Admin required' }, { status: 403 });
    }

    const { data, error } = await supabase.rpc('fn_vacuum_substrates', {
      p_workspace_id: workspace.id,
      p_limit: 100
    });
    if (error) return NextResponse.json({ error: error.message }, { status: 400 });
    return NextResponse.json({ success: true, result: data }, { status: 200 });
  } catch (e) {
    console.error('Vacuum run error:', e);
    return NextResponse.json({ error: 'internal_error' }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}

