export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

interface RouteContext { params: Promise<{ basketId: string }> }

export async function GET(_req: NextRequest, ctx: RouteContext) {
  try {
    const { basketId } = await ctx.params;
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    // Verify access
    const { data: basket, error: bErr } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basketId)
      .maybeSingle();
    if (bErr || !basket || basket.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'not_found_or_forbidden' }, { status: 404 });
    }

    // Load retention policy (for optional stale-by-age rule)
    const { data: wsSettings } = await supabase
      .from('workspace_governance_settings')
      .select('retention_enabled, retention_policy')
      .eq('workspace_id', workspace.id)
      .maybeSingle();

    const retentionEnabled = Boolean(wsSettings?.retention_enabled);
    const retentionPolicy = (wsSettings?.retention_policy as any) || {};
    const blockDays: number | null = Number(retentionPolicy?.block?.days ?? null) || null;
    const contextItemDays: number | null = Number(retentionPolicy?.context_item?.days ?? null) || null;

    // Compute cutoff timestamps if enabled and days provided (>0)
    const now = new Date();
    const cutoffBlock = retentionEnabled && blockDays && blockDays > 0
      ? new Date(now.getTime() - blockDays * 24 * 60 * 60 * 1000)
      : null;
    const cutoffContextItem = retentionEnabled && contextItemDays && contextItemDays > 0
      ? new Date(now.getTime() - contextItemDays * 24 * 60 * 60 * 1000)
      : null;

    // Load basket documents to scope reference checks
    const { data: docs } = await supabase
      .from('documents')
      .select('id')
      .eq('basket_id', basketId)
      .limit(1000);
    const docIds = (docs || []).map((d: any) => d.id);

    // Preload referenced block ids using anti-join pattern
    let referencedBlockIds = new Set<string>();
    if (docIds.length > 0) {
      const { data: refBlocks } = await supabase
        .from('substrate_references')
        .select('substrate_id')
        .in('document_id', docIds)
        .eq('substrate_type', 'block')
        .limit(5000);
      (refBlocks || []).forEach((r: any) => referencedBlockIds.add(r.substrate_id));
    }

    // Candidate blocks (not archived), optionally older than cutoff
    let blockQuery = supabase
      .from('blocks')
      .select('id, title, created_at, confidence_score, status')
      .eq('basket_id', basketId)
      .neq('status', 'archived')
      .limit(200);
    if (cutoffBlock) blockQuery = blockQuery.lte('created_at', cutoffBlock.toISOString());
    const { data: blocks } = await blockQuery;

    const unrefBlockIds: string[] = [];
    (blocks || []).forEach((b: any) => {
      if (!referencedBlockIds.has(b.id)) unrefBlockIds.push(b.id);
    });

    // Preload referenced context_item ids
    let referencedItemIds = new Set<string>();
    if (docIds.length > 0) {
      const { data: refItems } = await supabase
        .from('substrate_references')
        .select('substrate_id')
        .in('document_id', docIds)
        .eq('substrate_type', 'context_item')
        .limit(5000);
      (refItems || []).forEach((r: any) => referencedItemIds.add(r.substrate_id));
    }

    // Candidate context items (not archived), optionally older than cutoff
    let itemQuery = supabase
      .from('context_items')
      .select('id, title, created_at, status')
      .eq('basket_id', basketId)
      .neq('status', 'archived')
      .limit(200);
    if (cutoffContextItem) itemQuery = itemQuery.lte('created_at', cutoffContextItem.toISOString());
    const { data: items } = await itemQuery;
    const unrefItemIds: string[] = [];
    (items || []).forEach((ci: any) => {
      if (!referencedItemIds.has(ci.id)) unrefItemIds.push(ci.id);
    });

    // Dumps eligible for redaction (not already redacted)
    const { data: dumps } = await supabase
      .from('raw_dumps')
      .select('id, created_at, processing_status')
      .eq('basket_id', basketId)
      .neq('processing_status', 'redacted')
      .limit(100);
    const candidateDumpIds = (dumps || []).map(d => d.id);

    // Cascade preview for top N candidates
    const limitN = 10;
    const preview = async (type: 'block'|'dump', id: string) => {
      const { data, error } = await supabase.rpc('fn_cascade_preview', {
        p_basket_id: basketId,
        p_substrate_type: type,
        p_substrate_id: id
      });
      if (error) return { refs_detached_count: 0, relationships_pruned_count: 0, affected_documents_count: 0 };
      return data || { refs_detached_count: 0, relationships_pruned_count: 0, affected_documents_count: 0 };
    };

    const blocksPreview = [] as any[];
    for (const id of unrefBlockIds.slice(0, limitN)) {
      blocksPreview.push({ id, preview: await preview('block', id) });
    }
    const dumpsPreview = [] as any[];
    for (const id of candidateDumpIds.slice(0, limitN)) {
      dumpsPreview.push({ id, preview: await preview('dump', id) });
    }

    // Duplicate detection for context_items by normalized_label (simple heuristic)
    const { data: allItems } = await supabase
      .from('context_items')
      .select('id, title, normalized_label, status')
      .eq('basket_id', basketId)
      .neq('status', 'archived')
      .limit(500);

    const dupGroups: Array<{ label: string; ids: string[] }> = [];
    if (allItems && allItems.length > 0) {
      const groups: Record<string, string[]> = {};
      for (const it of allItems) {
        const key = String((it as any).normalized_label || (it as any).title || '').trim().toLowerCase();
        if (!key) continue;
        if (!groups[key]) groups[key] = [];
        groups[key].push((it as any).id);
      }
      for (const [label, ids] of Object.entries(groups)) {
        if (ids.length > 1) dupGroups.push({ label, ids });
      }
    }

    return NextResponse.json({
      candidates: {
        blocks_to_archive: blocksPreview,
        context_items_to_deprecate: unrefItemIds.slice(0, limitN),
        dumps_to_redact: dumpsPreview,
        context_item_duplicates: dupGroups.slice(0, limitN)
      },
      policy: {
        retention_enabled: retentionEnabled,
        block_days: blockDays,
        context_item_days: contextItemDays
      }
    }, { status: 200 });
  } catch (e) {
    console.error('Maintenance suggestion error:', e);
    return NextResponse.json({ error: 'internal_error' }, { status: 500 });
  }
}
