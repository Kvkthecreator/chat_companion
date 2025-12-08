import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createTestAwareClient, getTestAwareAuth } from '@/lib/auth/testHelpers';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext {
  params: Promise<{ id: string }>;
}

type RawDumpRow = {
  id: string;
  created_at: string;
  file_url: string | null;
  processing_status: string | null;
  source_meta: Record<string, any> | null;
  body_md: string | null;
  text_dump: string | null;
};

type BlockRow = {
  id: string;
  raw_dump_id: string | null;
  title: string | null;
  semantic_type: string | null;
  confidence_score: number | null;
  created_at: string;
  metadata: Record<string, any> | null;
  status: string | null;
};

// V3.0: context_items merged into blocks - type removed

export async function GET(request: NextRequest, ctx: RouteContext) {
  try {
    const { id: basketId } = await ctx.params;
    const supabase = createTestAwareClient({ cookies });
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest
      ? { id: '00000000-0000-0000-0000-000000000002' }
      : await ensureWorkspaceForUser(userId, supabase);

    // Verify basket access for the current workspace
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
      return NextResponse.json({ error: 'not_found' }, { status: 404 });
    }

    const { data: dumps, error: dumpsError } = await supabase
      .from('raw_dumps')
      .select(`
        id,
        created_at,
        file_url,
        processing_status,
        source_meta,
        body_md,
        text_dump
      `)
      .eq('basket_id', basketId)
      .eq('workspace_id', workspace.id)
      .order('created_at', { ascending: false })
      .limit(200);

    if (dumpsError) {
      console.error('Uploads API: failed to fetch raw dumps', dumpsError);
      return NextResponse.json({ error: 'Failed to fetch uploads' }, { status: 500 });
    }

    const dumpIds = (dumps ?? []).map((dump) => dump.id);

    let blocks: BlockRow[] = [];

    if (dumpIds.length > 0) {
      const { data: blockRows, error: blocksError } = await supabase
        .from('blocks')
        .select(`
          id,
          raw_dump_id,
          title,
          semantic_type,
          confidence_score,
          created_at,
          metadata,
          status
        `)
        .in('raw_dump_id', dumpIds)
        .eq('workspace_id', workspace.id)
        .eq('basket_id', basketId)
        .order('created_at', { ascending: false });

      if (blocksError) {
        console.error('Uploads API: failed to fetch derived blocks', blocksError);
        return NextResponse.json({ error: 'Failed to fetch derived blocks' }, { status: 500 });
      }

      blocks = blockRows ?? [];

      // V3.0: context_items merged into blocks - query removed
    }

    const blockMap = new Map<string, BlockRow[]>();
    blocks.forEach((block) => {
      if (!block.raw_dump_id) return;
      const existing = blockMap.get(block.raw_dump_id) ?? [];
      existing.push(block);
      blockMap.set(block.raw_dump_id, existing);
    });

    // V3.0: context_items merged into blocks - contextMap removed

    const uploads = (dumps ?? []).map((dump) => {
      const derivedBlocks = (blockMap.get(dump.id) ?? []).map((block) => ({
        id: block.id,
        title: block.title,
        semantic_type: block.semantic_type,
        confidence_score: block.confidence_score,
        created_at: block.created_at,
        metadata: block.metadata,
        state: block.status,
      }));

      // V3.0: context_items merged into blocks - derivedContextItems removed

      const bodyPreviewSource = dump.body_md || dump.text_dump || '';
      const body_preview = bodyPreviewSource ? bodyPreviewSource.slice(0, 280) : null;

      return {
        dump: {
          id: dump.id,
          created_at: dump.created_at,
          file_url: dump.file_url,
          processing_status: dump.processing_status,
          source_meta: dump.source_meta ?? {},
          body_preview,
        },
        derived_blocks: derivedBlocks,
        work_items: [] as any[],
      };
    });

    const stats = {
      total_uploads: uploads.length,
      total_blocks: blocks.length,
      files: uploads.filter((upload) => Boolean(upload.dump.file_url)).length,
      text: uploads.filter((upload) => !upload.dump.file_url).length,
    };

    return NextResponse.json({ uploads, stats }, { status: 200 });
  } catch (error) {
    console.error('Uploads API: unexpected error', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
