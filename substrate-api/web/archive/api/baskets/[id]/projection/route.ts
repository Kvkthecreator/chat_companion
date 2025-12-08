/**
 * Route: GET /api/baskets/:id/projection
 * @contract input  : none
 * @contract output : ReflectionDTO
 * RLS: workspace-scoped reads, service_role writes
 */
import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { getAuthenticatedUser } from "@/lib/auth/getAuthenticatedUser";
import { ensureWorkspaceForUser } from "@/lib/workspaces/ensureWorkspaceForUser";
import { persistReflection } from "@/app/_server/memory/persistReflection";

export const dynamic = "force-dynamic";

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id: basketId } = await params;
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    // Validate basket exists and user has access
    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basketId)
      .eq('workspace_id', workspace.id)
      .maybeSingle();

    if (basketError || !basket) {
      return NextResponse.json({ error: 'basket not found' }, { status: 404 });
    }

  // 1) Load substrate (dumps/context/relationships + analyzer artifacts from blocks)
  // Keep queries tight; limit rows as needed.
  const [{ data: dumps }, { data: items }, { data: edges }, { data: analyzerBlocks }] =
    await Promise.all([
      supabase.from("raw_dumps").select("id, body_md, created_at").eq("basket_id", basketId).order("created_at", { ascending: false }).limit(200),
      supabase.from("context_items").select("id, type, title, description, metadata, created_at").eq("basket_id", basketId).limit(500),
      supabase.from("substrate_relationships").select("from_type, from_id, to_type, to_id, relationship_type, strength").eq("basket_id", basketId).limit(1000),
      supabase.from("blocks").select("id, semantic_type, metadata, confidence_score, created_at").eq("basket_id", basketId).limit(200),
    ]);

  // 2) Compute reflections (replace with your real logic)
  const pattern =
    analyzerBlocks?.find(b => b.semantic_type === "theme")?.metadata?.summary ??
    null;
  const tension =
    analyzerBlocks?.find(b => b.semantic_type === "tension")?.metadata?.summary ??
    null;
  const question =
    analyzerBlocks?.find(b => b.semantic_type === "question")?.metadata?.text ??
    null;

  // 3) Persist durable reflection + timeline
  const computed_at = new Date().toISOString();
  await persistReflection({
    basketId,
    pattern,
    tension,
    question,
  });

  // 4) Assemble notes from recent dumps (UI helper)
  const notes = (dumps ?? []).slice(0, 10).map(d => ({
    id: d.id,
    text: d.body_md,
    created_at: d.created_at,
  }));

    return NextResponse.json({
      reflections: { pattern, tension, question, computed_at },
    });
  } catch (error) {
    console.error('Projection API error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}