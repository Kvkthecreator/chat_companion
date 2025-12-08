import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext {
  params: Promise<{ id: string }>;
}

// GET /api/baskets/:id/work — list recent work items scoped to a basket
export async function GET(_req: NextRequest, ctx: RouteContext) {
  try {
    const { id: basketId } = await ctx.params;
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    // Verify basket access
    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basketId)
      .eq('workspace_id', workspace.id)
      .maybeSingle();

    if (basketError) {
      return NextResponse.json({ error: basketError.message }, { status: 400 });
    }
    if (!basket) {
      return NextResponse.json({ error: 'basket not found' }, { status: 404 });
    }

    // Query agent/canonical queue for this basket
    const { data: work, error: workError } = await supabase
      .from('agent_processing_queue')
      .select('work_id, work_type, processing_state, created_at, basket_id, dump_id')
      .eq('basket_id', basketId)
      .order('created_at', { ascending: false })
      .limit(50);

    if (workError) {
      return NextResponse.json({ error: workError.message }, { status: 400 });
    }

    return NextResponse.json({
      basket_id: basketId,
      items: (work || []).map((w) => ({
        work_id: (w as any).work_id,
        work_type: (w as any).work_type,
        status: (w as any).processing_state,
        created_at: (w as any).created_at,
        last_activity: (w as any).created_at,
        dump_id: (w as any).dump_id ?? null,
      })),
    });
  } catch (err: any) {
    return NextResponse.json({ error: 'internal_error', details: String(err?.message ?? err) }, { status: 500 });
  }
}

