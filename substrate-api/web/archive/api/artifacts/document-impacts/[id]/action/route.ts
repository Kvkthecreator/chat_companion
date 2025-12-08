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
    const { id: impactId } = await ctx.params;
    const { action, notes = '', workspace_id } = await req.json();
    
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
    if (!workspace || workspace.id !== workspace_id) {
      return NextResponse.json({ error: "Workspace access required" }, { status: 401 });
    }

    // Validate action
    const validActions = ['approve', 'defer', 'skip', 'auto_apply'];
    if (!validActions.includes(action)) {
      return NextResponse.json({ error: "Invalid action" }, { status: 400 });
    }

    // Get the impact
    const { data: impact, error: impactError } = await supabase
      .from('document_impacts')
      .select('*')
      .eq('id', impactId)
      .eq('workspace_id', workspace_id)
      .single();

    if (impactError || !impact) {
      return NextResponse.json({ error: "Document impact not found" }, { status: 404 });
    }

    // Map action to status
    const statusMap = {
      'approve': 'user_approved',
      'defer': 'user_deferred',  
      'skip': 'user_skipped',
      'auto_apply': 'auto_applied'
    };

    const newStatus = statusMap[action as keyof typeof statusMap];

    // Update the impact
    const { error: updateError } = await supabase
      .from('document_impacts')
      .update({
        status: newStatus,
        user_choice: {
          action,
          timestamp: new Date().toISOString(),
          user_id: user.id
        },
        user_notes: notes,
        resolved_by: action !== 'defer' ? user.id : null,
        resolved_at: action !== 'defer' ? new Date().toISOString() : null,
        updated_at: new Date().toISOString()
      })
      .eq('id', impactId);

    if (updateError) {
      return NextResponse.json({ 
        error: "Failed to update impact status" 
      }, { status: 500 });
    }

    // If approved, trigger the document update process
    if (action === 'approve' || action === 'auto_apply') {
      try {
        await executeDocumentUpdate(supabase, impact, user.id);
      } catch (executeError) {
        console.error('Document update execution failed:', executeError);
        
        // Mark as failed but don't return error to user
        await supabase
          .from('document_impacts')
          .update({
            status: 'pending',
            user_notes: `${notes}\n\nExecution failed: ${executeError instanceof Error ? executeError.message : String(executeError)}`
          })
          .eq('id', impactId);
      }
    }

    // Update batch statistics if applicable
    if (impact.batch_id) {
      await supabase.rpc('update_batch_stats', { p_batch_id: impact.batch_id });
    }

    // Emit timeline event
    await supabase.rpc('emit_timeline_event', {
      p_basket_id: null, // Document impacts are workspace-level
      p_event_type: 'document_impact.processed',
      p_event_data: {
        impact_id: impactId,
        document_id: impact.document_id,
        action: action,
        proposed_action_type: impact.proposed_action_type
      },
      p_workspace_id: workspace_id,
      p_actor_id: user.id
    });

    return NextResponse.json({
      success: true,
      impact_id: impactId,
      status: newStatus,
      action: action
    });

  } catch (error) {
    console.error('Document impact action error:', error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

/**
 * Execute the proposed document update
 */
async function executeDocumentUpdate(
  supabase: any,
  impact: any,
  userId: string
): Promise<void> {
  switch (impact.proposed_action_type) {
    case 'recompose':
      await executeRecomposition(supabase, impact, userId);
      break;
    case 'add_references':
      await executeAddReferences(supabase, impact, userId);
      break;
    case 'update_references':
      await executeUpdateReferences(supabase, impact, userId);
      break;
    case 'version_snapshot':
      await executeVersionSnapshot(supabase, impact, userId);
      break;
    default:
      throw new Error(`Unknown proposed action type: ${impact.proposed_action_type}`);
  }
}

async function executeRecomposition(supabase: any, impact: any, userId: string): Promise<void> {
  // Call P4 presentation pipeline to recompose document with updated substrate
  const { error } = await supabase.rpc('fn_p4_recompose_document', {
    p_document_id: impact.document_id,
    p_user_id: userId,
    p_reason: `Document recomposition after substrate changes (impact: ${impact.id})`
  });

  if (error) {
    throw new Error(`Document recomposition failed: ${error.message}`);
  }
}

async function executeAddReferences(supabase: any, impact: any, userId: string): Promise<void> {
  // Add new substrate references to the document
  const references = impact.affected_references || [];
  
  for (const ref of references) {
    const { error } = await supabase
      .from('substrate_references')
      .insert({
        document_id: impact.document_id,
        substrate_id: ref.id,
        substrate_type: ref.type,
        role: ref.relationship_to_document || 'reference',
        weight: 0.5, // Default weight for new references
        added_by: userId,
        added_at: new Date().toISOString()
      });

    if (error) {
      console.error(`Failed to add reference ${ref.id}:`, error);
    }
  }
}

async function executeUpdateReferences(supabase: any, impact: any, userId: string): Promise<void> {
  // Update existing references (e.g., remove deleted substrates)
  const references = impact.affected_references || [];
  
  for (const ref of references) {
    // For removed references, soft delete them
    const { error } = await supabase
      .from('substrate_references')
      .update({
        status: 'removed',
        updated_by: userId,
        updated_at: new Date().toISOString()
      })
      .eq('document_id', impact.document_id)
      .eq('substrate_id', ref.id);

    if (error) {
      console.error(`Failed to update reference ${ref.id}:`, error);
    }
  }
}

async function executeVersionSnapshot(supabase: any, impact: any, userId: string): Promise<void> {
  // Create a version snapshot before making changes
  const { error } = await supabase.rpc('fn_create_document_version_snapshot', {
    p_document_id: impact.document_id,
    p_snapshot_reason: `Version snapshot before substrate changes (impact: ${impact.id})`,
    p_created_by: userId
  });

  if (error) {
    throw new Error(`Version snapshot creation failed: ${error.message}`);
  }

  // After snapshot, proceed with recomposition
  await executeRecomposition(supabase, impact, userId);
}