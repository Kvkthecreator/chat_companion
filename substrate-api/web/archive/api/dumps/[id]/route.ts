import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getTestAwareAuth } from '@/lib/auth/testHelpers';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext {
  params: Promise<{ id: string }>;
}

// GET /api/dumps/[id] - Retrieve specific dump
export async function GET(
  request: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id } = await ctx.params;
    const supabase = createServerSupabaseClient();
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    // Get dump with workspace isolation
    const { data: dump, error } = await supabase
      .from('raw_dumps')
      .select('*')
      .eq('id', id)
      .eq('workspace_id', workspace.id)
      .maybeSingle();

    if (error) {
      console.error('Error fetching dump:', error);
      return NextResponse.json({ error: 'Failed to fetch dump' }, { status: 500 });
    }

    if (!dump) {
      return NextResponse.json({ error: 'Dump not found' }, { status: 404 });
    }

    // Return dump data
    return NextResponse.json({
      id: dump.id,
      basket_id: dump.basket_id,
      workspace_id: dump.workspace_id,
      body_md: dump.body_md,
      file_url: dump.file_url,
      source_meta: dump.source_meta,
      created_at: dump.created_at,
      updated_at: dump.updated_at
    }, { status: 200 });

  } catch (error) {
    console.error('Dump retrieval error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}