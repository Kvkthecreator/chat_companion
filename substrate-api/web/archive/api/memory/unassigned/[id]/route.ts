import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import type { Database } from '@/lib/dbTypes';
import { ensureSingleWorkspace } from '@/lib/canon/WorkspaceResolver';

interface Body {
  status: 'assigned' | 'dismissed' | 'pending';
  assigned_basket_id?: string | null;
}

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const supabase = createRouteHandlerClient<Database>({ cookies });
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  const workspace = await ensureSingleWorkspace(user.id, supabase);
  const body = (await request.json()) as Body;

  const updates = {
    status: body.status,
    assigned_basket_id: body.assigned_basket_id ?? null,
    resolved_at: new Date().toISOString(),
    resolved_by: user.id,
  };

  const { data, error: updateError } = await supabase
    .from('mcp_unassigned_captures')
    .update(updates)
    .eq('id', params.id)
    .eq('workspace_id', workspace.id)
    .select('id')
    .maybeSingle();

  if (updateError) {
    return NextResponse.json({ error: updateError.message }, { status: 500 });
  }

  if (!data) {
    return NextResponse.json({ error: 'not_found' }, { status: 404 });
  }

  return NextResponse.json({ status: 'updated' });
}

export async function GET(request: Request, { params }: { params: { id: string } }) {
  const supabase = createRouteHandlerClient<Database>({ cookies });
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  const workspace = await ensureSingleWorkspace(user.id, supabase);

  const { data, error: queryError } = await supabase
    .from('mcp_unassigned_captures')
    .select(
      'id, tool, summary, payload, fingerprint, candidates, status, assigned_basket_id, source_host, source_session, created_at'
    )
    .eq('id', params.id)
    .eq('workspace_id', workspace.id)
    .maybeSingle();

  if (queryError) {
    return NextResponse.json({ error: queryError.message }, { status: 500 });
  }

  if (!data) {
    return NextResponse.json({ error: 'not_found' }, { status: 404 });
  }

  return NextResponse.json(data);
}
