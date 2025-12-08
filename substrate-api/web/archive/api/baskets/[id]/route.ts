import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient, createServiceRoleClient } from '@/lib/supabase/clients';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext { params: Promise<{ id: string }> }

// GET /api/baskets/[id] — fetch basket details within the user's workspace
export async function GET(req: NextRequest, ctx: RouteContext) {
  try {
    const { id } = await ctx.params;
    const supabase = createRouteHandlerClient({ cookies });
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    const { data: basket, error } = await supabase
      .from('baskets')
      .select('id,name,workspace_id,status,created_at')
      .eq('id', id)
      .maybeSingle();

    if (error) return NextResponse.json({ error: error.message }, { status: 400 });
    if (!basket) return NextResponse.json({ error: 'not found' }, { status: 404 });
    if (basket.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'forbidden' }, { status: 403 });
    }

    return NextResponse.json({
      id: basket.id,
      name: basket.name,
      status: basket.status,
      created_at: basket.created_at,
      has_setup_wizard: false,
    }, { status: 200 });
  } catch (e) {
    return NextResponse.json({ error: 'internal server error' }, { status: 500 });
  }
}

// PATCH /api/baskets/[id] — rename basket (direct, not governed)
export async function PATCH(req: NextRequest, ctx: RouteContext) {
  try {
    const { id } = await ctx.params;
    const body = await req.json().catch(() => ({}));
    const { name } = body;

    if (!name || typeof name !== 'string' || name.trim().length === 0) {
      return NextResponse.json({ error: 'name required' }, { status: 422 });
    }

    const supabase = createRouteHandlerClient({ cookies });
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    // Verify basket access
    const { data: basket } = await supabase
      .from('baskets')
      .select('id,workspace_id,name')
      .eq('id', id)
      .maybeSingle();

    if (!basket) return NextResponse.json({ error: 'not found' }, { status: 404 });
    if (basket.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'forbidden' }, { status: 403 });
    }

    // Update name
    const { data: updated, error } = await supabase
      .from('baskets')
      .update({ name: name.trim() })
      .eq('id', id)
      .select('id,name')
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    // Emit timeline event
    const serviceSupabase = createServiceRoleClient();
    const { error: timelineError } = await serviceSupabase.from('timeline_events').insert({
      basket_id: id,
      workspace_id: workspace.id,
      event_type: 'BASKET_RENAMED',
      user_id: userId,
      metadata: { old_name: basket.name, new_name: name.trim() }
    });

    if (timelineError) {
      console.warn('[Basket Rename] Failed to emit timeline event', timelineError);
    }

    return NextResponse.json(updated, { status: 200 });
  } catch (e) {
    console.error('Basket rename error:', e);
    return NextResponse.json({ error: 'internal server error' }, { status: 500 });
  }
}
