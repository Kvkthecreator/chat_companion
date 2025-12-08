import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext { params: Promise<{ id: string }> }

// POST /api/baskets/[id]/restore — restore archived basket (not governed)
export async function POST(req: NextRequest, ctx: RouteContext) {
  try {
    const { id } = await ctx.params;

    const supabase = createServerSupabaseClient() as any;
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    // Verify basket access
    const { data: basket } = await supabase
      .from('baskets')
      .select('id,workspace_id,status')
      .eq('id', id)
      .maybeSingle();

    if (!basket) return NextResponse.json({ error: 'not found' }, { status: 404 });
    if (basket.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'forbidden' }, { status: 403 });
    }
    if (basket.status !== 'ARCHIVED') {
      return NextResponse.json({ error: 'basket not archived' }, { status: 400 });
    }

    // Restore basket
    const { data: updated, error } = await supabase
      .from('baskets')
      .update({
        status: 'ACTIVE',
        updated_at: new Date().toISOString()
      })
      .eq('id', id)
      .select('id,name,status,updated_at')
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    // Emit timeline event
    await supabase.from('timeline_events').insert({
      basket_id: id,
      workspace_id: workspace.id,
      event_type: 'BASKET_RESTORED',
      user_id: userId,
      metadata: {}
    });

    return NextResponse.json(updated, { status: 200 });
  } catch (e) {
    console.error('Basket restore error:', e);
    return NextResponse.json({ error: 'internal server error' }, { status: 500 });
  }
}
