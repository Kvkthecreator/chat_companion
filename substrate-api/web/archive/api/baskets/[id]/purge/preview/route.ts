export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@/lib/supabase/clients';
import { ensureWorkspaceServer } from '@/lib/workspaces/ensureWorkspaceServer';

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const supabase = createRouteHandlerClient({ cookies: (await import('next/headers')).cookies });
    const workspace = await ensureWorkspaceServer(supabase);
    if (!workspace) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { id: basket_id } = await params;
    const [blocks, dumps] = await Promise.all([
      supabase.from('blocks')
        .select('id', { count: 'exact', head: true })
        .eq('basket_id', basket_id).eq('workspace_id', workspace.id).neq('status','archived'),
      supabase.from('raw_dumps')
        .select('id', { count: 'exact', head: true })
        .eq('basket_id', basket_id).eq('workspace_id', workspace.id).neq('processing_status','redacted')
    ]);

    return NextResponse.json({
      blocks: blocks.count || 0,
      dumps: dumps.count || 0
    });
  } catch (e) {
    console.error('Purge preview error:', e);
    return NextResponse.json({ error: 'internal_error' }, { status: 500 });
  }
}

