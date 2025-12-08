export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { routeWork } from '@/lib/governance/universalWorkRouter';

export async function POST(req: NextRequest) {
  try {
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    const body = await req.json().catch(() => null);
    if (!body || !Array.isArray(body.ops) || !body.basket_id) {
      return NextResponse.json({ error: 'basket_id and ops[] required' }, { status: 422 });
    }

    // Route through Universal Work (Canon v2.2)
    const work = await routeWork(supabase as any, {
      work_type: 'MANUAL_EDIT',
      work_payload: {
        operations: body.ops,
        basket_id: body.basket_id,
        provenance: body.provenance || []
      },
      workspace_id: workspace.id,
      user_id: userId,
      priority: 'normal'
    });
    return NextResponse.json(work, { status: 200 });
  } catch (e) {
    console.error('Maintenance proposal error:', e);
    return NextResponse.json({ error: 'internal_error' }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}
