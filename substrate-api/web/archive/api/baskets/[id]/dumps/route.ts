export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createTestAwareClient, getTestAwareAuth } from '@/lib/auth/testHelpers';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext {
  params: Promise<{ id: string }>;
}

// GET /api/baskets/[id]/dumps — List raw_dumps for a basket (test-aware auth)
export async function GET(
  request: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id: basketId } = await ctx.params;
    const supabase = createTestAwareClient({ cookies });
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest
      ? { id: '00000000-0000-0000-0000-000000000002' }
      : await ensureWorkspaceForUser(userId, supabase);

    // Verify basket access (RLS still protects)
    const { data: basket, error: bErr } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basketId)
      .eq('workspace_id', workspace.id)
      .maybeSingle();

    if (bErr) return NextResponse.json({ error: bErr.message }, { status: 400 });
    if (!basket) return NextResponse.json({ error: 'not_found' }, { status: 404 });

    // Return raw_dumps (minimal fields for testing)
    const { data, error } = await supabase
      .from('raw_dumps')
      .select('id, created_at')
      .eq('basket_id', basketId)
      .eq('workspace_id', workspace.id)
      .order('created_at', { ascending: false })
      .limit(500);

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json({ dumps: data ?? [] }, { status: 200 });
  } catch (error) {
    console.error('Dumps list error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

