import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { getAuthenticatedUser } from "@/lib/auth/getAuthenticatedUser";
import { ensureWorkspaceForUser } from "@/lib/workspaces/ensureWorkspaceForUser";

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(_req: NextRequest, ctx: RouteContext) {
  try {
    const { id: basketId } = await ctx.params;
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basketId)
      .eq('workspace_id', workspace.id)
      .maybeSingle();

    if (basketError || !basket) {
      return NextResponse.json({ error: 'basket not found' }, { status: 404 });
    }

    const { data: insightCanon } = await supabase
      .from('reflections_artifact')
      .select('id, substrate_hash, computation_timestamp')
      .eq('basket_id', basketId)
      .eq('insight_type', 'insight_canon')
      .eq('is_current', true)
      .maybeSingle();

    const { data: documentCanon } = await supabase
      .from('document_heads')
      .select('document_id, latest_version_created_at')
      .eq('basket_id', basketId)
      .eq('doc_type', 'document_canon')
      .maybeSingle();

    const { data: promptStarter } = await supabase
      .from('document_heads')
      .select('document_id')
      .eq('basket_id', basketId)
      .eq('doc_type', 'starter_prompt')
      .maybeSingle();

    return NextResponse.json({
      has_insight_canon: Boolean(insightCanon),
      insight_canon_stale: false,
      has_document_canon: Boolean(documentCanon),
      document_canon_stale: false,
      has_prompt_starter: Boolean(promptStarter),
      prompt_starter_stale: false,
    });
  } catch (error) {
    console.error('Canon health check failed:', error);
    return NextResponse.json({ error: 'health check failed' }, { status: 500 });
  }
}
