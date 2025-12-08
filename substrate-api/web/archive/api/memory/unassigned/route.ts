import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import type { Database } from '@/lib/dbTypes';
import { ensureSingleWorkspace } from '@/lib/canon/WorkspaceResolver';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET() {
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
    .select('id, tool, summary, payload, fingerprint, candidates, status, assigned_basket_id, source_host, source_session, created_at')
    .eq('workspace_id', workspace.id)
    .eq('status', 'pending')
    .order('created_at', { ascending: false });

  if (queryError) {
    return NextResponse.json({ error: queryError.message }, { status: 500 });
  }

  return NextResponse.json({ captures: data ?? [] });
}
