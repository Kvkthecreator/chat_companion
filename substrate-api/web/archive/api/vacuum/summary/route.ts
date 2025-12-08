export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

export async function GET(_req: NextRequest) {
  try {
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    const sinceIso = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();

    // Aggregate from tombstones to avoid schema drift in timeline_events
    const { data, error } = await supabase
      .from('substrate_tombstones')
      .select('substrate_type, physically_deleted_at')
      .eq('workspace_id', workspace.id)
      .not('physically_deleted_at', 'is', null)
      .gte('physically_deleted_at', sinceIso)
      .limit(1000);

    if (error) return NextResponse.json({ error: error.message }, { status: 400 });

    const total = (data || []).length;
    const byType: Record<string, number> = {};
    let lastEventAt: string | null = null;
    (data || []).forEach(row => {
      const t = row.substrate_type || 'unknown';
      byType[t] = (byType[t] || 0) + 1;
      const ts = row.physically_deleted_at as string | null;
      if (ts && (!lastEventAt || ts > lastEventAt)) lastEventAt = ts;
    });

    return NextResponse.json({
      window: '24h',
      total_deleted: total,
      by_type: byType,
      last_event_at: lastEventAt
    });
  } catch (e) {
    console.error('Vacuum summary error:', e);
    return NextResponse.json({ error: 'internal_error' }, { status: 500 });
  }
}

