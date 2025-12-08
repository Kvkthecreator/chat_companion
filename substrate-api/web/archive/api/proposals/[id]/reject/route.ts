import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function POST(
  req: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id: proposalId } = await ctx.params;
    const { review_notes, reason } = await req.json();
    
    const supabase = createRouteHandlerClient({ cookies });
    // Get authenticated user
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Ensure user has workspace access
    const workspace = await ensureWorkspaceServer(supabase);
    if (!workspace) {
      return NextResponse.json({ error: "Workspace access required" }, { status: 401 });
    }
    
    // Get proposal details
    const { data: proposal, error: proposalError } = await supabase
      .from('proposals')
      .select('*')
      .eq('id', proposalId)
      .single();

    if (proposalError || !proposal) {
      return NextResponse.json({ error: "Proposal not found" }, { status: 404 });
    }

    if (proposal.status !== 'PROPOSED' && proposal.status !== 'UNDER_REVIEW') {
      return NextResponse.json({ error: "Proposal cannot be rejected in current state" }, { status: 400 });
    }

    // Update proposal status
    const { error: updateError } = await supabase
      .from('proposals')
      .update({
        status: 'REJECTED',
        reviewed_by: user.id,
        reviewed_at: new Date().toISOString(),
        review_notes
      })
      .eq('id', proposalId);

    if (updateError) {
      return NextResponse.json({ error: "Failed to reject proposal" }, { status: 500 });
    }

    // Emit governance timeline event
    const { error: timelineError } = await supabase.rpc('emit_timeline_event', {
      p_basket_id: proposal.basket_id,
      p_event_type: 'proposal.rejected',
      p_event_data: {
        proposal_id: proposalId,
        proposal_kind: proposal.proposal_kind,
        reason: reason || 'No reason provided'
      },
      p_workspace_id: proposal.workspace_id,
      p_actor_id: user.id
    });

    if (timelineError) {
      console.error('Failed to emit timeline event:', timelineError);
    }

    return NextResponse.json({ 
      success: true, 
      proposal_id: proposalId,
      status: 'REJECTED'
    });

  } catch (error) {
    console.error('Proposal rejection error:', error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}