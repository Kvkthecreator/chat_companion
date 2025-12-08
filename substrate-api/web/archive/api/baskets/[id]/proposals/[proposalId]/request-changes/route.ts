import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";

interface RouteContext {
  params: Promise<{ id: string; proposalId: string }>;
}

export async function POST(
  req: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id: basketId, proposalId } = await ctx.params;
    const { review_notes = "", status = "UNDER_REVIEW" } = await req.json();
    
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

    // Fetch proposal to validate
    const { data: proposal, error: proposalError } = await supabase
      .from('proposals')
      .select('*')
      .eq('id', proposalId)
      .eq('basket_id', basketId)
      .single();

    if (proposalError || !proposal) {
      return NextResponse.json({ error: "Proposal not found" }, { status: 404 });
    }

    // Verify proposal can be put under review
    if (proposal.status === 'APPROVED' && proposal.is_executed) {
      return NextResponse.json({ 
        error: "Cannot request changes on executed proposal" 
      }, { status: 400 });
    }

    if (proposal.status === 'REJECTED') {
      return NextResponse.json({ 
        error: "Cannot request changes on rejected proposal" 
      }, { status: 400 });
    }

    // Update proposal status to UNDER_REVIEW
    const { error: updateError } = await supabase
      .from('proposals')
      .update({
        status: 'UNDER_REVIEW',
        reviewed_by: user.id,
        reviewed_at: new Date().toISOString(),
        review_notes: review_notes || 'Changes requested - see review comments'
      })
      .eq('id', proposalId);

    if (updateError) {
      return NextResponse.json({ 
        error: "Failed to request changes" 
      }, { status: 500 });
    }

    // Emit governance timeline event
    const { error: timelineError } = await supabase.rpc('emit_timeline_event', {
      p_basket_id: basketId,
      p_event_type: 'proposal.changes_requested',
      p_event_data: {
        proposal_id: proposalId,
        proposal_kind: proposal.proposal_kind,
        review_notes: review_notes || 'No specific changes noted'
      },
      p_workspace_id: workspace.id,
      p_actor_id: user.id
    });

    if (timelineError) {
      console.error('Failed to emit timeline event:', timelineError);
    }

    return NextResponse.json({
      success: true,
      proposal_id: proposalId,
      status: 'UNDER_REVIEW'
    });

  } catch (error) {
    console.error('Request changes error:', error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}