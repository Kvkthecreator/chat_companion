import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { transformTimeline } from '@/lib/timeline/transform';
import type { TimelineEventDTO } from '@/lib/timeline/types';

// GET /api/baskets/[id]/timeline?limit=50 — minimal projection to avoid 404s
export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const supabase = createServerSupabaseClient() as any;
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);
    const limit = Math.min(parseInt(new URL(req.url).searchParams.get('limit') || '50', 10) || 50, 200);

    // Verify basket belongs to workspace
    const { data: basket } = await supabase
      .from('baskets')
      .select('id,workspace_id')
      .eq('id', id)
      .maybeSingle();
    if (!basket) return NextResponse.json({ items: [] }, { status: 200 });
    if (basket.workspace_id !== workspace.id) return NextResponse.json({ items: [] }, { status: 200 });

    // Fetch recent timeline events (if table exists)
    const significanceParam = new URL(req.url).searchParams.get('significance');
    const significanceFilter = (['low', 'medium', 'high'] as const).includes(
      significanceParam as 'low' | 'medium' | 'high',
    )
      ? (significanceParam as 'low' | 'medium' | 'high')
      : null;

    const { data: events, error } = await supabase
      .from('timeline_events')
      .select('id, ts, kind, ref_id, preview, payload, source_host, source_session')
      .eq('basket_id', id)
      .order('ts', { ascending: false })
      .order('id', { ascending: false })
      .limit(limit);
    if (error || !events) return NextResponse.json({ items: [] }, { status: 200 });

    let items: TimelineEventDTO[] = transformTimeline(events);

    if (significanceFilter) {
      items = items.filter((event) => event.significance === significanceFilter);
    }

    return NextResponse.json({ items }, { status: 200 });
  } catch {
    return NextResponse.json({ items: [] }, { status: 200 });
  }
}
