import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext { params: Promise<{ id: string }> }

// POST /api/baskets/[id]/archive — archive basket (soft delete, not governed)
export async function POST(req: NextRequest, ctx: RouteContext) {
  try {
    const { id } = await ctx.params;
    const body = await req.json().catch(() => ({}));
    const { reason } = body;

    const supabase = createServerSupabaseClient() as any;
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    // Verify basket access
    const { data: basket } = await supabase
      .from('baskets')
      .select('id,workspace_id,status,name')
      .eq('id', id)
      .maybeSingle();

    if (!basket) return NextResponse.json({ error: 'not found' }, { status: 404 });
    if (basket.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'forbidden' }, { status: 403 });
    }
    if (basket.status === 'ARCHIVED') {
      return NextResponse.json({ error: 'already archived' }, { status: 400 });
    }

    // Get cascade preview (count affected substrate)
    const [blocksCount, docsCount] = await Promise.all([
      supabase.from('blocks')
        .select('id', { count: 'exact', head: true })
        .eq('basket_id', id)
        .neq('status', 'archived'),
      supabase.from('documents')
        .select('id', { count: 'exact', head: true })
        .eq('basket_id', id)
    ]);

    // Archive basket
    const { data: updated, error } = await supabase
      .from('baskets')
      .update({
        status: 'ARCHIVED',
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
      event_type: 'BASKET_ARCHIVED',
      user_id: userId,
      metadata: {
        reason: reason || 'user_archived',
        blocks_affected: blocksCount.count || 0,
        documents_affected: docsCount.count || 0
      }
    });

    return NextResponse.json({
      ...updated,
      cascade_preview: {
        blocks_affected: blocksCount.count || 0,
        documents_affected: docsCount.count || 0
      }
    }, { status: 200 });
  } catch (e) {
    console.error('Basket archive error:', e);
    return NextResponse.json({ error: 'internal server error' }, { status: 500 });
  }
}
